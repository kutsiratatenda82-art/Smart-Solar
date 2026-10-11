from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, Base, engine
import pytest
import uuid

# Recreate the database tables for a clean start
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"

def test_user_registration():
    email = f"test_{uuid.uuid4()}@example.com"
    response = client.post("/api/auth/register", json={
        "email": email,
        "password": "strongpassword123",
        "name": "Test User"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert "hashed_password" not in data # Passwords should not be returned in API response

    # Try registering again
    response = client.post("/api/auth/register", json={
        "email": email,
        "password": "strongpassword123",
        "name": "Test User"
    })
    assert response.status_code == 400

def test_user_login():
    email = f"test_{uuid.uuid4()}@example.com"
    password = "strongpassword123"
    client.post("/api/auth/register", json={"email": email, "password": password, "name": "Test User"})
    
    response = client.post("/api/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_auth_me():
    email = f"test_{uuid.uuid4()}@example.com"
    password = "strongpassword123"
    client.post("/api/auth/register", json={"email": email, "password": password, "name": "Test User"})
    token = client.post("/api/auth/login", data={"username": email, "password": password}).json()["access_token"]
    
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == email

def test_unauthorized_access():
    response = client.get("/api/auth/me")
    assert response.status_code == 401

def test_device_creation_and_listing():
    email = f"test_{uuid.uuid4()}@example.com"
    password = "strongpassword123"
    client.post("/api/auth/register", json={"email": email, "password": password, "name": "Test User"})
    token = client.post("/api/auth/login", data={"username": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    device_id = f"device_{uuid.uuid4()}"
    response = client.post("/api/devices", json={"device_identifier": device_id, "name": "Main Panel"}, headers=headers)
    assert response.status_code == 201
    
    response = client.get("/api/devices", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["device_identifier"] == device_id

def test_device_authorization_boundaries():
    email1 = f"test_{uuid.uuid4()}@example.com"
    email2 = f"test_{uuid.uuid4()}@example.com"
    password = "strongpassword123"
    
    client.post("/api/auth/register", json={"email": email1, "password": password})
    token1 = client.post("/api/auth/login", data={"username": email1, "password": password}).json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    client.post("/api/auth/register", json={"email": email2, "password": password})
    token2 = client.post("/api/auth/login", data={"username": email2, "password": password}).json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    device_id = f"device_{uuid.uuid4()}"
    res = client.post("/api/devices", json={"device_identifier": device_id, "name": "Main Panel"}, headers=headers1)
    db_id = res.json()["id"]
    
    # User 1 should access
    assert client.get(f"/api/devices/{db_id}", headers=headers1).status_code == 200
    
    # User 2 should NOT access
    assert client.get(f"/api/devices/{db_id}", headers=headers2).status_code == 403

def test_sensor_readings():
    email = f"test_{uuid.uuid4()}@example.com"
    password = "strongpassword123"
    client.post("/api/auth/register", json={"email": email, "password": password})
    token = client.post("/api/auth/login", data={"username": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    device_id = f"device_{uuid.uuid4()}"
    res = client.post("/api/devices", json={"device_identifier": device_id, "name": "Main Panel"}, headers=headers)
    db_id = res.json()["id"]
    
    # Valid reading
    res = client.post(f"/api/devices/{db_id}/readings", json={"voltage": 12.5, "current": 2.5}, headers=headers)
    assert res.status_code == 201
    
    # Invalid reading
    res = client.post(f"/api/devices/{db_id}/readings", json={"voltage": "invalid", "temperature": 25.0}, headers=headers)
    assert res.status_code == 422
    
    # Latest reading
    res = client.get(f"/api/devices/{db_id}/readings/latest", headers=headers)
    assert res.status_code == 200
    assert res.json()["voltage"] == 12.5
    
    # Reading history
    res = client.get(f"/api/devices/{db_id}/readings/history", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

def test_password_hashing():
    from app.core.database import SessionLocal
    from app.models import User
    
    email = f"test_{uuid.uuid4()}@example.com"
    password = "strongpassword123"
    client.post("/api/auth/register", json={"email": email, "password": password})
    
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()
    
    assert user is not None
    assert user.hashed_password != password
    assert user.hashed_password.startswith("$2b$") # bcrypt hash prefix

