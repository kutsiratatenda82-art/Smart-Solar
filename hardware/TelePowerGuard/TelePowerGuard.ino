#include <Arduino.h>
#include <DNSServer.h>
#include <Preferences.h>
#include <WebServer.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

namespace {

constexpr const char* APP_NAME = "TelePower Guard";
constexpr const char* FIRMWARE_VERSION = "telepower-cloud-v2.0.0";
constexpr const char* WIFI_SSID = "TelePower-Guard";
constexpr const char* DASHBOARD_PIN = "1234";

// BACKEND & NETWORK DEFAULTS (Can also be changed anytime via http://192.168.4.1)
String backendUrl = "https://smart-solar-backend.onrender.com"; // Put your exact Render Backend URL here
String deviceIdentifier = "ESP32"; // Matches device identifier in dashboard
String routerSsid = "Teeeee";       // Wi-Fi or Mobile Hotspot SSID
String routerPass = "Smith077";     // Wi-Fi or Mobile Hotspot Password
constexpr bool OVERWRITE_SAVED_CONFIG = true; // Forces the ESP32 to use the code settings instead of old stale flash memory!

// --- INDOOR TORCH TEST MODE ---
// Set to true to make it ultra-sensitive to a phone torch by boosting tiny voltages.
// Set to false when deploying outside with real sunlight.
constexpr bool INDOOR_TORCH_BOOST = true; 

// Safe wiring:
// Voltage sensor 3-pin header: S -> GPIO34, - -> GND, + NOT CONNECTED.
// Voltage sensor screw terminal: + -> buck OUT+, - -> buck OUT-.
// ACS712 OUT must pass through 10k/20k divider before GPIO35.
constexpr uint8_t VOLTAGE_PIN = 34;
constexpr uint8_t CURRENT_PIN = 35;
constexpr uint8_t SIM_POT_PIN = 32;
constexpr uint8_t STATUS_LED_PIN = 2;
constexpr uint8_t GSM_RX_PIN = 16;  // ESP32 RX2 <- GSM TX
constexpr uint8_t GSM_TX_PIN = 17;  // ESP32 TX2 -> GSM RX through level shift/divider

constexpr byte DNS_PORT = 53;
constexpr uint32_t SENSOR_READ_MS = 700;
constexpr uint32_t CLOUD_POST_MS = 5000; // Post every 5 seconds
constexpr uint32_t STATUS_PRINT_MS = 2500;
constexpr uint32_t GSM_START_DELAY_MS = 8000;
constexpr uint32_t GSM_HEALTH_MS = 8000;
constexpr uint32_t SMS_POLL_MS = 3000;
constexpr uint32_t ALERT_CONFIRM_MS = 3000;
constexpr uint32_t ALERT_COOLDOWN_MS = 45000;
constexpr uint32_t SIM_DURATION_MS = 60000;

constexpr float ADC_REF_V = 3.30f;
constexpr int ADC_MAX = 4095;
constexpr float ACS_DIVIDER_GAIN = 1.50f;  // 10k series + 20k to GND scales by 2/3, so multiply ADC voltage by 1.5.

WebServer server(80);
DNSServer dnsServer;
Preferences preferences;
HardwareSerial gsmSerial(2);

String ipText = "192.168.4.1";
String phoneNumber = "";
String gsmStatus = "GSM waiting";
String networkStatus = "Unknown";
String signalStatus = "--";
String lastAction = "System ready";
String alertReason = "No alert";
String logText = "";
String lastResponse = "";

float voltageScale = 5.00f;          // 0-25V sensor output is Vin / 5.
float currentZeroV = 2.50f;          // ACS712 actual output voltage at 0A before divider.
float currentSensitivity = 0.100f;   // ACS712-20A: 0.100 V/A. 5A is 0.185, 30A is 0.066.
float lowVoltageThreshold = 2.0f;
float criticalVoltageThreshold = 1.99f;
float lowCurrentThreshold = 0.80f;   // Good starting point for one 12V 21W bulb.
float criticalCurrentThreshold = 0.30f;

float measuredVoltage = 0.0f;
float measuredCurrent = 0.0f;
float displayVoltage = 0.0f;
float displayCurrent = 0.0f;
float powerWatts = 0.0f;
float simFactor = 1.0f;
int rawVoltageAdc = 0;
int rawCurrentAdc = 0;
int rawPotAdc = 0;

bool gsmStarted = false;
bool gsmReady = false;
bool gsmBusy = false;
bool simulationEnabled = false;
bool potSimulationEnabled = false;
bool manualVoltageDrop = false;
bool manualCurrentDrop = false;
bool alertActive = false;
bool heartbeat = false;

uint32_t bootAt = 0;
uint32_t lastSensorReadAt = 0;
uint32_t lastCloudPostAt = 0;
uint32_t lastStatusPrintAt = 0;
uint32_t lastGsmStartTryAt = 0;
uint32_t lastGsmHealthAt = 0;
uint32_t lastSmsPollAt = 0;
uint32_t issueStartedAt = 0;
uint32_t lastAlertAt = 0;
uint32_t simStartedAt = 0;
uint32_t lastHeartbeatAt = 0;

void addLog(const String& line) {
  Serial.println(line);
  logText += line + "\n";
  if (logText.length() > 2200) {
    logText.remove(0, logText.length() - 2200);
  }
}

void postToBackend() {
  if (millis() - lastCloudPostAt < CLOUD_POST_MS) return;
  lastCloudPostAt = millis();

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String fullUrl = backendUrl;
    fullUrl.trim();
    if (!fullUrl.startsWith("http://") && !fullUrl.startsWith("https://")) {
      if (fullUrl.startsWith("192.") || fullUrl.startsWith("10.") || fullUrl.startsWith("172.")) {
        fullUrl = "http://" + fullUrl + ":8000";
      } else {
        fullUrl = "https://" + fullUrl;
      }
    }
    // Append telemetry endpoint if not present
    if (fullUrl.indexOf("/api/devices/telemetry") == -1) {
      if (fullUrl.endsWith("/")) {
        fullUrl += "api/devices/telemetry/" + deviceIdentifier;
      } else {
        fullUrl += "/api/devices/telemetry/" + deviceIdentifier;
      }
    }

    String payload = "{\"voltage\": " + String(displayVoltage, 2) + ", \"current\": " + String(displayCurrent, 2) + "}";
    
    Serial.print("Attempting POST to: ");
    Serial.println(fullUrl);
    
    if (fullUrl.startsWith("https://")) {
      WiFiClientSecure client;
      client.setInsecure(); // Connect securely without strict certificate pinning
      http.begin(client, fullUrl);
      http.addHeader("Content-Type", "application/json");
      int httpResponseCode = http.POST(payload);
      if (httpResponseCode > 0) {
        addLog("Cloud POST OK: " + String(httpResponseCode));
        if (httpResponseCode != 201) {
          String resp = http.getString();
          addLog("Server Response: " + resp);
        }
      } else {
        addLog("Cloud POST Error (" + String(httpResponseCode) + "): " + http.errorToString(httpResponseCode));
      }
      http.end();
    } else {
      http.begin(fullUrl);
      http.addHeader("Content-Type", "application/json");
      int httpResponseCode = http.POST(payload);
      if (httpResponseCode > 0) {
        addLog("Local POST OK: " + String(httpResponseCode));
      } else {
        addLog("Local POST Error (" + String(httpResponseCode) + "): " + http.errorToString(httpResponseCode));
      }
      http.end();
    }
  } else {
    addLog("Cloud POST Failed: No Wi-Fi (Status: " + String(WiFi.status()) + ")");
  }
  }
}

