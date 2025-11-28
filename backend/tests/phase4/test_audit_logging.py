"""
Comprehensive test suite for audit logging functionality (Phase 4 - Task 4.2).

This test suite verifies that security-relevant events are properly logged to both
the database (AuditLog model) and log file (logs/audit.log).

Test Coverage:
- Configuration verification
- Registration logging
- Login success logging
- Login failure logging
- Logout logging
- Password reset logging
- Database storage verification
- Log file writing verification
- IP address extraction
- Metadata storage

Run with: djvenv/bin/python .claude/tests/phase4/test_audit_logging.py
"""

import os
import sys
import json
import unittest
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
from starview_app.models import AuditLog
from django.urls import reverse


class AuditLoggingTestCase(unittest.TestCase):
    """Test audit logging for security events."""

    def setUp(self):
        """Set up test client and clean database."""
        self.client = Client()

        # Clean up any existing test data
        User.objects.filter(username__startswith='audit_test_').delete()
        AuditLog.objects.all().delete()

        # Create a test user for login tests
        self.test_user = User.objects.create_user(
            username='audit_test_user',
            email='audit_test@example.com',
            password='TestPassword123!',
            first_name='Audit',
            last_name='Test'
        )

    def tearDown(self):
        """Clean up test data."""
        User.objects.filter(username__startswith='audit_test_').delete()
        AuditLog.objects.all().delete()

    def test_1_audit_logger_configuration(self):
        """Test 1: Verify audit logger is properly configured."""
        print("\n" + "="*80)
        print("TEST 1: Audit Logger Configuration")
        print("="*80)

        import logging
        from django.conf import settings

        # Check logging configuration exists
        self.assertIn('LOGGING', dir(settings), "LOGGING configuration missing")
        self.assertIn('audit', settings.LOGGING['loggers'], "Audit logger not configured")

        # Check audit logger has correct handlers
        audit_logger_config = settings.LOGGING['loggers']['audit']
        self.assertIn('audit_file', audit_logger_config['handlers'], "Audit file handler missing")
        self.assertIn('console', audit_logger_config['handlers'], "Console handler missing")

        # Check log file path exists
        log_file = settings.LOGS_DIR / 'audit.log'
        self.assertTrue(log_file.exists(), f"Audit log file doesn't exist: {log_file}")

        print("✅ Audit logger configuration verified")
        print(f"   - Logger 'audit' found with handlers: {audit_logger_config['handlers']}")
        print(f"   - Log file exists: {log_file}")

    def test_2_registration_logging(self):
        """Test 2: Verify registration events are logged."""
        print("\n" + "="*80)
        print("TEST 2: Registration Logging")
        print("="*80)

        # Register a new user
        response = self.client.post(reverse('register'), {
            'username': 'audit_test_newuser',
            'email': 'audit_test_new@example.com',
            'password1': 'NewPassword123!',
            'password2': 'NewPassword123!',
            'first_name': 'New',
            'last_name': 'User'
        })

        # Check response
        self.assertIn(response.status_code, [200, 201], f"Registration failed: {response.status_code}")

        # Check audit log was created
        audit_logs = AuditLog.objects.filter(event_type='registration_success')
        self.assertGreater(audit_logs.count(), 0, "No registration audit log found")

        # Verify log details
        log = audit_logs.latest('timestamp')
        self.assertEqual(log.event_type, 'registration_success')
        self.assertEqual(log.username, 'audit_test_newuser')
        self.assertTrue(log.success)
        self.assertIn('audit_test_new@example.com', log.metadata.get('email', ''))
        self.assertIsNotNone(log.ip_address)

        print("✅ Registration logging verified")
        print(f"   - Event type: {log.event_type}")
        print(f"   - Username: {log.username}")
        print(f"   - Success: {log.success}")
        print(f"   - IP address: {log.ip_address}")
        print(f"   - Metadata: {log.metadata}")

    def test_3_login_success_logging(self):
        """Test 3: Verify successful login events are logged."""
        print("\n" + "="*80)
        print("TEST 3: Login Success Logging")
        print("="*80)

        # Clear previous logs
        AuditLog.objects.all().delete()

        # Login with test user
        response = self.client.post(reverse('login'), {
            'username': 'audit_test_user',
            'password': 'TestPassword123!'
        })

        # Check response
        self.assertEqual(response.status_code, 200, f"Login failed: {response.status_code}")

        # Check audit log was created
        audit_logs = AuditLog.objects.filter(event_type='login_success')
        self.assertGreater(audit_logs.count(), 0, "No login success audit log found")

        # Verify log details
        log = audit_logs.latest('timestamp')
        self.assertEqual(log.event_type, 'login_success')
        self.assertEqual(log.username, 'audit_test_user')
        self.assertEqual(log.user, self.test_user)
        self.assertTrue(log.success)
        self.assertEqual(log.metadata.get('auth_method'), 'password')
        self.assertIsNotNone(log.ip_address)

        print("✅ Login success logging verified")
        print(f"   - Event type: {log.event_type}")
        print(f"   - Username: {log.username}")
        print(f"   - User ID: {log.user.id if log.user else None}")
        print(f"   - Success: {log.success}")
        print(f"   - IP address: {log.ip_address}")
        print(f"   - Auth method: {log.metadata.get('auth_method')}")

    def test_4_login_failure_logging(self):
        """Test 4: Verify failed login events are logged."""
        print("\n" + "="*80)
        print("TEST 4: Login Failure Logging")
        print("="*80)

        # Clear previous logs
        AuditLog.objects.all().delete()

        # Attempt login with wrong password
        response = self.client.post(reverse('login'), {
            'username': 'audit_test_user',
            'password': 'WrongPassword123!'
        })

        # Check response (should be unauthorized)
        self.assertEqual(response.status_code, 401, f"Expected 401, got {response.status_code}")

        # Check audit log was created
        audit_logs = AuditLog.objects.filter(event_type='login_failed')
        self.assertGreater(audit_logs.count(), 0, "No login failure audit log found")

        # Verify log details
        log = audit_logs.latest('timestamp')
        self.assertEqual(log.event_type, 'login_failed')
        self.assertEqual(log.username, 'audit_test_user')
        self.assertFalse(log.success)
        self.assertEqual(log.metadata.get('reason'), 'invalid_password')
        self.assertIsNotNone(log.ip_address)

        print("✅ Login failure logging verified")
        print(f"   - Event type: {log.event_type}")
        print(f"   - Username: {log.username}")
        print(f"   - Success: {log.success}")
        print(f"   - Reason: {log.metadata.get('reason')}")
        print(f"   - IP address: {log.ip_address}")

    def test_5_logout_logging(self):
        """Test 5: Verify logout events are logged."""
        print("\n" + "="*80)
        print("TEST 5: Logout Logging")
        print("="*80)

        # First login through the actual view (not test shortcut, because axes requires request)
        self.client.post(reverse('login'), {
            'username': 'audit_test_user',
            'password': 'TestPassword123!'
        })

        # Clear previous logs
        AuditLog.objects.all().delete()

        # Logout
        response = self.client.get(reverse('logout'))

        # Check response (should redirect)
        self.assertIn(response.status_code, [200, 302], f"Logout failed: {response.status_code}")

        # Check audit log was created
        audit_logs = AuditLog.objects.filter(event_type='logout')
        self.assertGreater(audit_logs.count(), 0, "No logout audit log found")

        # Verify log details
        log = audit_logs.latest('timestamp')
        self.assertEqual(log.event_type, 'logout')
        self.assertEqual(log.username, 'audit_test_user')
        self.assertTrue(log.success)
        self.assertIsNotNone(log.ip_address)

        print("✅ Logout logging verified")
        print(f"   - Event type: {log.event_type}")
        print(f"   - Username: {log.username}")
        print(f"   - Success: {log.success}")
        print(f"   - IP address: {log.ip_address}")

    def test_6_database_storage(self):
        """Test 6: Verify audit logs are stored in database with correct fields."""
        print("\n" + "="*80)
        print("TEST 6: Database Storage Verification")
        print("="*80)

        # Create a log entry
        self.client.post(reverse('login'), {
            'username': 'audit_test_user',
            'password': 'TestPassword123!'
        })

        # Get the log from database
        log = AuditLog.objects.filter(event_type='login_success').latest('timestamp')

        # Verify all required fields are populated
        self.assertIsNotNone(log.id, "Log ID is None")
        self.assertIsNotNone(log.event_type, "Event type is None")
        self.assertIsNotNone(log.timestamp, "Timestamp is None")
        self.assertIsNotNone(log.username, "Username is None")
        self.assertIsNotNone(log.ip_address, "IP address is None")
        self.assertIsInstance(log.metadata, dict, "Metadata is not a dict")
        self.assertIsInstance(log.success, bool, "Success is not a boolean")

        print("✅ Database storage verified")
        print(f"   - Log ID: {log.id}")
        print(f"   - Event type: {log.event_type}")
        print(f"   - Timestamp: {log.timestamp}")
        print(f"   - Username: {log.username}")
        print(f"   - IP address: {log.ip_address}")
        print(f"   - User agent: {log.user_agent[:50]}..." if len(log.user_agent) > 50 else f"   - User agent: {log.user_agent}")
        print(f"   - Metadata type: {type(log.metadata)}")
        print(f"   - Success: {log.success}")

    def test_7_log_file_writing(self):
        """Test 7: Verify audit events are written to log file."""
        print("\n" + "="*80)
        print("TEST 7: Log File Writing Verification")
        print("="*80)

        from django.conf import settings

        # Get log file path
        log_file = settings.LOGS_DIR / 'audit.log'

        # Get current file size
        initial_size = log_file.stat().st_size if log_file.exists() else 0

        # Trigger an audit event
        self.client.post(reverse('login'), {
            'username': 'audit_test_user',
            'password': 'TestPassword123!'
        })

        # Check file size increased
        final_size = log_file.stat().st_size
        self.assertGreater(final_size, initial_size, "Log file size didn't increase")

        # Read last line of log file
        with open(log_file, 'r') as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1].strip()
                # Try to parse as JSON
                try:
                    log_data = json.loads(last_line)
                    self.assertIn('event_type', log_data, "Log entry missing event_type")
                    self.assertIn('user', log_data, "Log entry missing user")
                    print("✅ Log file writing verified")
                    print(f"   - File size increased: {initial_size} → {final_size} bytes")
                    print(f"   - Latest log entry: {json.dumps(log_data, indent=2)}")
                except json.JSONDecodeError:
                    # Not JSON format, that's okay - might be verbose format
                    print("✅ Log file writing verified")
                    print(f"   - File size increased: {initial_size} → {final_size} bytes")
                    print(f"   - Latest log entry: {last_line}")

    def test_8_ip_address_extraction(self):
        """Test 8: Verify IP address is correctly extracted from requests."""
        print("\n" + "="*80)
        print("TEST 8: IP Address Extraction")
        print("="*80)

        # Clear previous logs
        AuditLog.objects.all().delete()

        # Login with test user
        self.client.post(reverse('login'), {
            'username': 'audit_test_user',
            'password': 'TestPassword123!'
        })

        # Get the log
        log = AuditLog.objects.filter(event_type='login_success').latest('timestamp')

        # Verify IP address is present and valid
        self.assertIsNotNone(log.ip_address, "IP address is None")
        self.assertNotEqual(log.ip_address, '', "IP address is empty")

        # Check it's a valid IP (should be 127.0.0.1 for test client)
        self.assertIn(log.ip_address, ['127.0.0.1', '::1'], f"Unexpected IP: {log.ip_address}")

        print("✅ IP address extraction verified")
        print(f"   - IP address: {log.ip_address}")
        print(f"   - IP type: IPv4" if log.ip_address == '127.0.0.1' else "   - IP type: IPv6")

    def test_9_metadata_storage(self):
        """Test 9: Verify metadata is correctly stored as JSON."""
        print("\n" + "="*80)
        print("TEST 9: Metadata Storage Verification")
        print("="*80)

        # Clear previous logs
        AuditLog.objects.all().delete()

        # Register a new user (has metadata with email)
        self.client.post(reverse('register'), {
            'username': 'audit_test_metadata',
            'email': 'metadata@example.com',
            'password1': 'MetadataPass123!',
            'password2': 'MetadataPass123!',
            'first_name': 'Meta',
            'last_name': 'Data'
        })

        # Get the log
        log = AuditLog.objects.filter(event_type='registration_success').latest('timestamp')

        # Verify metadata is a dict
        self.assertIsInstance(log.metadata, dict, "Metadata is not a dict")

        # Verify metadata contains expected data
        self.assertIn('email', log.metadata, "Metadata missing 'email' key")
        self.assertEqual(log.metadata['email'], 'metadata@example.com', "Metadata email mismatch")

        print("✅ Metadata storage verified")
        print(f"   - Metadata type: {type(log.metadata)}")
        print(f"   - Metadata content: {json.dumps(log.metadata, indent=2)}")


def run_tests():
    """Run all audit logging tests."""
    print("\n" + "="*80)
    print("AUDIT LOGGING TEST SUITE - PHASE 4 (Task 4.2)")
    print("="*80)
    print(f"Project: Star View")
    print(f"Test file: {__file__}")
    print(f"Django settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print("="*80)

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(AuditLoggingTestCase)

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
        print("✅ ALL TESTS PASSED! Audit logging implementation is working correctly.")
        return 0
    else:
        print("❌ SOME TESTS FAILED. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
