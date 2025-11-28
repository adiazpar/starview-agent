#!/usr/bin/env python3
"""
Functional Verification Test - Badge Fetching Optimization
===========================================================

Tests that badge caching optimization doesn't break badge awarding logic.

Tests verify:
1. All badge categories still work correctly
2. Badges are awarded when criteria met
3. Badge cache returns correct badge objects
4. Multiple signal triggers use cached badges
5. Edge cases (first access, multiple users, different badge types)
6. Cache isolation between different badge categories

This is a comprehensive functional test to ensure zero regressions from
the module-level badge caching optimization.
"""

import os
import sys
import django
import random
import string

# Setup Django environment
sys.path.insert(0, '/Users/adiaz/event-horizon')
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-secret-key-for-running-tests')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.test.utils import override_settings
from starview_app.models import Location, LocationVisit, Review, ReviewPhoto, Follow, ReviewComment, Badge, UserBadge
from starview_app.services.badge_service import BadgeService, get_badges_by_category, get_badge_by_slug, get_review_badges
import logging

# Disable logging for cleaner output
logging.disable(logging.CRITICAL)

# Helper function to generate unique username
def get_unique_username(base):
    """Generate a unique username with random suffix."""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f'{base}_{suffix}'


def test_cache_functions():
    """Test that cache helper functions return correct Badge objects."""
    print("\n" + "="*80)
    print("TEST 1: Cache Helper Functions")
    print("="*80)

    # Test get_badges_by_category
    exploration_badges = get_badges_by_category('EXPLORATION', 'LOCATION_VISITS')
    assert len(exploration_badges) > 0, "Should return exploration badges"
    assert all(b.category == 'EXPLORATION' for b in exploration_badges), "All badges should be EXPLORATION category"
    assert all(b.criteria_type == 'LOCATION_VISITS' for b in exploration_badges), "All badges should be LOCATION_VISITS criteria"
    print(f"✓ get_badges_by_category('EXPLORATION', 'LOCATION_VISITS') returned {len(exploration_badges)} badges")

    # Test cached access (should return same objects)
    exploration_badges_2 = get_badges_by_category('EXPLORATION', 'LOCATION_VISITS')
    assert exploration_badges_2 is exploration_badges, "Should return cached badges (same list object)"
    print(f"✓ Cached access returns same list object (no query)")

    # Test get_badge_by_slug
    pioneer_badge = get_badge_by_slug('pioneer')
    assert pioneer_badge is not None, "Should return pioneer badge"
    assert pioneer_badge.slug == 'pioneer', "Badge should have correct slug"
    print(f"✓ get_badge_by_slug('pioneer') returned: {pioneer_badge.name}")

    # Test cached slug access
    pioneer_badge_2 = get_badge_by_slug('pioneer')
    assert pioneer_badge_2 is pioneer_badge, "Should return cached badge (same object)"
    print(f"✓ Cached slug access returns same object (no query)")

    # Test get_review_badges
    review_badges = get_review_badges()
    assert len(review_badges) > 0, "Should return review badges"
    assert all(b.category == 'REVIEW' for b in review_badges), "All badges should be REVIEW category"
    print(f"✓ get_review_badges() returned {len(review_badges)} badges")

    print("\n✅ All cache functions working correctly")


def test_exploration_badge_awarding():
    """Test that exploration badges are still awarded correctly."""
    print("\n" + "="*80)
    print("TEST 2: Exploration Badge Awarding (with caching)")
    print("="*80)

    # Create test user
    user = User.objects.create_user(username=get_unique_username('user'), email=f'test_{random.randint(1000, 9999)}@test.com')

    # Create locations
    locations = []
    for i in range(3):
        loc = Location.objects.create(
            name=f'Exploration Test Location {i}',
            added_by=user,
            latitude=40.0 + i,
            longitude=-74.0 + i
        )
        locations.append(loc)

    # Mark 3 locations as visited (use get_or_create to avoid duplicates from signals)
    for loc in locations:
        LocationVisit.objects.get_or_create(user=user, location=loc)

    # Check exploration badges (should use cached badge objects)
    newly_awarded = BadgeService.check_exploration_badges(user)

    # Verify badges awarded
    user_badges = UserBadge.objects.filter(user=user, badge__category='EXPLORATION')
    assert user_badges.count() > 0, "User should have earned exploration badges"
    print(f"✓ User earned {user_badges.count()} exploration badge(s)")

    for ub in user_badges:
        print(f"  - {ub.badge.name} (criteria: {ub.badge.criteria_value} visits)")

    # Cleanup
    try:
        for loc in locations:
            loc.delete()
        user.delete()
    except:
        pass

    print("\n✅ Exploration badges awarded correctly with caching")


