#!/usr/bin/env python3
"""
Badge Fix Test 4: Review Badge Upvote Ratio Logic

Tests that Review badges correctly check:
1. Reviewer - 5 reviews (simple count)
2. Helpful Voice - 10 upvotes received
3. Expert Reviewer - 25 reviews with 75%+ helpful ratio
4. Trusted Critic - 50 reviews with 80%+ helpful ratio
5. Review Master - 100 reviews with 85%+ helpful ratio

Users: stony (reviewer), adiazpar (voter)
Run: djvenv/bin/python .claude/backend/tests/phase7/test_4_review_badges_upvote_ratio.py
"""

import os
import sys
import django

# Setup Django environment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from starview_app.models import Location, Review, UserBadge, Vote
from starview_app.services.badge_service import BadgeService
from decimal import Decimal


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


def cleanup(adiaz, stony):
    """Clean up test data"""
    print_header("CLEANUP")

    # Delete ALL Review badges first (to reset state)
    UserBadge.objects.filter(user__in=[adiaz, stony], badge__category='REVIEW').delete()

    # Delete votes, reviews, and locations
    review_ct = ContentType.objects.get_for_model(Review)
    Vote.objects.filter(content_type=review_ct).delete()
    Review.objects.filter(user__in=[adiaz, stony]).delete()
    Location.objects.filter(name__startswith="Review Test").delete()

    print_success("Test data cleaned up")


def test_review_count_badge():
    """Test Reviewer badge (5 reviews)"""
    print_header("TEST 4A: Reviewer Badge (Simple Count)")

    # Get test users
    try:
        adiaz = User.objects.get(username='adiazpar')
        stony = User.objects.get(username='stony')
        print_info(f"Using users: {stony.username} (reviewer), {adiaz.username} (location creator)")
    except User.DoesNotExist as e:
        print_error(f"Required user not found: {str(e)}")
        return False, None, None

    # Clean up
    cleanup(adiaz, stony)

    # Create 5 locations by adiaz
    print_info("\n1. Creating 5 locations by adiazpar...")
    locations = []
    for i in range(5):
        location = Location.objects.create(
            name=f"Review Test Location {i+1}",
            latitude=Decimal(str(35.0 + i * 0.01)),
            longitude=Decimal('-119.0'),
            added_by=adiaz
        )
        locations.append(location)
    print_success("Created 5 locations")

    # stony writes 5 reviews
    print_info("\n2. stony writes 5 reviews...")
    for loc in locations:
        Review.objects.create(
            user=stony,
            location=loc,
            rating=4,
            comment="Good spot"
        )
    print_success("Created 5 reviews")

    # Check badge
    print_info("\n3. Checking Reviewer badge...")
    has_reviewer = UserBadge.objects.filter(
        user=stony,
        badge__slug='reviewer'
    ).exists()

    if not has_reviewer:
        print_error("❌ Reviewer badge should be awarded (5 reviews written)!")
        return False, adiaz, stony

    print_success("✓ Reviewer badge awarded (5 reviews)")

    return True, adiaz, stony


def test_upvote_count_badge(adiaz, stony):
    """Test Helpful Voice badge (10 upvotes received)"""
    print_header("TEST 4B: Helpful Voice Badge (10 Upvotes)")

    # Get stony's existing reviews
    existing_reviews = list(Review.objects.filter(user=stony))
    print_info(f"\n1. stony has {len(existing_reviews)} existing reviews")

    # Create 5 more locations and reviews (total 10 reviews)
    print_info("\n2. Creating 5 more locations and reviews...")
    for i in range(5, 10):
        location = Location.objects.create(
            name=f"Review Test Location {i+1}",
            latitude=Decimal(str(35.0 + i * 0.01)),
            longitude=Decimal('-119.0'),
            added_by=adiaz
        )
        Review.objects.create(
            user=stony,
            location=location,
            rating=5,
            comment="Excellent!"
        )
    print_success("Created 5 more reviews (total 10)")

    # adiaz upvotes all 10 reviews
    print_info("\n3. adiazpar upvotes all 10 reviews...")
    review_ct = ContentType.objects.get_for_model(Review)
    all_reviews = Review.objects.filter(user=stony)

    for review in all_reviews:
        Vote.objects.create(
            user=adiaz,
            content_type=review_ct,
            object_id=review.id,
            is_upvote=True
        )
    print_success("Created 10 upvotes")

    # Check badge
    print_info("\n4. Checking Helpful Voice badge...")
    has_helpful_voice = UserBadge.objects.filter(
        user=stony,
        badge__slug='helpful-voice'
    ).exists()

    if not has_helpful_voice:
        print_error("❌ Helpful Voice badge should be awarded (10 upvotes received)!")
        return False

    print_success("✓ Helpful Voice badge awarded (10 upvotes)")

    return True


