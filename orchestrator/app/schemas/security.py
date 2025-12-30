"""Security schemas for secrets and audit logs."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, SecretStr


# Secret schemas
class SecretBase(BaseModel):
    """Base secret schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    secret_type: str = Field(..., pattern="^(api_key|password|token|certificate|ssh_key|other)$")
    server_id: Optional[int] = None
    deployment_id: Optional[int] = None
    integration_type: Optional[str] = None
    integration_id: Optional[int] = None
    rotation_interval_days: Optional[int] = Field(None, ge=1, le=365)
    tags: Optional[List[str]] = None


class SecretCreate(SecretBase):
    """Create secret request."""

    value: SecretStr = Field(..., description="Secret value (will be encrypted)")


class SecretUpdate(BaseModel):
    """Update secret request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rotation_interval_days: Optional[int] = Field(None, ge=1, le=365)
    tags: Optional[List[str]] = None


class SecretResponse(SecretBase):
    """Secret response (without decrypted value)."""

    id: int
    encryption_version: int
    encryption_algorithm: str
    expires_at: Optional[datetime] = None
    last_rotated: Optional[datetime] = None
    rotation_required: bool
    last_accessed: Optional[datetime] = None
    access_count: int
    is_active: bool
    is_revoked: bool
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SecretWithValue(SecretResponse):
    """Secret response with decrypted value."""

    value: str = Field(..., description="Decrypted secret value")


class SecretRotateRequest(BaseModel):
    """Rotate secret request."""

    new_value: SecretStr = Field(..., description="New secret value")


class SecretRevokeRequest(BaseModel):
    """Revoke secret request."""

    reason: str = Field(..., min_length=1, max_length=500)


# Secret access log schemas
class SecretAccessLogResponse(BaseModel):
    """Secret access log response."""

    id: int
    secret_id: int
    accessed_by_user_id: Optional[int] = None
    accessed_by_service: Optional[str] = None
    access_type: str
    access_method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Audit log schemas
class AuditLogFilter(BaseModel):
    """Audit log filter."""

    action: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AuditLogResponse(BaseModel):
    """Audit log response."""

    id: int
    action: str
    category: str
    severity: str
    status: str
    user_id: Optional[int] = None
    service: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    resource_name: Optional[str] = None
    description: str
    changes: Optional[dict] = None
    error_details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    compliance_tags: Optional[List[str]] = None
    retention_until: Optional[datetime] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Security event schemas
class SecurityEventResponse(BaseModel):
    """Security event response."""

    id: int
    event_type: str
    severity: str
    title: str
    description: str
    source_ip: Optional[str] = None
    source_user_id: Optional[int] = None
    source_service: Optional[str] = None
    target_resource_type: Optional[str] = None
    target_resource_id: Optional[int] = None
    response_required: bool
    response_status: Optional[str] = None
    responded_by_user_id: Optional[int] = None
    responded_at: Optional[datetime] = None
    response_notes: Optional[str] = None
    notified: bool
    notification_sent_at: Optional[datetime] = None
    notified_users: Optional[List[int]] = None
    evidence: Optional[dict] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SecurityEventResolveRequest(BaseModel):
    """Resolve security event request."""

    response_status: str = Field(..., pattern="^(investigating|resolved|false_positive)$")
    response_notes: str = Field(..., min_length=1, max_length=1000)


# Compliance report schemas
class ComplianceReportCreate(BaseModel):
    """Create compliance report request."""

    name: str = Field(..., min_length=1, max_length=255)
    report_type: str = Field(..., pattern="^(security|access|changes|gdpr|hipaa)$")
    period_start: datetime
    period_end: datetime
    filters: Optional[dict] = None


class ComplianceReportResponse(BaseModel):
    """Compliance report response."""

    id: int
    name: str
    report_type: str
    period_start: datetime
    period_end: datetime
    generated_by_user_id: Optional[int] = None
    generated_at: datetime
    generation_duration_seconds: Optional[int] = None
    summary: Optional[str] = None
    findings: Optional[dict] = None
    recommendations: Optional[List[str]] = None
    file_path: Optional[str] = None
    file_format: str
    file_size: Optional[int] = None
    status: str
    filters: Optional[dict] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Statistics schemas
class SecretStatistics(BaseModel):
    """Secret statistics."""

    total_secrets: int
    active_secrets: int
    revoked_secrets: int
    secrets_by_type: dict
    secrets_requiring_rotation: int
    total_accesses_today: int
    failed_accesses_today: int


class AuditStatistics(BaseModel):
    """Audit statistics."""

    total_events: int
    events_by_category: dict
    events_by_severity: dict
    events_today: int
    errors_today: int
    top_users: List[dict]
    top_actions: List[dict]


class SecurityStatistics(BaseModel):
    """Security statistics."""

    total_events: int
    critical_events: int
    high_severity_events: int
    unresolved_events: int
    events_by_type: dict
    events_requiring_response: int
