# Backend Test Suite

This directory contains comprehensive test scripts for the Starview Django backend, covering security, performance, badge system, and infrastructure.

## Directory Structure

```
.claude/backend/tests/
├── README.md              # This file
├── phase1/                # Critical Security (8 tests, 26 test functions)
├── phase2/                # Production Readiness (5 tests, 8 test functions)
├── phase3/                # AWS SES Migration (1 test, 2 test functions)
├── phase4/                # Hardening & Infrastructure (7 tests, 5 test functions)
├── phase5/                # Monitoring (1 test, 5 test functions)
├── phase6/                # Authentication (2 tests, 8 test functions)
├── phase7/                # Badge Fixes (4 tests, 6 test functions)
├── phase_badge/           # Badge System (5 tests, 26 test functions)
├── verification/          # Storage & Constraints (3 tests, 8 test functions)
└── [root test files]      # Integration & Performance (15+ tests, 48+ test functions)
```

**Total: 142+ test functions across 51+ test files**

## Test Coverage by Category

| Category | Test Functions | Key Areas |
|----------|----------------|-----------|
| **Security** | 34 | Rate limiting, XSS, file uploads, lockout, spam prevention |
| **Performance** | 21 | N+1 queries, caching, query optimization |
| **Badge System** | 38 | Badge awarding, progress, caching, revocation |
| **Authentication** | 16 | Password reset, email change, social auth |
| **Infrastructure** | 13 | Health checks, Celery, storage, logging |
| **Email** | 4 | AWS SES, Spanish templates |
| **API** | 16 | Endpoints, validation, constraints |

## Quick Reference

```bash
# Start Django server (required for most tests)
djvenv/bin/python manage.py runserver

# Run a specific test
djvenv/bin/python .claude/backend/tests/phase1/test_rate_limiting.py

# Run all tests in a phase
for test in .claude/backend/tests/phase1/*.py; do djvenv/bin/python "$test"; done

# Run badge system tests
djvenv/bin/python .claude/backend/tests/phase_badge/test_badge_system.py

# Run performance benchmarks
djvenv/bin/python .claude/backend/tests/medium_issue5_after.py
```

## Running Tests

**IMPORTANT:** Always use the Django virtual environment Python interpreter:

```bash
# From project root (/Users/adiaz/event-horizon/)
djvenv/bin/python .claude/backend/tests/phase1/test_[feature].py
```

**Never use system Python** - it doesn't have Django and project dependencies installed.

## Test Organization

### Phase 1: Critical Security (26 test functions)
- `test_rate_limiting.py` - DRF throttling (API, login, registration)
- `test_file_upload.py` - File size, MIME type, extension validation
- `test_xss_sanitization.py` - Input sanitization with bleach
- `test_coordinate_validation.py` - Geographic bounds validation
- `test_api_timeouts.py` - External API timeout handling
- `test_content_spam_prevention.py` - Content creation rate limits (20/hour locations, reviews, comments)
- `test_email_change_security.py` - Email change verification flow
- `test_sensitive_info.py` - Protection of sensitive user data

### Phase 2: Production Readiness (8 test functions)
- `test_query_optimization.py` - N+1 query detection
- `test_api_query_optimization.py` - API endpoint query analysis
- `test_detailed_queries.py` - Database query efficiency
- `test_redis_caching.py` - Cache hit/miss rates
- `create_test_data.py` - Test data generator

### Phase 3: AWS SES (2 test functions)
- `test_aws_ses_email.py` - AWS SES email delivery

### Phase 4: Hardening & Infrastructure (5 test functions)
- `test_account_lockout.py` - django-axes lockout (5 failed attempts)
- `test_audit_logging.py` - Security event logging
- `test_celery_tasks.py` - Async task execution (optional tier)
- `test_exception_handler.py` - Custom DRF exception handling
- `test_pilot_refactoring.py` - Pilot refactoring validation
- `test_refactored_views.py` - Refactored view validation
- `verify_throttling_enabled.py` - Throttle configuration check

### Phase 5: Monitoring (5 test functions)
- `test_health_check.py` - Database, cache, storage health checks

### Phase 6: Authentication (8 test functions)
- `test_password_reset.py` - Password reset flow
- `test_password_reset_rate_limit.py` - Password reset throttling

### Phase 7: Badge Fixes (6 test functions)
- `test_1_self_review_prevention.py` - Prevent self-review badge exploit
- `test_2_conversationalist_badge.py` - Comment count badge logic
- `test_3_quality_badges.py` - Quality badge criteria
- `test_4_review_badges_upvote_ratio.py` - Upvote ratio badge logic

### Phase Badge: Badge System (26 test functions)
- `test_badge_system.py` - Complete badge system integration
- `test_badge_api.py` - Badge API endpoints
- `test_badge_comprehensive.py` - Comprehensive badge awarding
- `test_badge_revocation.py` - Badge revocation logic
- `test_all_badge_categories.py` - All badge categories validation

### Verification: Storage & Constraints (8 test functions)
- `test_local_storage.py` - Local file storage validation
- `test_r2_upload.py` - Cloudflare R2 upload validation
- `test_review_constraints.py` - Review constraint validation

