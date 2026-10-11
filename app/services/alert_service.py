from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.models.alert import Alert
from app.schemas.diagnostic import DiagnosticResult, DiagnosticCondition

def process_diagnostics(db: Session, device_id: int, diagnostics: List[DiagnosticResult]):
    """
    Takes the output of the diagnostic engine and updates the database alerts.
    - Prevents duplicate ACTIVE alerts for the same condition.
    - Resolves ACTIVE alerts for conditions that are no longer present.
    - Returns the list of currently active alerts for this device (after processing).
    """
    # 1. Fetch existing ACTIVE or ACKNOWLEDGED alerts for this device
    active_alerts = db.query(Alert).filter(
        Alert.device_id == device_id,
        Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"])
    ).all()
    
    active_conditions_in_db = {alert.condition: alert for alert in active_alerts}
    
    current_conditions = {diag.condition.value for diag in diagnostics}
    
    # 2. Resolve alerts that are no longer present
    for alert in active_alerts:
        if alert.condition not in current_conditions:
            alert.status = "RESOLVED"
            alert.resolved_at = datetime.now(timezone.utc)
            db.add(alert)

    # 3. Create or re-activate alerts for conditions that are currently present
    from datetime import timedelta
    for diag in diagnostics:
        if diag.condition == DiagnosticCondition.NORMAL_OPERATION:
            continue
            
        if diag.condition.value not in active_conditions_in_db:
            # Create new alert
            new_alert = Alert(
                device_id=device_id,
                condition=diag.condition.value,
                severity=diag.severity.value,
                title=diag.title,
                message=diag.message,
                recommended_solution=diag.recommended_solution,
                measured_value=diag.measured_value,
                threshold_value=diag.threshold_value,
                status="ACTIVE"
            )
            db.add(new_alert)
        else:
            existing_alert = active_conditions_in_db[diag.condition.value]
            if existing_alert.status == "ACKNOWLEDGED" and existing_alert.acknowledged_at:
                # Re-activate if it has been acknowledged for more than 2 minutes
                if datetime.now(timezone.utc) - existing_alert.acknowledged_at > timedelta(minutes=2):
                    existing_alert.status = "ACTIVE"
                    db.add(existing_alert)
            
    db.commit()
