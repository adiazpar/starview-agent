#!/usr/bin/env python
"""
Query Optimization Testing Script

This script measures database query counts for key endpoints before and after optimization.
Run this script BEFORE making optimizations to establish a baseline, then again AFTER
to measure improvement.

Usage:
    djvenv/bin/python .claude/tests/phase2/test_query_optimization.py
"""

import os
import sys
import django
from django.conf import settings

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.test.utils import override_settings
from django.db import connection, reset_queries
from django.contrib.auth.models import User
from starview_app.models import Location, Review, ReviewComment

def print_separator(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")

def count_queries(func):
    """Decorator to count queries executed by a function"""
    reset_queries()
    result = func()
    query_count = len(connection.queries)
    return result, query_count

def test_location_list():
    """Test query count for fetching list of locations"""
    def fetch_locations():
        # Use the same optimized query as LocationViewSet
        locations = list(
            Location.objects.select_related(
                'added_by',
                'verified_by'
            ).prefetch_related(
                'reviews__user',
                'reviews__photos'
            ).all()[:10]
        )
        # Simulate what the serializer does
        for location in locations:
            _ = location.added_by
            _ = location.verified_by
            reviews = list(location.reviews.all())
            for review in reviews:
                _ = review.user
                _ = list(review.photos.all())
        return locations

    return count_queries(fetch_locations)

def test_review_list():
    """Test query count for fetching reviews for a location"""
    def fetch_reviews():
        location = Location.objects.first()
        if not location:
            return []

        # Use the same optimized query as ReviewViewSet
        reviews = list(
            Review.objects.filter(
                location=location
            ).select_related(
                'user',
                'location'
            ).prefetch_related(
                'photos',
                'comments__user'
            )[:10]
        )
        for review in reviews:
            _ = review.user
            _ = list(review.photos.all())
            _ = list(review.comments.all())
        return reviews

    return count_queries(fetch_reviews)

def test_comment_list():
    """Test query count for fetching comments for a review"""
    def fetch_comments():
        review = Review.objects.first()
        if not review:
            return []

        # Use the same optimized query as CommentViewSet
        comments = list(
            ReviewComment.objects.filter(
                review=review
            ).select_related(
                'user',
                'user__userprofile',
                'review'
            )[:10]
        )
        for comment in comments:
            _ = comment.user
            _ = comment.review
        return comments

    return count_queries(fetch_comments)

def main():
    print_separator("📊 QUERY OPTIMIZATION BASELINE TEST")

    # Check database state
    location_count = Location.objects.count()
    review_count = Review.objects.count()
    comment_count = ReviewComment.objects.count()

    print(f"Database Status:")
    print(f"  Locations: {location_count}")
    print(f"  Reviews: {review_count}")
    print(f"  Comments: {comment_count}")

    if location_count == 0:
        print("\n⚠️  WARNING: No locations in database. Create some test data first!")
        print("   You can do this via the admin interface at http://127.0.0.1:8000/admin/")
        return

    print_separator("Test 1: Location List (10 items)")
    locations, query_count = test_location_list()
    print(f"Locations fetched: {len(locations)}")
    print(f"🔍 Total Queries: {query_count}")

    if query_count > 20:
        print(f"⚠️  HIGH! Expected: 5-10 queries for optimized code")
        print(f"   This indicates N+1 query problems")
    else:
        print(f"✅ GOOD! Queries are optimized")

    print_separator("Test 2: Review List (for first location)")
    reviews, query_count = test_review_list()
    print(f"Reviews fetched: {len(reviews)}")
    print(f"🔍 Total Queries: {query_count}")

    if query_count > 15:
        print(f"⚠️  HIGH! Expected: 3-5 queries for optimized code")
        print(f"   This indicates N+1 query problems")
    else:
        print(f"✅ GOOD! Queries are optimized")

    print_separator("Test 3: Comment List (for first review)")
    comments, query_count = test_comment_list()
    print(f"Comments fetched: {len(comments)}")
    print(f"🔍 Total Queries: {query_count}")

    if query_count > 12:
        print(f"⚠️  HIGH! Expected: 2-3 queries for optimized code")
        print(f"   This indicates N+1 query problems")
    else:
        print(f"✅ GOOD! Queries are optimized")

    print_separator("📋 SUMMARY")
    print("Run this script again after optimization to measure improvement!")
    print("\nTo see detailed query information, check the queries with:")
    print("  from django.db import connection")
    print("  for q in connection.queries:")
    print("      print(q['sql'])")
    print("\n")

if __name__ == '__main__':
    # Enable query logging
    settings.DEBUG = True
    main()
