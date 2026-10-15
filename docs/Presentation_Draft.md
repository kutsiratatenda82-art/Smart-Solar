# SMART SOLAR ALERT — Final Year Presentation Draft
### (Text version for review — PowerPoint will be built from this once approved)

**Presenter:** Kutsira Tatenda | **Candidate No.:** 0625006G00010
**Institution:** Kwekwe Polytechnic — Department of Information Technology
**Supervisor:** [Supervisor Name]

> **How to read this document**
> Each slide has two parts:
> - **ON THE SLIDE** – the short text that will appear on screen (kept short on purpose; judges don't want to read paragraphs).
> - **WHAT YOU SAY** – your speaking notes. Learn the ideas, not the words.
>
> At the end there is a **Defence Section**: the hard questions judges are likely to ask, and strong answers.
> Target time: **10–12 minutes** + questions.

---

## SLIDE 1 — TITLE

**ON THE SLIDE**
> # Smart Solar Alert
> ### An IoT-Enabled Real-Time Solar Power Monitoring, Fault Diagnostics and Intelligent Alerting Platform
> *"Giving your solar system a voice."*
>
> Kutsira Tatenda · 0625006G00010 · Kwekwe Polytechnic · Dept. of IT

**WHAT YOU SAY**
"Good morning, honourable judges. My name is Kutsira Tatenda, and my project is **Smart Solar Alert**: a low-cost IoT system that watches a solar installation 24 hours a day, picks up faults within seconds, and tells the owner in plain language what is wrong and what to do about it. In short, it gives a solar system a voice."

---

## SLIDE 2 — INTRODUCTION

**ON THE SLIDE**
> - Solar power is now a **survival technology** in Zimbabwe, not a luxury
> - But a solar system is a **small power station** — panels, controller, battery, loads
> - Each part can fail **silently**
> - **Smart Solar Alert** = Sensor device (ESP32) + Cloud server + Web dashboard
> - Measures → Diagnoses → Alerts → Advises

**WHAT YOU SAY**
"Because of load-shedding, thousands of homes, clinics, schools and small businesses have put in solar. People forget that a solar installation is really a small power station. It has panels, a charge controller, a battery bank and loads, and **any of them can fail without anyone noticing**.

My system has three parts:
1. A small **sensor device** built on an ESP32 microcontroller (I call it the *TelePower Guard*) that measures voltage and current at the installation.
2. A **cloud server** that receives those readings every 5 seconds and runs a diagnostic engine on each one.
3. A **web dashboard** where the owner sees the live state of the system, gets alerts and is told what to do.

So the system does four things: it **measures**, **diagnoses**, **alerts** and **advises**."

---

## SLIDE 3 — BACKGROUND

**ON THE SLIDE**
> - Extended load-shedding (2022–2024) → mass adoption of home & business solar
> - **Battery = most expensive part** (US$250 – US$1,200)
> - Battery over-discharge permanently cuts its lifespan
> - Current monitoring = small LCD/LEDs on the controller, often in a back room
> - Commercial monitoring: **brand-locked, expensive, subscription-based**
> - Opportunity: ESP32 (< US$10) + cheap sensors + smartphones + cloud

**WHAT YOU SAY**
"Between 2022 and 2024, low output at Kariba and an ageing thermal fleet meant many suburbs went without power for most of the day. People answered that by buying solar.

The **battery** is the most expensive part of the system, costing anywhere from 250 to 1,200 US dollars. A lead-acid battery that keeps being drained too far loses a big part of its life. A lithium battery that drops below its cut-off voltage can be damaged for good.

So how do people monitor their systems today? With a small LCD or a few LEDs on the charge controller, usually in a back room or the roof space, and only a technician really understands it. Commercial monitoring products do exist, but each one is tied to one inverter brand, needs a subscription, and costs more than an ordinary household can pay.

Meanwhile, an ESP32 now costs less than 10 dollars, almost everyone has a smartphone, and cloud hosting is cheap. **That is the gap my project fills.**"

---

## SLIDE 4 — PROBLEM STATEMENT

**ON THE SLIDE**
> **Owners of small solar installations have no affordable way to continuously monitor their system's health and be alerted — in real time and in plain language — when something goes wrong.**
>
> **Result:** battery deep-discharge, overcharging and load failures go unnoticed **until damage is done.**
>
> | Problem today | Consequence |
> |---|---|
> | No continuous monitoring | Faults found only after symptoms appear |
> | No remote visibility | Owner away = owner blind |
> | Cryptic indicators | Wrong action taken |
> | No history | No evidence for technicians / warranty |
> | No alarm / escalation | Critical faults ignored overnight |
> | Slow technician response | 1–3 days + transport costs |

**WHAT YOU SAY**
*(Read the bold statement slowly. This is the most important sentence in the presentation.)*

"Owners of small solar installations have no affordable way to keep watching the health of their system, or to be told in real time and in plain language when something goes wrong. **The result is that preventable faults go unnoticed until the damage is done.**

At the moment, the owner only finds out when the lights dim or the inverter beeps, and by then the battery is already deeply discharged. They call a technician, who takes one to three days to arrive with a multimeter. There is no history, so the technician cannot see what happened overnight. Every one of these problems is one my system solves."

---

## SLIDE 5 — AIM & OBJECTIVES

**ON THE SLIDE**
> **AIM:** To design and develop a low-cost, secure IoT platform that continuously monitors a solar installation, automatically diagnoses faults, and alerts the owner in real time.
>
> **OBJECTIVES**
> 1. Build an **ESP32 sensing unit** that measures DC voltage & current and sends data over Wi-Fi every **5 seconds**
> 2. Develop a **secure REST API** (FastAPI) for users, devices, readings and alerts
> 3. Implement a **rule-based diagnostic engine** with centrally configurable thresholds
> 4. Implement an **intelligent alert lifecycle** that avoids alert fatigue
> 5. Deliver a **responsive web dashboard** for live and historical monitoring
> 6. Provide **attention-grabbing critical alerts** (full-screen overlay + siren)
> 7. Integrate a **smart assistant** that answers questions using live device data
> 8. **Test** the system with automated tests and user acceptance testing

**WHAT YOU SAY**
"My aim was to design and develop a low-cost, secure IoT platform that monitors a solar installation continuously, diagnoses faults automatically and alerts the owner in real time.

I split that into eight measurable objectives. *(Go through them quickly. Stress numbers 3 and 4, because they are where the intelligence of the system lives.)* Each objective has a measurable success criterion, and I will show you that each one has been met."

---

## SLIDE 6 — METHODS USED (1): Methodology & Fact-Finding

**ON THE SLIDE**
> **Development methodology:** Agile / Incremental (phased delivery)
> Requirements → Firmware → Backend → Frontend → Testing & Deployment
>
> **Fact-finding techniques**
> - Interviews (solar owners & installers)
> - Questionnaires
> - Site observation
> - Document analysis
>
> **Analysis tools:** DFDs, Use Cases, ERD, SWOT, **MoSCoW** prioritisation

**WHAT YOU SAY**
"I used an **Agile, incremental methodology**, building the system in phases so that each one could be tested before I moved on. I chose Agile over Waterfall because hardware brings uncertainty: sensor calibration and Wi-Fi behaviour have to be tried out in practice, and Agile let me go back and adjust.

To collect requirements I interviewed solar owners and installers, gave out questionnaires, observed real installations and looked at documents such as job cards. I then used **MoSCoW prioritisation** to keep the scope under control. *(Must-have: monitoring, diagnostics, alerts. Could-have: the assistant.)*"

---

## SLIDE 7 — METHODS USED (2): System Architecture

**ON THE SLIDE**
> ```
>  [ Solar Panel / Battery ]
>            │  voltage + current sensors
>            ▼
>  [ ESP32 — TelePower Guard ]  ── HTTPS POST every 5 s ──►  [ FastAPI Cloud Server ]
>                                                                   │        │
>                                                     Diagnostic Engine   PostgreSQL DB
>                                                                   │
>                                                    ◄── REST API (JWT secured) ──►
>                                                                   │
>                                                      [ React Web Dashboard ]
>                                                 Live gauges · Charts · Alerts · Siren · Assistant
> ```
> **Three tiers:** Edge (sensing) → Cloud (intelligence) → Presentation (user)

**WHAT YOU SAY**
"This is the architecture. It has **three tiers**.

- **The edge tier** is the ESP32 device. It takes 24 readings of voltage and current, averages them to remove noise, works out power as P = V × I, and sends the result to the cloud every five seconds.
- **The cloud tier** is a Python FastAPI server with a PostgreSQL database. Each reading is checked, stored, and passed straight through the **diagnostic engine**.
- **The presentation tier** is a React web dashboard. It works on a phone or a laptop and refreshes every five seconds.

One design choice to point out: **all the intelligence runs on the server, not on the device.** That keeps the device cheap and simple, and it means I can change diagnostic rules for every customer at once without touching any hardware."

---

## SLIDE 8 — METHODS USED (3): Technologies

**ON THE SLIDE**
> | Layer | Technology | Why chosen |
> |---|---|---|
> | Hardware | **ESP32**, voltage sensor (0–25 V), **ACS712** current sensor | Built-in Wi-Fi, dual-core, < US$10 |
> | Firmware | C++ (Arduino core) | Mature, huge community |
> | Backend | **Python FastAPI**, SQLAlchemy, Pydantic | Fast, automatic validation & API docs |
> | Database | **PostgreSQL** + Alembic migrations | Reliable (ACID), versioned schema |
> | Security | **JWT** tokens, **bcrypt** password hashing | Industry standard |
> | Frontend | **React + TypeScript**, Vite, Tailwind, Recharts | Responsive, mobile-friendly |
> | Hosting | Render (cloud) | Low cost, HTTPS by default |

**WHAT YOU SAY**
"These are the technologies I used. Each was chosen for a reason. *(Pick three to explain.)*
- **ESP32 instead of Arduino Uno:** Wi-Fi is built in, so there's no extra module. The Uno has no Wi-Fi at all.
- **FastAPI:** it checks every incoming reading automatically, so bad data, for example text where a number should be, is rejected before it gets near the database.
- **PostgreSQL:** it is ACID-compliant, so a critical alert record is never half-written or lost."

---

## SLIDE 9 — METHODS USED (4): The Intelligence — Diagnostics & Alert Lifecycle

**ON THE SLIDE**
> **Rule-based Diagnostic Engine** — every reading is classified:
>
> | Condition | Severity | Advice given to user |
> |---|---|---|
> | Normal Operation | 🟢 NORMAL | No action required |
> | High Voltage | 🟡 WARNING | Check charge controller regulation |
> | Critical High Voltage | 🔴 CRITICAL | Overcharging risk — disconnect panels |
> | Critical Low Voltage | 🔴 CRITICAL | Disconnect loads, charge battery |
> | Low Current | 🟡 WARNING | Check for partial load failure |
> | Critical Low Current | 🔴 CRITICAL | Load failed / disconnected — check wiring |
>
> **Smart Alert Lifecycle**
> `ACTIVE → ACKNOWLEDGED → (still faulty after 2 min?) → ACTIVE again`
> `Fault clears → RESOLVED automatically`
> ✔ No duplicate alerts ✔ Auto-resolution ✔ Re-escalation

**WHAT YOU SAY**
"This is the core of the system.

**First, the diagnostic engine.** Each reading is checked against thresholds that are all set in one place in the code. The result is a condition, a severity of Normal, Warning or Critical, a **plain-language message** and a **recommended solution**. So the owner doesn't see '10.2 volts'. They see *'Critical low voltage — disconnect loads and charge the battery.'*

**Second, the alert lifecycle**, which I am particularly proud of. A simple system would send a new alert every 5 seconds, which is about 720 alerts an hour for a single fault, and the owner would just stop paying attention. That is called **alert fatigue**. My system avoids it in three ways:
1. **De-duplication:** there is only ever one active alert per fault per device.
2. **Auto-resolution:** once readings are back to normal, the alert closes by itself.
3. **Re-escalation:** if the owner acknowledges an alert but the fault is still there after two minutes, the alert becomes active again. The system **will not let a critical fault be ignored.**"

---

## SLIDE 10 — METHODS USED (5): Security & Testing

**ON THE SLIDE**
> **Security**
> - Passwords hashed with **bcrypt** (never stored in plain text)
> - **JWT** token authentication on all user endpoints
> - **Ownership isolation** — users can only see their own devices, readings and alerts (403/404 otherwise)
> - Input validation on every request (Pydantic)
>
> **Testing**
> - Automated tests with **pytest**: authentication, devices, readings, alerts, simulation
> - **Demo Mode** — simulates fault readings without saving to the database
> - User Acceptance Testing with real users

**WHAT YOU SAY**
"On security: passwords are hashed with bcrypt, every user endpoint needs a JWT token, and there is **strict ownership isolation**. If User A tries to open User B's device, the server returns 403 Forbidden. That is required by Zimbabwe's **Cyber and Data Protection Act**.

On testing: I wrote automated tests with pytest covering authentication, devices, readings, alerts and simulation. I also built a **Demo Mode**, which lets a user or technician feed in a fault reading such as a critical over-voltage and watch the system respond, without causing a real fault and without filling the database with fake data. It also works as a training tool."

---

## SLIDE 11 — LIVE DEMONSTRATION *(recommended)*

**ON THE SLIDE**
> ### Live Demo
> 1. Live dashboard — real readings from the ESP32
> 2. Trigger a fault → alert appears → **critical overlay + siren**
> 3. Acknowledge → restore normal → **auto-resolved**
> 4. Ask the assistant: *"Is my battery okay?"*

**WHAT YOU SAY**
"Let me show you the system running."
*(Tip: practise this at least 3 times tonight. Have a **backup screen recording** in case the Wi-Fi at the venue fails. Use Demo Mode if the hardware won't connect.)*

---

## SLIDE 12 — BENEFITS

**ON THE SLIDE**
> **💰 Economic**
> - Device cost ≈ **US$34 per site** vs. battery worth **US$250–1,200**
> - Estimated payback: **~2 months** · 5-year NPV ≈ **US$728** per site
> - Fewer technician call-outs (remote diagnosis)
>
> **🏠 Social**
> - Clinics: protects vaccine fridges · Schools: protects learning hours · Businesses: protects income
> - Non-technical owners understand their system in plain language
>
> **⚙️ Technical**
> - Faults detected within **seconds**, not days
> - History gives technicians evidence for diagnosis & warranty claims
> - Brand-independent — works with any DC solar system
>
> | | Smart Solar Alert | Victron GX | Inverter Wi-Fi dongle |
> |---|---|---|---|
> | Upfront cost | **~$34** | ~$300+ | $60–120 |
> | Brand lock-in | **None** | Yes | Yes |
> | Plain-language advice | **Yes** | Partial | Limited |

**WHAT YOU SAY**
"The benefits fall into three groups.

**Economically**, one device costs about **34 dollars**, and it protects a battery worth up to 1,200 dollars. **Preventing one battery failure pays for the device many times over.** My cost-benefit analysis gives an estimated payback of about two months. Even in the pessimistic case, the net present value stays positive.

**Socially**, for a clinic this protects the vaccine fridge, for a school it protects learning hours, and for a small business it protects income.

**Technically**, a fault that used to take days to find is now caught in seconds, and the system works with **any brand**. Compared with Victron or inverter dongles, we're roughly **ten times cheaper**, there's no brand lock-in, and the owner gets **actual advice**, not just numbers."

---

## SLIDE 13 — FUTURE PLANS

**ON THE SLIDE**
> **Short term**
> - 📱 **SMS alerts via GSM module** (hardware pins already reserved on the ESP32)
> - 📦 Offline buffering — store readings when Wi-Fi drops, upload later
> - 🔐 Per-device secret keys for telemetry authentication
>
> **Medium term**
> - 🤖 **Machine-learning anomaly detection** & battery State-of-Charge prediction
> - 🧠 Upgrade the assistant to a full Large Language Model (e.g., Google Gemini)
> - 🌡️ Temperature & sunlight (irradiance) sensors → panel-efficiency diagnosis
> - 💬 WhatsApp / e-mail / push notifications
>
> **Long term**
> - 📡 LoRaWAN / NB-IoT for rural sites with no Wi-Fi
> - ⚡ Remote control — automatically cut non-essential loads to save the battery
> - 👷 Installer portal — one technician monitors hundreds of client sites
> - 📲 Native mobile app

**WHAT YOU SAY**
"This is the first version, and it was designed to grow.

In the **short term**, I'll add **SMS alerts through a GSM module**. The pins for this are already reserved in my firmware, so this matters for rural users without data. I'll also add offline buffering, so no readings are lost when Wi-Fi drops.

In the **medium term**, I'll move from rule-based to **machine-learning diagnostics**, which can spot a battery getting weaker *before* it fails, rather than only after it crosses a threshold.

In the **long term**, I see this becoming a **platform for installers**, where one technician monitors hundreds of client sites from one dashboard. That is also a business model: installers could offer monitoring as a paid service."

---

## SLIDE 14 — CONCLUSION

**ON THE SLIDE**
> ✅ Real-time monitoring every 5 seconds
> ✅ Automatic diagnosis with plain-language advice
> ✅ Smart alerts — no duplicates, auto-resolve, re-escalation
> ✅ Secure, multi-user, brand-independent
> ✅ Under US$35 per site
>
> ### *"From reactive repairs to proactive protection."*
> **Thank you — Questions are welcome.**

**WHAT YOU SAY**
"To conclude, Smart Solar Alert turns solar maintenance from **reactive** to **proactive**. Instead of finding out a battery is dead after it has died, the owner is warned in seconds, told what to do, and reminded until the problem is fixed, all for under 35 dollars. Thank you. I'm happy to take your questions."

---
---

# ⚠️ DEFENCE SECTION — READ THIS CAREFULLY

## Part A: Things the code does differently from the documentation

I compared the code with the written documentation. Judges who know what they're doing may open your code during questions. **These are the places where they could catch you out. Never claim something the code doesn't do.**

### 1. The "AI chatbot" does not use Gemini or any AI service
- The documentation says the assistant uses **Google Gemini**. The file `app/api/endpoints/chat.py` actually describes itself as a *"Smart rule-based solar assistant… keyword-matching… without any external API key."* `google-genai` is listed in requirements but **never used**.
- **On the slides, I wrote "smart assistant", not "AI / Gemini".** Gemini is listed as a *future plan*.
- **If asked:** *"The assistant is a context-aware, rule-based engine. It reads the device's live voltage, current and active alerts and builds its answer from them. I chose that deliberately for the first version: it is free, works without an external API key, can't hallucinate, and responds instantly. Plugging in an LLM like Gemini is on the roadmap. The integration point already exists."*

### 2. Indoor "torch boost" in the firmware (most serious)
- In `TelePowerGuard.ino`, `INDOOR_TORCH_BOOST = true` **multiplies the measured voltage by 4.5, caps it at 17.5 V and adds random noise** *"to make the live data bounce realistically."*
- If a judge reads this, it looks like **fake data**, and that could seriously hurt your credibility.
- **Recommendation:** either (a) set it to `false` for the presentation if you're demonstrating in sunlight, or (b) **say it openly before anyone finds it**: *"Indoors, a phone torch on a small panel only gives about 2 V, so I added an indoor demonstration mode that scales the signal to battery-level values. In the field this flag is switched off."* I'd **remove the random-noise line** either way, because it can't be defended.

### 3. Diagnostic thresholds are prototype values, not real 12 V battery values
- In the code, critical-low voltage = **2.0 V** and high = **15 V / 18 V**. A real 12 V battery is in trouble at around **11.8 V (warning)** and **10.5 V (critical)**.
- **If asked:** *"These thresholds are calibrated for my bench prototype, which uses a small panel and a bulb. They're all defined in one place, `diagnostics.py`, so for a real 12 V lead-acid installation I'd set 11.8 V warning, 10.5 V critical, 14.4 V high and 15 V critical-high. That's a configuration change, not a code change."*
- **Small bug:** `VOLTAGE_NORMAL_MIN` and `VOLTAGE_CRITICAL_LOW` are **both 2.0**, so the *Low Voltage Warning* can never trigger. That's why I left it off the Slide 9 table. I can fix it tonight if you want.

### 4. Telemetry endpoint has no device authentication
- `POST /api/devices/telemetry/{device_identifier}` accepts data from anyone who knows the device name. The firmware also uses `setInsecure()` (HTTPS encryption, but no certificate check).
- **If asked:** *"User-facing endpoints are fully JWT-protected. The device endpoint is identified by device ID, which was a deliberate trade-off to keep the firmware simple for the prototype. The next step, already on my roadmap, is a per-device secret API key and certificate pinning."*

### 5. No SMS yet
- GSM pins (16/17) are defined, but SMS is **not implemented**. Present it as a **future plan** (which the slides do), not as a feature.

### 6. Don't show the firmware on the projector
- Your **Wi-Fi name and password** are hard-coded in plain text on lines 19–20. Change them or hide them.

### 7. Use consistent cost figures
- Your document mentions **$34**, **$38** and **$315** in different places. Use **$34 per site (bill of materials)** throughout. If asked about $315, say: *"$315 was the total prototyping budget, including 5 test boards and a year of hosting. The per-site production cost is $34."*

---

## Part B: Likely judge questions and strong answers

**Q1. Why not just buy a Victron or inverter monitoring system?**
> "Those cost from $60 to over $300, only work with their own brand, and mostly show raw numbers. Mine costs about $34, works with any DC system, and tells the user *what to do*. It's designed for the ordinary Zimbabwean household, not the premium market."

**Q2. Why rule-based diagnostics and not machine learning?**
> "Three reasons. First, ML needs a lot of labelled fault data, and that doesn't exist yet for local installations. My system is what will *collect* it. Second, rules are **explainable**: every alert shows the measured value and the threshold it broke, which is what a technician needs. Third, safety-critical thresholds like battery cut-off voltages are well known from manufacturer specs, so rules are the right tool. ML is the next phase."

**Q3. What happens if Wi-Fi goes down?**
> "The dashboard notices the device is offline when no reading arrives within the expected window, and shows that to the user, which is a useful alert in its own right. In the current version, readings taken while offline aren't stored. Offline buffering and a GSM/SMS fallback are my first two roadmap items."

**Q4. Why every 5 seconds? Why not every second?**
> "It's a trade-off. Battery faults develop over seconds to minutes, so 5 seconds is fast enough to catch them. Each device already produces **17,280 readings a day** at 5 seconds. At 1 second that would be 86,400, five times the database cost for almost no gain in safety."

**Q5. How do you stop the user being flooded with alerts?**
> "Through the alert lifecycle: de-duplication (one active alert per fault per device), auto-resolution when the fault clears, and re-escalation after 2 minutes if an acknowledged fault continues. Without it, one fault would produce about 720 alerts an hour."

**Q6. How accurate are your sensors?**
> "The ESP32 has a 12-bit ADC, giving 4,096 levels. I average 24 samples per reading to reduce noise. The ACS712 output goes through a 10k/20k voltage divider to keep it within the ESP32's 3.3 V limit. The ESP32 ADC isn't perfectly linear near its extremes, so a calibration step is needed, and that's in my documented limitations."

**Q7. How is user data protected?**
> "Passwords are bcrypt-hashed, sessions use signed JWT tokens, all traffic goes over HTTPS, and every database query is limited to the logged-in user's own devices. I collect only what I need, an email and a password, in line with the Cyber and Data Protection Act."

**Q8. Can it scale?**
> "Yes. The server is stateless, so more instances can be added behind a load balancer. Fixed hosting costs are shared across sites: about $1.20 per site per year at 100 sites, and under 50 cents at 1,000."

**Q9. What was your biggest challenge?**
> *(Pick a true one, for example)* "Hardware calibration. The ACS712 outputs up to 5 V, but the ESP32 accepts only 3.3 V, so I had to design a voltage divider and correct for it in software. Getting the ESP32 to run as a Wi-Fi access point for configuration while also connecting to the router was the other big one."

**Q10. What makes your project original?**
> "Low-cost hardware, brand independence, plain-language advice and an alert lifecycle with re-escalation, all in one system built for the Zimbabwean context. Existing products give one or two of those, not all four."

---

## Part C: Presentation-day tips
1. **Lead with the problem, not the technology.** Judges remember the *"$1,200 battery destroyed because nobody was warned"* story.
2. **Practise the demo** and keep a **screen recording backup**.
3. If you don't know an answer: *"That's a good point. I haven't fully explored it yet, but my approach would be…"* Never bluff.
4. Don't read the slides. Look at the judges.
5. Keep it to 10–12 minutes. Going over time costs marks.
