from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class HaConfigBase(BaseModel):
    path: str

class HaConfigCreate(HaConfigBase):
    content: Optional[str] = None
    server_id: int

class HaConfigUpdate(BaseModel):
    content: Optional[str] = None

class HaConfigResponse(HaConfigBase):
    id: UUID
    server_id: int
    content: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
