# test_round2.py
import requests
import time
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path('.').resolve() / '.env')
MY_SECRET = os.getenv("MY_SECRET")

API_URL = "http://localhost:8000/api/build"

# IMPORTANT: Use the SAME task name from Round 1
test_request = {
    "email": "student@example.com",
    "secret": MY_SECRET,
    "task": "hello-world-test",  # ← SAME as Round 1
    "round": 2,  # ← NOW ROUND 2
    "nonce": "test-nonce-round2-" + str(int(time.time())),
    "brief": "Add a Bootstrap button with id='click-me' that shows an alert 'Button clicked!' when clicked.",
    "checks": [
        "Page still has h1#hello with 'Hello World'",
        "Page has button#click-me",
        "Button shows alert when clicked"
    ],
    "evaluation_url": "https://webhook.site/YOUR-UNIQUE-URL",  # Same as before
    "attachments": []
}

print("TESTING ROUND 2 UPDATE")
print("=" * 60)

response = requests.post(API_URL, json=test_request, headers={"Content-Type": "application/json"})
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200:
    print("\n✅ Round 2 accepted!")
    print("Wait 30-60 seconds, then check:")
    print("1. webhook.site for notification")
    print("2. GitHub repo - should have new commit")
    print("3. GitHub Pages - should show the button")
else:
    print("❌ FAILED")