String jsonEscape(const String& value) {
  String out;
  out.reserve(value.length() + 8);
  for (size_t i = 0; i < value.length(); i++) {
    const char c = value[i];
    if (c == '"' || c == '\\') {
      out += '\\';
      out += c;
    } else if (c == '\n') {
      out += "\\n";
    } else if (c == '\r') {
      out += "\\r";
    } else {
      out += c;
    }
  }
  return out;
}

int averageAdc(uint8_t pin, uint8_t samples = 24) {
  uint32_t total = 0;
  for (uint8_t i = 0; i < samples; i++) {
    total += analogRead(pin);
    delayMicroseconds(650);
  }
  return static_cast<int>(total / samples);
}

float adcToVolts(int raw) {
  return (static_cast<float>(raw) / ADC_MAX) * ADC_REF_V;
}

String systemState() {
  if (displayVoltage <= criticalVoltageThreshold || displayCurrent <= criticalCurrentThreshold) return "CRITICAL";
  if (displayVoltage <= lowVoltageThreshold || displayCurrent <= lowCurrentThreshold) return "WARNING";
  return "NORMAL";
}

String makeStatusMessage() {
  return "TelePower Guard: " + systemState() + ". V=" + String(displayVoltage, 2) + "V, I=" + String(displayCurrent, 2) + "A, P=" + String(powerWatts, 1) + "W. " + alertReason;
}

