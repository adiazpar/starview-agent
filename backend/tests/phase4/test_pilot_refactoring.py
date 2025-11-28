"""
Quick test for pilot refactoring of views_location.py (Phase 4 - Task 4.1).

This test verifies that the refactored report endpoint:
1. Returns consistent error format (using exception handler)
2. Still validates correctly (self-report, duplicate report)
3. Successfully creates reports

Run with: djvenv/bin/python .claude/tests/phase4/test_pilot_refactoring.py
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from starview_app.models import Location, Report

print("\n" + "="*80)
print("PILOT REFACTORING TEST - views_location.py")
print("="*80)

# Setup
client = Client()

# Clean up test data
User.objects.filter(username__startswith='pilot_test_').delete()
Location.objects.filter(name__startswith='Pilot Test Location').delete()
Report.objects.filter(reported_by__username__startswith='pilot_test_').delete()

# Create test users
user1 = User.objects.create_user(
    username='pilot_test_user1',
    email='pilot1@test.com',
    password='TestPass123!'
)

user2 = User.objects.create_user(
    username='pilot_test_user2',
    email='pilot2@test.com',
    password='TestPass123!'
)

# Create test location
location = Location.objects.create(
    name='Pilot Test Location',
    latitude=40.7128,
    longitude=-74.0060,
    added_by=user1
)

print(f"\n✓ Test setup complete")
print(f"  - Created users: pilot_test_user1, pilot_test_user2")
print(f"  - Created location: {location.name} (ID: {location.id})")

# Test 1: Self-report validation (should fail with ValidationError)
print("\n" + "-"*80)
print("TEST 1: Attempt to report own location (should fail)")
print("-"*80)

# Login via POST (required for django-axes)
client.post('/login/', {
    'username': 'pilot_test_user1',
    'password': 'TestPass123!'
})

response = client.post(
    f'/api/locations/{location.id}/report/',
    {'report_type': 'SPAM', 'description': 'Test report'},
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 400, f"Expected 400, got {response.status_code}"
assert 'error_code' in response.json(), "Missing error_code in response"
assert response.json()['error_code'] == 'VALIDATION_ERROR', f"Expected VALIDATION_ERROR, got {response.json()['error_code']}"
assert 'own content' in response.json()['detail'].lower(), "Expected 'own content' message"

print("✅ Self-report validation works correctly")
print(f"   - Status: 400")
print(f"   - Error code: {response.json()['error_code']}")
print(f"   - Message: {response.json()['detail']}")

# Test 2: Valid report (should succeed)
print("\n" + "-"*80)
print("TEST 2: Submit valid report from different user (should succeed)")
print("-"*80)

# Logout and login as user2
client.get('/logout/')
client.post('/login/', {
    'username': 'pilot_test_user2',
    'password': 'TestPass123!'
})

response = client.post(
    f'/api/locations/{location.id}/report/',
    {'report_type': 'INAPPROPRIATE', 'description': 'Test report from user2'},
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 201, f"Expected 201, got {response.status_code}"
assert 'detail' in response.json(), "Missing detail in response"
assert 'reported successfully' in response.json()['detail'].lower(), "Expected success message"

# Verify report was created
report_count = Report.objects.filter(
    object_id=location.id,
    reported_by=user2
).count()
assert report_count == 1, f"Expected 1 report, found {report_count}"

# Verify location times_reported was incremented
location.refresh_from_db()
assert location.times_reported == 1, f"Expected times_reported=1, got {location.times_reported}"

print("✅ Valid report submission works correctly")
print(f"   - Status: 201")
print(f"   - Message: {response.json()['detail']}")
print(f"   - Report created in database: Yes")
print(f"   - Location times_reported incremented: Yes ({location.times_reported})")

# Test 3: Duplicate report (should fail with ValidationError)
print("\n" + "-"*80)
print("TEST 3: Attempt duplicate report (should fail)")
print("-"*80)

response = client.post(
    f'/api/locations/{location.id}/report/',
    {'report_type': 'SPAM', 'description': 'Duplicate report attempt'},
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 400, f"Expected 400, got {response.status_code}"
assert 'error_code' in response.json(), "Missing error_code in response"
assert response.json()['error_code'] == 'VALIDATION_ERROR', f"Expected VALIDATION_ERROR, got {response.json()['error_code']}"
assert 'already reported' in response.json()['detail'].lower(), "Expected 'already reported' message"

print("✅ Duplicate report validation works correctly")
print(f"   - Status: 400")
print(f"   - Error code: {response.json()['error_code']}")
print(f"   - Message: {response.json()['detail']}")

# Cleanup
print("\n" + "-"*80)
print("Cleaning up test data...")
print("-"*80)

User.objects.filter(username__startswith='pilot_test_').delete()
Location.objects.filter(name__startswith='Pilot Test Location').delete()
Report.objects.filter(reported_by__username__startswith='pilot_test_').delete()

print("✓ Cleanup complete")

# Summary
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print("✅ ALL 3 TESTS PASSED!")
print()
print("Pilot refactoring validated:")
print("  ✓ Exception handler catches ValidationErrors")
print("  ✓ Consistent error format (error_code, detail, status_code)")
print("  ✓ Business logic still works correctly")
print("  ✓ No ResponseService needed - exceptions work perfectly")
print("="*80)
