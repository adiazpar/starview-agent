#!/usr/bin/env python3
"""
Badge Fix Test 1: Self-Review Prevention

Tests that users CANNOT review their own locations.
This is critical for Contribution and Quality badge integrity.

Users: adiazpar, stony
Run: djvenv/bin/python .claude/backend/tests/phase7/test_1_self_review_prevention.py
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
from django.core.exceptions import ValidationError
from starview_app.models import Location, Review
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


def cleanup():
    """Clean up test data"""
    print_header("CLEANUP")

    # Delete test locations
    Location.objects.filter(name__startswith="Self Review Test").delete()

    print_success("Test data cleaned up")


def test_self_review_prevention():
    """Test that users cannot review their own locations"""
    print_header("TEST 1: Self-Review Prevention")

    # Get test users
    try:
        adiaz = User.objects.get(username='adiazpar')
        stony = User.objects.get(username='stony')
        print_info(f"Using users: {adiaz.username}, {stony.username}")
    except User.DoesNotExist as e:
        print_error(f"Required user not found: {str(e)}")
        return False

    # Create location by adiaz
    print_info("\n1. Creating location by adiazpar...")
    location = Location.objects.create(
        name="Self Review Test Location 1",
        latitude=Decimal('35.0'),
        longitude=Decimal('-119.0'),
        added_by=adiaz
    )
    print_success(f"Location created: {location.name} (added by {location.added_by.username})")

    # Test 1: adiaz tries to review own location (should FAIL)
    print_info("\n2. Testing: adiazpar tries to review own location...")
    try:
        review = Review.objects.create(
            user=adiaz,
            location=location,
            rating=5,
            comment="Trying to review my own location"
        )
        print_error("❌ CRITICAL FAILURE: Self-review was allowed!")
        print_error(f"Review ID: {review.id}")
        review.delete()  # Clean up
        return False
    except ValidationError as e:
        print_success("✓ Self-review correctly prevented!")
        print_info(f"  Error message: {str(e)}")
    except Exception as e:
        print_error(f"❌ Unexpected error type: {type(e).__name__}")
        print_error(f"  Message: {str(e)}")
        return False

    # Test 2: stony reviews adiaz's location (should SUCCEED)
    print_info("\n3. Testing: stony reviews adiazpar's location...")
    try:
        review = Review.objects.create(
            user=stony,
            location=location,
            rating=4,
            comment="This is a legitimate review by another user"
        )
        print_success("✓ Normal review by other user allowed!")
        print_info(f"  Review ID: {review.id}")
        print_info(f"  Reviewer: {review.user.username}")
        print_info(f"  Location owner: {location.added_by.username}")
    except Exception as e:
        print_error(f"❌ Normal review incorrectly blocked!")
        print_error(f"  Error: {str(e)}")
        return False

    # Test 3: Create location by stony, adiaz reviews it (should SUCCEED)
    print_info("\n4. Testing: adiazpar reviews stony's location...")
    location2 = Location.objects.create(
        name="Self Review Test Location 2",
        latitude=Decimal('36.0'),
        longitude=Decimal('-120.0'),
        added_by=stony
    )
    print_info(f"Created location by {location2.added_by.username}")

    try:
        review2 = Review.objects.create(
            user=adiaz,
            location=location2,
            rating=5,
            comment="Reviewing stony's location"
        )
        print_success("✓ Cross-user review allowed!")
        print_info(f"  Review ID: {review2.id}")
    except Exception as e:
        print_error(f"❌ Cross-user review incorrectly blocked!")
        print_error(f"  Error: {str(e)}")
        return False

    # Test 4: stony tries to review own location (should FAIL)
    print_info("\n5. Testing: stony tries to review own location...")
    try:
        review3 = Review.objects.create(
            user=stony,
            location=location2,
            rating=5,
            comment="Trying to review my own location"
        )
        print_error("❌ CRITICAL FAILURE: Self-review was allowed!")
        print_error(f"Review ID: {review3.id}")
        review3.delete()
        return False
    except ValidationError as e:
        print_success("✓ Self-review correctly prevented!")
        print_info(f"  Error message: {str(e)}")
    except Exception as e:
        print_error(f"❌ Unexpected error type: {type(e).__name__}")
        print_error(f"  Message: {str(e)}")
        return False

    print_success("\n✓✓✓ ALL SELF-REVIEW PREVENTION TESTS PASSED!")
    return True


def run_tests():
    """Run all self-review prevention tests"""
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"BADGE FIX TEST 1: SELF-REVIEW PREVENTION")
    print(f"{'='*70}{Colors.RESET}\n")

    print_info("This test verifies:")
    print_info("  1. Users CANNOT review their own locations")
    print_info("  2. Users CAN review other users' locations")
    print_info("  3. Validation error is raised with clear message")

    try:
        success = test_self_review_prevention()

        print_header("TEST RESULTS")

        if success:
            print_success("="*70)
            print_success("ALL TESTS PASSED! ✓✓✓")
            print_success("="*70)
            print_info("\nSelf-review prevention is working correctly.")
            print_info("Users can only review locations added by OTHER users.")
            print_info("\nThis ensures:")
            print_info("  ✓ Contribution badges are earned fairly")
            print_info("  ✓ Quality badges require genuine external validation")
            print_info("  ✓ Review integrity is maintained")
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
        cleanup()


if __name__ == '__main__':
    run_tests()
