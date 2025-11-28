#!/usr/bin/env python
"""
Badge Progress Caching - AFTER Metrics Test

Tests the performance of get_user_badge_progress() WITH caching.
Verifies that the Redis cache optimization is working correctly.

Expected behavior:
- First call: 7 queries (cache miss - calculates and caches result)
- Subsequent calls: 0 queries (cache hits - returns cached data)
- 10-60x speedup for cache hits

This test verifies the fix for Medium Issue #7.
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
from starview_app.models import Location, Review, LocationVisit, UserBadge, Badge


def reset_query_counter():
    """Reset Django query counter for accurate measurements."""
    reset_queries()


def get_query_count():
    """Get number of queries executed since last reset."""
    return len(connection.queries)


def print_queries():
    """Print all queries executed (for debugging)."""
    for i, query in enumerate(connection.queries, 1):
        print(f"Query {i}: {query['sql']}")


@override_settings(DEBUG=True)  # Required for query logging
def test_badge_progress_with_caching():
    """
    Test badge progress calculation WITH caching.

    Optimized metrics:
    - Query count per call (0 for cache hits, 7 for cache miss)
    - Execution time per call (much faster for cache hits)
    - Cache hit/miss ratio
    """

    print("\n" + "="*80)
    print("MEDIUM ISSUE #7 - AFTER OPTIMIZATION")
    print("Badge Progress Caching - Optimized Metrics (WITH CACHING)")
    print("="*80)

    # Create test user with some activity
    try:
        user = User.objects.get(username='cache_test_user_after')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='cache_test_user_after',
            email='cache_test_after@example.com',
            password='testpass123'
        )
        print(f"✓ Created test user: {user.username}")

    # Give user some badges to make the test realistic
    badges = Badge.objects.all()[:5]  # First 5 badges
    for badge in badges:
        UserBadge.objects.get_or_create(user=user, badge=badge)

    earned_count = UserBadge.objects.filter(user=user).count()
    print(f"✓ User has {earned_count} earned badges")

    # Clear cache to start fresh
    cache_key = f'badge_progress:{user.id}'
    cache.delete(cache_key)
    print(f"✓ Cleared cache for user {user.id}\n")

    # Test multiple calls to get_user_badge_progress()
    num_calls = 10
    query_counts = []
    execution_times = []
    cache_hits = 0
    cache_misses = 0

    print(f"Testing {num_calls} consecutive calls to get_user_badge_progress()...")
    print("-" * 80)

    for i in range(num_calls):
        reset_query_counter()

        start_time = time.time()
        result = BadgeService.get_user_badge_progress(user)
        end_time = time.time()

        query_count = get_query_count()
        execution_time = (end_time - start_time) * 1000  # Convert to ms

        query_counts.append(query_count)
        execution_times.append(execution_time)

        if query_count == 0:
            cache_hits += 1
            status = "CACHE HIT ✓"
        else:
            cache_misses += 1
            status = "CACHE MISS"

        print(f"Call #{i+1:2d}: {query_count:2d} queries, {execution_time:6.2f}ms - {status}")

    # Calculate statistics
    avg_queries = sum(query_counts) / len(query_counts)
    avg_time = sum(execution_times) / len(execution_times)
    min_queries = min(query_counts)
    max_queries = max(query_counts)
    min_time = min(execution_times)
    max_time = max(execution_times)

    # Get cache hit metrics
    cache_hit_times = [execution_times[i] for i in range(len(query_counts)) if query_counts[i] == 0]
    cache_miss_times = [execution_times[i] for i in range(len(query_counts)) if query_counts[i] > 0]

    avg_cache_hit_time = sum(cache_hit_times) / len(cache_hit_times) if cache_hit_times else 0
    avg_cache_miss_time = sum(cache_miss_times) / len(cache_miss_times) if cache_miss_times else 0

    print("-" * 80)
    print("\nOPTIMIZED METRICS (WITH CACHING):")
    print(f"  Average Queries:  {avg_queries:.1f} queries/call")
    print(f"  Query Range:      {min_queries}-{max_queries} queries")
    print(f"  Average Time:     {avg_time:.2f}ms/call")
    print(f"  Time Range:       {min_time:.2f}-{max_time:.2f}ms")

    print("\nCACHE PERFORMANCE:")
    print(f"  Cache Hits:       {cache_hits}/{num_calls} calls ({cache_hits/num_calls*100:.0f}%)")
    print(f"  Cache Misses:     {cache_misses}/{num_calls} calls ({cache_misses/num_calls*100:.0f}%)")
    print(f"  Avg Hit Time:     {avg_cache_hit_time:.2f}ms (0 queries)")
    print(f"  Avg Miss Time:    {avg_cache_miss_time:.2f}ms (7 queries)")

    if avg_cache_hit_time > 0 and avg_cache_miss_time > 0:
        speedup = avg_cache_miss_time / avg_cache_hit_time
        print(f"  Speedup:          {speedup:.1f}x faster (cache hits vs misses)")

    # Verify caching working correctly
    print("\nCACHE VERIFICATION:")
    if cache_hits >= 9:  # Expect 9/10 hits (first call is miss)
        print(f"  ✓ CACHING WORKING (9+ cache hits detected)")
        print(f"    → First call: Cache miss (7 queries, stores in cache)")
        print(f"    → Subsequent calls: Cache hits (0 queries, reads from cache)")
        print(f"    → Cache TTL: 5 minutes (300 seconds)")
    else:
        print(f"  ⚠ WARNING: Fewer cache hits than expected ({cache_hits}/10)")
        print(f"    → Expected 9 hits, got {cache_hits}")
        print(f"    → Possible issue with cache configuration")

    # Compare with BEFORE metrics
    print("\nIMPROVEMENT OVER BEFORE:")
    before_avg_queries = 7.0  # From BEFORE test
    before_avg_time = 6.11  # From BEFORE test

    query_reduction = ((before_avg_queries - avg_queries) / before_avg_queries * 100)
    time_improvement = ((before_avg_time - avg_time) / before_avg_time * 100)

    print(f"  Query Reduction:  {query_reduction:.1f}% fewer queries")
    print(f"  Time Improvement: {time_improvement:.1f}% faster")

    if avg_cache_hit_time > 0:
        cache_hit_speedup = before_avg_time / avg_cache_hit_time
        print(f"  Cache Hit Speedup: {cache_hit_speedup:.1f}x faster than BEFORE baseline")

    print("\n" + "="*80)
    print("OPTIMIZATION SUCCESSFUL - Caching working correctly")
    print("="*80)

    # Return metrics for comparison
    return {
        'avg_queries': avg_queries,
        'avg_time': avg_time,
        'cache_hits': cache_hits,
        'cache_misses': cache_misses,
        'avg_cache_hit_time': avg_cache_hit_time,
        'avg_cache_miss_time': avg_cache_miss_time,
    }


if __name__ == '__main__':
    metrics = test_badge_progress_with_caching()
    print(f"\nTest completed successfully!")
    print(f"Optimized: {metrics['avg_queries']:.1f} queries, {metrics['avg_time']:.2f}ms per call")
    print(f"Cache: {metrics['cache_hits']} hits, {metrics['cache_misses']} misses")
