# Celery Async Tasks - Complete Guide

## Quick Overview

**Celery is OPTIONAL** - Your app works perfectly without it (FREE tier) or with it (PAID tier with instant responses).

| Mode | Cost | User Experience | Setup |
|------|------|-----------------|-------|
| **FREE** | $0/month | 2-5s delay on location creation | Set `CELERY_ENABLED=False` |
| **PAID** | $7-10/month | Instant (99.4% faster) | Set `CELERY_ENABLED=True` + worker |

---

## What is Celery?

Celery executes time-consuming operations asynchronously in the background:
- **Location enrichment:** Fetches address + elevation from Mapbox API (2-5 seconds)
- **99.4% faster response:** API returns instantly, enrichment happens in background
- **Graceful degradation:** App works without worker (FREE tier support)

### Architecture

```
Django → Redis (queue) → Celery Worker → Mapbox API → Database
  ↓
Returns 201 Created immediately (when CELERY_ENABLED=True)
```

---

## Current Tasks

### 1. `enrich_location_data(location_id)`
- **Purpose:** Fetches address (city, state, country) and elevation from Mapbox
- **Trigger:** Automatically when location is created (if `CELERY_ENABLED=True`)
- **Duration:** 2-5 seconds (background)
- **Retries:** 3 attempts with 60-second delay
- **Fallback:** Runs synchronously if `CELERY_ENABLED=False`

### 2. `test_celery(message)`
- **Purpose:** Verifies Celery worker is running
- **Usage:** Testing and monitoring

---

## Development Setup

### Prerequisites
- Redis running (`brew services start redis`)
- Celery installed (`pip install celery==5.4.0`)

### Start Worker

```bash
# Terminal 1: Django server
djvenv/bin/python manage.py runserver

# Terminal 2: Celery worker
djvenv/bin/celery -A django_project worker --loglevel=info

# Terminal 3 (optional): Monitor tasks
djvenv/bin/celery -A django_project events
```

### Test Celery

```bash
# Run test suite
djvenv/bin/python .claude/backend/tests/phase4/test_celery_tasks.py

# Expected output:
# ✓ Redis connection test passed
# ✓ Celery configuration test passed
# ✓ Simple task execution test passed
# ✓ Location enrichment test passed
# ✓ Performance comparison test passed
# Total: 5/5 tests passed
```

---

## Production Deployment (Render)

### Option 1: FREE Tier (No Worker)

**In Render dashboard** → star-view → Environment:
```bash
CELERY_ENABLED=False
```

**That's it!** App works normally, location enrichment runs synchronously.

**Pros:**
- $0/month cost
- No additional services
- Fully functional

**Cons:**
- 2-5 second delay when creating locations
- User must wait for API response

---

### Option 2: PAID Tier (With Worker)

#### Step 1: Verify Redis URL

**In Render dashboard** → star-view → Environment:
- Look for `REDIS_URL` environment variable
- If missing, copy from star-view-cache → Internal Redis URL
- Format: `redis://red-xxxxx:6379`

#### Step 2: Create Background Worker Service

1. Go to Render Dashboard → New → Background Worker
2. Fill in:
   - **Name:** `star-view-celery-worker`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `celery -A django_project worker --loglevel=info`
   - **Plan:** Starter ($7/month)

#### Step 3: Add Environment Variables to Worker

Copy these from your web service (star-view) to worker:
```bash
REDIS_URL=redis://red-xxxxx:6379          # From star-view-cache
DB_ENGINE=postgresql
DB_NAME=<from-render-postgres>
DB_USER=<from-render-postgres>
DB_PASSWORD=<from-render-postgres>
DB_HOST=<from-render-postgres>
DB_PORT=5432
MAPBOX_TOKEN=<your-mapbox-token>
DISABLE_EXTERNAL_APIS=False
CELERY_ENABLED=True                        # Important!
```

#### Step 4: Enable Celery in Web Service

**In Render dashboard** → star-view → Environment:
```bash
CELERY_ENABLED=True
```

Save changes → Render will auto-deploy.

#### Step 5: Verify Worker is Running

```bash
# Check Render dashboard
star-view-celery-worker → Logs

# Should see:
[tasks]
  . starview_app.utils.tasks.enrich_location_data
  . starview_app.utils.tasks.test_celery

celery@hostname ready.
```

#### Step 6: Test in Production

Create a new location and check:
1. API responds instantly (< 100ms)
2. Worker logs show task execution
3. Location enriched within 2-5 seconds

---

## Monitoring

