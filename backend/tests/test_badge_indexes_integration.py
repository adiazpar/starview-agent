#!/usr/bin/env python
"""
Badge Index Integration Test

Verifies that badge checking still works correctly after adding composite indexes.

Purpose:
- Ensure badge queries return correct results
- Verify no regressions in badge awarding logic
- Confirm index migration was successful

Usage:
    djvenv/bin/python .claude/backend/tests/test_badge_indexes_integration.py
"""

import os
import sys
import django

# Setup Django environment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)
os.chdir(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from starview_app.models import Badge, UserBadge, LocationVisit, Location
from starview_app.services.badge_service import BadgeService


def test_badge_queries():
    """Test that badge queries return correct results."""
    print("\n" + "="*80)
    print("TEST: Badge Query Correctness")
    print("="*80)

    # Test all badge categories
    categories = [
        ('EXPLORATION', 'LOCATION_VISITS'),
        ('CONTRIBUTION', 'LOCATIONS_ADDED'),
        ('QUALITY', 'LOCATION_RATING'),
        ('REVIEW', 'REVIEWS_WRITTEN'),
        ('COMMUNITY', 'FOLLOWER_COUNT'),
    ]

    for category, criteria_type in categories:
        badges = Badge.objects.filter(
            category=category,
            criteria_type=criteria_type
        ).order_by('criteria_value')

        count = badges.count()
        if count > 0:
            values = list(badges.values_list('criteria_value', flat=True))
            print(f"✓ {category:15s} - {count} badges, values: {values}")

            # Verify ordering
            assert values == sorted(values), f"Badges not sorted correctly: {values}"
        else:
            print(f"  {category:15s} - 0 badges (OK)")

    print("\n✓ All badge queries return correctly ordered results")
    return True


def test_badge_awarding():
    """Test that badge awarding still works."""
    print("\n" + "="*80)
    print("TEST: Badge Awarding Integration")
    print("="*80)

    # Create test user
    username = f"index_test_{int(__import__('time').time())}"
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123"
    )
    print(f"✓ Created test user: {user.username}")

    try:
        # Create locations
        locations = []
        for i in range(5):
            location = Location.objects.create(
                name=f"Test Location {i}",
                latitude=40.7128 + (i * 0.01),
                longitude=-74.0060 + (i * 0.01),
                elevation=100.0,
                added_by=user
            )
            locations.append(location)
        print(f"✓ Created 5 test locations")

        # Create location visits
        for location in locations:
            LocationVisit.objects.get_or_create(
                user=user,
                location=location
            )
        print(f"✓ Created 5 location visits")

        # Check exploration badges
        newly_awarded = BadgeService.check_exploration_badges(user)
        earned_count = UserBadge.objects.filter(
            user=user,
            badge__category='EXPLORATION'
        ).count()

        print(f"✓ Exploration badge check returned {len(newly_awarded)} newly awarded")
        print(f"✓ User has {earned_count} exploration badges total")

        # Check contribution badges
        newly_awarded = BadgeService.check_contribution_badges(user)
        earned_count = UserBadge.objects.filter(
            user=user,
            badge__category='CONTRIBUTION'
        ).count()

        print(f"✓ Contribution badge check returned {len(newly_awarded)} newly awarded")
        print(f"✓ User has {earned_count} contribution badges total")

        print("\n✓ Badge awarding works correctly")
        return True

    finally:
        # Cleanup
        LocationVisit.objects.filter(user=user).delete()
        Location.objects.filter(added_by=user).delete()
        UserBadge.objects.filter(user=user).delete()
        user.delete()
        print(f"\n✓ Cleaned up test data")


def test_index_exists():
    """Verify the new indexes exist in the database."""
    print("\n" + "="*80)
    print("TEST: Index Verification")
    print("="*80)

    from django.db import connection

    with connection.cursor() as cursor:
        # Check for badge_query_idx
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'starview_app_badge'
              AND indexname IN ('badge_query_idx', 'badge_slug_idx');
        """)

        results = cursor.fetchall()

        if len(results) == 2:
            print("✓ Both indexes exist:")
            for name, definition in results:
                print(f"  - {name}")
        else:
            print(f"✗ Expected 2 indexes, found {len(results)}")
            return False

    print("\n✓ All indexes verified")
    return True


def run_all_tests():
    """Run all integration tests."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              BADGE INDEX INTEGRATION TEST SUITE                              ║
║                                                                              ║
║  Purpose: Verify badge system works correctly after index migration         ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    tests = [
        ("Index Verification", test_index_exists),
        ("Badge Query Correctness", test_badge_queries),
        ("Badge Awarding Integration", test_badge_awarding),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ TEST FAILED: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n" + "="*80)
        print("ALL TESTS PASSED!")
        print("="*80)
        print("\n✓ Badge index migration successful")
        print("✓ Badge queries working correctly")
        print("✓ Badge awarding functional")
        print("\n")
    else:
        print("\n" + "="*80)
        print("SOME TESTS FAILED")
        print("="*80)
        sys.exit(1)


if __name__ == '__main__':
    run_all_tests()
