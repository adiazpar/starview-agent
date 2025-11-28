#!/usr/bin/env python3
"""
Test Suite: 1.5 Input Sanitization (XSS Prevention)
Phase: 1 - Critical Security
Purpose: Verify that user-generated content is sanitized to prevent XSS attacks

Tests:
1. Review comment XSS sanitization
2. ReviewComment content XSS sanitization
3. Location name XSS sanitization
4. Allowed HTML tags work properly (safe formatting)
5. Malicious tags are stripped

Security Impact:
- Prevents stored XSS where malicious scripts are saved and executed in victims' browsers
- Protects all users from JavaScript injection attacks
- Allows safe HTML formatting while blocking dangerous content

Expected Results:
- <script> tags completely stripped
- Event handlers (onclick, onerror) removed
- Safe formatting tags (b, i, strong, em) preserved
- Location names have all HTML stripped (plain text only)
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
    'username': 'test_xss_user',
    'email': 'test_xss@example.com',
    'first_name': 'Test',
    'last_name': 'XSS',
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

def create_test_location(session, name='Test Location for XSS', lat=40.7128, lng=-74.0060):
    """Create a test location for XSS testing"""
    csrf_token = get_csrf_token(session)

    # Create location with provided name
    location_data = {
        'name': name,
        'latitude': lat,
        'longitude': lng
    }

    response = session.post(
        LOCATION_API_URL,
        json=location_data,
        headers={'X-CSRFToken': csrf_token}
    )

    if response.status_code == 201:
        return response.json()
    else:
        # Location might already exist, try to find it
        locations = session.get(LOCATION_API_URL).json()
        for loc in locations.get('results', []):
            if loc['name'] == name or loc.get('latitude') == lat:
                return {'id': loc['id'], 'name': loc['name']}

    return None


def test_review_comment_xss_with_session(session):
    """
    Test 1: Review Comment XSS Sanitization

    Verify that review comments are sanitized to prevent XSS attacks while
    allowing safe HTML formatting.
    """
    print("\n" + "="*80)
    print("TEST 1: Review Comment XSS Sanitization")
    print("="*80)

    print("\n1.1 Creating test location...")
    location_result = create_test_location(session)

    if not location_result:
        print("❌ FAIL: Could not create test location")
        return False

    location_id = location_result['id'] if isinstance(location_result, dict) else location_result
    print(f"✅ Test location created (ID: {location_id})")

    # Test cases for review comments
    test_cases = [
        {
            'name': 'Script tag injection',
            'input': '<script>alert("XSS")</script>Great location!',
            'expected_stripped': 'Great location!',
            'malicious': True
        },
        {
            'name': 'IMG tag with onerror',
            'input': '<img src=x onerror=alert("XSS")>Nice spot',
            'expected_stripped': 'Nice spot',
            'malicious': True
        },
        {
            'name': 'Onclick event handler',
            'input': '<div onclick="alert(\'XSS\')">Click me</div>',
            'expected_contains': 'Click me',
            'malicious': True
        },
        {
            'name': 'Safe formatting (bold)',
            'input': 'This is <b>bold</b> text',
            'expected_exact': 'This is <b>bold</b> text',
            'malicious': False
        },
        {
            'name': 'Safe formatting (italic)',
            'input': 'This is <em>emphasized</em> text',
            'expected_exact': 'This is <em>emphasized</em> text',
            'malicious': False
        },
        {
            'name': 'Mixed safe and malicious',
            'input': 'This is <strong>important</strong><script>alert("XSS")</script>',
            'expected_exact': 'This is <strong>important</strong>',
            'malicious': True
        }
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        print(f"\n1.{i + 1} Testing: {test['name']}")
        print(f"   Input: {test['input'][:60]}...")

        csrf_token = get_csrf_token(session)

        # Create review with XSS attempt
        review_data = {
            'rating': 5,
            'comment': test['input']
        }

        response = session.post(
            f"{LOCATION_API_URL}{location_id}/reviews/",
            json=review_data,
            headers={'X-CSRFToken': csrf_token}
        )

        if response.status_code == 201:
            review_id = response.json()['id']
            stored_comment = response.json()['comment']

            print(f"   Stored: {stored_comment[:60]}...")

            # Verify sanitization
            if 'expected_exact' in test:
                if stored_comment == test['expected_exact']:
                    print(f"   ✅ PASS: Content matches expected output")
                else:
                    print(f"   ❌ FAIL: Expected '{test['expected_exact']}'")
                    print(f"            Got '{stored_comment}'")
                    all_passed = False
            elif 'expected_stripped' in test:
                if stored_comment == test['expected_stripped']:
                    print(f"   ✅ PASS: Malicious content stripped")
                else:
                    print(f"   ❌ FAIL: Expected '{test['expected_stripped']}'")
                    print(f"            Got '{stored_comment}'")
                    all_passed = False
            elif 'expected_contains' in test:
                if test['expected_contains'] in stored_comment and '<script>' not in stored_comment.lower():
                    print(f"   ✅ PASS: Safe content preserved, malicious content removed")
                else:
                    print(f"   ❌ FAIL: Sanitization failed")
                    all_passed = False

            # Verify no script tags made it through
            if test['malicious']:
                dangerous_patterns = ['<script', 'onerror=', 'onclick=', 'javascript:']
                found_dangerous = any(pattern in stored_comment.lower() for pattern in dangerous_patterns)

                if found_dangerous:
                    print(f"   ❌ FAIL: Dangerous content not removed: {stored_comment}")
                    all_passed = False

            # Delete review for next test
            csrf_token = get_csrf_token(session)
            session.delete(
                f"{LOCATION_API_URL}{location_id}/reviews/{review_id}/",
                headers={'X-CSRFToken': csrf_token}
            )

        elif response.status_code in [400, 401]:
            # Either already reviewed or auth issue - try to get and update existing review
            print(f"   ℹ️  Response {response.status_code}, checking for existing review...")

            # Get all reviews for this location
            reviews_response = session.get(f"{LOCATION_API_URL}{location_id}/reviews/")

            if reviews_response.status_code == 200:
                reviews = reviews_response.json()
                if reviews and len(reviews) > 0:
                    # Find our user's review
                    user_review = reviews[0]  # Assuming first review is ours
                    review_id = user_review['id']

                    print(f"   ℹ️  Updating existing review (ID: {review_id})")
                    csrf_token = get_csrf_token(session)

                    update_response = session.patch(
                        f"{LOCATION_API_URL}{location_id}/reviews/{review_id}/",
                        json=review_data,
                        headers={'X-CSRFToken': csrf_token}
                    )

                    if update_response.status_code == 200:
                        stored_comment = update_response.json()['comment']
                        print(f"   Stored: {stored_comment[:60]}...")

                        # Same verification as above
                        if 'expected_exact' in test:
                            if stored_comment == test['expected_exact']:
                                print(f"   ✅ PASS: Content matches expected output")
                            else:
                                print(f"   ❌ FAIL: Expected '{test['expected_exact']}'")
                                all_passed = False
                        elif test['malicious']:
                            dangerous_patterns = ['<script', 'onerror=', 'onclick=']
                            if any(p in stored_comment.lower() for p in dangerous_patterns):
                                print(f"   ❌ FAIL: Dangerous content found")
                                all_passed = False
                    else:
                        print(f"   ❌ FAIL: Could not update review: {update_response.status_code}")
                        all_passed = False
                else:
                    print(f"   ❌ FAIL: No existing reviews found, auth issue?")
                    print(f"   Response: {response.json()}")
                    all_passed = False
            else:
                print(f"   ❌ FAIL: Could not fetch reviews: {reviews_response.status_code}")
                all_passed = False

        else:
            print(f"   ❌ FAIL: Unexpected response: {response.status_code}")
            print(f"   Response: {response.json()}")
            all_passed = False

        sleep(0.5)  # Small delay between requests

    if all_passed:
        print("\n" + "-"*80)
        print("✅ TEST 1 PASSED: Review comments properly sanitized")
        print("-"*80)
    else:
        print("\n" + "-"*80)
        print("❌ TEST 1 FAILED: Review sanitization issues detected")
        print("-"*80)

    return all_passed


def test_location_name_xss(session):
    """
    Test 2: Location Name XSS Sanitization

    Verify that location names have ALL HTML stripped (plain text only).
    Uses the same authenticated session from Test 1.
    """
    print("\n" + "="*80)
    print("TEST 2: Location Name XSS Sanitization")
    print("="*80)

    test_cases = [
        {
            'name': 'Script tag in location name',
            'input': '<script>alert("XSS")</script>Observatory',
            'expected': 'Observatory'
        },
        {
            'name': 'Bold tags (should be stripped)',
            'input': '<b>Dark Sky</b> Park',
            'expected': 'Dark Sky Park'
        },
        {
            'name': 'Event handler',
            'input': '<div onclick="alert()">Mountain Peak</div>',
            'expected': 'Mountain Peak'
        }
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        print(f"\n2.{i} Testing: {test['name']}")
        print(f"   Input: {test['input']}")

        # Use the helper function to create location
        location_result = create_test_location(
            session,
            name=test['input'],
            lat=40.7128 + i * 0.01,
            lng=-74.0060 + i * 0.01
        )

        if location_result:
            stored_name = location_result['name']
            location_id = location_result['id']
            print(f"   Stored: {stored_name}")

            if stored_name == test['expected']:
                print(f"   ✅ PASS: All HTML stripped correctly")
            else:
                print(f"   ❌ FAIL: Expected '{test['expected']}', got '{stored_name}'")
                all_passed = False

            # Verify no HTML tags remain
            if '<' in stored_name or '>' in stored_name:
                print(f"   ❌ FAIL: HTML tags found in location name")
                all_passed = False

            # Clean up
            csrf_token = get_csrf_token(session)
            session.delete(
                f"{LOCATION_API_URL}{location_id}/",
                headers={'X-CSRFToken': csrf_token}
            )

        else:
            print(f"   ❌ FAIL: Could not create location")
            all_passed = False

        sleep(0.5)

    if all_passed:
        print("\n" + "-"*80)
        print("✅ TEST 2 PASSED: Location names properly sanitized")
        print("-"*80)
    else:
        print("\n" + "-"*80)
        print("❌ TEST 2 FAILED: Location name sanitization issues")
        print("-"*80)

    return all_passed


def run_all_tests():
    """Run all XSS sanitization tests"""
    print("\n" + "="*80)
    print("PHASE 1 TEST SUITE: 1.5 Input Sanitization (XSS Prevention)")
    print("="*80)
    print("\nTesting XSS prevention across user-generated content:")
    print("1. Review comments (allows safe formatting)")
    print("2. Location names (plain text only)")

    # Create single authenticated session for all tests
    print("\nAuthenticating test user...")
    session = requests.Session()
    session = register_and_login(session)

    results = []

    # Run tests with shared session
    results.append(("Review Comment XSS", test_review_comment_xss_with_session(session)))
    results.append(("Location Name XSS", test_location_name_xss(session)))

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
        print("✅ ALL TESTS PASSED - 1.5 Input Sanitization (XSS) Fixed")
    else:
        print("❌ SOME TESTS FAILED - Review output above")
    print("="*80 + "\n")

    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