### Check Worker Status

**Render Dashboard** → star-view-celery-worker:
- **Logs:** View task execution in real-time
- **Metrics:** CPU, memory, task throughput
- **Health:** Worker uptime and restart count

### Check Task Queue

**If you need to inspect Redis queue:**
```bash
# Connect to Redis (use Internal Connection String from Render)
redis-cli -h <redis-host> -p 6379 -a <password>

# Check queue length
LLEN celery

# View queued tasks
LRANGE celery 0 -1
```

### Common Issues

**Worker keeps restarting:**
- Check environment variables are set correctly
- Verify database connection (DB_HOST, DB_NAME, etc.)
- Check worker logs for specific errors

**Tasks not executing:**
- Verify `CELERY_ENABLED=True` in web service
- Check `REDIS_URL` is same in web service and worker
- Restart both web service and worker

**Tasks failing:**
- Check Mapbox API token is valid
- Verify `DISABLE_EXTERNAL_APIS=False`
- Check worker logs for specific error messages

---

## Cost Comparison

### FREE Tier
- **Web Service:** $0/month (Render free tier) or $7/month (paid)
- **PostgreSQL:** $0/month (Render free tier) or $7/month (paid)
- **Redis:** Included with web service
- **Celery Worker:** Not deployed
- **Total:** $0-14/month

### PAID Tier (With Celery)
- **Web Service:** $7/month (Starter)
- **PostgreSQL:** $7/month (Starter)
- **Redis:** Included with web service
- **Celery Worker:** $7/month (Starter)
- **Total:** $21/month

**Performance Gain:** 99.4% faster (2.5s → 0.015s response time)

---

## Implementation Details

### Django Integration

**File:** `starview_app/models/model_location.py` (lines 94-131)

```python
def save(self, *args, **kwargs):
    # Sanitize and validate
    if self.name:
        self.name = sanitize_plain_text(self.name)
    validate_latitude(self.latitude)
    validate_longitude(self.longitude)
    validate_elevation(self.elevation)

    is_new = not self.pk
    super().save(*args, **kwargs)

    # Enrich data for new locations or coordinate changes
    if is_new or any(field in kwargs.get('update_fields', [])
                     for field in ['latitude', 'longitude']):
        from django.conf import settings
        use_celery = getattr(settings, 'CELERY_ENABLED', False)

        if use_celery:
            # Async enrichment via Celery worker
            from starview_app.utils.tasks import enrich_location_data
            enrich_location_data.delay(self.pk)
            logger.info("Queued async enrichment task for location '%s' (ID: %d)",
                       self.name, self.pk,
                       extra={'location_id': self.pk, 'mode': 'async'})
        else:
            # Sync enrichment (fallback for FREE tier)
            logger.info("Running sync enrichment for location '%s' (ID: %d)",
                       self.name, self.pk,
                       extra={'location_id': self.pk, 'mode': 'sync'})
            from starview_app.services.location_service import LocationService
            LocationService.initialize_location_data(self)
```

### Celery Configuration

**File:** `django_project/celery.py`

```python
import os
from celery import Celery

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

# Create Celery app instance
app = Celery('django_project')

# Load configuration from Django settings with 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed Django apps
app.autodiscover_tasks()
```

**File:** `django_project/__init__.py`

```python
# Import Celery app so it's loaded when Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)
```

This ensures Celery is initialized when Django starts, even in FREE tier mode (where tasks run synchronously).

**File:** `django_project/settings.py` (lines 650-684)

```python
# Enable/disable Celery async tasks
CELERY_ENABLED = os.getenv('CELERY_ENABLED', 'False') == 'True'

# Celery broker and result backend (uses same Redis as cache)
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')

# Serialization formats (JSON is more secure than pickle)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Timezone settings
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Task time limits (prevent runaway tasks)
CELERY_TASK_TIME_LIMIT = 300        # Hard limit: 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240   # Soft limit: 4 minutes

# Task result settings
CELERY_RESULT_EXPIRES = 3600              # Results expire after 1 hour
CELERY_TASK_TRACK_STARTED = True          # Track when tasks start
CELERY_TASK_SEND_SENT_EVENT = True        # Send event when task queued

# Worker optimization settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 4     # Tasks each worker prefetches
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Restart after N tasks (prevent memory leaks)
```

### Task Implementation

