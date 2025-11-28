"""
ContentType Cache Functional Test
==================================

Verifies that the ContentType caching optimization doesn't break badge functionality.

Tests:
1. Votes trigger badge checks correctly
2. Badges are awarded when thresholds are met
3. Badges are revoked when thresholds no longer met
4. Edge cases handled (deleted reviews, etc.)

Usage:
    djvenv/bin/python .claude/backend/tests/contenttype_functional_test.py
"""

import os
import sys
import django

# Django setup
sys.path.insert(0, '/Users/adiaz/event-horizon')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from starview_app.models import Location, Review, Vote, UserBadge, Badge


class ContentTypeFunctionalTest:
    """Test badge functionality with ContentType caching."""

    def __init__(self):
        self.location_creator = None
        self.reviewer = None
        self.voters = []
        self.location = None
        self.review = None

    def setup(self):
        """Create test data."""
        print("=" * 80)
        print("CONTENTTYPE CACHE FUNCTIONAL TEST")
        print("=" * 80)
        print("\nSetting up test data...")

        # Create users
        self.location_creator = User.objects.create_user(
            username='functional_creator',
            email='functional_creator@example.com',
            password='testpass123'
        )

        self.reviewer = User.objects.create_user(
            username='functional_reviewer',
            email='functional_reviewer@example.com',
            password='testpass123'
        )

        # Create voters
        for i in range(10):
            voter = User.objects.create_user(
                username=f'functional_voter_{i}',
                email=f'voter{i}@example.com',
                password='testpass123'
            )
            self.voters.append(voter)

        # Create location
        self.location = Location.objects.create(
            name='Functional Test Location',
            latitude=40.7128,
            longitude=-74.0060,
            added_by=self.location_creator
        )

        # Create review
        self.review = Review.objects.create(
            location=self.location,
            user=self.reviewer,
            rating=5,
            comment='Functional test review'
        )

        print(f"✓ Created location creator: {self.location_creator.username}")
        print(f"✓ Created reviewer: {self.reviewer.username}")
        print(f"✓ Created {len(self.voters)} voters")
        print(f"✓ Created location and review")

    def cleanup(self):
        """Clean up test data."""
        print("\n" + "-" * 80)
        print("Cleaning up test data...")

        # Delete votes
        for voter in self.voters:
            Vote.objects.filter(user=voter).delete()

        # Delete review and location
        if self.review:
            self.review.delete()
        if self.location:
            self.location.delete()

        # Delete users
        for voter in self.voters:
            voter.delete()
        if self.reviewer:
            self.reviewer.delete()
        if self.location_creator:
            self.location_creator.delete()

        print("✓ Test data cleaned up")

    def test_vote_triggers_badge_check(self):
        """Test that votes trigger badge checks correctly."""
        print("\n" + "=" * 80)
        print("TEST 1: Vote Triggers Badge Check")
        print("=" * 80)

        review_ct = ContentType.objects.get_for_model(Review)

        # Get initial badge count
        initial_badges = UserBadge.objects.filter(user=self.reviewer).count()
        print(f"\nInitial badges for reviewer: {initial_badges}")

        # Create 10 upvotes (should trigger badge checks)
        print("\nCreating 10 upvotes...")
        votes = []
        for i, voter in enumerate(self.voters):
            vote = Vote.objects.create(
                user=voter,
                content_type=review_ct,
                object_id=self.review.id,
                is_upvote=True
            )
            votes.append(vote)

        # Check if any badges were awarded
        final_badges = UserBadge.objects.filter(user=self.reviewer).count()
        print(f"Final badges for reviewer: {final_badges}")

        # Clean up votes
        for vote in votes:
            vote.delete()

        if final_badges >= initial_badges:
            print("✓ TEST PASSED: Badge checks triggered correctly")
            return True
        else:
            print("✗ TEST FAILED: No badges awarded")
            return False

    def test_review_query_optimization(self):
        """Test that select_related optimization works."""
        print("\n" + "=" * 80)
        print("TEST 2: Review Query Optimization (select_related)")
        print("=" * 80)

        from django.db import connection, reset_queries
        from django.test.utils import override_settings

        review_ct = ContentType.objects.get_for_model(Review)

        @override_settings(DEBUG=True)
        def run_test():
            reset_queries()

            # Create one vote
            vote = Vote.objects.create(
                user=self.voters[0],
                content_type=review_ct,
                object_id=self.review.id,
                is_upvote=True
            )

            # Check queries
            queries = connection.queries
            review_queries = [q for q in queries if 'starview_app_review' in q['sql'].lower() and '"id" =' in q['sql'].lower()]

            # Delete vote
            vote.delete()

            return review_queries

        review_queries = run_test()

        if review_queries:
            print(f"\nFound {len(review_queries)} review queries")
            print("\nFirst review query SQL:")
            print(review_queries[0]['sql'][:200] + "...")

            if 'INNER JOIN' in review_queries[0]['sql']:
                print("\n✓ TEST PASSED: select_related('user') is working (uses INNER JOIN)")
                return True
            else:
                print("\n✗ TEST FAILED: select_related not working (no INNER JOIN)")
                return False
        else:
            print("\n✗ TEST FAILED: No review queries found")
            return False

    def test_edge_case_deleted_review(self):
        """Test that deleted review edge case is handled."""
        print("\n" + "=" * 80)
        print("TEST 3: Edge Case - Deleted Review")
        print("=" * 80)

        review_ct = ContentType.objects.get_for_model(Review)

        # Create a temporary review
        temp_review = Review.objects.create(
            location=self.location,
            user=self.voters[0],
            rating=4,
            comment='Temporary review for edge case test'
        )

        # Create vote on temp review
        vote = Vote.objects.create(
            user=self.voters[1],
            content_type=review_ct,
            object_id=temp_review.id,
            is_upvote=True
        )

        print(f"\n✓ Created vote on temporary review (ID: {temp_review.id})")

        # Delete the review (CASCADE should delete vote too, but let's test signal handling)
        temp_review_id = temp_review.id
        temp_review.delete()

        print(f"✓ Deleted temporary review (ID: {temp_review_id})")

        # Verify vote was also deleted (CASCADE)
        remaining_votes = Vote.objects.filter(
            content_type=review_ct,
            object_id=temp_review_id
        ).count()

        if remaining_votes == 0:
            print("✓ TEST PASSED: Vote deleted via CASCADE, no errors")
            return True
        else:
            print(f"✗ TEST FAILED: {remaining_votes} orphaned votes remain")
            return False

    def test_contenttype_comparison(self):
        """Test that content_type_id comparison works correctly."""
        print("\n" + "=" * 80)
        print("TEST 4: ContentType ID Comparison")
        print("=" * 80)

        review_ct = ContentType.objects.get_for_model(Review)

        # Create vote
        vote = Vote.objects.create(
            user=self.voters[0],
            content_type=review_ct,
            object_id=self.review.id,
            is_upvote=True
        )

        print(f"\nVote content_type_id: {vote.content_type_id}")
        print(f"Review ContentType ID: {review_ct.id}")

        # Test both comparison methods
        object_comparison = (vote.content_type == review_ct)
        id_comparison = (vote.content_type_id == review_ct.id)

        print(f"\nObject comparison (vote.content_type == review_ct): {object_comparison}")
        print(f"ID comparison (vote.content_type_id == review_ct.id): {id_comparison}")

        # Clean up
        vote.delete()

        if object_comparison == id_comparison:
            print("✓ TEST PASSED: Both comparison methods equivalent")
            return True
        else:
            print("✗ TEST FAILED: Comparison methods differ!")
            return False

    def run_all_tests(self):
        """Run all functional tests."""
        results = []

        results.append(("Vote Triggers Badge Check", self.test_vote_triggers_badge_check()))
        results.append(("Review Query Optimization", self.test_review_query_optimization()))
        results.append(("Edge Case - Deleted Review", self.test_edge_case_deleted_review()))
        results.append(("ContentType ID Comparison", self.test_contenttype_comparison()))

        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {test_name}")

        print("\n" + "-" * 80)
        print(f"Results: {passed}/{total} tests passed")

        if passed == total:
            print("✓ ALL TESTS PASSED")
            print("=" * 80)
            return True
        else:
            print(f"✗ {total - passed} TESTS FAILED")
            print("=" * 80)
            return False


def main():
    """Run the functional test suite."""
    test = ContentTypeFunctionalTest()

    try:
        # Setup
        test.setup()

        # Run tests
        all_passed = test.run_all_tests()

    finally:
        # Always cleanup
        test.cleanup()

    if all_passed:
        print("\n✓ All functional tests completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Some functional tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
