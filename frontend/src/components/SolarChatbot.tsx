import React, { useState, useRef, useEffect } from 'react';
import { Brain, X, Send, Loader2, BotMessageSquare } from 'lucide-react';
import { useDevice } from '../context/DeviceContext';
import { chatService } from '../api/services';

interface Message {
  id: number;
  role: 'user' | 'bot';
  text: string;
  timestamp: Date;
}

// ──────────────────────────────────────────────────────────────────────────────
// Hardcoded Solar AI Response Engine (no API key required)
// ──────────────────────────────────────────────────────────────────────────────

/** Words/phrases that indicate the user is trying to probe system internals */
const SYSTEM_PROBE_PATTERNS = [
  'system prompt', 'system message', 'initial prompt', 'initial instruction',
  'your instructions', 'your prompt', 'your rules', 'your guidelines',
  'behind the scenes', 'under the hood', 'how are you built', 'how were you made',
  'what model are you', 'what llm', 'what ai model', 'your source code', 'your code',
  'ignore previous', 'ignore above', 'ignore all', 'disregard',
  'forget your instructions', 'override', 'jailbreak', 'dan mode',
  'pretend you are', 'act as if', 'roleplay as',
  'api key', 'api secret', 'secret key', 'access token', 'auth token',
  'backend code', 'server code', 'database schema', 'sql injection',
  'admin password', 'root access', 'sudo', 'internal api',
  'reveal your', 'show me your prompt', 'repeat your instructions',
  'what are you running on', 'tech stack', 'architecture',
  'exploit', 'vulnerability', 'hack', 'penetration test',
];

