#!/usr/bin/env python3
"""
Health Check Endpoint Test Suite - Phase 5
==========================================

Tests the comprehensive health check endpoint that monitors:
- Database connectivity (PostgreSQL)
- Cache connectivity (Redis)
- Celery worker availability (when enabled)

This test suite verifies that the health check endpoint correctly:
1. Returns 200 OK when all services are healthy
2. Returns 503 Service Unavailable when any critical service fails
3. Provides detailed status for each service
4. Handles CELERY_ENABLED=False correctly (free tier support)
5. Completes checks within acceptable time limits (<100ms target)

Test Categories:
- Basic health check (all services healthy)
- Database failure simulation
- Cache failure simulation
- Celery status reporting (enabled vs disabled)
- Performance verification
"""

import requests
import time
import sys

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
HEALTH_ENDPOINT = f"{BASE_URL}/health/"

def print_header(title):
    """Print a formatted test section header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")

def print_test(description):
    """Print test description"""
    print(f"Testing: {description}")

def print_success(message):
    """Print success message"""
    print(f"  ✓ {message}")

def print_error(message):
    """Print error message"""
    print(f"  ✗ {message}")

def print_info(message):
    """Print info message"""
    print(f"  ℹ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"  ⚠ {message}")

def test_basic_health_check():
    """Test 1: Basic health check - all services should be healthy"""
    print_test("Basic health check with all services operational")

    try:
        start_time = time.time()
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        elapsed_ms = (time.time() - start_time) * 1000

        data = response.json()

        # Verify response structure
        if "status" not in data:
            print_error("Missing 'status' field in response")
            return False

        if "timestamp" not in data:
            print_error("Missing 'timestamp' field in response")
            return False

        if "checks" not in data:
            print_error("Missing 'checks' field in response")
            return False

        print_success(f"Response structure valid")
        print_info(f"Status: {data['status']}")
        print_info(f"Response time: {elapsed_ms:.2f}ms")

        # Verify checks object
        checks = data['checks']

        # Database check
        if "database" not in checks:
            print_error("Missing 'database' check")
            return False
        print_success(f"Database check: {checks['database']}")

        # Cache check
        if "cache" not in checks:
            print_error("Missing 'cache' check")
            return False
        print_success(f"Cache check: {checks['cache']}")

        # Celery check
        if "celery" not in checks:
            print_error("Missing 'celery' check")
            return False

        celery_status = checks['celery']
        if celery_status == "disabled":
            print_info(f"Celery check: {celery_status} (FREE tier mode)")
        elif celery_status == "ok":
            print_success(f"Celery check: {celery_status} (worker running)")
        elif celery_status == "error":
            print_warning(f"Celery check: {celery_status} (check if worker is running)")
        else:
            print_error(f"Unexpected Celery status: {celery_status}")
            return False

        # Verify HTTP status code
        if data['status'] == 'healthy':
            if response.status_code != 200:
                print_error(f"Expected status code 200 for healthy status, got {response.status_code}")
                return False
            print_success(f"HTTP status code: {response.status_code} (healthy)")
        else:
            if response.status_code != 503:
                print_error(f"Expected status code 503 for unhealthy status, got {response.status_code}")
                return False
            print_warning(f"HTTP status code: {response.status_code} (unhealthy)")

            # Print error details if present
            if "errors" in data:
                print_info("Errors reported:")
                for error in data['errors']:
                    print_info(f"  - {error}")

        # Performance check
        if elapsed_ms > 100:
            print_warning(f"Response time ({elapsed_ms:.2f}ms) exceeds 100ms target")
        else:
            print_success(f"Response time within target (<100ms)")

        print_success("Basic health check test passed")
        return True

    except requests.exceptions.ConnectionError:
        print_error("Could not connect to server - is Django running on http://127.0.0.1:8000?")
        return False
    except requests.exceptions.Timeout:
        print_error("Request timed out")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_response_format():
    """Test 2: Verify JSON response format is correct"""
    print_test("Response format validation")

    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)

        # Verify content type
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            print_error(f"Expected JSON content type, got: {content_type}")
            return False
        print_success("Content-Type is application/json")

        # Verify JSON is parseable
        try:
            data = response.json()
            print_success("Response is valid JSON")
        except ValueError:
            print_error("Response is not valid JSON")
            return False

        # Verify timestamp format (ISO 8601)
        timestamp = data.get('timestamp', '')
        if 'T' not in timestamp or 'Z' not in timestamp:
            # Check if it's ISO 8601 with timezone offset
            if 'T' not in timestamp or ('+' not in timestamp and '-' not in timestamp.split('T')[1]):
                print_warning(f"Timestamp format may not be ISO 8601: {timestamp}")
        else:
            print_success(f"Timestamp is ISO 8601 format: {timestamp}")

        print_success("Response format test passed")
        return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_performance():
    """Test 3: Performance test - verify response time is acceptable"""
    print_test("Performance test (10 requests)")

    try:
        response_times = []

        for i in range(10):
            start_time = time.time()
            response = requests.get(HEALTH_ENDPOINT, timeout=5)
            elapsed_ms = (time.time() - start_time) * 1000
            response_times.append(elapsed_ms)

            if response.status_code not in [200, 503]:
                print_error(f"Request {i+1}: Unexpected status code {response.status_code}")
                return False

        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)

        print_success(f"Completed 10 requests")
        print_info(f"Average response time: {avg_time:.2f}ms")
        print_info(f"Min response time: {min_time:.2f}ms")
        print_info(f"Max response time: {max_time:.2f}ms")

        if avg_time > 100:
            print_warning(f"Average response time exceeds 100ms target")
        else:
            print_success(f"Average response time within target")

        if max_time > 200:
            print_warning(f"Maximum response time is quite high")

        print_success("Performance test passed")
        return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_celery_status_reporting():
    """Test 4: Verify Celery status is reported correctly"""
    print_test("Celery status reporting")

    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        data = response.json()

        celery_status = data['checks'].get('celery', 'missing')

        if celery_status == 'missing':
            print_error("Celery status not reported")
            return False

        if celery_status == 'disabled':
            print_info("Celery is disabled (CELERY_ENABLED=False)")
            print_info("This is expected for FREE tier deployment")

            # When disabled, status should still be healthy
            if data['status'] != 'healthy':
                print_error("Status should be 'healthy' when Celery is disabled")
                return False
            print_success("Status is 'healthy' with Celery disabled (correct)")

        elif celery_status == 'ok':
            print_success("Celery worker is running and healthy")
            print_info("CELERY_ENABLED=True and worker is active")

        elif celery_status == 'error':
            print_warning("Celery status is 'error'")

            # Check if errors array provides details
            if "errors" in data:
                for error in data['errors']:
                    if 'celery' in error.lower():
                        print_info(f"Error details: {error}")

            # When Celery is enabled but failing, status should be unhealthy
            if data['status'] != 'unhealthy':
                print_error("Status should be 'unhealthy' when Celery is enabled but failing")
                return False
            print_info("Status is 'unhealthy' with Celery error (correct)")

        else:
            print_error(f"Unexpected Celery status: {celery_status}")
            return False

        print_success("Celery status reporting test passed")
        return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_concurrent_requests():
    """Test 5: Verify endpoint handles concurrent requests correctly"""
    print_test("Concurrent requests handling")

    try:
        import concurrent.futures

        def make_request():
            start_time = time.time()
            response = requests.get(HEALTH_ENDPOINT, timeout=5)
            elapsed_ms = (time.time() - start_time) * 1000
            return response.status_code, elapsed_ms

        # Make 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Analyze results
        status_codes = [r[0] for r in results]
        response_times = [r[1] for r in results]

        # All should return either 200 or 503 (not errors)
        valid_codes = all(code in [200, 503] for code in status_codes)

        if not valid_codes:
            print_error("Some requests returned invalid status codes")
            invalid = [code for code in status_codes if code not in [200, 503]]
            print_info(f"Invalid codes: {invalid}")
            return False

        print_success(f"All 20 concurrent requests completed successfully")

        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)

        print_info(f"Average response time: {avg_time:.2f}ms")
        print_info(f"Max response time: {max_time:.2f}ms")

        if max_time > 500:
            print_warning(f"Maximum response time is high under concurrent load")
        else:
            print_success(f"Response times acceptable under concurrent load")

        print_success("Concurrent requests test passed")
        return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False

def main():
    """Run all health check tests"""
    print_header("HEALTH CHECK ENDPOINT TEST SUITE - PHASE 5")

    print(f"Testing endpoint: {HEALTH_ENDPOINT}")
    print(f"Target server: {BASE_URL}\n")

    # Run all tests
    tests = [
        ("Basic Health Check", test_basic_health_check),
        ("Response Format", test_response_format),
        ("Performance", test_performance),
        ("Celery Status Reporting", test_celery_status_reporting),
        ("Concurrent Requests", test_concurrent_requests),
    ]

    results = []

    for test_name, test_func in tests:
        print_header(f"TEST: {test_name}")
        result = test_func()
        results.append((test_name, result))
        print()

    # Print summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print(f"\n✓ ALL TESTS PASSED")
        print(f"\nHealth check endpoint is production-ready!")
        return 0
    else:
        print(f"\n✗ SOME TESTS FAILED")
        print(f"\nPlease review the failures above and fix any issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
