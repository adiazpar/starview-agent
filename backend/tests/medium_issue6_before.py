#!/usr/bin/env python3
"""
Medium Issue #6 - BEFORE Optimization Test
===========================================

Tests BEFORE optimization to establish baseline query count for badge fetching.

Issue: Signal handlers fetch the same badge objects multiple times using
Badge.objects.filter() queries, even though badge data is static and rarely changes.

This test measures:
1. Number of Badge.objects queries per signal execution
2. Total queries for various badge checking scenarios
3. Baseline metrics to compare against AFTER optimization

Expected Results (BEFORE):
- Each signal execution performs 1-2 Badge.objects.filter() queries
- No caching of badge objects
- Redundant badge fetching on every signal invocation
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/Users/adiaz/event-horizon')
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-secret-key-for-running-tests')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection, reset_queries
from django.test.utils import override_settings
from starview_app.models import Location, LocationVisit, Review, ReviewPhoto, Follow, ReviewComment, Badge
from starview_app.services.badge_service import BadgeService
import logging

# Disable logging for cleaner output
logging.disable(logging.CRITICAL)

# Enable query logging
django.db.reset_queries()


def count_badge_queries(queries):
    """Count queries that fetch Badge objects."""
    badge_queries = []
    for query in queries:
        sql = query['sql'].upper()
        if '"STARVIEW_APP_BADGE"' in sql and 'SELECT' in sql:
            badge_queries.append(query)
    return badge_queries


def test_exploration_badge_queries():
    """Test badge queries when checking exploration badges."""
    print("\n" + "="*80)
    print("TEST 1: Exploration Badge Checking (LocationVisit created)")
    print("="*80)

    # Create test user
    user = User.objects.create_user(username='explorer_test', email='explorer@test.com')

    # Create test location
    location = Location.objects.create(
        name='Test Location',
        added_by=user,
        latitude=40.7128,
        longitude=-74.0060
    )

    # Reset query counter
    reset_queries()

    # Trigger badge check (simulates what signal would do)
    BadgeService.check_exploration_badges(user)

    queries = connection.queries
    badge_queries = count_badge_queries(queries)

    print(f"\nTotal queries: {len(queries)}")
    print(f"Badge queries: {len(badge_queries)}")

    if badge_queries:
        print("\nBadge query SQL:")
        for i, query in enumerate(badge_queries, 1):
            print(f"  {i}. {query['sql'][:200]}...")

    badge_query_count = len(badge_queries)

    # Cleanup
    try:
        location.delete()
    except:
        pass
    try:
        user.delete()
    except:
        pass

    return badge_query_count


def test_contribution_badge_queries():
    """Test badge queries when checking contribution badges."""
    print("\n" + "="*80)
    print("TEST 2: Contribution Badge Checking (Location created)")
    print("="*80)

    # Create test user
    user = User.objects.create_user(username='contributor_test', email='contributor@test.com')

    # Reset query counter
    reset_queries()

    # Trigger badge check (simulates what signal would do)
    BadgeService.check_contribution_badges(user)

    queries = connection.queries
    badge_queries = count_badge_queries(queries)

    print(f"\nTotal queries: {len(queries)}")
    print(f"Badge queries: {len(badge_queries)}")

    if badge_queries:
        print("\nBadge query SQL:")
        for i, query in enumerate(badge_queries, 1):
            print(f"  {i}. {query['sql'][:200]}...")

    badge_query_count = len(badge_queries)

    # Cleanup
    try:
        user.delete()
    except:
        pass

    return badge_query_count


def test_review_badge_queries():
    """Test badge queries when checking review badges."""
    print("\n" + "="*80)
    print("TEST 3: Review Badge Checking (Review created)")
    print("="*80)

    # Create test user and location
    user = User.objects.create_user(username='reviewer_test', email='reviewer@test.com')
    location = Location.objects.create(
        name='Test Location 2',
        added_by=user,
        latitude=40.7128,
        longitude=-74.0060
    )

    # Reset query counter
    reset_queries()

    # Trigger badge check (simulates what signal would do)
    BadgeService.check_review_badges(user)

    queries = connection.queries
    badge_queries = count_badge_queries(queries)

    print(f"\nTotal queries: {len(queries)}")
    print(f"Badge queries: {len(badge_queries)}")

    if badge_queries:
        print("\nBadge query SQL:")
        for i, query in enumerate(badge_queries, 1):
            print(f"  {i}. {query['sql'][:200]}...")

    badge_query_count = len(badge_queries)

    # Cleanup (delete location first to avoid FK constraint issues)
    location.delete()
    user.delete()

    return badge_query_count


def test_community_badge_queries():
    """Test badge queries when checking community badges."""
    print("\n" + "="*80)
    print("TEST 4: Community Badge Checking (Follow/Comment created)")
    print("="*80)

    # Create test user
    user = User.objects.create_user(username='community_test', email='community@test.com')

    # Reset query counter
    reset_queries()

    # Trigger badge check (simulates what signal would do)
    BadgeService.check_community_badges(user)

    queries = connection.queries
    badge_queries = count_badge_queries(queries)

    print(f"\nTotal queries: {len(queries)}")
    print(f"Badge queries: {len(badge_queries)}")

    if badge_queries:
        print("\nBadge query SQL:")
        for i, query in enumerate(badge_queries, 1):
            print(f"  {i}. {query['sql'][:200]}...")

    badge_query_count = len(badge_queries)

    # Cleanup
    try:
        user.delete()
    except:
        pass

    return badge_query_count


def test_photographer_badge_queries():
    """Test badge queries when checking photographer badge."""
    print("\n" + "="*80)
    print("TEST 5: Photographer Badge Checking (ReviewPhoto created)")
    print("="*80)

    # Create test user
    user = User.objects.create_user(username='photographer_test', email='photographer@test.com')

    # Reset query counter
    reset_queries()

    # Trigger badge check (simulates what signal would do)
    BadgeService.check_photographer_badge(user)

    queries = connection.queries
    badge_queries = count_badge_queries(queries)

    print(f"\nTotal queries: {len(queries)}")
    print(f"Badge queries: {len(badge_queries)}")

    if badge_queries:
        print("\nBadge query SQL:")
        for i, query in enumerate(badge_queries, 1):
            print(f"  {i}. {query['sql'][:200]}...")

    badge_query_count = len(badge_queries)

    # Cleanup
    try:
        user.delete()
    except:
        pass

    return badge_query_count


def test_pioneer_badge_queries():
    """Test badge queries when checking pioneer badge."""
    print("\n" + "="*80)
    print("TEST 6: Pioneer Badge Checking (Email verified)")
    print("="*80)

    # Create test user
    user = User.objects.create_user(username='pioneer_test', email='pioneer@test.com')

    # Reset query counter
    reset_queries()

    # Trigger badge check (simulates what signal would do)
    BadgeService.check_pioneer_badge(user)

    queries = connection.queries
    badge_queries = count_badge_queries(queries)

    print(f"\nTotal queries: {len(queries)}")
    print(f"Badge queries: {len(badge_queries)}")

    if badge_queries:
        print("\nBadge query SQL:")
        for i, query in enumerate(badge_queries, 1):
            print(f"  {i}. {query['sql'][:200]}...")

    badge_query_count = len(badge_queries)

    # Cleanup
    try:
        user.delete()
    except:
        pass

    return badge_query_count


def test_multiple_signal_executions():
    """Test badge queries across multiple signal executions (worst case)."""
    print("\n" + "="*80)
    print("TEST 7: Multiple Signal Executions (Real-World Scenario)")
    print("="*80)
    print("Simulates: User visits 5 locations, creates 1 location, writes 2 reviews")

    # Create test users and locations
    user = User.objects.create_user(username='active_user', email='active@test.com')
    other_user = User.objects.create_user(username='other_user', email='other@test.com')

    locations = []
    for i in range(5):
        loc = Location.objects.create(
            name=f'Location {i}',
            added_by=other_user,
            latitude=40.7128 + i,
            longitude=-74.0060 + i
        )
        locations.append(loc)

    # Reset query counter
    reset_queries()

    # Simulate user activity
    # 1. Visit 5 locations (5 exploration badge checks)
    for loc in locations[:5]:
        BadgeService.check_exploration_badges(user)

    # 2. Create 1 location (1 contribution badge check)
    BadgeService.check_contribution_badges(user)

    # 3. Write 2 reviews (2 review badge checks)
    BadgeService.check_review_badges(user)
    BadgeService.check_review_badges(user)

    # 4. Gain 1 follower (1 community badge check)
    BadgeService.check_community_badges(user)

    queries = connection.queries
    badge_queries = count_badge_queries(queries)

    print(f"\nTotal badge checks: 9 (5 exploration + 1 contribution + 2 review + 1 community)")
    print(f"Total queries: {len(queries)}")
    print(f"Badge queries: {len(badge_queries)}")
    print(f"Average badge queries per check: {len(badge_queries) / 9:.2f}")

    badge_query_count = len(badge_queries)

    # Cleanup
    try:
        for loc in locations:
            loc.delete()
    except:
        pass
    try:
        user.delete()
    except:
        pass
    try:
        other_user.delete()
    except:
        pass

    return badge_query_count


def main():
    print("\n" + "="*80)
    print("MEDIUM ISSUE #6 - BEFORE OPTIMIZATION BASELINE")
    print("="*80)
    print("Testing badge fetching queries BEFORE optimization")
    print("Issue: Redundant badge fetching in signal handlers")
    print("="*80)

    results = {}

    # Run individual tests
    results['exploration'] = test_exploration_badge_queries()
    results['contribution'] = test_contribution_badge_queries()
    results['review'] = test_review_badge_queries()
    results['community'] = test_community_badge_queries()
    results['photographer'] = test_photographer_badge_queries()
    results['pioneer'] = test_pioneer_badge_queries()
    results['multiple'] = test_multiple_signal_executions()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY - BASELINE METRICS (BEFORE OPTIMIZATION)")
    print("="*80)
    print(f"Exploration badge check:     {results['exploration']} badge queries")
    print(f"Contribution badge check:    {results['contribution']} badge queries")
    print(f"Review badge check:          {results['review']} badge queries")
    print(f"Community badge check:       {results['community']} badge queries")
    print(f"Photographer badge check:    {results['photographer']} badge queries")
    print(f"Pioneer badge check:         {results['pioneer']} badge queries")
    print(f"Multiple operations (9x):    {results['multiple']} badge queries")

    total_single = sum([
        results['exploration'],
        results['contribution'],
        results['review'],
        results['community'],
        results['photographer'],
        results['pioneer']
    ])

    print(f"\nTotal badge queries for 6 different badge checks: {total_single}")
    print(f"Average badge queries per check: {total_single / 6:.2f}")

    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    print("PROBLEM: Every badge checking method fetches Badge objects from database")
    print("IMPACT: 1-2 badge queries per signal execution")
    print("WASTE: Badge data is static - these queries are 100% redundant")
    print("SOLUTION: Cache Badge objects at module level (similar to ContentType cache)")
    print("="*80)

    return results


if __name__ == '__main__':
    with override_settings(DEBUG=True):
        main()
