#!/usr/bin/env python
"""
Create Test Data for Query Optimization Testing

This script creates realistic test data to demonstrate N+1 query problems.
Creates multiple locations, reviews, and comments to show the performance impact.

Usage:
    djvenv/bin/python .claude/tests/phase2/create_test_data.py
"""

import os
import sys
import django
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
# Disable external API calls to avoid rate limits
os.environ['DISABLE_EXTERNAL_APIS'] = 'True'
django.setup()

from django.contrib.auth.models import User
from starview_app.models import Location, Review, ReviewComment

def create_test_users(count=10):
    """Create test users"""
    users = []
    for i in range(count):
        username = f"testuser{i}"
        email = f"testuser{i}@example.com"

        # Check if user exists
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created user: {username}")
        else:
            print(f"ℹ️  User already exists: {username}")
        users.append(user)

    return users

def create_test_locations(users, count=20):
    """Create test locations"""
    locations = []

    # Base coordinates (San Francisco area)
    base_lat = 37.7749
    base_lon = -122.4194

    for i in range(count):
        # Use update_or_create to avoid triggering the save() method multiple times
        # and to skip API calls by using direct database insert
        location, created = Location.objects.update_or_create(
            name=f"Dark Sky Location {i}",
            defaults={
                'latitude': base_lat + (i * 0.01),
                'longitude': base_lon + (i * 0.01),
                'elevation': 100 + (i * 10),  # Varying elevations
                'added_by': users[i % len(users)],
                'is_verified': i % 3 == 0,  # Every 3rd location is verified
                'verified_by': users[0] if i % 3 == 0 else None,
                # Pre-populate address fields to avoid API calls
                'formatted_address': f"Test Address {i}, San Francisco, CA",
                'administrative_area': "California",
                'locality': "San Francisco",
                'country': "United States",
            }
        )

        if created:
            print(f"✅ Created location: {location.name}")
        else:
            print(f"ℹ️  Location already exists: {location.name}")

        locations.append(location)

    return locations

def create_test_reviews(users, locations, reviews_per_location=5):
    """Create test reviews for each location"""
    reviews = []

    for location in locations:
        for i in range(reviews_per_location):
            review, created = Review.objects.get_or_create(
                location=location,
                user=users[(i + location.id) % len(users)],
                defaults={
                    'rating': ((i % 5) + 1),  # Ratings 1-5
                    'comment': f"Review #{i} for {location.name}. Great spot for stargazing! The sky was clear and dark.",
                }
            )

            if created:
                reviews.append(review)

    print(f"✅ Created {len(reviews)} reviews")
    return reviews

def create_test_comments(users, reviews, comments_per_review=3):
    """Create test comments for each review"""
    comments = []

    for review in reviews:
        for i in range(comments_per_review):
            comment, created = ReviewComment.objects.get_or_create(
                review=review,
                user=users[(i + review.id) % len(users)],
                defaults={
                    'content': f"Comment #{i} on review {review.id}. Thanks for sharing this spot!",
                }
            )

            if created:
                comments.append(comment)

    print(f"✅ Created {len(comments)} comments")
    return comments

def main():
    print("="*80)
    print(" 📊 CREATING TEST DATA FOR QUERY OPTIMIZATION")
    print("="*80)
    print()

    # Create test data
    print("Creating test users...")
    users = create_test_users(10)
    print()

    print("Creating test locations...")
    locations = create_test_locations(users, 20)
    print()

    print("Creating test reviews...")
    reviews = create_test_reviews(users, locations, reviews_per_location=5)
    print()

    print("Creating test comments...")
    comments = create_test_comments(users, reviews, comments_per_review=3)
    print()

    print("="*80)
    print(" 📋 SUMMARY")
    print("="*80)
    print(f"Total Users: {User.objects.count()}")
    print(f"Total Locations: {Location.objects.count()}")
    print(f"Total Reviews: {Review.objects.count()}")
    print(f"Total Comments: {ReviewComment.objects.count()}")
    print()
    print("✅ Test data created successfully!")
    print("Now run: djvenv/bin/python .claude/tests/phase2/test_query_optimization.py")
    print()

if __name__ == '__main__':
    main()
