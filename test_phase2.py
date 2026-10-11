from fastapi.testclient import TestClient
from app.main import app
import pytest
import uuid
import time

client = TestClient(app)

def create_test_user_and_token():
    email = f"test_{uuid.uuid4()}@example.com"
    password = "strongpassword123"
    client.post("/api/auth/register", json={"email": email, "password": password})
    token = client.post("/api/auth/login", data={"username": email, "password": password}).json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}

def create_test_device(headers):
    device_id = f"device_{uuid.uuid4()}"
    res = client.post("/api/devices", json={"device_identifier": device_id, "name": "Test Device"}, headers=headers)
    return res.json()["id"]

def test_diagnostic_engine_normal():
    from app.core.diagnostics import evaluate_reading
    from app.schemas.reading import ReadingBase
    
    reading = ReadingBase(voltage=12.0, current=25.0)
    results = evaluate_reading(reading)
    assert len(results) == 1
    assert results[0].condition.value == "NORMAL_OPERATION"

def test_diagnostic_engine_critical_low_voltage():
    from app.core.diagnostics import evaluate_reading
    from app.schemas.reading import ReadingBase
    
    reading = ReadingBase(voltage=10.0, current=25.0)
    results = evaluate_reading(reading)
    assert any(r.condition.value == "CRITICAL_LOW_VOLTAGE" for r in results)

def test_reading_submission_generates_alerts():
    token, headers = create_test_user_and_token()
    db_id = create_test_device(headers)
    
    # Submit critical low voltage reading
    res = client.post(f"/api/devices/{db_id}/readings", json={"voltage": 10.0, "current": 25.0}, headers=headers)
    assert res.status_code == 201
    
    # Check that alert was created
    alerts_res = client.get("/api/alerts", headers=headers)
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1
    assert any(a["condition"] == "CRITICAL_LOW_VOLTAGE" and a["device_id"] == db_id for a in alerts)

def test_alert_deduplication():
    token, headers = create_test_user_and_token()
    db_id = create_test_device(headers)
    
    # Submit first bad reading
    client.post(f"/api/devices/{db_id}/readings", json={"voltage": 10.0, "current": 25.0}, headers=headers)
    
    # Submit second identical bad reading
    client.post(f"/api/devices/{db_id}/readings", json={"voltage": 10.1, "current": 25.0}, headers=headers)
    
    # Check alerts, should only be one ACTIVE critical low voltage
    alerts_res = client.get("/api/alerts", headers=headers)
    alerts = [a for a in alerts_res.json() if a["condition"] == "CRITICAL_LOW_VOLTAGE" and a["device_id"] == db_id]
    assert len(alerts) == 1

def test_alert_resolution():
    token, headers = create_test_user_and_token()
    db_id = create_test_device(headers)
    
    # Submit bad reading
    client.post(f"/api/devices/{db_id}/readings", json={"voltage": 10.0, "current": 25.0}, headers=headers)
    
    # Submit normal reading
    client.post(f"/api/devices/{db_id}/readings", json={"voltage": 12.0, "current": 25.0}, headers=headers)
    
    # Check active alerts, should be empty for this device
    alerts_res = client.get("/api/alerts", headers=headers)
    alerts = [a for a in alerts_res.json() if a["device_id"] == db_id]
    assert len(alerts) == 0
    
    # Check history
    history_res = client.get("/api/alerts/history", headers=headers)
    history = [a for a in history_res.json() if a["device_id"] == db_id]
    assert len(history) == 1
    assert history[0]["status"] == "RESOLVED"

def test_simulation_mode():
    token, headers = create_test_user_and_token()
    db_id = create_test_device(headers)
    
    # Run simulation
    res = client.post(f"/api/devices/{db_id}/simulate", json={"voltage": 9.0, "current": 0.2}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "DEMO"
    assert data["simulated"] is True
    assert len(data["diagnostics"]) >= 2 # Should have both critical voltage and current
    
    # Ensure it wasn't saved to DB
    alerts_res = client.get("/api/alerts", headers=headers)
    alerts = [a for a in alerts_res.json() if a["device_id"] == db_id]
    assert len(alerts) == 0

def test_alert_authorization():
    token1, headers1 = create_test_user_and_token()
    db_id1 = create_test_device(headers1)
    client.post(f"/api/devices/{db_id1}/readings", json={"voltage": 10.0, "current": 25.0}, headers=headers1)
    
    alerts_res1 = client.get("/api/alerts", headers=headers1)
    alert_id = alerts_res1.json()[0]["id"]
    
    token2, headers2 = create_test_user_and_token()
    
    # User 2 tries to get User 1's alert
    res = client.get(f"/api/alerts/{alert_id}", headers=headers2)
    assert res.status_code == 404
    
    # User 2 tries to acknowledge User 1's alert
    res = client.patch(f"/api/alerts/{alert_id}/acknowledge", headers=headers2)
    assert res.status_code == 404
    
    # User 1 acknowledges own alert
    res = client.patch(f"/api/alerts/{alert_id}/acknowledge", headers=headers1)
    assert res.status_code == 200
    assert res.json()["status"] == "ACKNOWLEDGED"

def test_device_diagnostics_endpoint():
    token, headers = create_test_user_and_token()
    db_id = create_test_device(headers)
    
    # Initially no readings
    res = client.get(f"/api/devices/{db_id}/diagnostics", headers=headers)
    assert res.status_code == 404
    
    # Submit bad reading
    client.post(f"/api/devices/{db_id}/readings", json={"voltage": 10.0, "current": 25.0}, headers=headers)
    
    # Check diagnostics
    res = client.get(f"/api/devices/{db_id}/diagnostics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["condition"] == "CRITICAL_LOW_VOLTAGE"
