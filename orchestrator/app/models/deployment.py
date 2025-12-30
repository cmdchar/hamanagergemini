"""Deployment models."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TableNameMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.server import Server
    from app.models.user import User


class DeploymentStatus(str, enum.Enum):
    """Deployment status enumeration."""

    PENDING = "pending"
    VALIDATING = "validating"
    BACKING_UP = "backing_up"
    DEPLOYING = "deploying"
    RESTARTING = "restarting"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class DeploymentTrigger(str, enum.Enum):
    """Deployment trigger enumeration."""

    MANUAL = "manual"
    GITHUB_PUSH = "github_push"
    GITHUB_PR = "github_pr"
    SCHEDULED = "scheduled"
    API = "api"


class Deployment(Base, TableNameMixin, TimestampMixin):
    """Deployment model for tracking configuration deployments."""

    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Relationships
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    user: Mapped["User"] = relationship("User", back_populates="deployments")

    # Deployment details
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Deployment")
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[DeploymentStatus] = mapped_column(
        Enum(DeploymentStatus), default=DeploymentStatus.PENDING, nullable=False
    )
    trigger: Mapped[DeploymentTrigger] = mapped_column(
        Enum(DeploymentTrigger), default=DeploymentTrigger.MANUAL, nullable=False
    )

    # Git information
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=True)
    commit_message: Mapped[str] = mapped_column(Text, nullable=True)
    branch: Mapped[str] = mapped_column(String(255), nullable=True)
    author: Mapped[str] = mapped_column(String(255), nullable=True)

    # GitHub PR information
    pr_number: Mapped[int] = mapped_column(Integer, nullable=True)
    pr_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)

    # Configuration
    target_servers: Mapped[list] = mapped_column(JSON, nullable=True)  # List of server IDs
    deploy_all: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skip_validation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skip_backup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_restart: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_rollback: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Results
    total_servers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_servers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_servers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Logs and errors
    logs: Mapped[str] = mapped_column(Text, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Metadata
    meta_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Rollback information
    can_rollback: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rolled_back_from_id: Mapped[int] = mapped_column(Integer, nullable=True)

    # Server-specific results
    server_results: Mapped[list["DeploymentResult"]] = relationship(
        "DeploymentResult", back_populates="deployment", lazy="selectin"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Deployment(id={self.id}, status={self.status}, commit={self.commit_sha})>"

    @property
    def is_complete(self) -> bool:
        """Check if deployment is complete."""
        return self.status in [
            DeploymentStatus.SUCCESS,
            DeploymentStatus.FAILED,
            DeploymentStatus.ROLLED_BACK,
            DeploymentStatus.CANCELLED,
        ]

    @property
    def is_successful(self) -> bool:
        """Check if deployment was successful."""
        return self.status == DeploymentStatus.SUCCESS


class DeploymentResult(Base, TableNameMixin, TimestampMixin):
    """Deployment result for individual servers."""

    __tablename__ = "deployment_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Relationships
    deployment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deployments.id"), nullable=False, index=True
    )
    deployment: Mapped["Deployment"] = relationship(
        "Deployment", back_populates="server_results"
    )

    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("servers.id"), nullable=False, index=True
    )
    server: Mapped["Server"] = relationship("Server", back_populates="deployment_results")

    # Result
    status: Mapped[DeploymentStatus] = mapped_column(
        Enum(DeploymentStatus), default=DeploymentStatus.PENDING, nullable=False
    )
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)

    # Details
    validation_output: Mapped[str] = mapped_column(Text, nullable=True)
    backup_id: Mapped[int] = mapped_column(Integer, nullable=True)
    logs: Mapped[str] = mapped_column(Text, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Files
    files_changed: Mapped[list] = mapped_column(JSON, nullable=True)
    files_added: Mapped[list] = mapped_column(JSON, nullable=True)
    files_deleted: Mapped[list] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DeploymentResult(id={self.id}, deployment_id={self.deployment_id}, "
            f"server_id={self.server_id}, status={self.status})>"
        )
