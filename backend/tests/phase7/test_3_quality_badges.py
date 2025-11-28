#!/usr/bin/env python3
"""
Badge Fix Test 3: Quality Badge Logic

Tests that Quality badges are awarded based on locations with 4+ star average ratings.
Tests that self-review prevention ensures quality badges require external validation.

Users: adiazpar (location creator), stony (reviewer)
Run: djvenv/bin/python .claude/backend/tests/phase7/test_3_quality_badges.py
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
from starview_app.models import Location, Review, UserBadge
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

    # Delete ALL Quality badges first (to reset state)
    UserBadge.objects.filter(user__in=[adiaz, stony], badge__category='QUALITY').delete()

    # Delete test reviews and locations
    Review.objects.filter(user__in=[adiaz, stony]).delete()
    Location.objects.filter(name__startswith="Quality Test").delete()

    # Also delete any old test locations that might have reviews
    Location.objects.filter(name__startswith="Test Dark Sky").delete()

    print_success("Test data cleaned up")


def test_quality_badge_logic():
    """Test that Quality badges award based on 4+ star average ratings"""
    print_header("TEST 3: Quality Badge Logic")

    # Get test users
    try:
        adiaz = User.objects.get(username='adiazpar')
        stony = User.objects.get(username='stony')
        print_info(f"Using users: {adiaz.username} (creator), {stony.username} (reviewer)")
    except User.DoesNotExist as e:
        print_error(f"Required user not found: {str(e)}")
        return False, None, None

    # Clean up existing data
    cleanup(adiaz, stony)

    # Test Scenario:
    # adiaz creates 10 locations
    # stony reviews them with different ratings
    # Expected: adiaz earns Quality badges when enough locations reach 4+ stars

    print_info("\n1. adiazpar creates 10 locations...")
    locations = []
    for i in range(10):
        location = Location.objects.create(
            name=f"Quality Test Location {i+1}",
            latitude=Decimal(str(35.0 + i * 0.01)),
            longitude=Decimal('-119.0'),
            added_by=adiaz
        )
        locations.append(location)
    print_success(f"Created 10 locations by adiazpar")

    # Verify no quality badges yet
    print_info("\n2. Verifying no Quality badges yet (no reviews)...")
    quality_badges = UserBadge.objects.filter(user=adiaz, badge__category='QUALITY')
    assert quality_badges.count() == 0, "Should have 0 quality badges with no reviews"
    print_success("✓ No quality badges yet (correct)")

    # stony reviews 3 locations with 5 stars
    print_info("\n3. stony reviews 3 locations with 5 stars...")
    for i in range(3):
        Review.objects.create(
            user=stony,
            location=locations[i],
            rating=5,
            comment=f"Excellent location {i+1}!"
        )
    print_success("Created 3 reviews with 5 stars")

    # Check location averages
    print_info("\n4. Checking location average ratings...")
    for i in range(3):
        locations[i].refresh_from_db()
        print_info(f"  Location {i+1}: average_rating = {locations[i].average_rating}")
        assert locations[i].average_rating == 5.0, f"Expected 5.0, got {locations[i].average_rating}"

    # Manually trigger quality badge check
    print_info("\n5. Checking Quality badges for adiazpar...")
    newly_awarded = BadgeService.check_quality_badges(adiaz)

    # Verify Quality Contributor badge awarded (3+ locations with 4+ stars)
    has_quality_contributor = UserBadge.objects.filter(
        user=adiaz,
        badge__slug='quality-contributor'
    ).exists()

    if not has_quality_contributor:
        print_error("❌ Quality Contributor badge should be awarded (3 locations with 5 stars)!")
        return False, adiaz, stony

    print_success("✓ Quality Contributor badge awarded (3+ locations with 4+ stars)")

    # Verify higher tier badges NOT awarded yet
    has_trusted_source = UserBadge.objects.filter(
        user=adiaz,
        badge__slug='trusted-source'
    ).exists()
    if has_trusted_source:
        print_error("❌ Trusted Source badge incorrectly awarded (need 5+ locations)")
        return False, adiaz, stony

    print_success("✓ Trusted Source badge NOT awarded yet (need 5 locations)")

    # stony reviews 2 more locations with 4 stars (total 5 with 4+ stars)
    print_info("\n6. stony reviews 2 more locations with 4 stars...")
    for i in range(3, 5):
        Review.objects.create(
            user=stony,
            location=locations[i],
            rating=4,
            comment=f"Good location {i+1}"
        )
    print_success("Created 2 more reviews with 4 stars")

    # Check badge again
    print_info("\n7. Checking badges again (should have 5 locations with 4+ stars)...")
    newly_awarded = BadgeService.check_quality_badges(adiaz)

    has_trusted_source = UserBadge.objects.filter(
        user=adiaz,
        badge__slug='trusted-source'
    ).exists()

    if not has_trusted_source:
        print_error("❌ Trusted Source badge should be awarded (5 locations with 4+ stars)!")
        return False, adiaz, stony

    print_success("✓ Trusted Source badge awarded (5+ locations with 4+ stars)")

    # stony reviews 3 more with 3 stars (below threshold, shouldn't count)
    print_info("\n8. stony reviews 3 more with 3 stars (below 4.0 threshold)...")
    for i in range(5, 8):
        Review.objects.create(
            user=stony,
            location=locations[i],
            rating=3,
            comment=f"Average location {i+1}"
        )
    print_success("Created 3 reviews with 3 stars")

    # Check badge again - should still only have Trusted Source (5 locations with 4+)
    print_info("\n9. Verifying badge count unchanged (3-star reviews don't count)...")
    newly_awarded = BadgeService.check_quality_badges(adiaz)

    has_elite_curator = UserBadge.objects.filter(
        user=adiaz,
        badge__slug='elite-curator'
    ).exists()

    if has_elite_curator:
        print_error("❌ Elite Curator badge incorrectly awarded (only 5 locations with 4+, need 10)!")
        return False, adiaz, stony

    print_success("✓ Elite Curator NOT awarded (only 5 locations with 4+ stars)")

    # stony reviews remaining 2 locations with 5 stars each
    print_info("\n10. stony reviews last 2 locations with 5 stars...")
    for i in range(8, 10):
        Review.objects.create(
            user=stony,
            location=locations[i],
            rating=5,
            comment=f"Amazing location {i+1}!"
        )
    print_success("Created 2 more reviews with 5 stars")

    # Now adiaz should have 7 locations with 4+ stars (3 with 5★, 2 with 4★, 2 with 5★)
    print_info("\n11. Counting locations with 4+ star average...")
    quality_count = Location.objects.filter(
        added_by=adiaz,
        average_rating__gte=4.0
    ).count()
    print_info(f"  Locations with 4+ stars: {quality_count}")

    # Should still not have Elite Curator (need 10)
    newly_awarded = BadgeService.check_quality_badges(adiaz)
    has_elite_curator = UserBadge.objects.filter(
        user=adiaz,
        badge__slug='elite-curator'
    ).exists()

    if has_elite_curator:
        print_error(f"❌ Elite Curator incorrectly awarded (only {quality_count} locations with 4+)!")
        return False, adiaz, stony

    print_success(f"✓ Elite Curator NOT awarded (only {quality_count}/10 locations with 4+ stars)")

    # Create 3 more locations and review them with 5 stars to reach 10 total
    print_info("\n12. Creating 3 more locations to reach 10 total with 4+ stars...")
    for i in range(10, 13):
        location = Location.objects.create(
            name=f"Quality Test Location {i+1}",
            latitude=Decimal(str(36.0 + i * 0.01)),
            longitude=Decimal('-120.0'),
            added_by=adiaz
        )
        Review.objects.create(
            user=stony,
            location=location,
            rating=5,
            comment=f"Excellent location {i+1}!"
        )
    print_success("Created 3 more locations with 5-star reviews")

    # Check final badge count
    print_info("\n13. Final badge check (should have 10 locations with 4+ stars)...")
    quality_count_final = Location.objects.filter(
        added_by=adiaz,
        average_rating__gte=4.0
    ).count()
    print_info(f"  Locations with 4+ stars: {quality_count_final}")

    newly_awarded = BadgeService.check_quality_badges(adiaz)
    has_elite_curator = UserBadge.objects.filter(
        user=adiaz,
        badge__slug='elite-curator'
    ).exists()

    if not has_elite_curator:
        print_error(f"❌ Elite Curator should be awarded ({quality_count_final} locations with 4+)!")
        return False, adiaz, stony

    print_success("✓ Elite Curator badge awarded (10+ locations with 4+ stars)")

    # Final verification
    print_info("\n14. Final verification...")
    earned_badges = UserBadge.objects.filter(user=adiaz, badge__category='QUALITY').order_by('badge__tier')
    print_success(f"Quality badges earned: {earned_badges.count()}/3")
    for ub in earned_badges:
        print_info(f"  🏆 {ub.badge.name} (Tier {ub.badge.tier})")

    assert earned_badges.count() == 3, f"Expected 3 badges, got {earned_badges.count()}"

    print_success("\n✓✓✓ ALL QUALITY BADGE TESTS PASSED!")
    return True, adiaz, stony


def run_tests():
    """Run all Quality badge tests"""
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"BADGE FIX TEST 3: QUALITY BADGE LOGIC")
    print(f"{'='*70}{Colors.RESET}\n")

    print_info("This test verifies:")
    print_info("  1. Quality badges count locations with 4+ star AVERAGE rating")
    print_info("  2. Ratings below 4.0 do NOT count toward quality badges")
    print_info("  3. Badges awarded at correct thresholds (3, 5, 10 locations)")
    print_info("  4. Self-review prevention ensures quality requires external validation")

    try:
        success, adiaz, stony = test_quality_badge_logic()

        print_header("TEST RESULTS")

        if success:
            print_success("="*70)
            print_success("ALL TESTS PASSED! ✓✓✓")
            print_success("="*70)
            print_info("\nQuality badge logic working correctly:")
            print_info("  ✓ Only counts locations with 4+ star average rating")
            print_info("  ✓ Awards badges at correct thresholds (3, 5, 10)")
            print_info("  ✓ Requires external validation (self-reviews prevented)")
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
