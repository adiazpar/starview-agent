#!/usr/bin/env python
"""
Badge Progress Caching - BEFORE Metrics Test

Tests the performance of get_user_badge_progress() WITHOUT caching.
This establishes a baseline for comparison with the cached implementation.

Expected behavior:
- Each call performs 7 database queries (5 stats + 1 UserBadge + 1 all_badges)
- Multiple calls for the same user perform the same queries repeatedly
- No caching = predictable but inefficient

This test verifies the problem described in Medium Issue #7.
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
def test_badge_progress_no_caching():
    """
    Test badge progress calculation WITHOUT caching.

    Baseline metrics:
    - Query count per call
    - Execution time per call
    - Consistency across multiple calls
    """

    print("\n" + "="*80)
    print("MEDIUM ISSUE #7 - BEFORE OPTIMIZATION")
    print("Badge Progress Caching - Baseline Metrics (NO CACHING)")
    print("="*80)

    # Create test user with some activity
    try:
        user = User.objects.get(username='cache_test_user')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='cache_test_user',
            email='cache_test@example.com',
            password='testpass123'
        )
        print(f"✓ Created test user: {user.username}")

    # Give user some badges to make the test realistic
    # (Users with badges are the common case)
    badges = Badge.objects.all()[:5]  # First 5 badges
    for badge in badges:
        UserBadge.objects.get_or_create(user=user, badge=badge)

    earned_count = UserBadge.objects.filter(user=user).count()
    print(f"✓ User has {earned_count} earned badges\n")

    # Test multiple calls to get_user_badge_progress()
    num_calls = 10
    query_counts = []
    execution_times = []

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

        print(f"Call #{i+1:2d}: {query_count:2d} queries, {execution_time:6.2f}ms")

    # Calculate statistics
    avg_queries = sum(query_counts) / len(query_counts)
    avg_time = sum(execution_times) / len(execution_times)
    min_queries = min(query_counts)
    max_queries = max(query_counts)
    min_time = min(execution_times)
    max_time = max(execution_times)

    print("-" * 80)
    print("\nBASELINE METRICS (WITHOUT CACHING):")
    print(f"  Average Queries:  {avg_queries:.1f} queries/call")
    print(f"  Query Range:      {min_queries}-{max_queries} queries")
    print(f"  Average Time:     {avg_time:.2f}ms/call")
    print(f"  Time Range:       {min_time:.2f}-{max_time:.2f}ms")

    # Show query breakdown for first call
    print("\nQUERY BREAKDOWN (Call #1):")
    reset_query_counter()
    BadgeService.get_user_badge_progress(user)

    for i, query in enumerate(connection.queries, 1):
        sql = query['sql']
        if 'starview_app_locationvisit' in sql:
            print(f"  {i}. COUNT LocationVisits (exploration stats)")
        elif 'starview_app_location' in sql and 'added_by' in sql:
            print(f"  {i}. COUNT Locations added (contribution stats)")
        elif 'starview_app_review' in sql:
            print(f"  {i}. COUNT Reviews (review stats)")
        elif 'starview_app_follow' in sql:
            print(f"  {i}. COUNT Followers (community stats)")
        elif 'starview_app_reviewcomment' in sql:
            print(f"  {i}. COUNT Comments (community stats)")
        elif 'starview_app_userbadge' in sql and 'SELECT' in sql:
            print(f"  {i}. SELECT UserBadge (earned badges with JOIN)")
        elif 'starview_app_badge' in sql and 'SELECT' in sql:
            print(f"  {i}. SELECT Badge (all badges)")
        else:
            print(f"  {i}. {sql[:80]}...")

    # Verify NO caching (all calls should have same query count)
    print("\nCACHE VERIFICATION:")
    if min_queries == max_queries:
        print(f"  ✓ NO CACHING DETECTED (all calls: {min_queries} queries)")
        print(f"    → Every call recalculates from scratch")
        print(f"    → No performance improvement for repeated requests")
    else:
        print(f"  ⚠ WARNING: Query count varies ({min_queries}-{max_queries})")
        print(f"    → Unexpected variation (possible Django query caching?)")

    # Expected impact of caching
    print("\nEXPECTED IMPACT OF CACHING:")
    print(f"  Current: {avg_queries:.1f} queries per call")
    print(f"  With cache hit: 0 queries per call")
    print(f"  With cache miss: {avg_queries:.1f} queries (same as now)")
    print(f"  Improvement: 100% query reduction for cache hits")

    if avg_time > 0:
        estimated_speedup = avg_time / 0.5  # Assume 0.5ms for cache hit
        print(f"  Estimated speedup: {estimated_speedup:.0f}x faster (cache hits)")

    print("\n" + "="*80)
    print("BASELINE ESTABLISHED - Ready for caching implementation")
    print("="*80)

    # Return metrics for comparison
    return {
        'avg_queries': avg_queries,
        'avg_time': avg_time,
        'query_counts': query_counts,
        'execution_times': execution_times,
    }


if __name__ == '__main__':
    metrics = test_badge_progress_no_caching()
    print(f"\nTest completed successfully!")
    print(f"Baseline: {metrics['avg_queries']:.1f} queries, {metrics['avg_time']:.2f}ms per call")
