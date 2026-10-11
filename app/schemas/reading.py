from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReadingBase(BaseModel):
    voltage: float = Field(..., description="Voltage reading from the solar panel")
    current: float = Field(..., description="Current reading from the solar panel")

class ReadingCreate(ReadingBase):
    pass

class ReadingInDBBase(ReadingBase):
    id: int
    device_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class Reading(ReadingInDBBase):
    pass

from app.schemas.diagnostic import DiagnosticResult
from typing import List

class ReadingResponse(Reading):
    diagnostics: List[DiagnosticResult] = []
