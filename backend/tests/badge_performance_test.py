#!/usr/bin/env python
"""
Badge Performance Test - BEFORE/AFTER Index Optimization

Tests query performance for Badge model queries with missing composite indexes.

Purpose:
- Measure baseline performance BEFORE adding indexes
- Re-run AFTER adding indexes to measure improvement
- Validate that indexes improve query performance by 25-50%

Test Environment:
- Local PostgreSQL database (same as production)
- Realistic test data (user with 10 visits, 5 locations, 5 reviews)
- 10 iterations per test for statistical accuracy

Expected Results AFTER Fix:
- Query time reduced by 25-50%
- EXPLAIN ANALYZE shows "Index Scan" instead of "Seq Scan" or filesort
- All badge checking methods faster

Usage:
    djvenv/bin/python .claude/backend/tests/badge_performance_test.py
"""

import os
import sys
import time
import django
from statistics import mean, stdev

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection, reset_queries
from django.test.utils import override_settings
from starview_app.models import Badge, UserBadge, LocationVisit, Location, Review
from starview_app.services.badge_service import BadgeService


class BadgePerformanceTest:
    """Test badge query performance before/after index optimization."""

    def __init__(self):
        self.test_user = None
        self.reviewer_user = None
        self.results = {}

    def setup(self):
        """Create test data for performance testing."""
        print("\n" + "="*80)
        print("BADGE PERFORMANCE TEST - SETUP")
        print("="*80)

        # Create test user
        username = f"perf_test_user_{int(time.time())}"
        self.test_user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="testpass123"
        )
        print(f"✓ Created test user: {self.test_user.username}")

        # Create reviewer user (for reviews, since users can't review their own locations)
        reviewer_username = f"perf_reviewer_{int(time.time())}"
        self.reviewer_user = User.objects.create_user(
            username=reviewer_username,
            email=f"{reviewer_username}@example.com",
            password="testpass123"
        )
        print(f"✓ Created reviewer user: {self.reviewer_user.username}")

        # Create test locations (need for visits)
        locations = []
        for i in range(10):
            location = Location.objects.create(
                name=f"Test Location {i}",
                latitude=40.7128 + (i * 0.01),
                longitude=-74.0060 + (i * 0.01),
                elevation=100.0,
                added_by=self.test_user
            )
            locations.append(location)
        print(f"✓ Created {len(locations)} test locations")

        # Create location visits (use get_or_create to avoid unique constraint issues)
        for location in locations:
            LocationVisit.objects.get_or_create(
                user=self.test_user,
                location=location
            )
        print(f"✓ Created {len(locations)} location visits")

        # Create reviews by reviewer_user (users can't review their own locations)
        for location in locations[:5]:
            Review.objects.get_or_create(
                user=self.reviewer_user,
                location=location,
                defaults={
                    'rating': 5,
                    'comment': "Great location for stargazing!"
                }
            )
        print(f"✓ Created 5 test reviews")

        print(f"\nTest Data Summary:")
        print(f"  - User: {self.test_user.username}")
        print(f"  - Location Visits: {LocationVisit.objects.filter(user=self.test_user).count()}")
        print(f"  - Locations Added: {Location.objects.filter(added_by=self.test_user).count()}")
        print(f"  - Reviews Written: {Review.objects.filter(user=self.test_user).count()}")

    def teardown(self):
        """Clean up test data."""
        if self.test_user:
            # Delete in correct order (relationships)
            Review.objects.filter(user=self.reviewer_user).delete()
            LocationVisit.objects.filter(user=self.test_user).delete()
            Location.objects.filter(added_by=self.test_user).delete()
            UserBadge.objects.filter(user=self.test_user).delete()
            UserBadge.objects.filter(user=self.reviewer_user).delete()
            self.test_user.delete()
            if self.reviewer_user:
                self.reviewer_user.delete()
            print(f"\n✓ Cleaned up test users and related data")

    def run_timed_test(self, test_func, iterations=10):
        """Run a test function multiple times and return timing statistics."""
        times = []
        query_counts = []

        for i in range(iterations):
            # Reset query tracking
            reset_queries()

            # Time the function
            start = time.time()
            test_func()
            elapsed = (time.time() - start) * 1000  # Convert to milliseconds

            times.append(elapsed)
            query_counts.append(len(connection.queries))

        return {
            'avg_time_ms': mean(times),
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'stdev_ms': stdev(times) if len(times) > 1 else 0,
            'avg_queries': mean(query_counts),
            'total_iterations': iterations
        }

    def test_exploration_badges(self):
        """Test check_exploration_badges performance."""
        def run_check():
            BadgeService.check_exploration_badges(self.test_user)

        print("\n" + "-"*80)
        print("TEST: check_exploration_badges()")
        print("-"*80)

        results = self.run_timed_test(run_check)
        self.results['exploration_badges'] = results

        print(f"Average Time: {results['avg_time_ms']:.2f}ms")
        print(f"Min/Max: {results['min_time_ms']:.2f}ms / {results['max_time_ms']:.2f}ms")
        print(f"Std Dev: {results['stdev_ms']:.2f}ms")
        print(f"Avg Queries: {results['avg_queries']:.1f}")

    def test_contribution_badges(self):
        """Test check_contribution_badges performance."""
        def run_check():
            BadgeService.check_contribution_badges(self.test_user)

        print("\n" + "-"*80)
        print("TEST: check_contribution_badges()")
        print("-"*80)

        results = self.run_timed_test(run_check)
        self.results['contribution_badges'] = results

        print(f"Average Time: {results['avg_time_ms']:.2f}ms")
        print(f"Min/Max: {results['min_time_ms']:.2f}ms / {results['max_time_ms']:.2f}ms")
        print(f"Std Dev: {results['stdev_ms']:.2f}ms")
        print(f"Avg Queries: {results['avg_queries']:.1f}")

    def test_quality_badges(self):
        """Test check_quality_badges performance."""
        def run_check():
            BadgeService.check_quality_badges(self.test_user)

        print("\n" + "-"*80)
        print("TEST: check_quality_badges()")
        print("-"*80)

        results = self.run_timed_test(run_check)
        self.results['quality_badges'] = results

        print(f"Average Time: {results['avg_time_ms']:.2f}ms")
        print(f"Min/Max: {results['min_time_ms']:.2f}ms / {results['max_time_ms']:.2f}ms")
        print(f"Std Dev: {results['stdev_ms']:.2f}ms")
        print(f"Avg Queries: {results['avg_queries']:.1f}")

    def test_review_badges(self):
        """Test check_review_badges performance."""
        def run_check():
            BadgeService.check_review_badges(self.test_user)

        print("\n" + "-"*80)
        print("TEST: check_review_badges()")
        print("-"*80)

        results = self.run_timed_test(run_check)
        self.results['review_badges'] = results

        print(f"Average Time: {results['avg_time_ms']:.2f}ms")
        print(f"Min/Max: {results['min_time_ms']:.2f}ms / {results['max_time_ms']:.2f}ms")
        print(f"Std Dev: {results['stdev_ms']:.2f}ms")
        print(f"Avg Queries: {results['avg_queries']:.1f}")

    def test_community_badges(self):
        """Test check_community_badges performance."""
        def run_check():
            BadgeService.check_community_badges(self.test_user)

        print("\n" + "-"*80)
        print("TEST: check_community_badges()")
        print("-"*80)

        results = self.run_timed_test(run_check)
        self.results['community_badges'] = results

        print(f"Average Time: {results['avg_time_ms']:.2f}ms")
        print(f"Min/Max: {results['min_time_ms']:.2f}ms / {results['max_time_ms']:.2f}ms")
        print(f"Std Dev: {results['stdev_ms']:.2f}ms")
        print(f"Avg Queries: {results['avg_queries']:.1f}")

    def test_badge_query_explain(self):
        """Run EXPLAIN ANALYZE on the slow badge query."""
        print("\n" + "-"*80)
        print("EXPLAIN ANALYZE: Badge Query")
        print("-"*80)

        # Run EXPLAIN ANALYZE on the actual query used by BadgeService
        with connection.cursor() as cursor:
            cursor.execute("""
                EXPLAIN ANALYZE
                SELECT * FROM starview_app_badge
                WHERE category = 'EXPLORATION'
                  AND criteria_type = 'LOCATION_VISITS'
                ORDER BY criteria_value;
            """)

            results = cursor.fetchall()

            print("\nQuery Plan:")
            for row in results:
                print(f"  {row[0]}")

        self.results['query_plan'] = [row[0] for row in results]

    def print_summary(self):
        """Print performance test summary."""
        print("\n" + "="*80)
        print("PERFORMANCE TEST SUMMARY")
        print("="*80)

        # Calculate total time across all tests
        total_time = sum(r['avg_time_ms'] for r in self.results.values() if 'avg_time_ms' in r)
        total_queries = sum(r['avg_queries'] for r in self.results.values() if 'avg_queries' in r)

        print(f"\nTotal Average Time: {total_time:.2f}ms")
        print(f"Total Average Queries: {total_queries:.1f}")

        print("\nDetailed Breakdown:")
        for test_name, results in self.results.items():
            if 'avg_time_ms' in results:
                print(f"  {test_name}:")
                print(f"    - Time: {results['avg_time_ms']:.2f}ms")
                print(f"    - Queries: {results['avg_queries']:.1f}")

        # Check query plan for index usage
        if 'query_plan' in self.results:
            plan_text = '\n'.join(self.results['query_plan'])

            print("\nQuery Plan Analysis:")
            if 'Index Scan' in plan_text:
                print("  ✓ Using index (Index Scan)")
            elif 'Seq Scan' in plan_text:
                print("  ✗ Sequential scan (NO INDEX!)")

            if 'filesort' in plan_text.lower() or 'Sort' in plan_text:
                print("  ✗ Using filesort (ORDER BY not indexed)")
            else:
                print("  ✓ No filesort needed")

    def run_all_tests(self):
        """Run all performance tests."""
        try:
            self.setup()

            # Run all badge checking tests
            self.test_exploration_badges()
            self.test_contribution_badges()
            self.test_quality_badges()
            self.test_review_badges()
            self.test_community_badges()

            # Run query plan analysis
            self.test_badge_query_explain()

            # Print summary
            self.print_summary()

            print("\n" + "="*80)
            print("TEST COMPLETE")
            print("="*80)
            print("\nNext Steps:")
            print("1. Note the BEFORE metrics above")
            print("2. Run migration: djvenv/bin/python manage.py migrate")
            print("3. Re-run this test to measure improvement")
            print("4. Compare BEFORE vs AFTER results")
            print("\n")

        finally:
            self.teardown()


if __name__ == '__main__':
    # Enable query logging
    from django.conf import settings
    settings.DEBUG = True

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     BADGE PERFORMANCE TEST SUITE                             ║
║                                                                              ║
║  Purpose: Measure badge query performance BEFORE index optimization         ║
║  Target: 25-50% improvement after adding composite indexes                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    test = BadgePerformanceTest()
    test.run_all_tests()
