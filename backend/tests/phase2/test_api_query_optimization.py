#!/usr/bin/env python
"""
API Query Optimization Testing Script

This script tests the ACTUAL API endpoints (not just ORM queries) to verify
that N+1 query optimizations are working in production-like conditions.

Usage:
    djvenv/bin/python .claude/tests/phase2/test_api_query_optimization.py
"""

import os
import sys
import django

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.db import connection, reset_queries
from starview_app.models import Location, Review

def print_separator(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")

def count_queries_for_request(client, url, auth_user=None):
    """Make API request and count queries"""
    reset_queries()

    if auth_user:
        client.force_login(auth_user)

    response = client.get(url)
    query_count = len(connection.queries)

    return response, query_count

def main():
    print_separator("🌐 API QUERY OPTIMIZATION TEST")

    # Create test client
    client = Client()

    # Get or create a test user for authenticated endpoints
    test_user, _ = User.objects.get_or_create(
        username='api_test_user',
        defaults={'email': 'apitest@example.com'}
    )

    # Check database state
    location_count = Location.objects.count()
    review_count = Review.objects.count()

    print(f"Database Status:")
    print(f"  Locations: {location_count}")
    print(f"  Reviews: {review_count}")
    print()

    if location_count == 0:
        print("⚠️  WARNING: No locations in database. Run create_test_data.py first!")
        return

    # Test 1: Location List API
    print_separator("Test 1: Location List API (/api/locations/)")
    response, query_count = count_queries_for_request(
        client,
        '/api/locations/',
        auth_user=test_user
    )

    print(f"Response Status: {response.status_code}")
    print(f"🔍 Total Queries: {query_count}")

    if query_count > 20:
        print(f"⚠️  HIGH! Expected: 5-15 queries for optimized code")
        print(f"   This indicates N+1 query problems")
    else:
        print(f"✅ GOOD! Queries are optimized")

    # Show what was returned
    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        if 'results' in data:
            print(f"Locations returned: {len(data['results'])}")
        else:
            print(f"Locations returned: {len(data)}")

    # Test 2: Location Detail API
    print_separator("Test 2: Location Detail API (/api/locations/<id>/)")
    first_location = Location.objects.first()

    response, query_count = count_queries_for_request(
        client,
        f'/api/locations/{first_location.id}/',
        auth_user=test_user
    )

    print(f"Response Status: {response.status_code}")
    print(f"🔍 Total Queries: {query_count}")

    if query_count > 15:
        print(f"⚠️  HIGH! Expected: 5-10 queries for optimized code")
    else:
        print(f"✅ GOOD! Queries are optimized")

    # Test 3: Review List API (for a specific location)
    print_separator("Test 3: Review List API (/api/locations/<id>/reviews/)")

    response, query_count = count_queries_for_request(
        client,
        f'/api/locations/{first_location.id}/reviews/',
        auth_user=test_user
    )

    print(f"Response Status: {response.status_code}")
    print(f"🔍 Total Queries: {query_count}")

    if query_count > 15:
        print(f"⚠️  HIGH! Expected: 3-8 queries for optimized code")
    else:
        print(f"✅ GOOD! Queries are optimized")

    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        if 'results' in data:
            print(f"Reviews returned: {len(data['results'])}")
        else:
            print(f"Reviews returned: {len(data)}")

    # Test 4: Favorite Locations API (requires auth)
    print_separator("Test 4: Favorite Locations API (/api/favorite-locations/)")

    # Create a favorite for testing
    from starview_app.models import FavoriteLocation
    FavoriteLocation.objects.get_or_create(
        user=test_user,
        location=first_location,
        defaults={'nickname': 'Test Favorite'}
    )

    response, query_count = count_queries_for_request(
        client,
        '/api/favorite-locations/',
        auth_user=test_user
    )

    print(f"Response Status: {response.status_code}")
    print(f"🔍 Total Queries: {query_count}")

    if query_count > 20:
        print(f"⚠️  HIGH! Expected: 5-10 queries for optimized code")
        print(f"   FavoriteLocationViewSet may need optimization!")
    else:
        print(f"✅ GOOD! Queries are optimized")

    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        if 'results' in data:
            print(f"Favorites returned: {len(data['results'])}")
        else:
            print(f"Favorites returned: {len(data)}")

    # Summary
    print_separator("📋 SUMMARY")
    print("This test hits the ACTUAL API endpoints (not just ORM queries)")
    print("to verify that optimizations work in production-like conditions.")
    print()
    print("If any endpoint shows HIGH query counts, that ViewSet needs optimization.")
    print()

if __name__ == '__main__':
    # Enable query logging and allow testserver
    from django.conf import settings
    settings.DEBUG = True
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('testserver')
    main()
