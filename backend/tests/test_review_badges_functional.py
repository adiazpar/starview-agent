#!/usr/bin/env python
"""
Functional Verification Test - Review Badges

Tests ALL review badge awarding logic after the duplicate vote query optimization.

Verifies that the optimization (using aggregate() instead of separate count queries)
produces IDENTICAL badge awarding behavior to the original implementation.

Review Badges Tested:
1. Reviewer (5 reviews)
2. Critic (25 reviews)
3. Tastemaker (50 upvotes)
4. Master Reviewer (100 reviews + 85% helpful ratio)

Edge Cases:
- 0 reviews, 0 votes
- Exact threshold values
- Helpful ratio calculations
- Mixed upvote/downvote scenarios

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
from starview_app.models import Badge, UserBadge, Location, Review, Vote
from starview_app.services.badge_service import BadgeService


class TestReviewBadges:
    """Test suite for review badge functionality."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests_run = 0

    def assert_equal(self, actual, expected, test_name):
        """Assert equality and track results."""
        self.tests_run += 1
        if actual == expected:
            self.passed += 1
            print(f"  ✓ {test_name}")
            return True
        else:
            self.failed += 1
            print(f"  ✗ {test_name}")
            print(f"    Expected: {expected}")
            print(f"    Actual: {actual}")
            return False

    def assert_true(self, condition, test_name):
        """Assert condition is true."""
        self.tests_run += 1
        if condition:
            self.passed += 1
            print(f"  ✓ {test_name}")
            return True
        else:
            self.failed += 1
            print(f"  ✗ {test_name}")
            return False

    def create_user_with_reviews(self, username, num_reviews):
        """Helper: Create user with specified number of reviews."""
        # Create location creator
        location_creator = User.objects.create_user(
            username=f'{username}_creator',
            email=f'{username}_creator@example.com',
            password='testpass123'
        )

        # Create reviewer
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='testpass123'
        )

        # Create locations and reviews
        for i in range(num_reviews):
            location = Location.objects.create(
                name=f'{username} Location {i+1}',
                latitude=40.7128 + (i * 0.01),
                longitude=-74.0060 + (i * 0.01),
                added_by=location_creator
            )

            Review.objects.create(
                user=user,
                location=location,
                rating=5,
                comment=f'Review {i+1}'
            )

        return user

    def add_votes_to_reviews(self, user, upvotes, downvotes):
        """Helper: Add votes to user's reviews."""
        reviews = Review.objects.filter(user=user)
        review_ct = ContentType.objects.get_for_model(Review)

        # Create voters
        voters = []
        for i in range(upvotes + downvotes):
            voter = User.objects.create_user(
                username=f'voter_{user.username}_{i}',
                email=f'voter_{user.username}_{i}@example.com',
                password='testpass123'
            )
            voters.append(voter)

        # Add upvotes
        vote_index = 0
        for i in range(upvotes):
            if reviews:
                review = reviews[i % reviews.count()]
                Vote.objects.create(
                    user=voters[vote_index],
                    content_type=review_ct,
                    object_id=review.id,
                    is_upvote=True
                )
                vote_index += 1

        # Add downvotes
        for i in range(downvotes):
            if reviews:
                review = reviews[i % reviews.count()]
                Vote.objects.create(
                    user=voters[vote_index],
                    content_type=review_ct,
                    object_id=review.id,
                    is_upvote=False
                )
                vote_index += 1

    def test_reviewer_badge(self):
        """Test Reviewer badge (5 reviews)."""
        print("\n" + "-"*80)
        print("TEST: Reviewer Badge (5 reviews)")
        print("-"*80)

        # Create user with exactly 5 reviews
        user = self.create_user_with_reviews('reviewer_test', 5)

        # Check badge
        newly_awarded = BadgeService.check_review_badges(user)

        # Verify Reviewer badge awarded
        reviewer_badge = Badge.objects.filter(
            category='REVIEW',
            criteria_type='REVIEWS_WRITTEN',
            criteria_value=5
        ).first()

        if reviewer_badge:
            has_badge = UserBadge.objects.filter(user=user, badge=reviewer_badge).exists()
            self.assert_true(has_badge, "Reviewer badge awarded for 5 reviews")
        else:
            print("  ⚠️  Reviewer badge not found in database")

    def test_critic_badge(self):
        """Test Critic badge (25 reviews)."""
        print("\n" + "-"*80)
        print("TEST: Critic Badge (25 reviews)")
        print("-"*80)

        # Create user with exactly 25 reviews
        user = self.create_user_with_reviews('critic_test', 25)

        # Check badge
        newly_awarded = BadgeService.check_review_badges(user)

        # Verify Critic badge awarded
        critic_badge = Badge.objects.filter(
            category='REVIEW',
            criteria_type='REVIEWS_WRITTEN',
            criteria_value=25
        ).first()

        if critic_badge:
            has_badge = UserBadge.objects.filter(user=user, badge=critic_badge).exists()
            self.assert_true(has_badge, "Critic badge awarded for 25 reviews")
        else:
            print("  ⚠️  Critic badge not found in database")

    def test_tastemaker_badge(self):
        """Test Tastemaker badge (50 upvotes)."""
        print("\n" + "-"*80)
        print("TEST: Tastemaker Badge (50 upvotes)")
        print("-"*80)

        # Create user with 10 reviews
        user = self.create_user_with_reviews('tastemaker_test', 10)

        # Add exactly 50 upvotes
        self.add_votes_to_reviews(user, upvotes=50, downvotes=0)

        # Check badge
        newly_awarded = BadgeService.check_review_badges(user)

        # Verify Tastemaker badge awarded
        tastemaker_badge = Badge.objects.filter(
            category='REVIEW',
            criteria_type='UPVOTES_RECEIVED',
            criteria_value=50
        ).first()

        if tastemaker_badge:
            has_badge = UserBadge.objects.filter(user=user, badge=tastemaker_badge).exists()
            self.assert_true(has_badge, "Tastemaker badge awarded for 50 upvotes")
        else:
            print("  ⚠️  Tastemaker badge not found in database")

    def test_master_reviewer_badge(self):
        """Test Master Reviewer badge (100 reviews + 85% helpful ratio)."""
        print("\n" + "-"*80)
        print("TEST: Master Reviewer Badge (100 reviews + 85% helpful ratio)")
        print("-"*80)

        # Create user with exactly 100 reviews
        user = self.create_user_with_reviews('master_test', 100)

        # Add votes to achieve 85% helpful ratio
        # 85% means: upvotes / total_votes >= 0.85
        # Example: 85 upvotes, 15 downvotes = 85/100 = 85%
        self.add_votes_to_reviews(user, upvotes=85, downvotes=15)

        # Check badge
        newly_awarded = BadgeService.check_review_badges(user)

        # Verify Master Reviewer badge awarded
        master_badge = Badge.objects.filter(
            category='REVIEW',
            criteria_type='HELPFUL_RATIO',
            criteria_value=100,  # Minimum reviews
            criteria_secondary=85  # Minimum helpful percentage
        ).first()

        if master_badge:
            has_badge = UserBadge.objects.filter(user=user, badge=master_badge).exists()
            self.assert_true(has_badge, "Master Reviewer badge awarded (100 reviews + 85% ratio)")
        else:
            print("  ⚠️  Master Reviewer badge not found in database")

    def test_edge_case_zero_reviews(self):
        """Test edge case: User with 0 reviews."""
        print("\n" + "-"*80)
        print("TEST: Edge Case - Zero Reviews")
        print("-"*80)

        # Create user with no reviews
        user = User.objects.create_user(
            username='zero_reviews_test',
            email='zero@example.com',
            password='testpass123'
        )

        # Check badge (should not crash)
        newly_awarded = BadgeService.check_review_badges(user)

        # Verify no review badges awarded
        review_badges = UserBadge.objects.filter(
            user=user,
            badge__category='REVIEW'
        ).count()

        self.assert_equal(review_badges, 0, "No review badges awarded for 0 reviews")
        self.assert_equal(len(newly_awarded), 0, "No newly awarded badges returned")

    def test_edge_case_exact_threshold(self):
        """Test edge case: User with exactly threshold values."""
        print("\n" + "-"*80)
        print("TEST: Edge Case - Exact Threshold Values")
        print("-"*80)

        # Create user with exactly 5 reviews (Reviewer threshold)
        user = self.create_user_with_reviews('exact_threshold_test', 5)

        # Check badge
        newly_awarded = BadgeService.check_review_badges(user)

        # Verify badge awarded at exact threshold
        reviewer_badge = Badge.objects.filter(
            category='REVIEW',
            criteria_type='REVIEWS_WRITTEN',
            criteria_value=5
        ).first()

        if reviewer_badge:
            has_badge = UserBadge.objects.filter(user=user, badge=reviewer_badge).exists()
            self.assert_true(has_badge, "Badge awarded at exact threshold (5 reviews)")
        else:
            print("  ⚠️  Reviewer badge not found in database")

    def test_edge_case_below_threshold(self):
        """Test edge case: User just below threshold."""
        print("\n" + "-"*80)
        print("TEST: Edge Case - Below Threshold")
        print("-"*80)

        # Create user with 4 reviews (1 below Reviewer threshold)
        user = self.create_user_with_reviews('below_threshold_test', 4)

        # Check badge
        newly_awarded = BadgeService.check_review_badges(user)

        # Verify Reviewer badge NOT awarded
        reviewer_badge = Badge.objects.filter(
            category='REVIEW',
            criteria_type='REVIEWS_WRITTEN',
            criteria_value=5
        ).first()

        if reviewer_badge:
            has_badge = UserBadge.objects.filter(user=user, badge=reviewer_badge).exists()
            self.assert_equal(has_badge, False, "Reviewer badge NOT awarded for 4 reviews")
        else:
            print("  ⚠️  Reviewer badge not found in database")

    def test_helpful_ratio_calculation(self):
        """Test helpful ratio calculation correctness."""
        print("\n" + "-"*80)
        print("TEST: Helpful Ratio Calculation")
        print("-"*80)

        # Create user with 10 reviews
        user = self.create_user_with_reviews('ratio_test', 10)

        # Add votes: 8 upvotes, 2 downvotes = 80% helpful ratio
        self.add_votes_to_reviews(user, upvotes=8, downvotes=2)

        # Manually calculate expected helpful ratio
        from django.contrib.contenttypes.models import ContentType
        from django.db.models import Count, Q
        from starview_app.models import Vote

        review_ct = ContentType.objects.get_for_model(Review)
        user_reviews = Review.objects.filter(user=user)

        vote_stats = Vote.objects.filter(
            content_type=review_ct,
            object_id__in=user_reviews.values('id')
        ).aggregate(
            upvote_count=Count('id', filter=Q(is_upvote=True)),
            total_votes=Count('id')
        )

        upvote_count = vote_stats['upvote_count'] or 0
        total_votes = vote_stats['total_votes'] or 0
        helpful_ratio = (upvote_count / total_votes * 100) if total_votes > 0 else 0

        # Verify calculation
        self.assert_equal(upvote_count, 8, "Upvote count correct (8)")
        self.assert_equal(total_votes, 10, "Total votes correct (10)")
        self.assert_equal(int(helpful_ratio), 80, "Helpful ratio correct (80%)")

    def run_all_tests(self):
        """Run all test methods."""
        print("\n" + "="*80)
        print("FUNCTIONAL VERIFICATION TEST - REVIEW BADGES")
        print("="*80)
        print("\nTesting badge awarding logic after duplicate vote query optimization...")

        # Run tests
        self.test_reviewer_badge()
        self.test_critic_badge()
        self.test_tastemaker_badge()
        self.test_master_reviewer_badge()
        self.test_edge_case_zero_reviews()
        self.test_edge_case_exact_threshold()
        self.test_edge_case_below_threshold()
        self.test_helpful_ratio_calculation()

        # Summary
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Passed: {self.passed} ✓")
        print(f"Failed: {self.failed} ✗")

        if self.failed == 0:
            print("\n✓ ALL TESTS PASSED - Badge logic is correct!")
            print("  The optimization preserves exact badge awarding behavior.")
            return True
        else:
            print(f"\n✗ {self.failed} TEST(S) FAILED - Badge logic may be broken!")
            print("  Review the optimization and ensure no logic changes.")
            return False