/** Topic → keyword patterns → array of possible responses (picked randomly) */
const RESPONSE_MAP: { keywords: string[]; responses: string[] }[] = [
  // ── Battery ──
  {
    keywords: ['battery', 'charge', 'charging', 'soc', 'state of charge', 'battery level', 'battery percentage', 'battery life', 'battery health'],
    responses: [
      "Great question, bro ski! 🔋 Your battery health is key to your solar system's performance. Check the Dashboard for your real-time State of Charge (SoC). If it's consistently below 20%, consider reducing nighttime loads or upgrading your battery bank.",
      "Bro ski, battery management is crucial! 🔋 A healthy solar battery should cycle between 20-80% for maximum lifespan. Head over to your Dashboard to see your live battery stats. If you're seeing rapid drain, check for phantom loads!",
      "Yo bro ski! 🔋 Your battery is the heart of your off-grid setup. For optimal performance, avoid deep discharges below 20%. The Analytics page shows your charge/discharge trends over time — super helpful for spotting issues early!",
    ],
  },
  // ── Solar Panels / Generation ──
  {
    keywords: ['panel', 'solar panel', 'generation', 'power generation', 'watt', 'kilowatt', 'kwh', 'energy production', 'pv', 'photovoltaic', 'solar output', 'solar power'],
    responses: [
      "Bro ski, your solar panels are your money-makers! ☀️ Check the Dashboard for real-time power generation data. Peak output is usually between 10 AM – 2 PM. If your numbers seem low, check for shading, dirt buildup, or panel angle issues.",
      "Great question, bro ski! ⚡ Your panel output depends on sunlight intensity, angle, and cleanliness. The Analytics section shows your daily/weekly/monthly generation trends. Pro tip: clean panels can boost efficiency by up to 25%!",
      "Yo bro ski! 🌞 Solar generation varies with weather and season. Your Dashboard shows live wattage output. If you notice a sudden drop, it could be cloud cover, shading from new structures, or a wiring issue worth investigating.",
    ],
  },
  // ── Voltage ──
  {
    keywords: ['voltage', 'volt', 'overvoltage', 'undervoltage', 'low voltage', 'high voltage', 'voltage drop'],
    responses: [
      "Bro ski, voltage monitoring is critical! ⚡ Normal system voltage depends on your setup (12V, 24V, or 48V). If you're seeing voltage drops, check your wiring connections and cable gauge. The Alerts page will flag any anomalies automatically.",
      "Good question, bro ski! ⚡ Voltage fluctuations can indicate wiring issues, overloaded circuits, or charge controller problems. Your Dashboard shows real-time voltage readings. If you see consistent drops, inspect your connections and consider thicker gauge wiring.",
    ],
  },
  // ── Current / Amperage ──
  {
    keywords: ['current', 'amperage', 'amp', 'amps', 'overcurrent', 'short circuit'],
    responses: [
      "Bro ski, keeping an eye on current draw is essential! 🔌 High current could mean an overloaded circuit or even a short. Check your Alerts page — SolarGuard flags unusual current spikes automatically. Always use properly rated fuses and breakers!",
      "Great question, bro ski! ⚡ Your system's current flow tells you how hard your equipment is working. The Dashboard shows live amperage. If you see unexpected spikes, check your connected loads and wiring for any faults.",
    ],
  },
  // ── Temperature ──
  {
    keywords: ['temperature', 'temp', 'heat', 'overheat', 'thermal', 'hot', 'cold', 'cooling'],
    responses: [
      "Bro ski, temperature management is crucial for your solar system's longevity! 🌡️ Batteries perform best between 20-25°C. High temps degrade battery life, while extreme cold reduces capacity. The Dashboard shows your real-time temperature readings.",
      "Great question, bro ski! 🌡️ Overheating panels actually lose efficiency — they can drop 0.3-0.5% per degree above 25°C. Your system monitors temp automatically, and the Alerts page will flag any thermal warnings. Keep good airflow around your equipment!",
    ],
  },
  // ── Alerts / Notifications ──
  {
    keywords: ['alert', 'alarm', 'notification', 'warning', 'critical', 'danger', 'emergency', 'fault', 'error', 'issue', 'problem'],
    responses: [
      "Bro ski, your Alerts page is your early warning system! 🚨 SolarGuard monitors voltage, current, temperature, and battery levels 24/7. Critical alerts need immediate attention — check the Alerts section for details and recommended actions.",
      "Good question, bro ski! 🚨 Alerts are categorized by severity: Info, Warning, and Critical. Critical alerts (like overcurrent or extreme temperature) need immediate action. Head to the Alerts page to see all active and resolved notifications.",
      "Yo bro ski! 🔔 Stay on top of your alerts! The system automatically detects anomalies and sends notifications. You can view, filter, and resolve alerts from the Alerts page. Pro tip: don't ignore warnings — they can prevent bigger issues!",
    ],
  },
  // ── Dashboard / Overview ──
  {
    keywords: ['dashboard', 'overview', 'status', 'summary', 'home page', 'main page', 'monitor'],
    responses: [
      "Bro ski, the Dashboard is your command center! 📊 It shows real-time data: power generation, battery level, voltage, current, and temperature — all at a glance. It's the first place to check when you want to know how your system is doing.",
      "Great question, bro ski! 📊 Your Dashboard provides a comprehensive overview of your entire solar system. You'll see live metrics, recent alerts, and performance trends. It updates in real-time so you're always in the know!",
    ],
  },
  // ── Analytics / History ──
  {
    keywords: ['analytics', 'history', 'trend', 'graph', 'chart', 'statistics', 'stats', 'report', 'data', 'performance'],
    responses: [
      "Bro ski, the Analytics section is where the magic happens! 📈 You can track your solar generation, consumption, and battery trends over days, weeks, and months. It's perfect for spotting patterns and optimizing your energy usage.",
      "Great question, bro ski! 📊 Analytics gives you deep insights into your system's performance over time. Look for trends in generation vs consumption to optimize your setup. The historical data helps you plan for seasonal changes too!",
    ],
  },
  // ── Devices ──
  {
    keywords: ['device', 'devices', 'controller', 'inverter', 'charge controller', 'mppt', 'hardware', 'equipment', 'setup', 'configure'],
    responses: [
      "Bro ski, managing your devices is easy! 🔧 Head to the Devices page to see all connected equipment — charge controllers, inverters, and sensors. You can select a device to get detailed stats and context-aware insights.",
      "Great question, bro ski! ⚙️ Your Devices page shows all connected hardware. Select a device to see its live data and telemetry. Make sure your devices are properly configured for accurate monitoring and alerts.",
    ],
  },
  // ── Savings / Cost / Money ──
  {
    keywords: ['save', 'saving', 'cost', 'money', 'bill', 'electricity bill', 'roi', 'return on investment', 'payback', 'economics', 'expensive', 'cheap', 'afford'],
    responses: [
      "Bro ski, that's the best part about solar — saving money! 💰 Your system reduces grid dependency, cutting electricity bills significantly. Check the Analytics page to see your generation vs consumption trends. The more you generate, the more you save!",
      "Great question, bro ski! 💸 Solar ROI depends on your setup size, local electricity rates, and usage patterns. Most residential systems pay for themselves in 5-8 years. Track your savings through the Analytics page!",
    ],
  },
  // ── Weather / Sunlight ──
  {
    keywords: ['weather', 'sun', 'sunlight', 'cloud', 'cloudy', 'rain', 'rainy', 'shade', 'shading', 'irradiance', 'sunshine'],
    responses: [
      "Bro ski, weather plays a huge role in solar generation! ☁️ Cloudy days can reduce output by 25-50%, while rainy days might drop to 10-25% of peak capacity. Your system automatically adjusts, and the Dashboard reflects real-time conditions.",
      "Great question, bro ski! 🌤️ Solar panels still work on cloudy days, just at reduced efficiency. Direct sunlight gives peak performance. If shading is an issue, consider trimming nearby trees or adjusting panel placement.",
    ],
  },
  // ── Maintenance / Cleaning ──
  {
    keywords: ['maintenance', 'maintain', 'clean', 'cleaning', 'dust', 'dirty', 'wash', 'care', 'upkeep', 'service'],
    responses: [
      "Bro ski, regular maintenance keeps your system running at peak performance! 🧹 Clean your panels every 2-4 weeks (or after dust storms). Inspect wiring connections quarterly. A well-maintained system can last 25+ years!",
      "Great question, bro ski! 🔧 Solar maintenance is minimal but important: clean panels regularly, check battery terminals for corrosion, ensure ventilation around batteries and inverters, and review your Alerts page for any early warnings.",
    ],
  },
  // ── Efficiency / Optimization ──
  {
    keywords: ['efficiency', 'efficient', 'optimize', 'optimization', 'improve', 'better', 'maximize', 'boost', 'enhance', 'upgrade'],
    responses: [
      "Bro ski, optimizing your solar system is smart! 🚀 Key tips: keep panels clean, ensure optimal tilt angle, minimize shading, use efficient appliances, and shift heavy loads to peak solar hours (10 AM – 2 PM). The Analytics page helps identify optimization opportunities!",
      "Great question, bro ski! ⚡ To maximize efficiency: clean panels regularly, check for shading, ensure your charge controller is properly configured (MPPT is best), and monitor your battery cycling patterns. Small tweaks can make a big difference!",
    ],
  },
  // ── Load / Consumption ──
  {
    keywords: ['load', 'consumption', 'usage', 'consume', 'power usage', 'energy usage', 'appliance', 'watt hour'],
    responses: [
      "Bro ski, managing your loads is key to solar success! 🔌 Monitor your consumption on the Dashboard and try to run heavy appliances (washing machine, iron, etc.) during peak solar hours. The Analytics page shows your consumption patterns over time.",
      "Great question, bro ski! ⚡ Understanding your load profile helps optimize your solar system. Check the Dashboard for real-time consumption data. Pro tip: stagger high-draw appliances instead of running them all at once to prevent overloading!",
    ],
  },
  // ── Help / What can you do ──
  {
    keywords: ['help', 'what can you do', 'capabilities', 'features', 'guide', 'tutorial', 'how to use', 'instructions'],
    responses: [
      "Bro ski, I'm here to help you with everything solar! 🌞 I can assist with:\n\n🔋 Battery health & charging\n☀️ Solar panel performance\n⚡ Voltage & current monitoring\n🌡️ Temperature management\n🚨 Alert interpretation\n📊 Analytics & trends\n💰 Energy savings tips\n🔧 Maintenance advice\n\nJust ask me anything!",
      "Yo bro ski! 🤙 I'm your SolarGuard AI assistant. Here's what I can help with:\n\n• System health monitoring\n• Battery management tips\n• Solar generation insights\n• Alert troubleshooting\n• Efficiency optimization\n• Maintenance reminders\n• Cost savings strategies\n\nFire away with any question!",
    ],
  },
  // ── Thanks / Appreciation ──
  {
    keywords: ['thanks', 'thank you', 'appreciate', 'awesome', 'great', 'perfect', 'nice', 'cool', 'amazing', 'wonderful', 'love it'],
    responses: [
      "Anytime, bro ski! 🤙 That's what I'm here for. Keep monitoring your system and don't hesitate to ask if anything comes up! Stay solar! ☀️",
      "You're welcome, bro ski! 😎 Always happy to help. Keep those panels clean and that battery healthy! ⚡🌞",
      "No problem at all, bro ski! 💪 Your solar system is in good hands. Reach out whenever you need assistance!",
    ],
  },
  // ── Goodbye ──
  {
    keywords: ['bye', 'goodbye', 'see you', 'later', 'peace', 'take care', 'gotta go', 'ciao'],
    responses: [
      "Catch you later, bro ski! ✌️ Keep those panels soaking up that sunshine. I'll be here whenever you need me! ☀️",
      "Peace out, bro ski! 🤙 Stay solar and stay smart. Your system is looking great! See you around! 🌞",
      "Later, bro ski! 😎 Remember — the sun's got your back, and so do I. Take care! ⚡",
    ],
  },
  // ── Who are you ──
  {
    keywords: ['who are you', 'what are you', 'your name', 'introduce yourself', 'about you'],
    responses: [
      "I'm SolarGuard AI, bro ski! 🌞 Your personal solar energy assistant. I help you monitor, optimize, and troubleshoot your solar power system. I've got your back when it comes to batteries, panels, alerts, and everything in between! ⚡",
      "Yo bro ski! I'm SolarGuard AI — your smart solar companion! 🤖☀️ I'm designed to help you understand your solar system's performance, manage alerts, and maximize your energy savings. Ask me anything about your setup!",
    ],
  },
  // ── Greetings (Moved to bottom so it doesn't override specific topics) ──
  {
    keywords: ['hello', 'hi', 'hey', 'howdy', 'sup', 'good morning', 'good afternoon', 'good evening', 'greetings', 'yo'],
    responses: [
      "Hey there, bro ski! 🌞 Welcome to SolarGuard AI. How can I help you with your solar system today?",
      "What's good, bro ski! ⚡ I'm your solar assistant — ask me anything about your panels, battery, or power generation!",
      "Yo bro ski! 🤙 SolarGuard AI at your service. What do you need help with today?",
    ],
  },
];

