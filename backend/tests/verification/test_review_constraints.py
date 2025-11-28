#!/usr/bin/env python3
"""
Test script to verify review constraints:
1. One review per user per location (unique_together constraint)
2. Maximum 5 photos per review (model validation + view validation)

Run with: djvenv/bin/python .claude/backend/tests/verification/test_review_constraints.py
"""

import os
import sys
import django

# Django setup:
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from starview_app.models import Location, Review, ReviewPhoto
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile


def create_test_image():
    """Creates a simple test image in memory."""
    img = Image.new('RGB', (100, 100), color='red')
    img_io = BytesIO()
    img.save(img_io, format='JPEG', quality=85)
    img_io.seek(0)
    return InMemoryUploadedFile(
        img_io, None, 'test.jpg', 'image/jpeg', img_io.tell(), None
    )


def test_one_review_per_user_per_location():
    """Test that unique_together constraint prevents duplicate reviews."""
    print("\n" + "="*70)
    print("TEST 1: One Review Per User Per Location")
    print("="*70)

    # Create test users (need 2: location creator and reviewer)
    user, _ = User.objects.get_or_create(username='test_review_user', defaults={'email': 'test@review.com'})
    creator, _ = User.objects.get_or_create(username='test_location_creator', defaults={'email': 'creator@review.com'})

    location, _ = Location.objects.get_or_create(
        name='Test Review Location',
        added_by=creator,  # Part of lookup to ensure consistent creator
        defaults={
            'latitude': 34.0,
            'longitude': -118.0
        }
    )

    # Delete any existing reviews for this user/location
    Review.objects.filter(user=user, location=location).delete()

    print(f"\n✓ Created test user: {user.username}")
    print(f"✓ Created test location: {location.name} (by {location.added_by.username})")

    # Test 1: Create first review (should succeed)
    try:
        review1 = Review.objects.create(
            user=user,
            location=location,
            rating=5,
            comment="Great location!"
        )
        print(f"\n✓ First review created successfully (ID: {review1.id})")
    except Exception as e:
        print(f"\n✗ FAILED: First review creation failed: {e}")
        return False

    # Test 2: Try to create duplicate review (should fail)
    try:
        review2 = Review.objects.create(
            user=user,
            location=location,
            rating=3,
            comment="Changed my mind"
        )
        print(f"\n✗ FAILED: Duplicate review was created (ID: {review2.id})")
        print("   Expected ValidationError or IntegrityError due to unique_together constraint")
        review2.delete()  # Cleanup
        return False
    except (IntegrityError, ValidationError) as e:
        print(f"\n✓ Duplicate review blocked by unique_together constraint")
        print(f"   Error: {str(e)[:100]}...")

    # Cleanup
    try:
        review1.delete()
    except Exception as e:
        print(f"\nWarning: Cleanup error (non-critical): {e}")
    print(f"\n✓ Test passed: One review per user per location enforced")
    return True


def test_max_five_photos_per_review():
    """Test that ReviewPhoto model prevents more than 5 photos per review."""
    print("\n" + "="*70)
    print("TEST 2: Maximum 5 Photos Per Review")
    print("="*70)

    # Create test user and location
    user, _ = User.objects.get_or_create(username='test_photo_user', defaults={'email': 'test@photo.com'})
    user2, _ = User.objects.get_or_create(username='test_photo_user2', defaults={'email': 'test2@photo.com'})
    location, _ = Location.objects.get_or_create(
        name='Test Photo Location',
        defaults={
            'added_by': user2,  # Different user to avoid self-review
            'latitude': 35.0,
            'longitude': -119.0
        }
    )

    # Delete any existing reviews for this user/location
    Review.objects.filter(user=user, location=location).delete()

    # Create test review
    review = Review.objects.create(
        user=user,
        location=location,
        rating=4,
        comment="Testing photo limits"
    )
    print(f"\n✓ Created test review (ID: {review.id})")

    # Test 1: Upload 5 photos (should succeed)
    photos_created = []
    for i in range(5):
        try:
            photo = ReviewPhoto.objects.create(
                review=review,
                image=create_test_image(),
                order=i
            )
            photos_created.append(photo)
            print(f"✓ Photo {i+1}/5 uploaded successfully (ID: {photo.id})")
        except Exception as e:
            print(f"✗ FAILED: Photo {i+1}/5 upload failed: {e}")
            review.delete()
            return False

    # Verify 5 photos exist
    photo_count = review.photos.count()
    print(f"\n✓ Review has {photo_count} photos (maximum reached)")

    # Test 2: Try to upload 6th photo (should fail)
    try:
        photo6 = ReviewPhoto.objects.create(
            review=review,
            image=create_test_image(),
            order=5
        )
        print(f"\n✗ FAILED: 6th photo was created (ID: {photo6.id})")
        print("   Expected ValidationError due to 5 photo limit")
        photo6.delete()
        review.delete()
        return False
    except ValidationError as e:
        print(f"\n✓ 6th photo blocked by model validation")
        print(f"   Error: {str(e)}")

    # Cleanup
    try:
        review.delete()  # CASCADE will delete all photos
    except Exception as e:
        print(f"\nWarning: Cleanup error (non-critical): {e}")
    print(f"\n✓ Test passed: Maximum 5 photos per review enforced")
    return True


def test_self_review_prevention():
    """Test that users cannot review their own locations."""
    print("\n" + "="*70)
    print("TEST 3: Self-Review Prevention")
    print("="*70)

    # Create test user and their own location
    user, _ = User.objects.get_or_create(username='test_self_review', defaults={'email': 'test@selfreview.com'})
    location, _ = Location.objects.get_or_create(
        name='User Own Location',
        defaults={
            'added_by': user,  # Same user as reviewer
            'latitude': 36.0,
            'longitude': -120.0
        }
    )

    # Delete any existing reviews for this user/location
    Review.objects.filter(user=user, location=location).delete()

    print(f"\n✓ Created test user: {user.username}")
    print(f"✓ Created location owned by {location.added_by.username}")

    # Test: Try to create self-review (should fail)
    try:
        review = Review(
            user=user,
            location=location,
            rating=5,
            comment="Reviewing my own location"
        )
        review.save()  # This calls full_clean() which should raise ValidationError
        print(f"\n✗ FAILED: Self-review was created (ID: {review.id})")
        print("   Expected ValidationError due to self-review prevention")
        review.delete()
        return False
    except ValidationError as e:
        print(f"\n✓ Self-review blocked by model validation")
        print(f"   Error: {str(e)}")

    print(f"\n✓ Test passed: Self-review prevention enforced")
    return True


def main():
    print("\n" + "="*70)
    print("REVIEW CONSTRAINTS VERIFICATION TEST SUITE")
    print("="*70)
    print("Testing:")
    print("1. One review per user per location (unique_together)")
    print("2. Maximum 5 photos per review (ValidationError)")
    print("3. Self-review prevention (ValidationError)")
    print("="*70)

    results = []

    # Run all tests
    results.append(("One review per user per location", test_one_review_per_user_per_location()))
    results.append(("Maximum 5 photos per review", test_max_five_photos_per_review()))
    results.append(("Self-review prevention", test_self_review_prevention()))

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")

    all_passed = all(result[1] for result in results)
    print("="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*70 + "\n")

    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
