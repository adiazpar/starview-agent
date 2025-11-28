"""
ContentType Cache Optimization Test
====================================

Tests the performance impact of caching ContentType objects at module level
in signal handlers instead of querying the database on every signal invocation.

BEFORE Optimization:
- Every vote triggers ContentType.objects.get_for_model(Review) query
- Expected: 50 votes = 50 ContentType queries

AFTER Optimization:
- First vote triggers query (cache miss), subsequent votes use cached value
- Expected: 50 votes = 1 ContentType query (98% reduction)

Test Strategy:
1. Reset database query counter
2. Create 50 vote operations (simulating real user activity)
3. Track ContentType queries using connection.queries
4. Measure total queries and time
5. Calculate cache hit rate

Usage:
    djvenv/bin/python .claude/backend/tests/contenttype_cache_test.py
"""

import os
import sys
import django
import time

# Django setup
sys.path.insert(0, '/Users/adiaz/event-horizon')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import connection, reset_queries
from django.test.utils import override_settings
from starview_app.models import Location, Review, Vote


class ContentTypeCacheTest:
    """Test ContentType caching in signal handlers."""

    def __init__(self):
        self.test_user = None
        self.reviewer_users = []
        self.test_location = None
        self.test_review = None
        self.review_ct = None

    def setup(self):
        """Create test data."""
        print("=" * 80)
        print("CONTENTTYPE CACHE OPTIMIZATION TEST")
        print("=" * 80)
        print("\nSetting up test data...")

        # Create test user (location creator)
        self.test_user = User.objects.create_user(
            username='contenttype_test_user',
            email='contenttype_test@example.com',
            password='testpass123'
        )

        # Create 50 reviewer users (to allow 50 unique votes)
        print("Creating 50 reviewer users...")
        for i in range(50):
            reviewer = User.objects.create_user(
                username=f'reviewer_{i}',
                email=f'reviewer{i}@example.com',
                password='testpass123'
            )
            self.reviewer_users.append(reviewer)

        # Create test location
        self.test_location = Location.objects.create(
            name='ContentType Test Location',
            latitude=40.7128,
            longitude=-74.0060,
            added_by=self.test_user
        )

        # Create test review (by first reviewer)
        self.test_review = Review.objects.create(
            location=self.test_location,
            user=self.reviewer_users[0],
            rating=5,
            comment='Test review for ContentType cache testing'
        )

        # Get Review ContentType for comparison
        self.review_ct = ContentType.objects.get_for_model(Review)

        print(f"✓ Created location creator: {self.test_user.username}")
        print(f"✓ Created 50 reviewer users")
        print(f"✓ Created test location: {self.test_location.name}")
        print(f"✓ Created test review: {self.test_review.id}")
        print(f"✓ Review ContentType ID: {self.review_ct.id}")

    def cleanup(self):
        """Clean up test data."""
        print("\n" + "-" * 80)
        print("Cleaning up test data...")

        # Delete in reverse order to avoid FK constraints
        for reviewer in self.reviewer_users:
            Vote.objects.filter(user=reviewer).delete()
        if self.test_review:
            self.test_review.delete()
        if self.test_location:
            self.test_location.delete()
        for reviewer in self.reviewer_users:
            reviewer.delete()
        if self.test_user:
            self.test_user.delete()

        print("✓ Test data cleaned up")

    def count_contenttype_queries(self, queries):
        """
        Count ContentType queries in query log.

        Looks for queries to django_content_type table.
        """
        contenttype_queries = []
        review_queries = []
        user_queries = []

        for query in queries:
            sql = query['sql']

            # Look for ContentType queries (case-insensitive)
            if 'django_content_type' in sql.lower():
                contenttype_queries.append(query)

            # Look for Review queries via get(id=...)
            if 'SELECT' in sql and 'starview_app_review' in sql.lower() and '"id" =' in sql.lower():
                review_queries.append(query)

            # Look for standalone User queries via get(id=...) but NOT JOINs
            if 'SELECT' in sql and 'auth_user' in sql.lower() and '"id" =' in sql.lower():
                # Exclude queries that are part of a JOIN (select_related)
                if 'JOIN' not in sql.upper() and sql.startswith('SELECT "auth_user"'):
                    user_queries.append(query)

        return contenttype_queries, review_queries, user_queries

    def analyze_queries(self, queries, duration_ms):
        """Analyze query log and return metrics."""
        contenttype_queries, review_queries, user_queries = self.count_contenttype_queries(queries)

        return {
            'total_queries': len(queries),
            'contenttype_queries': len(contenttype_queries),
            'review_queries': len(review_queries),
            'user_queries': len(user_queries),
            'contenttype_query_percentage': (len(contenttype_queries) / len(queries) * 100) if queries else 0,
            'total_time_ms': duration_ms,
            'avg_time_per_vote_ms': duration_ms / 50,
            'sample_contenttype_queries': contenttype_queries[:3],  # First 3 samples
            'sample_review_queries': review_queries[:3],  # First 3 samples
            'sample_user_queries': user_queries[:3]  # First 3 samples
        }

    @override_settings(DEBUG=True)
    def run_test(self, num_votes=50):
        """
        Run the performance test.

        Creates num_votes vote operations and measures ContentType query count.
        """
        print("\n" + "=" * 80)
        print(f"RUNNING PERFORMANCE TEST ({num_votes} votes)")
        print("=" * 80)

        # Reset query counter
        reset_queries()

        # Track time
        start_time = time.time()

        # Create votes (triggers signal handlers)
        print(f"\nCreating {num_votes} votes...")
        votes_created = []

        for i in range(num_votes):
            # Alternate between upvotes and downvotes
            is_upvote = (i % 2 == 0)

            # Create vote with unique user (triggers check_badges_on_vote signal)
            vote = Vote.objects.create(
                user=self.reviewer_users[i],
                content_type=self.review_ct,
                object_id=self.test_review.id,
                is_upvote=is_upvote
            )
            votes_created.append(vote)

            if (i + 1) % 10 == 0:
                print(f"  ✓ Created {i + 1}/{num_votes} votes...")

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        print(f"\n✓ All {num_votes} votes created in {duration_ms:.2f}ms")

        # Analyze queries
        queries = connection.queries
        metrics = self.analyze_queries(queries, duration_ms)

        # Clean up votes
        print(f"\nCleaning up {len(votes_created)} votes...")
        for vote in votes_created:
            vote.delete()
        print("✓ Votes cleaned up")

        return metrics

    def print_results(self, metrics, show_all_queries=False):
        """Print test results in a formatted way."""
        print("\n" + "=" * 80)
        print("TEST RESULTS")
        print("=" * 80)

        print(f"\nTotal Votes Processed:        {50}")
        print(f"Total Database Queries:       {metrics['total_queries']}")
        print(f"ContentType Queries:          {metrics['contenttype_queries']}")
        print(f"Review Get Queries:           {metrics['review_queries']}")
        print(f"User Get Queries:             {metrics['user_queries']}")
        print(f"ContentType Query %:          {metrics['contenttype_query_percentage']:.1f}%")
        print(f"Total Time:                   {metrics['total_time_ms']:.2f}ms")
        print(f"Avg Time per Vote:            {metrics['avg_time_per_vote_ms']:.2f}ms")

        if metrics['sample_contenttype_queries']:
            print(f"\nSample ContentType Queries (first 3):")
            for i, query in enumerate(metrics['sample_contenttype_queries'], 1):
                print(f"\n  Query {i}:")
                print(f"  SQL: {query['sql'][:150]}...")
                print(f"  Time: {query['time']}s")

        if metrics['sample_review_queries']:
            print(f"\nSample Review.objects.get() Queries (first 3):")
            for i, query in enumerate(metrics['sample_review_queries'], 1):
                print(f"\n  Query {i}:")
                print(f"  SQL: {query['sql'][:150]}...")
                print(f"  Time: {query['time']}s")

        if metrics['sample_user_queries']:
            print(f"\nSample User.objects.get() Queries (first 3):")
            for i, query in enumerate(metrics['sample_user_queries'], 1):
                print(f"\n  Query {i}:")
                print(f"  SQL: {query['sql'][:200]}...")
                print(f"  Time: {query['time']}s")

        if show_all_queries:
            print("\n" + "=" * 80)
            print("REVIEW QUERIES (showing if select_related works):")
            print("=" * 80)
            if metrics['sample_review_queries']:
                for i, query in enumerate(metrics['sample_review_queries'][:2], 1):
                    print(f"\nReview Query {i}:")
                    print(f"  {query['sql']}")
                    if 'JOIN' in query['sql'].upper():
                        print("  ✓ Uses JOIN (select_related working!)")
                    else:
                        print("  ✗ No JOIN (select_related NOT working)")

            print("\n" + "=" * 80)
            print("ALL QUERIES (first 10):")
            print("=" * 80)
            for i, query in enumerate(connection.queries[:10], 1):
                print(f"\nQuery {i}:")
                print(f"  {query['sql'][:150]}")

        print("\n" + "=" * 80)

        # Expected results
        print("\nEXPECTED RESULTS:")
        print("\nBEFORE Optimization:")
        print("  - ContentType queries: ~50 (one per vote)")
        print("  - ContentType query %: High percentage of total queries")
        print("  - Cache hit rate: 0%")

        print("\nAFTER Optimization:")
        print("  - ContentType queries: 1 (only first vote)")
        print("  - ContentType query %: <5% of total queries")
        print("  - Cache hit rate: 98% (49/50 votes)")
        print("  - Query reduction: ~98%")

        print("\n" + "=" * 80)


def main():
    """Run the test."""
    test = ContentTypeCacheTest()

    try:
        # Setup
        test.setup()

        # Run test
        metrics = test.run_test(num_votes=50)

        # Print results (show first 10 queries for debugging)
        test.print_results(metrics, show_all_queries=True)

    finally:
        # Always cleanup
        test.cleanup()

    print("\n✓ Test completed successfully!")


if __name__ == '__main__':
    main()
