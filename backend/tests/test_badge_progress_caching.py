#!/usr/bin/env python
"""
Badge Progress Caching - Comprehensive Functional Tests

Tests the badge progress caching system end-to-end:
1. Cache hits and misses
2. Cache invalidation on all user activities
3. Cache isolation between users
4. Cache expiration (TTL)

This verifies the complete fix for Medium Issue #7.
"""

import os
import sys
import django
import time

# Setup Django (assume running from project root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.db import connection, reset_queries
from django.core.cache import cache
from starview_app.services.badge_service import BadgeService
from starview_app.models import (
    Location, Review, LocationVisit, UserBadge, Badge,
    Follow, ReviewComment, Vote, ReviewPhoto
)
from django.contrib.contenttypes.models import ContentType


def reset_query_counter():
    """Reset Django query counter for accurate measurements."""
    reset_queries()


def get_query_count():
    """Get number of queries executed since last reset."""
    return len(connection.queries)


def create_test_user(username):
    """Create a test user or get existing one."""
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='testpass123'
        )


@override_settings(DEBUG=True)
def run_all_tests():
    """Run all functional tests."""
    print("\n" + "="*80)
    print("BADGE PROGRESS CACHING - FUNCTIONAL TESTS")
    print("="*80)

    tests = [
        test_cache_hit_and_miss,
        test_invalidation_on_location_creation,
        test_invalidation_on_review_creation,
        test_invalidation_on_vote_received,
        test_invalidation_on_follower_gained,
        test_invalidation_on_comment_created,
        test_invalidation_on_visit_logged,
        test_cache_isolation_between_users,
        test_cache_expiration,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✓ PASSED\n")
        except AssertionError as e:
            failed += 1
            print(f"✗ FAILED: {e}\n")
        except Exception as e:
            failed += 1
            print(f"✗ ERROR: {e}\n")

    print("="*80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*80)

    return failed == 0


def test_cache_hit_and_miss():
    """Test 1: Cache miss on first call, cache hit on subsequent calls."""
    print("\nTest 1: Cache Hit and Miss")
    print("-" * 80)

    user = create_test_user('cache_test_1')
    cache.delete(f'badge_progress:{user.id}')

    # First call - cache miss
    reset_query_counter()
    result1 = BadgeService.get_user_badge_progress(user)
    queries1 = get_query_count()

    print(f"First call:  {queries1} queries (cache miss)")
    assert queries1 == 7, f"Expected 7 queries on cache miss, got {queries1}"

    # Second call - cache hit
    reset_query_counter()
    result2 = BadgeService.get_user_badge_progress(user)
    queries2 = get_query_count()

    print(f"Second call: {queries2} queries (cache hit)")
    assert queries2 == 0, f"Expected 0 queries on cache hit, got {queries2}"

    # Results should be identical
    assert result1 == result2, "Cached result differs from fresh calculation"
    print("Results match ✓")


def test_invalidation_on_location_creation():
    """Test 2: Cache invalidated when user creates a location."""
    print("\nTest 2: Cache Invalidation on Location Creation")
    print("-" * 80)

    user = create_test_user('cache_test_2')
    cache.delete(f'badge_progress:{user.id}')

    # Prime cache
    BadgeService.get_user_badge_progress(user)
    print("Cache primed")

    # Verify cache hit
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    assert get_query_count() == 0, "Cache should be hit before invalidation"
    print("Cache hit confirmed ✓")

    # Create location (should invalidate cache)
    location = Location.objects.create(
        name=f'Test Location {user.username}',
        latitude=40.7128,
        longitude=-74.0060,
        added_by=user
    )
    print(f"Created location: {location.name}")

    # Next call should be cache miss
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    queries = get_query_count()
    print(f"Post-creation call: {queries} queries")
    assert queries == 7, f"Cache should be invalidated after location creation, expected 7 queries, got {queries}"

    # Cleanup
    location.delete()


def test_invalidation_on_review_creation():
    """Test 3: Cache invalidated when user creates a review."""
    print("\nTest 3: Cache Invalidation on Review Creation")
    print("-" * 80)

    user = create_test_user('cache_test_3')
    location_owner = create_test_user('cache_test_3_owner')
    location = Location.objects.create(
        name='Test Location for Reviews',
        latitude=40.7128,
        longitude=-74.0060,
        added_by=location_owner
    )
    cache.delete(f'badge_progress:{user.id}')

    # Prime cache
    BadgeService.get_user_badge_progress(user)
    print("Cache primed")

    # Verify cache hit
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    assert get_query_count() == 0, "Cache should be hit before invalidation"
    print("Cache hit confirmed ✓")

    # Create review (should invalidate cache)
    review = Review.objects.create(
        user=user,
        location=location,
        rating=5,
        comment='Great spot!'
    )
    print(f"Created review for {location.name}")

    # Next call should be cache miss
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    queries = get_query_count()
    print(f"Post-creation call: {queries} queries")
    assert queries == 7, f"Cache should be invalidated after review creation, expected 7 queries, got {queries}"

    # Cleanup
    review.delete()
    location.delete()


def test_invalidation_on_vote_received():
    """Test 4: Cache invalidated when user's review receives a vote."""
    print("\nTest 4: Cache Invalidation on Vote Received")
    print("-" * 80)

    user = create_test_user('cache_test_4')
    voter = create_test_user('cache_test_4_voter')
    location_owner = create_test_user('cache_test_4_owner')

    location = Location.objects.create(
        name='Test Location for Votes',
        latitude=40.7128,
        longitude=-74.0060,
        added_by=location_owner
    )

    review = Review.objects.create(
        user=user,
        location=location,
        rating=5,
        comment='Amazing!'
    )

    cache.delete(f'badge_progress:{user.id}')

    # Prime cache
    BadgeService.get_user_badge_progress(user)
    print("Cache primed")

    # Verify cache hit
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    assert get_query_count() == 0, "Cache should be hit before invalidation"
    print("Cache hit confirmed ✓")

    # Create vote on review (should invalidate cache for review author)
    review_ct = ContentType.objects.get_for_model(Review)
    vote = Vote.objects.create(
        user=voter,
        content_type=review_ct,
        object_id=review.id,
        is_upvote=True
    )
    print(f"Vote created on review by {voter.username}")

    # Next call should be cache miss
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    queries = get_query_count()
    print(f"Post-vote call: {queries} queries")
    assert queries == 7, f"Cache should be invalidated after vote, expected 7 queries, got {queries}"

    # Cleanup
    vote.delete()
    review.delete()
    location.delete()


def test_invalidation_on_follower_gained():
    """Test 5: Cache invalidated when user gains a follower."""
    print("\nTest 5: Cache Invalidation on Follower Gained")
    print("-" * 80)

    user = create_test_user('cache_test_5')
    follower = create_test_user('cache_test_5_follower')
    cache.delete(f'badge_progress:{user.id}')

    # Prime cache
    BadgeService.get_user_badge_progress(user)
    print("Cache primed")

    # Verify cache hit
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    assert get_query_count() == 0, "Cache should be hit before invalidation"
    print("Cache hit confirmed ✓")

    # Create follow (should invalidate cache for followed user)
    follow = Follow.objects.create(
        follower=follower,
        following=user
    )
    print(f"{follower.username} followed {user.username}")

    # Next call should be cache miss
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    queries = get_query_count()
    print(f"Post-follow call: {queries} queries")
    assert queries == 7, f"Cache should be invalidated after gaining follower, expected 7 queries, got {queries}"

    # Cleanup
    follow.delete()


def test_invalidation_on_comment_created():
    """Test 6: Cache invalidated when user creates a comment."""
    print("\nTest 6: Cache Invalidation on Comment Created")
    print("-" * 80)

    user = create_test_user('cache_test_6')
    location_owner = create_test_user('cache_test_6_owner')
    reviewer = create_test_user('cache_test_6_reviewer')

    location = Location.objects.create(
        name='Test Location for Comments',
        latitude=40.7128,
        longitude=-74.0060,
        added_by=location_owner
    )

    review = Review.objects.create(
        user=reviewer,
        location=location,
        rating=4,
        comment='Nice spot'
    )

    cache.delete(f'badge_progress:{user.id}')

    # Prime cache
    BadgeService.get_user_badge_progress(user)
    print("Cache primed")

    # Verify cache hit
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    assert get_query_count() == 0, "Cache should be hit before invalidation"
    print("Cache hit confirmed ✓")

    # Create comment (should invalidate cache for commenter)
    comment = ReviewComment.objects.create(
        user=user,
        review=review,
        content='Great review!'
    )
    print(f"{user.username} commented on review")

    # Next call should be cache miss
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    queries = get_query_count()
    print(f"Post-comment call: {queries} queries")
    assert queries == 7, f"Cache should be invalidated after comment, expected 7 queries, got {queries}"

    # Cleanup
    comment.delete()
    review.delete()
    location.delete()


def test_invalidation_on_visit_logged():
    """Test 7: Cache invalidated when user logs a location visit."""
    print("\nTest 7: Cache Invalidation on Visit Logged")
    print("-" * 80)

    user = create_test_user('cache_test_7')
    location_owner = create_test_user('cache_test_7_owner')

    location = Location.objects.create(
        name='Test Location for Visits',
        latitude=40.7128,
        longitude=-74.0060,
        added_by=location_owner
    )

    cache.delete(f'badge_progress:{user.id}')

    # Prime cache
    BadgeService.get_user_badge_progress(user)
    print("Cache primed")

    # Verify cache hit
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    assert get_query_count() == 0, "Cache should be hit before invalidation"
    print("Cache hit confirmed ✓")

    # Log visit (should invalidate cache)
    visit = LocationVisit.objects.create(
        user=user,
        location=location
    )
    print(f"{user.username} marked location as visited")

    # Next call should be cache miss
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    queries = get_query_count()
    print(f"Post-visit call: {queries} queries")
    assert queries == 7, f"Cache should be invalidated after visit, expected 7 queries, got {queries}"

    # Cleanup
    visit.delete()
    location.delete()


def test_cache_isolation_between_users():
    """Test 8: Cache is isolated between different users."""
    print("\nTest 8: Cache Isolation Between Users")
    print("-" * 80)

    user1 = create_test_user('cache_test_8a')
    user2 = create_test_user('cache_test_8b')

    cache.delete(f'badge_progress:{user1.id}')
    cache.delete(f'badge_progress:{user2.id}')

    # User 1: Prime cache
    BadgeService.get_user_badge_progress(user1)
    print(f"User 1 ({user1.username}) cache primed")

    # User 1: Cache hit
    reset_query_counter()
    BadgeService.get_user_badge_progress(user1)
    queries1 = get_query_count()
    print(f"User 1 second call: {queries1} queries (cache hit)")
    assert queries1 == 0, "User 1 should have cache hit"

    # User 2: First call should be cache miss (different user)
    reset_query_counter()
    BadgeService.get_user_badge_progress(user2)
    queries2 = get_query_count()
    print(f"User 2 first call: {queries2} queries (cache miss)")
    assert queries2 == 7, "User 2 should have cache miss (different cache key)"

    # User 1: Should still have cache (not affected by user 2)
    reset_query_counter()
    BadgeService.get_user_badge_progress(user1)
    queries3 = get_query_count()
    print(f"User 1 third call: {queries3} queries (cache still valid)")
    assert queries3 == 0, "User 1 cache should not be affected by user 2"


def test_cache_expiration():
    """Test 9: Cache expires after TTL (5 minutes = 300 seconds)."""
    print("\nTest 9: Cache Expiration (TTL)")
    print("-" * 80)

    user = create_test_user('cache_test_9')
    cache.delete(f'badge_progress:{user.id}')

    # Prime cache
    BadgeService.get_user_badge_progress(user)
    print("Cache primed with 5-minute TTL")

    # Verify cache hit
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    assert get_query_count() == 0, "Cache should be hit before expiration"
    print("Cache hit confirmed (within TTL) ✓")

    # Manually expire cache by setting TTL to 1 second
    cache_key = f'badge_progress:{user.id}'
    cached_value = cache.get(cache_key)
    cache.set(cache_key, cached_value, 1)  # Set to 1 second TTL
    print("Cache TTL set to 1 second for testing")

    # Wait for expiration
    time.sleep(1.1)
    print("Waited 1.1 seconds...")

    # Next call should be cache miss (expired)
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)
    queries = get_query_count()
    print(f"Post-expiration call: {queries} queries")
    assert queries == 7, f"Cache should be expired and miss, expected 7 queries, got {queries}"


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
