# AWS SES + SNS Setup Guide

**Status:** ✅ PRODUCTION ACTIVE - System configured and monitoring live

Simple step-by-step guide to configure email bounce and complaint monitoring.

---

## What This Does

Automatically tracks when emails bounce or get marked as spam, saving records to your Django database.

**Flow:** Your App → AWS SES → Email bounces → AWS SNS → Your webhook → Database

**Current Production Status:**
- ✅ SNS topics created: `ses-bounces` and `ses-complaints`
- ✅ Webhook subscriptions confirmed: `https://starview.app/api/webhooks/ses-bounce/` and `/ses-complaint/`
- ✅ SES identity linked to SNS topics
- ✅ Real-time bounce and complaint tracking active
- ✅ Weekly automated cleanup cronjob configured

---

## Prerequisites

- ✅ AWS account with SES configured
- ✅ Verified domain in SES (e.g., `starview.app`)
- ✅ Django app deployed at `https://starview.app` (or `https://www.starview.app`)
- ✅ SNS and SES in same AWS region
- ✅ Environment variables configured in Django:
  - `AWS_SES_ACCESS_KEY_ID` - AWS credentials for SES
  - `AWS_SES_SECRET_ACCESS_KEY` - AWS secret key
  - `AWS_SES_REGION_NAME` - Region (e.g., `us-east-2`)
  - `DEFAULT_FROM_EMAIL` - Sender email (e.g., `noreply@starview.app`)
- ✅ Python dependencies installed: `cryptography`, `requests` (in requirements.txt)

---

## Step 1: Create SNS Topics

1. Go to **AWS SNS Console**
2. Ensure you're in the **same region as SES** (Production: `us-east-2` - Ohio)
3. Click **Topics** → **Create topic**

**IMPORTANT**: SNS topics and SES identity MUST be in the same AWS region. Starview production uses `us-east-2` (Ohio).

**Bounce Topic:**
- Type: **Standard**
- Name: `ses-bounces`
- Click **Create topic**

**Complaint Topic:**
- Click **Create topic** again
- Type: **Standard**
- Name: `ses-complaints`
- Click **Create topic**

---

## Step 2: Configure Topic Permissions

Each topic needs permission for SES to publish.

### For `ses-bounces` topic:

1. Click on `ses-bounces` topic
2. Click **Edit**
3. Scroll to **Access policy**
4. Replace with (update `AWS-ACCOUNT-ID` and `REGION`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ses.amazonaws.com"
      },
      "Action": "SNS:Publish",
      "Resource": "arn:aws:sns:REGION:AWS-ACCOUNT-ID:ses-bounces",
      "Condition": {
        "StringEquals": {
          "AWS:SourceAccount": "AWS-ACCOUNT-ID"
        }
      }
    }
  ]
}
```

5. Click **Save changes**

### For `ses-complaints` topic:

Repeat the same steps, replacing `ses-bounces` with `ses-complaints` in the JSON.

---

## Step 3: Subscribe Webhooks

Subscribe your Django webhooks to the SNS topics.

### For `ses-bounces` topic:

1. Click on `ses-bounces` topic
2. Click **Create subscription**
3. Configure:
   - **Protocol**: HTTPS
   - **Endpoint**: `https://www.starview.app/api/webhooks/ses-bounce/`
4. Click **Create subscription**

**CRITICAL:** URL must NOT redirect. AWS SNS does not follow redirects.

**Common issue:** If your site redirects `starview.app` → `www.starview.app` (or vice versa), the subscription will fail.

**Solution:** Use the final destination URL directly (the one that returns 200/400, not 301/302/307).

Test for redirects:
```bash
# Test both variants
curl -I https://starview.app/api/webhooks/ses-bounce/
curl -I https://www.starview.app/api/webhooks/ses-bounce/

# Should return: HTTP/2 200 or HTTP/2 400
# Should NOT return: HTTP/2 301, 302, or 307 (redirects)
```

For Starview production, use: `https://www.starview.app/api/webhooks/ses-bounce/` (with www)

### For `ses-complaints` topic:

1. Click on `ses-complaints` topic
2. Click **Create subscription**
3. Configure:
   - **Protocol**: HTTPS
   - **Endpoint**: `https://www.starview.app/api/webhooks/ses-complaint/`
4. Click **Create subscription**

### Confirm Subscriptions

