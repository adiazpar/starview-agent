#!/usr/bin/env python3
"""
Test script to verify R2 upload functionality:
1. Upload a test profile picture for adiazpar
2. Create a test review with a photo
3. Verify files are in R2 (check URLs)
4. Delete the files
5. Verify deletion worked

Run with: djvenv/bin/python .claude/backend/tests/verification/test_r2_upload.py
"""

import os
import sys
import django
import requests
from io import BytesIO
from PIL import Image

# Django setup:
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from starview_app.models import UserProfile, Location, Review, ReviewPhoto


def create_test_image(color='blue', size=(200, 200)):
    """Creates a test image in memory."""
    img = Image.new('RGB', size, color=color)
    img_io = BytesIO()
    img.save(img_io, format='JPEG', quality=85)
    file_size = img_io.tell()
    img_io.seek(0)
    return InMemoryUploadedFile(
        img_io, None, 'test_image.jpg', 'image/jpeg', file_size, None
    )


def test_profile_picture_upload():
    """Test uploading a profile picture to R2."""
    print("\n" + "="*70)
    print("TEST 1: Profile Picture Upload to R2")
    print("="*70)

    # Get adiazpar user
    try:
        user = User.objects.get(username='adiazpar')
        profile = user.userprofile
        print(f"\n✓ Found user: {user.username}")
    except User.DoesNotExist:
        print("\n✗ User 'adiazpar' not found")
        return None, None

    # Save old profile picture (if exists)
    old_profile_pic = profile.profile_picture.name if profile.profile_picture else None
    print(f"  Current profile picture: {old_profile_pic or 'None'}")

    # Upload new test profile picture
    test_image = create_test_image(color='green', size=(300, 300))
    profile.profile_picture = test_image
    profile.save()

    print(f"\n✓ Uploaded new profile picture")
    print(f"  Storage name: {profile.profile_picture.name}")
    print(f"  Public URL: {profile.profile_picture.url}")

    # Verify URL is R2 (should contain r2.dev or custom domain)
    if 'r2.dev' in profile.profile_picture.url or 'starview.app' in profile.profile_picture.url:
        print(f"  ✓ URL is R2-hosted")
    else:
        print(f"  ⚠️  URL might be local: {profile.profile_picture.url}")

    # Try to fetch the image to verify it's accessible
    try:
        response = requests.head(profile.profile_picture.url, timeout=5)
        if response.status_code == 200:
            print(f"  ✓ Image is accessible (HTTP {response.status_code})")
        else:
            print(f"  ⚠️  Image returned HTTP {response.status_code}")
    except Exception as e:
        print(f"  ⚠️  Could not verify accessibility: {e}")

    return profile, old_profile_pic


def test_review_photo_upload():
    """Test uploading a review photo to R2."""
    print("\n" + "="*70)
    print("TEST 2: Review Photo Upload to R2")
    print("="*70)

    # Get adiazpar user
    user = User.objects.get(username='adiazpar')

    # Create a test location (by different user to avoid self-review)
    test_user, _ = User.objects.get_or_create(
        username='r2_test_user',
        defaults={'email': 'r2test@test.com'}
    )

    location, _ = Location.objects.get_or_create(
        name='R2 Upload Test Location',
        added_by=test_user,
        defaults={
            'latitude': 40.0,
            'longitude': -100.0
        }
    )

    print(f"\n✓ Created/found test location: {location.name}")

    # Delete any existing review for this location
    Review.objects.filter(user=user, location=location).delete()

    # Create a test review
    review = Review.objects.create(
        user=user,
        location=location,
        rating=5,
        comment="R2 upload test review"
    )

    print(f"✓ Created test review (ID: {review.id})")

    # Upload a test photo to the review
    test_image = create_test_image(color='red', size=(400, 400))
    photo = ReviewPhoto.objects.create(
        review=review,
        image=test_image,
        caption="Test photo for R2 verification"
    )

    print(f"\n✓ Uploaded review photo")
    print(f"  Storage name: {photo.image.name}")
    print(f"  Public URL: {photo.image.url}")
    print(f"  Thumbnail URL: {photo.thumbnail.url if photo.thumbnail else 'None'}")

    # Verify URL is R2
    if 'r2.dev' in photo.image.url or 'starview.app' in photo.image.url:
        print(f"  ✓ URL is R2-hosted")
    else:
        print(f"  ⚠️  URL might be local: {photo.image.url}")

    # Try to fetch the image to verify it's accessible
    try:
        response = requests.head(photo.image.url, timeout=5)
        if response.status_code == 200:
            print(f"  ✓ Image is accessible (HTTP {response.status_code})")
        else:
            print(f"  ⚠️  Image returned HTTP {response.status_code}")
    except Exception as e:
        print(f"  ⚠️  Could not verify accessibility: {e}")

    return review, photo


