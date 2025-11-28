"""
Comprehensive test suite for exception handler functionality (Phase 4 - Task 4.1).

This test suite verifies that the custom exception handler properly catches,
formats, and logs all types of exceptions across the API.

Test Coverage:
- DRF exceptions (ValidationError, NotFound, PermissionDenied, etc.)
- Django exceptions (Http404, PermissionDenied)
- Unexpected exceptions (500 errors)
- Consistent response format
- Audit logging integration
- Application logging
- Production vs development behavior

Run with: djvenv/bin/python .claude/tests/phase4/test_exception_handler.py
"""

import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.views import APIView
from starview_app.models import AuditLog
from starview_app.utils.exception_handler import (
    custom_exception_handler,
    format_drf_exception,
    format_unexpected_exception,
)


class ExceptionHandlerTestCase(unittest.TestCase):
    """Test custom exception handler for consistent error responses."""

    def setUp(self):
        """Set up test client and request factory."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='exception_test_user',
            email='exception_test@example.com',
            password='TestPassword123!'
        )

    def tearDown(self):
        """Clean up test data."""
        User.objects.filter(username__startswith='exception_test_').delete()
        AuditLog.objects.all().delete()

    def test_1_validation_error_format(self):
        """Test 1: ValidationError returns consistent format."""
        print("\n" + "="*80)
        print("TEST 1: ValidationError Format")
        print("="*80)

        exc = exceptions.ValidationError("Invalid data")
        request = self.factory.post('/api/test/')
        context = {'request': request, 'view': None}

        response = custom_exception_handler(exc, context)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', response.data)
        self.assertIn('error_code', response.data)
        self.assertIn('status_code', response.data)
        self.assertEqual(response.data['error_code'], 'VALIDATION_ERROR')
        self.assertEqual(response.data['status_code'], 400)

        print("✅ ValidationError formatted consistently")
        print(f"   - Response data: {response.data}")

    def test_2_authentication_failed_format(self):
        """Test 2: AuthenticationFailed returns consistent format."""
        print("\n" + "="*80)
        print("TEST 2: AuthenticationFailed Format")
        print("="*80)

        exc = exceptions.AuthenticationFailed("Invalid credentials")
        request = self.factory.post('/api/login/')
        context = {'request': request, 'view': None}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['error_code'], 'AUTHENTICATION_FAILED')
        self.assertIn('Invalid credentials', response.data['detail'])

        print("✅ AuthenticationFailed formatted consistently")
        print(f"   - Error code: {response.data['error_code']}")
        print(f"   - Status code: {response.status_code}")

    def test_3_permission_denied_format(self):
        """Test 3: PermissionDenied returns consistent format."""
        print("\n" + "="*80)
        print("TEST 3: PermissionDenied Format")
        print("="*80)

        exc = exceptions.PermissionDenied("You cannot edit this resource")
        request = self.factory.put('/api/reviews/1/')
        request.user = self.user
        context = {'request': request, 'view': None}

        # Clear previous audit logs
        AuditLog.objects.all().delete()

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error_code'], 'PERMISSION_DENIED')

        # Check that permission denial was logged to AuditLog
        audit_logs = AuditLog.objects.filter(user=self.user)
        self.assertGreater(audit_logs.count(), 0, "Permission denial not logged to AuditLog")

        print("✅ PermissionDenied formatted consistently")
        print(f"   - Audit log created: {audit_logs.count()} entries")
        print(f"   - Response: {response.data}")

    def test_4_not_found_format(self):
        """Test 4: NotFound returns consistent format."""
        print("\n" + "="*80)
        print("TEST 4: NotFound Format")
        print("="*80)

        exc = exceptions.NotFound("Resource not found")
        request = self.factory.get('/api/locations/999/')
        context = {'request': request, 'view': None}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error_code'], 'NOT_FOUND')
        self.assertIn('detail', response.data)

        print("✅ NotFound formatted consistently")
        print(f"   - Response: {response.data}")

    def test_5_throttled_format(self):
        """Test 5: Throttled returns consistent format with retry_after."""
        print("\n" + "="*80)
        print("TEST 5: Throttled Format")
        print("="*80)

        exc = exceptions.Throttled(wait=60)
        request = self.factory.post('/api/login/')
        context = {'request': request, 'view': None}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data['error_code'], 'THROTTLED')
        self.assertIn('retry_after', response.data)
        self.assertEqual(response.data['retry_after'], 60)

        print("✅ Throttled formatted consistently")
        print(f"   - Retry after: {response.data['retry_after']} seconds")

    def test_6_django_http404_handling(self):
        """Test 6: Django Http404 is caught and formatted."""
        print("\n" + "="*80)
        print("TEST 6: Django Http404 Handling")
        print("="*80)

        exc = Http404("Page not found")
        request = self.factory.get('/some/path/')
        context = {'request': request, 'view': None}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error_code'], 'NOT_FOUND')
        self.assertEqual(response.data['detail'], 'Resource not found')

        print("✅ Django Http404 handled correctly")
        print(f"   - Response: {response.data}")

    def test_7_django_permission_denied_handling(self):
        """Test 7: Django PermissionDenied is caught and formatted."""
        print("\n" + "="*80)
        print("TEST 7: Django PermissionDenied Handling")
        print("="*80)

        exc = DjangoPermissionDenied("Access denied")
        request = self.factory.post('/api/admin-action/')
        request.user = self.user
        context = {'request': request, 'view': None}

        # Clear previous audit logs
        AuditLog.objects.all().delete()

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error_code'], 'PERMISSION_DENIED')

        # Verify audit logging
        audit_logs = AuditLog.objects.all()
        self.assertGreater(audit_logs.count(), 0)

        print("✅ Django PermissionDenied handled correctly")
        print(f"   - Audit logs created: {audit_logs.count()}")

    def test_8_unexpected_exception_development(self):
        """Test 8: Unexpected exception in development mode shows details."""
        print("\n" + "="*80)
        print("TEST 8: Unexpected Exception (Development)")
        print("="*80)

        exc = ZeroDivisionError("division by zero")
        request = self.factory.get('/api/locations/')
        context = {'request': request, 'view': None}

        with patch('django.conf.settings.DEBUG', True):
            response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['error_code'], 'SERVER_ERROR')
        # In development, should show exception details
        self.assertIn('exception_type', response.data)
        self.assertEqual(response.data['exception_type'], 'ZeroDivisionError')

        print("✅ Unexpected exception in development shows details")
        print(f"   - Exception type exposed: {response.data['exception_type']}")

    def test_9_unexpected_exception_production(self):
        """Test 9: Unexpected exception in production hides details."""
        print("\n" + "="*80)
        print("TEST 9: Unexpected Exception (Production)")
        print("="*80)

        exc = ZeroDivisionError("division by zero")
        request = self.factory.get('/api/locations/')
        context = {'request': request, 'view': None}

        with patch('django.conf.settings.DEBUG', False):
            response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['error_code'], 'SERVER_ERROR')
        # In production, should NOT show exception details
        self.assertNotIn('exception_type', response.data)
        self.assertEqual(response.data['detail'], 'Internal server error. Please try again later.')

        print("✅ Unexpected exception in production hides details")
        print(f"   - Generic message: {response.data['detail']}")

    def test_10_validation_error_with_field_errors(self):
        """Test 10: ValidationError with field-level errors includes 'errors' key."""
        print("\n" + "="*80)
        print("TEST 10: ValidationError with Field Errors")
        print("="*80)

        # Simulate field-level validation errors
        exc = exceptions.ValidationError({
            'username': ['This field is required.'],
            'email': ['Enter a valid email address.']
        })
        request = self.factory.post('/api/register/')
        context = {'request': request, 'view': None}

        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.data)
        self.assertIn('username', response.data['errors'])
        self.assertIn('email', response.data['errors'])

        print("✅ Field-level validation errors included")
        print(f"   - Errors: {response.data['errors']}")

    def test_11_consistent_response_structure(self):
        """Test 11: All error responses have consistent structure."""
        print("\n" + "="*80)
        print("TEST 11: Consistent Response Structure")
        print("="*80)

        test_exceptions = [
            (exceptions.ValidationError("test"), 400),
            (exceptions.AuthenticationFailed("test"), 401),
            (exceptions.PermissionDenied("test"), 403),
            (exceptions.NotFound("test"), 404),
        ]

        request = self.factory.get('/api/test/')
        context = {'request': request, 'view': None}

        for exc, expected_status in test_exceptions:
            response = custom_exception_handler(exc, context)

            # All responses must have these keys
            self.assertIn('detail', response.data)
            self.assertIn('error_code', response.data)
            self.assertIn('status_code', response.data)
            self.assertEqual(response.data['status_code'], expected_status)

        print("✅ All error responses have consistent structure")
        print("   - Keys present in all responses: detail, error_code, status_code")

    def test_12_audit_logging_integration(self):
        """Test 12: Security-relevant errors are logged to AuditLog."""
        print("\n" + "="*80)
        print("TEST 12: Audit Logging Integration")
        print("="*80)

        # Clear audit logs
        AuditLog.objects.all().delete()

        # Test authentication failure
        exc = exceptions.AuthenticationFailed("Invalid credentials")
        request = self.factory.post('/api/login/')
        context = {'request': request, 'view': None}

        response = custom_exception_handler(exc, context)

        # Check audit log was created
        audit_logs = AuditLog.objects.filter(event_type='login_failed')
        self.assertGreater(audit_logs.count(), 0, "Authentication failure not logged")

        print("✅ Security errors logged to AuditLog")
        print(f"   - Audit logs created: {audit_logs.count()}")

        # Test permission denial
        AuditLog.objects.all().delete()

        exc = exceptions.PermissionDenied("Access denied")
        request = self.factory.put('/api/reviews/1/')
        request.user = self.user
        context = {'request': request, 'view': None}

        response = custom_exception_handler(exc, context)

        audit_logs = AuditLog.objects.all()
        self.assertGreater(audit_logs.count(), 0, "Permission denial not logged")

        print(f"   - Permission denials logged: {audit_logs.count()}")


def run_tests():
    """Run all exception handler tests."""
    print("\n" + "="*80)
    print("EXCEPTION HANDLER TEST SUITE - PHASE 4 (Task 4.1)")
    print("="*80)
    print(f"Project: Star View")
    print(f"Test file: {__file__}")
    print(f"Django settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print("="*80)

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(ExceptionHandlerTestCase)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"❌ Errors: {len(result.errors)}")
    print("="*80)

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED! Exception handler is working correctly.")
        return 0
    else:
        print("❌ SOME TESTS FAILED. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
