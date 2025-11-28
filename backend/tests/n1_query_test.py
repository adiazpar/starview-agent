#!/usr/bin/env python
"""
N+1 Query Performance Test for Badge Progress Calculation

Tests the get_user_badge_progress() method to identify and measure the N+1 query
anti-pattern where UserBadge.objects.get() is called inside a loop for each earned badge.

Expected BEFORE optimization:
- User with 0 badges: ~2 queries
- User with 5 badges: ~7 queries (2 initial + 5 UserBadge lookups)
- User with 10 badges: ~12 queries (2 initial + 10 UserBadge lookups)
- User with 15 badges: ~17 queries (2 initial + 15 UserBadge lookups)

Expected AFTER optimization:
- All scenarios: 2-3 queries (constant, regardless of badge count)
"""

import os
import sys
import django
import time
from django.db import connection, reset_queries
from django.conf import settings

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-key-for-performance-testing')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from starview_app.models import Badge, UserBadge, LocationVisit, Location
from starview_app.services.badge_service import BadgeService


def create_test_user_with_badges(username, badge_count):
    """
    Create a test user and award them a specific number of badges.

    Args:
        username (str): Username for the test user
        badge_count (int): Number of badges to award (0-15)

    Returns:
        User: The created user with awarded badges
    """
    # Create user
    user = User.objects.create_user(
        username=username,
        email=f'{username}@test.com',
        password='testpass123'
    )

    # Award badges
    if badge_count > 0:
        # Get badges to award (in order)
        badges = Badge.objects.all().order_by('id')[:badge_count]

        for badge in badges:
            UserBadge.objects.create(user=user, badge=badge)

    return user


def measure_query_count_and_time(user, iterations=10):
    """
    Measure average query count and execution time for get_user_badge_progress().

    Args:
        user (User): User to test
        iterations (int): Number of times to run the test

    Returns:
        dict: {
            'avg_queries': float,
            'avg_time_ms': float,
            'sample_queries': list,
            'n1_pattern_detected': bool
        }
    """
    query_counts = []
    execution_times = []
    sample_queries = None

    for i in range(iterations):
        # Reset query log
        reset_queries()

        # Enable query logging
        settings.DEBUG = True

        # Measure execution time
        start_time = time.time()
        result = BadgeService.get_user_badge_progress(user)
        end_time = time.time()

        execution_time_ms = (end_time - start_time) * 1000
        execution_times.append(execution_time_ms)

        # Count queries
        query_count = len(connection.queries)
        query_counts.append(query_count)

        # Save first iteration's queries for analysis
        if i == 0:
            sample_queries = [q['sql'] for q in connection.queries]

    # Detect N+1 pattern
    # N+1 pattern is present if we see repeated similar queries
    n1_pattern_detected = False
    if sample_queries:
        # Look for repeated UserBadge.objects.get() queries
        user_badge_get_queries = [q for q in sample_queries if 'SELECT' in q and 'starview_app_userbadge' in q and 'WHERE' in q]
        if len(user_badge_get_queries) > 1:
            # Multiple UserBadge queries indicate N+1 problem
            n1_pattern_detected = True

    return {
        'avg_queries': sum(query_counts) / len(query_counts),
        'avg_time_ms': sum(execution_times) / len(execution_times),
        'sample_queries': sample_queries,
        'n1_pattern_detected': n1_pattern_detected
    }


def cleanup_test_users():
    """Delete all test users created by this script."""
    User.objects.filter(username__startswith='n1_test_user_').delete()


