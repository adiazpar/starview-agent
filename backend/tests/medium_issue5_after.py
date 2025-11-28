#!/usr/bin/env python
"""
AFTER Optimization Test - Medium Issue #5: Duplicate Vote Count Queries

Tests the OPTIMIZED implementation of check_review_badges() to verify query reduction.

Optimization Applied:
- Replaced two separate COUNT queries with single aggregate() query
- Used conditional Count() with filter=Q() to get both upvote_count and total_votes

Expected Result:
- Query reduction: 6 queries → 5 queries (16.7% reduction)
- Both upvote_count and total_votes calculated in single database query

Test Methodology:
1. Create test user with reviews (identical to BEFORE test)
2. Add votes to reviews (identical to BEFORE test)
3. Call check_review_badges(user)
4. Count and analyze database queries
5. Compare to BEFORE baseline

Environment:
- Django virtual environment: djvenv/bin/python
- Test database: SQLite (development)
- Server: http://127.0.0.1:8000/
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
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from starview_app.models import Location, Review, Vote
from starview_app.services.badge_service import BadgeService


def create_test_data():
    """Create test user with reviews and votes (identical to BEFORE test)."""
    print("\n" + "="*80)
    print("SETTING UP TEST DATA")
    print("="*80)

    # Create location creator
    location_creator = User.objects.create_user(
        username='location_creator_after',
        email='creator_after@example.com',
        password='testpass123'
    )
    print(f"✓ Created location creator: {location_creator.username}")

    # Create test user (reviewer)
    user = User.objects.create_user(
        username='test_reviewer_after',
        email='test_after@example.com',
        password='testpass123'
    )
    print(f"✓ Created test user (reviewer): {user.username}")

    # Create 10 test locations (by different user to allow reviews)
    locations = []
    for i in range(10):
        location = Location.objects.create(
            name=f'Test Location After {i+1}',
            latitude=40.7128 + (i * 0.01),
            longitude=-74.0060 + (i * 0.01),
            added_by=location_creator  # Different user to allow reviews
        )
        locations.append(location)
    print(f"✓ Created {len(locations)} test locations")

    # Create 10 reviews (one per location)
    reviews = []
    for i, location in enumerate(locations):
        review = Review.objects.create(
            user=user,
            location=location,
            rating=5,
            comment=f'Test review {i+1}'
        )
        reviews.append(review)
    print(f"✓ Created {len(reviews)} reviews")

    # Create voter users
    voters = []
    for i in range(5):
        voter = User.objects.create_user(
            username=f'voter_after_{i}',
            email=f'voter_after_{i}@example.com',
            password='testpass123'
        )
        voters.append(voter)
    print(f"✓ Created {len(voters)} voter users")

    # Add votes to reviews (mix of upvotes and downvotes)
    review_ct = ContentType.objects.get_for_model(Review)
    vote_count = 0

    for review in reviews[:5]:  # First 5 reviews get upvotes
        for voter in voters:
            Vote.objects.create(
                user=voter,
                content_type=review_ct,
                object_id=review.id,
                is_upvote=True
            )
            vote_count += 1

    for review in reviews[5:8]:  # Next 3 reviews get downvotes
        for voter in voters[:3]:
            Vote.objects.create(
                user=voter,
                content_type=review_ct,
                object_id=review.id,
                is_upvote=False
            )
            vote_count += 1

    print(f"✓ Created {vote_count} votes on reviews")
    print(f"  - Upvotes: {Vote.objects.filter(content_type=review_ct, is_upvote=True).count()}")
    print(f"  - Downvotes: {Vote.objects.filter(content_type=review_ct, is_upvote=False).count()}")

    return user


def test_after_optimization():
    """Test AFTER optimization - measure optimized query count."""
    print("\n" + "="*80)
    print("AFTER OPTIMIZATION - OPTIMIZED METRICS")
    print("="*80)

    # Create test data
    user = create_test_data()

    # Reset query log
    connection.queries_log.clear()

    print("\n" + "-"*80)
    print("RUNNING check_review_badges(user) - OPTIMIZED VERSION")
    print("-"*80)

    # Measure queries with context manager
    with CaptureQueriesContext(connection) as context:
        newly_awarded = BadgeService.check_review_badges(user)

    # Analyze results
    query_count = len(context.captured_queries)

    print(f"\n✓ Badge check complete")
    print(f"  - Newly awarded badges: {len(newly_awarded)}")

    print("\n" + "="*80)
    print(f"QUERY ANALYSIS - TOTAL QUERIES: {query_count}")
    print("="*80)

    # Print each query with details
    for i, query in enumerate(context.captured_queries, 1):
        sql = query['sql']
        time = query['time']

        print(f"\nQuery {i}: ({time}s)")
        print("-" * 80)

        # Identify query type
        if 'COUNT' in sql and 'FILTER' in sql:
            print("[OPTIMIZED AGGREGATE QUERY - Single query for upvote + total counts]")
        elif 'COUNT' in sql:
            if 'starview_app_review' in sql:
                print("[REVIEW COUNT QUERY]")
            else:
                print("[COUNT QUERY]")
        elif 'django_content_type' in sql:
            print("[CONTENTTYPE LOOKUP]")
        elif 'starview_app_review' in sql and 'SELECT' in sql:
            print("[REVIEW IDS QUERY]")
        elif 'starview_app_badge' in sql:
            print("[BADGE FETCH QUERY]")
        elif 'INSERT' in sql or 'UPDATE' in sql:
            print("[BADGE AWARD QUERY]")
        else:
            print("[OTHER QUERY]")

        # Print SQL (truncated if too long)
        if len(sql) > 200:
            print(sql[:200] + "...")
        else:
            print(sql)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Queries: {query_count}")
    print(f"Badges Awarded: {len(newly_awarded)}")

    # Identify aggregate queries
    count_queries = [q for q in context.captured_queries if 'COUNT' in q['sql']]
    aggregate_queries = [q for q in count_queries if 'FILTER' in q['sql']]
    vote_queries = [q for q in count_queries if 'starview_app_vote' in q['sql']]

    print(f"\nVote-related COUNT queries: {len(vote_queries)}")
    if aggregate_queries:
        print(f"  ✓ Using optimized aggregate query with conditional COUNT")
        for i, q in enumerate(aggregate_queries, 1):
            print(f"    {i}. Aggregate (upvotes + total): {q['time']}s")
    else:
        print(f"  ⚠️  No aggregate query detected")

    if len(vote_queries) == 1:
        print("\n✓ OPTIMIZATION SUCCESSFUL: Single vote count query")
        print("    Expected: Single aggregated query with COUNT for both upvotes and total")
        print("    Actual: ✓ Confirmed - using aggregate() with conditional Count()")
    elif len(vote_queries) > 1:
        print("\n⚠️  OPTIMIZATION INCOMPLETE: Still multiple vote queries")
        print(f"    Expected: 1 query")
        print(f"    Actual: {len(vote_queries)} queries")

    print("\n" + "="*80)
    print("OPTIMIZATION RESULTS")
    print("="*80)

    # Compare to baseline (from BEFORE test)
    baseline_queries = 6  # From medium_issue5_before.py results
    baseline_vote_queries = 2

    improvement = baseline_queries - query_count
    percentage = (improvement / baseline_queries * 100) if baseline_queries > 0 else 0

    print(f"Baseline (BEFORE): {baseline_queries} queries")
    print(f"Optimized (AFTER): {query_count} queries")
    print(f"Reduction: {improvement} queries ({percentage:.1f}% improvement)")
    print(f"")
    print(f"Vote queries BEFORE: {baseline_vote_queries}")
    print(f"Vote queries AFTER: {len(vote_queries)}")
    print(f"Vote query reduction: {baseline_vote_queries - len(vote_queries)} queries")

    if improvement >= 1:
        print("\n✓ OPTIMIZATION VERIFIED - Query reduction achieved!")
    else:
        print("\n⚠️  WARNING - Expected query reduction not achieved")

    return query_count


def cleanup():
    """Clean up test data."""
    print("\n" + "-"*80)
    print("CLEANING UP TEST DATA")
    print("-"*80)

    # Delete test users (cascade will delete reviews, votes, etc.)
    deleted_users = User.objects.filter(username__startswith='test_reviewer_after').delete()
    deleted_creators = User.objects.filter(username__startswith='location_creator_after').delete()
    deleted_voters = User.objects.filter(username__startswith='voter_after_').delete()
    deleted_locations = Location.objects.filter(name__startswith='Test Location After').delete()

    print(f"✓ Cleaned up test data")
    print(f"  - Reviewers: {deleted_users[0]}")
    print(f"  - Creators: {deleted_creators[0]}")
    print(f"  - Voters: {deleted_voters[0]}")
    print(f"  - Locations: {deleted_locations[0]}")


if __name__ == '__main__':
    try:
        optimized_queries = test_after_optimization()

        print("\n" + "="*80)
        print("TEST COMPLETE")
        print("="*80)
        print(f"Optimized Query Count: {optimized_queries}")
        print("\nNext Steps:")
        print("1. Compare BEFORE (6 queries) vs AFTER ({} queries)".format(optimized_queries))
        print("2. Run functional tests to verify badge logic correctness")
        print("3. Document optimization in summary report")

    finally:
        cleanup()
