# Email Monitoring System Documentation

**AWS SES Bounce and Complaint Tracking for Starview**

---

## 📚 Documentation Index

This directory contains complete documentation for the email monitoring system that tracks bounces and spam complaints from AWS SES.

### **Quick Start**

1. **[AWS Setup Guide](./01_AWS_SETUP_GUIDE.md)** ⭐ START HERE
   - Complete step-by-step AWS Console configuration
   - SNS topic creation and permissions
   - Webhook subscription setup
   - Testing procedures
   - Troubleshooting guide

2. **[System Flow Diagram](./02_SYSTEM_FLOW.md)**
   - Visual flow diagrams
   - File responsibilities
   - Data flow by bounce type
   - Quick reference guide

---

## 🎯 What This System Does

**Problem**: AWS SES requires monitoring of bounces and complaints. High rates lead to account suspension.

**Solution**: Automatically receive notifications when emails bounce or get spam complaints, track them in your database, and manage suppression lists.

### The Flow (In 30 Seconds)

```
Django sends email → AWS SES → Email bounces or spam complaint
                                        ↓
                                    AWS SNS (notifies)
                                        ↓
                                Django webhook receives
                                        ↓
                              Saved to database automatically
                                        ↓
                          Bad addresses added to suppression list
```

---

## 🚀 Current Status

**System Status**: ✅ **PRODUCTION ACTIVE - FULLY DEPLOYED**

**Code Status**:
- ✅ Webhook handlers implemented (`views_webhooks.py`)
- ✅ Database models created (`models/email_events/`)
- ✅ Admin interface configured (`admin.py`)
- ✅ Utilities and helpers ready (`utils/email_utils.py`)
- ✅ Cleanup management command available

**AWS Status**: ✅ **LIVE IN PRODUCTION**
- ✅ **Region**: `us-east-2` (Ohio)
- ✅ SNS topics created: `ses-bounces` and `ses-complaints`
- ✅ Webhooks subscribed and confirmed:
  - `https://www.starview.app/api/webhooks/ses-bounce/`
  - `https://www.starview.app/api/webhooks/ses-complaint/`
- ✅ SES identity verified: `starview.app` domain
- ✅ SES identity linked to SNS topics
- ✅ Real-time monitoring active

**Automation**: ✅ **ACTIVE**
- ✅ Render cronjob: `starview-cleanup-email-suppressions`
- ✅ Schedule: Every Sunday at 3 AM
- ✅ Weekly health reports via email

**Reference**: See `01_AWS_SETUP_GUIDE.md` for detailed configuration documentation.

---

## 📦 Dependencies

**Python Libraries Required:**
- `cryptography==46.0.3` - SNS signature verification using x509 certificates
- `requests==2.32.3` - Download AWS public certificates and confirm SNS subscriptions
- `django` - Core framework (EmailMultiAlternatives, JsonResponse, models, admin)

**AWS Services:**
- **AWS SES** (Simple Email Service) - Sends emails and detects bounces/complaints
- **AWS SNS** (Simple Notification Service) - Publishes notifications to webhooks

All dependencies are in `requirements.txt` and automatically installed during deployment.

---

## 📂 Related Code Files

### Models
- `starview_app/models/email_events/model_email_bounce.py` - Bounce tracking
  - Fields: email, user, bounce_type, bounce_subtype, bounce_count, diagnostic_code, raw_notification, suppressed
  - Method: `should_suppress()` - Returns True if email should be suppressed (hard bounce or 3+ soft bounces)
  - Indexes: email + last_bounce_date, bounce_type + suppressed
- `starview_app/models/email_events/model_email_complaint.py` - Spam complaints
  - Fields: email, user, complaint_type, user_agent, feedback_id, raw_notification, suppressed, reviewed
  - All complaints immediately suppressed (critical for sender reputation)
  - Indexes: email + complaint_date, reviewed + suppressed
- `starview_app/models/email_events/model_email_suppressionlist.py` - Suppression list
  - Fields: email (unique), user, reason, bounce, complaint, is_active, added_date, notes
  - Class methods: `is_suppressed(email)`, `add_to_suppression(email, reason, ...)`
  - Indexes: email + is_active, reason + added_date

### Views
- `starview_app/views/views_webhooks.py` - SNS webhook handlers

### Admin
- `starview_app/admin.py` (lines 220-823) - Admin interfaces

### Utilities
- `starview_app/utils/email_utils.py` - Helper functions