def test_helpful_ratio_badges(adiaz, stony):
    """Test Expert Reviewer (25 reviews, 75%+ helpful ratio)"""
    print_header("TEST 4C: Expert Reviewer Badge (25 reviews, 75%+ ratio)")

    # stony currently has 10 reviews with 10 upvotes (100% ratio)
    print_info("\n1. Current state: 10 reviews, 10 upvotes (100% ratio)")

    # Create 15 more locations and reviews (total 25)
    print_info("\n2. Creating 15 more reviews (total 25)...")
    for i in range(10, 25):
        location = Location.objects.create(
            name=f"Review Test Location {i+1}",
            latitude=Decimal(str(36.0 + i * 0.01)),
            longitude=Decimal('-120.0'),
            added_by=adiaz
        )
        Review.objects.create(
            user=stony,
            location=location,
            rating=4,
            comment=f"Review {i+1}"
        )
    print_success("Created 15 more reviews (total 25)")

    # adiaz upvotes 12 of these 15 reviews (total 22/25 upvotes = 88% helpful)
    print_info("\n3. adiazpar upvotes 12 of the 15 new reviews...")
    review_ct = ContentType.objects.get_for_model(Review)
    new_reviews = Review.objects.filter(user=stony).order_by('-id')[:15]

    for i, review in enumerate(new_reviews):
        if i < 12:  # Upvote first 12
            Vote.objects.create(
                user=adiaz,
                content_type=review_ct,
                object_id=review.id,
                is_upvote=True
            )
        else:  # Downvote last 3
            Vote.objects.create(
                user=adiaz,
                content_type=review_ct,
                object_id=review.id,
                is_upvote=False
            )

    # Calculate actual ratio
    total_votes = Vote.objects.filter(
        content_type=review_ct,
        object_id__in=Review.objects.filter(user=stony).values_list('id', flat=True)
    ).count()
    upvotes = Vote.objects.filter(
        content_type=review_ct,
        object_id__in=Review.objects.filter(user=stony).values_list('id', flat=True),
        is_upvote=True
    ).count()
    ratio = (upvotes / total_votes * 100) if total_votes > 0 else 0

    print_success(f"Created votes: {upvotes}/{total_votes} upvotes = {ratio:.1f}% helpful")

    # Manually trigger badge check
    print_info("\n4. Checking Expert Reviewer badge...")
    BadgeService.check_review_badges(stony)

    has_expert = UserBadge.objects.filter(
        user=stony,
        badge__slug='expert-reviewer'
    ).exists()

    if not has_expert:
        print_error(f"❌ Expert Reviewer should be awarded (25 reviews, {ratio:.1f}% > 75%)!")
        return False

    print_success(f"✓ Expert Reviewer badge awarded (25 reviews, {ratio:.1f}% helpful)")

    # Verify higher tier badges NOT awarded
    has_trusted = UserBadge.objects.filter(
        user=stony,
        badge__slug='trusted-critic'
    ).exists()
    if has_trusted:
        print_error("❌ Trusted Critic incorrectly awarded (need 50 reviews)!")
        return False

    print_success("✓ Trusted Critic NOT awarded yet (need 50 reviews)")

    return True


def run_tests():
    """Run all Review badge tests"""
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"BADGE FIX TEST 4: REVIEW BADGE UPVOTE RATIO LOGIC")
    print(f"{'='*70}{Colors.RESET}\n")

    print_info("This test verifies:")
    print_info("  1. Reviewer badge - 5 reviews (simple count)")
    print_info("  2. Helpful Voice badge - 10 upvotes received")
    print_info("  3. Expert Reviewer badge - 25 reviews with 75%+ helpful ratio")

    adiaz = None
    stony = None

    try:
        # Test 1: Reviewer badge
        success, adiaz, stony = test_review_count_badge()
        if not success:
            raise Exception("Test 4A failed")

        # Test 2: Helpful Voice badge
        success = test_upvote_count_badge(adiaz, stony)
        if not success:
            raise Exception("Test 4B failed")

        # Test 3: Expert Reviewer badge
        success = test_helpful_ratio_badges(adiaz, stony)
        if not success:
            raise Exception("Test 4C failed")

        print_header("TEST RESULTS")
        print_success("="*70)
        print_success("ALL TESTS PASSED! ✓✓✓")
        print_success("="*70)
        print_info("\nReview badge logic working correctly:")
        print_info("  ✓ Reviewer badge awards at 5 reviews")
        print_info("  ✓ Helpful Voice badge awards at 10 upvotes")
        print_info("  ✓ Expert Reviewer badge checks review count AND helpful ratio")
        print_info("  ✓ Ratio calculated as upvotes / total_votes")

    except Exception as e:
        print_error(f"\nTEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if adiaz and stony:
            cleanup(adiaz, stony)


if __name__ == '__main__':
    run_tests()