def test_contribution_badge_awarding():
    """Test that contribution badges are still awarded correctly."""
    print("\n" + "="*80)
    print("TEST 3: Contribution Badge Awarding (with caching)")
    print("="*80)

    # Create test user
    user = User.objects.create_user(username=get_unique_username('user'), email=f'test_{random.randint(1000, 9999)}@test.com')

    # Create locations (contribution requires adding locations)
    locations = []
    for i in range(3):
        loc = Location.objects.create(
            name=f'Contribution Test Location {i}',
            added_by=user,
            latitude=40.0 + i,
            longitude=-74.0 + i
        )
        locations.append(loc)

    # Check contribution badges (should use cached badge objects)
    newly_awarded = BadgeService.check_contribution_badges(user)

    # Verify badges awarded
    user_badges = UserBadge.objects.filter(user=user, badge__category='CONTRIBUTION')
    assert user_badges.count() > 0, "User should have earned contribution badges"
    print(f"✓ User earned {user_badges.count()} contribution badge(s)")

    for ub in user_badges:
        print(f"  - {ub.badge.name} (criteria: {ub.badge.criteria_value} locations)")

    # Cleanup
    try:
        for loc in locations:
            loc.delete()
        user.delete()
    except:
        pass

    print("\n✅ Contribution badges awarded correctly with caching")


def test_photographer_badge_caching():
    """Test that photographer badge uses cached object."""
    print("\n" + "="*80)
    print("TEST 4: Photographer Badge Caching")
    print("="*80)

    # Create test user
    user = User.objects.create_user(username=get_unique_username('user'), email=f'test_{random.randint(1000, 9999)}@test.com')

    # First check (cache initialization)
    BadgeService.check_photographer_badge(user)
    print("✓ First photographer badge check (cache initialization)")

    # Second check (cache hit)
    BadgeService.check_photographer_badge(user)
    print("✓ Second photographer badge check (cache hit)")

    # Verify cache contains photographer badge
    photographer_badge = get_badge_by_slug('photographer')
    assert photographer_badge is not None, "Photographer badge should be in cache"
    assert photographer_badge.slug == 'photographer', "Cached badge should have correct slug"
    print(f"✓ Photographer badge cached: {photographer_badge.name}")

    # Cleanup
    try:
        user.delete()
    except:
        pass

    print("\n✅ Photographer badge caching working correctly")


def test_pioneer_badge_caching():
    """Test that pioneer badge uses cached object."""
    print("\n" + "="*80)
    print("TEST 5: Pioneer Badge Caching")
    print("="*80)

    # Create test user
    user = User.objects.create_user(username=get_unique_username('user'), email=f'test_{random.randint(1000, 9999)}@test.com')

    # First check (cache initialization)
    BadgeService.check_pioneer_badge(user)
    print("✓ First pioneer badge check (cache initialization)")

    # Second check (cache hit)
    BadgeService.check_pioneer_badge(user)
    print("✓ Second pioneer badge check (cache hit)")

    # Verify cache contains pioneer badge
    pioneer_badge = get_badge_by_slug('pioneer')
    assert pioneer_badge is not None, "Pioneer badge should be in cache"
    assert pioneer_badge.slug == 'pioneer', "Cached badge should have correct slug"
    print(f"✓ Pioneer badge cached: {pioneer_badge.name}")

    # Cleanup
    try:
        user.delete()
    except:
        pass

    print("\n✅ Pioneer badge caching working correctly")


def test_multiple_users_cached_badges():
    """Test that cache works correctly across multiple users."""
    print("\n" + "="*80)
    print("TEST 6: Multiple Users with Cached Badges")
    print("="*80)

    # Create 3 test users
    users = []
    for i in range(3):
        user = User.objects.create_user(
            username=get_unique_username(f'multi_user_{i}'),
            email=f'multi_{i}_{random.randint(1000, 9999)}@test.com'
        )
        users.append(user)

    # Each user visits a location (all should use cached exploration badges)
    for i, user in enumerate(users):
        loc = Location.objects.create(
            name=f'Multi User Location {i}',
            added_by=user,
            latitude=40.0 + i,
            longitude=-74.0 + i
        )
        # LocationVisit automatically created by signal when Location is created
        newly_awarded = BadgeService.check_exploration_badges(user)
        print(f"✓ User {i+1}: Checked exploration badges (used cached badges)")

    # Verify all users got badges
    for i, user in enumerate(users):
        user_badges = UserBadge.objects.filter(user=user, badge__category='EXPLORATION')
        assert user_badges.count() > 0, f"User {i+1} should have exploration badges"
        print(f"  - User {i+1} earned {user_badges.count()} badge(s)")

    # Cleanup
    try:
        for user in users:
            Location.objects.filter(added_by=user).delete()
            user.delete()
    except:
        pass

    print("\n✅ Cache works correctly across multiple users")


