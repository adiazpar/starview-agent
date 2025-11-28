#!/usr/bin/env python3
"""
Password Reset Rate Limiting Test

Tests the improved rate limiting (3/hour vs 5/minute) to ensure
better UX while still preventing email bombing attacks.
"""

import os
import sys
import requests
import time

# Test configuration
BASE_URL = 'http://127.0.0.1:8000'
TEST_EMAIL = 'alexdiaz0923@gmail.com'


def test_rate_limiting():
    """Test password reset rate limiting"""
    print("\n" + "=" * 80)
    print("  PASSWORD RESET RATE LIMITING TEST")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  - Rate limit: 3 requests per hour")
    print(f"  - Test email: {TEST_EMAIL}")
    print(f"\n" + "-" * 80)

    # Attempt 4 requests quickly (should allow 3, block 4th)
    results = []

    for i in range(4):
        print(f"\n[Attempt {i+1}] Requesting password reset...")

        response = requests.post(
            f'{BASE_URL}/api/auth/password-reset/',
            json={'email': TEST_EMAIL},
            headers={'Content-Type': 'application/json'}
        )

        print(f"  Status Code: {response.status_code}")

        if response.status_code == 200:
            print(f"  ✓ Request accepted")
            results.append('PASS')
        elif response.status_code == 429:
            print(f"  ✗ Rate limited (Too Many Requests)")
            data = response.json()
            print(f"  Message: {data.get('detail', 'No message')}")
            results.append('THROTTLED')
        else:
            print(f"  ✗ Unexpected status: {response.status_code}")
            results.append('ERROR')

        time.sleep(1)  # Small delay between requests

    # Summary
    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)

    passed = results.count('PASS')
    throttled = results.count('THROTTLED')

    print(f"\n  Requests accepted: {passed}/4")
    print(f"  Requests throttled: {throttled}/4")

    if passed == 3 and throttled == 1:
        print("\n  ✓ CORRECT: 3 requests allowed, 4th throttled")
        print("  ✓ Rate limiting working as expected (3/hour)")
        return 0
    else:
        print(f"\n  ✗ UNEXPECTED: Expected 3 allowed + 1 throttled")
        print(f"  ✗ Got: {passed} allowed + {throttled} throttled")
        return 1


if __name__ == '__main__':
    try:
        exit_code = test_rate_limiting()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
