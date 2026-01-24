# PostGIS API integration tests.
# Tests distance filtering through REST API endpoints.

import os
import sys
import django

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.test import TestCase, skipUnlessDBFeature
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from starview_app.models import Location


class LocationAPIDistanceTests(TestCase):
    """Tests for distance filtering via API endpoints."""

    @classmethod
    def setUpTestData(cls):
        """Create test user and locations."""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Seattle area locations
        cls.seattle_lat = 47.6062
        cls.seattle_lng = -122.3321

        # ~10km from Seattle
        cls.bellevue = Location.objects.create(
            name='Bellevue Observatory',
            latitude=47.6101,
            longitude=-122.2015,
            added_by=cls.user
        )

        # ~50km from Seattle
        cls.tacoma = Location.objects.create(
            name='Tacoma Dark Sky',
            latitude=47.2529,
            longitude=-122.4443,
            added_by=cls.user
        )

        # ~200km from Seattle
        cls.portland = Location.objects.create(
            name='Portland Viewpoint',
            latitude=45.5152,
            longitude=-122.6784,
            added_by=cls.user
        )

    def setUp(self):
        """Set up API client."""
        self.client = APIClient()

    @skipUnlessDBFeature('has_geometry_columns')
    def test_list_no_distance_filter(self):
        """GET /api/locations/ returns all locations without distance field."""
        response = self.client.get('/api/locations/')

        self.assertEqual(response.status_code, 200)
        results = response.json().get('results', response.json())

        # All locations returned
        self.assertEqual(len(results), 3)

        # Distance field should be null when no filter
        for loc in results:
            self.assertIsNone(loc.get('distance'))

    @skipUnlessDBFeature('has_geometry_columns')
    def test_list_with_distance_filter_default_radius(self):
        """GET /api/locations/?near=lat,lng uses default 50mi radius."""
        response = self.client.get(
            f'/api/locations/?near={self.seattle_lat},{self.seattle_lng}'
        )

        self.assertEqual(response.status_code, 200)
        results = response.json().get('results', response.json())

        # 50mi (~80km) should include Bellevue and Tacoma
        location_names = [loc['name'] for loc in results]
        self.assertIn('Bellevue Observatory', location_names)
        self.assertIn('Tacoma Dark Sky', location_names)
        self.assertNotIn('Portland Viewpoint', location_names)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_list_with_custom_radius(self):
        """GET /api/locations/?near=lat,lng&radius=25 uses custom radius."""
        response = self.client.get(
            f'/api/locations/?near={self.seattle_lat},{self.seattle_lng}&radius=25'
        )

        self.assertEqual(response.status_code, 200)
        results = response.json().get('results', response.json())

        # 25mi (~40km) should only include Bellevue
        location_names = [loc['name'] for loc in results]
        self.assertIn('Bellevue Observatory', location_names)
        self.assertNotIn('Tacoma Dark Sky', location_names)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_distance_field_present_with_filter(self):
        """Distance field is present when distance filter is active."""
        response = self.client.get(
            f'/api/locations/?near={self.seattle_lat},{self.seattle_lng}'
        )

        self.assertEqual(response.status_code, 200)
        results = response.json().get('results', response.json())

        # All results should have distance field
        for loc in results:
            self.assertIsNotNone(loc.get('distance'))

    @skipUnlessDBFeature('has_geometry_columns')
    def test_distance_in_kilometers(self):
        """Distance is returned in kilometers."""
        response = self.client.get(
            f'/api/locations/?near={self.seattle_lat},{self.seattle_lng}'
        )

        self.assertEqual(response.status_code, 200)
        results = response.json().get('results', response.json())

        # Find Bellevue (should be ~10km away)
        bellevue = next((loc for loc in results if 'Bellevue' in loc['name']), None)
        self.assertIsNotNone(bellevue)

        # Distance should be approximately 10km (allow 8-15km range)
        self.assertGreater(bellevue['distance'], 8)
        self.assertLess(bellevue['distance'], 15)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_sort_by_distance(self):
        """GET /api/locations/?near=lat,lng&sort=distance orders nearest first."""
        response = self.client.get(
            f'/api/locations/?near={self.seattle_lat},{self.seattle_lng}&radius=150&sort=distance'
        )

        self.assertEqual(response.status_code, 200)
        results = response.json().get('results', response.json())

        # Should be ordered by distance: Bellevue, Tacoma, Portland
        self.assertEqual(results[0]['name'], 'Bellevue Observatory')
        self.assertEqual(results[1]['name'], 'Tacoma Dark Sky')
        # Portland at ~200km is outside 150mi range

    @skipUnlessDBFeature('has_geometry_columns')
    def test_map_geojson_endpoint(self):
        """GET /api/locations/map_geojson/ returns valid GeoJSON."""
        response = self.client.get('/api/locations/map_geojson/')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Valid GeoJSON structure
        self.assertEqual(data['type'], 'FeatureCollection')
        self.assertIn('features', data)

        # All locations included
        self.assertEqual(len(data['features']), 3)

        # Each feature has valid geometry
        for feature in data['features']:
            self.assertEqual(feature['type'], 'Feature')
            self.assertEqual(feature['geometry']['type'], 'Point')
            self.assertEqual(len(feature['geometry']['coordinates']), 2)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_map_geojson_with_bbox(self):
        """GET /api/locations/map_geojson/?bbox=... filters by bounding box."""
        # Bounding box around Seattle area (should include Bellevue and exclude others)
        bbox = '-122.5,47.5,-122.0,47.7'  # west,south,east,north

        response = self.client.get(f'/api/locations/map_geojson/?bbox={bbox}')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Only Bellevue should be in this tight bbox
        names = [f['properties']['name'] for f in data['features']]
        self.assertIn('Bellevue Observatory', names)
        # Tacoma and Portland are outside this bbox

    @skipUnlessDBFeature('has_geometry_columns')
    def test_create_location_syncs_coordinates(self):
        """POST /api/locations/ creates location with synced coordinates."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/locations/', {
            'name': 'New Test Location',
            'latitude': 48.0,
            'longitude': -123.0,
            'location_type': 'viewpoint'
        })

        self.assertEqual(response.status_code, 201)

        # Verify coordinates were synced
        location = Location.objects.get(name='New Test Location')
        self.assertIsNotNone(location.coordinates)
        self.assertAlmostEqual(location.coordinates.x, -123.0, places=4)
        self.assertAlmostEqual(location.coordinates.y, 48.0, places=4)

    @skipUnlessDBFeature('has_geometry_columns')
    def test_invalid_near_parameter(self):
        """Invalid near parameter is ignored gracefully."""
        response = self.client.get('/api/locations/?near=invalid')

        self.assertEqual(response.status_code, 200)
        # Should return all locations without filtering
        results = response.json().get('results', response.json())
        self.assertEqual(len(results), 3)


if __name__ == '__main__':
    import unittest
    unittest.main()
