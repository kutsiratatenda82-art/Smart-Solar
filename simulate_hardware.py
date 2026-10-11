"""
Hardware Simulator - Mimics the ESP32 posting telemetry data to the backend.
Run this to test the dashboard while debugging the actual hardware connection.
Posts voltage/current readings every 5 seconds, just like the real TelePowerGuard.
"""
import sys
import os
import requests
import time
import random
import math

# Automatically supports Render cloud URL (e.g. python simulate_hardware.py https://smart-solar-backend.onrender.com)
RAW_URL = sys.argv[1] if len(sys.argv) > 1 else os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
RAW_URL = RAW_URL.rstrip("/")
if not RAW_URL.endswith("/kutsira"):
    BACKEND_URL = f"{RAW_URL}/api/devices/telemetry/kutsira"
else:
    BACKEND_URL = RAW_URL

def simulate():
    print("Hardware Simulator Started")
    print(f"   Posting to: {BACKEND_URL}")
    print(f"   Press Ctrl+C to stop\n")
    
    t = 0
    while True:
        # Simulate realistic solar panel readings with slight fluctuation
        base_voltage = 13.5 + 2.0 * math.sin(t * 0.05)  # Slow oscillation 11.5V - 15.5V
        base_current = 2.8 + 0.8 * math.sin(t * 0.03)    # Slow oscillation 2.0A - 3.6A
        
        voltage = round(base_voltage + random.uniform(-0.3, 0.3), 2)
        current = round(base_current + random.uniform(-0.15, 0.15), 2)
        
        payload = {"voltage": voltage, "current": current}
        
        try:
            r = requests.post(BACKEND_URL, json=payload, timeout=5)
            if r.status_code == 201:
                print(f"OK | V={voltage:.2f}V  I={current:.2f}A  P={voltage*current:.1f}W")
            else:
                print(f"POST {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"Connection Error: {e}")
        
        t += 1
        time.sleep(5)

if __name__ == "__main__":
    simulate()
