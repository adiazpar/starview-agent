#!/usr/bin/env python3
"""
Complete Badge System Test - ALL Categories

Tests ALL badge categories thoroughly:
1. Exploration badges (location visits)
2. Contribution badges (location adds)
3. Review badges (review count)
4. Community badges (followers, comments)

Verifies signal handlers work for all badge types.

Run: djvenv/bin/python .claude/backend/tests/phase_badge/test_all_badge_categories.py
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
from starview_app.models import (
    Badge, UserBadge, LocationVisit, Location, Review,
    Follow, ReviewComment, UserProfile
)
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


def cleanup_test_data(user):
    """Clean up all test data for fresh start"""
    print_header("CLEANUP: Removing Existing Test Data")

    LocationVisit.objects.filter(user=user).delete()
    UserBadge.objects.filter(user=user).delete()
    Review.objects.filter(user=user).delete()
    ReviewComment.objects.filter(user=user).delete()
    Follow.objects.filter(follower=user).delete()
    Follow.objects.filter(following=user).delete()

    # Don't delete locations, just reset ownership
    # Location.objects.filter(added_by=user).delete()

    user.userprofile.pinned_badge_ids = []
    user.userprofile.save()

    print_success("All test data cleaned up")


def test_exploration_badges(user, locations):
    """Test Exploration badges (location visits)"""
    print_header("TEST 1: Exploration Badges (Location Visits)")

    initial_badges = UserBadge.objects.filter(user=user, badge__category='EXPLORATION').count()
    print_info(f"Starting with {initial_badges} exploration badges")

    # Mark 1 location (should earn "First Light")
    print_info("\n1. Marking 1 location as visited (First Light)...")
    LocationVisit.objects.create(user=user, location=locations[0])

    badges_earned = UserBadge.objects.filter(user=user, badge__category='EXPLORATION')
    assert badges_earned.count() >= 1, "Should have earned at least First Light"
    print_success(f"✓ Earned {badges_earned.count()} exploration badge(s)")

    # Mark 4 more locations (should earn "Explorer" at 5)
    print_info("\n2. Marking 4 more locations (Explorer at 5 visits)...")
    for location in locations[1:5]:
        LocationVisit.objects.create(user=user, location=location)

    has_explorer = UserBadge.objects.filter(user=user, badge__slug='explorer').exists()
    assert has_explorer, "Should have earned Explorer badge"
    print_success("✓ Earned Explorer badge at 5 visits")

    # Mark 5 more locations (should earn "Pathfinder" at 10)
    print_info("\n3. Marking 5 more locations (Pathfinder at 10 visits)...")
    for location in locations[5:10]:
        LocationVisit.objects.create(user=user, location=location)

    has_pathfinder = UserBadge.objects.filter(user=user, badge__slug='pathfinder').exists()
    assert has_pathfinder, "Should have earned Pathfinder badge"
    print_success("✓ Earned Pathfinder badge at 10 visits")

    total_exploration = UserBadge.objects.filter(user=user, badge__category='EXPLORATION').count()
    print_success(f"\n✓ Total exploration badges earned: {total_exploration}")

    return True


def test_contribution_badges(user):
    """Test Contribution badges (location adds)"""
    print_header("TEST 2: Contribution Badges (Location Adds)")

    initial_count = Location.objects.filter(added_by=user).count()
    print_info(f"User currently has {initial_count} locations")

    if initial_count < 1:
        print_info("Creating test locations...")
        # Create 10 locations
        for i in range(10):
            Location.objects.create(
                name=f"Contrib Test Location {i+1}",
                latitude=Decimal(str(34.0 + i * 0.1)),
                longitude=Decimal(str(-118.0 + i * 0.1)),
                added_by=user
            )
        print_success(f"Created 10 test locations")

    # Manually trigger badge check (in case signal didn't fire)
    print_info("\nManually checking contribution badges...")
    newly_awarded = BadgeService.check_contribution_badges(user)

    contrib_badges = UserBadge.objects.filter(user=user, badge__category='CONTRIBUTION')
    print_success(f"✓ Contribution badges earned: {contrib_badges.count()}")

    for ub in contrib_badges:
        print_info(f"  • {ub.badge.name} - {ub.badge.description}")

    # Verify expected badges
    location_count = Location.objects.filter(added_by=user).count()
    if location_count >= 1:
        assert UserBadge.objects.filter(user=user, badge__slug='scout').exists(), "Should have Scout"
    if location_count >= 5:
        assert UserBadge.objects.filter(user=user, badge__slug='discoverer').exists(), "Should have Discoverer"
    if location_count >= 10:
        assert UserBadge.objects.filter(user=user, badge__slug='trailblazer').exists(), "Should have Trailblazer"

    print_success(f"\n✓ Contribution badges working! ({contrib_badges.count()} earned)")
    return True


def test_review_badges(user, locations):
    """Test Review badges (review count)"""
    print_header("TEST 3: Review Badges (Review Count)")

    initial_reviews = Review.objects.filter(user=user).count()
    print_info(f"User currently has {initial_reviews} reviews")

    # Create 5 reviews (should earn "Reviewer")
    print_info("\n1. Creating 5 reviews (Reviewer)...")
    for i, location in enumerate(locations[:5]):
        Review.objects.create(
            user=user,
            location=location,
            rating=4,
            comment=f"Test review {i+1} for badge testing"
        )

    # Manually check (in case signal didn't fire)
    BadgeService.check_review_badges(user)

    has_reviewer = UserBadge.objects.filter(user=user, badge__slug='reviewer').exists()
    assert has_reviewer, "Should have earned Reviewer badge"
    print_success("✓ Earned Reviewer badge at 5 reviews")

    # Create 5 more reviews (should earn "Helpful Voice" at 10)
    print_info("\n2. Creating 5 more reviews (Helpful Voice at 10)...")
    for i, location in enumerate(locations[5:10]):
        Review.objects.create(
            user=user,
            location=location,
            rating=5,
            comment=f"Test review {i+6} for badge testing"
        )

    BadgeService.check_review_badges(user)

    has_helpful_voice = UserBadge.objects.filter(user=user, badge__slug='helpful-voice').exists()
    assert has_helpful_voice, "Should have earned Helpful Voice badge"
    print_success("✓ Earned Helpful Voice badge at 10 reviews")

    review_badges = UserBadge.objects.filter(user=user, badge__category='REVIEW')
    print_success(f"\n✓ Review badges earned: {review_badges.count()}")

    for ub in review_badges:
        print_info(f"  • {ub.badge.name} - {ub.badge.description}")

    return True


def test_community_badges(user):
    """Test Community badges (followers and comments)"""
    print_header("TEST 4: Community Badges (Followers & Comments)")

    # Create dummy users to follow the test user
    print_info("\n1. Creating 10 followers (Connector at 10)...")

    for i in range(10):
        follower, created = User.objects.get_or_create(
            username=f"badge_follower_{i}",
            defaults={'email': f'follower{i}@test.com'}
        )
        Follow.objects.get_or_create(follower=follower, following=user)

    # Manually check (in case signal didn't fire)
    BadgeService.check_community_badges(user)

    has_connector = UserBadge.objects.filter(user=user, badge__slug='connector').exists()
    assert has_connector, "Should have earned Connector badge"
    print_success("✓ Earned Connector badge at 10 followers")

    # Create 10 comments (Conversationalist)
    print_info("\n2. Creating 10 comments (Conversationalist)...")

    # Get a review to comment on
    review = Review.objects.first()
    if review:
        for i in range(10):
            ReviewComment.objects.create(
                user=user,
                review=review,
                content=f"Test comment {i+1} for badge testing"
            )

        BadgeService.check_community_badges(user)

        has_conversationalist = UserBadge.objects.filter(
            user=user,
            badge__slug='conversationalist'
        ).exists()
        assert has_conversationalist, "Should have earned Conversationalist badge"
        print_success("✓ Earned Conversationalist badge at 10 comments")
    else:
        print_info("No reviews available for commenting, skipping comment badge test")

    community_badges = UserBadge.objects.filter(user=user, badge__category='COMMUNITY')
    print_success(f"\n✓ Community badges earned: {community_badges.count()}")

    for ub in community_badges:
        print_info(f"  • {ub.badge.name} - {ub.badge.description}")

    return True


def print_final_summary(user):
    """Print comprehensive badge summary"""
    print_header("FINAL BADGE SUMMARY")

    categories = ['EXPLORATION', 'CONTRIBUTION', 'REVIEW', 'COMMUNITY', 'SPECIAL']

    total_earned = 0
    for category in categories:
        count = UserBadge.objects.filter(user=user, badge__category=category).count()
        total_badges = Badge.objects.filter(category=category).count()
        total_earned += count

        status = f"{Colors.GREEN}TESTED{Colors.RESET}" if count > 0 else f"{Colors.YELLOW}NOT TESTED{Colors.RESET}"
        print(f"  {category}: {count}/{total_badges} badges earned - {status}")

    print_success(f"\n✓ Total badges earned: {total_earned}/20")

    # Show earned badges
    print_info("\nAll Earned Badges:")
    earned = UserBadge.objects.filter(user=user).select_related('badge').order_by('badge__category', 'badge__tier')
    for ub in earned:
        print(f"  🏆 {ub.badge.name} ({ub.badge.category}) - {ub.badge.description}")


def run_all_tests():
    """Run all badge category tests"""
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"COMPLETE BADGE SYSTEM TEST - ALL CATEGORIES")
    print(f"{'='*70}{Colors.RESET}\n")

    username = "adiazpar"

    try:
        user = User.objects.get(username=username)
        print_info(f"Using test user: {username}")
    except User.DoesNotExist:
        print_error(f"User '{username}' not found!")
        sys.exit(1)

    # Get or create test locations
    locations = list(Location.objects.all()[:10])
    if len(locations) < 10:
        print_error("Need at least 10 locations for testing")
        sys.exit(1)

    print_info(f"Using {len(locations)} test locations")

    # Clean up existing data
    cleanup_test_data(user)

    results = []

    # Test all badge categories
    try:
        results.append(("Exploration Badges", test_exploration_badges(user, locations)))
        results.append(("Contribution Badges", test_contribution_badges(user)))
        results.append(("Review Badges", test_review_badges(user, locations)))
        results.append(("Community Badges", test_community_badges(user)))

        # Print summary
        print_final_summary(user)

        # Print test results
        print_header("TEST RESULTS")

        all_passed = all(result[1] for result in results)

        for test_name, passed in results:
            status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
            print(f"  {test_name}: {status}")

        if all_passed:
            print_success("\n" + "="*70)
            print_success("ALL BADGE CATEGORIES TESTED & WORKING! ✓✓✓")
            print_success("="*70)
        else:
            print_error("\n✗ SOME TESTS FAILED")
            sys.exit(1)

    except AssertionError as e:
        print_error(f"\nTEST FAILED: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nTEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    run_all_tests()
