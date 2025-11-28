#!/usr/bin/env python3
"""
Test Suite: 1.6 Geographic Coordinate Validation
Phase: 1 - Critical Security
Purpose: Verify that geographic coordinates are validated before storage

Tests:
1. Latitude validation (must be -90 to 90)
2. Longitude validation (must be -180 to 180)
3. Elevation validation (must be -500m to 9000m)
4. Valid coordinates are accepted

Security Impact:
- Prevents invalid coordinates from breaking map rendering
- Prevents database corruption from impossible values
- Prevents potential injection attacks via coordinate fields

Expected Results:
- Latitude outside -90 to 90 rejected
- Longitude outside -180 to 180 rejected
- Elevation outside -500 to 9000 rejected
- Valid coordinates accepted successfully
"""

import requests
from time import sleep

# Configuration
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/login/"
REGISTER_URL = f"{BASE_URL}/register/"
LOCATION_API_URL = f"{BASE_URL}/api/locations/"

# Test user credentials
TEST_USER = {
    'username': 'test_coordinate_user',
    'email': 'test_coordinate@example.com',
    'first_name': 'Test',
    'last_name': 'Coordinate',
    'password1': 'SecurePassword123!@#',
    'password2': 'SecurePassword123!@#'
}

def get_csrf_token(session):
    """Get CSRF token from login page"""
    response = session.get(LOGIN_URL)
    return session.cookies.get('csrftoken')

def register_and_login(session):
    """Register and login test user"""
    csrf_token = get_csrf_token(session)

    # Try to register
    register_response = session.post(
        REGISTER_URL,
        json=TEST_USER,
        headers={'X-CSRFToken': csrf_token}
    )

    # If user already exists, just login
    if register_response.status_code != 201:
        csrf_token = get_csrf_token(session)
        session.post(
            LOGIN_URL,
            json={
                'username': TEST_USER['username'],
                'password': TEST_USER['password1']
            },
            headers={'X-CSRFToken': csrf_token}
        )

    return session


