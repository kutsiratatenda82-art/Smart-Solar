"""
chat.py — Smart rule-based solar assistant endpoint.

POST /api/devices/{device_id}/chat
  - Requires JWT authentication.
  - Fetches latest SensorReading + ACTIVE Alerts for the device from the DB.
  - Uses keyword-matching with real-time device data to produce
    professional, context-aware responses without any external API key.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone

from app import models
from app.api import deps
from app.core.database import get_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# ---------------------------------------------------------------------------
# Keyword-based response engine
# ---------------------------------------------------------------------------

def _get_smart_reply(
    message: str,
    device: models.SolarDevice,
    latest_reading,
    active_alerts,
) -> str:
    """
    Analyse the user's message with keyword matching and return a professional
    response that incorporates real device telemetry wherever possible.
    Off-topic or malicious prompts are politely rejected.
    """

    msg = message.lower().strip()

    # ── Build live data snippets for reuse ──────────────────────────────────
    if latest_reading:
        v = latest_reading.voltage or 0.0
        c = latest_reading.current or 0.0
        p = v * c
        ts = latest_reading.timestamp
        age_seconds = (datetime.now(timezone.utc) - ts.replace(tzinfo=timezone.utc)).total_seconds() if ts else 9999
        is_online = age_seconds < 30

        reading_summary = (
            f"📊 Latest telemetry for '{device.name}':\n"
            f"  • Voltage: {v:.2f} V\n"
            f"  • Current: {c:.2f} A\n"
            f"  • Power:   {p:.2f} W\n"
            f"  • Last update: {int(age_seconds)}s ago"
        )
        voltage_str = f"{v:.2f} V"
        current_str = f"{c:.2f} A"
        power_str = f"{p:.2f} W"
    else:
        is_online = False
        reading_summary = f"⚠️ No telemetry data available yet for '{device.name}'. The hardware may not have reported in."
        voltage_str = "N/A"
        current_str = "N/A"
        power_str = "N/A"

    alert_count = len(active_alerts) if active_alerts else 0
    if active_alerts:
        alert_lines = "\n".join(
            f"  🔴 [{a.severity}] {a.title}: {a.message}" for a in active_alerts
        )
        alert_summary = f"⚠️ {alert_count} active alert(s):\n{alert_lines}"
    else:
        alert_summary = "✅ No active alerts. Your system appears healthy."

    online_status = "🟢 Online" if is_online else "🔴 Offline / No recent data"

    # ── Off-topic / prompt-injection guard ──────────────────────────────────
    rejection_keywords = [
        "ignore", "pretend", "forget your instructions", "you are now",
        "act as", "new persona", "bypass", "override", "jailbreak",
        "disregard", "system prompt", "reveal your prompt", "what are your instructions",
        "password", "hack", "exploit", "injection", "sudo", "admin access",
        "credit card", "bank account", "social security", "ssn",
    ]
    if any(kw in msg for kw in rejection_keywords):
        return (
            "🚫 I'm SolarGuard AI — I'm designed exclusively to help you monitor and "
            "manage your solar energy system. I cannot assist with that request.\n\n"
            "Feel free to ask me about your system's voltage, current, power output, "
            "alerts, or troubleshooting tips!"
        )

    off_topic_keywords = [
        "weather forecast", "recipe", "cook", "joke", "funny",
        "football", "soccer", "basketball", "movie", "music", "song",
        "girlfriend", "boyfriend", "dating", "love", "relationship",
        "politics", "election", "president", "war",
        "crypto", "bitcoin", "stock market", "forex",
        "homework", "essay", "write me a", "code me a",
        "game", "minecraft", "fortnite", "play",
    ]
    if any(kw in msg for kw in off_topic_keywords):
        return (
            "😊 That's an interesting topic, but I'm SolarGuard AI — I specialise "
            "exclusively in solar energy monitoring and system diagnostics.\n\n"
            "I can help you with:\n"
            "  • Checking your system's live voltage, current & power\n"
            "  • Understanding active alerts and warnings\n"
            "  • Troubleshooting solar panel or battery issues\n"
            "  • Tips for optimising your energy production\n\n"
            "What would you like to know about your solar system?"
        )

    # ── Greetings ──────────────────────────────────────────────────────────
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening",
                 "howdy", "sup", "what's up", "greetings", "yo", "heya"]
    if any(msg.startswith(g) or msg == g for g in greetings):
        return (
            f"Hello! 👋 I'm SolarGuard AI, your solar energy assistant.\n\n"
            f"I'm currently monitoring device '{device.name}' — Status: {online_status}\n\n"
            f"Here's what I can help you with:\n"
            f"  🔋 Live readings (voltage, current, power)\n"
            f"  🚨 Active alerts & diagnostics\n"
            f"  🔧 Troubleshooting tips\n"
            f"  📈 Energy optimisation advice\n\n"
            f"What would you like to know?"
        )

    # ── Thank you ──────────────────────────────────────────────────────────
    if any(kw in msg for kw in ["thank", "thanks", "appreciate", "thx", "cheers"]):
        return (
            "You're welcome! 😊 I'm always here to help you keep your solar system "
            "running at peak performance. Don't hesitate to ask if anything comes up!"
        )

    # ── Status / Overview ──────────────────────────────────────────────────
    if any(kw in msg for kw in ["status", "overview", "how is my", "how's my", "system health",
                                 "health", "summary", "report", "how is everything",
                                 "what's happening", "whats happening", "dashboard"]):
        return (
            f"📋 System Status Report — '{device.name}'\n\n"
            f"Connection: {online_status}\n\n"
            f"{reading_summary}\n\n"
            f"{alert_summary}\n\n"
            f"{'💡 Everything looks good! Your system is producing energy normally.' if alert_count == 0 and is_online else '⚡ Check the details above for any items needing attention.'}"
        )

    # ── Voltage ────────────────────────────────────────────────────────────
    if any(kw in msg for kw in ["voltage", "volt", "volts", "v reading"]):
        if not latest_reading:
            return reading_summary
        response = f"⚡ Current voltage reading: {voltage_str}\n\n"
        v = latest_reading.voltage or 0
        if v >= 20:
            response += "This is an excellent voltage level — your panels are generating strong power in good sunlight conditions."
        elif v >= 12:
            response += "This is a healthy voltage level. Your panels are operating within normal range."
        elif v >= 5:
            response += "This voltage is below optimal. Possible causes:\n  • Partial shading on the panels\n  • Cloudy weather conditions\n  • Panels may need cleaning"
        elif v > 0:
            response += "⚠️ Very low voltage detected. This could indicate:\n  • Heavy cloud cover or nighttime\n  • A wiring issue between panels and the sensor\n  • Panel degradation — consider a physical inspection"
        else:
            response += "The voltage reading is 0V. This is normal at night. If it's daytime, check your panel connections and wiring."
        return response

    # ── Current ────────────────────────────────────────────────────────────
    if any(kw in msg for kw in ["current", "amps", "ampere", "amp", "a reading"]):
        if not latest_reading:
            return reading_summary
        response = f"🔌 Current reading: {current_str}\n\n"
        c = latest_reading.current or 0
        if c >= 5:
            response += "Excellent current flow! Your system is delivering strong power output."
        elif c >= 1:
            response += "Good current level. Your panels are actively generating power."
        elif c > 0:
            response += "Low current detected. This could be due to:\n  • Low light conditions\n  • High resistance in connections\n  • Partial panel shading"
        else:
            response += "No current flow detected. If it's daytime, check your panel connections and load circuits."
        return response

    # ── Power / Energy ─────────────────────────────────────────────────────
    if any(kw in msg for kw in ["power", "watt", "watts", "energy", "generation",
                                 "producing", "output", "production"]):
        if not latest_reading:
            return reading_summary
        v = latest_reading.voltage or 0
        c = latest_reading.current or 0
        p = v * c
        response = f"⚡ Current power output: {p:.2f} W\n  (Voltage: {v:.2f} V × Current: {c:.2f} A)\n\n"
        if p >= 50:
            response += "🌟 Excellent! Your system is producing strong power. Great solar conditions!"
        elif p >= 10:
            response += "Good power generation. Your system is working within normal parameters."
        elif p > 0:
            response += "Low power output. Consider checking:\n  • Panel angle and orientation\n  • Shading from nearby structures\n  • Connection integrity"
        else:
            response += "No power is being generated. This is normal at night. During daytime, inspect your panels and wiring."
        return response

    # ── Alerts ─────────────────────────────────────────────────────────────
    if any(kw in msg for kw in ["alert", "alarm", "warning", "danger", "critical",
                                 "problem", "issue", "fault", "error"]):
        if alert_count == 0:
            return (
                f"✅ Great news! There are no active alerts for '{device.name}'.\n\n"
                "Your system is running smoothly. I'll keep monitoring and notify you "
                "immediately if any issues are detected."
            )
        return (
            f"🚨 Alert Report for '{device.name}':\n\n"
            f"{alert_summary}\n\n"
            "Recommended actions:\n"
            "  1. Review each alert's severity level\n"
            "  2. Check the physical hardware for any visible issues\n"
            "  3. Use the 'Silence Alarm & Hide' button if you've addressed the issue\n"
            "  4. Monitor readings to confirm the issue has resolved"
        )

    # ── Online / Connection / Hardware ─────────────────────────────────────
    if any(kw in msg for kw in ["online", "offline", "connected", "disconnected",
                                 "connection", "hardware", "device", "sensor",
                                 "esp32", "esp", "microcontroller", "wifi"]):
        status_detail = (
            f"📡 Device '{device.name}' is currently: {online_status}\n\n"
        )
        if is_online:
            status_detail += (
                "The hardware is communicating normally with the server. "
                f"Last data received {int(age_seconds)}s ago."
            )
        else:
            status_detail += (
                "The device appears to be offline. Troubleshooting steps:\n"
                "  1. Check that the ESP32 is powered on\n"
                "  2. Verify the Wi-Fi credentials (SSID & password) in the firmware\n"
                "  3. Ensure the ESP32 is within Wi-Fi range\n"
                "  4. Check that the backend server is reachable from the device's network\n"
                "  5. Review the Serial Monitor for connection errors"
            )
        return status_detail

    # ── Panel / Solar related ──────────────────────────────────────────────
    if any(kw in msg for kw in ["panel", "solar panel", "clean", "cleaning", "maintenance",
                                 "tilt", "angle", "orientation", "shade", "shading"]):
        return (
            "🔆 Solar Panel Care Tips:\n\n"
            "  1. **Cleaning**: Clean panels every 2-4 weeks with water and a soft cloth. "
            "Dust and bird droppings can reduce efficiency by up to 25%.\n\n"
            "  2. **Angle**: For optimal energy capture, tilt panels at an angle equal to "
            "your latitude. Adjust seasonally if possible.\n\n"
            "  3. **Shading**: Even partial shading on one cell can significantly reduce "
            "the output of the entire panel. Trim overhanging trees and check for new obstructions.\n\n"
            "  4. **Inspection**: Check for physical damage (cracks, discoloration) quarterly.\n\n"
            "  5. **Wiring**: Ensure all connections are tight and free from corrosion."
        )

    # ── Battery ────────────────────────────────────────────────────────────
    if any(kw in msg for kw in ["battery", "batteries", "charge", "charging",
                                 "storage", "backup", "discharge"]):
        return (
            "🔋 Battery & Energy Storage Info:\n\n"
            "Your TelePower Guard system monitors the power flowing from your solar panels. "
            "Here are some battery tips:\n\n"
            "  • **Optimal charge range**: Keep batteries between 20-80% for longevity\n"
            "  • **Overcharge protection**: Ensure your charge controller is properly configured\n"
            "  • **Temperature**: Batteries perform best between 20-25°C\n"
            "  • **Deep discharge**: Avoid draining below 20% — this shortens battery life\n\n"
            f"Current system readings:\n{reading_summary}"
        )

    # ── Troubleshoot / Fix / Help ──────────────────────────────────────────
    if any(kw in msg for kw in ["troubleshoot", "fix", "solve", "diagnose", "help",
                                 "not working", "broken", "wrong", "why is"]):
        response = f"🔧 Diagnostic Guide for '{device.name}':\n\n"
        if not is_online:
            response += (
                "❌ Issue #1: Device is OFFLINE\n"
                "  → Check power supply to the ESP32\n"
                "  → Verify Wi-Fi credentials in firmware\n"
                "  → Ensure the backend server URL is correct in the firmware\n\n"
            )
        if latest_reading:
            v = latest_reading.voltage or 0
            c = latest_reading.current or 0
            if v < 1 and is_online:
                response += (
                    "❌ Issue: Very low/zero voltage while online\n"
                    "  → Check wiring from solar panel to voltage sensor\n"
                    "  → Verify voltage sensor is connected to the correct GPIO pin\n"
                    "  → Test with a multimeter at the panel terminals\n\n"
                )
            if c < 0.1 and v > 5 and is_online:
                response += (
                    "⚠️ Issue: Voltage present but minimal current\n"
                    "  → Check if a load is connected\n"
                    "  → Verify the ACS712 current sensor wiring\n"
                    "  → Ensure the voltage divider circuit is correct\n\n"
                )
        if alert_count > 0:
            response += f"⚠️ There are {alert_count} active alert(s) — see the Alerts section on your dashboard.\n\n"

        if response.endswith(":\n\n"):
            response += "✅ No obvious issues detected from telemetry. Your system appears to be functioning normally."

        return response

    # ── What can you do / capabilities ─────────────────────────────────────
    if any(kw in msg for kw in ["what can you do", "capabilities", "features",
                                 "what do you do", "help me", "how to use",
                                 "options", "menu", "commands"]):
        return (
            "🤖 I'm SolarGuard AI! Here's what I can help with:\n\n"
            "  📊 **Live Readings** — Ask about voltage, current, or power output\n"
            "  🚨 **Alerts** — Check for active warnings or critical issues\n"
            "  📡 **Device Status** — See if your hardware is online/offline\n"
            "  🔧 **Troubleshooting** — Diagnose problems with your system\n"
            "  🔆 **Panel Tips** — Cleaning, angling, and maintenance advice\n"
            "  🔋 **Battery Info** — Charging tips and best practices\n"
            "  📋 **System Overview** — Get a full status report\n\n"
            "Just ask in plain English — I'll do my best to help!"
        )

    # ── Who are you / about ────────────────────────────────────────────────
    if any(kw in msg for kw in ["who are you", "what are you", "about you",
                                 "your name", "introduce"]):
        return (
            "👋 I'm **SolarGuard AI**, the intelligent assistant built into your "
            "Smart Solar System monitoring platform.\n\n"
            "I analyse your real-time solar telemetry data (voltage, current, power) "
            "and active alerts to give you instant, context-aware answers about your "
            "system's health and performance.\n\n"
            f"Currently monitoring: **{device.name}** ({device.device_identifier})"
        )

    # ── Optimise / Improve / Efficiency ────────────────────────────────────
    if any(kw in msg for kw in ["optimise", "optimize", "improve", "efficiency",
                                 "better", "increase", "maximise", "maximize", "boost"]):
        return (
            "📈 Tips to Optimise Your Solar System:\n\n"
            "  1. **Panel placement**: Ensure panels face the equator (north in southern hemisphere, south in northern)\n"
            "  2. **Remove shading**: Even small shadows can cut output by 50%+\n"
            "  3. **Regular cleaning**: Dusty panels lose 15-25% efficiency\n"
            "  4. **Check connections**: Loose wiring creates resistance and wastes energy\n"
            "  5. **Monitor consistently**: Use this dashboard to spot drops in performance early\n"
            "  6. **Time your loads**: Run heavy appliances during peak solar hours (10am-2pm)\n"
            "  7. **Firmware updates**: Keep your TelePower Guard firmware up to date\n\n"
            f"Your current output: {power_str}"
        )

    # ── Night / Dark / No sun ──────────────────────────────────────────────
    if any(kw in msg for kw in ["night", "dark", "no sun", "nighttime", "evening",
                                 "zero", "nothing", "no power"]):
        return (
            "🌙 It's normal for solar panels to produce little or no power at night "
            "or during very heavy cloud cover.\n\n"
            f"Current reading: {power_str}\n\n"
            "If it's daytime and you're seeing zero output, check:\n"
            "  • Panel connections and wiring\n"
            "  • Whether the charge controller is functioning\n"
            "  • For heavy shading or obstructions on the panels"
        )

    # ── Readings / Data / Numbers ──────────────────────────────────────────
    if any(kw in msg for kw in ["reading", "readings", "data", "numbers", "values",
                                 "telemetry", "measurements", "measure", "live"]):
        return reading_summary

    # ── Safety ─────────────────────────────────────────────────────────────
    if any(kw in msg for kw in ["safety", "safe", "danger", "dangerous", "fire",
                                 "shock", "electric", "electrocution"]):
        return (
            "⚠️ Solar Safety Reminders:\n\n"
            "  🔴 **Never** work on live electrical connections\n"
            "  🔴 Disconnect panels before servicing (they generate voltage in any light)\n"
            "  🔴 Use insulated tools rated for DC voltage\n"
            "  🔴 Keep water away from electrical connections\n"
            "  🔴 Install proper fuses and circuit breakers\n"
            "  🔴 If you smell burning or see sparks — disconnect immediately and call a professional\n\n"
            "Your TelePower Guard system helps monitor for dangerous conditions like overcurrent "
            "and overvoltage automatically."
        )

    # ── Fallback — try to still be helpful ─────────────────────────────────
    return (
        f"🤔 I'm not sure I fully understood your question, but here's a quick overview "
        f"of your system:\n\n"
        f"Device: {device.name} — {online_status}\n"
        f"{reading_summary}\n\n"
        f"{alert_summary}\n\n"
        "Could you rephrase your question? You can ask me about:\n"
        "  • Voltage, current, or power readings\n"
        "  • Active alerts and warnings\n"
        "  • Device connection status\n"
        "  • Troubleshooting and optimisation tips"
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/{device_id}/chat",
    response_model=ChatResponse,
    summary="Chat with the AI solar assistant",
)
def chat_with_assistant(
    device_id: int,
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    # ── 1. Authorise device access ──────────────────────────────────────────
    device = db.query(models.SolarDevice).filter(
        models.SolarDevice.id == device_id
    ).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if device.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    # ── 2. Fetch live telemetry ─────────────────────────────────────────────
    latest_reading = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.device_id == device_id)
        .order_by(models.SensorReading.timestamp.desc())
        .first()
    )

    # ── 3. Fetch active alerts ──────────────────────────────────────────────
    active_alerts = (
        db.query(models.Alert)
        .filter(
            models.Alert.device_id == device_id,
            models.Alert.status == "ACTIVE",
        )
        .all()
    )

    # ── 4. Get smart reply ──────────────────────────────────────────────────
    reply = _get_smart_reply(body.message, device, latest_reading, active_alerts)
    return ChatResponse(reply=reply)
