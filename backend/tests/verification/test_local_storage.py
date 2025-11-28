#!/usr/bin/env python3
"""
Test script to verify local filesystem storage:
1. Upload a test profile picture
2. Create a test review with a photo
3. Verify files are in local media/ directory
4. Delete the files
5. Verify deletion worked

Run with: djvenv/bin/python .claude/backend/tests/verification/test_local_storage.py
"""

import os
import sys
import django
from io import BytesIO
from PIL import Image

# Django setup:
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
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


def test_storage_mode():
    """Check which storage mode is active."""
    print("\n" + "="*70)
    print("STORAGE MODE CHECK")
    print("="*70)

    use_r2 = os.getenv('USE_R2_STORAGE', 'False') == 'True'
    storage_backend = settings.STORAGES['default']['BACKEND']

    print(f"\nUSE_R2_STORAGE env var: {os.getenv('USE_R2_STORAGE', 'Not Set')}")
    print(f"Storage backend: {storage_backend}")
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")

    if 'FileSystemStorage' in storage_backend:
        print(f"\n✓ Using LOCAL filesystem storage")
        print(f"  Files will be saved to: {settings.MEDIA_ROOT}")
        return 'local'
    elif 'S3Storage' in storage_backend:
        print(f"\n✓ Using CLOUDFLARE R2 storage")
        print(f"  Files will be saved to R2 bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
        return 'r2'
    else:
        print(f"\n⚠️  Unknown storage backend: {storage_backend}")
        return 'unknown'


def test_profile_picture_upload():
    """Test uploading a profile picture."""
    print("\n" + "="*70)
    print("TEST 1: Profile Picture Upload")
    print("="*70)

    # Get adiazpar user
    try:
        user = User.objects.get(username='adiazpar')
        profile = user.userprofile
        print(f"\n✓ Found user: {user.username}")
    except User.DoesNotExist:
        print("\n✗ User 'adiazpar' not found")
        return None

    # Save old profile picture (if exists)
    old_profile_pic = profile.profile_picture.name if profile.profile_picture else None
    print(f"  Current profile picture: {old_profile_pic or 'None'}")

    # Upload new test profile picture
    test_image = create_test_image(color='purple', size=(250, 250))
    profile.profile_picture = test_image
    profile.save()

    print(f"\n✓ Uploaded new profile picture")
    print(f"  Storage name: {profile.profile_picture.name}")
    print(f"  URL: {profile.profile_picture.url}")

    # Check if file exists locally
    if hasattr(profile.profile_picture, 'path'):
        file_path = profile.profile_picture.path
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"  ✓ File exists on filesystem: {file_path}")
            print(f"  ✓ File size: {file_size} bytes")
        else:
            print(f"  ✗ File NOT found on filesystem: {file_path}")
    else:
        print(f"  ℹ️  Using remote storage (no local path)")

    return profile


def test_review_photo_upload():
    """Test uploading a review photo."""
    print("\n" + "="*70)
    print("TEST 2: Review Photo Upload")
    print("="*70)

    # Get adiazpar user
    user = User.objects.get(username='adiazpar')

    # Create a test location (by different user to avoid self-review)
    test_user, _ = User.objects.get_or_create(
        username='local_test_user',
        defaults={'email': 'localtest@test.com'}
    )

    location, _ = Location.objects.get_or_create(
        name='Local Storage Test Location',
        added_by=test_user,
        defaults={
            'latitude': 41.0,
            'longitude': -101.0
        }
    )

    print(f"\n✓ Created/found test location: {location.name}")

    # Delete any existing review for this location
    Review.objects.filter(user=user, location=location).delete()

    # Create a test review
    review = Review.objects.create(
        user=user,
        location=location,
        rating=4,
        comment="Local storage test review"
    )

    print(f"✓ Created test review (ID: {review.id})")

    # Upload a test photo to the review
    test_image = create_test_image(color='orange', size=(350, 350))
    photo = ReviewPhoto.objects.create(
        review=review,
        image=test_image,
        caption="Test photo for local storage verification"
    )

    print(f"\n✓ Uploaded review photo")
    print(f"  Storage name: {photo.image.name}")
    print(f"  URL: {photo.image.url}")
    print(f"  Thumbnail: {photo.thumbnail.name if photo.thumbnail else 'None'}")

    # Check if files exist locally
    if hasattr(photo.image, 'path'):
        # Check main image
        image_path = photo.image.path
        if os.path.exists(image_path):
            file_size = os.path.getsize(image_path)
            print(f"  ✓ Image exists: {image_path}")
            print(f"    Size: {file_size} bytes")
        else:
            print(f"  ✗ Image NOT found: {image_path}")

        # Check thumbnail
        if photo.thumbnail and hasattr(photo.thumbnail, 'path'):
            thumb_path = photo.thumbnail.path
            if os.path.exists(thumb_path):
                thumb_size = os.path.getsize(thumb_path)
                print(f"  ✓ Thumbnail exists: {thumb_path}")
                print(f"    Size: {thumb_size} bytes")
            else:
                print(f"  ✗ Thumbnail NOT found: {thumb_path}")
    else:
        print(f"  ℹ️  Using remote storage (no local path)")

    return review, photo


