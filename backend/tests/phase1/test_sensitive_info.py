#!/usr/bin/env python3
"""
Test Suite: 1.4 Sensitive Information Exposure
Phase: 1 - Critical Security
Purpose: Verify that sensitive information is not exposed through API responses

Tests:
1. User enumeration protection in login endpoint
2. verification_notes field not exposed in location API

Security Impact:
- User enumeration allows attackers to discover valid usernames/emails
- verification_notes contains staff-only internal data about location verification

Expected Results:
- Login returns same generic error for invalid username and wrong password
- Location API response does not include verification_notes field
"""

import requests
import json
from time import sleep

# Configuration
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/login/"
REGISTER_URL = f"{BASE_URL}/register/"
LOCATION_API_URL = f"{BASE_URL}/api/locations/"

# Test user credentials
TEST_USER = {
    'username': 'test_sensitive_user',
    'email': 'test_sensitive@example.com',
    'first_name': 'Test',
    'last_name': 'User',
    'password1': 'SecurePassword123!@#',
    'password2': 'SecurePassword123!@#'
}

def get_csrf_token(session):
    """Get CSRF token from login page"""
    response = session.get(LOGIN_URL)
    return session.cookies.get('csrftoken')

def register_test_user(session):
    """Register a test user for login enumeration tests"""
    csrf_token = get_csrf_token(session)
    response = session.post(
        REGISTER_URL,
        json=TEST_USER,
        headers={'X-CSRFToken': csrf_token}
    )
    return response

def test_user_enumeration_protection():
    """
    Test 1: User Enumeration Protection

    Verify that login endpoint returns same generic error for:
    - Non-existent username/email
    - Valid username but wrong password

    This prevents attackers from discovering valid usernames.
    """
    print("\n" + "="*80)
    print("TEST 1: User Enumeration Protection")
    print("="*80)

    # Wait for any previous rate limits to expire
    print("\nWaiting 15 seconds for rate limits to reset...")
    sleep(15)

    session = requests.Session()

    # First, register a test user
    print("\n1.1 Registering test user...")
    register_response = register_test_user(session)

    if register_response.status_code == 201:
        print("✅ Test user registered successfully")
    elif 'already' in register_response.json().get('detail', '').lower():
        print("ℹ️  Test user already exists (this is fine)")
    else:
        print(f"❌ Failed to register test user: {register_response.json()}")
        return False

    # Test 1.2: Non-existent user login attempt
    print("\n1.2 Testing login with non-existent user...")
    session_nonexistent = requests.Session()
    csrf_token = get_csrf_token(session_nonexistent)

    nonexistent_response = session_nonexistent.post(
        LOGIN_URL,
        json={
            'username': 'this_user_definitely_does_not_exist_12345',
            'password': 'RandomPassword123'
        },
        headers={'X-CSRFToken': csrf_token}
    )

    # Check for throttle response
    if nonexistent_response.status_code == 429:
        print(f"   ⚠️  Rate limited - waiting 30 seconds...")
        sleep(30)
        # Retry
        csrf_token = get_csrf_token(session_nonexistent)
        nonexistent_response = session_nonexistent.post(
            LOGIN_URL,
            json={
                'username': 'this_user_definitely_does_not_exist_12345',
                'password': 'RandomPassword123'
            },
            headers={'X-CSRFToken': csrf_token}
        )

    nonexistent_error = nonexistent_response.json().get('detail', '')
    print(f"   Status: {nonexistent_response.status_code}")
    print(f"   Error message: \"{nonexistent_error}\"")

    # Wait to avoid rate limiting (5 req/min = 12 seconds between requests)
    print("\n   Waiting 13 seconds to avoid rate limiting...")
    sleep(13)

    # Test 1.3: Valid user but wrong password
    print("\n1.3 Testing login with valid user but wrong password...")
    session_wrong_pass = requests.Session()
    csrf_token = get_csrf_token(session_wrong_pass)

    wrong_password_response = session_wrong_pass.post(
        LOGIN_URL,
        json={
            'username': TEST_USER['username'],
            'password': 'DefinitelyWrongPassword123'
        },
        headers={'X-CSRFToken': csrf_token}
    )

    # Check for throttle response
    if wrong_password_response.status_code == 429:
        error_msg = wrong_password_response.json().get('detail', '')
        # Extract wait time from error message (e.g., "Expected available in 17 seconds")
        import re
        match = re.search(r'(\d+)\s+seconds', error_msg)
        wait_time = int(match.group(1)) + 2 if match else 30  # Add 2 seconds buffer
        print(f"   ⚠️  Rate limited - waiting {wait_time} seconds...")
        sleep(wait_time)
        # Retry
        csrf_token = get_csrf_token(session_wrong_pass)
        wrong_password_response = session_wrong_pass.post(
            LOGIN_URL,
            json={
                'username': TEST_USER['username'],
                'password': 'DefinitelyWrongPassword123'
            },
            headers={'X-CSRFToken': csrf_token}
        )

    wrong_password_error = wrong_password_response.json().get('detail', '')
    print(f"   Status: {wrong_password_response.status_code}")
    print(f"   Error message: \"{wrong_password_error}\"")

    # Verify both errors are identical
    print("\n1.4 Verifying error messages are identical...")
    if nonexistent_error == wrong_password_error:
        print(f"✅ PASS: Both return same generic error")
        print(f"   Message: \"{nonexistent_error}\"")
    else:
        print(f"❌ FAIL: Error messages differ (allows user enumeration)")
        print(f"   Non-existent user: \"{nonexistent_error}\"")
        print(f"   Wrong password:    \"{wrong_password_error}\"")
        return False

    # Verify error doesn't reveal if user exists
    print("\n1.5 Verifying error message is appropriately generic...")
    forbidden_phrases = [
        'no account',
        'user not found',
        'email not found',
        'username not found',
        'incorrect password',
        'wrong password',
        'password is wrong',
        'does not exist'
    ]

    error_lower = nonexistent_error.lower()
    reveals_info = any(phrase in error_lower for phrase in forbidden_phrases)

    if reveals_info:
        print(f"❌ FAIL: Error message reveals too much information")
        print(f"   Message: \"{nonexistent_error}\"")
        return False
    else:
        print(f"✅ PASS: Error message is generic and secure")

    # Verify status code is 401 Unauthorized (not 404)
    print("\n1.6 Verifying status code is 401 Unauthorized...")
    if nonexistent_response.status_code == 401 and wrong_password_response.status_code == 401:
        print(f"✅ PASS: Both return 401 Unauthorized")
    else:
        print(f"❌ FAIL: Status codes differ")
        print(f"   Non-existent: {nonexistent_response.status_code}")
        print(f"   Wrong password: {wrong_password_response.status_code}")
        return False

    print("\n" + "-"*80)
    print("✅ TEST 1 PASSED: User enumeration protection working correctly")
    print("-"*80)
    return True


