from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SolarDevice(Base):
    __tablename__ = "solar_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_identifier = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="devices")
    readings = relationship("SensorReading", back_populates="device", cascade="all, delete-orphan")
