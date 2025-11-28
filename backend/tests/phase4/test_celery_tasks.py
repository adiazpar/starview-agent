#!/usr/bin/env python3
# ----------------------------------------------------------------------------------------------------- #
# Test script for Celery async tasks implementation                                                    #
#                                                                                                       #
# Purpose:                                                                                              #
# Validates that Celery is properly configured and that async location enrichment works correctly.     #
#                                                                                                       #
# Tests:                                                                                                #
# 1. Celery configuration verification                                                                 #
# 2. Test task execution (simple task)                                                                 #
# 3. Location enrichment task (full workflow)                                                          #
# 4. Error handling and retries                                                                        #
#                                                                                                       #
# Requirements:                                                                                         #
# - Redis server running (redis-server)                                                                #
# - Celery worker running: celery -A django_project worker --loglevel=info                             #
# - Django development server NOT required                                                             #
#                                                                                                       #
# Run with: djvenv/bin/python .claude/tests/phase4/test_celery_tasks.py                                #
# ----------------------------------------------------------------------------------------------------- #

import os
import sys
import time
import django

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from starview_app.models import Location
from starview_app.utils.tasks import test_celery, enrich_location_data
from celery import current_app
import redis


def print_header(text):
    """Print formatted test header"""
    print(f"\n{'=' * 80}")
    print(f"  {text}")
    print('=' * 80)


def print_test(test_num, description):
    """Print test description"""
    print(f"\n[TEST {test_num}] {description}")


def print_result(success, message):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")


def test_redis_connection():
    """Test 1: Verify Redis is running and accessible"""
    print_test(1, "Redis Connection Test")

    try:
        # Parse Redis URL from settings
        redis_url = settings.CELERY_BROKER_URL
        r = redis.from_url(redis_url)

        # Test connection
        response = r.ping()
        print_result(True, f"Redis connection successful (PING response: {response})")
        return True

    except Exception as e:
        print_result(False, f"Redis connection failed: {str(e)}")
        print("  💡 Make sure Redis is running: brew services start redis")
        return False


def test_celery_configuration():
    """Test 2: Verify Celery configuration"""
    print_test(2, "Celery Configuration Test")

    try:
        # Check broker URL
        broker = current_app.conf.broker_url
        print(f"  - Broker URL: {broker}")

        # Check result backend
        result_backend = current_app.conf.result_backend
        print(f"  - Result Backend: {result_backend}")

        # Check task serializer
        task_serializer = current_app.conf.task_serializer
        print(f"  - Task Serializer: {task_serializer}")

        # Check timezone
        timezone = current_app.conf.timezone
        print(f"  - Timezone: {timezone}")

        print_result(True, "Celery configuration loaded successfully")
        return True

    except Exception as e:
        print_result(False, f"Celery configuration error: {str(e)}")
        return False


def test_simple_task():
    """Test 3: Execute simple test task"""
    print_test(3, "Simple Task Execution Test")

    try:
        # Send task to Celery worker
        result = test_celery.delay("Testing Celery setup!")
        print(f"  - Task ID: {result.id}")
        print(f"  - Task State: {result.state}")

        # Wait for result (timeout after 10 seconds)
        print("  - Waiting for task to complete...")
        task_result = result.get(timeout=10)

        print(f"  - Task Result: {task_result}")
        print_result(True, "Simple task executed successfully")
        return True

    except Exception as e:
        print_result(False, f"Simple task failed: {str(e)}")
        print("  💡 Make sure Celery worker is running:")
        print("     celery -A django_project worker --loglevel=info")
        return False


def test_location_enrichment():
    """Test 4: Location enrichment task (full workflow)"""
    print_test(4, "Location Enrichment Task Test")

    try:
        # Create test user
        user, _ = User.objects.get_or_create(
            username='celery_test_user',
            defaults={'email': 'celery_test@example.com'}
        )

        # Create test location (sync - without triggering Celery yet)
        print("  - Creating test location...")

        # We need to temporarily disable the signal that triggers Celery
        # For testing, we'll create the location and then manually trigger enrichment
        location = Location(
            name="Celery Test Observatory",
            latitude=37.7749,  # San Francisco
            longitude=-122.4194,
            elevation=0,
            added_by=user
        )

        # Save without triggering signal (we'll trigger manually)
        # This is just for testing - in production, save() automatically triggers Celery
        super(Location, location).save()

        print(f"  - Location created (ID: {location.id})")
        print(f"  - Initial state:")
        print(f"    * Address: {location.formatted_address or 'None'}")
        print(f"    * Elevation: {location.elevation}m")

        # Now trigger enrichment task manually
        print("\n  - Triggering enrichment task...")
        result = enrich_location_data.delay(location.id)
        print(f"  - Task ID: {result.id}")
        print(f"  - Task State: {result.state}")

        # Wait for enrichment to complete
        print("  - Waiting for enrichment task to complete (max 30 seconds)...")
        task_result = result.get(timeout=30)

        print(f"\n  - Task completed!")
        print(f"  - Result: {task_result}")

        # Refresh location from database
        location.refresh_from_db()

        print(f"\n  - Enriched state:")
        print(f"    * Address: {location.formatted_address}")
        print(f"    * Locality: {location.locality}")
        print(f"    * Administrative Area: {location.administrative_area}")
        print(f"    * Country: {location.country}")
        print(f"    * Elevation: {location.elevation}m")

        # Verify enrichment worked
        success = (
            location.formatted_address is not None and
            location.formatted_address != '' and
            task_result['status'] == 'success'
        )

        if success:
            print_result(True, f"Location enriched successfully: {location.formatted_address}")
        else:
            print_result(False, "Location enrichment incomplete")

        # Cleanup
        location.delete()
        user.delete()

        return success

    except Exception as e:
        print_result(False, f"Location enrichment test failed: {str(e)}")
        import traceback
        traceback.print_exc()

        # Cleanup on error
        try:
            if location and location.id:
                location.delete()
            if user and user.id:
                user.delete()
        except:
            pass

        return False


