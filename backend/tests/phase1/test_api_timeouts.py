#!/usr/bin/env python3
"""
Test Suite: 1.7 External API Calls Without Timeout
Phase: 1 - Critical Security
Purpose: Verify that external API calls (Mapbox) have timeouts to prevent hanging

Tests:
1. Code inspection: Verify timeout parameter exists in requests.get()
2. Mock timeout test: Verify timeout exceptions are handled gracefully
3. Functional test: Verify location creation completes even if Mapbox times out

Security Impact:
- Prevents application from hanging indefinitely if Mapbox is slow/down
- Ensures requests fail fast instead of blocking indefinitely
- Protects against potential DOS via slow external APIs

Expected Results:
- Mapbox API requests timeout after 10 seconds
- Timeout errors are caught and handled gracefully
- Location creation completes even if Mapbox times out
"""

import os
import sys
import django
from unittest.mock import patch, MagicMock
import time

# Setup Django
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

import requests
from django.contrib.auth.models import User
from starview_app.models import Location
from starview_app.services.location_service import LocationService


def test_code_inspection():
    """
    Test 1: Code Inspection

    Read the location_service.py file and verify timeout parameter exists.
    """
    print("\n" + "="*80)
    print("TEST 1: Code Inspection - Timeout Parameter")
    print("="*80)

    service_file = 'stars_app/services/location_service.py'

    with open(service_file, 'r') as f:
        content = f.read()

    # Check if timeout parameter exists in requests.get()
    if 'requests.get(url, timeout=' in content:
        print("\n✅ PASS: Timeout parameter found in requests.get()")

        # Extract timeout value
        import re
        match = re.search(r'requests\.get\(url,\s*timeout=(\d+)\)', content)
        if match:
            timeout_value = match.group(1)
            print(f"   Timeout value: {timeout_value} seconds")

            if timeout_value == '10':
                print("✅ PASS: Timeout correctly set to 10 seconds")
                return True
            else:
                print(f"⚠️  WARNING: Timeout is {timeout_value}s, recommended is 10s")
                return True
        else:
            print("⚠️  WARNING: Could not extract timeout value")
            return True
    else:
        print("❌ FAIL: No timeout parameter found in requests.get()")
        return False


def test_timeout_exception_handling():
    """
    Test 2: Timeout Exception Handling

    Verify that timeout exceptions are caught and handled gracefully.
    """
    print("\n" + "="*80)
    print("TEST 2: Timeout Exception Handling")
    print("="*80)

    with patch('requests.get') as mock_get:
        # Mock a timeout exception
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out after 10 seconds")

        # Call Mapbox request directly
        result = LocationService._make_mapbox_request("https://api.mapbox.com/test")

        # Verify the result is None (error handled gracefully)
        if result is None:
            print("\n✅ PASS: Timeout exception handled gracefully (returned None)")
            return True
        else:
            print(f"❌ FAIL: Expected None, got {result}")
            return False


def test_location_creation_with_timeout():
    """
    Test 3: Location Creation with API Timeout

    Verify that location creation completes even if Mapbox API times out.
    """
    print("\n" + "="*80)
    print("TEST 3: Location Creation with Mapbox Timeout")
    print("="*80)

    # Create test user
    test_user, created = User.objects.get_or_create(
        username='test_timeout_user',
        defaults={
            'email': 'test_timeout@example.com',
            'first_name': 'Test',
            'last_name': 'Timeout'
        }
    )
    if created:
        test_user.set_password('SecurePassword123!@#')
        test_user.save()

    with patch('requests.get') as mock_get:
        # Mock timeout for all Mapbox requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        # Try to create a location
        try:
            location = Location.objects.create(
                name='Timeout Resilience Test',
                latitude=37.7749,
                longitude=-122.4194,
                added_by=test_user
            )

            print("\n✅ PASS: Location created successfully despite API timeout")
            print(f"   Location ID: {location.id}")
            print(f"   Location name: {location.name}")
            print(f"   Coordinates: ({location.latitude}, {location.longitude})")

            # Clean up
            location.delete()
            return True

        except Exception as e:
            print(f"❌ FAIL: Location creation failed with timeout: {e}")
            return False


def test_timeout_prevents_hanging():
    """
    Test 4: Timeout Parameter Verification

    Verify that timeout parameter is passed to requests.get().
    Note: We can't test actual timeout behavior with mocks, but we can verify
    the parameter is correctly passed.
    """
    print("\n" + "="*80)
    print("TEST 4: Timeout Parameter Verification")
    print("="*80)

    with patch('requests.get') as mock_get:
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {'features': []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Call the Mapbox request
        LocationService._make_mapbox_request("https://api.mapbox.com/test")

        # Verify requests.get was called with timeout parameter
        if mock_get.called:
            call_args = mock_get.call_args

            # Check positional and keyword arguments
            if call_args[1].get('timeout') == 10:
                print("\n✅ PASS: requests.get() called with timeout=10")
                print(f"   Full call: requests.get('{call_args[0][0]}', timeout=10)")
                return True
            else:
                print(f"❌ FAIL: Timeout parameter incorrect: {call_args[1].get('timeout')}")
                return False
        else:
            print("❌ FAIL: requests.get() was not called")
            return False


def test_requests_exception_handling():
    """
    Test 5: General Request Exception Handling

    Verify that other request exceptions are also handled.
    """
    print("\n" + "="*80)
    print("TEST 5: General Request Exception Handling")
    print("="*80)

    test_cases = [
        (requests.exceptions.ConnectionError("Connection failed"), "ConnectionError"),
        (requests.exceptions.HTTPError("404 Not Found"), "HTTPError"),
        (requests.exceptions.RequestException("Generic error"), "RequestException"),
    ]

    all_passed = True

    for exception, name in test_cases:
        with patch('requests.get') as mock_get:
            mock_get.side_effect = exception
            result = LocationService._make_mapbox_request("https://api.mapbox.com/test")

            if result is None:
                print(f"\n✅ PASS: {name} handled gracefully")
            else:
                print(f"❌ FAIL: {name} not handled properly")
                all_passed = False

    return all_passed


def run_all_tests():
    """Run all API timeout tests"""
    print("\n" + "="*80)
    print("PHASE 1 TEST SUITE: 1.7 External API Timeout")
    print("="*80)
    print("\nTesting Mapbox API timeout implementation:")
    print("1. Code inspection: Verify timeout parameter exists")
    print("2. Timeout exception: Verify graceful error handling")
    print("3. Location creation: Verify resilience to timeouts")
    print("4. Timeout parameter: Verify timeout is passed correctly")
    print("5. Exception handling: Verify all error types handled")

    results = []

    # Run tests
    results.append(("Code Inspection", test_code_inspection()))
    results.append(("Timeout Exception Handling", test_timeout_exception_handling()))
    results.append(("Location Creation with Timeout", test_location_creation_with_timeout()))
    results.append(("Timeout Prevents Hanging", test_timeout_prevents_hanging()))
    results.append(("Request Exception Handling", test_requests_exception_handling()))

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
        print("✅ ALL TESTS PASSED - 1.7 API Timeouts Fixed")
    else:
        print("❌ SOME TESTS FAILED - Review output above")
    print("="*80 + "\n")

    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