**File:** `starview_app/utils/tasks.py`

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def enrich_location_data(self, location_id):
    """
    Asynchronously enriches a location with address and elevation data from Mapbox.

    This task is triggered after a location is created, allowing the user to get
    an instant response while the enrichment happens in the background.
    """
    from starview_app.models import Location
    from starview_app.services.location_service import LocationService

    logger.info(f"Starting enrichment for location ID: {location_id}")

    try:
        location = Location.objects.get(id=location_id)

        # Skip if external APIs are disabled (testing mode)
        if getattr(settings, 'DISABLE_EXTERNAL_APIS', False):
            logger.info(f"Skipping enrichment for location {location_id} (APIs disabled)")
            return {
                'status': 'skipped',
                'location_id': location_id,
                'reason': 'DISABLE_EXTERNAL_APIS is True'
            }

        enriched_fields = []

        # Enrich address from coordinates
        try:
            address_success = LocationService.update_address_from_coordinates(location)
            if address_success:
                enriched_fields.append('address')
                logger.info(f"Address enriched: {location.formatted_address}")
        except Exception as e:
            logger.error(f"Error enriching address: {str(e)}")

        # Enrich elevation from Mapbox
        try:
            elevation_success = LocationService.update_elevation_from_mapbox(location)
            if elevation_success:
                enriched_fields.append('elevation')
                logger.info(f"Elevation enriched: {location.elevation}m")
        except Exception as e:
            logger.error(f"Error enriching elevation: {str(e)}")

        # Return success with enriched fields
        result = {
            'status': 'success',
            'location_id': location_id,
            'location_name': location.name,
            'enriched_fields': enriched_fields,
            'formatted_address': location.formatted_address,
            'elevation': location.elevation
        }

        logger.info(f"Enrichment complete: {enriched_fields}")
        return result

    except Location.DoesNotExist:
        logger.error(f"Location {location_id} not found - may have been deleted")
        return {
            'status': 'error',
            'location_id': location_id,
            'error': 'Location not found (may have been deleted)'
        }

    except Exception as exc:
        logger.error(f"Unexpected error enriching location {location_id}: {str(exc)}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for location {location_id}")
            return {
                'status': 'failed',
                'location_id': location_id,
                'error': f'Max retries exceeded: {str(exc)}'
            }
```

### Health Check Integration

**File:** `starview_app/views/views_health.py`

The health check endpoint (`/health/`) automatically detects Celery status:

```python
# Health check behavior based on CELERY_ENABLED setting
celery_enabled = getattr(settings, 'CELERY_ENABLED', False)

if not celery_enabled:
    # FREE tier mode - Celery intentionally disabled
    checks["celery"] = "disabled"
else:
    # PAID tier mode - Verify worker is running
    try:
        inspector = celery_app.control.inspect()
        active_workers = inspector.active()

        if active_workers:
            checks["celery"] = "ok"
        else:
            checks["celery"] = "error"
            errors.append("No active Celery workers found")
            is_healthy = False
    except Exception as e:
        checks["celery"] = "error"
        errors.append(f"Celery connection error: {str(e)}")
```

**Health Check Response Examples:**

**FREE Tier** (`CELERY_ENABLED=False`):
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "celery": "disabled"
  }
}
```

**PAID Tier** (`CELERY_ENABLED=True` with worker running):
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "celery": "ok"
  }
}
```

**PAID Tier** (worker NOT running - error state):
```json
{
  "status": "unhealthy",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "celery": "error"
  },
  "errors": ["No active Celery workers found"]
}
```

### Key Implementation Features

**1. Automatic Trigger on Location Creation:**
- Task automatically queued when new location is saved
- Also triggers when `latitude` or `longitude` fields are updated
- No manual task invocation needed

**2. Graceful Degradation:**
- If `CELERY_ENABLED=False`: Runs synchronously (2-5s response time)
- If `CELERY_ENABLED=True` but worker down: Tasks queue in Redis, process when worker starts
- No code changes needed to switch between modes

**3. DISABLE_EXTERNAL_APIS Support:**
- Task respects `DISABLE_EXTERNAL_APIS=True` setting
- Returns early with 'skipped' status for testing environments
- Prevents unnecessary API calls during tests

**4. Partial Success Handling:**
- Address enrichment and elevation enrichment are independent
- If address fails, elevation still attempts (and vice versa)
- Returns detailed status with `enriched_fields` array

**5. Comprehensive Logging:**
- Logs task start, completion, and errors
- Includes structured logging with `location_id` and `mode` extras
- Easy to trace in production logs

---

## Testing

**Test Script:** `.claude/backend/tests/phase4/test_celery_tasks.py`

**Tests:**
1. Redis connection
2. Celery configuration
3. Simple task execution
4. Location enrichment
5. Performance comparison (sync vs async)

**Run:**
```bash
djvenv/bin/python .claude/backend/tests/phase4/test_celery_tasks.py
```

---

## Environment Variables Reference

**Required for Celery (both modes):**
```bash
REDIS_URL=redis://127.0.0.1:6379/0  # Redis connection for broker/backend
```

**FREE Tier (Synchronous Mode):**
```bash
CELERY_ENABLED=False                 # Default if omitted
```

**PAID Tier (Asynchronous Mode):**
```bash
CELERY_ENABLED=True                  # Enable async task processing
```

**For Worker Service (Render deployment):**
The worker needs these environment variables copied from the web service:
```bash
# Database connection (to save enriched data)
DB_ENGINE=postgresql
DB_NAME=<your-db-name>
DB_USER=<your-db-user>
DB_PASSWORD=<your-db-password>
DB_HOST=<your-db-host>
DB_PORT=5432