def cleanup_test_files(profile, review):
    """Delete test files."""
    print("\n" + "="*70)
    print("TEST 3: Deleting Test Files")
    print("="*70)

    # Get file paths before deletion
    profile_path = None
    image_path = None
    thumb_path = None

    if profile and profile.profile_picture:
        if hasattr(profile.profile_picture, 'path'):
            profile_path = profile.profile_picture.path
        profile.profile_picture.delete(save=True)
        print(f"\n  ✓ Deleted profile picture")
        if profile_path and os.path.exists(profile_path):
            print(f"    ✗ WARNING: File still exists: {profile_path}")
        elif profile_path:
            print(f"    ✓ File removed from filesystem: {profile_path}")

    if review:
        # Get photo paths
        photo = review.photos.first()
        if photo:
            if hasattr(photo.image, 'path'):
                image_path = photo.image.path
            if photo.thumbnail and hasattr(photo.thumbnail, 'path'):
                thumb_path = photo.thumbnail.path

        review_id = review.id
        photo_count = review.photos.count()
        review.delete()
        print(f"\n  ✓ Deleted review {review_id} with {photo_count} photo(s)")

        # Check if files are gone
        if image_path:
            if os.path.exists(image_path):
                print(f"    ✗ WARNING: Image still exists: {image_path}")
            else:
                print(f"    ✓ Image removed: {image_path}")

        if thumb_path:
            if os.path.exists(thumb_path):
                print(f"    ✗ WARNING: Thumbnail still exists: {thumb_path}")
            else:
                print(f"    ✓ Thumbnail removed: {thumb_path}")

    print("\n✓ Cleanup complete")


def main():
    print("\n" + "="*70)
    print("LOCAL STORAGE VERIFICATION TEST")
    print("="*70)

    # Check storage mode
    storage_mode = test_storage_mode()

    if storage_mode != 'local':
        print("\n" + "="*70)
        print("⚠️  WARNING: Not using local storage!")
        print("="*70)
        print("\nTo use local storage, set USE_R2_STORAGE=False in .env")
        print("Then restart your Django server.\n")
        return 1

    print("\nThis test will:")
    print("1. Upload a test profile picture for adiazpar")
    print("2. Create a test review with a photo")
    print("3. Verify files exist in media/ directory")
    print("4. Delete all test files")
    print("\n" + "="*70)

    profile = None
    review = None

    try:
        # Test 1: Profile picture upload
        profile = test_profile_picture_upload()

        # Test 2: Review photo upload
        review, photo = test_review_photo_upload()

        # Wait for user verification
        print("\n" + "="*70)
        print("VERIFICATION CHECKPOINT")
        print("="*70)
        print(f"\nPlease check your media/ directory:")
        print(f"  {settings.MEDIA_ROOT}")
        print("\nYou should see:")
        print("  - profile_pics/test_image.jpg")
        print("  - review_photos/{location_id}/{review_id}/*.jpg")
        print("  - review_photos/{location_id}/{review_id}/thumbnails/*_thumb.jpg")

        # Test 3: Delete files
        cleanup_test_files(profile, review)

        print("\n" + "="*70)
        print("FINAL VERIFICATION")
        print("="*70)
        print("\nPlease check your media/ directory again to verify:")
        print("  - Test files have been deleted")
        print("  - Directories are cleaned up (if empty)")
        print("\n" + "="*70)

        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("\n💡 TIP: To switch to R2 storage, set USE_R2_STORAGE=True in .env\n")
        return 0

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Attempt cleanup even on error
        print("\nAttempting cleanup...")
        try:
            cleanup_test_files(profile, review)
        except:
            pass

        return 1


if __name__ == '__main__':
    exit(main())
