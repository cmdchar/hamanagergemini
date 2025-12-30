"""Secrets management and encryption service."""

import base64
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security import AuditLog, Secret, SecretAccessLog, SecurityEvent
from app.utils.logging import log_integration_event

logger = logging.getLogger(__name__)


class SecretsManager:
    """Service for secrets encryption, decryption, and management."""

    def __init__(self, db: AsyncSession, master_key: Optional[str] = None):
        """
        Initialize secrets manager.

        Args:
            db: Database session
            master_key: Master encryption key (from environment)
        """
        self.db = db
        self.master_key = master_key or os.getenv("SECRETS_MASTER_KEY", "default-dev-key-change-in-prod")
        self._cipher = self._initialize_cipher()

    def _initialize_cipher(self) -> Fernet:
        """
        Initialize Fernet cipher with master key.

        Returns:
            Fernet: Cipher instance
        """
        # Derive key from master key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"ha-config-manager-salt",  # Should be random in production
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return Fernet(key)

    async def create_secret(
        self,
        name: str,
        value: str,
        secret_type: str,
        description: Optional[str] = None,
        user_id: Optional[int] = None,
        **kwargs,
    ) -> Optional[Secret]:
        """
        Create and encrypt a new secret.

        Args:
            name: Secret name
            value: Secret value (plaintext)
            secret_type: Type of secret
            description: Optional description
            user_id: User creating the secret
            **kwargs: Additional fields

        Returns:
            Optional[Secret]: Created secret
        """
        try:
            # Encrypt the value
            encrypted_value = self._encrypt(value)

            # Create secret record
            secret = Secret(
                name=name,
                description=description,
                secret_type=secret_type,
                encrypted_value=encrypted_value,
                encryption_version=1,
                encryption_algorithm="AES-256-GCM",
                **kwargs,
            )

            self.db.add(secret)
            await self.db.commit()
            await self.db.refresh(secret)

            # Log creation
            await self._log_secret_access(
                secret_id=secret.id,
                access_type="create",
                user_id=user_id,
                success=True,
            )

            await self._audit_log(
                action="secret_created",
                category="secret",
                severity="info",
                status="success",
                user_id=user_id,
                resource_type="secret",
                resource_id=secret.id,
                resource_name=name,
                description=f"Created secret: {name} ({secret_type})",
            )

            log_integration_event(
                "Secrets",
                "secret_created",
                True,
                {"secret_id": secret.id, "name": name, "type": secret_type},
            )

            return secret

        except Exception as e:
            logger.exception(f"Failed to create secret: {e}")
            await self._audit_log(
                action="secret_create_failed",
                category="secret",
                severity="error",
                status="failure",
                user_id=user_id,
                description=f"Failed to create secret: {name}",
                error_details=str(e),
            )
            return None

    async def get_secret(
        self,
        secret_id: Optional[int] = None,
        secret_name: Optional[str] = None,
        decrypt: bool = False,
        user_id: Optional[int] = None,
        service: Optional[str] = None,
    ) -> Optional[Secret]:
        """
        Get a secret by ID or name.

        Args:
            secret_id: Secret ID
            secret_name: Secret name
            decrypt: Whether to decrypt the value
            user_id: User requesting the secret
            service: Service requesting the secret

        Returns:
            Optional[Secret]: Secret record
        """
        try:
            if secret_id:
                result = await self.db.execute(
                    select(Secret).where(Secret.id == secret_id, Secret.is_active == True)
                )
            elif secret_name:
                result = await self.db.execute(
                    select(Secret).where(Secret.name == secret_name, Secret.is_active == True)
                )
            else:
                return None

            secret = result.scalar_one_or_none()

            if not secret:
                return None

            # Update access tracking
            secret.last_accessed = datetime.utcnow()
            secret.access_count += 1
            await self.db.commit()

            # Log access
            await self._log_secret_access(
                secret_id=secret.id,
                access_type="read" if not decrypt else "decrypt",
                user_id=user_id,
                service=service,
                success=True,
            )

            return secret

        except Exception as e:
            logger.exception(f"Failed to get secret: {e}")
            await self._log_secret_access(
                secret_id=secret_id or 0,
                access_type="read",
                user_id=user_id,
                service=service,
                success=False,
                error_message=str(e),
            )
            return None

    async def decrypt_secret(
        self,
        secret_id: Optional[int] = None,
        secret_name: Optional[str] = None,
        user_id: Optional[int] = None,
        service: Optional[str] = None,
    ) -> Optional[str]:
        """
        Decrypt and return secret value.

        Args:
            secret_id: Secret ID
            secret_name: Secret name
            user_id: User requesting decryption
            service: Service requesting decryption

        Returns:
            Optional[str]: Decrypted value
        """
        try:
            secret = await self.get_secret(
                secret_id=secret_id,
                secret_name=secret_name,
                decrypt=True,
                user_id=user_id,
                service=service,
            )

            if not secret:
                return None

            # Check if revoked
            if secret.is_revoked:
                logger.warning(f"Attempted to decrypt revoked secret: {secret.name}")
                await self._create_security_event(
                    event_type="revoked_secret_access",
                    severity="high",
                    title=f"Attempted access to revoked secret",
                    description=f"User/service attempted to decrypt revoked secret: {secret.name}",
                    source_user_id=user_id,
                    source_service=service,
                    target_resource_type="secret",
                    target_resource_id=secret.id,
                )
                return None

            # Decrypt
            decrypted_value = self._decrypt(secret.encrypted_value)

            return decrypted_value

        except Exception as e:
            logger.exception(f"Failed to decrypt secret: {e}")
            return None

    async def rotate_secret(
        self,
        secret_id: int,
        new_value: str,
        user_id: Optional[int] = None,
    ) -> bool:
        """
        Rotate a secret value.

        Args:
            secret_id: Secret ID
            new_value: New secret value
            user_id: User performing rotation

        Returns:
            bool: Success status
        """
        try:
            result = await self.db.execute(
                select(Secret).where(Secret.id == secret_id)
            )
            secret = result.scalar_one_or_none()

            if not secret:
                return False

            # Encrypt new value
            encrypted_value = self._encrypt(new_value)

            # Update secret
            secret.encrypted_value = encrypted_value
            secret.last_rotated = datetime.utcnow()
            secret.rotation_required = False

            await self.db.commit()

            # Log rotation
            await self._log_secret_access(
                secret_id=secret_id,
                access_type="rotate",
                user_id=user_id,
                success=True,
            )

            await self._audit_log(
                action="secret_rotated",
                category="secret",
                severity="info",
                status="success",
                user_id=user_id,
                resource_type="secret",
                resource_id=secret_id,
                resource_name=secret.name,
                description=f"Rotated secret: {secret.name}",
            )

            return True

        except Exception as e:
            logger.exception(f"Failed to rotate secret: {e}")
            return False

    async def revoke_secret(
        self,
        secret_id: int,
        reason: str,
        user_id: Optional[int] = None,
    ) -> bool:
        """
        Revoke a secret.

        Args:
            secret_id: Secret ID
            reason: Revocation reason
            user_id: User performing revocation

        Returns:
            bool: Success status
        """
        try:
            result = await self.db.execute(
                select(Secret).where(Secret.id == secret_id)
            )
            secret = result.scalar_one_or_none()

            if not secret:
                return False

            # Revoke secret
            secret.is_revoked = True
            secret.is_active = False
            secret.revoked_at = datetime.utcnow()
            secret.revoked_reason = reason

            await self.db.commit()

            # Log revocation
            await self._log_secret_access(
                secret_id=secret_id,
                access_type="revoke",
                user_id=user_id,
                success=True,
            )

            await self._audit_log(
                action="secret_revoked",
                category="secret",
                severity="warning",
                status="success",
                user_id=user_id,
                resource_type="secret",
                resource_id=secret_id,
                resource_name=secret.name,
                description=f"Revoked secret: {secret.name}. Reason: {reason}",
            )

            return True

        except Exception as e:
            logger.exception(f"Failed to revoke secret: {e}")
            return False

    async def check_rotation_required(self) -> List[Secret]:
        """
        Check for secrets that require rotation.

        Returns:
            List[Secret]: Secrets requiring rotation
        """
        try:
            # Find secrets with rotation interval that haven't been rotated
            query = select(Secret).where(
                Secret.is_active == True,
                Secret.rotation_interval_days.is_not(None),
            )

            result = await self.db.execute(query)
            secrets = list(result.scalars().all())

            needs_rotation = []
            for secret in secrets:
                if secret.last_rotated:
                    days_since_rotation = (datetime.utcnow() - secret.last_rotated).days
                    if days_since_rotation >= secret.rotation_interval_days:
                        secret.rotation_required = True
                        needs_rotation.append(secret)
                elif secret.rotation_interval_days:
                    # Never rotated, check creation date
                    days_since_creation = (datetime.utcnow() - secret.created_at).days
                    if days_since_creation >= secret.rotation_interval_days:
                        secret.rotation_required = True
                        needs_rotation.append(secret)

            if needs_rotation:
                await self.db.commit()

            return needs_rotation

        except Exception as e:
            logger.exception(f"Failed to check rotation: {e}")
            return []

    def _encrypt(self, value: str) -> str:
        """
        Encrypt a value.

        Args:
            value: Plaintext value

        Returns:
            str: Encrypted value (base64)
        """
        encrypted = self._cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()

    def _decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt a value.

        Args:
            encrypted_value: Encrypted value (base64)

        Returns:
            str: Decrypted plaintext
        """
        encrypted = base64.b64decode(encrypted_value.encode())
        decrypted = self._cipher.decrypt(encrypted)
        return decrypted.decode()

    async def _log_secret_access(
        self,
        secret_id: int,
        access_type: str,
        user_id: Optional[int] = None,
        service: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Log secret access."""
        try:
            log = SecretAccessLog(
                secret_id=secret_id,
                accessed_by_user_id=user_id,
                accessed_by_service=service,
                access_type=access_type,
                success=success,
                error_message=error_message,
            )
            self.db.add(log)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log secret access: {e}")

    async def _audit_log(
        self,
        action: str,
        category: str,
        severity: str,
        status: str,
        description: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        error_details: Optional[str] = None,
    ):
        """Create audit log entry."""
        try:
            log = AuditLog(
                action=action,
                category=category,
                severity=severity,
                status=status,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                description=description,
                error_details=error_details,
            )
            self.db.add(log)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")

    async def _create_security_event(
        self,
        event_type: str,
        severity: str,
        title: str,
        description: str,
        source_user_id: Optional[int] = None,
        source_service: Optional[str] = None,
        target_resource_type: Optional[str] = None,
        target_resource_id: Optional[int] = None,
        response_required: bool = True,
    ):
        """Create security event."""
        try:
            event = SecurityEvent(
                event_type=event_type,
                severity=severity,
                title=title,
                description=description,
                source_user_id=source_user_id,
                source_service=source_service,
                target_resource_type=target_resource_type,
                target_resource_id=target_resource_id,
                response_required=response_required,
                response_status="pending" if response_required else None,
            )
            self.db.add(event)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to create security event: {e}")
