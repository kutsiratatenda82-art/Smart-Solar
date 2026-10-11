from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeviceBase(BaseModel):
    device_identifier: str
    name: str
    status: Optional[str] = "active"

class DeviceCreate(DeviceBase):
    pass

class DeviceInDBBase(DeviceBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Device(DeviceInDBBase):
    pass