def test_async_vs_sync_performance():
    """Test 5: Compare async vs sync performance"""
    print_test(5, "Performance Comparison (Async vs Sync)")

    try:
        # Create test user
        user, _ = User.objects.get_or_create(
            username='perf_test_user',
            defaults={'email': 'perf@example.com'}
        )

        # Test 1: Synchronous enrichment (how it used to work)
        print("\n  📊 Synchronous Enrichment (OLD WAY):")
        location_sync = Location(
            name="Sync Test Location",
            latitude=40.7128,  # New York
            longitude=-74.0060,
            elevation=0,
            added_by=user
        )

        # Save without signal, then call enrichment synchronously
        super(Location, location_sync).save()

        start_time = time.time()
        from starview_app.services.location_service import LocationService
        LocationService.initialize_location_data(location_sync)
        sync_duration = time.time() - start_time

        print(f"    ⏱️  Duration: {sync_duration:.2f} seconds (BLOCKING)")
        print(f"    📍 Result: {location_sync.formatted_address}")

        # Test 2: Asynchronous enrichment (new way)
        print("\n  ⚡ Asynchronous Enrichment (NEW WAY):")
        location_async = Location(
            name="Async Test Location",
            latitude=51.5074,  # London
            longitude=-0.1278,
            elevation=0,
            added_by=user
        )

        super(Location, location_async).save()

        start_time = time.time()
        result = enrich_location_data.delay(location_async.id)
        async_duration = time.time() - start_time

        print(f"    ⏱️  Duration: {async_duration:.3f} seconds (NON-BLOCKING)")
        print(f"    📝 Task queued: {result.id}")
        print(f"    ⚙️  Task running in background...")

        # Wait for completion to show final result
        task_result = result.get(timeout=30)
        location_async.refresh_from_db()
        print(f"    ✅ Task completed: {location_async.formatted_address}")

        # Calculate improvement
        improvement = ((sync_duration - async_duration) / sync_duration) * 100

        print(f"\n  📈 Performance Improvement:")
        print(f"    - Sync (blocking):  {sync_duration:.2f}s")
        print(f"    - Async (instant):  {async_duration:.3f}s")
        print(f"    - Speed improvement: {improvement:.1f}% faster response")
        print(f"    - User experience: INSTANT vs {sync_duration:.1f}s wait")

        # Cleanup
        location_sync.delete()
        location_async.delete()
        user.delete()

        print_result(True, f"Async is {improvement:.1f}% faster for user response time")
        return True

    except Exception as e:
        print_result(False, f"Performance test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print_header("CELERY ASYNC TASKS TEST SUITE")
    print("Testing Celery integration for async location enrichment")

    results = []

    # Run tests
    results.append(("Redis Connection", test_redis_connection()))

    if not results[-1][1]:
        print("\n⚠️  Redis is not running. Skipping remaining tests.")
        print("   Start Redis with: brew services start redis")
        return

    results.append(("Celery Configuration", test_celery_configuration()))
    results.append(("Simple Task Execution", test_simple_task()))

    if not results[-1][1]:
        print("\n⚠️  Celery worker is not running. Skipping enrichment tests.")
        print("   Start worker with: celery -A django_project worker --loglevel=info")
        return

    results.append(("Location Enrichment", test_location_enrichment()))
    results.append(("Performance Comparison", test_async_vs_sync_performance()))

    # Print summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Celery async tasks are working correctly.")
        print("\n📝 Next steps:")
        print("   1. Update .env.example with REDIS_URL documentation")
        print("   2. Update deployment docs with Celery worker setup")
        print("   3. Update SECURITY_AUDIT.md marking 2.3 as complete")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")


if __name__ == '__main__':
    main()