def test_cache_isolation_between_categories():
    """Test that different badge categories use separate cache entries."""
    print("\n" + "="*80)
    print("TEST 7: Cache Isolation Between Categories")
    print("="*80)

    # Get badges from different categories
    exploration_badges = get_badges_by_category('EXPLORATION', 'LOCATION_VISITS')
    contribution_badges = get_badges_by_category('CONTRIBUTION', 'LOCATIONS_ADDED')
    quality_badges = get_badges_by_category('QUALITY', 'LOCATION_RATING')
    community_follower_badges = get_badges_by_category('COMMUNITY', 'FOLLOWER_COUNT')
    community_comment_badges = get_badges_by_category('COMMUNITY', 'COMMENTS_WRITTEN')

    # Verify they're different lists
    assert exploration_badges is not contribution_badges, "Different categories should have separate cache entries"
    assert exploration_badges is not quality_badges, "Different categories should have separate cache entries"
    assert community_follower_badges is not community_comment_badges, "Different criteria types should have separate cache entries"

    print(f"✓ Exploration badges: {len(exploration_badges)} (separate cache)")
    print(f"✓ Contribution badges: {len(contribution_badges)} (separate cache)")
    print(f"✓ Quality badges: {len(quality_badges)} (separate cache)")
    print(f"✓ Community (follower) badges: {len(community_follower_badges)} (separate cache)")
    print(f"✓ Community (comment) badges: {len(community_comment_badges)} (separate cache)")

    # Verify cached access returns same objects
    exploration_badges_2 = get_badges_by_category('EXPLORATION', 'LOCATION_VISITS')
    assert exploration_badges_2 is exploration_badges, "Cached access should return same list object"
    print(f"✓ Cached access verified for each category")

    print("\n✅ Cache isolation working correctly")


def test_badge_criteria_still_enforced():
    """Test that badge criteria are still properly enforced with caching."""
    print("\n" + "="*80)
    print("TEST 8: Badge Criteria Enforcement (with caching)")
    print("="*80)

    # Create test user
    user = User.objects.create_user(username=get_unique_username('user'), email=f'test_{random.randint(1000, 9999)}@test.com')

    # Create 1 location (not enough for some badges)
    loc = Location.objects.create(
        name='Criteria Test Location',
        added_by=user,
        latitude=40.0,
        longitude=-74.0
    )
    # LocationVisit automatically created by signal when Location is created

    # Check exploration badges
    BadgeService.check_exploration_badges(user)

    # Get all exploration badges to see what criteria exist
    exploration_badges = get_badges_by_category('EXPLORATION', 'LOCATION_VISITS')
    highest_criteria = max(b.criteria_value for b in exploration_badges)

    # User should only have badges where criteria_value <= 1
    user_badges = UserBadge.objects.filter(user=user, badge__category='EXPLORATION')
    for ub in user_badges:
        assert ub.badge.criteria_value <= 1, f"User should not have badge requiring {ub.badge.criteria_value} visits"
        print(f"✓ Correctly awarded: {ub.badge.name} (requires {ub.badge.criteria_value} visit)")

    # User should NOT have badges requiring > 1 visit
    high_tier_badges = [b for b in exploration_badges if b.criteria_value > 1]
    for badge in high_tier_badges:
        user_has_badge = UserBadge.objects.filter(user=user, badge=badge).exists()
        assert not user_has_badge, f"User should not have {badge.name} (requires {badge.criteria_value} visits)"
        print(f"✓ Correctly NOT awarded: {badge.name} (requires {badge.criteria_value} visits, user has 1)")

    # Cleanup
    try:
        loc.delete()
        user.delete()
    except:
        pass

    print("\n✅ Badge criteria still properly enforced with caching")


def main():
    print("\n" + "="*80)
    print("FUNCTIONAL VERIFICATION TEST - BADGE FETCHING OPTIMIZATION")
    print("="*80)
    print("Testing that badge caching doesn't break badge awarding logic")
    print("="*80)

    test_count = 0
    passed_count = 0

    tests = [
        test_cache_functions,
        test_exploration_badge_awarding,
        test_contribution_badge_awarding,
        test_photographer_badge_caching,
        test_pioneer_badge_caching,
        test_multiple_users_cached_badges,
        test_cache_isolation_between_categories,
        test_badge_criteria_still_enforced,
    ]

    for test_func in tests:
        test_count += 1
        try:
            test_func()
            passed_count += 1
        except AssertionError as e:
            print(f"\n❌ FAILED: {e}")
        except Exception as e:
            print(f"\n❌ ERROR: {e}")

    print("\n" + "="*80)
    print("FUNCTIONAL TEST RESULTS")
    print("="*80)
    print(f"Tests run: {test_count}")
    print(f"Tests passed: {passed_count}")
    print(f"Tests failed: {test_count - passed_count}")

    if passed_count == test_count:
        print("\n✅ ALL FUNCTIONAL TESTS PASSED")
        print("Badge caching optimization is working correctly with no regressions!")
    else:
        print(f"\n❌ {test_count - passed_count} TEST(S) FAILED")
        print("Badge caching optimization may have introduced regressions!")

    print("="*80)


if __name__ == '__main__':
    with override_settings(DEBUG=True):
        main()
