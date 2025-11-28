"""
Test Suite for Account Lockout Policy (django-axes - Phase 4, Item 1)

Tests the account lockout functionality to prevent brute force attacks.
Verifies that accounts are locked after excessive failed login attempts
and that lockouts work across different IP addresses (distributed attack protection).

IMPORTANT: Run this test standalone:
    djvenv/bin/python .claude/tests/phase4/test_account_lockout.py

Test Coverage:
1. django-axes configuration verification
2. Account lockout after 5 failed attempts
3. Lockout persists across different IP addresses (CRITICAL for distributed attack protection)
4. Successful login resets failure counter
5. Access Failure logging
"""

import os
import sys
import json
from datetime import timedelta

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

import django
django.setup()

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from axes.models import AccessAttempt, AccessFailureLog
from axes.utils import reset


class AccountLockoutTestCase(TestCase):
    """Test case for django-axes account lockout functionality."""

    def setUp(self):
        """Set up test data before each test."""
        # Clear any existing axes data
        AccessAttempt.objects.all().delete()
        AccessFailureLog.objects.all().delete()
        reset()

        # Clear Redis cache to reset DRF throttling counters
        cache.clear()

        # Create test user
        self.username = 'lockout_test_user'
        self.email = 'lockout@test.com'
        self.password = 'correct_password123!'

        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password
        )

        # Create client for making requests
        self.client = Client()
        self.login_url = reverse('login')

    def tearDown(self):
        """Clean up test data after each test."""
        User.objects.filter(username=self.username).delete()
        AccessAttempt.objects.all().delete()
        AccessFailureLog.objects.all().delete()
        reset()

    def _login_post(self, username, password, remote_addr=None):
        """Helper method to make login POST request with proper JSON format."""
        kwargs = {
            'data': json.dumps({'username': username, 'password': password}),
            'content_type': 'application/json'
        }
        if remote_addr:
            kwargs['REMOTE_ADDR'] = remote_addr
        return self.client.post(self.login_url, **kwargs)

    def test_axes_configuration(self):
        """Test 1: Verify django-axes configuration."""
        print("\n" + "="*80)
        print("TEST 1: Verify django-axes Configuration")
        print("="*80)

        # Check AXES_FAILURE_LIMIT
        self.assertTrue(hasattr(settings, 'AXES_FAILURE_LIMIT'))
        self.assertEqual(settings.AXES_FAILURE_LIMIT, 5)
        print(f"✅ AXES_FAILURE_LIMIT = {settings.AXES_FAILURE_LIMIT}")

        # Check AXES_COOLOFF_TIME
        self.assertTrue(hasattr(settings, 'AXES_COOLOFF_TIME'))
        self.assertEqual(settings.AXES_COOLOFF_TIME, timedelta(hours=1))
        print(f"✅ AXES_COOLOFF_TIME = {settings.AXES_COOLOFF_TIME}")

        # Check AXES_LOCKOUT_PARAMETERS
        self.assertTrue(hasattr(settings, 'AXES_LOCKOUT_PARAMETERS'))
        self.assertEqual(settings.AXES_LOCKOUT_PARAMETERS, ['username'])
        print(f"✅ AXES_LOCKOUT_PARAMETERS = {settings.AXES_LOCKOUT_PARAMETERS}")

        # Check AXES_RESET_ON_SUCCESS
        self.assertTrue(hasattr(settings, 'AXES_RESET_ON_SUCCESS'))
        self.assertTrue(settings.AXES_RESET_ON_SUCCESS)
        print(f"✅ AXES_RESET_ON_SUCCESS = {settings.AXES_RESET_ON_SUCCESS}")

        # Check authentication backend
        self.assertIn('axes.backends.AxesStandaloneBackend', settings.AUTHENTICATION_BACKENDS)
        print("✅ AxesStandaloneBackend configured in AUTHENTICATION_BACKENDS")

        # Check middleware
        self.assertIn('axes.middleware.AxesMiddleware', settings.MIDDLEWARE)
        print("✅ AxesMiddleware configured in MIDDLEWARE")

        print("✅ All configuration settings verified")

    @override_settings(
        AXES_ENABLED=True,
        ALLOWED_HOSTS=['*'],  # Allow testserver
        # Disable DRF throttling for this test to isolate django-axes behavior
        REST_FRAMEWORK={
            **settings.REST_FRAMEWORK,
            'DEFAULT_THROTTLE_CLASSES': [],
            'DEFAULT_THROTTLE_RATES': {},
        }
    )
    def test_account_lockout_after_failures(self):
        """Test 2: Account locks after 5 failed login attempts."""
        print("\n" + "="*80)
        print("TEST 2: Account Lockout After 5 Failed Attempts")
        print("="*80)

        print("ℹ️  Making 5 failed login attempts...")

        # Make 5 failed login attempts
        for i in range(1, 6):
            response = self._login_post(self.username, 'wrong_password')

            if i < 5:
                # First 4 attempts should return 401 (invalid credentials)
                self.assertEqual(response.status_code, 401,
                    f"Attempt {i}: Expected 401, got {response.status_code}")
                print(f"✅ Attempt {i}/5: Failed login (401) - counter incremented")
            else:
                # 5th attempt should trigger lockout (403)
                self.assertEqual(response.status_code, 403,
                    f"Attempt {i}: Expected 403 (lockout), got {response.status_code}")
                print(f"✅ Attempt {i}/5: Account locked (403)")

        # Verify lockout persists even with correct password
        print("ℹ️  Attempting 6th login with CORRECT password (should still be blocked)...")
        response = self._login_post(self.username, self.password)

        self.assertEqual(response.status_code, 403,
            f"Expected lockout with correct password, got {response.status_code}")
        print("✅ 6th attempt blocked (even with correct password)")

        # Verify AccessFailureLog or AccessAttempt entries exist
        # django-axes may use either model depending on configuration
        failure_logs = AccessFailureLog.objects.filter(username=self.username)
        access_attempts = AccessAttempt.objects.filter(username=self.username)

        has_logs = failure_logs.exists() or access_attempts.exists()
        self.assertTrue(has_logs, f"No failure logs found in database. FailureLog count: {failure_logs.count()}, AccessAttempt count: {access_attempts.count()}")

        log_count = max(failure_logs.count(), access_attempts.count())
        self.assertGreaterEqual(log_count, 1,
            f"Expected at least 1 log entry, found {log_count}")
        print(f"✅ Failure logs recorded: {log_count} entries")

        print("✅ Account lockout test PASSED")

    @override_settings(
        AXES_ENABLED=True,
        ALLOWED_HOSTS=['*'],
        REST_FRAMEWORK={
            **settings.REST_FRAMEWORK,
            'DEFAULT_THROTTLE_CLASSES': [],
            'DEFAULT_THROTTLE_RATES': {},
        }
    )
    def test_lockout_across_different_ips(self):
        """Test 3: CRITICAL - Lockout persists across different IP addresses (distributed attack protection)."""
        print("\n" + "="*80)
        print("TEST 3: Lockout Across Different IPs (Distributed Attack Protection)")
        print("="*80)
        print("ℹ️  This is CRITICAL - protects against distributed brute force attacks")

        # Simulate attacks from 3 different IP addresses
        ip_addresses = ['192.168.1.100', '10.0.0.50', '172.16.0.200']

        print(f"ℹ️  Simulating attacks from {len(ip_addresses)} different IPs...")

        # First 2 failed attempts from IP #1
        print(f"\n📍 IP #1: {ip_addresses[0]}")
        for i in range(1, 3):
            response = self._login_post(self.username, 'wrong_password', ip_addresses[0])
            self.assertEqual(response.status_code, 401,
                f"IP #1, Attempt {i}: Expected 401, got {response.status_code}")
            print(f"  ✅ Attempt {i}/2 from IP #1: Failed (401)")

        # Next 2 failed attempts from IP #2
        print(f"\n📍 IP #2: {ip_addresses[1]}")
        for i in range(1, 3):
            response = self._login_post(self.username, 'wrong_password', ip_addresses[1])
            self.assertEqual(response.status_code, 401,
                f"IP #2, Attempt {i}: Expected 401, got {response.status_code}")
            print(f"  ✅ Attempt {i}/2 from IP #2: Failed (401)")

        # 5th attempt from IP #3 should trigger lockout
        print(f"\n📍 IP #3: {ip_addresses[2]}")
        print("  ℹ️  This is the 5th failed attempt overall (should trigger lockout)")
        response = self._login_post(self.username, 'wrong_password', ip_addresses[2])
        self.assertEqual(response.status_code, 403,
            f"IP #3, 5th attempt total: Expected 403 (lockout), got {response.status_code}")
        print(f"  ✅ Attempt 5 (total) from IP #3: LOCKED (403)")

        # CRITICAL TEST: Try from a 4th IP with CORRECT password - should still be locked
        print(f"\n📍 IP #4: 203.0.113.1 (NEW IP with CORRECT password)")
        print("  ⚠️  CRITICAL: Account should be locked even from new IP")
        response = self._login_post(self.username, self.password, '203.0.113.1')

        self.assertEqual(response.status_code, 403,
            f"Expected lockout from new IP with correct password, got {response.status_code}")
        print("  ✅ Account STILL LOCKED from new IP (even with correct password)")

        print("\n🎯 DISTRIBUTED ATTACK PROTECTION VERIFIED:")
        print("   - Account locked by USERNAME, not by IP")
        print("   - Attacker cannot bypass lockout by switching IPs")
        print("   - Even correct password is blocked during lockout period")
        print("✅ Distributed attack protection test PASSED")

    @override_settings(
        AXES_ENABLED=True,
        ALLOWED_HOSTS=['*'],
        REST_FRAMEWORK={
            **settings.REST_FRAMEWORK,
            'DEFAULT_THROTTLE_CLASSES': [],
            'DEFAULT_THROTTLE_RATES': {},
        }
    )
    def test_successful_login_resets_counter(self):
        """Test 4: Successful login resets the failure counter."""
        print("\n" + "="*80)
        print("TEST 4: Successful Login Resets Failure Counter")
        print("="*80)

        # Make 3 failed attempts (below the 5-attempt threshold)
        print("ℹ️  Making 3 failed login attempts...")
        for i in range(1, 4):
            response = self._login_post(self.username, 'wrong_password')
            self.assertEqual(response.status_code, 401)
            print(f"✅ Failed attempt {i}/3")

        # Verify we're not locked yet by logging in successfully
        print("ℹ️  Attempting successful login after 3 failures...")
        response = self._login_post(self.username, self.password)
        self.assertEqual(response.status_code, 200,
            f"Expected successful login, got {response.status_code}")
        print("✅ Successful login after 3 failures")

        # Logout to test counter reset
        self.client.logout()

        # Counter should be reset - make 4 more failed attempts (should NOT lock)
        print("ℹ️  Making 4 more failed attempts (counter should be reset to 0)...")
        for i in range(1, 5):
            response = self._login_post(self.username, 'wrong_password')
            self.assertEqual(response.status_code, 401,
                f"Attempt {i}: Expected 401, got {response.status_code}")
            print(f"✅ Failed attempt {i}/4 - not locked yet (counter was reset)")

        # 5th failed attempt should trigger lockout
        print("ℹ️  Making 5th failed attempt (should trigger lockout)...")
        response = self._login_post(self.username, 'wrong_password')
        self.assertEqual(response.status_code, 403,
            f"Expected lockout on 5th attempt, got {response.status_code}")
        print("✅ Account locked on 5th attempt after reset")

        print("✅ Counter reset on successful login VERIFIED")

    @override_settings(
        AXES_ENABLED=True,
        ALLOWED_HOSTS=['*'],
        REST_FRAMEWORK={
            **settings.REST_FRAMEWORK,
            'DEFAULT_THROTTLE_CLASSES': [],
            'DEFAULT_THROTTLE_RATES': {},
        }
    )
    def test_lockout_message_and_logging(self):
        """Test 5: Verify lockout response and database logging."""
        print("\n" + "="*80)
        print("TEST 5: Verify Lockout Response and Database Logging")
        print("="*80)

        # Trigger lockout
        print("ℹ️  Triggering lockout with 5 failed attempts...")
        for i in range(5):
            self._login_post(self.username, 'wrong_password')

        # Check lockout response
        print("ℹ️  Checking lockout response...")
        response = self._login_post(self.username, self.password)

        # Verify lockout status code
        self.assertEqual(response.status_code, 403)
        print(f"✅ Lockout status code: 403 Forbidden")

        # Verify response contains error information
        if response.content:
            try:
                response_data = response.json()
                print(f"✅ Lockout response: {response_data}")
            except:
                print(f"✅ Lockout response: {response.text[:100]}")

        # Verify database logging
        print("\nℹ️  Checking database logging...")

        # Check AccessFailureLog or AccessAttempt (django-axes uses different models depending on handler)
        failure_logs = AccessFailureLog.objects.filter(username=self.username)
        access_attempts = AccessAttempt.objects.filter(username=self.username)

        has_logs = failure_logs.exists() or access_attempts.exists()
        self.assertTrue(has_logs, f"No log entries found. FailureLog: {failure_logs.count()}, AccessAttempt: {access_attempts.count()}")

        log_count = max(failure_logs.count(), access_attempts.count())
        print(f"✅ Log entries: {log_count} (FailureLog: {failure_logs.count()}, AccessAttempt: {access_attempts.count()})")

        # Print sample log entry from whichever table has data
        if failure_logs.exists():
            log = failure_logs.first()
            print(f"   - AccessFailureLog entry:")
            print(f"     Username: {log.username}")
            print(f"     Timestamp: {log.attempt_time}")
            print(f"     User agent: {log.user_agent[:50] if log.user_agent else 'N/A'}...")
        elif access_attempts.exists():
            log = access_attempts.first()
            print(f"   - AccessAttempt entry:")
            print(f"     Username: {log.username}")
            print(f"     Failures: {log.failures_since_start}")

        print("✅ Lockout message and logging test PASSED")


def run_tests_standalone():
    """Run tests in standalone mode (without Django's test runner)."""
    import unittest

    print("\n" + "="*80)
    print("ACCOUNT LOCKOUT POLICY TEST SUITE (Phase 4, Item 1)")
    print("Testing django-axes integration for brute force attack prevention")
    print("="*80)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(AccountLockoutTestCase)

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

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests_standalone()
    sys.exit(0 if success else 1)
