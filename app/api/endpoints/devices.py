from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core.database import get_db
from app.core.diagnostics import evaluate_reading
from typing import List

router = APIRouter()

@router.post("", response_model=schemas.Device, status_code=status.HTTP_201_CREATED)
def create_device(
    device_in: schemas.DeviceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    device = db.query(models.SolarDevice).filter(models.SolarDevice.device_identifier == device_in.device_identifier).first()
    if device:
        raise HTTPException(
            status_code=400,
            detail="The device with this identifier already exists in the system.",
        )
    db_device = models.SolarDevice(
        **device_in.model_dump(),
        owner_id=current_user.id
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@router.get("", response_model=List[schemas.Device])
def list_devices(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    devices = db.query(models.SolarDevice).filter(models.SolarDevice.owner_id == current_user.id).all()
    return devices

@router.get("/{device_id}", response_model=schemas.Device)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    device = db.query(models.SolarDevice).filter(models.SolarDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return device

@router.get("/{device_id}/diagnostics", response_model=List[schemas.DiagnosticResult])
def get_device_diagnostics(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    device = db.query(models.SolarDevice).filter(models.SolarDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    latest_reading = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.device_id == device_id)
        .order_by(models.SensorReading.timestamp.desc())
        .first()
    )
    
    if not latest_reading:
        raise HTTPException(status_code=404, detail="No readings available to diagnose")
        
    reading_base = schemas.ReadingBase(voltage=latest_reading.voltage, current=latest_reading.current)
    diagnostics = evaluate_reading(reading_base)
    return diagnostics

@router.post("/{device_id}/simulate", response_model=schemas.SimulationResult)
def simulate_device_reading(
    device_id: int,
    reading_in: schemas.ReadingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    device = db.query(models.SolarDevice).filter(models.SolarDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    diagnostics = evaluate_reading(reading_in)
    
    return schemas.SimulationResult(
        mode="DEMO",
        simulated=True,
        diagnostics=diagnostics
    )