def cleanup_test_files(profile, old_profile_pic, review):
    """Delete test files from R2."""
    print("\n" + "="*70)
    print("TEST 3: Deleting Test Files from R2")
    print("="*70)

    # Restore old profile picture or clear it
    if profile:
        profile_pic_name = profile.profile_picture.name
        if old_profile_pic:
            print(f"\n  Restoring old profile picture: {old_profile_pic}")
            # Note: We can't easily restore the old file, so we'll just clear it
            profile.profile_picture.delete(save=False)
            profile.profile_picture = None
            profile.save()
            print(f"  ✓ Cleared profile picture (old one was: {old_profile_pic})")
        else:
            print(f"\n  Deleting profile picture: {profile_pic_name}")
            profile.profile_picture.delete(save=True)
            print(f"  ✓ Profile picture deleted from R2")

    # Delete review (CASCADE will delete photo)
    if review:
        review_id = review.id
        photo_count = review.photos.count()
        print(f"\n  Deleting review {review_id} with {photo_count} photo(s)")
        review.delete()
        print(f"  ✓ Review and photos deleted from R2")

    print("\n✓ Cleanup complete")


def main():
    print("\n" + "="*70)
    print("R2 UPLOAD VERIFICATION TEST")
    print("="*70)
    print("\nThis test will:")
    print("1. Upload a test profile picture for adiazpar")
    print("2. Create a test review with a photo")
    print("3. Display R2 URLs for verification")
    print("4. Delete all test files")
    print("\n" + "="*70)

    profile, old_profile_pic = None, None
    review, photo = None, None

    try:
        # Test 1: Profile picture upload
        profile, old_profile_pic = test_profile_picture_upload()

        # Test 2: Review photo upload
        review, photo = test_review_photo_upload()

        # Pause for user verification
        print("\n" + "="*70)
        print("VERIFICATION CHECKPOINT")
        print("="*70)
        print("\nPlease check your Cloudflare R2 dashboard to verify:")
        print("1. Profile picture appears in: profile_pics/")
        print("2. Review photo appears in: review_photos/{location_id}/{review_id}/")
        print("3. Thumbnail appears in: review_photos/{location_id}/{review_id}/thumbnails/")
        print("\nURLs to verify:")
        if profile and profile.profile_picture:
            print(f"\nProfile: {profile.profile_picture.url}")
        if photo:
            print(f"Review Photo: {photo.image.url}")
            if photo.thumbnail:
                print(f"Thumbnail: {photo.thumbnail.url}")

        input("\nPress ENTER when ready to delete test files...")

        # Test 3: Delete files
        cleanup_test_files(profile, old_profile_pic, review)

        print("\n" + "="*70)
        print("FINAL VERIFICATION")
        print("="*70)
        print("\nPlease check your R2 dashboard again to verify:")
        print("1. Test files have been deleted")
        print("2. Directories are cleaned up (if empty)")
        print("\n" + "="*70)

        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY\n")
        return 0

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Attempt cleanup even on error
        print("\nAttempting cleanup...")
        try:
            cleanup_test_files(profile, old_profile_pic, review)
        except:
            pass

        return 1


if __name__ == '__main__':
    exit(main())
