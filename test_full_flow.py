# test_full_flow.py
import requests
import time
import json

# Your local server URL (or deployed URL later)
API_URL = "http://localhost:8000/api/build"

# Test request payload
test_request = {
    "email": "23f1002234@ds.study.iitm.ac.in",  # Change this to your actual email
    "secret": "Robin@1234",  # Change this to match your .env MY_SECRET
    "task": "hello-world-test",
    "round": 1,
    "nonce": "test-nonce-" + str(int(time.time())),
    "brief": "Create a simple Hello World page that displays today's date. The page must have an h1 element with id='hello' containing 'Hello World', and a paragraph with id='date' showing today's date in YYYY-MM-DD format.",
    "checks": [
        "Repo has MIT LICENSE",
        "README.md exists and is professional",
        "Page has h1#hello with text 'Hello World'",
        "Page has element #date showing current date",
        "Page uses Bootstrap CSS from CDN"
    ],
    "evaluation_url": "https://webhook.site/8d97e792-5036-4a58-bc9c-907a9f811a32",  # Get from webhook.site
    "attachments": []
}

print("=" * 60)
print("TESTING FULL DEPLOYMENT FLOW")
print("=" * 60)

# Step 1: Send request to your API
print("\n1. Sending request to API...")
print(f"   URL: {API_URL}")

try:
    response = requests.post(
        API_URL,
        json=test_request,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code != 200:
        print("❌ FAILED: API did not return 200")
        exit(1)
    
    print("✅ API accepted the request")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit(1)

# Step 2: Wait for background processing
print("\n2. Waiting for background processing...")
print("   (This may take 30-90 seconds)")

# Monitor your webhook.site to see when the notification arrives
input("\n   Press ENTER after you see the notification on webhook.site...")

# Step 3: Manual verification checklist
print("\n3. MANUAL VERIFICATION CHECKLIST:")
print("   Go to webhook.site and check the received payload")
print("   It should contain:")
print("   - ✓ email")
print("   - ✓ task")
print("   - ✓ round: 1")
print("   - ✓ nonce")
print("   - ✓ repo_url (GitHub repo link)")
print("   - ✓ commit_sha")
print("   - ✓ pages_url (GitHub Pages link)")

print("\n4. Visit the GitHub repo and check:")
print("   - ✓ Repo exists and is public")
print("   - ✓ Has index.html file")
print("   - ✓ Has README.md file")
print("   - ✓ Has LICENSE file (MIT)")

print("\n5. Visit the GitHub Pages URL and check:")
print("   - ✓ Page loads (might take 1-2 minutes)")
print("   - ✓ Has 'Hello World' in h1#hello")
print("   - ✓ Shows today's date")
print("   - ✓ Uses Bootstrap styling")

print("\n" + "=" * 60)
print("TEST COMPLETE - Check all items above!")
print("=" * 60)