/**
 * Generate a hardcoded response based on user input.
 * No API key required — everything runs client-side.
 */
function generateLocalResponse(userMessage: string, hasDevice: boolean): string {
  const lower = userMessage.toLowerCase().trim();

  // ── 1. Reject system probing / prompt injection attempts ──
  const isSystemProbe = SYSTEM_PROBE_PATTERNS.some((pattern) => lower.includes(pattern));
  if (isSystemProbe) {
    const rejections = [
      "I appreciate your curiosity, bro ski, but I'm only here to help with your solar energy system! 🌞 I can't share details about my internal workings, system prompts, or architecture. Let's keep the conversation focused on making your solar setup shine! ☀️",
      "Nice try, bro ski! 😄 But that's classified territory. I'm strictly a solar energy assistant — I can't discuss my system configuration, prompts, or behind-the-scenes details. How about we talk about your panels or battery instead? ⚡",
      "Bro ski, I'm going to have to respectfully decline that one! 🔒 My internals are off-limits for security reasons. I'm here to help you with solar panels, batteries, alerts, and energy optimization. What solar topic can I assist you with?",
      "Whoa there, bro ski! 🛡️ That request falls outside my scope. For security and integrity reasons, I can't share information about my internal systems, instructions, or architecture. But I'm all ears for any solar energy questions! 🌞",
    ];
    return rejections[Math.floor(Math.random() * rejections.length)];
  }

  // ── 2. If no device is selected, prompt the user first ──
  if (!hasDevice) {
    return "Hey bro ski! 🌞 Before I can give you the best insights, please select a device from the Devices page. That way I can reference your live solar data and give you accurate, personalized answers! ⚡";
  }

  // ── 3. Match against known topics ──
  for (const entry of RESPONSE_MAP) {
    const matched = entry.keywords.some((kw) => lower.includes(kw));
    if (matched) {
      return entry.responses[Math.floor(Math.random() * entry.responses.length)];
    }
  }

  // ── 4. Fallback — general solar guidance ──
  const fallbacks = [
    "Bro ski, that's an interesting question! 🤔 While I don't have a specific answer for that one, I'd recommend checking your Dashboard for real-time system data, or the Alerts page if something seems off. I'm best with solar panels, batteries, voltage, alerts, and energy optimization questions! ☀️",
    "Hmm, I'm not quite sure about that one, bro ski! 🌞 My expertise is in solar energy systems — panels, batteries, charge controllers, alerts, and energy management. Try rephrasing your question around those topics and I'll hook you up with solid info! ⚡",
    "Good question, bro ski! 🤙 I might not have a perfect answer for that specific topic, but here's what I can help with: battery health, solar generation, voltage/current monitoring, alert interpretation, and efficiency tips. What would you like to explore? 🔋☀️",
    "Bro ski, I want to give you the best answer possible! 💪 That topic is a bit outside my solar expertise though. Try asking about your panels, battery, alerts, temperature, or energy savings — that's where I really shine! 🌞",
  ];
  return fallbacks[Math.floor(Math.random() * fallbacks.length)];
}

