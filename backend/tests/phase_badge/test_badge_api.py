#!/usr/bin/env python3
"""
Badge API Endpoint Test

Tests the badge system API endpoints using curl commands.

Prerequisites:
- Server running at http://127.0.0.1:8000/
- At least one user with some activity (visits, reviews, etc.)

Run: djvenv/bin/python .claude/backend/tests/phase_badge/test_badge_api.py
"""

import os
import sys
import django
import requests
import json

# Setup Django environment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from starview_app.models import Badge, UserBadge, LocationVisit, Location


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


def test_get_user_badges():
    """Test GET /api/users/{username}/badges/ endpoint"""
    print_header("TEST 1: GET User Badges")

    # Get a user (prefer one with some activity)
    user = User.objects.filter(location_visits__isnull=False).first()
    if not user:
        user = User.objects.first()

    if not user:
        print_error("No users found in database")
        return False

    print_info(f"Testing with user: {user.username}")

    # Test API endpoint
    url = f"http://127.0.0.1:8000/api/users/{user.username}/badges/"
    print_info(f"GET {url}")

    try:
        response = requests.get(url)
        print_info(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            print_success(f"Earned badges: {len(data['earned'])}")
            for badge in data['earned'][:3]:
                print_info(f"  • {badge['name']} (earned {badge['earned_at']})")

            print_success(f"In-progress badges: {len(data['in_progress'])}")
            for badge in data['in_progress'][:3]:
                print_info(f"  • {badge['name']} ({badge['current_progress']}/{badge['criteria_value']})")

            print_success(f"Locked badges: {len(data['locked'])}")
            print_success(f"Pinned badge IDs: {data['pinned_badge_ids']}")

            print_success("✓ GET /api/users/{username}/badges/ WORKING")
            return True
        else:
            print_error(f"Request failed: {response.status_code}")
            print_error(response.text)
            return False

    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False


def test_badge_service_directly():
    """Test BadgeService methods directly"""
    print_header("TEST 2: BadgeService Direct Testing")

    from starview_app.services.badge_service import BadgeService

    # Get test user with some data
    user = User.objects.first()
    if not user:
        print_error("No users found")
        return False

    print_info(f"Testing with user: {user.username}")

    # Test check_exploration_badges
    print_info("\nTesting check_exploration_badges...")
    visit_count = LocationVisit.objects.filter(user=user).count()
    print_info(f"User has {visit_count} location visits")

    newly_awarded = BadgeService.check_exploration_badges(user)
    if newly_awarded:
        print_success(f"Newly awarded {len(newly_awarded)} exploration badges")
    else:
        print_info("No new exploration badges (may already have them)")

    # Test get_user_badge_progress
    print_info("\nTesting get_user_badge_progress...")
    progress = BadgeService.get_user_badge_progress(user)

    print_success(f"Earned: {len(progress['earned'])} badges")
    print_success(f"In-progress: {len(progress['in_progress'])} badges")
    print_success(f"Locked: {len(progress['locked'])} badges")

    total = len(progress['earned']) + len(progress['in_progress']) + len(progress['locked'])
    assert total == 20, f"Expected 20 total badges, got {total}"

    print_success("✓ BadgeService methods WORKING")
    return True


def test_badge_database():
    """Test badge database queries"""
    print_header("TEST 3: Badge Database Queries")

    # Test badge seeding
    total_badges = Badge.objects.count()
    print_info(f"Total badges: {total_badges}")
    assert total_badges == 20, f"Expected 20 badges, found {total_badges}"
    print_success("✓ 20 badges seeded")

    # Test badge categories
    categories = Badge.objects.values_list('category', flat=True).distinct()
    print_success(f"Categories: {list(categories)}")

    # Test badge with highest criteria
    highest = Badge.objects.order_by('-criteria_value').first()
    print_success(f"Highest criteria badge: {highest.name} (requires {highest.criteria_value})")

    # Test user badges
    users_with_badges = UserBadge.objects.values_list('user__username', flat=True).distinct()
    print_success(f"Users with badges: {len(list(users_with_badges))}")

    print_success("✓ Database queries WORKING")
    return True


def run_all_tests():
    """Run all API tests"""
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"BADGE API ENDPOINT TESTS")
    print(f"{'='*70}{Colors.RESET}\n")

    print_info("Prerequisites:")
    print_info("  • Django server running at http://127.0.0.1:8000/")
    print_info("  • At least one user in database")
    print_info("  • Badges seeded (20 badges)")

    results = []

    # Test database first
    results.append(("Badge Database", test_badge_database()))

    # Test service layer
    results.append(("BadgeService", test_badge_service_directly()))

    # Test API endpoint
    results.append(("GET User Badges API", test_get_user_badges()))

    # Print summary
    print_header("TEST SUMMARY")

    all_passed = all(result[1] for result in results)

    for test_name, passed in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {test_name}: {status}")

    if all_passed:
        print_success("\n✓ ALL TESTS PASSED!")
    else:
        print_error("\n✗ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == '__main__':
    run_all_tests()
