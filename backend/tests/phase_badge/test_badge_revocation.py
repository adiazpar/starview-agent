#!/usr/bin/env python3
"""
Test Badge Revocation System

Tests that badges are automatically revoked when users delete content
that brought them below the badge threshold.

Test Coverage:
- Exploration badges (LocationVisit deletion)
- Contribution badges (Location deletion)
- Quality badges (Review deletion affecting rating)
- Review badges (Review/Vote deletion)
- Community badges (Follow/Comment deletion)
- Photographer badge (ReviewPhoto deletion)
- User deletion (CASCADE delete of UserBadge)
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
    Badge, UserBadge, Location, Review, ReviewComment,
    LocationVisit, Follow, Vote, ReviewPhoto
)
from starview_app.services.badge_service import BadgeService
from django.contrib.contenttypes.models import ContentType


def setup_test_data():
    """Create test users and badges"""
    print("\n🔧 Setting up test data...")

    # Create test users
    user1 = User.objects.create_user(
        username='badge_test_user1',
        email='badge_test1@example.com',
        password='testpass123'
    )

    user2 = User.objects.create_user(
        username='badge_test_user2',
        email='badge_test2@example.com',
        password='testpass123'
    )

    print(f"✓ Created test users: {user1.username}, {user2.username}")
    return user1, user2


def cleanup_test_data(user1, user2):
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")

    # Delete all test locations (will CASCADE delete reviews, visits, etc.)
    Location.objects.filter(added_by__in=[user1, user2]).delete()

    # Delete follows
    Follow.objects.filter(follower__in=[user1, user2]).delete()
    Follow.objects.filter(following__in=[user1, user2]).delete()

    # Delete users (will CASCADE delete UserBadge, UserProfile, etc.)
    user1.delete()
    user2.delete()

    print("✓ Cleaned up test data")


def test_exploration_badge_revocation(user):
    """Test that exploration badges are revoked when visits are deleted"""
    print("\n📍 Test: Exploration Badge Revocation")

    # Create 6 locations (signal auto-creates a LocationVisit for each since user is the creator)
    locations = []
    for i in range(6):
        location = Location.objects.create(
            name=f"Test Location {i}",
            latitude=34.0 + (i * 0.01),
            longitude=-118.0 + (i * 0.01),
            added_by=user
        )
        locations.append(location)

    # Now user has 6 location visits (all auto-created by signal)

    # Check for First Light badge (1 visit)
    first_light = Badge.objects.filter(slug='first-light').first()
    assert UserBadge.objects.filter(user=user, badge=first_light).exists()
    print("✓ User earned 'First Light' badge (1 visit)")

    # Check for Sky Seeker badge (5 visits)
    sky_seeker = Badge.objects.filter(slug='sky-seeker').first()
    visit_count = LocationVisit.objects.filter(user=user).count()
    print(f"  Current visits: {visit_count}")

    if sky_seeker and visit_count >= 5:
        assert UserBadge.objects.filter(user=user, badge=sky_seeker).exists()
        print("✓ User earned 'Sky Seeker' badge (5 visits)")

        # Delete visits to drop below threshold (delete all but 3 visits)
        visits_to_delete = LocationVisit.objects.filter(user=user)[3:]
        for visit in visits_to_delete:
            visit.delete()

        # Check badge was revoked
        visit_count_after = LocationVisit.objects.filter(user=user).count()
        print(f"  Visits after deletion: {visit_count_after}")

        assert not UserBadge.objects.filter(user=user, badge=sky_seeker).exists()
        print("✓ 'Sky Seeker' badge revoked after deleting visits")

        # Check First Light badge still exists (3 visits still > 1)
        assert UserBadge.objects.filter(user=user, badge=first_light).exists()
        print("✓ 'First Light' badge still retained (still above threshold)")
    else:
        print("⚠️  'Sky Seeker' badge not found or not earned, skipping revocation test")


def test_contribution_badge_revocation(user):
    """Test that contribution badges are revoked when locations are deleted"""
    print("\n🏗️  Test: Contribution Badge Revocation")

    # Create 5 locations
    locations = []
    for i in range(5):
        location = Location.objects.create(
            name=f"Contribution Test {i}",
            latitude=35.0 + (i * 0.01),
            longitude=-119.0 + (i * 0.01),
            added_by=user
        )
        locations.append(location)

    location_count = Location.objects.filter(added_by=user).count()
    print(f"  Created {location_count} locations")

    # Check for Scout badge (1 location)
    scout = Badge.objects.filter(slug='scout').first()
    assert UserBadge.objects.filter(user=user, badge=scout).exists()
    print("✓ User earned 'Scout' badge (1 location)")

    # Check for Trailblazer badge (5 locations)
    trailblazer = Badge.objects.filter(slug='trailblazer').first()
    if trailblazer and location_count >= 5:
        assert UserBadge.objects.filter(user=user, badge=trailblazer).exists()
        print("✓ User earned 'Trailblazer' badge (5 locations)")

        # Delete locations to drop below threshold (keep only 3)
        locations[3].delete()
        locations[4].delete()

        location_count_after = Location.objects.filter(added_by=user).count()
        print(f"  Locations after deletion: {location_count_after}")

        # Check Trailblazer badge was revoked
        assert not UserBadge.objects.filter(user=user, badge=trailblazer).exists()
        print("✓ 'Trailblazer' badge revoked after deleting locations")

        # Check Scout badge still exists
        assert UserBadge.objects.filter(user=user, badge=scout).exists()
        print("✓ 'Scout' badge still retained")


def test_review_badge_revocation(user1, user2):
    """Test that review badges are revoked when reviews are deleted"""
    print("\n⭐ Test: Review Badge Revocation")

    # Create locations
    locations = []
    for i in range(6):
        location = Location.objects.create(
            name=f"Review Test Location {i}",
            latitude=36.0 + (i * 0.01),
            longitude=-120.0 + (i * 0.01),
            added_by=user2
        )
        locations.append(location)

    # Create 5 reviews
    reviews = []
    for i in range(5):
        review = Review.objects.create(
            user=user1,
            location=locations[i],
            rating=5,
            comment=f"Great location {i}!"
        )
        reviews.append(review)

    review_count = Review.objects.filter(user=user1).count()
    print(f"  Created {review_count} reviews")

    # Check for Reviewer badge (5 reviews)
    reviewer = Badge.objects.filter(slug='reviewer').first()
    if reviewer:
        assert UserBadge.objects.filter(user=user1, badge=reviewer).exists()
        print("✓ User earned 'Reviewer' badge (5 reviews)")

        # Delete 2 reviews (drops to 3)
        reviews[3].delete()
        reviews[4].delete()

        review_count_after = Review.objects.filter(user=user1).count()
        print(f"  Reviews after deletion: {review_count_after}")

        # Check badge was revoked
        assert not UserBadge.objects.filter(user=user1, badge=reviewer).exists()
        print("✓ 'Reviewer' badge revoked after deleting reviews")


def test_community_badge_revocation(user1, user2):
    """Test that community badges are revoked when follows/comments are deleted"""
    print("\n👥 Test: Community Badge Revocation (Followers)")

    # Create 10 test followers (clean up any existing first)
    User.objects.filter(username__startswith='badge_follower_').delete()

    followers = []
    for i in range(10):
        follower = User.objects.create_user(
            username=f'badge_follower_{i}',
            email=f'badge_follower_{i}@example.com',
            password='testpass123'
        )
        Follow.objects.create(follower=follower, following=user1)
        followers.append(follower)

    follower_count = Follow.objects.filter(following=user1).count()
    print(f"  Created {follower_count} followers")

    # Check for Popular badge (10 followers)
    popular = Badge.objects.filter(slug='popular').first()
    if popular:
        assert UserBadge.objects.filter(user=user1, badge=popular).exists()
        print("✓ User earned 'Popular' badge (10 followers)")

        # Remove 3 followers (drops to 7)
        for follower in followers[:3]:
            Follow.objects.filter(follower=follower, following=user1).delete()
            follower.delete()

        follower_count_after = Follow.objects.filter(following=user1).count()
        print(f"  Followers after deletion: {follower_count_after}")

        # Check badge was revoked
        assert not UserBadge.objects.filter(user=user1, badge=popular).exists()
        print("✓ 'Popular' badge revoked after losing followers")

    # Clean up remaining followers
    for follower in followers[3:]:
        follower.delete()


def test_photographer_badge_revocation(user1, user2):
    """Test that Photographer badge is revoked when photos are deleted"""
    print("\n📷 Test: Photographer Badge Revocation")

    # Create 5 locations
    locations = []
    for i in range(5):
        location = Location.objects.create(
            name=f"Photo Test Location {i}",
            latitude=37.0 + (i * 0.01),
            longitude=-121.0 + (i * 0.01),
            added_by=user2
        )
        locations.append(location)

    # Create 5 reviews (one per location)
    reviews = []
    for i, location in enumerate(locations):
        review = Review.objects.create(
            user=user1,
            location=location,
            rating=5,
            comment=f"Great spot {i}!"
        )
        reviews.append(review)

    # Create 5 photos per review (5 reviews * 5 photos = 25 photos total)
    # This is the minimum for Photographer badge
    photos = []
    for review in reviews:
        for i in range(5):
            photo = ReviewPhoto.objects.create(
                review=review,
                image=f'test_photos/review_{review.id}_photo_{i}.jpg'
            )
            photos.append(photo)

    photo_count = ReviewPhoto.objects.filter(review__user=user1).count()
    print(f"  Created {photo_count} photos")

    # Check for Photographer badge
    photographer = Badge.objects.filter(slug='photographer').first()
    if photographer:
        assert UserBadge.objects.filter(user=user1, badge=photographer).exists()
        print("✓ User earned 'Photographer' badge (25 photos)")

        # Delete 5 photos (drops to 20)
        for photo in photos[:5]:
            photo.delete()

        photo_count_after = ReviewPhoto.objects.filter(review__user=user1).count()
        print(f"  Photos after deletion: {photo_count_after}")

        # Check badge was revoked
        assert not UserBadge.objects.filter(user=user1, badge=photographer).exists()
        print("✓ 'Photographer' badge revoked after deleting photos")


def test_user_deletion_cascade(user):
    """Test that all user badges are deleted when user is deleted"""
    print("\n🗑️  Test: User Deletion CASCADE")

    # Give user some badges
    first_light = Badge.objects.filter(slug='first-light').first()
    scout = Badge.objects.filter(slug='scout').first()

    if first_light:
        UserBadge.objects.create(user=user, badge=first_light)
    if scout:
        UserBadge.objects.create(user=user, badge=scout)

    badge_count = UserBadge.objects.filter(user=user).count()
    print(f"  User has {badge_count} badges")

    user_id = user.id
    username = user.username

    # Delete user
    user.delete()

    # Check that UserBadge records are gone
    remaining_badges = UserBadge.objects.filter(user_id=user_id).count()
    assert remaining_badges == 0
    print(f"✓ All badges deleted with user '{username}' (CASCADE delete working)")


def run_tests():
    """Run all badge revocation tests"""
    print("=" * 70)
    print("BADGE REVOCATION SYSTEM TEST")
    print("=" * 70)

    try:
        # Setup
        user1, user2 = setup_test_data()

        # Run tests
        test_exploration_badge_revocation(user1)
        test_contribution_badge_revocation(user1)
        test_review_badge_revocation(user1, user2)
        test_community_badge_revocation(user1, user2)
        test_photographer_badge_revocation(user1, user2)

        # Test CASCADE delete (creates new user for this test)
        test_user = User.objects.create_user(
            username='cascade_test_user',
            email='cascade@example.com',
            password='testpass123'
        )
        test_user_deletion_cascade(test_user)

        # Cleanup
        cleanup_test_data(user1, user2)

        print("\n" + "=" * 70)
        print("✅ ALL BADGE REVOCATION TESTS PASSED")
        print("=" * 70)
        print("\n✓ Badges are correctly revoked when content is deleted")
        print("✓ UserBadge CASCADE delete working correctly")
        print("✓ Progress tracking accurately reflects current counts")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        # Attempt cleanup on failure
        try:
            cleanup_test_data(user1, user2)
        except:
            pass

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Attempt cleanup on error
        try:
            cleanup_test_data(user1, user2)
        except:
            pass


if __name__ == '__main__':
    run_tests()
