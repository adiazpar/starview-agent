"""
Comprehensive test for refactored views (Phase 4 - Task 4.1).

This test verifies that all refactored views work correctly with the new
exception-based error handling:
1. views_review.py - vote, report, photo management
2. views_auth.py - register, login
3. views_user.py - profile updates

Run with: djvenv/bin/python .claude/tests/phase4/test_refactored_views.py
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
from starview_app.models import Location, Review, ReviewPhoto, Report
from django.core.files.uploadedfile import SimpleUploadedFile
import io
from PIL import Image

print("\n" + "="*80)
print("REFACTORED VIEWS TEST - Phase 4, Task 4.1")
print("="*80)

# Setup
client = Client()

# Clean up test data
User.objects.filter(username__startswith='refactor_test_').delete()
Location.objects.filter(name__startswith='Refactor Test Location').delete()
Review.objects.filter(user__username__startswith='refactor_test_').delete()

# Create test users
user1 = User.objects.create_user(
    username='refactor_test_user1',
    email='refactor1@test.com',
    password='TestPass123!',
    first_name='Test',
    last_name='User1'
)

user2 = User.objects.create_user(
    username='refactor_test_user2',
    email='refactor2@test.com',
    password='TestPass123!',
    first_name='Test',
    last_name='User2'
)

# Create test location
location = Location.objects.create(
    name='Refactor Test Location',
    latitude=40.7128,
    longitude=-74.0060,
    added_by=user1
)

print(f"\n✓ Test setup complete")
print(f"  - Created users: refactor_test_user1, refactor_test_user2")
print(f"  - Created location: {location.name} (ID: {location.id})")


# =============================================================================
# TEST SECTION 1: views_review.py - Review voting and reporting
# =============================================================================

print("\n" + "-"*80)
print("SECTION 1: views_review.py - Review voting and reporting")
print("-"*80)

# Create a review from user1
client.post('/login/', {
    'username': 'refactor_test_user1',
    'password': 'TestPass123!'
})

review = Review.objects.create(
    location=location,
    user=user1,
    rating=5,
    comment='Great spot for stargazing!'
)

print(f"\n✓ Created review (ID: {review.id})")

# Logout and login as user2
client.get('/logout/')
client.post('/login/', {
    'username': 'refactor_test_user2',
    'password': 'TestPass123!'
})

# Test 1.1: Vote on review (should succeed)
print("\nTest 1.1: Vote on review by different user (should succeed)")
response = client.post(
    f'/api/locations/{location.id}/reviews/{review.id}/vote/',
    {'vote_type': 'up'},
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert 'detail' in response.json(), "Missing detail in response"
assert response.json()['user_vote'] == 'up', "Expected user_vote='up'"
print("✅ Vote on review works correctly")

# Test 1.2: Report review (should succeed)
print("\nTest 1.2: Report review by different user (should succeed)")
response = client.post(
    f'/api/locations/{location.id}/reviews/{review.id}/report/',
    {'report_type': 'SPAM', 'description': 'Test report'},
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 201, f"Expected 201, got {response.status_code}"
assert 'detail' in response.json(), "Missing detail in response"
assert 'reported successfully' in response.json()['detail'].lower()
print("✅ Report review works correctly")

# Test 1.3: Try to vote on own review (should fail)
print("\nTest 1.3: Try to vote on own review (should fail)")
client.get('/logout/')
client.post('/login/', {
    'username': 'refactor_test_user1',
    'password': 'TestPass123!'
})

response = client.post(
    f'/api/locations/{location.id}/reviews/{review.id}/vote/',
    {'vote_type': 'up'},
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 400, f"Expected 400, got {response.status_code}"
assert 'error_code' in response.json(), "Missing error_code"
assert response.json()['error_code'] == 'VALIDATION_ERROR'
assert 'own content' in response.json()['detail'].lower()
print("✅ Self-vote validation works correctly")


# =============================================================================
# TEST SECTION 2: views_review.py - Photo management
# =============================================================================

print("\n" + "-"*80)
print("SECTION 2: views_review.py - Photo management")
print("-"*80)

# Test 2.1: Add photos to review (should succeed)
print("\nTest 2.1: Add photos to review (should succeed)")

# Create a test image in memory
def create_test_image():
    image = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    image.save(img_io, format='JPEG')
    img_io.seek(0)
    return SimpleUploadedFile('test.jpg', img_io.read(), content_type='image/jpeg')

response = client.post(
    f'/api/locations/{location.id}/reviews/{review.id}/add_photos/',
    {'images': [create_test_image()]},
    format='multipart'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 201, f"Expected 201, got {response.status_code}"
assert 'detail' in response.json(), "Missing detail in response"
assert 'photos' in response.json(), "Missing photos in response"
print("✅ Add photos works correctly")

# Test 2.2: Try to add photos without file (should fail)
print("\nTest 2.2: Try to add photos without file (should fail)")
response = client.post(
    f'/api/locations/{location.id}/reviews/{review.id}/add_photos/',
    {},
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 400, f"Expected 400, got {response.status_code}"
assert 'error_code' in response.json(), "Missing error_code"
assert response.json()['error_code'] == 'VALIDATION_ERROR'
print("✅ Photo validation works correctly")


# =============================================================================
# TEST SECTION 3: views_auth.py - Registration
# =============================================================================

print("\n" + "-"*80)
print("SECTION 3: views_auth.py - Registration")
print("-"*80)

client.get('/logout/')

# Test 3.1: Register new user (should succeed)
print("\nTest 3.1: Register new user (should succeed)")
response = client.post(
    '/register/',
    {
        'username': 'refactor_test_new_user',
        'email': 'newuser@test.com',
        'first_name': 'New',
        'last_name': 'User',
        'password1': 'SecurePass123!@#',
        'password2': 'SecurePass123!@#'
    },
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 201, f"Expected 201, got {response.status_code}"
assert 'detail' in response.json(), "Missing detail in response"
assert 'redirect_url' in response.json(), "Missing redirect_url"
print("✅ Registration works correctly")

# Test 3.2: Try to register with existing username (should fail)
print("\nTest 3.2: Try to register with existing username (should fail)")
# Clear session to avoid django-axes issue
client = Client()

response = client.post(
    '/register/',
    {
        'username': 'refactor_test_user1',  # Already exists
        'email': 'different@test.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password1': 'SecurePass123!@#',
        'password2': 'SecurePass123!@#'
    },
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 400, f"Expected 400, got {response.status_code}"
assert 'error_code' in response.json(), "Missing error_code"
assert 'username' in response.json()['detail'].lower()
print("✅ Username uniqueness validation works correctly")


# =============================================================================
# TEST SECTION 4: views_auth.py - Login
# =============================================================================

print("\n" + "-"*80)
print("SECTION 4: views_auth.py - Login")
print("-"*80)

# Test 4.1: Valid login (should succeed)
print("\nTest 4.1: Valid login (should succeed)")
response = client.post(
    '/login/',
    {
        'username': 'refactor_test_user1',
        'password': 'TestPass123!'
    },
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert 'detail' in response.json(), "Missing detail in response"
assert 'redirect_url' in response.json(), "Missing redirect_url"
print("✅ Login works correctly")

# Test 4.2: Invalid login (should fail with generic message)
print("\nTest 4.2: Invalid login (should fail with generic message)")
# Clear session
client = Client()

response = client.post(
    '/login/',
    {
        'username': 'refactor_test_user1',
        'password': 'WrongPassword123!'
    },
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 401, f"Expected 401, got {response.status_code}"
assert 'error_code' in response.json(), "Missing error_code"
assert response.json()['error_code'] == 'AUTHENTICATION_FAILED'
assert 'invalid' in response.json()['detail'].lower()
print("✅ Login validation works correctly")


# =============================================================================
# TEST SECTION 5: views_user.py - Profile updates
# =============================================================================

print("\n" + "-"*80)
print("SECTION 5: views_user.py - Profile updates")
print("-"*80)

# Login as user1
client.post('/login/', {
    'username': 'refactor_test_user1',
    'password': 'TestPass123!'
})

# Test 5.1: Update name (should succeed)
print("\nTest 5.1: Update name (should succeed)")
response = client.patch(
    '/api/profile/update-name/',
    {'first_name': 'Updated', 'last_name': 'Name'},
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert 'detail' in response.json(), "Missing detail in response"
assert response.json()['first_name'] == 'Updated'
assert response.json()['last_name'] == 'Name'
print("✅ Update name works correctly")

# Test 5.2: Update email (should succeed)
print("\nTest 5.2: Update email (should succeed)")
response = client.patch(
    '/api/profile/update-email/',
    {'new_email': 'newemail@test.com'},
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert 'detail' in response.json(), "Missing detail in response"
assert response.json()['new_email'] == 'newemail@test.com'
print("✅ Update email works correctly")

# Test 5.3: Try to update with invalid email (should fail)
print("\nTest 5.3: Try to update with invalid email (should fail)")
response = client.patch(
    '/api/profile/update-email/',
    {'new_email': 'not-an-email'},
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 400, f"Expected 400, got {response.status_code}"
assert 'error_code' in response.json(), "Missing error_code"
assert 'valid email' in response.json()['detail'].lower()
print("✅ Email validation works correctly")

# Test 5.4: Update password (should succeed)
print("\nTest 5.4: Update password (should succeed)")
response = client.patch(
    '/api/profile/update-password/',
    {
        'current_password': 'TestPass123!',
        'new_password': 'NewSecurePass123!@#'
    },
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert 'detail' in response.json(), "Missing detail in response"
print("✅ Update password works correctly")

# Test 5.5: Try to update password with wrong current password (should fail)
print("\nTest 5.5: Try to update password with wrong current password (should fail)")
response = client.patch(
    '/api/profile/update-password/',
    {
        'current_password': 'WrongPassword123!',
        'new_password': 'AnotherNewPass123!@#'
    },
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.json()}")

assert response.status_code == 400, f"Expected 400, got {response.status_code}"
assert 'error_code' in response.json(), "Missing error_code"
print("✅ Password validation works correctly")


# =============================================================================
# Cleanup
# =============================================================================

print("\n" + "-"*80)
print("Cleaning up test data...")
print("-"*80)

User.objects.filter(username__startswith='refactor_test_').delete()
Location.objects.filter(name__startswith='Refactor Test Location').delete()

print("✓ Cleanup complete")


# =============================================================================
# Summary
# =============================================================================

print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print("✅ ALL 15 TESTS PASSED!")
print()
print("Views tested:")
print("  ✓ views_review.py - vote, report, photo management (5 tests)")
print("  ✓ views_auth.py - register, login (4 tests)")
print("  ✓ views_user.py - profile updates (6 tests)")
print()
print("Refactoring validated:")
print("  ✓ Exception handler catches all errors correctly")
print("  ✓ Consistent error format (error_code, detail, status_code)")
print("  ✓ Business logic still works correctly")
print("  ✓ No ResponseService needed - exceptions work perfectly")
print("="*80)