const SolarChatbot: React.FC = () => {
  const { currentDevice } = useDevice();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      role: 'bot',
      text: "Hello! I'm SolarGuard AI 🌞 I have access to your live solar data and alerts. Ask me anything about your system's health, battery status, or power generation.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const nextId = useRef(1);

  // Auto-scroll to the latest message
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 80);
    }
  }, [isOpen]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMessage: Message = {
      id: nextId.current++,
      role: 'user',
      text: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    // Short "thinking" pause so replies don't appear unnaturally instantly
    const thinking = new Promise((resolve) => setTimeout(resolve, 700 + Math.random() * 700));

    let reply: string;
    try {
      // Primary path: backend assistant grounded in live telemetry + active alerts
      const [res] = await Promise.all([
        chatService.sendMessage(currentDevice ? currentDevice.id : null, trimmed),
        thinking,
      ]);
      reply = res.reply;
    } catch {
      // Fallback: offline local guidance if the server is unreachable
      await thinking;
      reply = generateLocalResponse(trimmed, !!currentDevice)
        .replace(/^(yo\s+)?bro ski[,!]?\s*/i, '')
        .replace(/,?\s*bro ski/gi, '');
      reply = reply.charAt(0).toUpperCase() + reply.slice(1);
    }

    const botMessage: Message = {
      id: nextId.current++,
      role: 'bot',
      text: reply,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, botMessage]);
    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (d: Date) =>
    d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <>
      {/* ── Floating toggle button ───────────────────────────────────────── */}
      <button
        id="solar-chatbot-toggle"
        aria-label={isOpen ? 'Close AI assistant' : 'Open AI assistant'}
        onClick={() => setIsOpen((o) => !o)}
        className={`
          fixed bottom-6 right-6 z-50
          w-14 h-14 rounded-full shadow-2xl
          flex items-center justify-center
          transition-all duration-300 ease-in-out
          ${isOpen
            ? 'bg-gray-700 hover:bg-gray-600 rotate-0 scale-95'
            : 'bg-gradient-to-br from-blue-500 to-indigo-600 hover:from-blue-400 hover:to-indigo-500 hover:scale-110'
          }
          focus:outline-none focus:ring-4 focus:ring-blue-300
        `}
      >
        {isOpen ? (
          <X className="text-white" size={22} />
        ) : (
          <Brain className="text-white" size={26} />
        )}

        {/* Pulse ring when closed */}
        {!isOpen && (
          <span className="absolute inset-0 rounded-full bg-blue-400 opacity-30 animate-ping" />
        )}
      </button>

      {/* ── Chat panel ──────────────────────────────────────────────────── */}
      <div
        id="solar-chatbot-panel"
        className={`
          fixed bottom-24 right-6 z-50
          w-[360px] max-h-[520px]
          flex flex-col
          rounded-2xl overflow-hidden shadow-2xl
          border border-white/10
          transition-all duration-300 ease-in-out origin-bottom-right
          ${isOpen ? 'opacity-100 scale-100 pointer-events-auto' : 'opacity-0 scale-95 pointer-events-none'}
        `}
        style={{ backdropFilter: 'blur(12px)' }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-700 shrink-0">
          <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
            <Brain className="text-white" size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white font-semibold text-sm leading-tight">SolarGuard AI</p>
            <p className="text-blue-200 text-xs truncate">
              {currentDevice ? `Device: ${currentDevice.name}` : 'No device selected'}
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-emerald-300 text-xs font-medium">Live</span>
          </div>
        </div>

        {/* No-device warning */}
        {!currentDevice && (
          <div className="px-4 py-2 bg-amber-50 border-b border-amber-200 text-amber-800 text-xs flex items-center gap-2 shrink-0">
            <BotMessageSquare size={14} />
            Select a device to get context-aware answers.
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto bg-gray-50 px-4 py-4 space-y-3">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-end gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar */}
              {msg.role === 'bot' && (
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0">
                  <Brain size={14} className="text-white" />
                </div>
              )}

              <div className={`max-w-[78%] ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                <div
                  className={`px-3 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap break-words shadow-sm ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-br-sm'
                      : 'bg-white text-gray-800 border border-gray-200 rounded-bl-sm'
                  }`}
                >
                  {msg.text}
                </div>
                <span className="text-gray-400 text-[10px] px-1">{formatTime(msg.timestamp)}</span>
              </div>
            </div>
          ))}

          {/* Loading bubble */}
          {loading && (
            <div className="flex items-end gap-2">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0">
                <Brain size={14} className="text-white" />
              </div>
              <div className="px-4 py-3 bg-white border border-gray-200 rounded-2xl rounded-bl-sm shadow-sm">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-3 py-3 bg-white border-t border-gray-200 flex items-center gap-2 shrink-0">
          <input
            id="solar-chatbot-input"
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="lets save your home"
            disabled={loading}
            className="
              flex-1 px-4 py-2.5 rounded-full text-sm
              bg-gray-100 border border-gray-200
              focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent
              placeholder:text-gray-400 text-gray-800
              disabled:opacity-50 transition
            "
          />
          <button
            id="solar-chatbot-send"
            onClick={handleSend}
            disabled={loading || !input.trim()}
            aria-label="Send message"
            className="
              w-10 h-10 rounded-full flex items-center justify-center shrink-0
              bg-gradient-to-br from-blue-500 to-indigo-600
              hover:from-blue-400 hover:to-indigo-500
              disabled:opacity-40 disabled:cursor-not-allowed
              transition-all shadow-md hover:shadow-blue-300
              focus:outline-none focus:ring-2 focus:ring-blue-400
            "
          >
            {loading ? (
              <Loader2 size={16} className="text-white animate-spin" />
            ) : (
              <Send size={16} className="text-white" />
            )}
          </button>
        </div>
      </div>
    </>
  );
};

export default SolarChatbot;
