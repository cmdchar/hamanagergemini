"""Common Pydantic schemas."""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseSchema):
    """Generic message response."""

    message: str
    success: bool = True


class ErrorResponse(BaseSchema):
    """Error response schema."""

    detail: str
    error_code: Optional[str] = None
    error_type: Optional[str] = None


class HealthResponse(BaseSchema):
    """Health check response."""

    status: str = "healthy"
    version: str
    timestamp: datetime
    database: str = "connected"
    redis: str = "connected"
    services: dict = Field(default_factory=dict)


T = TypeVar("T")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response."""

    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20
    pages: int = 1

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int = 1,
        page_size: int = 20,
    ) -> "PaginatedResponse[T]":
        """Create paginated response."""
        pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )


class IDResponse(BaseSchema):
    """Response with resource ID."""

    id: int
    message: str = "Resource created successfully"


class BulkOperationResponse(BaseSchema):
    """Bulk operation response."""

    total: int
    successful: int
    failed: int
    errors: List[dict] = Field(default_factory=list)
