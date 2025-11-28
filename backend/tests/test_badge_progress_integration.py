#!/usr/bin/env python
"""
Integration Test for Badge Progress Optimization

Verifies that the get_user_badge_progress() optimization maintains
correct functionality while eliminating N+1 queries.

Tests:
1. Correct badge categorization (earned, in_progress, locked)
2. Accurate progress calculations
3. Proper earned_at timestamps
4. Edge cases (0 badges, all badges, partial progress)
"""

import os
import sys
import django

# Setup Django environment
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from starview_app.models import Badge, UserBadge, LocationVisit, Location, Review
from starview_app.services.badge_service import BadgeService


def cleanup_test_data():
    """Remove test users and their data."""
    User.objects.filter(username__startswith='integration_test_').delete()


def test_earned_badges():
    """Test that earned badges are correctly identified with timestamps."""
    print("\n[TEST 1] Earned Badges Display")
    print("-" * 60)

    # Create test user
    user = User.objects.create_user(
        username='integration_test_earned',
        email='earned@test.com',
        password='testpass123'
    )

    # Award 3 badges manually
    badges = Badge.objects.all()[:3]
    for badge in badges:
        UserBadge.objects.create(user=user, badge=badge)

    # Get badge progress
    progress = BadgeService.get_user_badge_progress(user)

    # Verify
    assert len(progress['earned']) == 3, f"Expected 3 earned badges, got {len(progress['earned'])}"

    for earned_item in progress['earned']:
        assert 'badge' in earned_item, "Missing 'badge' key"
        assert 'earned_at' in earned_item, "Missing 'earned_at' key"
        assert earned_item['earned_at'] is not None, "earned_at should not be None"

    print(f"✓ Earned badges count: {len(progress['earned'])}")
    print(f"✓ All badges have earned_at timestamps")
    print(f"✓ Badge structure correct")

    return True


def test_in_progress_badges():
    """Test that in-progress badges show correct progress calculations."""
    print("\n[TEST 2] In-Progress Badges Calculation")
    print("-" * 60)

    # Create test user with some progress
    user = User.objects.create_user(
        username='integration_test_progress',
        email='progress@test.com',
        password='testpass123'
    )

    # Create 3 location visits (not enough for First Light badge at 5 visits)
    locations = Location.objects.all()[:3]
    for location in locations:
        LocationVisit.objects.create(user=user, location=location)

    # Get badge progress
    progress = BadgeService.get_user_badge_progress(user)

    # Find exploration badges in progress
    exploration_in_progress = [
        item for item in progress['in_progress']
        if item['badge'].category == 'EXPLORATION'
    ]

    if exploration_in_progress:
        first_badge = exploration_in_progress[0]
        assert 'current_progress' in first_badge, "Missing 'current_progress' key"
        assert 'criteria_value' in first_badge, "Missing 'criteria_value' key"
        assert 'percentage' in first_badge, "Missing 'percentage' key"

        print(f"✓ Found {len(exploration_in_progress)} exploration badges in progress")
        print(f"✓ Progress: {first_badge['current_progress']}/{first_badge['criteria_value']}")
        print(f"✓ Percentage: {first_badge['percentage']}%")
    else:
        print("✓ No exploration badges in progress (user may have earned all)")

    return True


def test_locked_badges():
    """Test that locked badges (0 progress) are correctly identified."""
    print("\n[TEST 3] Locked Badges Display")
    print("-" * 60)

    # Create brand new user with no activity
    user = User.objects.create_user(
        username='integration_test_locked',
        email='locked@test.com',
        password='testpass123'
    )

    # Get badge progress
    progress = BadgeService.get_user_badge_progress(user)

    # All badges should be locked except pioneer (if user is in first 100)
    print(f"✓ Earned badges: {len(progress['earned'])}")
    print(f"✓ In-progress badges: {len(progress['in_progress'])}")
    print(f"✓ Locked badges: {len(progress['locked'])}")

    total = len(progress['earned']) + len(progress['in_progress']) + len(progress['locked'])
    total_badges = Badge.objects.count()

    assert total == total_badges, f"Expected {total_badges} total, got {total}"
    print(f"✓ Total badges accounted for: {total} (matches database)")

    return True