def test_latitude_validation(session):
    """
    Test 1: Latitude Validation

    Verify that latitude values outside -90 to 90 are rejected.
    """
    print("\n" + "="*80)
    print("TEST 1: Latitude Validation")
    print("="*80)

    test_cases = [
        {
            'name': 'Valid latitude (equator)',
            'latitude': 0,
            'longitude': 0,
            'elevation': 0,
            'should_pass': True
        },
        {
            'name': 'Valid latitude (North Pole)',
            'latitude': 90,
            'longitude': 0,
            'elevation': 0,
            'should_pass': True
        },
        {
            'name': 'Valid latitude (South Pole)',
            'latitude': -90,
            'longitude': 0,
            'elevation': 0,
            'should_pass': True
        },
        {
            'name': 'Invalid latitude (too high)',
            'latitude': 91,
            'longitude': 0,
            'elevation': 0,
            'should_pass': False
        },
        {
            'name': 'Invalid latitude (too low)',
            'latitude': -91,
            'longitude': 0,
            'elevation': 0,
            'should_pass': False
        },
        {
            'name': 'Invalid latitude (way out of range)',
            'latitude': 999,
            'longitude': 0,
            'elevation': 0,
            'should_pass': False
        }
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        print(f"\n1.{i} Testing: {test['name']}")
        print(f"   Coordinates: ({test['latitude']}, {test['longitude']}, {test['elevation']}m)")

        csrf_token = get_csrf_token(session)

        location_data = {
            'name': f"Test Location {i}",
            'latitude': test['latitude'],
            'longitude': test['longitude'],
            'elevation': test['elevation']
        }

        response = session.post(
            LOCATION_API_URL,
            json=location_data,
            headers={'X-CSRFToken': csrf_token}
        )

        if test['should_pass']:
            if response.status_code == 201:
                print(f"   ✅ PASS: Valid coordinates accepted")
                # Clean up
                location_id = response.json()['id']
                csrf_token = get_csrf_token(session)
                session.delete(
                    f"{LOCATION_API_URL}{location_id}/",
                    headers={'X-CSRFToken': csrf_token}
                )
            else:
                print(f"   ❌ FAIL: Valid coordinates rejected")
                print(f"   Response: {response.json()}")
                all_passed = False
        else:
            if response.status_code == 400:
                error_msg = response.json()
                print(f"   ✅ PASS: Invalid coordinates rejected")
                print(f"   Error: {error_msg}")
            else:
                print(f"   ❌ FAIL: Invalid coordinates accepted (status {response.status_code})")
                all_passed = False

        sleep(0.3)

    if all_passed:
        print("\n" + "-"*80)
        print("✅ TEST 1 PASSED: Latitude validation working correctly")
        print("-"*80)
    else:
        print("\n" + "-"*80)
        print("❌ TEST 1 FAILED: Latitude validation issues")
        print("-"*80)

    return all_passed


def test_longitude_validation(session):
    """
    Test 2: Longitude Validation

    Verify that longitude values outside -180 to 180 are rejected.
    """
    print("\n" + "="*80)
    print("TEST 2: Longitude Validation")
    print("="*80)

    test_cases = [
        {
            'name': 'Valid longitude (prime meridian)',
            'latitude': 0,
            'longitude': 0,
            'elevation': 0,
            'should_pass': True
        },
        {
            'name': 'Valid longitude (date line east)',
            'latitude': 0,
            'longitude': 180,
            'elevation': 0,
            'should_pass': True
        },
        {
            'name': 'Valid longitude (date line west)',
            'latitude': 0,
            'longitude': -180,
            'elevation': 0,
            'should_pass': True
        },
        {
            'name': 'Invalid longitude (too high)',
            'latitude': 0,
            'longitude': 181,
            'elevation': 0,
            'should_pass': False
        },
        {
            'name': 'Invalid longitude (too low)',
            'latitude': 0,
            'longitude': -181,
            'elevation': 0,
            'should_pass': False
        },
        {
            'name': 'Invalid longitude (way out of range)',
            'latitude': 0,
            'longitude': 500,
            'elevation': 0,
            'should_pass': False
        }
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        print(f"\n2.{i} Testing: {test['name']}")
        print(f"   Coordinates: ({test['latitude']}, {test['longitude']}, {test['elevation']}m)")

        csrf_token = get_csrf_token(session)

        location_data = {
            'name': f"Test Location {i}",
            'latitude': test['latitude'],
            'longitude': test['longitude'],
            'elevation': test['elevation']
        }

        response = session.post(
            LOCATION_API_URL,
            json=location_data,
            headers={'X-CSRFToken': csrf_token}
        )

        if test['should_pass']:
            if response.status_code == 201:
                print(f"   ✅ PASS: Valid coordinates accepted")
                # Clean up
                location_id = response.json()['id']
                csrf_token = get_csrf_token(session)
                session.delete(
                    f"{LOCATION_API_URL}{location_id}/",
                    headers={'X-CSRFToken': csrf_token}
                )
            else:
                print(f"   ❌ FAIL: Valid coordinates rejected")
                print(f"   Response: {response.json()}")
                all_passed = False
        else:
            if response.status_code == 400:
                error_msg = response.json()
                print(f"   ✅ PASS: Invalid coordinates rejected")
                print(f"   Error: {error_msg}")
            else:
                print(f"   ❌ FAIL: Invalid coordinates accepted (status {response.status_code})")
                all_passed = False

        sleep(0.3)

    if all_passed:
        print("\n" + "-"*80)
        print("✅ TEST 2 PASSED: Longitude validation working correctly")
        print("-"*80)
    else:
        print("\n" + "-"*80)
        print("❌ TEST 2 FAILED: Longitude validation issues")
        print("-"*80)

    return all_passed


def test_elevation_validation(session):
    """
    Test 3: Elevation Validation

    Verify that elevation values outside -500m to 9000m are rejected.
    """
    print("\n" + "="*80)
    print("TEST 3: Elevation Validation")
    print("="*80)

    test_cases = [
        {
            'name': 'Valid elevation (sea level)',
            'latitude': 0,
            'longitude': 0,
            'elevation': 0,
            'should_pass': True
        },
        {
            'name': 'Valid elevation (Dead Sea)',
            'latitude': 0,
            'longitude': 0,
            'elevation': -500,
            'should_pass': True
        },
        {
            'name': 'Valid elevation (Mount Everest)',
            'latitude': 0,
            'longitude': 0,
            'elevation': 9000,
            'should_pass': True
        },
        {
            'name': 'Invalid elevation (too high)',
            'latitude': 0,
            'longitude': 0,
            'elevation': 10000,
            'should_pass': False
        },
        {
            'name': 'Invalid elevation (too low)',
            'latitude': 0,
            'longitude': 0,
            'elevation': -600,
            'should_pass': False
        }
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        print(f"\n3.{i} Testing: {test['name']}")
        print(f"   Coordinates: ({test['latitude']}, {test['longitude']}, {test['elevation']}m)")

        csrf_token = get_csrf_token(session)

        location_data = {
            'name': f"Test Location {i}",
            'latitude': test['latitude'],
            'longitude': test['longitude'],
            'elevation': test['elevation']
        }

        response = session.post(
            LOCATION_API_URL,
            json=location_data,
            headers={'X-CSRFToken': csrf_token}
        )

        if test['should_pass']:
            if response.status_code == 201:
                print(f"   ✅ PASS: Valid elevation accepted")
                # Clean up
                location_id = response.json()['id']
                csrf_token = get_csrf_token(session)
                session.delete(
                    f"{LOCATION_API_URL}{location_id}/",
                    headers={'X-CSRFToken': csrf_token}
                )
            else:
                print(f"   ❌ FAIL: Valid elevation rejected")
                print(f"   Response: {response.json()}")
                all_passed = False
        else:
            if response.status_code == 400:
                error_msg = response.json()
                print(f"   ✅ PASS: Invalid elevation rejected")
                print(f"   Error: {error_msg}")
            else:
                print(f"   ❌ FAIL: Invalid elevation accepted (status {response.status_code})")
                all_passed = False

        sleep(0.3)

    if all_passed:
        print("\n" + "-"*80)
        print("✅ TEST 3 PASSED: Elevation validation working correctly")
        print("-"*80)
    else:
        print("\n" + "-"*80)
        print("❌ TEST 3 FAILED: Elevation validation issues")
        print("-"*80)

    return all_passed


def run_all_tests():
    """Run all coordinate validation tests"""
    print("\n" + "="*80)
    print("PHASE 1 TEST SUITE: 1.6 Geographic Coordinate Validation")
    print("="*80)
    print("\nTesting coordinate validation for locations:")
    print("1. Latitude must be between -90 and 90")
    print("2. Longitude must be between -180 and 180")
    print("3. Elevation must be between -500m and 9000m")

    # Create single authenticated session for all tests
    print("\nAuthenticating test user...")
    session = requests.Session()
    session = register_and_login(session)

    results = []

    # Run tests with shared session
    results.append(("Latitude Validation", test_latitude_validation(session)))
    results.append(("Longitude Validation", test_longitude_validation(session)))
    results.append(("Elevation Validation", test_elevation_validation(session)))

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
        print("✅ ALL TESTS PASSED - 1.6 Coordinate Validation Fixed")
    else:
        print("❌ SOME TESTS FAILED - Review output above")
    print("="*80 + "\n")

    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
