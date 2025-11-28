#!/usr/bin/env python3
"""
Test that is_following field is included in user API response
"""

import os
import sys
import django

# Setup Django environment
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

import requests

BASE_URL = 'http://127.0.0.1:8000'

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_section(message):
    print(f"\n{Colors.CYAN}{'=' * 60}")
    print(f"{message}")
    print(f"{'=' * 60}{Colors.END}\n")


def test_is_following_in_response():
    """Test that is_following field is included in user API response"""

    session = requests.Session()

    # Step 1: Login as adiazpar
    print_section("Testing is_following in User API Response")
    print_info("Logging in as adiazpar...")

    login_response = session.post(
        f'{BASE_URL}/api/auth/login/',
        json={'username': 'adiazpar', 'password': 'A092320d@'},
        headers={'Content-Type': 'application/json'}
    )

    if login_response.status_code != 200:
        print_error("Login failed")
        return

    print_success("Logged in successfully")

    # Step 2: Get stony's profile (should include is_following)
    print_info("Fetching stony's profile...")

    profile_response = session.get(f'{BASE_URL}/api/users/stony/')

    if profile_response.status_code != 200:
        print_error(f"Failed to get profile: {profile_response.status_code}")
        return

    profile_data = profile_response.json()
    print_success("Retrieved profile successfully")

    # Step 3: Check if is_following field exists
    if 'is_following' in profile_data:
        print_success(f"✅ 'is_following' field is present: {profile_data['is_following']}")
    else:
        print_error("❌ 'is_following' field is missing from response")
        return

    # Step 4: Verify the value is correct
    is_following = profile_data['is_following']

    if is_following is False:
        print_success("Value is False (not following) - correct!")
    elif is_following is True:
        print_success("Value is True (following) - checking if correct...")

        # Verify by checking actual follow status
        from django.contrib.auth.models import User
        from starview_app.models import Follow

        adiazpar = User.objects.get(username='adiazpar')
        stony = User.objects.get(username='stony')

        actual_following = Follow.objects.filter(follower=adiazpar, following=stony).exists()

        if actual_following:
            print_success("Confirmed: adiazpar is following stony ✓")
        else:
            print_error("Database says not following, but API says following")
    elif is_following is None:
        print_error("Value is None (should be True/False for authenticated user)")

    # Step 5: Show full response
    print_info("\nFull API Response:")
    import json
    print(json.dumps(profile_data, indent=2))

    print_section("✅ Test Complete!")


if __name__ == '__main__':
    test_is_following_in_response()
