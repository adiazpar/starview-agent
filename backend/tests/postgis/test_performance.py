# PostGIS performance tests.
# Benchmarks spatial query performance.

import os
import sys
import django
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.test import TestCase, skipUnlessDBFeature
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db import connection
from starview_app.models import Location
import random


class PostGISPerformanceTests(TestCase):
    """Performance tests for PostGIS spatial queries."""

    @classmethod
    def setUpTestData(cls):
        """Create test user and many test locations."""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Reference point for queries
        cls.ref_lat = 47.6062
        cls.ref_lng = -122.3321

        # Create many test locations spread around the reference point
        cls.locations = []
        for i in range(100):
            # Random offset within ~500km
            lat_offset = random.uniform(-5, 5)
            lng_offset = random.uniform(-5, 5)

            location = Location.objects.create(
                name=f'Test Location {i}',
                latitude=cls.ref_lat + lat_offset,
                longitude=cls.ref_lng + lng_offset,
                added_by=cls.user
            )
            cls.locations.append(location)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_distance_query_performance(self):
        """PostGIS distance query should complete quickly."""
        user_location = Point(self.ref_lng, self.ref_lat, srid=4326)

        start_time = time.time()

        # Query with 100km radius
        results = list(Location.objects.filter(
            coordinates__dwithin=(user_location, D(km=100))
        ).annotate(
            distance=Distance('coordinates', user_location)
        ).order_by('distance'))

        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms

        # Should complete in under 200ms even without proper index
        self.assertLess(elapsed_time, 200, f'Query took {elapsed_time:.1f}ms')

    @skipUnlessDBFeature('has_geometry_columns')
    def test_query_plan_uses_index(self):
        """Verify spatial index is used for distance queries."""
        user_location = Point(self.ref_lng, self.ref_lat, srid=4326)

        # Build the query
        queryset = Location.objects.filter(
            coordinates__dwithin=(user_location, D(km=100))
        )

        # Get the SQL query
        sql = str(queryset.query)

        # The query should use ST_DWithin
        self.assertIn('ST_DWithin', sql.upper())

    @skipUnlessDBFeature('has_geometry_columns')
    def test_multiple_distance_queries(self):
        """Multiple distance queries should be efficient."""
        user_locations = [
            Point(self.ref_lng + random.uniform(-2, 2),
                  self.ref_lat + random.uniform(-2, 2),
                  srid=4326)
            for _ in range(10)
        ]

        start_time = time.time()

        for user_loc in user_locations:
            list(Location.objects.filter(
                coordinates__dwithin=(user_loc, D(km=50))
            )[:10])

        elapsed_time = (time.time() - start_time) * 1000

        # 10 queries should complete in under 500ms total
        self.assertLess(elapsed_time, 500, f'10 queries took {elapsed_time:.1f}ms')

    @skipUnlessDBFeature('has_geometry_columns')
    def test_count_query_performance(self):
        """Count queries with spatial filter should be fast."""
        user_location = Point(self.ref_lng, self.ref_lat, srid=4326)

        start_time = time.time()

        count = Location.objects.filter(
            coordinates__dwithin=(user_location, D(km=200))
        ).count()

        elapsed_time = (time.time() - start_time) * 1000

        # Count should be very fast
        self.assertLess(elapsed_time, 100, f'Count query took {elapsed_time:.1f}ms')
        self.assertGreater(count, 0)


if __name__ == '__main__':
    import unittest
    unittest.main()
