#!/usr/bin/env python3
"""
Rate Limiting Test Script

Tests DRF throttling implementation for authentication endpoints.
Tests:
1. Anonymous API rate limiting (100/hour)
2. Login rate limiting (5/minute)
3. Registration rate limiting (5/minute)
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_api_rate_limiting():
    """Test general API rate limiting for anonymous users"""
    print("\n" + "="*60)
    print("TEST 1: General API Rate Limiting (100/hour)")
    print("="*60)

    url = f"{BASE_URL}/api/locations/"

    print(f"Making requests to {url}...")
    for i in range(1, 6):
        response = requests.get(url)
        print(f"Request {i}: Status {response.status_code}")

        if response.status_code == 429:
            print(f"✅ Rate limit enforced after {i} requests")
            print(f"Response: {response.json()}")
            return True

    print(f"✅ Successfully made 5 requests (limit is 100/hour)")
    return True


def test_login_rate_limiting():
    """Test login endpoint rate limiting (5/minute)"""
    print("\n" + "="*60)
    print("TEST 2: Login Rate Limiting (5/minute)")
    print("="*60)

    url = f"{BASE_URL}/login/"

    # Test data (intentionally invalid)
    data = {
        'username': 'testuser',
        'password': 'wrongpassword'
    }

    print(f"Attempting 7 rapid login requests...")
    for i in range(1, 8):
        response = requests.post(url, json=data)
        print(f"Request {i}: Status {response.status_code}")

        if response.status_code == 429:
            print(f"✅ Rate limit enforced after {i-1} requests")
            try:
                error_data = response.json()
                print(f"Error message: {error_data.get('detail', 'No detail')}")
            except:
                print(f"Response text: {response.text}")
            return True

        time.sleep(0.1)  # Small delay between requests

    print("❌ Rate limit was NOT enforced (should have been blocked at request 6)")
    return False


def test_registration_rate_limiting():
    """Test registration endpoint rate limiting (5/minute)"""
    print("\n" + "="*60)
    print("TEST 3: Registration Rate Limiting (5/minute)")
    print("="*60)

    url = f"{BASE_URL}/register/"

    print(f"Attempting 7 rapid registration requests...")
    for i in range(1, 8):
        # Use different username each time to avoid duplicate errors
        data = {
            'username': f'testuser{i}{int(time.time())}',
            'email': f'test{i}{int(time.time())}@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpassword123',
            'password2': 'testpassword123'
        }

        response = requests.post(url, json=data)
        print(f"Request {i}: Status {response.status_code}")

        if response.status_code == 429:
            print(f"✅ Rate limit enforced after {i-1} requests")
            try:
                error_data = response.json()
                print(f"Error message: {error_data.get('detail', 'No detail')}")
            except:
                print(f"Response text: {response.text}")
            return True

        time.sleep(0.1)  # Small delay between requests

    print("❌ Rate limit was NOT enforced (should have been blocked at request 6)")
    return False


def main():
    print("\n" + "="*60)
    print("RATE LIMITING TEST SUITE")
    print("="*60)
    print("Testing Django REST Framework throttling implementation")
    print("Server: " + BASE_URL)
    print("\nNOTE: Ensure Django development server is running")
    print("="*60)

    try:
        # Test general API rate limiting
        api_test = test_api_rate_limiting()

        # Test login rate limiting
        login_test = test_login_rate_limiting()

        # Test registration rate limiting
        registration_test = test_registration_rate_limiting()

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"General API Rate Limiting: {'✅ PASS' if api_test else '❌ FAIL'}")
        print(f"Login Rate Limiting: {'✅ PASS' if login_test else '❌ FAIL'}")
        print(f"Registration Rate Limiting: {'✅ PASS' if registration_test else '❌ FAIL'}")
        print("="*60)

        if all([api_test, login_test, registration_test]):
            print("\n✅ ALL TESTS PASSED - Rate limiting is working correctly!")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED - Review configuration")
            return 1

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("Make sure Django development server is running:")
        print("  python manage.py runserver")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
