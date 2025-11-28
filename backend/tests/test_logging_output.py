#!/usr/bin/env python
"""
Test script for verifying proper logging output after replacing print statements.

This script tests:
1. Logger configuration in settings
2. Logging output format (timestamp, level, module, message)
3. Different log levels (DEBUG, INFO, WARNING, ERROR)
4. Structured logging with extra context
5. Verify no print statements remain in production code

Run: djvenv/bin/python .claude/backend/tests/test_logging_output.py
"""

import os
import sys
import django
import logging
import io
from contextlib import redirect_stdout, redirect_stderr

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from starview_app.models import Location, Review, ReviewPhoto, UserProfile
from allauth.account.models import EmailAddress
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile


class TestLogging:
    """Test logging configuration and output"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_results = []

    def log_result(self, test_name, passed, message=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status} - {test_name}"
        if message:
            result += f": {message}"
        self.test_results.append(result)
        print(result)

        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def test_logging_configuration(self):
        """Test Django logging configuration"""
        print("\n" + "="*80)
        print("TEST 1: Django Logging Configuration")
        print("="*80)

        try:
            # Check LOGGING exists
            has_logging_config = hasattr(settings, 'LOGGING')
            self.log_result(
                "LOGGING configuration exists",
                has_logging_config,
                "Found in settings.py" if has_logging_config else "Missing!"
            )

            if has_logging_config:
                logging_config = settings.LOGGING

                # Check formatters
                has_formatters = 'formatters' in logging_config
                self.log_result(
                    "Log formatters configured",
                    has_formatters,
                    f"Found {len(logging_config.get('formatters', {}))} formatter(s)"
                )

                # Check handlers
                has_handlers = 'handlers' in logging_config
                self.log_result(
                    "Log handlers configured",
                    has_handlers,
                    f"Found {len(logging_config.get('handlers', {}))} handler(s)"
                )

                # Check console handler
                has_console = 'console' in logging_config.get('handlers', {})
                self.log_result(
                    "Console handler configured",
                    has_console,
                    "Logs will output to stdout"
                )

                # Check app logger
                has_app_logger = 'starview_app' in logging_config.get('loggers', {})
                self.log_result(
                    "starview_app logger configured",
                    has_app_logger,
                    f"Level: {logging_config.get('loggers', {}).get('starview_app', {}).get('level', 'N/A')}"
                )

        except Exception as e:
            self.log_result("Logging configuration check", False, str(e))

    def test_logger_instances(self):
        """Test that logger instances are properly created in modules"""
        print("\n" + "="*80)
        print("TEST 2: Logger Instance Creation")
        print("="*80)

        modules_to_check = [
            'django_project.settings',
            'django_project.celery',
            'starview_app.models.model_location',
            'starview_app.models.model_review_photo',
            'starview_app.utils.signals',
        ]

        for module_name in modules_to_check:
            try:
                module = __import__(module_name, fromlist=[''])
                has_logger = hasattr(module, 'logger')
                self.log_result(
                    f"Logger in {module_name}",
                    has_logger,
                    "Logger instance found" if has_logger else "Logger missing!"
                )
            except ImportError as e:
                self.log_result(f"Import {module_name}", False, str(e))

    def test_logging_output_format(self):
        """Test logging output format"""
        print("\n" + "="*80)
        print("TEST 3: Logging Output Format")
        print("="*80)

        # Create a string buffer to capture log output
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(logging.Formatter(
            '{levelname} {asctime} {module} {message}',
            style='{'
        ))

        # Add handler to test logger
        test_logger = logging.getLogger('test_logging')
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.DEBUG)

        # Test different log levels
        test_logger.debug("Debug message")
        test_logger.info("Info message")
        test_logger.warning("Warning message")
        test_logger.error("Error message")

        # Get output
        output = log_stream.getvalue()
        lines = output.strip().split('\n')

        # Check format
        has_debug = 'DEBUG' in output
        has_info = 'INFO' in output
        has_warning = 'WARNING' in output
        has_error = 'ERROR' in output

        self.log_result("DEBUG level logging", has_debug, "DEBUG message logged")
        self.log_result("INFO level logging", has_info, "INFO message logged")
        self.log_result("WARNING level logging", has_warning, "WARNING message logged")
        self.log_result("ERROR level logging", has_error, "ERROR message logged")

        # Check format includes module name
        has_module = 'test_logging' in output
        self.log_result("Module name in logs", has_module, "Module names included")

        # Clean up
        test_logger.removeHandler(handler)

    def test_structured_logging(self):
        """Test structured logging with extra context"""
        print("\n" + "="*80)
        print("TEST 4: Structured Logging (extra context)")
        print("="*80)

        # Create a custom handler that captures extra fields
        class ExtraFieldHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []

            def emit(self, record):
                self.records.append(record)

        handler = ExtraFieldHandler()
        test_logger = logging.getLogger('test_structured')
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)

        # Log with extra context
        test_logger.info(
            "Test message with context",
            extra={'user_id': 123, 'action': 'test_action'}
        )

        # Check if extra fields are captured
        has_records = len(handler.records) > 0
        self.log_result("Extra context logging", has_records, f"{len(handler.records)} record(s) captured")

        if has_records:
            record = handler.records[0]
            has_user_id = hasattr(record, 'user_id')
            has_action = hasattr(record, 'action')

            self.log_result("Extra field: user_id", has_user_id, f"Value: {getattr(record, 'user_id', 'N/A')}")
            self.log_result("Extra field: action", has_action, f"Value: {getattr(record, 'action', 'N/A')}")

        # Clean up
        test_logger.removeHandler(handler)

    def test_no_print_statements(self):
        """Verify no print statements remain in production code"""
        print("\n" + "="*80)
        print("TEST 5: No Print Statements in Production Code")
        print("="*80)

        import subprocess

        # Search for print statements in production code
        try:
            result = subprocess.run(
                ['grep', '-rn', '--include=*.py', 'print(',
                 'starview_app/', 'django_project/',
                 '--exclude-dir=migrations',
                 '--exclude-dir=__pycache__'],
                cwd='/Users/adiaz/event-horizon',
                capture_output=True,
                text=True
            )

            # Filter out acceptable print statements (in comments, docstrings, etc.)
            lines = [line for line in result.stdout.split('\n') if line.strip()]

            # Exclude build.sh, migration files, test files, and comments
            production_prints = []
            for line in lines:
                # Skip if in excluded files/directories
                if any(exclude in line for exclude in [
                    'build.sh',
                    'migrations/',
                    'tests/',
                    '__pycache__',
                    '.pyc',
                ]):
                    continue

                # Skip if it's a comment (has # before print)
                # Extract the part after the filename:line_number:
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    code_part = parts[2].strip()
                    # Check if the line is a comment
                    if code_part.startswith('#'):
                        continue

                production_prints.append(line)

            no_prints = len(production_prints) == 0
            self.log_result(
                "No print statements in production code",
                no_prints,
                "All print statements replaced!" if no_prints else f"Found {len(production_prints)} print statement(s)"
            )

            if not no_prints:
                print("\n⚠️  Remaining print statements:")
                for line in production_prints[:10]:  # Show first 10
                    print(f"   {line}")

        except Exception as e:
            self.log_result("Print statement check", False, str(e))

    def test_location_enrichment_logging(self):
        """Test location enrichment logging (sync mode only for testing)"""
        print("\n" + "="*80)
        print("TEST 6: Location Enrichment Logging")
        print("="*80)

        try:
            # Ensure Celery is disabled for this test
            original_celery_enabled = settings.CELERY_ENABLED
            settings.CELERY_ENABLED = False

            # Create test user
            test_user = User.objects.filter(username='logging_test_user').first()
            if not test_user:
                test_user = User.objects.create_user(
                    username='logging_test_user',
                    email='logging_test@example.com',
                    password='testpass123'
                )

            # Capture logs
            log_stream = io.StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setFormatter(logging.Formatter(
                '{levelname} {asctime} {module} {message}',
                style='{'
            ))

            location_logger = logging.getLogger('starview_app.models.model_location')
            location_logger.addHandler(handler)
            location_logger.setLevel(logging.INFO)

            # Create location (should trigger enrichment logging)
            location = Location.objects.create(
                name="Logging Test Location",
                added_by=test_user,
                latitude=40.7128,
                longitude=-74.0060,
                elevation=10
            )

            # Check output
            output = log_stream.getvalue()
            has_enrichment_log = 'enrichment' in output.lower()

            self.log_result(
                "Location enrichment logged",
                has_enrichment_log,
                "Enrichment message found in logs" if has_enrichment_log else "No enrichment log found"
            )

            if has_enrichment_log:
                has_sync_mode = 'sync' in output.lower() or 'celery disabled' in output.lower()
                self.log_result(
                    "Sync mode indicated",
                    has_sync_mode,
                    "Correctly identified sync enrichment"
                )

            # Clean up
            location.delete()
            test_user.delete()
            location_logger.removeHandler(handler)
            settings.CELERY_ENABLED = original_celery_enabled

        except Exception as e:
            self.log_result("Location enrichment logging", False, str(e))

    def test_signal_logging(self):
        """Test signal handler logging"""
        print("\n" + "="*80)
        print("TEST 7: Signal Handler Logging")
        print("="*80)

        try:
            # Create test user
            test_user = User.objects.filter(username='signal_test_user').first()
            if not test_user:
                test_user = User.objects.create_user(
                    username='signal_test_user',
                    email='signal_test@example.com',
                    password='testpass123'
                )

            # Verify profile was auto-created (signal)
            profile_exists = UserProfile.objects.filter(user=test_user).exists()
            self.log_result(
                "User profile signal triggered",
                profile_exists,
                "Profile auto-created on user creation"
            )

            # Clean up
            test_user.delete()

        except Exception as e:
            self.log_result("Signal logging test", False, str(e))

    def run_all_tests(self):
        """Run all logging tests"""
        print("\n" + "="*80)
        print("LOGGING TEST SUITE")
        print("="*80)
        print(f"Testing logging configuration after print statement replacement")
        print(f"Django settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
        print(f"Python: {sys.version.split()[0]}")
        print("="*80)

        # Run tests
        self.test_logging_configuration()
        self.test_logger_instances()
        self.test_logging_output_format()
        self.test_structured_logging()
        self.test_no_print_statements()
        self.test_location_enrichment_logging()
        self.test_signal_logging()

        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        print("="*80)

        if self.failed == 0:
            print("✅ ALL TESTS PASSED - Logging is properly configured!")
            return 0
        else:
            print(f"❌ {self.failed} TEST(S) FAILED - Review failures above")
            return 1


if __name__ == '__main__':
    tester = TestLogging()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
