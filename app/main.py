from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine, SessionLocal
from app import models
from app.core.security import get_password_hash
from app.api.endpoints import auth, devices, readings, health, alerts, chat

logger = logging.getLogger("uvicorn.info")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all tables exist on startup (especially on first Render deployment)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
        
        # Auto-seed default admin account & kutsira device for hardware plug-and-play
        db = SessionLocal()
        try:
            admin = db.query(models.User).filter(models.User.email == "admin@solar.com").first()
            if not admin:
                admin = models.User(
                    name="Admin User",
                    email="admin@solar.com",
                    hashed_password=get_password_hash("admin123"),
                    role="admin",
                    is_active=True,
                )
                db.add(admin)
                db.commit()
                db.refresh(admin)
                logger.info("Created default admin user: admin@solar.com (password: admin123)")
            
            kutsira = db.query(models.SolarDevice).filter(models.SolarDevice.device_identifier == "kutsira").first()
            if not kutsira:
                kutsira = models.SolarDevice(
                    device_identifier="kutsira",
                    name="TelePower Guard (Kutsira)",
                    owner_id=admin.id,
                    status="active",
                )
                db.add(kutsira)
                db.commit()
                logger.info("Auto-registered hardware device 'kutsira' for default admin.")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during startup database init: {e}")
    yield

app = FastAPI(
    title="Smart Solar Alert",
    description="Backend Foundation for Smart Solar Alert system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(readings.router, prefix="/api/devices", tags=["readings"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(chat.router, prefix="/api/devices", tags=["chat"])

@app.get("/")
def root():
    return {"message": "Welcome to Smart Solar Alert API"}
