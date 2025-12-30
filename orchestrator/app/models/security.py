"""Secrets management and audit log models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
import enum

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TableNameMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class SecretType(str, enum.Enum):
    """Secret type enumeration."""

    PASSWORD = "password"
    API_KEY = "api_key"
    TOKEN = "token"
    SSH_KEY = "ssh_key"
    CERTIFICATE = "certificate"
    CONNECTION_STRING = "connection_string"
    OTHER = "other"


class AuditAction(str, enum.Enum):
    """Audit action enumeration."""

    # User actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"

    # Server actions
    SERVER_CREATED = "server_created"
    SERVER_UPDATED = "server_updated"
    SERVER_DELETED = "server_deleted"
    SERVER_CONNECTED = "server_connected"
    SERVER_DISCONNECTED = "server_disconnected"

    # Deployment actions
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_FAILED = "deployment_failed"
    DEPLOYMENT_ROLLED_BACK = "deployment_rolled_back"

    # Snapshot actions
    SNAPSHOT_CREATED = "snapshot_created"
    SNAPSHOT_RESTORED = "snapshot_restored"
    SNAPSHOT_DELETED = "snapshot_deleted"

    # Secret actions
    SECRET_CREATED = "secret_created"
    SECRET_UPDATED = "secret_updated"
    SECRET_DELETED = "secret_deleted"
    SECRET_ACCESSED = "secret_accessed"

    # Integration actions
    INTEGRATION_ENABLED = "integration_enabled"
    INTEGRATION_DISABLED = "integration_disabled"
    INTEGRATION_CONFIGURED = "integration_configured"

    # Configuration actions
    CONFIG_VALIDATED = "config_validated"
    CONFIG_UPDATED = "config_updated"

    # System actions
    SYSTEM_SETTINGS_UPDATED = "system_settings_updated"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"


class Secret(Base, TableNameMixin, TimestampMixin):
    """Secret storage model with encryption."""

    __tablename__ = "secrets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Secret identification
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    secret_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # api_key, password, token, certificate, ssh_key, etc.

    # Encrypted value
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)  # AES-256 encrypted
    encryption_version: Mapped[int] = mapped_column(
        Integer, default=1
    )  # For key rotation support
    encryption_algorithm: Mapped[str] = mapped_column(String(50), default="AES-256-GCM")

    # Association (where this secret is used)
    server_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("servers.id"), nullable=True
    )
    deployment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("deployments.id"), nullable=True
    )
    integration_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # wled, fpp, tailscale, etc.
    integration_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Expiration and rotation
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_rotated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rotation_interval_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Auto-rotate every N days
    rotation_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Access tracking
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Secret(id={self.id}, name={self.name}, type={self.secret_type})>"


class SecretAccessLog(Base, TableNameMixin, TimestampMixin):
    """Secret access audit log."""

    __tablename__ = "secret_access_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Secret reference
    secret_id: Mapped[int] = mapped_column(Integer, ForeignKey("secrets.id"), nullable=False)

    # Access details
    accessed_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    accessed_by_service: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Which service accessed it
    access_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # read, decrypt, rotate, revoke, create, update
    access_method: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # api, cli, ui, automated

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Result
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<SecretAccessLog(id={self.id}, secret_id={self.secret_id}, type={self.access_type})>"


class AuditLog(Base, TableNameMixin, TimestampMixin):
    """System-wide audit log for all operations."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Operation details
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # auth, server, deployment, backup, secret, etc.
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # info, warning, error, critical
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # success, failure, partial

    # Actor (who performed the action)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")
    service: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Automated service that performed action

    # Target (what was affected)
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # server, deployment, backup, secret, etc.
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resource_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    changes: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Before/after for modifications
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    request_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    request_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Compliance
    compliance_tags: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # GDPR, HIPAA, etc.
    retention_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )  # Keep until this date

    # Metadata
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<AuditLog(id={self.id}, action={self.action}, category={self.category})>"


class ComplianceReport(Base, TableNameMixin, TimestampMixin):
    """Compliance report model for regulatory requirements."""

    __tablename__ = "compliance_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Report information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # security, access, changes, gdpr, etc.
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Report generation
    generated_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    generation_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Report content
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    findings: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Key findings and statistics
    recommendations: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # Security recommendations

    # Export
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_format: Mapped[str] = mapped_column(
        String(20), default="json"
    )  # json, csv, pdf, html
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="completed"
    )  # pending, generating, completed, failed

    # Metadata
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ComplianceReport(id={self.id}, type={self.report_type}, name={self.name})>"


class SecurityEvent(Base, TableNameMixin, TimestampMixin):
    """Security-specific events and alerts."""

    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Event details
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # failed_login, unauthorized_access, secret_leak, etc.
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # low, medium, high, critical
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Source
    source_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    source_service: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Target
    target_resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Response
    response_required: Mapped[bool] = mapped_column(Boolean, default=False)
    response_status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # pending, investigating, resolved, false_positive
    responded_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    response_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Notification
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notified_users: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Metadata
    evidence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<SecurityEvent(id={self.id}, type={self.event_type}, severity={self.severity})>"
