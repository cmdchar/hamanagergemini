"""Server model."""

import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TableNameMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.deployment import Deployment, DeploymentResult
    from app.models.led_device import LEDDevice
    from app.models.snapshot import Snapshot


class ServerType(str, enum.Enum):
    """Server type enumeration."""

    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"


class ServerStatus(str, enum.Enum):
    """Server status enumeration."""

    ONLINE = "online"
    OFFLINE = "offline"
    DEPLOYING = "deploying"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class Server(Base, TableNameMixin, TimestampMixin):
    """Server model for managing Home Assistant instances."""

    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Connection details
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=8123, nullable=False)
    use_ssl: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Authentication
    access_token: Mapped[str] = mapped_column(String(500), nullable=True)
    api_key: Mapped[str] = mapped_column(String(255), nullable=True)
    ha_username: Mapped[str] = mapped_column(String(255), nullable=True)
    ha_password: Mapped[str] = mapped_column(String(500), nullable=True)  # Encrypted

    # SSH details
    ssh_host: Mapped[str] = mapped_column(String(255), nullable=True)
    ssh_port: Mapped[int] = mapped_column(Integer, default=22, nullable=True)
    ssh_user: Mapped[str] = mapped_column(String(100), nullable=True)
    ssh_key_path: Mapped[str] = mapped_column(String(500), nullable=True)
    ssh_password: Mapped[str] = mapped_column(String(255), nullable=True)  # Encrypted
    ssh_key_passphrase: Mapped[str] = mapped_column(String(255), nullable=True)  # Encrypted

    # GitHub integration
    github_repo: Mapped[str] = mapped_column(String(500), nullable=True)
    github_branch: Mapped[str] = mapped_column(String(255), nullable=True)

    # Server info
    server_type: Mapped[ServerType] = mapped_column(
        Enum(ServerType), default=ServerType.PRODUCTION, nullable=False
    )
    status: Mapped[ServerStatus] = mapped_column(
        Enum(ServerStatus), default=ServerStatus.OFFLINE, nullable=False
    )

    # Paths
    config_path: Mapped[str] = mapped_column(
        String(500), default="/config", nullable=False
    )
    backup_path: Mapped[str] = mapped_column(
        String(500), default="/backup", nullable=True
    )

    # Settings
    auto_deploy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_backup: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Tailscale integration
    tailscale_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tailscale_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    tailscale_hostname: Mapped[str] = mapped_column(String(255), nullable=True)

    # Metadata
    version: Mapped[str] = mapped_column(String(50), nullable=True)
    meta_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=True)

    # Relationships
    deployment_results: Mapped[list["DeploymentResult"]] = relationship(
        "DeploymentResult", back_populates="server", lazy="selectin"
    )
    snapshots: Mapped[list["Snapshot"]] = relationship(
        "Snapshot", back_populates="server", lazy="selectin"
    )
    led_devices: Mapped[list["LEDDevice"]] = relationship(
        "LEDDevice", back_populates="server", lazy="selectin"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Server(id={self.id}, name={self.name}, host={self.host})>"

    @property
    def url(self) -> str:
        """Get server URL."""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"

    @property
    def is_online(self) -> bool:
        """Check if server is online."""
        return self.status == ServerStatus.ONLINE
