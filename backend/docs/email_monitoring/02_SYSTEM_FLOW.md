# Email Monitoring System Flow - Quick Reference

## Complete System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. EMAIL SENDING                                                    │
│                                                                     │
│    views_auth.py (password reset)                                  │
│           │                                                         │
│           ├─→ EmailMultiAlternatives()                             │
│           │                                                         │
│           └─→ .send() ──────────────────────────┐                  │
│                                                  │                  │
└──────────────────────────────────────────────────┼──────────────────┘
                                                   │
                                                   ↓
                                         ┌─────────────────┐
                                         │    AWS SES      │
                                         │  (Email Server) │
                                         └─────────────────┘
                                                   │
                                    ┌──────────────┴──────────────┐
                                    │                             │
                                    ↓                             ↓
                           ┌────────────────┐            ┌─────────────────┐
                           │  Delivered ✅  │            │  BOUNCED ❌     │
                           │  (success)     │            │  or             │
                           └────────────────┘            │  COMPLAINED 🚫  │
                                                         └─────────────────┘
                                                                  │
                                                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. AWS SES DETECTS ISSUE                                            │
│                                                                     │
│    - Recipient server rejects email (bounce)                        │
│    - OR user clicks "Mark as spam" (complaint)                      │
│                                                                     │
│    SES automatically publishes event to SNS                         │
└──────────────────────────────────────────┬──────────────────────────┘
                                           │
                                           ↓
                                  ┌─────────────────┐
                                  │    AWS SNS      │
                                  │  (Notification) │
                                  └─────────────────┘
                                           │
                         ┌─────────────────┴─────────────────┐
                         │                                   │
                         ↓                                   ↓
         ┌──────────────────────────┐      ┌──────────────────────────┐
         │  SNS Topic: ses-bounces  │      │ SNS Topic: ses-complaints│
         │  (subscribed endpoints)  │      │  (subscribed endpoints)  │
         └──────────────────────────┘      └──────────────────────────┘
                         │                                   │
                         │ POST to webhook                   │
                         ↓                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. DJANGO WEBHOOK RECEIVES NOTIFICATION                             │
│                                                                     │
│    POST /api/webhooks/ses-bounce/                                  │
│    POST /api/webhooks/ses-complaint/                               │
│                                                                     │
│    File: views_webhooks.py                                         │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. SECURITY: VERIFY SNS SIGNATURE                                   │
│                                                                     │
│    Function: verify_sns_message()                                  │
│                                                                     │
│    - Download AWS public certificate                               │
│    - Verify cryptographic signature                                │
│    - Prevent spoofing attacks                                      │
│                                                                     │
│    If invalid → Return 403 Forbidden                               │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 5. PARSE NOTIFICATION                                               │
│                                                                     │
│    {                                                                │
│      "notificationType": "Bounce",                                  │
│      "bounce": {                                                    │
│        "bounceType": "Permanent",                                   │
│        "bouncedRecipients": [                                       │
│          {"emailAddress": "baduser@invalid.com"}                    │
│        ]                                                            │
│      }                                                              │
│    }                                                                │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 6. SAVE TO DATABASE                                                 │
│                                                                     │
│    Model: EmailBounce or EmailComplaint                            │
│    File: models/email_events/model_email_bounce.py                 │
│                                                                     │
│    EmailBounce.objects.create(                                     │
│       email='baduser@invalid.com',                                 │
│       bounce_type='hard',                                          │
│       bounce_count=1,                                              │
│       diagnostic_code='550 User not found',                        │
│       sns_message_id='unique-sns-id',  # Prevents duplicate processing│
│       raw_notification={...}  # Full SNS payload                   │
│    )                                                               │
│                                                                     │
│    NOTE: sns_message_id is unique - prevents processing same bounce twice│
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 7. CHECK SUPPRESSION RULES                                          │
│                                                                     │
│    Function: bounce_record.should_suppress()                       │
│                                                                     │
│    Rules:                                                           │
│    - Hard bounce → Suppress immediately                            │
│    - Soft bounce (3+ times) → Suppress                             │
│    - Transient → Never suppress                                    │
│    - Complaint → Suppress immediately                              │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 8. ADD TO SUPPRESSION LIST (if needed)                              │
│                                                                     │
│    Model: EmailSuppressionList                                     │
│    File: models/email_events/model_email_suppressionlist.py        │
│                                                                     │
│    EmailSuppressionList.add_to_suppression(                        │
│       email='baduser@invalid.com',                                 │
│       reason='hard_bounce',                                        │
│       bounce=bounce_record                                         │
│    )                                                               │
│                                                                     │
│    Future marketing emails to this address will be blocked         │
│    (Transactional emails like password reset still send!)          │
│                                                                     │
│    NOTE: Django's default send_mail() does NOT check suppression   │
│    Use send_email_safe() from email_utils.py for marketing emails  │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 9. ADMIN VISIBILITY                                                 │
│                                                                     │
│    File: admin.py                                                  │
│                                                                     │
│    Django Admin Interface:                                         │
│    - /admin/starview_app/emailbounce/                              │
│    - /admin/starview_app/emailcomplaint/                           │
│    - /admin/starview_app/emailsuppressionlist/                     │
│                                                                     │
│    Admins can:                                                     │
│    - View bounce/complaint details                                 │
│    - See diagnostic codes                                          │
│    - Manually suppress/unsuppress                                  │
│    - Generate reports                                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## File Responsibilities