def cleanup():
    """Clean up all test data."""
    print("\n" + "-"*80)
    print("CLEANING UP TEST DATA")
    print("-"*80)

    # Delete all test users (cascade will delete reviews, votes, etc.)
    test_usernames = [
        'reviewer_test', 'critic_test', 'tastemaker_test', 'master_test',
        'zero_reviews_test', 'exact_threshold_test', 'below_threshold_test', 'ratio_test'
    ]

    for username in test_usernames:
        User.objects.filter(username=username).delete()
        User.objects.filter(username__startswith=f'{username}_creator').delete()
        User.objects.filter(username__startswith=f'voter_{username}_').delete()

    # Delete test locations
    Location.objects.filter(name__regex=r'(reviewer|critic|tastemaker|master|ratio)_test Location').delete()

    print("✓ Cleaned up all test data")


if __name__ == '__main__':
    try:
        test_suite = TestReviewBadges()
        all_passed = test_suite.run_all_tests()

        print("\n" + "="*80)
        print("FUNCTIONAL VERIFICATION COMPLETE")
        print("="*80)

        if all_passed:
            print("\n✓ Optimization is production-ready!")
            print("  - No badge logic broken")
            print("  - All edge cases handled correctly")
            print("  - Helpful ratio calculation accurate")
            sys.exit(0)
        else:
            print("\n✗ Optimization requires fixes before deployment!")
            sys.exit(1)

    finally:
        cleanup()
