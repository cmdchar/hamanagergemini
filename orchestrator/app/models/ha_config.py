import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base, TimestampMixin, TableNameMixin

class HaConfig(Base, TimestampMixin, TableNameMixin):
    """Model for storing Home Assistant configuration files."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relationships
    server = relationship("Server", backref="ha_configs")
