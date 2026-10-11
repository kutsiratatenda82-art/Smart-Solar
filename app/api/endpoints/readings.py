from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core.database import get_db
from app.core.diagnostics import evaluate_reading
from app.services.alert_service import process_diagnostics

router = APIRouter()

def get_device_if_owner(device_id: int, db: Session, current_user: models.User):
    device = db.query(models.SolarDevice).filter(models.SolarDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return device

@router.post("/{device_id}/readings", response_model=schemas.ReadingResponse, status_code=status.HTTP_201_CREATED)
def create_reading(
    device_id: int,
    reading_in: schemas.ReadingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    device = get_device_if_owner(device_id, db, current_user)
    
    db_reading = models.SensorReading(
        **reading_in.model_dump(),
        device_id=device.id
    )
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    
    # Run diagnostic engine
    diagnostics = evaluate_reading(reading_in)
    
    # Process alerts
    process_diagnostics(db, device.id, diagnostics)
    
    # Build response
    response_data = schemas.ReadingResponse.model_validate(db_reading)
    response_data.diagnostics = diagnostics
    
    return response_data

@router.post("/telemetry/{device_identifier}", response_model=schemas.ReadingResponse, status_code=status.HTTP_201_CREATED)
def ingest_hardware_reading(
    device_identifier: str,
    reading_in: schemas.ReadingCreate,
    db: Session = Depends(get_db),
):
    device = db.query(models.SolarDevice).filter(models.SolarDevice.device_identifier == device_identifier).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db_reading = models.SensorReading(
        **reading_in.model_dump(),
        device_id=device.id
    )
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    
    diagnostics = evaluate_reading(reading_in)
    process_diagnostics(db, device.id, diagnostics)
    
    response_data = schemas.ReadingResponse.model_validate(db_reading)
    response_data.diagnostics = diagnostics
    
    return response_data

@router.get("/{device_id}/readings/latest", response_model=schemas.Reading)
def get_latest_reading(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    device = get_device_if_owner(device_id, db, current_user)
    
    reading = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.device_id == device_id)
        .order_by(models.SensorReading.timestamp.desc())
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="No readings found for this device")
    return reading

@router.get("/{device_id}/readings/history", response_model=List[schemas.Reading])
def get_readings_history(
    device_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    device = get_device_if_owner(device_id, db, current_user)
    
    readings = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.device_id == device_id)
        .order_by(models.SensorReading.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return readings
