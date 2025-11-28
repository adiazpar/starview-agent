"""
Test script for the /api/auth/status/ endpoint.

This script verifies:
1. Unauthenticated users receive authenticated=false
2. Authenticated users receive authenticated=true with user data
3. Response includes all expected user fields
"""

import requests
import json
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = "http://127.0.0.1:8000"
AUTH_STATUS_URL = f"{BASE_URL}/api/auth/status/"

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def print_test(test_name, passed, message=""):
    """Print test result with color."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {test_name}")
    if message:
        print(f"  {message}")


def test_unauthenticated_status():
    """Test that unauthenticated requests return authenticated=false."""
    print(f"\n{YELLOW}Test 1: Unauthenticated User{RESET}")

    try:
        response = requests.get(AUTH_STATUS_URL)
        data = response.json()

        # Check status code
        print_test(
            "Status code is 200",
            response.status_code == 200,
            f"Got: {response.status_code}"
        )

        # Check authenticated field
        print_test(
            "authenticated is false",
            data.get('authenticated') == False,
            f"Got: {data.get('authenticated')}"
        )

        # Check user field is None
        print_test(
            "user is null",
            data.get('user') is None,
            f"Got: {data.get('user')}"
        )

        print(f"\n{GREEN}Response:{RESET}")
        print(json.dumps(data, indent=2))

        return True

    except Exception as e:
        print_test("Request succeeded", False, str(e))
        return False


def test_authenticated_status(username, password):
    """Test that authenticated requests return authenticated=true with user data."""
    print(f"\n{YELLOW}Test 2: Authenticated User{RESET}")

    try:
        # Create session to maintain cookies
        session = requests.Session()

        # First, get CSRF token
        session.get(BASE_URL)
        csrftoken = session.cookies.get('csrftoken', '')

        # Login
        login_url = f"{BASE_URL}/api/auth/login/"
        login_data = {
            'username': username,
            'password': password
        }
        login_response = session.post(
            login_url,
            json=login_data,
            headers={'X-CSRFToken': csrftoken}
        )

        if login_response.status_code != 200:
            print_test(
                "Login succeeded",
                False,
                f"Login failed with status {login_response.status_code}: {login_response.text}"
            )
            return False

        print_test("Login succeeded", True)

        # Now test auth status
        response = session.get(AUTH_STATUS_URL)
        data = response.json()

        # Check status code
        print_test(
            "Status code is 200",
            response.status_code == 200,
            f"Got: {response.status_code}"
        )

        # Check authenticated field
        print_test(
            "authenticated is true",
            data.get('authenticated') == True,
            f"Got: {data.get('authenticated')}"
        )

        # Check user object exists
        user = data.get('user')
        print_test(
            "user object exists",
            user is not None,
            f"Got: {type(user)}"
        )

        if user:
            # Check required fields
            required_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile_picture_url']
            for field in required_fields:
                print_test(
                    f"user.{field} exists",
                    field in user,
                    f"Value: {user.get(field)}"
                )

        print(f"\n{GREEN}Response:{RESET}")
        print(json.dumps(data, indent=2))

        return True

    except Exception as e:
        print_test("Request succeeded", False, str(e))
        return False


def main():
    """Run all tests."""
    print(f"{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Testing /api/auth/status/ Endpoint{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")

    # Test 1: Unauthenticated
    test1_passed = test_unauthenticated_status()

    # Test 2: Authenticated (requires credentials)
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print("For Test 2, please provide credentials of an existing user:")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    if username and password:
        test2_passed = test_authenticated_status(username, password)
    else:
        print(f"{YELLOW}Skipping authenticated test (no credentials provided){RESET}")
        test2_passed = None

    # Summary
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Test Summary{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")
    print(f"Test 1 (Unauthenticated): {GREEN}PASS{RESET}" if test1_passed else f"Test 1 (Unauthenticated): {RED}FAIL{RESET}")
    if test2_passed is not None:
        print(f"Test 2 (Authenticated): {GREEN}PASS{RESET}" if test2_passed else f"Test 2 (Authenticated): {RED}FAIL{RESET}")
    else:
        print(f"Test 2 (Authenticated): {YELLOW}SKIPPED{RESET}")


if __name__ == "__main__":
    main()
