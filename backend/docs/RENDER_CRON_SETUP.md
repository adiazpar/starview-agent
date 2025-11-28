# Render Cron Job Setup Guide

Complete guide for setting up scheduled maintenance tasks for Starview in production.

---

## Table of Contents

1. [Production Cron Jobs Overview](#production-cron-jobs-overview)
2. [Quick Start: Setup Instructions](#quick-start-production-cron-jobs)
   - [Cron Job #1: Cleanup Unverified Users](#cron-job-1-cleanup-unverified-users)
   - [Cron Job #2: Cleanup Email Suppressions](#cron-job-2-cleanup-email-suppressions)
   - [Cron Job #3: Archive Audit Logs](#cron-job-3-archive-audit-logs)
3. [Common Configuration Details](#common-configuration-details)
4. [Environment Variables](#environment-variables)
5. [Testing & Monitoring](#testing--monitoring)
6. [Adding More Cron Jobs](#adding-more-cron-jobs)
7. [Troubleshooting](#troubleshooting)
8. [Cost Monitoring](#cost-monitoring)
9. [Best Practices](#best-practices)

---

## Quick Start: Production Cron Jobs

Follow these steps to set up all 3 required cron jobs for Starview in production.

---

## Cron Job #1: Cleanup Unverified Users

**Purpose:** Prevents email squatting and database bloat by deleting unverified accounts older than 7 days.

### Step 1: Create New Cron Job

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** button (top right)
3. Select **"Cron Job"**

### Step 2: Connect Repository

1. Select **"Build and deploy from a Git repository"**
2. Connect your GitHub account (if not already connected)
3. Find and select your repository: `adiaz/event-horizon` (or whatever your repo name is)
4. Click **"Connect"**

### Step 3: Configure Cron Job

**Name**: `starview-cleanup-unverified-users`

**Region**: `Oregon (US West)` (same as web service)

**Branch**: `main`

**Runtime**: `Python 3`

**Build Command**:
```bash
./build-cron.sh
```

**Start Command**:
```bash
python manage.py cleanup_unverified_users --days=7
```

**Schedule**: `0 2 * * *` (Daily at 2 AM UTC)

**Instance Type**: `Starter` ($0.00016/min)

### Step 4: Add Environment Variables

Copy ALL environment variables from your web service. See "Environment Variables" section below.

### Step 5: Deploy & Test

1. Click **"Create Cron Job"**
2. After deployment, click **"Trigger Run"** to test
3. Check logs for successful output

---

## Cron Job #2: Cleanup Email Suppressions

**Purpose:** Manages email bounce/complaint tracking, sends weekly health reports to admins.

### Step 1-2: Create & Connect

Follow same steps as Cron Job #1 (Create → Connect Repository)

### Step 3: Configure Cron Job

**Name**: `starview-cleanup-email-suppressions`

**Region**: `Oregon (US West)`

**Branch**: `main`

**Runtime**: `Python 3`

**Build Command**:
```bash
./build-cron.sh
```

**Start Command**:
```bash
python manage.py cleanup_email_suppressions --email-report your-admin@example.com
```
**⚠️ IMPORTANT:** Replace `your-admin@example.com` with your actual admin email address!

**Schedule**: `0 3 * * 0` (Every Sunday at 3 AM UTC)

**Instance Type**: `Starter`

### Step 4: Add Environment Variables

Copy ALL environment variables from your web service. See "Environment Variables" section below.

**⚠️ Required:** Email settings must be configured for weekly reports:
- `AWS_SES_ACCESS_KEY_ID`
- `AWS_SES_SECRET_ACCESS_KEY`
- `AWS_SES_REGION_NAME`
- `DEFAULT_FROM_EMAIL`

### Step 5: Deploy & Test

1. Click **"Create Cron Job"**
2. After deployment, click **"Trigger Run"** to test
3. Check your admin email for the health report

---

## Cron Job #3: Archive Audit Logs

**Purpose:** Archives old audit logs to R2 storage and removes them from database to prevent bloat.

### Step 1-2: Create & Connect

Follow same steps as Cron Job #1 (Create → Connect Repository)

### Step 3: Configure Cron Job

**Name**: `starview-archive-audit-logs`

**Region**: `Oregon (US West)`

**Branch**: `main`

**Runtime**: `Python 3`

**Build Command**:
```bash
./build-cron.sh
```

**Start Command**:
```bash
python manage.py archive_audit_logs --days=30
```

**Schedule**: `0 4 1 * *` (1st day of each month at 4 AM UTC)

**Instance Type**: `Starter`

### Step 4: Add Environment Variables

Copy ALL environment variables from your web service. See "Environment Variables" section below.

**⚠️ Required:** R2 storage credentials must be configured:
- `AWS_ACCESS_KEY_ID` (R2 credentials)
- `AWS_SECRET_ACCESS_KEY` (R2 credentials)
- `AWS_STORAGE_BUCKET_NAME`
- `CLOUDFLARE_ACCOUNT_ID`

### Step 5: Deploy & Test

1. Click **"Create Cron Job"**
2. After deployment, click **"Trigger Run"** to test
3. Check R2 bucket for archived files in `audit-archives/` folder

---

## Common Configuration Details

### Build Command: `./build-cron.sh`

Uses minimal build script (only installs Python dependencies). DO NOT use `./build.sh` (that's for web service - includes React build, migrations, etc.)

### Common Cron Schedules

```
0 2 * * *      # Daily at 2 AM UTC
0 3 * * 0      # Weekly on Sunday at 3 AM UTC
0 4 1 * *      # First day of each month at 4 AM UTC
0 */6 * * *    # Every 6 hours
*/30 * * * *   # Every 30 minutes (probably overkill)
```

Use [Crontab Guru](https://crontab.guru/) to generate custom schedules.

### Instance Type

**Plan**: `Starter` ($0.00016/min)
- This is the only option for cron jobs
- Cost: ~$0.005/month for daily 1-minute job

---

## Environment Variables

You need to copy ALL environment variables from your web service to each cron job. Here's how:

### Option A: Manual Copy (Simple)

1. Go to your web service (`starview-backend`)
2. Go to **"Environment"** tab
3. Copy each variable to the cron job:

**Required Variables:**
```
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://... (if not auto-provided)
ALLOWED_HOSTS=starview.app,www.starview.app
CSRF_TRUSTED_ORIGINS=https://starview.app
DEFAULT_FROM_EMAIL=noreply@starview.app
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_SES_REGION_NAME=us-east-2
REDIS_URL=redis://... (if using Redis)
CELERY_ENABLED=False
```

**Optional Variables:**
```
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
MAPBOX_TOKEN=...
DISABLE_EXTERNAL_APIS=False
```

### Option B: Environment Groups (Recommended for Multiple Services)

If you have multiple services/cron jobs that share variables:

1. Go to **"Account Settings"** → **"Environment Groups"**
2. Click **"New Environment Group"**
3. Name it: `starview-shared`
4. Add all shared variables
5. Link the group to your web service AND cron job

**Benefits:**
- Update once, applies everywhere
- Easier to manage
- Less chance of typos

---

## Advanced Settings (Optional)

**Docker Settings**: Leave empty (we're using Python runtime)

**Health Check Path**: Not applicable for cron jobs

**Auto-Deploy**: `Yes` (recommended)
- Automatically redeploys when you push to `main` branch

---

## Testing & Monitoring

### Manual Trigger (Testing)

1. Go to your cron job dashboard
2. Click **"Trigger Run"** button
3. Wait for it to complete (~5-30 seconds)
4. Check logs for output

### Expected Outputs

**Cleanup Unverified Users:**
```
Found 0 unverified user(s) older than 7 days:
No unverified users found to delete.
```

OR if there are unverified users:
```
Found 2 unverified user(s) older than 7 days:
Cutoff date: 2025-10-30 02:00:00

  - testuser (test@example.com) - registered 10 days ago
  - spammer (spam@fake.com) - registered 15 days ago

Deleting unverified users...
  ✓ Deleted: testuser (test@example.com)
  ✓ Deleted: spammer (spam@fake.com)

✓ Successfully deleted 2 unverified user(s)
```

**Cleanup Email Suppressions:**
```
SOFT BOUNCE CLEANUP
================================================================================
Found 3 soft bounce suppressions older than 30 days
  - user1@example.com: Last bounce 2025-01-15 (2x)
  - user2@example.com: Last bounce 2025-01-10 (1x)

Deactivated 3 soft bounce suppressions

STALE BOUNCE CLEANUP
================================================================================
Found 5 stale bounce records (inactive for 90+ days)
Deleted 5 stale bounce records

Email report sent to your-admin@example.com
```

**Archive Audit Logs:**
```
Found 1523 audit logs older than 30 days
Cutoff date: 2024-12-27 04:00:00

Production mode: Archives will be stored in R2
JSON archive uploaded to R2: audit_logs_20241001_to_20241227_20250127_040001.json
TXT archive uploaded to R2: audit_logs_20241001_to_20241227_20250127_040001.txt

Archived 1523 audit logs
Archive location: R2 bucket "starview-media" in audit-archives/ folder
```

### Monitoring

### View Logs

1. Go to cron job dashboard
2. Click **"Logs"** tab
3. See output from each run

### View Run History

1. Go to cron job dashboard
2. See list of recent runs with:
   - Timestamp
   - Duration
   - Status (success/failure)
   - Cost

## Production Cron Jobs Overview

Starview has **3 scheduled maintenance tasks** that should run in production:

| Cron Job Name | Command | Schedule | Purpose |
|---------------|---------|----------|---------|
| `starview-cleanup-unverified-users` | `python manage.py cleanup_unverified_users --days=7` | `0 2 * * *` (Daily 2 AM) | Delete unverified users, prevent email squatting |
| `starview-cleanup-email-suppressions` | `python manage.py cleanup_email_suppressions --email-report admin@example.com` | `0 3 * * 0` (Sunday 3 AM) | Clean email bounces, send weekly health report |
| `starview-archive-audit-logs` | `python manage.py archive_audit_logs --days=30` | `0 4 1 * *` (1st of month 4 AM) | Archive old audit logs to R2 storage |

**Optional Maintenance Tasks:**

| Task | Command | Suggested Schedule | Purpose |
|------|---------|-------------------|---------|
| Clear expired sessions | `python manage.py clearsessions` | `0 5 * * 0` (Sunday 5 AM) | Remove expired session data from Redis |

---

## Adding More Cron Jobs

Each cron job runs ONE command. To add more tasks:

### Example: Clear Old Sessions Cron Job

1. Create new cron job: `starview-clear-sessions`
2. Command: `python manage.py clearsessions`
3. Schedule: `0 5 * * 0` (weekly on Sunday at 5 AM)
4. Use same environment variables

**Note:** Sessions are stored in Redis (`SESSION_ENGINE = 'django.contrib.sessions.backends.cache'`) and expire automatically after 2 weeks (`SESSION_COOKIE_AGE = 1209600`). The `clearsessions` command is optional but recommended for Redis cache cleanup.

## Multi-Command Wrapper (Advanced)

If you want ONE cron job to run multiple commands:

**Create**: `starview_app/management/commands/run_maintenance.py`

```python
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Run all maintenance tasks'

    def handle(self, *args, **options):
        self.stdout.write('Running cleanup_unverified_users...')
        call_command('cleanup_unverified_users', '--days=7')

        self.stdout.write('Running clearsessions...')
        call_command('clearsessions')

        self.stdout.write('All maintenance tasks completed!')
```

**Cron Job Command**: `python manage.py run_maintenance`

**Pros**: Single cron job, easier to manage
**Cons**: If one task fails, harder to debug; all tasks run at same frequency

## Troubleshooting

### Issue: "ModuleNotFoundError" or "ImportError"

**Cause**: Dependencies not installed
**Solution**: Ensure `build.sh` or `requirements.txt` is correct

### Issue: "django.core.exceptions.ImproperlyConfigured"

**Cause**: Missing environment variables
**Solution**: Copy all required env vars from web service

### Issue: "FATAL: database does not exist"

**Cause**: DATABASE_URL not set or incorrect
**Solution**:
- If using Render PostgreSQL, link the database to the cron job
- Render will auto-inject `DATABASE_URL`

### Issue: Cron job runs but command does nothing

**Cause**: Wrong working directory
**Solution**: Ensure command is run from project root:
```bash
cd /opt/render/project/src && python manage.py cleanup_unverified_users
```

### Issue: "Secret key not set"

**Cause**: DJANGO_SECRET_KEY missing
**Solution**: Copy from web service environment variables

## Cost Monitoring

### View Costs

1. Go to **"Account Settings"** → **"Billing"**
2. See breakdown by service
3. Cron jobs listed separately

### Expected Costs for Starview Production

**Cleanup Unverified Users (daily, ~1 min/run):**
- 30 minutes/month × $0.00016 = **$0.0048/month**

**Cleanup Email Suppressions (weekly, ~1 min/run):**
- 4 minutes/month × $0.00016 = **$0.00064/month**

**Archive Audit Logs (monthly, ~1 min/run):**
- 1 minute/month × $0.00016 = **$0.00016/month**

**Total for all 3 cron jobs: ~$0.0054/month (~$0.06/year)**

Essentially negligible cost - less than a penny per month!

## Best Practices

1. ✅ **Use descriptive names**: `starview-cleanup-unverified-users` not `cron1`
2. ✅ **Set appropriate schedules**: Daily for cleanup, weekly for backups
3. ✅ **Test manually first**: Use "Trigger Run" before waiting for scheduled run
4. ✅ **Monitor logs**: Check logs after first few runs
5. ✅ **Use Environment Groups**: Share variables across services
6. ✅ **Set up alerts**: Render can notify you of failures (Settings → Notifications)
7. ✅ **Document schedules**: Keep track of what runs when

## Next Steps

After setting up the 3 production cron jobs, consider adding:

1. **Clear expired sessions** (`clearsessions`)
   - Schedule: Weekly (Sunday 5 AM)
   - Purpose: Clean up Redis session cache
   - Optional: Sessions auto-expire after 2 weeks

2. **Database backups** (requires `django-dbbackup` package)
   - Schedule: Daily or weekly
   - Purpose: Automated PostgreSQL backups to R2
   - Requires additional setup

3. **Analytics reports** (if implemented)
   - Schedule: Weekly or monthly
   - Purpose: Email summaries to admins
   - Custom management command required

4. **Badge audit** (maintenance task)
   - Command: `python manage.py audit_badges --fix`
   - Schedule: Monthly (optional)
   - Purpose: Remove invalid badges after bulk deletions

## Available Management Commands

Starview includes several management commands. Here's what should and shouldn't be scheduled:

### ✅ Recommended for Cron Jobs

| Command | Purpose | Suggested Schedule |
|---------|---------|-------------------|
| `cleanup_unverified_users` | Delete unverified users | Daily |
| `cleanup_email_suppressions` | Manage email bounces/complaints | Weekly |
| `archive_audit_logs` | Archive old audit logs to R2 | Monthly |
| `clearsessions` | Clear expired Redis sessions | Weekly (optional) |

### ⚠️ Manual/One-Time Commands (Do NOT Schedule)

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `diagnose_db` | Database diagnostics | Manual debugging only |
| `audit_badges` | Audit user badges | Manual maintenance only |
| `award_pioneer_badges` | Award Pioneer badges | One-time retroactive setup |
| `setup_google_oauth` | Configure Google OAuth | One-time initial setup |

**Important:** Do NOT create cron jobs for the manual/one-time commands. They are meant to be run manually when needed, not on a schedule.

---

## Quick Reference: Command Summary

For easy copy-paste when setting up cron jobs:

**Cron Job #1: Cleanup Unverified Users**
```
Name: starview-cleanup-unverified-users
Build: ./build-cron.sh
Start: python manage.py cleanup_unverified_users --days=7
Schedule: 0 2 * * *
```

**Cron Job #2: Cleanup Email Suppressions**
```
Name: starview-cleanup-email-suppressions
Build: ./build-cron.sh
Start: python manage.py cleanup_email_suppressions --email-report YOUR-EMAIL@example.com
Schedule: 0 3 * * 0
```

**Cron Job #3: Archive Audit Logs**
```
Name: starview-archive-audit-logs
Build: ./build-cron.sh
Start: python manage.py archive_audit_logs --days=30
Schedule: 0 4 1 * *
```

**Optional: Clear Sessions**
```
Name: starview-clear-sessions
Build: ./build-cron.sh
Start: python manage.py clearsessions
Schedule: 0 5 * * 0
```

---

## Resources

- [Render Cron Jobs Docs](https://render.com/docs/cronjobs)
- [Crontab Guru](https://crontab.guru/) - Schedule generator
- [Django Management Commands](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)
- [Django Clearsessions](https://docs.djangoproject.com/en/stable/topics/http/sessions/#clearing-the-session-store)
