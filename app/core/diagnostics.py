from typing import List
from app.schemas.reading import ReadingBase
from app.schemas.diagnostic import DiagnosticResult, DiagnosticCondition, Severity

# Centralized configurable thresholds
VOLTAGE_NORMAL_MIN = 2.0
VOLTAGE_NORMAL_MAX = 15.0
VOLTAGE_CRITICAL_LOW = 2.0
VOLTAGE_CRITICAL_HIGH = 18.0

CURRENT_NORMAL_MIN = 0.8
CURRENT_CRITICAL_LOW = 0.3

def evaluate_reading(reading: ReadingBase) -> List[DiagnosticResult]:
    """
    Deterministic rule-based diagnostic engine.
    Evaluates a reading against defined thresholds and returns a list of diagnostic conditions.
    """
    results = []

    # --- Voltage Diagnostics ---
    if reading.voltage < VOLTAGE_CRITICAL_LOW:
        results.append(DiagnosticResult(
            condition=DiagnosticCondition.CRITICAL_LOW_VOLTAGE,
            severity=Severity.CRITICAL,
            title="Critical Low Voltage",
            message="Critical low voltage detected. The battery is severely depleted and may suffer permanent damage.",
            recommended_solution="Disconnect all loads immediately and charge the battery.",
            measured_value=reading.voltage,
            threshold_value=VOLTAGE_CRITICAL_LOW
        ))
    elif reading.voltage < VOLTAGE_NORMAL_MIN:
        results.append(DiagnosticResult(
            condition=DiagnosticCondition.LOW_VOLTAGE,
            severity=Severity.WARNING,
            title="Low Voltage Warning",
            message="Low voltage detected. The measured voltage is below the normal operating range.",
            recommended_solution="Reduce power consumption and ensure solar panels are receiving sunlight.",
            measured_value=reading.voltage,
            threshold_value=VOLTAGE_NORMAL_MIN
        ))
    elif reading.voltage > VOLTAGE_CRITICAL_HIGH:
        results.append(DiagnosticResult(
            condition=DiagnosticCondition.CRITICAL_HIGH_VOLTAGE,
            severity=Severity.CRITICAL,
            title="Critical High Voltage",
            message="Critical high voltage detected. Risk of overcharging and battery damage.",
            recommended_solution="Check charge controller immediately. Disconnect solar panels if necessary.",
            measured_value=reading.voltage,
            threshold_value=VOLTAGE_CRITICAL_HIGH
        ))
    elif reading.voltage > VOLTAGE_NORMAL_MAX:
        results.append(DiagnosticResult(
            condition=DiagnosticCondition.HIGH_VOLTAGE,
            severity=Severity.WARNING,
            title="High Voltage Warning",
            message="High voltage detected. The voltage is above the normal operating range.",
            recommended_solution="Monitor the charge controller to ensure it is regulating voltage properly.",
            measured_value=reading.voltage,
            threshold_value=VOLTAGE_NORMAL_MAX
        ))

    # --- Current Diagnostics ---
    if reading.current <= CURRENT_CRITICAL_LOW:
        results.append(DiagnosticResult(
            condition=DiagnosticCondition.CRITICAL_CURRENT,
            severity=Severity.CRITICAL,
            title="Critical Low Current",
            message="Critical low current detected. A load may have failed or disconnected.",
            recommended_solution="Check all connected loads and wiring immediately.",
            measured_value=reading.current,
            threshold_value=CURRENT_CRITICAL_LOW
        ))
    elif reading.current <= CURRENT_NORMAL_MIN:
        results.append(DiagnosticResult(
            condition=DiagnosticCondition.LOW_CURRENT,
            severity=Severity.WARNING,
            title="Low Current Warning",
            message="Current draw is lower than expected.",
            recommended_solution="Monitor loads. If unexpected, check for partial load failure.",
            measured_value=reading.current,
            threshold_value=CURRENT_NORMAL_MIN
        ))

    # If no abnormal conditions, return a normal result
    if not results:
        results.append(DiagnosticResult(
            condition=DiagnosticCondition.NORMAL_OPERATION,
            severity=Severity.NORMAL,
            title="Normal Operation",
            message="All sensor readings are within normal operating parameters.",
            recommended_solution="No action required.",
            measured_value=reading.voltage, # Just providing context
            threshold_value=None
        ))

    return results
