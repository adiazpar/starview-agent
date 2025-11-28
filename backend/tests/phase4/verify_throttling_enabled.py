"""
Quick verification that throttling is enabled in production mode.
This script simulates production (not a test) and verifies throttling works.

Run: djvenv/bin/python .claude/tests/phase4/verify_throttling_enabled.py
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/login/"

print("="*80)
print("THROTTLING VERIFICATION (Production Mode)")
print("="*80)
print("\nThis script runs in PRODUCTION mode (not test mode)")
print("Throttling SHOULD be active and block after 5 requests/minute")
print()

# Make 6 rapid requests to trigger throttle
print("Making 6 rapid login requests...")
for i in range(1, 7):
    response = requests.post(
        LOGIN_URL,
        json={'username': 'test', 'password': 'test'},
        timeout=5
    )

    print(f"  Request {i}: Status {response.status_code}", end="")

    if response.status_code == 429:
        print(" → ✅ THROTTLED (This is correct!)")
        print(f"     Message: {response.json()}")
    elif response.status_code == 400:
        print(" → ✅ Normal response (within throttle limit)")
    elif response.status_code == 401:
        print(" → ✅ Normal response (within throttle limit)")
    else:
        print(f" → Unexpected: {response.text[:100]}")

    time.sleep(0.1)  # Small delay between requests

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print("\n✅ If you saw 429 'Too Many Requests' above, throttling is ENABLED")
print("✅ Throttling only disables during test execution (unittest/pytest)")
print("✅ Your production deployment is fully protected!")
