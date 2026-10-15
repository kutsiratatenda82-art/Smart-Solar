"""
assistant_conversation.py — Conversational intent layer for the SolarGuard assistant.

Handles the most common, high-value questions with natural, multi-sentence
answers. Every answer is computed from the device's latest SensorReading and
its ACTIVE alerts, and uses the SAME thresholds as the diagnostic engine
(app/core/diagnostics.py), so the assistant can never contradict the alerts.

Returns None when no intent matches, so the caller can fall back to the
keyword engine in chat.py.
"""

import random
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app import schemas
from app.core.diagnostics import (
    evaluate_reading,
    VOLTAGE_NORMAL_MIN,
    VOLTAGE_NORMAL_MAX,
    VOLTAGE_CRITICAL_LOW,
    VOLTAGE_CRITICAL_HIGH,
    CURRENT_NORMAL_MIN,
    CURRENT_CRITICAL_LOW,
)
from app.schemas.diagnostic import DiagnosticCondition, DiagnosticResult, Severity

# Zimbabwe local time (CAT, UTC+2) — the server itself runs in UTC.
LOCAL_TZ = timezone(timedelta(hours=2))
ONLINE_WINDOW_SECONDS = 30

# Typical running wattage of common household appliances.
APPLIANCE_WATTS = {
    "phone": ("a phone charger", 10),
    "phones": ("a phone charger", 10),
    "bulb": ("an LED bulb", 9),
    "bulbs": ("an LED bulb", 9),
    "light": ("an LED light", 9),
    "lights": ("a set of 4 LED bulbs", 36),
    "radio": ("a radio", 15),
    "router": ("a Wi-Fi router", 12),
    "wifi": ("a Wi-Fi router", 12),
    "laptop": ("a laptop", 60),
    "fan": ("a fan", 50),
    "tv": ("a TV", 80),
    "television": ("a TV", 80),
    "fridge": ("a fridge", 150),
    "refrigerator": ("a fridge", 150),
    "freezer": ("a chest freezer", 200),
    "microwave": ("a microwave", 1000),
    "iron": ("an electric iron", 1000),
    "kettle": ("an electric kettle", 2000),
    "stove": ("an electric stove", 2000),
    "geyser": ("a geyser", 3000),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has(msg: str, *phrases: str) -> bool:
    """Whole-word / whole-phrase match (so 'hi' does not match 'high')."""
    return any(re.search(r"\b" + re.escape(p) + r"\b", msg) for p in phrases)


def _local_now() -> datetime:
    return datetime.now(LOCAL_TZ)


def _part_of_day() -> str:
    h = _local_now().hour
    if h < 12:
        return "morning"
    if h < 17:
        return "afternoon"
    return "evening"


def _is_daylight() -> bool:
    return 6 <= _local_now().hour < 18


def _ago(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s} seconds ago"
    if s < 3600:
        return f"{s // 60} minute{'s' if s // 60 != 1 else ''} ago"
    return f"{s // 3600} hour{'s' if s // 3600 != 1 else ''} ago"


class _Ctx:
    """Snapshot of everything the assistant knows about the device right now."""

    def __init__(self, device, latest_reading, active_alerts):
        self.device = device
        self.name = device.name
        self.alerts = list(active_alerts or [])
        self.has_data = latest_reading is not None
        self.v = self.c = self.p = 0.0
        self.age = 9999.0
        self.diags: List[DiagnosticResult] = []

        if latest_reading is not None:
            self.v = float(latest_reading.voltage or 0.0)
            self.c = float(latest_reading.current or 0.0)
            self.p = self.v * self.c
            ts = latest_reading.timestamp
            if ts is not None:
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                self.age = (datetime.now(timezone.utc) - ts).total_seconds()
            self.diags = evaluate_reading(
                schemas.ReadingBase(voltage=self.v, current=self.c)
            )

        self.online = self.has_data and self.age < ONLINE_WINDOW_SECONDS
        self.issues = [d for d in self.diags if d.condition != DiagnosticCondition.NORMAL_OPERATION]
        self.critical = [d for d in self.issues if d.severity == Severity.CRITICAL]
        self.warnings = [d for d in self.issues if d.severity == Severity.WARNING]

    # Readable one-liners -------------------------------------------------
    def live_line(self) -> str:
        return f"{self.v:.2f} V, {self.c:.2f} A, about {self.p:.1f} W"

    def health_word(self) -> str:
        if not self.has_data:
            return "waiting for its first reading"
        if not self.online:
            return "offline"
        if self.critical:
            return "in a critical state"
        if self.warnings:
            return "running, but with a warning"
        return "healthy"


def _no_data(ctx: _Ctx) -> str:
    return (
        f"I don't have any readings from '{ctx.name}' yet, so I can't give you an honest "
        "assessment. Once the TelePower Guard unit is powered and connected to Wi-Fi it "
        "reports every 5 seconds, and I'll be able to analyse it straight away."
    )


def _offline_note(ctx: _Ctx) -> str:
    return (
        f"One caveat: '{ctx.name}' last reported {_ago(ctx.age)}, so it looks offline. "
        f"The figures below are from that last reading ({ctx.live_line()}), not live data. "
        "Check that the ESP32 is powered and within Wi-Fi range."
    )


# ---------------------------------------------------------------------------
# Intent handlers
# ---------------------------------------------------------------------------

def _greeting(ctx: _Ctx) -> str:
    opener = random.choice([
        f"Good {_part_of_day()}! I'm SolarGuard, your solar monitoring assistant.",
        f"Hi there, good {_part_of_day()}! SolarGuard here.",
        f"Hello! Good {_part_of_day()}. I'm SolarGuard, and I'm watching over your system.",
    ])
    if not ctx.has_data:
        status = f"I'm connected to '{ctx.name}', but it hasn't sent any readings yet."
    elif not ctx.online:
        status = f"I'm connected to '{ctx.name}', but its last reading came in {_ago(ctx.age)}, so it appears to be offline right now."
    elif ctx.critical:
        status = (
            f"I've just checked '{ctx.name}' and I need your attention: {ctx.critical[0].title.lower()} "
            f"is active ({ctx.live_line()}). Ask me \"what should I do?\" and I'll walk you through it."
        )
    elif ctx.warnings:
        status = (
            f"I've just checked '{ctx.name}'. It's running at {ctx.live_line()}, with one thing worth "
            f"keeping an eye on: {ctx.warnings[0].title.lower()}."
        )
    else:
        status = (
            f"I've just checked '{ctx.name}' and everything looks good. It's online and running at "
            f"{ctx.live_line()}, with no active alerts."
        )
    close = random.choice([
        "What would you like to know?",
        "How can I help you today?",
        "Ask me anything about your panels, battery, power or alerts.",
    ])
    return f"{opener}\n\n{status}\n\n{close}"


def _how_are_you(ctx: _Ctx) -> str:
    if not ctx.has_data or not ctx.online:
        return (
            "I'm running fine, thanks for asking! I just wish I could say the same about my "
            f"connection to '{ctx.name}'. I haven't heard from it recently, so I can't vouch "
            "for it at the moment."
        )
    if ctx.issues:
        return (
            "I'm doing well, thank you! Your system needs a bit of attention, though: "
            f"{ctx.issues[0].title.lower()} at the moment. Want me to explain it?"
        )
    return (
        "I'm doing great, thanks for asking! More importantly, so is your system. "
        f"'{ctx.name}' is online at {ctx.live_line()} with no active alerts."
    )


def _panels_health(ctx: _Ctx) -> str:
    if not ctx.has_data:
        return _no_data(ctx)

    parts: List[str] = []
    if not ctx.online:
        parts.append(_offline_note(ctx))

    v, c = ctx.v, ctx.c

    # Voltage analysis — same thresholds as the diagnostic engine.
    if v > VOLTAGE_CRITICAL_HIGH:
        v_ok, v_text = False, (
            f"Voltage is {v:.2f} V, which is above the critical limit of {VOLTAGE_CRITICAL_HIGH:.1f} V. "
            "That usually means the charge controller isn't regulating properly, and it can overcharge the battery."
        )
    elif v > VOLTAGE_NORMAL_MAX:
        v_ok, v_text = False, (
            f"Voltage is {v:.2f} V, slightly above the normal ceiling of {VOLTAGE_NORMAL_MAX:.1f} V. "
            "It isn't dangerous yet, but I'd watch the charge controller."
        )
    elif v < VOLTAGE_CRITICAL_LOW:
        if not _is_daylight():
            v_ok, v_text = True, (
                f"Voltage is low at {v:.2f} V, but it's {_part_of_day()} here, so the panels aren't "
                "getting sunlight. That's completely expected."
            )
        else:
            v_ok, v_text = False, (
                f"Voltage is only {v:.2f} V, below the {VOLTAGE_CRITICAL_LOW:.1f} V minimum, even though it's daytime. "
                "The panels are either heavily shaded, covered, or disconnected."
            )
    else:
        v_ok, v_text = True, (
            f"Voltage is {v:.2f} V, comfortably inside the healthy band of "
            f"{VOLTAGE_NORMAL_MIN:.1f}–{VOLTAGE_NORMAL_MAX:.1f} V, so the panels are receiving light and "
            "producing a stable voltage."
        )

    # Current analysis.
    if c <= CURRENT_CRITICAL_LOW:
        c_ok, c_text = False, (
            f"Current, however, is only {c:.2f} A (critical limit {CURRENT_CRITICAL_LOW:.1f} A). "
            "Almost no energy is flowing, which points to a disconnected load or a broken connection."
        )
    elif c <= CURRENT_NORMAL_MIN:
        c_ok, c_text = False, (
            f"Current is a bit low at {c:.2f} A (expected above {CURRENT_NORMAL_MIN:.1f} A). "
            "Possible causes are partial shading, dust on the panels, or a lighter load than usual."
        )
    else:
        c_ok, c_text = True, (
            f"Current is {c:.2f} A, which is healthy: energy is flowing properly through the system."
        )

    if v_ok and c_ok:
        verdict = random.choice([
            "Yes, your solar panels are okay. ✅",
            "Good news: your panels are working well. ✅",
            "Yes, the panels look healthy right now. ✅",
        ])
        closing = (
            f"Together that's about {ctx.p:.1f} W of power. I'll keep checking every reading and "
            "alert you immediately if anything changes."
        )
    elif v_ok or c_ok:
        verdict = "Mostly, but there's one thing I'd look at. ⚠️"
        closing = "I'd give the panels and wiring a quick visual check. I'll alert you if it gets worse."
    else:
        verdict = "No, the panels need attention right now. 🔴"
        closing = "I recommend a physical inspection of the panels, cables and connectors as soon as it's safe."

    parts.extend([verdict, v_text, c_text, closing])
    return "\n\n".join(parts)


def _battery_health(ctx: _Ctx) -> str:
    if not ctx.has_data:
        return _no_data(ctx)

    v = ctx.v
    prefix = _offline_note(ctx) + "\n\n" if not ctx.online else ""

    if v > VOLTAGE_CRITICAL_HIGH:
        body = (
            f"🔴 I'm concerned. System voltage is {v:.2f} V, above the {VOLTAGE_CRITICAL_HIGH:.1f} V critical "
            "limit. That is an overcharging condition, and over time it can boil a lead-acid battery or "
            "damage a lithium one.\n\nCheck the charge controller immediately, and disconnect the panels if "
            "the voltage doesn't come down."
        )
    elif v < VOLTAGE_CRITICAL_LOW:
        body = (
            f"🔴 System voltage is very low at {v:.2f} V. If this is the battery side, it means a deep "
            "discharge, which is the number one cause of shortened battery life.\n\nI'd switch off "
            "non-essential loads now and let the battery recharge before using it heavily."
        )
    elif v > VOLTAGE_NORMAL_MAX:
        body = (
            f"⚠️ The battery is fine for now, but voltage is slightly high at {v:.2f} V (normal ceiling "
            f"{VOLTAGE_NORMAL_MAX:.1f} V). It's worth checking that the charge controller is "
            "regulating properly."
        )
    else:
        body = (
            f"✅ Your battery looks healthy. System voltage is {v:.2f} V, inside the safe operating band, so "
            "I see no sign of deep discharge or overcharging.\n\nTip: avoid running heavy loads late at night, "
            "and your battery will last noticeably longer."
        )
    return prefix + body


def _what_should_i_do(ctx: _Ctx) -> str:
    if not ctx.has_data:
        return _no_data(ctx)
    if not ctx.online:
        return (
            f"The first step is to get '{ctx.name}' back online. It last reported {_ago(ctx.age)}.\n\n"
            "1. Make sure the ESP32 has power (the blue LED should be blinking).\n"
            "2. Check that the Wi-Fi router or hotspot is on and in range.\n"
            "3. Restart the unit. It reconnects automatically.\n\n"
            "As soon as data starts flowing again I'll re-assess everything."
        )
    if not ctx.issues:
        return random.choice([
            "Nothing at all, right now. 😊 Every reading is within normal limits and there are no "
            f"active alerts. '{ctx.name}' is running at {ctx.live_line()}. Sit back; I'll tell you if that changes.",
            "You don't need to do anything. Your system is operating normally "
            f"({ctx.live_line()}) and there are no active alerts. I'm keeping watch.",
        ])

    lines = ["Here's what I recommend, most urgent first:\n"]
    ordered = ctx.critical + ctx.warnings
    for i, d in enumerate(ordered, 1):
        tag = "🔴 CRITICAL" if d.severity == Severity.CRITICAL else "⚠️ WARNING"
        threshold = f" (limit {d.threshold_value:g})" if d.threshold_value is not None else ""
        lines.append(
            f"{i}. {tag}: {d.title}. Measured {d.measured_value:.2f}{threshold}.\n"
            f"   → {d.recommended_solution}"
        )
    lines.append("\nOnce the readings return to normal, I'll resolve the alert automatically.")
    return "\n".join(lines)


def _explain_alerts(ctx: _Ctx) -> str:
    if not ctx.alerts:
        return (
            f"There are no active alerts on '{ctx.name}' right now. ✅\n\n"
            "For context: I raise an alert whenever a reading crosses a safety threshold, I make sure "
            "you only get one alert per problem (no spam), I close it automatically when readings "
            "recover, and if you acknowledge an alert but the fault is still there two minutes later, "
            "I raise it again so it can't be forgotten."
        )
    lines = [f"You have {len(ctx.alerts)} active alert{'s' if len(ctx.alerts) != 1 else ''}. Here's what each one means:\n"]
    for a in ctx.alerts:
        measured = f"{a.measured_value:.2f}" if a.measured_value is not None else "n/a"
        limit = f"{a.threshold_value:g}" if a.threshold_value is not None else "n/a"
        lines.append(
            f"• {a.title} [{a.severity}]\n"
            f"  What happened: {a.message}\n"
            f"  Evidence: measured {measured} against a limit of {limit}.\n"
            f"  What to do: {a.recommended_solution}"
        )
    return "\n\n".join(lines)


def _why_low(ctx: _Ctx) -> str:
    if not ctx.has_data:
        return _no_data(ctx)
    reasons = []
    if not _is_daylight():
        reasons.append(f"It's {_part_of_day()} in Zimbabwe right now, so low output is normal: there's simply no sun.")
    if ctx.v < VOLTAGE_CRITICAL_LOW and _is_daylight():
        reasons.append(f"Voltage is only {ctx.v:.2f} V in daylight, so the panels are shaded, covered or disconnected.")
    if ctx.c <= CURRENT_NORMAL_MIN:
        reasons.append(f"Current is {ctx.c:.2f} A, below the expected {CURRENT_NORMAL_MIN:.1f} A. Dust, partial shading or a loose connector are the usual suspects.")
    if not reasons:
        return (
            f"Actually, your readings look normal to me: {ctx.live_line()}. If output feels lower than "
            "usual, the most common causes are passing clouds, dust on the panels (which can cost up to "
            "25% efficiency) or new shade from trees or buildings."
        )
    return "Here's my analysis:\n\n" + "\n".join(f"• {r}" for r in reasons) + (
        "\n\nI'd start with a quick visual check of the panels and connectors."
    )


def _power_now(ctx: _Ctx) -> str:
    if not ctx.has_data:
        return _no_data(ctx)
    prefix = _offline_note(ctx) + "\n\n" if not ctx.online else ""
    est_day_wh = ctx.p * 5.5  # Zimbabwe averages ~5.5 peak-sun-hours per day.
    return prefix + (
        f"Right now '{ctx.name}' is producing about {ctx.p:.1f} W ({ctx.v:.2f} V × {ctx.c:.2f} A).\n\n"
        f"If conditions stayed like this through the day, that works out to roughly {est_day_wh:.0f} Wh "
        "of energy, based on Zimbabwe's average of about 5.5 peak-sun-hours. It's a rough estimate, "
        "since output naturally rises towards midday and falls in the afternoon."
    )


def _appliance(ctx: _Ctx, msg: str) -> Optional[str]:
    found = None
    for word, info in APPLIANCE_WATTS.items():
        if _has(msg, word):
            found = info
            break
    if not found:
        return None
    label, watts = found
    if not ctx.has_data:
        return _no_data(ctx)
    p = ctx.p
    head = f"A typical {label.split(' ', 1)[1] if label.startswith(('a ', 'an ')) else label} uses around {watts} W. Your system is generating about {p:.1f} W right now."
    if p >= watts * 1.2:
        verdict = f"✅ Yes, you can run {label} comfortably from solar right now, with about {p - watts:.0f} W to spare."
    elif p >= watts:
        verdict = f"⚠️ Just about. {label[0].upper() + label[1:]} would use almost all of your current solar output, so anything else would come from the battery."
    else:
        verdict = (
            f"❌ Not from solar alone at the moment. {label[0].upper() + label[1:]} needs more than the panels are "
            "producing, so the difference would be drawn from your battery and drain it faster. "
            "Best to run it closer to midday, when output peaks."
        )
    return f"{head}\n\n{verdict}"


def _how_it_works() -> str:
    return (
        "Here's how I keep an eye on your system, step by step:\n\n"
        "1. Sense: the TelePower Guard unit (an ESP32 microcontroller) takes 24 voltage and current samples, "
        "averages them to remove noise, and calculates power as P = V × I.\n\n"
        "2. Transmit: every 5 seconds it sends that reading securely to the cloud server, which is "
        "17,280 readings a day.\n\n"
        "3. Diagnose: each reading goes through the diagnostic engine, which checks it against safety "
        "thresholds and classifies it as Normal, Warning or Critical.\n\n"
        "4. Alert: if something is wrong, an alert is raised with a plain-language explanation and a "
        "recommended fix. Duplicate alerts are suppressed, alerts close automatically when the problem "
        "clears, and an ignored critical fault is raised again after two minutes.\n\n"
        "5. Advise: that's where I come in. I read the same live data and alerts, so I can answer your "
        "questions about your system in plain language."
    )


def _identity(ctx: _Ctx) -> str:
    return (
        "I'm SolarGuard, the assistant built into Smart Solar Alert. 🌞\n\n"
        "I'm not a general-purpose chatbot: I'm purpose-built for solar monitoring. Every answer I give "
        f"comes from your device's actual live readings and alerts (right now I'm watching '{ctx.name}'), "
        "analysed with the same rules the diagnostic engine uses. That means I won't make things up. "
        "If I don't have the data, I'll tell you."
    )


def _creator() -> str:
    return (
        "I was designed and built by Kutsira Tatenda, an Information Technology student at Kwekwe "
        "Polytechnic, as part of the Smart Solar Alert final-year project. The goal: give every "
        "solar owner in Zimbabwe an affordable way to know their system is healthy, and to be warned "
        "before small faults become expensive ones. 🇿🇼"
    )


def _thanks() -> str:
    return random.choice([
        "You're very welcome! I'll keep watching your system around the clock. 😊",
        "Anytime! If anything changes I'll let you know straight away.",
        "My pleasure. That's what I'm here for. ☀️",
    ])


def _goodbye(ctx: _Ctx) -> str:
    tail = "Everything looks good as you leave. 👋" if ctx.online and not ctx.issues else "I'll keep an eye on things while you're away. 👋"
    return f"Goodbye! I'll keep monitoring '{ctx.name}' and alert you the moment anything needs attention. {tail}"


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

_GREETING_RE = re.compile(
    r"^(hi+|hy+|hie|hiya|hello+|helo|hey+|heya|howdy|greetings|good (morning|afternoon|evening|day)|morning|afternoon|evening)\b"
)


def conversational_reply(message: str, device, latest_reading, active_alerts) -> Optional[str]:
    """Return a natural-language reply for recognised intents, or None."""
    msg = re.sub(r"\s+", " ", message.lower().strip())
    msg_clean = re.sub(r"[^\w\s']", " ", msg).strip()
    words = msg_clean.split()
    ctx = _Ctx(device, latest_reading, active_alerts)

    is_greeting = bool(_GREETING_RE.match(msg_clean))
    filler = {"there", "solarguard", "solar", "guard", "bot", "assistant", "friend", "team", "sir", "again", "everyone", "all"}

    # 1. Pure greeting ("hi", "hy", "hello there", "good morning SolarGuard")
    if is_greeting and all(
        w in filler or _GREETING_RE.match(w) or w in {"good", "morning", "afternoon", "evening", "day"}
        for w in words
    ):
        return _greeting(ctx)

    # 2. How are you
    if _has(msg_clean, "how are you", "how are u", "how r u", "how you doing", "how's it going", "hows it going"):
        return _how_are_you(ctx)

    # 3. Who built / identity
    if _has(msg_clean, "who made you", "who built you", "who created you", "who developed you",
            "who designed you", "who programmed you", "who is your creator", "who owns you"):
        return _creator()
    if _has(msg_clean, "are you an ai", "are you ai", "are you real", "are you a robot", "are you human",
            "what model", "chatgpt", "gemini", "are you a bot", "who are you", "what are you",
            "your name", "introduce yourself"):
        return _identity(ctx)

    # 4. How the system works
    if _has(msg_clean, "how do you work", "how does this work", "how does the system work",
            "how does it work", "how do you detect", "how do you know", "how does this system work",
            "how do you monitor", "explain the system", "explain how"):
        return _how_it_works()

    # 5. Appliances ("can I run my fridge?", "can I use the TV?", "can I charge my phone?")
    if _has(msg_clean, "can i run", "can i use", "can i switch on", "can i turn on", "can i power",
            "can i charge", "charge my", "enough power for", "enough for", "is it safe to use", "can i plug"):
        reply = _appliance(ctx, msg_clean)
        if reply:
            return reply

    # 6. Solar panels okay?
    maintenance_words = ("clean", "cleaning", "wash", "tilt", "angle", "orientation", "maintain",
                         "maintenance", "install", "tips", "how many")
    if _has(msg_clean, "panel", "panels", "pv", "solar panel", "solar panels", "array", "modules") and not _has(msg_clean, *maintenance_words):
        return _panels_health(ctx)

    # 7. Battery
    if _has(msg_clean, "battery", "batteries", "batt"):
        return _battery_health(ctx)

    # 8. Why low output
    if _has(msg_clean, "why") and _has(msg_clean, "low", "dropping", "drop", "dropped", "less", "weak", "zero", "reduced"):
        return _why_low(ctx)

    # 9. Explain alerts
    if (_has(msg_clean, "explain", "why", "meaning", "mean", "what is this", "what's this", "tell me about")
            and _has(msg_clean, "alert", "alerts", "alarm", "warning", "siren")):
        return _explain_alerts(ctx)

    # 10. Is it safe / what should I do
    if _has(msg_clean, "what should i do", "what do i do", "do i need to", "should i be worried",
            "anything to worry", "is my system safe", "is it safe", "am i safe", "next step",
            "any action", "recommend", "what can i do", "should i worry", "is everything okay",
            "is everything ok", "is everything fine", "everything alright",
            "is my system okay", "is my system ok", "is the system okay", "is the system ok",
            "is my system fine", "is my system working", "is the system working"):
        return _what_should_i_do(ctx)

    # 11. How much power
    if _has(msg_clean, "how much power", "how much energy", "how much am i", "how many watts",
            "power am i", "producing", "generating", "how much electricity"):
        return _power_now(ctx)

    # 12. Thanks / bye
    if _has(msg_clean, "thank you", "thanks", "thank u", "thx", "appreciate", "great job", "well done"):
        return _thanks()
    if _has(msg_clean, "bye", "goodbye", "see you", "good night", "later", "take care"):
        return _goodbye(ctx)

    # Greeting followed by an unrecognised question: still greet warmly.
    if is_greeting and len(words) <= 4:
        return _greeting(ctx)

    return None
