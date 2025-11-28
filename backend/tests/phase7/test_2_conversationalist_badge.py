#!/usr/bin/env python3
"""
Badge Fix Test 2: Conversationalist Badge Logic

Tests that Conversationalist badge only counts comments on OTHER users' reviews,
not comments on own reviews.

Users: adiazpar, stony
Run: djvenv/bin/python .claude/backend/tests/phase7/test_2_conversationalist_badge.py
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
from starview_app.models import Location, Review, ReviewComment, UserBadge
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

    # Delete test data
    ReviewComment.objects.filter(user__in=[adiaz, stony]).delete()
    Review.objects.filter(user__in=[adiaz, stony]).delete()
    Location.objects.filter(name__startswith="Comment Test").delete()
    UserBadge.objects.filter(user__in=[adiaz, stony], badge__category='COMMUNITY').delete()

    print_success("Test data cleaned up")


def test_comment_counting_logic():
    """Test that comments are counted correctly for Conversationalist badge"""
    print_header("TEST 2: Conversationalist Badge - Comment Counting")

    # Get test users
    try:
        adiaz = User.objects.get(username='adiazpar')
        stony = User.objects.get(username='stony')
        print_info(f"Using users: {adiaz.username}, {stony.username}")
    except User.DoesNotExist as e:
        print_error(f"Required user not found: {str(e)}")
        return False, None, None

    # Clean up existing data
    cleanup(adiaz, stony)

    # Create locations (need separate locations for each review due to unique constraint)
    print_info("\n1. Creating test locations...")
    adiaz_locations = []
    stony_locations = []

    # Create 10 locations by each user
    for i in range(10):
        adiaz_loc = Location.objects.create(
            name=f"Comment Test adiaz Location {i+1}",
            latitude=Decimal(str(35.0 + i * 0.01)),
            longitude=Decimal('-119.0'),
            added_by=adiaz
        )
        adiaz_locations.append(adiaz_loc)

        stony_loc = Location.objects.create(
            name=f"Comment Test stony Location {i+1}",
            latitude=Decimal(str(36.0 + i * 0.01)),
            longitude=Decimal('-120.0'),
            added_by=stony
        )
        stony_locations.append(stony_loc)

    print_success(f"Created 20 locations (10 per user)")

    # adiaz writes 5 reviews on stony's locations
    print_info("\n2. adiazpar writes 5 reviews on stony's locations...")
    adiaz_reviews = []
    for i in range(5):
        review = Review.objects.create(
            user=adiaz,
            location=stony_locations[i],
            rating=4,
            comment=f"adiaz review {i+1}"
        )
        adiaz_reviews.append(review)
    print_success(f"Created 5 reviews by adiazpar")

    # stony writes 5 reviews on adiaz's locations
    print_info("\n3. stony writes 5 reviews on adiazpar's locations...")
    stony_reviews = []
    for i in range(5):
        review = Review.objects.create(
            user=stony,
            location=adiaz_locations[i],
            rating=5,
            comment=f"stony review {i+1}"
        )
        stony_reviews.append(review)
    print_success(f"Created 5 reviews by stony")

    # stony comments on adiaz's 5 reviews (should COUNT)
    print_info("\n4. stony comments on adiazpar's 5 reviews (should COUNT)...")
    for review in adiaz_reviews:
        ReviewComment.objects.create(
            user=stony,
            review=review,
            content=f"stony commenting on adiaz's review"
        )
    print_success("Created 5 comments on OTHER user's reviews")

    # stony comments on own 5 reviews (should NOT COUNT)
    print_info("\n5. stony comments on own 5 reviews (should NOT COUNT)...")
    for review in stony_reviews:
        ReviewComment.objects.create(
            user=stony,
            review=review,
            content=f"stony commenting on own review"
        )
    print_success("Created 5 comments on OWN reviews")

    # Verify comment counts
    print_info("\n6. Verifying comment counts...")
    total_comments = ReviewComment.objects.filter(user=stony).count()
    print_info(f"  Total comments by stony: {total_comments}")
    assert total_comments == 10, f"Expected 10 total comments, got {total_comments}"

    # Count comments excluding own reviews
    valid_comments = ReviewComment.objects.filter(user=stony).exclude(
        review__user=stony
    ).count()
    print_info(f"  Comments on OTHER user's reviews: {valid_comments}")
    assert valid_comments == 5, f"Expected 5 valid comments, got {valid_comments}"

    # Manually trigger badge check
    print_info("\n7. Manually checking community badges...")
    newly_awarded = BadgeService.check_community_badges(stony)

    # Check if badge was awarded
    has_conversationalist = UserBadge.objects.filter(
        user=stony,
        badge__slug='conversationalist'
    ).exists()

    print_info(f"  Badge check result: {'Badge awarded' if has_conversationalist else 'No badge (need 10 valid comments)'}")

    # Verify badge NOT awarded yet (only 5 valid comments)
    if has_conversationalist:
        print_error("❌ Badge incorrectly awarded with only 5 valid comments!")
        return False, adiaz, stony

    print_success("✓ Badge correctly NOT awarded (only 5/10 valid comments)")

    # Now add 5 more comments on adiaz's reviews to reach 10
    print_info("\n8. Adding 5 more comments on OTHER user's reviews...")

    # Create 5 more reviews by adiaz for stony to comment on
    for i in range(5, 10):
        review = Review.objects.create(
            user=adiaz,
            location=stony_locations[i],
            rating=4,
            comment=f"adiaz review {i+1}"
        )
        ReviewComment.objects.create(
            user=stony,
            review=review,
            content=f"stony commenting on adiaz's review {i+1}"
        )

    # Verify counts again
    total_comments_now = ReviewComment.objects.filter(user=stony).count()
    valid_comments_now = ReviewComment.objects.filter(user=stony).exclude(
        review__user=stony
    ).count()

    print_info(f"  Total comments: {total_comments_now}")
    print_info(f"  Valid comments (on other's reviews): {valid_comments_now}")

    assert total_comments_now == 15, f"Expected 15 total comments, got {total_comments_now}"
    assert valid_comments_now == 10, f"Expected 10 valid comments, got {valid_comments_now}"

    # Check badge again
    print_info("\n9. Checking badge again with 10 valid comments...")
    newly_awarded = BadgeService.check_community_badges(stony)

    has_conversationalist = UserBadge.objects.filter(
        user=stony,
        badge__slug='conversationalist'
    ).exists()

    if not has_conversationalist:
        print_error("❌ Badge should be awarded with 10 valid comments!")
        return False, adiaz, stony

    print_success("✓ Badge correctly awarded with 10 valid comments!")

    # Final verification
    print_info("\n10. Final verification...")
    earned_badges = UserBadge.objects.filter(user=stony, badge__category='COMMUNITY')
    print_success(f"Community badges earned: {earned_badges.count()}")
    for ub in earned_badges:
        print_info(f"  🏆 {ub.badge.name}")

    print_success("\n✓✓✓ ALL CONVERSATIONALIST BADGE TESTS PASSED!")
    return True, adiaz, stony


def run_tests():
    """Run all Conversationalist badge tests"""
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"BADGE FIX TEST 2: CONVERSATIONALIST BADGE")
    print(f"{'='*70}{Colors.RESET}\n")

    print_info("This test verifies:")
    print_info("  1. Comments on OTHER users' reviews COUNT toward badge")
    print_info("  2. Comments on OWN reviews do NOT count")
    print_info("  3. Badge awarded correctly at 10 valid comments")

    try:
        success, adiaz, stony = test_comment_counting_logic()

        print_header("TEST RESULTS")

        if success:
            print_success("="*70)
            print_success("ALL TESTS PASSED! ✓✓✓")
            print_success("="*70)
            print_info("\nConversationalist badge logic working correctly:")
            print_info("  ✓ Only counts comments on OTHER users' reviews")
            print_info("  ✓ Excludes self-comments (on own reviews)")
            print_info("  ✓ Badge awarded at correct threshold (10 comments)")
        else:
            print_error("="*70)
            print_error("TESTS FAILED! ✗✗✗")
            print_error("="*70)
            sys.exit(1)

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