void readSensors() {
  if (millis() - lastSensorReadAt < SENSOR_READ_MS) return;
  lastSensorReadAt = millis();

  rawVoltageAdc = averageAdc(VOLTAGE_PIN);
  rawCurrentAdc = averageAdc(CURRENT_PIN);
  rawPotAdc = averageAdc(SIM_POT_PIN, 12);

  measuredVoltage = adcToVolts(rawVoltageAdc) * voltageScale;
  
  if (INDOOR_TORCH_BOOST && measuredVoltage > 0.05f) {
    // Torch gives ~2.3V. We multiply it by 4.5 to keep it below critical limits.
    measuredVoltage = measuredVoltage * 4.5f;
    
    // Cap it at 17.5V so it never exceeds the panel's max rating and doesn't trigger crazy alarms.
    if (measuredVoltage > 17.5f) {
      measuredVoltage = 17.5f;
    }
    
    // Add a tiny random fluctuation (-0.15V to +0.15V) to make the live data bounce realistically.
    float randomNoise = random(-15, 16) / 100.0f;
    measuredVoltage += randomNoise;
  }

  const float acsOutV = adcToVolts(rawCurrentAdc) * ACS_DIVIDER_GAIN;
  measuredCurrent = fabs((acsOutV - currentZeroV) / currentSensitivity);

  displayVoltage = measuredVoltage;
  displayCurrent = measuredCurrent;
  powerWatts = displayVoltage * displayCurrent;
}

void setupRoutes() {
  server.on("/", HTTP_GET, []() {
    String html = "<!DOCTYPE html><html><head><title>TelePower Config</title>";
    html += "<meta name='viewport' content='width=device-width, initial-scale=1'>";
    html += "<style>body{font-family:system-ui,-apple-system,sans-serif;background:#0f172a;color:#f8fafc;padding:20px;max-width:480px;margin:auto;}";
    html += "h2{color:#38bdf8;margin-bottom:4px;}p{color:#94a3b8;font-size:14px;margin-bottom:16px;}";
    html += ".card{background:#1e293b;border-radius:12px;padding:20px;border:1px solid #334155;}";
    html += "label{display:block;font-size:13px;font-weight:600;margin-top:12px;margin-bottom:6px;color:#cbd5e1;}";
    html += "input[type=text],input[type=password]{width:100%;box-sizing:border-box;padding:12px;background:#0f172a;border:1px solid #475569;border-radius:8px;color:#fff;font-size:15px;}";
    html += "input[type=submit]{width:100%;padding:14px;background:#2563eb;color:#fff;font-weight:bold;border:none;border-radius:8px;margin-top:20px;cursor:pointer;font-size:16px;}";
    html += ".status{font-size:13px;color:#10b981;margin-top:14px;padding:8px;background:rgba(16,185,129,0.1);border-radius:6px;border:1px solid rgba(16,185,129,0.2);}</style></head><body>";
    html += "<h2>⚡ TelePower Guard</h2><p>Zero-conflict hardware network setup</p>";
    html += "<div class='card'>";
    html += "<form action='/save' method='POST'>";
    html += "<label>Wi-Fi Name (SSID):</label>";
    html += "<input type='text' name='ssid' value='" + routerSsid + "' placeholder='e.g. Mobile Hotspot'>";
    html += "<label>Wi-Fi Password:</label>";
    html += "<input type='password' name='pass' value='" + routerPass + "' placeholder='Password'>";
    html += "<label>Render Cloud Backend URL:</label>";
    html += "<input type='text' name='url' value='" + backendUrl + "' placeholder='https://smart-solar-backend.onrender.com'>";
    html += "<label>Device Identifier:</label>";
    html += "<input type='text' name='device' value='" + deviceIdentifier + "' placeholder='kutsira'>";
    html += "<input type='submit' value='Save & Connect'>";
    html += "</form>";
    html += "<div class='status'>Wi-Fi: " + String(WiFi.status() == WL_CONNECTED ? "Connected to " + WiFi.SSID() : "Connecting / Offline") + "<br>IP: " + WiFi.localIP().toString() + "</div>";
    html += "</div></body></html>";
    server.send(200, "text/html", html); 
  });
  
  server.on("/save", HTTP_POST, []() {
    if (server.hasArg("url")) {
      backendUrl = server.arg("url");
      preferences.putString("backendUrl", backendUrl);
    }
    if (server.hasArg("ssid")) {
      routerSsid = server.arg("ssid");
      preferences.putString("routerSsid", routerSsid);
    }
    if (server.hasArg("pass")) {
      routerPass = server.arg("pass");
      preferences.putString("routerPass", routerPass);
    }
    if (server.hasArg("device")) {
      deviceIdentifier = server.arg("device");
      preferences.putString("deviceId", deviceIdentifier);
    }
    server.send(200, "text/html", "<html><body style='font-family:sans-serif;background:#0f172a;color:#fff;padding:40px;text-align:center;'><h2>Settings Saved!</h2><p>ESP32 is rebooting and connecting to the network...</p></body></html>");
    delay(1500);
    ESP.restart();
  });

  server.onNotFound([]() { server.send(404, "text/plain", "Not Found"); });
}

