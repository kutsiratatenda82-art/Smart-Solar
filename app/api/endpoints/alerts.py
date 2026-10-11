from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app import models, schemas
from app.api import deps
from app.core.database import get_db

router = APIRouter()

@router.get("", response_model=List[schemas.Alert])
def get_active_alerts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """Get active alerts for devices owned by the current user."""
    alerts = (
        db.query(models.Alert)
        .join(models.SolarDevice)
        .filter(
            models.SolarDevice.owner_id == current_user.id,
            models.Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"])
        )
        .order_by(models.Alert.created_at.desc())
        .all()
    )
    return alerts

@router.get("/history", response_model=List[schemas.Alert])
def get_alert_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """Get alert history for devices owned by the current user."""
    alerts = (
        db.query(models.Alert)
        .join(models.SolarDevice)
        .filter(models.SolarDevice.owner_id == current_user.id)
        .order_by(models.Alert.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return alerts

@router.get("/{alert_id}", response_model=schemas.Alert)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """Get a specific alert by ID."""
    alert = (
        db.query(models.Alert)
        .join(models.SolarDevice)
        .filter(
            models.Alert.id == alert_id,
            models.SolarDevice.owner_id == current_user.id
        )
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.patch("/{alert_id}/acknowledge", response_model=schemas.Alert)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """Acknowledge a specific alert."""
    alert = (
        db.query(models.Alert)
        .join(models.SolarDevice)
        .filter(
            models.Alert.id == alert_id,
            models.SolarDevice.owner_id == current_user.id
        )
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    if alert.status == "ACTIVE":
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)
    return alert

@router.patch("/{alert_id}/resolve", response_model=schemas.Alert)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """Resolve a specific alert."""
    alert = (
        db.query(models.Alert)
        .join(models.SolarDevice)
        .filter(
            models.Alert.id == alert_id,
            models.SolarDevice.owner_id == current_user.id
        )
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    if alert.status in ("ACTIVE", "ACKNOWLEDGED"):
        alert.status = "RESOLVED"
        alert.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)
    return alert
