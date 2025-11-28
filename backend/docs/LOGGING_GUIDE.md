# Django Logging Best Practices Guide

**Last Updated:** 2025-11-27
**Project:** Starview
**Status:** Production-Ready ✅

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration](#configuration)
3. [Logger Creation](#logger-creation)
4. [Log Levels](#log-levels)
5. [Message Formatting](#message-formatting)
6. [Structured Logging](#structured-logging)
7. [Common Patterns](#common-patterns)
8. [Security Considerations](#security-considerations)
9. [Production Logs (Render)](#production-logs-render)
10. [Common Pitfalls](#common-pitfalls)

---

## Overview

Proper logging is essential for:
- **Debugging:** Identify issues in production without print statements
- **Monitoring:** Track application behavior and performance
- **Auditing:** Security events and user actions
- **Troubleshooting:** Diagnose problems after they occur

**Golden Rule:** Use Python's `logging` module, NEVER use `print()` in production code.

---

## Current Implementation Status

### ✅ What's Working Well

1. **Logger Configuration** - Properly configured in Django settings
   - Formatters: `verbose` and `json` formats defined
   - Handlers: `console` and `audit_file` (rotating file handler)
   - Loggers: `audit` and `starview_app` configured
   - Log directory: `/logs/audit.log` (10MB rotation, 10 backups)

2. **Module-Level Loggers** - Consistently used across codebase
   - All major modules have `logger = logging.getLogger(__name__)`
   - Files: settings.py, celery.py, models, views, utils, signals

3. **Structured Logging** - Using `extra={}` for context
   - Good examples in: model_location.py, signals.py, model_review_photo.py
   - Context includes: location_id, user_id, action, error details

4. **Exception Logging** - Proper use of `exc_info=True`
   - Used in error handlers across views and models
   - Captures full stack traces for debugging

5. **Audit Logging** - Dedicated security event logging
   - Custom `audit` logger with database + file storage
   - Helper functions: `log_auth_event()`, `log_admin_action()`, `log_permission_denied()`
   - JSON formatted audit trail in logs/audit.log

6. **Celery Task Logging** - Using `get_task_logger()`
   - Properly integrates with Celery worker logging
   - File: starview_app/utils/tasks.py

### ⚠️ Issues Found

1. **F-string Logging** - 35+ violations across 5 files (CRITICAL)
   - views_webhooks.py: 14 violations
   - utils/tasks.py: 12 violations
   - utils/email_utils.py: 4 violations
   - views_health.py: 3 violations
   - utils/exception_handler.py: 2 violations

2. **Print Statement** - 1 violation in migrations
   - starview_app/migrations/0010_add_quality_and_pioneer_badges.py (line 101)

3. **Mixed Logging Patterns** - Some files use parameterized logging correctly, others use f-strings

### 📋 Recommended Actions

1. **High Priority:** Replace all f-string logging with parameterized logging
2. **Medium Priority:** Replace print statement in migration with logger
3. **Low Priority:** Add more structured logging (extra={}) to webhook handlers

---

## Configuration

### Django Settings (`django_project/settings.py`)

```python
import logging

# Configure module logger for settings
logger = logging.getLogger(__name__)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    # Log formatting
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },

    # Log handlers (where logs go)
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'audit.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'json',
        },
    },

    # Loggers (what to log)
    'loggers': {
        # Audit logger for security events
        'audit': {
            'handlers': ['audit_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Application logger for general events
        'starview_app': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Log Levels by Environment

**Current Configuration (settings.py):**
```python
# Both loggers are set to INFO level
'loggers': {
    'audit': {
        'handlers': ['audit_file', 'console'],
        'level': 'INFO',  # INFO and above only
        'propagate': False,
    },
    'starview_app': {
        'handlers': ['console'],
        'level': 'INFO',  # INFO and above only
        'propagate': False,
    },
}
```

**Recommended Settings:**

**Development:**
```python
'level': 'DEBUG'  # Show all logs including debug messages
```

**Production:**
```python
'level': 'INFO'  # Show INFO, WARNING, ERROR, CRITICAL only (current setting)
```

**Note:** The current configuration uses INFO level for both development and production. To enable DEBUG logs during development, change the level in settings.py or use environment variables.

---

## Logger Creation

### Module-Level Logger (Recommended)

**Pattern:** Create one logger per module at the top of the file.

```python
import logging

# Configure module logger
logger = logging.getLogger(__name__)

# Now use logger throughout the module
def my_function():
    logger.info("Function called")
```

**Why `__name__`?**
- Automatically uses module path (e.g., `starview_app.models.model_location`)
- Hierarchical logging (can configure parent/child loggers)
- Easy to filter logs by module in production

### Examples from Starview Codebase

**Settings Module:**
```python
# django_project/settings.py
import logging
logger = logging.getLogger(__name__)
```

**Model Module:**
```python
# starview_app/models/model_location.py
import logging
logger = logging.getLogger(__name__)
```

**Signal Module:**
```python
# starview_app/utils/signals.py
import logging
logger = logging.getLogger(__name__)
```

---

## Log Levels

### When to Use Each Level

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Detailed diagnostic info (development only) | Variable values, function entry/exit |
| **INFO** | General informational messages | Successful operations, configuration |
| **WARNING** | Something unexpected but handled | Deprecated features, recoverable errors |
| **ERROR** | Error that prevented operation | Failed API calls, database errors |
| **CRITICAL** | Severe error, application may crash | Database unavailable, critical service down |

### Examples

```python
# DEBUG - Detailed diagnostic info
logger.debug("Processing user input: %s", user_data)

# INFO - Normal operations
logger.info("User %s logged in successfully", username)

# WARNING - Unexpected but handled
logger.warning("API rate limit approaching: %d/%d", current, limit)

# ERROR - Operation failed
logger.error("Failed to send email to %s: %s", email, str(error))

# CRITICAL - System failure
logger.critical("Database connection lost, shutting down")
```

---

## Message Formatting

### ✅ DO: Parameterized Logging

**Use % formatting (lazy evaluation):**

```python
# CORRECT - Message formatted only if log level is enabled
logger.info("User %s created location %d", username, location_id)
logger.debug("Processing %d items", item_count)
```

**Benefits:**
- Lazy evaluation (no formatting if log level disabled)
- Performance optimization
- Safer (no string interpolation vulnerabilities)

### ❌ DON'T: f-strings or .format()

```python
# WRONG - String formatted even if DEBUG is disabled
logger.debug(f"Processing {item_count} items")

# WRONG - .format() called before logging
logger.info("User {} logged in".format(username))
```

**Why not?**
- String formatted even if log level is disabled (performance hit)
- Potential security issues (untrusted input)
- Not following Python logging best practices

### Exception Logging

**Use `exc_info=True` for stack traces:**

```python
try:
    process_payment(amount)
except Exception as e:
    logger.error(
        "Payment processing failed for amount %s: %s",
        amount,
        str(e),
        exc_info=True  # Includes full stack trace
    )
```

---

## Structured Logging

### Adding Context with `extra={}`

**Pattern:** Use `extra` dict for structured data.

```python
logger.info(
    "User %s created location %d",
    username,
    location_id,
    extra={
        'user_id': user.id,
        'location_id': location_id,
        'action': 'location_create',
        'ip_address': request.META.get('REMOTE_ADDR')
    }
)
```

**Benefits:**
- Machine-readable logs (for parsing/analysis)
- Easy filtering in production
- Consistent structure across codebase
- Works with log aggregation tools (Sentry, Datadog, etc.)

### Examples from Starview

**Settings Configuration:**
```python
logger.info(
    "Using Cloudflare R2 for media files (Bucket: %s)",
    AWS_STORAGE_BUCKET_NAME,
    extra={'storage_backend': 'r2', 'bucket': AWS_STORAGE_BUCKET_NAME}
)
```

**Location Enrichment:**
```python
logger.info(
    "Queued async enrichment task for location '%s' (ID: %d)",
    self.name,
    self.pk,
    extra={'location_id': self.pk, 'location_name': self.name, 'mode': 'async'}
)
```

**Signal Handler:**
```python
logger.info(
    "Deleted %d EmailConfirmation record(s) for verified user: %s",
    deleted_count,
    email_address.email,
    extra={'action': 'email_cleanup', 'count': deleted_count, 'email': email_address.email}
)
```

---

## Common Patterns

### Pattern 1: Model Save Operations

```python
def save(self, *args, **kwargs):
    try:
        # Validate and process
        self.full_clean()

        # Log important state changes
        logger.info(
            "Saving %s (ID: %s)",
            self.__class__.__name__,
            self.pk or 'new',
            extra={'model': self.__class__.__name__, 'id': self.pk}
        )

        super().save(*args, **kwargs)

    except Exception as e:
        logger.error(
            "Error saving %s: %s",
            self.__class__.__name__,
            str(e),
            extra={'model': self.__class__.__name__, 'error': str(e)},
            exc_info=True
        )
        raise
```

### Pattern 2: API Calls

```python
def fetch_geocoding_data(latitude, longitude):
    try:
        logger.debug(
            "Fetching geocoding data for coordinates (%f, %f)",
            latitude,
            longitude
        )

        response = requests.get(api_url, params=params)
        response.raise_for_status()

        logger.info(
            "Successfully fetched geocoding data",
            extra={'lat': latitude, 'lon': longitude, 'status': response.status_code}
        )

        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(
            "Geocoding API request failed: %s",
            str(e),
            extra={'lat': latitude, 'lon': longitude, 'error': str(e)},
            exc_info=True
        )
        raise
```

### Pattern 3: Signal Handlers

```python
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        logger.info(
            "Creating profile for new user: %s",
            instance.username,
            extra={'user_id': instance.id, 'username': instance.username}
        )
        UserProfile.objects.create(user=instance)
```

### Pattern 5: Audit Logging (Security Events)

**IMPORTANT:** Security events should use the dedicated `audit` logger and custom audit functions.

```python
from starview_app.utils.audit_logger import log_auth_event, log_admin_action, log_permission_denied

# Authentication events
log_auth_event(
    request=request,
    event_type='login_success',
    user=user,
    success=True,
    message='User logged in successfully',
    metadata={'method': 'password'}
)

# Admin actions
log_admin_action(
    request=request,
    event_type='location_verified',
    user=request.user,
    message='Location marked as verified',
    metadata={'location_id': location.id}
)

# Permission denials
log_permission_denied(
    request=request,
    user=request.user,
    resource='/api/admin/users/',
    message='Non-staff user attempted to access admin endpoint'
)
```

**Why use audit logger?**
- Logs to both database (AuditLog model) and file (logs/audit.log)
- Structured JSON format for easy parsing and analysis
- Automatic IP address and user agent capture
- Immutable audit trail for compliance and security investigations
- Configured in settings.py with separate handler and formatter

### Pattern 4: Celery Tasks

**IMPORTANT:** Celery tasks should use `get_task_logger()` instead of `logging.getLogger(__name__)` for proper integration with Celery's logging infrastructure.

```python
from celery import shared_task
from celery.utils.log import get_task_logger

# Get Celery logger (integrates with Celery's logging system)
logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def enrich_location_data(self, location_id):
    logger.info(f"Starting enrichment for location ID: {location_id}")

    try:
        location = Location.objects.get(id=location_id)
        # Enrichment logic...

        logger.info(f"Enrichment complete for location {location_id}")

    except Location.DoesNotExist:
        logger.error(f"Location {location_id} not found - may have been deleted")
    except Exception as exc:
        logger.error(f"Unexpected error enriching location {location_id}: {str(exc)}")
        raise self.retry(exc=exc)
```

**Why use `get_task_logger()`?**
- Automatically includes task name and ID in log messages
- Integrates with Celery worker's logging configuration
- Properly propagates log levels from worker command (`--loglevel=info`)
- Supports distributed tracing and task monitoring

---

## Security Considerations

### ⚠️ Never Log Sensitive Data

**NEVER log:**
- Passwords (plain or hashed)
- API keys or tokens
- Credit card numbers
- Session tokens
- Private keys
- Personal identifying information (PII) without consent

**BAD:**
```python
logger.info("User login: username=%s, password=%s", username, password)  # ❌
logger.debug("API request: %s", api_key)  # ❌
logger.info("Payment: card=%s", credit_card_number)  # ❌
```

**GOOD:**
```python
logger.info("User login: username=%s", username)  # ✅
logger.debug("API request made")  # ✅
logger.info("Payment: last4=%s", card_last_four)  # ✅
```

### Sanitize User Input

**Always sanitize before logging user input:**

```python
from django.utils.html import escape

user_input = request.POST.get('comment')
sanitized = escape(user_input)

logger.info(
    "User posted comment: %s",
    sanitized[:100],  # Truncate to 100 chars
    extra={'user_id': request.user.id}
)
```

---

## Production Logs (Render)

### Viewing Logs on Render

1. Go to Render dashboard: https://dashboard.render.com
2. Select your service (starview-web)
3. Click "Logs" tab
4. Filter by log level, module, or search term

### Log Format in Production

```
INFO 2025-11-12 10:30:45 model_location Queued async enrichment task for location 'Dark Sky Park' (ID: 123)
```

**Format:** `{LEVEL} {TIMESTAMP} {MODULE} {MESSAGE}`

### Searching Production Logs

**By level:**
- Filter: `ERROR` (shows only errors)
- Filter: `WARNING` (shows warnings and above)

**By module:**
- Filter: `model_location` (location-related logs)
- Filter: `signals` (signal handler logs)

**By keyword:**
- Search: `enrichment` (all enrichment logs)
- Search: `user_id:123` (logs with user_id=123)

### Log Retention

**Render:**
- Recent logs: Available in dashboard (last 7 days)
- Historical logs: Configure external logging service (Sentry, Datadog)

---

## Common Pitfalls

### ⚠️ CRITICAL ISSUE: F-strings in Production Code

**STATUS:** Multiple violations found in production code (as of 2025-11-27)

**Files with f-string logging violations:**
- `starview_app/views/views_webhooks.py` - 14 violations
- `starview_app/views/views_health.py` - 3 violations
- `starview_app/utils/email_utils.py` - 4 violations
- `starview_app/utils/tasks.py` - 12 violations
- `starview_app/utils/exception_handler.py` - 2 violations

**Example violations:**
```python
# WRONG - f-strings are evaluated BEFORE logging check
logger.warning(f"Invalid certificate URL: {cert_url}")
logger.error(f"Health check - Database failure: {e}", exc_info=True)
logger.info(f"Starting enrichment for location ID: {location_id}")
```

**Correct approach:**
```python
# CORRECT - Parameterized logging (lazy evaluation)
logger.warning("Invalid certificate URL: %s", cert_url)
logger.error("Health check - Database failure: %s", e, exc_info=True)
logger.info("Starting enrichment for location ID: %d", location_id)
```

**Impact:**
- Performance degradation (strings formatted even when log level is disabled)
- Increased memory usage
- Security risk (untrusted input in string interpolation)
- Not following Python logging best practices

**Action Required:**
Replace all f-string logging with parameterized logging (%s, %d formatting).

---

### ❌ Pitfall 1: Using print() Instead of logging

**BAD:**
```python
print(f"Processing item {item_id}")  # ❌
```

**GOOD:**
```python
logger.info("Processing item %s", item_id)  # ✅
```

### ❌ Pitfall 2: f-strings in Logger Calls

**BAD:**
```python
logger.debug(f"User {user.username} logged in")  # ❌
```

**GOOD:**
```python
logger.debug("User %s logged in", user.username)  # ✅
```

### ❌ Pitfall 3: Wrong Log Level

**BAD:**
```python
logger.error("User viewed profile page")  # ❌ (not an error!)
logger.debug("Database connection failed")  # ❌ (not a debug message!)
```

**GOOD:**
```python
logger.info("User viewed profile page")  # ✅
logger.error("Database connection failed")  # ✅
```

### ❌ Pitfall 4: Over-Logging

**BAD:**
```python
for item in items:
    logger.info("Processing item %d", item.id)  # ❌ (logs every iteration)
```

**GOOD:**
```python
logger.info("Processing %d items", len(items))  # ✅
# Process items...
logger.info("Finished processing %d items", len(items))  # ✅
```

### ❌ Pitfall 5: No Exception Context

**BAD:**
```python
except Exception as e:
    logger.error("Error: %s", str(e))  # ❌ (no stack trace)
```

**GOOD:**
```python
except Exception as e:
    logger.error(
        "Error processing request: %s",
        str(e),
        exc_info=True  # ✅ (includes stack trace)
    )
```

---

## Quick Reference

### Cheat Sheet

```python
import logging

# Create logger (once per module, at top)
logger = logging.getLogger(__name__)

# Log levels (least to most severe)
logger.debug("Detailed diagnostic info")
logger.info("General informational message")
logger.warning("Something unexpected but handled")
logger.error("Error that prevented operation")
logger.critical("Severe error, may crash")

# Parameterized logging (preferred)
logger.info("User %s did action %s", username, action)

# With extra context
logger.info(
    "Message",
    extra={'user_id': 123, 'action': 'create'}
)

# With exception info
try:
    risky_operation()
except Exception as e:
    logger.error("Failed: %s", str(e), exc_info=True)
```

---

## Migration Checklist

**When replacing print statements:**

- [ ] Add `import logging` to imports
- [ ] Add `logger = logging.getLogger(__name__)` at module level
- [ ] Replace each `print()` with appropriate `logger.level()`
- [ ] Use parameterized logging (% formatting, not f-strings)
- [ ] Choose correct log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- [ ] Add `extra={}` context where useful
- [ ] Add `exc_info=True` for exception logging
- [ ] Test logging output locally
- [ ] Verify logs appear correctly in production

---

## Further Reading

**Django Docs:**
- https://docs.djangoproject.com/en/stable/topics/logging/

**Python Docs:**
- https://docs.python.org/3/library/logging.html
- https://docs.python.org/3/howto/logging.html

**Best Practices:**
- https://docs.python-guide.org/writing/logging/
- https://12factor.net/logs (The Twelve-Factor App)

---

## Testing

### Logging Test Suite

**Location:** `.claude/backend/tests/test_logging_output.py`

**Run:** `djvenv/bin/python .claude/backend/tests/test_logging_output.py`

**Tests:**
1. ✅ Django logging configuration (formatters, handlers, loggers)
2. ✅ Logger instance creation in modules
3. ✅ Logging output format (timestamp, level, module, message)
4. ✅ Structured logging with extra context
5. ⚠️ Print statement detection (1 violation found)
6. ✅ Location enrichment logging (sync/async modes)
7. ✅ Signal handler logging

**Recent Results:**
- 18/19 tests passing
- 1 print statement detected in migration file
- All core logging functionality working correctly

### Audit Logging Tests

**Location:** `.claude/backend/tests/phase4/test_audit_logging.py`

Tests audit logging for security events (authentication, admin actions, permission denials).

---

## Production Monitoring

### Log Files

**Location:** `/logs/audit.log` (in project root)

**Format:** JSON structured logs
```json
{"event_type": "login_success", "user": "alice", "ip_address": "192.168.1.1", "success": true, "message": "User logged in successfully", "metadata": {"method": "password"}}
```

**Rotation:**
- Max file size: 10MB
- Backups: 10 files
- Total storage: ~100MB

### Render Dashboard

**Production Logs:** https://dashboard.render.com
1. Select starview-web service
2. Click "Logs" tab
3. Filter by log level or search keywords

**Console Format:** `{LEVEL} {TIMESTAMP} {MODULE} {MESSAGE}`

Example:
```
INFO 2025-11-27 15:54:23 model_location Queued async enrichment task for location 'Dark Sky Park' (ID: 123)
```

---

## Support

For questions or issues with logging:
1. Check this guide first
2. Review `.claude/backend/ARCHITECTURE.md` for project patterns
3. Search production logs on Render dashboard
4. Run test suite: `.claude/backend/tests/test_logging_output.py`
5. Check audit logs: `/logs/audit.log`

**Last Updated:** 2025-11-27
**Audit Status:** Complete (35+ f-string violations documented, fix pending)
**Maintained By:** Starview Development Team
