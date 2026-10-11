from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class AlertBase(BaseModel):
    condition: str
    severity: str
    title: str
    message: str
    recommended_solution: str
    measured_value: float
    threshold_value: Optional[float] = None
    status: str = "ACTIVE"

class AlertCreate(AlertBase):
    device_id: int

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class AlertInDBBase(AlertBase):
    id: int
    device_id: int
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Alert(AlertInDBBase):
    pass