### Management Commands
- `starview_app/management/commands/cleanup_email_suppressions.py` - Maintenance

---

## 🧪 Testing

AWS provides test email addresses:

```python
# In Django shell
from django.core.mail import send_mail

# Test bounce
send_mail('Test', 'Test', 'noreply@starview.app',
          ['bounce@simulator.amazonses.com'])

# Test complaint
send_mail('Test', 'Test', 'noreply@starview.app',
          ['complaint@simulator.amazonses.com'])
```

Wait 30 seconds, then check:
```python
from starview_app.models import EmailBounce, EmailComplaint
print(f"Bounces: {EmailBounce.objects.count()}")
print(f"Complaints: {EmailComplaint.objects.count()}")
```

---

## 📊 Monitoring

### Django Admin
- `/admin/starview_app/emailbounce/` - View bounces
- `/admin/starview_app/emailcomplaint/` - View complaints (CRITICAL!)
- `/admin/starview_app/emailsuppressionlist/` - Manage suppressions

### Management Commands
```bash
# Run cleanup and generate report
python manage.py cleanup_email_suppressions --report

# Get statistics
python manage.py shell -c "
from starview_app.utils.email_utils import get_email_statistics
print(get_email_statistics())
"
```

### AWS Console
- **Bounce Rate**: Must be < 5%
- **Complaint Rate**: Must be < 0.1%
- Check: SES Console → Reputation dashboard

---

## 🛠️ Maintenance

### Weekly
- Review spam complaints in admin (CRITICAL)
- Run cleanup command: `python manage.py cleanup_email_suppressions`

### Monthly
- Review bounce patterns
- Check AWS SES reputation dashboard
- Verify bounce/complaint rates within limits

### Automated (via cleanup command)
- Soft bounces auto-recover after 30 days
- Transient bounces deleted after 7 days
- Stale records cleaned up after 90 days

---

## ⚠️ Important Notes

### Transactional vs Marketing Emails

**Transactional emails** (password resets, email verification):
- ✅ **ALWAYS SEND** even if email is suppressed
- Critical for user access to the app
- Never blocked by suppression list

**Marketing emails** (newsletters, announcements):
- ❌ **BLOCKED** if email is on suppression list
- Should check suppression before sending
- Use `is_email_suppressed()` utility function

### Bounce Types

1. **Hard Bounce (Permanent)**
   - Invalid email, domain doesn't exist
   - Immediate suppression
   - Never recovered

2. **Soft Bounce (Temporary)**
   - Mailbox full, server down
   - Suppressed after 3 consecutive bounces
   - Auto-recovery after 30 days of no bounces

3. **Transient (Connection Issues)**
   - Throttling, timeouts
   - Never suppressed
   - Auto-deleted after 7 days

4. **Spam Complaint**
   - User marked email as spam
   - Immediate suppression
   - Manual review required

---

## 🆘 Troubleshooting

See `01_AWS_SETUP_GUIDE.md` → "Troubleshooting" section for:
- Subscription confirmation issues
- Signature verification failures
- No notifications received
- Webhook errors
- Development/localhost testing

---

## 📖 Additional Resources

- **AWS SES Docs**: https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications.html
- **AWS SNS Docs**: https://docs.aws.amazon.com/sns/latest/dg/sns-http-https-endpoint-as-subscriber.html
- **CAN-SPAM Act**: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business

---

## 🔐 Security

### Webhook Security
- ✅ SNS signature verification (cryptographic using AWS public certificates)
- ✅ Certificate URL validation (must be `https://sns.*`)
- ✅ CSRF exempt (external AWS service - @csrf_exempt decorator)
- ✅ Message type validation (Notification vs SubscriptionConfirmation)
- ✅ Automatic subscription confirmation (HTTP GET to SubscribeURL)
- ✅ Audit logging for all events (logger.info/warning/critical)
- ✅ Raw notification storage for investigation (raw_notification JSONField)
- ✅ Signature verification uses cryptography library with PKCS1v15 padding and SHA1 hashing

### AWS Compliance
- ✅ Monitors bounce rate (< 5% required)
- ✅ Monitors complaint rate (< 0.1% required)
- ✅ Maintains suppression list
- ✅ Provides admin visibility and reporting

---

**Last Updated**: 2025-11-27
**Status**: ✅ Live in Production - AWS SNS webhooks active and monitoring
**Version**: 1.1 (Added dependencies, enhanced security details, production region specification)