def test_progress_accuracy():
    """Test that progress calculations match actual user stats."""
    print("\n[TEST 4] Progress Calculation Accuracy")
    print("-" * 60)

    # Create user with specific progress
    user = User.objects.create_user(
        username='integration_test_accuracy',
        email='accuracy@test.com',
        password='testpass123'
    )

    # Create exactly 7 location visits
    locations = Location.objects.all()[:7]
    for location in locations:
        LocationVisit.objects.create(user=user, location=location)

    # Get badge progress
    progress = BadgeService.get_user_badge_progress(user)

    # Check if First Light (5 visits) is earned
    first_light = Badge.objects.filter(slug='first-light').first()
    if first_light:
        earned_badge_ids = [item['badge'].id for item in progress['earned']]

        if first_light.criteria_value <= 7:
            assert first_light.id in earned_badge_ids, "First Light should be earned with 7 visits"
            print(f"✓ First Light badge correctly marked as earned (7 visits >= {first_light.criteria_value})")
        else:
            print(f"✓ First Light requires {first_light.criteria_value} visits (user has 7)")

    # Check exploration badges in progress
    exploration_in_progress = [
        item for item in progress['in_progress']
        if item['badge'].category == 'EXPLORATION'
    ]

    for item in exploration_in_progress:
        if item['current_progress'] == 7:
            print(f"✓ Found exploration badge in progress with correct count (7 visits)")
            break

    return True


def test_badge_data_structure():
    """Test that badge progress data structure is correct."""
    print("\n[TEST 5] Data Structure Validation")
    print("-" * 60)

    user = User.objects.create_user(
        username='integration_test_structure',
        email='structure@test.com',
        password='testpass123'
    )

    # Award 1 badge
    badge = Badge.objects.first()
    UserBadge.objects.create(user=user, badge=badge)

    # Get badge progress
    progress = BadgeService.get_user_badge_progress(user)

    # Validate structure
    assert isinstance(progress, dict), "Progress should be a dict"
    assert 'earned' in progress, "Missing 'earned' key"
    assert 'in_progress' in progress, "Missing 'in_progress' key"
    assert 'locked' in progress, "Missing 'locked' key"

    assert isinstance(progress['earned'], list), "'earned' should be a list"
    assert isinstance(progress['in_progress'], list), "'in_progress' should be a list"
    assert isinstance(progress['locked'], list), "'locked' should be a list"

    print("✓ Top-level structure correct (dict with 3 keys)")
    print("✓ All values are lists")
    print("✓ All required keys present")

    return True


def main():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("BADGE PROGRESS INTEGRATION TESTS")
    print("="*80)

    # Cleanup from previous runs
    print("\n[SETUP] Cleaning up test data...")
    cleanup_test_data()

    tests = [
        ("Earned Badges Display", test_earned_badges),
        ("In-Progress Badges Calculation", test_in_progress_badges),
        ("Locked Badges Display", test_locked_badges),
        ("Progress Calculation Accuracy", test_progress_accuracy),
        ("Data Structure Validation", test_badge_data_structure),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, "PASS"))
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            results.append((test_name, f"FAIL: {e}"))
        except Exception as e:
            print(f"✗ ERROR: {e}")
            results.append((test_name, f"ERROR: {e}"))

    # Cleanup after tests
    print("\n[CLEANUP] Removing test data...")
    cleanup_test_data()

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print()

    passed = sum(1 for _, result in results if result == "PASS")
    failed = len(results) - passed

    for test_name, result in results:
        status = "✓" if result == "PASS" else "✗"
        print(f"{status} {test_name}: {result}")

    print()
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n✓ ALL TESTS PASSED - Badge progress functionality maintained!")
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        sys.exit(1)


if __name__ == '__main__':
    main()