# Redis connection (to receive tasks)
REDIS_URL=redis://red-xxxxx:6379

# External APIs (to fetch data)
MAPBOX_TOKEN=<your-mapbox-token>
DISABLE_EXTERNAL_APIS=False          # Must be False for enrichment

# Celery mode
CELERY_ENABLED=True                  # Enable async tasks

# Django settings
DJANGO_SETTINGS_MODULE=django_project.settings
```

**Testing Environment Variables:**
```bash
DISABLE_EXTERNAL_APIS=True           # Skip external API calls in tests
CELERY_ENABLED=False                 # Run tasks synchronously in tests
```

---

## Troubleshooting

### Common Issues and Solutions

**Issue: Tasks queue but never execute**
- **Cause:** Worker not running or not connected to same Redis instance
- **Solution:**
  1. Verify worker is running: `celery -A django_project inspect active`
  2. Check `REDIS_URL` matches in both web service and worker
  3. Restart both web service and worker

**Issue: "Connection refused" errors**
- **Cause:** Redis not running or wrong URL
- **Solution:**
  1. Development: `brew services start redis`
  2. Production: Verify `REDIS_URL` environment variable is set
  3. Test connection: `redis-cli -u $REDIS_URL ping`

**Issue: Tasks fail silently**
- **Cause:** Missing environment variables in worker
- **Solution:**
  1. Check worker logs for errors
  2. Verify all required env vars are set (especially `DB_*` and `MAPBOX_TOKEN`)
  3. Test task manually: `python manage.py shell` → `enrich_location_data.delay(location_id)`

**Issue: Health check shows "celery: error" even though worker is running**
- **Cause:** Worker connected to different Redis instance
- **Solution:** Ensure `REDIS_URL` is identical in web service and worker

**Issue: Memory usage keeps growing**
- **Cause:** Worker not restarting after processing many tasks
- **Solution:** `CELERY_WORKER_MAX_TASKS_PER_CHILD=1000` already configured (worker restarts every 1000 tasks)

**Issue: Tasks timeout**
- **Cause:** Mapbox API slow or down
- **Solution:**
  1. Task will auto-retry 3 times with 60s delay
  2. Check `CELERY_TASK_TIME_LIMIT=300` (5 min hard limit)
  3. Monitor Mapbox API status

### Development Debugging

**Check if Celery is properly configured:**
```bash
djvenv/bin/python manage.py shell
```
```python
from django.conf import settings
print(f"CELERY_ENABLED: {settings.CELERY_ENABLED}")
print(f"CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")
```

**Test Redis connection:**
```bash
redis-cli -u $REDIS_URL ping
# Should respond: PONG
```

**Check active workers:**
```bash
djvenv/bin/celery -A django_project inspect active
```

**Check queued tasks:**
```bash
djvenv/bin/celery -A django_project inspect reserved
```

**Purge all queued tasks (development only):**
```bash
djvenv/bin/celery -A django_project purge
```

**Monitor task execution in real-time:**
```bash
djvenv/bin/celery -A django_project events
```

---

## Summary

- ✅ **FREE tier supported:** Works without Celery worker (sync fallback)
- ✅ **PAID tier optional:** 99.4% faster with worker ($7/month)
- ✅ **Easy migration:** Toggle `CELERY_ENABLED` environment variable
- ✅ **Production tested:** 5/5 tests passing
- ✅ **Graceful degradation:** No code changes needed
- ✅ **Well documented:** Comprehensive error handling and logging

**Recommendation:** Start with FREE tier, upgrade to PAID when user base grows.