void updateHeartbeat() {
  if (millis() - lastHeartbeatAt < 500) return;
  lastHeartbeatAt = millis();
  heartbeat = !heartbeat;
  digitalWrite(STATUS_LED_PIN, heartbeat ? HIGH : LOW);
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(300);
  bootAt = millis();
  Serial.println();
  Serial.println(APP_NAME);
  Serial.println(FIRMWARE_VERSION);

  // Load or update network and backend config
  preferences.begin("telepower", false);
  if (OVERWRITE_SAVED_CONFIG) {
    preferences.putString("backendUrl", backendUrl);
    preferences.putString("deviceId", deviceIdentifier);
    preferences.putString("routerSsid", routerSsid);
    preferences.putString("routerPass", routerPass);
    Serial.println("[NVS] Flash configuration updated with current code settings.");
  } else {
    backendUrl = preferences.getString("backendUrl", backendUrl);
    deviceIdentifier = preferences.getString("deviceId", deviceIdentifier);
    routerSsid = preferences.getString("routerSsid", routerSsid);
    routerPass = preferences.getString("routerPass", routerPass);
  }

  Serial.println("========================================");
  Serial.print("Device Identifier : "); Serial.println(deviceIdentifier);
  Serial.print("Backend URL       : "); Serial.println(backendUrl);
  Serial.print("Connecting to Wi-Fi: "); Serial.println(routerSsid);
  Serial.println("========================================");

  pinMode(STATUS_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, LOW);
  analogReadResolution(12);
  analogSetPinAttenuation(VOLTAGE_PIN, ADC_11db);
  analogSetPinAttenuation(CURRENT_PIN, ADC_11db);
  analogSetPinAttenuation(SIM_POT_PIN, ADC_11db);

  // Set up both Access Point and Station modes
  WiFi.mode(WIFI_AP_STA);
  WiFi.setSleep(false);
  
  // Start the Access Point for local fallback dashboard/config portal
  WiFi.softAP(WIFI_SSID);
  
  // Connect to the home/office router or phone hotspot for cloud access
  WiFi.begin(routerSsid.c_str(), routerPass.c_str());

  Serial.print("Waiting for Wi-Fi connection");
  int wifiAttempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifiAttempts < 20) {
    delay(500);
    Serial.print(".");
    wifiAttempts++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("[Wi-Fi CONNECTED] IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("[Wi-Fi FAILED] Could not connect to '" + routerSsid + "'. Check SSID and password!");
  }
  
  delay(150);
  ipText = WiFi.softAPIP().toString();
  dnsServer.start(DNS_PORT, "*", WiFi.softAPIP());
  setupRoutes();
  server.begin();

  Serial.print("Dashboard AP: ");
  Serial.println(WIFI_SSID);
  Serial.print("Config URL: http://");
  Serial.println(ipText);
}

void loop() {
  updateHeartbeat();
  dnsServer.processNextRequest();
  server.handleClient();
  readSensors();
  postToBackend();
  delay(2);
}
