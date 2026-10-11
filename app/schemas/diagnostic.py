from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class Severity(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class DiagnosticCondition(str, Enum):
    NORMAL_OPERATION = "NORMAL_OPERATION"
    LOW_VOLTAGE = "LOW_VOLTAGE"
    CRITICAL_LOW_VOLTAGE = "CRITICAL_LOW_VOLTAGE"
    HIGH_VOLTAGE = "HIGH_VOLTAGE"
    CRITICAL_HIGH_VOLTAGE = "CRITICAL_HIGH_VOLTAGE"
    LOW_CURRENT = "LOW_CURRENT"
    CRITICAL_CURRENT = "CRITICAL_CURRENT"

class DiagnosticResult(BaseModel):
    condition: DiagnosticCondition
    severity: Severity
    title: str
    message: str
    recommended_solution: str
    measured_value: float
    threshold_value: Optional[float] = None

class SimulationResult(BaseModel):
    mode: str = "DEMO"
    simulated: bool = True
    diagnostics: List[DiagnosticResult]