Your Django webhook automatically confirms subscriptions.

1. Wait 1-2 minutes
2. Refresh subscriptions page
3. Status should change to **"Confirmed"**

If still "Pending":
- Check Render logs for errors
- Click "Request confirmation" button
- Verify no URL redirects (most common issue)

**Note:** Can't delete pending subscriptions (grayed out). AWS auto-deletes after 48 hours.

---

## Step 4: Link SES to SNS

Configure your SES identity to send notifications to SNS topics.

1. Go to **AWS SES Console**
2. Click **Verified identities**
3. Click on your domain (e.g., `starview.app`)
4. Click **Notifications** tab
5. Click **Edit** in "Feedback notifications" section
6. Configure:
   - **Bounce feedback**: Select `ses-bounces` topic
   - **Complaint feedback**: Select `ses-complaints` topic
   - **Include original email headers**: Yes (recommended)
7. Click **Save changes**

---

## Step 5: Test

Send test emails to AWS simulator addresses:

```python
# In production Django shell (Render Shell tab)
from django.core.mail import send_mail

# Test bounce
send_mail('Test', 'Test', 'noreply@starview.app',
          ['bounce@simulator.amazonses.com'])

# Test complaint
send_mail('Test', 'Test', 'noreply@starview.app',
          ['complaint@simulator.amazonses.com'])
```

Wait 30-60 seconds, then check:

**Render Logs:**
- Should see: "Created bounce record for bounce@simulator.amazonses.com"
- Should see: "Email suppressed due to bounces"

**Django Admin:**
- `https://www.starview.app/admin/starview_app/emailbounce/`
- `https://www.starview.app/admin/starview_app/emailcomplaint/`
- Should see test records with red badges

---

## Monitoring

### Automated Weekly Reports (Recommended)

Set up a Render cronjob to automatically clean up bounces and email you a weekly report:

**Cronjob Command:**
```bash
python manage.py cleanup_email_suppressions --email-report your.email@example.com
```

**Schedule:** Every Sunday at 3 AM (cron: `0 3 * * 0`)

**What it does:**
- Recovers soft bounces after 30 days (gives them another chance)
- Cleans up stale bounce records (90+ days inactive)
- Removes transient bounces (7+ days old)
- Emails you a comprehensive report with statistics and health warnings

### Manual Monitoring

**Daily:**
- Check Django Admin → Email Complaints (review immediately)

**Weekly:**
- AWS SES Console → Reputation dashboard (bounce < 5%, complaint < 0.1%)
- Django Admin → Review new bounces

**Monthly:**
- AWS SNS Console → Topic metrics (delivery failures = 0)
- Review suppression list growth

---

## Troubleshooting

**Subscriptions not confirming:**
- Most common: URL redirects (use `curl -I` to test)
- Check Render logs for webhook errors
- Verify webhook URL is accessible via HTTPS
- Click "Request confirmation" button after fixing

**No records in database:**
- Check SNS topic metrics (are messages being published?)
- Check Render logs (is webhook receiving requests?)
- Verify SES identity has SNS topics linked (Step 4)

**High bounce/complaint rates:**
- Review Django admin for patterns
- Check diagnostic codes in bounce records
- Verify email list quality (old addresses?)

---

## Setup Checklist

**AWS Configuration:**
- [x] Created `ses-bounces` and `ses-complaints` topics ✅
- [x] Added SES publish permissions to both topics ✅
- [x] Subscribed webhooks (status = "Confirmed") ✅
- [x] Linked SES identity to SNS topics ✅

**Testing:**
- [x] Tested bounce handling (bounce@simulator.amazonses.com) ✅
- [x] Tested complaint handling (complaint@simulator.amazonses.com) ✅
- [x] Verified records in Django admin ✅
- [x] Verified logs show "Created bounce record" ✅

**Automation:**
- [x] Set up Render cronjob for weekly cleanup + email reports ✅
  - Cronjob: `starview-cleanup-email-suppressions`
  - Schedule: Every Sunday at 3 AM (`0 3 * * 0`)
  - Reports sent to: admin email

**✅ COMPLETE!** Your email monitoring system is live and active in production.

---

## Additional Resources

- Detailed monitoring guide: `02_SYSTEM_FLOW.md`
- Django code: `starview_app/views/views_webhooks.py`
- Models: `starview_app/models/email_events/`
