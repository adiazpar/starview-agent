# PostGIS distance filtering unit tests.
# Tests ST_DWithin spatial queries and distance annotation.

import os
import sys
import django

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.test import TestCase, skipUnlessDBFeature
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from starview_app.models import Location


class DistanceFilteringTests(TestCase):
    """Tests for PostGIS distance filtering."""

    @classmethod
    def setUpTestData(cls):
        """Create test user and locations at known distances."""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Reference point: Seattle, WA
        cls.seattle_lat = 47.6062
        cls.seattle_lng = -122.3321

        # Create locations at varying distances from Seattle
        # Location 1: ~10km from Seattle (Bellevue)
        cls.bellevue = Location.objects.create(
            name='Bellevue',
            latitude=47.6101,
            longitude=-122.2015,
            added_by=cls.user
        )

        # Location 2: ~50km from Seattle (Tacoma)
        cls.tacoma = Location.objects.create(
            name='Tacoma',
            latitude=47.2529,
            longitude=-122.4443,
            added_by=cls.user
        )

        # Location 3: ~200km from Seattle (Portland)
        cls.portland = Location.objects.create(
            name='Portland',
            latitude=45.5152,
            longitude=-122.6784,
            added_by=cls.user
        )

        # Location 4: ~1500km from Seattle (Los Angeles)
        cls.los_angeles = Location.objects.create(
            name='Los Angeles',
            latitude=34.0522,
            longitude=-118.2437,
            added_by=cls.user
        )

    @skipUnlessDBFeature('has_geometry_columns')
    def test_filter_within_radius(self):
        """Locations within radius are returned."""
        user_location = Point(self.seattle_lng, self.seattle_lat, srid=4326)

        # 80km radius should include Bellevue (~10km) and Tacoma (~50km)
        nearby = Location.objects.filter(
            coordinates__dwithin=(user_location, D(km=80))
        )

        self.assertIn(self.bellevue, nearby)
        self.assertIn(self.tacoma, nearby)
        self.assertNotIn(self.portland, nearby)
        self.assertNotIn(self.los_angeles, nearby)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_filter_outside_radius(self):
        """Locations outside radius excluded."""
        user_location = Point(self.seattle_lng, self.seattle_lat, srid=4326)

        # 20km radius should only include Bellevue (~10km)
        nearby = Location.objects.filter(
            coordinates__dwithin=(user_location, D(km=20))
        )

        self.assertIn(self.bellevue, nearby)
        self.assertNotIn(self.tacoma, nearby)
        self.assertNotIn(self.portland, nearby)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_distance_annotation(self):
        """Results have distance annotation."""
        user_location = Point(self.seattle_lng, self.seattle_lat, srid=4326)

        nearby = Location.objects.filter(
            coordinates__dwithin=(user_location, D(km=100))
        ).annotate(
            distance=Distance('coordinates', user_location)
        )

        for loc in nearby:
            self.assertTrue(hasattr(loc, 'distance'))
            self.assertIsNotNone(loc.distance)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_distance_in_meters(self):
        """PostGIS Distance returns meters for geography fields."""
        user_location = Point(self.seattle_lng, self.seattle_lat, srid=4326)

        bellevue_with_distance = Location.objects.filter(
            pk=self.bellevue.pk
        ).annotate(
            distance=Distance('coordinates', user_location)
        ).first()

        # Distance should be approximately 10km (10000m)
        # Allow 20% tolerance for geographic variations
        distance_km = bellevue_with_distance.distance.m / 1000
        self.assertGreater(distance_km, 8)
        self.assertLess(distance_km, 15)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_sort_by_distance_asc(self):
        """Results can be sorted by distance ascending."""
        user_location = Point(self.seattle_lng, self.seattle_lat, srid=4326)

        nearby = list(Location.objects.filter(
            coordinates__dwithin=(user_location, D(km=250))
        ).annotate(
            distance=Distance('coordinates', user_location)
        ).order_by('distance'))

        # Should be ordered: Bellevue, Tacoma, Portland
        self.assertEqual(nearby[0], self.bellevue)
        self.assertEqual(nearby[1], self.tacoma)
        self.assertEqual(nearby[2], self.portland)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_sort_by_distance_desc(self):
        """Results can be sorted by distance descending."""
        user_location = Point(self.seattle_lng, self.seattle_lat, srid=4326)

        nearby = list(Location.objects.filter(
            coordinates__dwithin=(user_location, D(km=250))
        ).annotate(
            distance=Distance('coordinates', user_location)
        ).order_by('-distance'))

        # Should be ordered: Portland, Tacoma, Bellevue
        self.assertEqual(nearby[0], self.portland)
        self.assertEqual(nearby[1], self.tacoma)
        self.assertEqual(nearby[2], self.bellevue)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_large_radius(self):
        """Large radius query works efficiently."""
        user_location = Point(self.seattle_lng, self.seattle_lat, srid=4326)

        # 2000km radius should include all locations
        all_nearby = Location.objects.filter(
            coordinates__dwithin=(user_location, D(km=2000))
        )

        self.assertEqual(all_nearby.count(), 4)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_zero_distance(self):
        """Query at exact location coordinates works."""
        user_location = Point(self.bellevue.longitude, self.bellevue.latitude, srid=4326)

        # 1km radius from Bellevue's exact coordinates
        nearby = Location.objects.filter(
            coordinates__dwithin=(user_location, D(km=1))
        ).annotate(
            distance=Distance('coordinates', user_location)
        )

        self.assertIn(self.bellevue, nearby)

        bellevue_result = nearby.get(pk=self.bellevue.pk)
        # Distance should be very close to 0 (within 100m due to floating point)
        self.assertLess(bellevue_result.distance.m, 100)


if __name__ == '__main__':
    import unittest
    unittest.main()
