import pytest
from types import SimpleNamespace
from datetime import datetime, timezone
from app.services.assistant_conversation import conversational_reply
from app.api.endpoints.chat import _get_smart_reply

@pytest.fixture
def test_device():
    return SimpleNamespace(id=1, name="Solar Inverter 1", device_identifier="ESP32_01")

@pytest.fixture
def healthy_reading():
    return SimpleNamespace(voltage=12.8, current=1.5, timestamp=datetime.now(timezone.utc))

@pytest.fixture
def critical_alert():
    return SimpleNamespace(
        title="Critical High Voltage",
        severity="CRITICAL",
        message="Critical high voltage detected.",
        recommended_solution="Check charge controller immediately.",
        measured_value=19.5,
        threshold_value=18.0,
    )

def test_greeting_replies(test_device, healthy_reading):
    greetings = ["hy", "Hy", "hi", "Hi there", "hello", "good morning", "good afternoon", "good evening"]
    for g in greetings:
        reply = conversational_reply(g, test_device, healthy_reading, [])
        assert reply is not None
        assert "SolarGuard" in reply

def test_are_solar_panels_okay(test_device, healthy_reading):
    queries = [
        "are the solar panels okay",
        "Are the solar panels okay?",
        "is the solar panel okay?",
        "are my panels working?",
        "how are my solar panels",
    ]
    for q in queries:
        reply = conversational_reply(q, test_device, healthy_reading, [])
        assert reply is not None
        assert "solar panels" in reply.lower() or "panels" in reply.lower()
        assert "12.80 V" in reply or "healthy" in reply.lower() or "okay" in reply.lower()

def test_battery_queries(test_device, healthy_reading):
    reply = conversational_reply("is my battery healthy?", test_device, healthy_reading, [])
    assert reply is not None
    assert "battery" in reply.lower()

def test_appliance_queries(test_device, healthy_reading):
    fridge_reply = conversational_reply("can I run my fridge?", test_device, healthy_reading, [])
    assert fridge_reply is not None
    assert "fridge" in fridge_reply.lower()

    phone_reply = conversational_reply("can I charge my phone?", test_device, healthy_reading, [])
    assert phone_reply is not None
    assert "phone" in phone_reply.lower()

def test_fault_awareness(test_device, critical_alert):
    fault_reading = SimpleNamespace(voltage=19.5, current=0.1, timestamp=datetime.now(timezone.utc))
    reply = _get_smart_reply("are the solar panels okay?", test_device, fault_reading, [critical_alert])
    assert "No, the panels need attention right now" in reply or "critical" in reply.lower()