def main():
    """
    Run N+1 query performance test with users having varying badge counts.
    """
    print("\n" + "="*80)
    print("N+1 QUERY PERFORMANCE TEST - Badge Progress Calculation")
    print("="*80)

    # Cleanup from previous runs
    print("\n[1] Cleaning up test data from previous runs...")
    cleanup_test_users()

    # Test scenarios
    scenarios = [
        {'username': 'n1_test_user_0', 'badge_count': 0, 'label': 'User with 0 badges'},
        {'username': 'n1_test_user_5', 'badge_count': 5, 'label': 'User with 5 badges'},
        {'username': 'n1_test_user_10', 'badge_count': 10, 'label': 'User with 10 badges'},
        {'username': 'n1_test_user_15', 'badge_count': 15, 'label': 'User with 15 badges'},
    ]

    results = {}

    print("\n[2] Creating test users and measuring performance...\n")

    for scenario in scenarios:
        print(f"Testing: {scenario['label']}")

        # Create test user
        user = create_test_user_with_badges(scenario['username'], scenario['badge_count'])
        print(f"  - Created user: {user.username}")
        print(f"  - Earned badges: {scenario['badge_count']}")

        # Measure performance
        metrics = measure_query_count_and_time(user, iterations=10)
        results[scenario['label']] = metrics

        print(f"  - Average queries: {metrics['avg_queries']:.1f}")
        print(f"  - Average time: {metrics['avg_time_ms']:.2f}ms")
        print(f"  - N+1 pattern detected: {metrics['n1_pattern_detected']}")
        print()

    # Display summary
    print("="*80)
    print("PERFORMANCE SUMMARY (BEFORE OPTIMIZATION)")
    print("="*80)
    print()

    print(f"{'Scenario':<30} {'Avg Queries':<15} {'Avg Time (ms)':<15} {'N+1 Pattern'}")
    print("-"*80)

    for scenario in scenarios:
        label = scenario['label']
        metrics = results[label]
        pattern_str = "YES" if metrics['n1_pattern_detected'] else "NO"
        print(f"{label:<30} {metrics['avg_queries']:<15.1f} {metrics['avg_time_ms']:<15.2f} {pattern_str}")

    # Detailed query analysis for user with 10 badges
    print("\n" + "="*80)
    print("DETAILED QUERY ANALYSIS (User with 10 badges)")
    print("="*80)
    print()

    sample_metrics = results['User with 10 badges']
    print(f"Total queries: {len(sample_metrics['sample_queries'])}")
    print()

    print("Query breakdown:")
    for i, query in enumerate(sample_metrics['sample_queries'], 1):
        # Truncate long queries
        query_display = query[:150] + "..." if len(query) > 150 else query
        print(f"{i}. {query_display}")

    # N+1 pattern confirmation
    print("\n" + "="*80)
    print("N+1 PATTERN CONFIRMATION")
    print("="*80)
    print()

    if sample_metrics['n1_pattern_detected']:
        user_badge_queries = [q for q in sample_metrics['sample_queries'] if 'starview_app_userbadge' in q and 'WHERE' in q]
        print(f"✗ N+1 PATTERN DETECTED")
        print(f"  Found {len(user_badge_queries)} individual UserBadge queries in loop")
        print(f"  This confirms the N+1 anti-pattern in get_user_badge_progress()")
        print()
        print("  Example of repeated queries:")
        for i, query in enumerate(user_badge_queries[:3], 1):
            query_display = query[:120] + "..." if len(query) > 120 else query
            print(f"    {i}. {query_display}")
    else:
        print("✓ NO N+1 PATTERN DETECTED")
        print("  Query count is constant regardless of badge count")
        print("  Optimization appears to be working correctly!")

    # Expected improvement
    print("\n" + "="*80)
    print("EXPECTED IMPROVEMENT AFTER OPTIMIZATION")
    print("="*80)
    print()

    print("After implementing select_related() optimization:")
    print("  - Query count should be CONSTANT (2-3) regardless of badge count")
    print("  - Expected improvement: 50-80% fewer queries for users with many badges")
    print("  - Time improvement: 50-80% faster for users with 10+ badges")
    print()
    print("Target metrics:")
    print("  - User with 0 badges:  2-3 queries (no change)")
    print("  - User with 5 badges:  2-3 queries (was ~7)")
    print("  - User with 10 badges: 2-3 queries (was ~12)")
    print("  - User with 15 badges: 2-3 queries (was ~17)")

    # Cleanup
    print("\n[3] Cleaning up test data...")
    cleanup_test_users()
    print("    Test users deleted successfully")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print()


if __name__ == '__main__':
    main()