| File | Purpose | What It Does |
|------|---------|--------------|
| **views_auth.py** | Sends emails | Password reset, verification emails (using Django's send_mail) |
| **views_webhooks.py** | Receives notifications | Processes bounce/complaint webhooks from AWS SNS (plain Django views, CSRF exempt) |
| **model_email_bounce.py** | Stores bounces | Database table for bounce events with bounce_type, bounce_count, diagnostic_code |
| **model_email_complaint.py** | Stores complaints | Database table for spam complaints with complaint_type, feedback_id |
| **model_email_suppressionlist.py** | Master blocklist | Emails that should not receive marketing emails (unique email constraint) |
| **admin.py** | Admin interface | View/manage bounces, complaints, suppressions (lines 220-823) |
| **email_utils.py** | Helper functions | Check suppression, send safe emails, get stats, bulk suppress |
| **cleanup_email_suppressions.py** | Maintenance | Remove old bounces, auto-recover soft bounces, email weekly reports |
| **urls.py** | URL routing | Maps `/api/webhooks/ses-bounce/` and `/api/webhooks/ses-complaint/` to webhook views |

---

## Data Flow by Bounce Type

### Hard Bounce (Permanent Failure)
```
Email sent → Bounces (user doesn't exist)
           → AWS SES detects
           → SNS publishes to ses-bounces topic
           → Django webhook receives
           → EmailBounce created (bounce_type='hard', bounce_count=1)
           → should_suppress() returns True (hard bounce)
           → EmailSuppressionList created (reason='hard_bounce')
           → Future marketing emails blocked ✅
           → Transactional emails still send ✅
```

### Soft Bounce (Temporary Failure)
```
Email sent → Bounces (mailbox full)
           → AWS SES detects
           → SNS publishes
           → Django webhook receives
           → EmailBounce created (bounce_type='soft', bounce_count=1)
           → should_suppress() returns False (< 3 bounces)
           → NOT suppressed yet ✅

(Same email bounces again 2 days later)
           → Webhook checks: EmailBounce.objects.filter(email=...).first()
           → UPDATES existing record (not create new):
               - bounce_count incremented (1 → 2)
               - bounce_type updated to latest
               - diagnostic_code updated
               - last_bounce_date updated automatically
           → should_suppress() returns False (< 3 bounces)
           → Still NOT suppressed ✅

(Same email bounces AGAIN)
           → EmailBounce updated (bounce_count=3)
           → should_suppress() returns True (>= 3 bounces)
           → EmailSuppressionList created (reason='soft_bounce')
           → bounce.suppressed = True
           → Now suppressed for marketing ✅
           → Auto-recovery after 30 days (cleanup command) ✅
```

### Spam Complaint
```
Email sent → Delivered successfully
           → User clicks "Mark as spam"
           → ISP reports to AWS SES
           → SNS publishes to ses-complaints topic
           → Django webhook receives
           → EmailComplaint created
           → EmailSuppressionList created IMMEDIATELY (complaints are critical!)
           → Admin notified for review
           → Future marketing emails blocked ✅
```

### Transient (Connection Issue)
```
Email sent → Connection timeout
           → AWS SES retries
           → Eventually succeeds OR gives up
           → SNS publishes bounce (bounceType='Transient')
           → Django webhook receives
           → EmailBounce created (bounce_type='transient')
           → should_suppress() returns False (never suppress transient)
           → NOT suppressed ✅
           → Auto-deleted after 7 days (cleanup command) ✅
```

---

## AWS Configuration Summary

### Required AWS Resources

1. **SNS Topics** (2 topics)
   - `ses-bounces` (Standard, not FIFO)
   - `ses-complaints` (Standard, not FIFO)

2. **SNS Subscriptions** (2 subscriptions)
   - `ses-bounces` → `https://starview.app/api/webhooks/ses-bounce/`
   - `ses-complaints` → `https://starview.app/api/webhooks/ses-complaint/`

3. **SES Identity Settings** (1 configuration)
   - Verified identity: `starview.app` or `noreply@starview.app`
   - Bounce feedback: Link to `ses-bounces` topic
   - Complaint feedback: Link to `ses-complaints` topic

### Testing Endpoints

| Test Email | Result |
|------------|--------|
| `bounce@simulator.amazonses.com` | Always hard bounces |
| `complaint@simulator.amazonses.com` | Always generates complaint |
| `success@simulator.amazonses.com` | Always succeeds |
| `ooto@simulator.amazonses.com` | Out of office (soft bounce) |
| `suppressionlist@simulator.amazonses.com` | On SES suppression list |

---

## Quick Testing Script

```python
# In Django shell: python manage.py shell

from django.core.mail import send_mail
from starview_app.models import EmailBounce, EmailSuppressionList

# Send test email
send_mail(
    subject='Test Bounce',
    message='Testing bounce handling',
    from_email='noreply@starview.app',
    recipient_list=['bounce@simulator.amazonses.com'],
    fail_silently=False,
)

# Wait 30 seconds for webhook to process
import time
time.sleep(30)

# Check database
bounces = EmailBounce.objects.all()
print(f"Bounces: {bounces.count()}")
if bounces.exists():
    b = bounces.first()
    print(f"Email: {b.email}")
    print(f"Type: {b.bounce_type}")
    print(f"Count: {b.bounce_count}")
    print(f"Suppressed: {b.suppressed}")

suppressed = EmailSuppressionList.objects.all()
print(f"\nSuppressed emails: {suppressed.count()}")
if suppressed.exists():
    s = suppressed.first()
    print(f"Email: {s.email}")
    print(f"Reason: {s.reason}")
```

---

## Monitoring

You monitor in **two places**: AWS Console (overall metrics) and Django Admin (detailed records).

---

### Monitoring Quick Reference

| What | Where | When | Action |
|------|-------|------|--------|
| **Bounce/Complaint Rates** | AWS SES Console | Weekly | Verify < 5% bounce, < 0.1% complaint |
| **Spam Complaints** | Django Admin | **Daily/Immediately** | Review and mark as reviewed |
| **Bounce Details** | Django Admin | Weekly | Look for patterns, check diagnostics |
| **Suppression List** | Django Admin | Monthly | Verify justified, remove false positives |
| **SNS Delivery** | AWS SNS Console | Monthly | Ensure delivery failures = 0 |
| **Statistics Report** | Management Command | Weekly/Monthly | Track trends over time |

---

### AWS Console (Weekly)

**1. AWS SES Reputation Dashboard:**

```
AWS Console → SES → Reputation dashboard
```

**Check:**
- **Bounce Rate**: < 5% (AWS requirement)
- **Complaint Rate**: < 0.1% (AWS requirement)
- **Reputation Status**: "Healthy"

**If rates high:**
→ Go to Django Admin to investigate specific addresses
→ Review bounce diagnostic codes
→ Check for pattern (same domain bouncing repeatedly?)

**2. AWS SNS Topic Metrics:**

```
AWS Console → SNS → Topics → ses-bounces → Monitoring tab
```

**Check:**
- **Messages Published**: Should match bounce count
- **Delivery Failures**: Should be 0 (webhooks working)

**If delivery failures > 0:**
→ Check Render logs for webhook errors
→ Verify subscription still confirmed
→ Test webhook URL accessibility

---

### Django Admin (Daily/Weekly)

**DAILY - Email Complaints:**

```
https://www.starview.app/admin/starview_app/emailcomplaint/
```

**Actions:**
1. Review new complaints immediately (CRITICAL priority)
2. Check complaint type (abuse, fraud, virus)
3. Investigate why user complained:
   - Email frequency too high?
   - Content issues?
   - User didn't opt-in?
4. Mark as "Reviewed" after investigation
5. Look for patterns (multiple from same domain = problem)

**WEEKLY - Email Bounces:**

```
https://www.starview.app/admin/starview_app/emailbounce/
```

**Actions:**
1. Review new bounce records
2. Filter by bounce type (hard/soft/transient)
3. Check diagnostic codes for details
4. Look for patterns:
   - Same email domain bouncing?
   - Specific content causing bounces?
   - Recent spike in bounce rate?
5. Investigate hard bounces (permanent issues)

**MONTHLY - Suppression List:**

```
https://www.starview.app/admin/starview_app/emailsuppressionlist/
```

**Actions:**
1. Review newly suppressed emails
2. Verify suppressions are justified
3. Check suppression reasons (hard_bounce, complaint, etc.)
4. Remove false positives if needed (rare)
5. Monitor list growth (should be slow/steady)

---

### Management Commands

**Weekly Cleanup:**

```bash
# Run on production server (Render Shell)
python manage.py cleanup_email_suppressions --report
```

**What it does:**
- Recovers soft bounces after 30 days (mailbox might be fixed)
- Deletes transient bounces after 7 days (temporary issues)
- Cleans stale records (90+ days, no activity)
- Shows statistics report

**Monthly Statistics:**

```bash
python manage.py shell -c "
from starview_app.utils.email_utils import get_email_statistics
stats = get_email_statistics()
print('='*60)
print('EMAIL HEALTH REPORT')
print('='*60)
for key, value in stats.items():
    print(f'{key}: {value}')
print('='*60)
"
```

**Output Example:**
```
============================================================
EMAIL HEALTH REPORT
============================================================
total_bounces: 42
hard_bounces: 10
soft_bounces: 30
transient_bounces: 2
total_complaints: 3
suppressed_emails: 13
active_suppressions: 11
inactive_suppressions: 2
============================================================
```

---

### Admin Features Reference

**Search:**
- Find specific email addresses
- Search by email domain (e.g., "@gmail.com")

**Filters (Right sidebar):**
- Bounce type (hard/soft/transient)
- Suppression reason (hard_bounce, complaint, etc.)
- Status (active/inactive, suppressed/not suppressed)
- Date range (last 7 days, last month, etc.)

**Bulk Actions:**
- Suppress multiple emails at once
- Unsuppress multiple emails (careful!)
- Mark complaints as reviewed

**Color Coding:**
- 🔴 **Red**: Critical (hard bounce, complaint, suppressed, active)
- 🟠 **Orange**: Attention needed (soft bounce, pending review)
- 🟢 **Green**: Normal (transient bounce)

---

### Setting Up Monitoring (Optional)

**Option 1: CloudWatch Alarms**

Set up AWS CloudWatch alarms to email you:
- Bounce rate > 3% (warning before 5% limit)
- Complaint rate > 0.05% (warning before 0.1% limit)

**Option 2: Render Log Alerts**

Configure Render to notify you:
- CRITICAL log level = new complaint
- ERROR log level = webhook failure

**Option 3: Cron Job (Weekly Report)**

Set up weekly automated reports:
```bash
# Add to Render Cron Jobs
0 9 * * 1 python manage.py cleanup_email_suppressions --report
```

Emails you a weekly summary every Monday at 9 AM.

---

**For detailed setup instructions, see: `.claude/backend/docs/email_monitoring/01_AWS_SETUP_GUIDE.md`**
