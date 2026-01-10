import requests
import json

url = "http://localhost:11434/api/generate"
payload = {
    "model": "mistral:7b-instruct",
    "prompt": "Say 'System Operational' if you can hear me.",
    "stream": False
}

try:
    print(f"Testing connection to {url}...")
    response = requests.post(url, json=payload, timeout=30)
    if response.status_code == 200:
        print("✅ SUCCESS!")
        print("Response:", response.json().get("response"))
    else:
        print(f"❌ ERROR: Status {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ EXCEPTION: {e}")
