from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("solar_devices.id"), nullable=False, index=True)
    condition = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    recommended_solution = Column(String, nullable=False)
    measured_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=True)
    status = Column(String, default="ACTIVE", index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    device = relationship("SolarDevice", backref="alerts")