### Root Directory: Integration & Performance (48+ test functions)
- `badge_performance_test.py` - Badge system performance
- `contenttype_cache_test.py` - ContentType caching optimization
- `contenttype_cache_comparison.py` - Cache comparison metrics
- `contenttype_functional_test.py` - ContentType functional tests
- `n1_query_test.py` - N+1 query detection
- `test_badge_progress_integration.py` - Badge progress integration
- `test_badge_progress_caching.py` - Badge progress caching
- `test_badge_fetching_functional.py` - Badge fetching optimization
- `test_badge_indexes_integration.py` - Badge database indexes
- `test_review_badges_functional.py` - Review badge functionality
- `test_email_change_verification.py` - Email change verification
- `test_spanish_emails.py` - Spanish email templates
- `test_auth_status.py` - Authentication status check
- `test_follow_in_user_response.py` - Follow status in user API
- `medium_issue5_before.py` / `medium_issue5_after.py` - Performance fix validation
- `medium_issue6_before.py` / `medium_issue6_after.py` - Performance fix validation
- `medium_issue7_before.py` / `medium_issue7_after.py` - Performance fix validation

## Writing New Tests

When creating a new test script:

1. **Name it descriptively:** `test_[feature_name].py`
2. **Place in appropriate phase directory**
3. **Include docstring** explaining what's being tested
4. **Use requests library** for API testing
5. **Target local dev server:** `http://127.0.0.1:8000`
6. **Return exit codes:** 0 for success, 1 for failure
7. **Print clear results:** Use ✅/❌ for pass/fail

### Example Template:

```python
#!/usr/bin/env python3
"""
Feature Name Test Script

Tests implementation of [security feature].
"""

import requests

BASE_URL = "http://127.0.0.1:8000"

def test_feature():
    """Test description"""
    # Test implementation
    pass

def main():
    print("="*60)
    print("FEATURE NAME TEST SUITE")
    print("="*60)

    try:
        result = test_feature()

        if result:
            print("✅ ALL TESTS PASSED")
            return 0
        else:
            print("❌ TESTS FAILED")
            return 1

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
```

## Test Types

This test suite includes multiple testing approaches:

### 1. **Standalone Integration Tests**
Scripts that run independently, testing specific features end-to-end:
- Located in phase directories (phase1-7)
- Use `requests` library to test live Django server
- Return exit codes: 0 (success), 1 (failure)
- Example: `test_rate_limiting.py`, `test_xss_sanitization.py`

### 2. **Django TestCase Tests**
Standard Django unit tests using Django's TestCase:
- Located in phase4 and verification directories
- Use Django test framework with database transactions
- Example: `test_account_lockout.py`, `test_review_constraints.py`

### 3. **Performance Benchmarks**
Before/after comparison tests for performance optimizations:
- Located in root directory with `_before` and `_after` suffixes
- Measure query counts and execution time
- Example: `medium_issue5_before.py` vs `medium_issue5_after.py`

### 4. **Functional Integration Tests**
Complex multi-step tests validating entire workflows:
- Located in root directory and phase_badge
- Test badge awarding, caching, progress calculation
- Example: `test_badge_fetching_functional.py`, `contenttype_functional_test.py`

## Critical Tests for Deployment

Before deploying to production, ensure these critical tests pass:

### Security (Must Pass)
```bash
# Rate limiting and spam prevention
djvenv/bin/python .claude/backend/tests/phase1/test_rate_limiting.py
djvenv/bin/python .claude/backend/tests/phase1/test_content_spam_prevention.py

# XSS and input validation
djvenv/bin/python .claude/backend/tests/phase1/test_xss_sanitization.py
djvenv/bin/python .claude/backend/tests/phase1/test_file_upload.py

# Account security
djvenv/bin/python .claude/backend/tests/phase4/test_account_lockout.py
djvenv/bin/python .claude/backend/tests/phase1/test_email_change_security.py
```

### Performance (Should Pass)
```bash
# Query optimization
djvenv/bin/python .claude/backend/tests/phase2/test_query_optimization.py
djvenv/bin/python .claude/backend/tests/n1_query_test.py

# Caching
djvenv/bin/python .claude/backend/tests/phase2/test_redis_caching.py
djvenv/bin/python .claude/backend/tests/contenttype_cache_test.py
```

### Infrastructure (Should Pass)
```bash
# Health checks
djvenv/bin/python .claude/backend/tests/phase5/test_health_check.py

# Storage (if using R2)
djvenv/bin/python .claude/backend/tests/verification/test_r2_upload.py
```

## Prerequisites

- Django development server must be running at http://127.0.0.1:8000
- Virtual environment must be activated (or use `djvenv/bin/python`)
- All dependencies must be installed in virtual environment
- Redis server running (for caching tests)
- AWS SES configured (for email tests)

## Troubleshooting

**"ModuleNotFoundError: No module named 'requests'"**
- Install in venv: `djvenv/bin/pip install requests`

**"Connection refused"**
- Start Django server: `djvenv/bin/python manage.py runserver`

**"ImportError: No module named 'django'"**
- You're using system Python instead of venv Python
- Use: `djvenv/bin/python` instead of `python3`
