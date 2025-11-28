#!/usr/bin/env python3
"""
Test Suite: 1.8 Content Creation Spam Prevention
Phase: 1 - Critical Security
Purpose: Verify that content creation endpoints have rate limiting to prevent spam

Tests:
1. Location creation throttle (20/hour)
2. Review creation throttle (20/hour)
3. Comment creation throttle (20/hour)
4. Vote throttle (60/hour)
5. Report throttle (10/hour)
6. Throttle configuration check
7. Throttle classes existence check

Security Impact:
- Prevents automated spam/abuse attacks
- Protects database from content flooding
- Maintains application performance under abuse
- Prevents vote manipulation and report abuse

Expected Results:
- 21st location creation in 1 hour is throttled
- 21st review creation in 1 hour is throttled
- 21st comment creation in 1 hour is throttled
- 61st vote in 1 hour is throttled
- 11th report in 1 hour is throttled
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
    'username': 'test_spam_user',
    'email': 'test_spam@example.com',
    'first_name': 'Test',
    'last_name': 'Spam',
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


def test_location_creation_throttle(session):
    """
    Test 1: Location Creation Throttle

    Verify that location creation is limited to 20 per hour.
    """
    print("\n" + "="*80)
    print("TEST 1: Location Creation Throttle (20/hour)")
    print("="*80)
    print("\nCreating 21 locations to test throttle limit...")

    created_locations = []

    for i in range(21):
        csrf_token = get_csrf_token(session)

        location_data = {
            'name': f'Spam Test Location {i+1}',
            'latitude': 40.7128 + (i * 0.001),
            'longitude': -74.0060 + (i * 0.001)
        }

        response = session.post(
            LOCATION_API_URL,
            json=location_data,
            headers={'X-CSRFToken': csrf_token}
        )

        if response.status_code == 201:
            created_locations.append(response.json()['id'])
            print(f"   Location {i+1}/21: Created ✓")
        elif response.status_code == 429:
            print(f"\n   Location {i+1}/21: Throttled (429) ✓")
            print(f"   ✅ PASS: Throttle activated after {i} locations")
            print(f"   Throttle message: {response.json().get('detail', 'N/A')}")

            # Clean up created locations
            print(f"\n   Cleaning up {len(created_locations)} test locations...")
            for location_id in created_locations:
                csrf_token = get_csrf_token(session)
                session.delete(
                    f"{LOCATION_API_URL}{location_id}/",
                    headers={'X-CSRFToken': csrf_token}
                )

            return True
        else:
            print(f"   Location {i+1}/21: Unexpected status {response.status_code}")

        sleep(0.1)  # Small delay between requests

    # If we got here, throttle didn't activate
    print(f"\n   ❌ FAIL: Created 21 locations without throttling")

    # Clean up
    for location_id in created_locations:
        csrf_token = get_csrf_token(session)
        session.delete(
            f"{LOCATION_API_URL}{location_id}/",
            headers={'X-CSRFToken': csrf_token}
        )

    return False


def test_review_creation_throttle(session):
    """
    Test 2: Review Creation Throttle

    Verify that review creation is limited to 20 per hour.
    """
    print("\n" + "="*80)
    print("TEST 2: Review Creation Throttle (20/hour)")
    print("="*80)

    # First, create locations to review
    print("\n   Creating 21 test locations for reviews...")
    created_locations = []

    for i in range(21):
        csrf_token = get_csrf_token(session)
        location_data = {
            'name': f'Review Test Location {i+1}',
            'latitude': 37.7749 + (i * 0.001),
            'longitude': -122.4194 + (i * 0.001)
        }
        response = session.post(LOCATION_API_URL, json=location_data, headers={'X-CSRFToken': csrf_token})
        if response.status_code == 201:
            created_locations.append(response.json()['id'])
        sleep(0.05)

    print(f"   Created {len(created_locations)} locations ✓")
    print("\n   Creating 21 reviews to test throttle limit...")

    created_reviews = []

    for i, location_id in enumerate(created_locations):
        csrf_token = get_csrf_token(session)

        review_data = {
            'rating': 5,
            'comment': f'Test review {i+1}'
        }

        response = session.post(
            f"{LOCATION_API_URL}{location_id}/reviews/",
            json=review_data,
            headers={'X-CSRFToken': csrf_token}
        )

        if response.status_code == 201:
            created_reviews.append((location_id, response.json()['id']))
            print(f"   Review {i+1}/21: Created ✓")
        elif response.status_code == 429:
            print(f"\n   Review {i+1}/21: Throttled (429) ✓")
            print(f"   ✅ PASS: Throttle activated after {i} reviews")
            print(f"   Throttle message: {response.json().get('detail', 'N/A')}")

            # Clean up
            print(f"\n   Cleaning up test data...")
            for loc_id, rev_id in created_reviews:
                csrf_token = get_csrf_token(session)
                session.delete(f"{LOCATION_API_URL}{loc_id}/reviews/{rev_id}/", headers={'X-CSRFToken': csrf_token})

            for location_id in created_locations:
                csrf_token = get_csrf_token(session)
                session.delete(f"{LOCATION_API_URL}{location_id}/", headers={'X-CSRFToken': csrf_token})

            return True
        else:
            print(f"   Review {i+1}/21: Unexpected status {response.status_code}")

        sleep(0.1)

    # If we got here, throttle didn't activate
    print(f"\n   ❌ FAIL: Created 21 reviews without throttling")

    # Clean up
    for loc_id, rev_id in created_reviews:
        csrf_token = get_csrf_token(session)
        session.delete(f"{LOCATION_API_URL}{loc_id}/reviews/{rev_id}/", headers={'X-CSRFToken': csrf_token})

    for location_id in created_locations:
        csrf_token = get_csrf_token(session)
        session.delete(f"{LOCATION_API_URL}{location_id}/", headers={'X-CSRFToken': csrf_token})

    return False


def test_vote_throttle(session):
    """
    Test 3: Vote Throttle

    Verify that voting is limited to 60 per hour.
    """
    print("\n" + "="*80)
    print("TEST 3: Vote Throttle (60/hour)")
    print("="*80)

    # Create a location and review to vote on
    print("\n   Creating test location and review...")
    csrf_token = get_csrf_token(session)
    location_data = {'name': 'Vote Test Location', 'latitude': 34.0522, 'longitude': -118.2437}
    loc_response = session.post(LOCATION_API_URL, json=location_data, headers={'X-CSRFToken': csrf_token})
    location_id = loc_response.json()['id']

    csrf_token = get_csrf_token(session)
    review_data = {'rating': 5, 'comment': 'Vote test review'}
    rev_response = session.post(f"{LOCATION_API_URL}{location_id}/reviews/", json=review_data, headers={'X-CSRFToken': csrf_token})
    review_id = rev_response.json()['id']

    print("   Test data created ✓")
    print("\n   Attempting 61 votes to test throttle limit...")

    for i in range(61):
        csrf_token = get_csrf_token(session)

        vote_data = {'vote_type': 'upvote' if i % 2 == 0 else 'downvote'}

        response = session.post(
            f"{LOCATION_API_URL}{location_id}/reviews/{review_id}/vote/",
            json=vote_data,
            headers={'X-CSRFToken': csrf_token}
        )

        if response.status_code in [200, 201]:
            print(f"   Vote {i+1}/61: Registered ✓")
        elif response.status_code == 429:
            print(f"\n   Vote {i+1}/61: Throttled (429) ✓")
            print(f"   ✅ PASS: Throttle activated after {i} votes")
            print(f"   Throttle message: {response.json().get('detail', 'N/A')}")

            # Clean up
            print(f"\n   Cleaning up test data...")
            csrf_token = get_csrf_token(session)
            session.delete(f"{LOCATION_API_URL}{location_id}/reviews/{review_id}/", headers={'X-CSRFToken': csrf_token})
            csrf_token = get_csrf_token(session)
            session.delete(f"{LOCATION_API_URL}{location_id}/", headers={'X-CSRFToken': csrf_token})

            return True
        else:
            print(f"   Vote {i+1}/61: Unexpected status {response.status_code}")

        sleep(0.05)

    # If we got here, throttle didn't activate
    print(f"\n   ❌ FAIL: Made 61 votes without throttling")

    # Clean up
    csrf_token = get_csrf_token(session)
    session.delete(f"{LOCATION_API_URL}{location_id}/reviews/{review_id}/", headers={'X-CSRFToken': csrf_token})
    csrf_token = get_csrf_token(session)
    session.delete(f"{LOCATION_API_URL}{location_id}/", headers={'X-CSRFToken': csrf_token})

    return False


def test_report_throttle(session):
    """
    Test 4: Report Throttle

    Verify that reporting is limited to 10 per hour.
    """
    print("\n" + "="*80)
    print("TEST 4: Report Throttle (10/hour)")
    print("="*80)

    # Create 11 locations to report
    print("\n   Creating 11 test locations to report...")
    created_locations = []

    for i in range(11):
        csrf_token = get_csrf_token(session)
        location_data = {
            'name': f'Report Test Location {i+1}',
            'latitude': 51.5074 + (i * 0.001),
            'longitude': -0.1278 + (i * 0.001)
        }
        response = session.post(LOCATION_API_URL, json=location_data, headers={'X-CSRFToken': csrf_token})
        if response.status_code == 201:
            created_locations.append(response.json()['id'])
        sleep(0.05)

    print(f"   Created {len(created_locations)} locations ✓")
    print("\n   Submitting 11 reports to test throttle limit...")

    for i, location_id in enumerate(created_locations):
        csrf_token = get_csrf_token(session)

        report_data = {
            'report_type': 'SPAM',
            'description': f'Test report {i+1}'
        }

        response = session.post(
            f"{LOCATION_API_URL}{location_id}/report/",
            json=report_data,
            headers={'X-CSRFToken': csrf_token}
        )

        if response.status_code in [200, 201]:
            print(f"   Report {i+1}/11: Submitted ✓")
        elif response.status_code == 429:
            print(f"\n   Report {i+1}/11: Throttled (429) ✓")
            print(f"   ✅ PASS: Throttle activated after {i} reports")
            print(f"   Throttle message: {response.json().get('detail', 'N/A')}")

            # Clean up
            print(f"\n   Cleaning up {len(created_locations)} test locations...")
            for loc_id in created_locations:
                csrf_token = get_csrf_token(session)
                session.delete(f"{LOCATION_API_URL}{loc_id}/", headers={'X-CSRFToken': csrf_token})

            return True
        else:
            print(f"   Report {i+1}/11: Unexpected status {response.status_code}")

        sleep(0.1)

    # If we got here, throttle didn't activate
    print(f"\n   ❌ FAIL: Submitted 11 reports without throttling")

    # Clean up
    for loc_id in created_locations:
        csrf_token = get_csrf_token(session)
        session.delete(f"{LOCATION_API_URL}{loc_id}/", headers={'X-CSRFToken': csrf_token})

    return False


def test_throttle_configuration():
    """
    Test 5: Throttle Configuration Check

    Verify that all throttle rates are configured in settings.
    """
    print("\n" + "="*80)
    print("TEST 5: Throttle Configuration Check")
    print("="*80)

    import sys
    import os
    import django

    # Setup Django
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
    django.setup()

    from django.conf import settings

    throttle_rates = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', {})

    required_scopes = {
        'content_creation': '20/hour',
        'vote': '60/hour',
        'report': '10/hour',
    }

    all_configured = True

    for scope, expected_rate in required_scopes.items():
        actual_rate = throttle_rates.get(scope)
        if actual_rate == expected_rate:
            print(f"\n   ✅ PASS: '{scope}' = '{actual_rate}'")
        else:
            print(f"\n   ❌ FAIL: '{scope}' expected '{expected_rate}', got '{actual_rate}'")
            all_configured = False

    return all_configured


def test_throttle_classes_exist():
    """
    Test 6: Throttle Classes Existence

    Verify that all throttle classes are defined.
    """
    print("\n" + "="*80)
    print("TEST 6: Throttle Classes Existence Check")
    print("="*80)

    import sys
    import os
    import django

    # Setup Django
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
    django.setup()

    try:
        from starview_app.utils import (
            ContentCreationThrottle,
            VoteThrottle,
            ReportThrottle,
            LoginRateThrottle
        )

        throttle_classes = [
            ('ContentCreationThrottle', ContentCreationThrottle, 'content_creation'),
            ('VoteThrottle', VoteThrottle, 'vote'),
            ('ReportThrottle', ReportThrottle, 'report'),
            ('LoginRateThrottle', LoginRateThrottle, 'login'),
        ]

        all_exist = True

        for class_name, throttle_class, expected_scope in throttle_classes:
            actual_scope = getattr(throttle_class, 'scope', None)
            if actual_scope == expected_scope:
                print(f"\n   ✅ PASS: {class_name} exists with scope='{actual_scope}'")
            else:
                print(f"\n   ❌ FAIL: {class_name} scope expected '{expected_scope}', got '{actual_scope}'")
                all_exist = False

        return all_exist

    except ImportError as e:
        print(f"\n   ❌ FAIL: Could not import throttle classes: {e}")
        return False


def run_all_tests():
    """Run all content spam prevention tests"""
    print("\n" + "="*80)
    print("PHASE 1 TEST SUITE: 1.8 Content Spam Prevention")
    print("="*80)
    print("\nTesting comprehensive content creation throttles:")
    print("1. Location creation limit (20/hour)")
    print("2. Review creation limit (20/hour)")
    print("3. Vote limit (60/hour)")
    print("4. Report limit (10/hour)")
    print("5. Throttle configuration in settings")
    print("6. Throttle classes existence")

    results = []

    # Configuration tests (don't need server)
    results.append(("Throttle Configuration", test_throttle_configuration()))
    results.append(("Throttle Classes Exist", test_throttle_classes_exist()))

    # Integration tests (need server)
    print("\n" + "="*80)
    print("Integration Tests (requires server running)")
    print("="*80)
    print("\nAuthenticating test user...")
    session = requests.Session()
    session = register_and_login(session)

    results.append(("Location Creation Throttle", test_location_creation_throttle(session)))
    results.append(("Review Creation Throttle", test_review_creation_throttle(session)))
    results.append(("Vote Throttle", test_vote_throttle(session)))
    results.append(("Report Throttle", test_report_throttle(session)))

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
        print("✅ ALL TESTS PASSED - 1.8 Content Spam Prevention Fixed")
    else:
        print("❌ SOME TESTS FAILED - Review output above")
    print("="*80 + "\n")

    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
