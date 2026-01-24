# PostGIS Location model unit tests.
# Tests PointField synchronization from latitude/longitude values.

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
from starview_app.models import Location


class LocationCoordinatesSyncTests(TestCase):
    """Tests for PostGIS coordinates field synchronization."""

    @classmethod
    def setUpTestData(cls):
        """Create test user for location ownership."""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @skipUnlessDBFeature('has_geometry_columns')
    def test_coordinates_sync_on_create(self):
        """New location gets coordinates from lat/lng."""
        location = Location.objects.create(
            name='Test Location',
            latitude=47.6062,
            longitude=-122.3321,
            added_by=self.user
        )

        self.assertIsNotNone(location.coordinates)
        self.assertEqual(location.coordinates.srid, 4326)
        # Point uses (lng, lat) order
        self.assertAlmostEqual(location.coordinates.x, -122.3321, places=4)
        self.assertAlmostEqual(location.coordinates.y, 47.6062, places=4)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_coordinates_sync_on_update(self):
        """Updating lat/lng updates coordinates."""
        location = Location.objects.create(
            name='Test Location',
            latitude=47.6062,
            longitude=-122.3321,
            added_by=self.user
        )

        # Update coordinates
        location.latitude = 34.0522
        location.longitude = -118.2437
        location.save()

        location.refresh_from_db()
        self.assertAlmostEqual(location.coordinates.x, -118.2437, places=4)
        self.assertAlmostEqual(location.coordinates.y, 34.0522, places=4)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_coordinates_srid(self):
        """Coordinates use WGS84 (SRID 4326)."""
        location = Location.objects.create(
            name='Test Location',
            latitude=47.6062,
            longitude=-122.3321,
            added_by=self.user
        )

        self.assertEqual(location.coordinates.srid, 4326)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_point_order(self):
        """Point uses (lng, lat) not (lat, lng)."""
        location = Location.objects.create(
            name='Test Location',
            latitude=47.6062,
            longitude=-122.3321,
            added_by=self.user
        )

        # x = longitude, y = latitude in PostGIS Point
        self.assertAlmostEqual(location.coordinates.x, location.longitude, places=4)
        self.assertAlmostEqual(location.coordinates.y, location.latitude, places=4)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_coordinates_at_extreme_values(self):
        """Test coordinates at extreme latitude/longitude values."""
        # Near the poles
        location = Location.objects.create(
            name='Arctic Location',
            latitude=85.0,
            longitude=0.0,
            added_by=self.user
        )

        self.assertIsNotNone(location.coordinates)
        self.assertAlmostEqual(location.coordinates.y, 85.0, places=4)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_coordinates_at_antimeridian(self):
        """Test coordinates near the antimeridian (±180°)."""
        location = Location.objects.create(
            name='Pacific Location',
            latitude=0.0,
            longitude=179.9,
            added_by=self.user
        )

        self.assertIsNotNone(location.coordinates)
        self.assertAlmostEqual(location.coordinates.x, 179.9, places=4)


if __name__ == '__main__':
    import unittest
    unittest.main()