def test_verification_notes_not_exposed():
    """
    Test 2: verification_notes Field Not Exposed

    Verify that the verification_notes field (staff-only internal data)
    is not included in the location API response.
    """
    print("\n" + "="*80)
    print("TEST 2: Verification Notes Not Exposed")
    print("="*80)

    print("\n2.1 Fetching location list from API...")
    response = requests.get(LOCATION_API_URL)

    if response.status_code != 200:
        print(f"❌ FAIL: Could not fetch locations (status {response.status_code})")
        return False

    data = response.json()
    locations = data.get('results', [])

    if not locations:
        print("⚠️  WARNING: No locations in database to test")
        print("   This test requires at least one location to exist")
        print("   Skipping verification_notes check...")
        return True

    print(f"✅ Successfully fetched {len(locations)} location(s)")

    # Check each location for verification_notes field
    print("\n2.2 Checking if verification_notes is exposed...")
    found_verification_notes = False

    for i, location in enumerate(locations, 1):
        if 'verification_notes' in location:
            found_verification_notes = True
            print(f"❌ FAIL: verification_notes found in location {i}")
            print(f"   Location: {location.get('name', 'Unknown')}")
            print(f"   Exposed field: verification_notes = \"{location['verification_notes']}\"")
            break

    if not found_verification_notes:
        print(f"✅ PASS: verification_notes not exposed in any location")

        # Show example of fields that ARE exposed (for verification)
        print("\n2.3 Example of exposed fields (first location):")
        first_location = locations[0]
        exposed_fields = list(first_location.keys())
        print(f"   Fields: {', '.join(exposed_fields)}")

        # Verify other verification fields ARE still exposed (they're public)
        expected_public_fields = ['is_verified', 'verification_date', 'verified_by']
        public_fields_present = [f for f in expected_public_fields if f in exposed_fields]

        print(f"\n2.4 Verifying public verification fields are still present...")
        if public_fields_present:
            print(f"✅ Public fields present: {', '.join(public_fields_present)}")
        else:
            print(f"ℹ️  Note: No public verification fields in response")

    if found_verification_notes:
        print("\n" + "-"*80)
        print("❌ TEST 2 FAILED: verification_notes is exposed to public")
        print("-"*80)
        return False

    print("\n" + "-"*80)
    print("✅ TEST 2 PASSED: verification_notes properly hidden")
    print("-"*80)
    return True


def run_all_tests():
    """Run all sensitive information exposure tests"""
    print("\n" + "="*80)
    print("PHASE 1 TEST SUITE: 1.4 Sensitive Information Exposure")
    print("="*80)
    print("\nTesting two security vulnerabilities:")
    print("1. User enumeration through login errors")
    print("2. Exposure of staff-only verification_notes field")

    results = []

    # Run tests
    results.append(("User Enumeration Protection", test_user_enumeration_protection()))
    results.append(("Verification Notes Hidden", test_verification_notes_not_exposed()))

    # Summary
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result[1] for result in results)

    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL TESTS PASSED - 1.4 Sensitive Information Exposure Fixed")
    else:
        print("❌ SOME TESTS FAILED - Review output above")
    print("="*80 + "\n")

    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
