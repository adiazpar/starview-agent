"""
Test AWS SES Email Integration (Phase 3)

This script tests that AWS SES is properly configured and can send emails.
Run with: djvenv/bin/python .claude/tests/phase3/test_aws_ses_email.py

Prerequisites:
- AWS SES email verified in AWS console
- AWS credentials in .env file
- django-ses installed
"""

import os
import sys
import django

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_aws_ses_configuration():
    """Test that AWS SES is properly configured"""
    print("=" * 70)
    print("AWS SES Configuration Test")
    print("=" * 70)

    # Check configuration
    print("\n1. Checking AWS SES Configuration...")
    print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"   AWS_ACCESS_KEY_ID: {settings.AWS_ACCESS_KEY_ID[:10]}..." if settings.AWS_ACCESS_KEY_ID else "   AWS_ACCESS_KEY_ID: NOT SET")
    print(f"   AWS_SECRET_ACCESS_KEY: {settings.AWS_SECRET_ACCESS_KEY[:10]}..." if settings.AWS_SECRET_ACCESS_KEY else "   AWS_SECRET_ACCESS_KEY: NOT SET")
    print(f"   AWS_SES_REGION_NAME: {settings.AWS_SES_REGION_NAME}")
    print(f"   AWS_SES_REGION_ENDPOINT: {settings.AWS_SES_REGION_ENDPOINT}")
    print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   USE_SES_V2: {settings.USE_SES_V2}")

    # Check if credentials are set
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        print("\n❌ ERROR: AWS credentials not found in .env file!")
        print("   Please add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to your .env file")
        return False

    print("   ✅ Configuration looks good!")

    return True


def test_send_test_email(recipient=None):
    """Send a test email via AWS SES"""
    print("\n2. Sending Test Email...")
    print("=" * 70)

    # Get recipient email from: command line arg > env variable > fail
    if not recipient:
        if len(sys.argv) > 1:
            recipient = sys.argv[1]
        else:
            recipient = os.getenv('TEST_RECIPIENT_EMAIL')

    if not recipient:
        print("   ❌ No recipient provided.")
        print("   Options:")
        print("   1. Set TEST_RECIPIENT_EMAIL in .env file")
        print("   2. Pass email as argument: djvenv/bin/python .claude/tests/phase3/test_aws_ses_email.py <email>")
        return False

    recipient = recipient.strip()
    if not recipient:
        print("   ❌ No recipient provided. Skipping email test.")
        return False

    print(f"\n   From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   To: {recipient}")
    print(f"   Subject: AWS SES Test Email")
    print("\n   Attempting to send email...")

    try:
        # Send test email with improved content to avoid spam filters
        subject = 'Welcome to Event Horizon - Email Verification'
        message = """Hello,

Thank you for joining Event Horizon - your stargazing location discovery platform.

This email confirms that our notification system is working correctly. You'll receive important updates about:
- Password reset requests
- Account security notifications
- Community updates

If you have any questions, please don't hesitate to reach out.

Best regards,
The Event Horizon Team

---
Event Horizon - Discover the Best Stargazing Locations
"""

        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )

        if result == 1:
            print("\n   ✅ SUCCESS! Email sent successfully!")
            print(f"\n   Check the inbox for: {recipient}")
            print("   Note: If in sandbox mode, the recipient must be verified in AWS SES.")
            print("   Note: Check spam folder if you don't see it in inbox.")
            return True
        else:
            print("\n   ❌ FAILED: send_mail returned 0 (no emails sent)")
            return False

    except Exception as e:
        print(f"\n   ❌ ERROR sending email: {str(e)}")
        print("\n   Common issues:")
        print("   - Email address not verified in AWS SES (if in sandbox mode)")
        print("   - Incorrect AWS credentials")
        print("   - Wrong AWS region")
        print("   - AWS SES service issues")
        return False


def main():
    """Run all tests"""
    print("\nEvent Horizon - AWS SES Email Test")
    print("=" * 70)

    # Test configuration
    config_ok = test_aws_ses_configuration()

    if not config_ok:
        print("\n" + "=" * 70)
        print("RESULT: Configuration test FAILED")
        print("=" * 70)
        return

    # Test sending email
    email_ok = test_send_test_email()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Email Sending: {'✅ PASS' if email_ok else '❌ FAIL'}")
    print("=" * 70)

    if config_ok and email_ok:
        print("\n🎉 AWS SES integration is working correctly!")
        print("You can now send password reset emails via AWS SES.")
    else:
        print("\n⚠️  AWS SES integration needs attention.")
        print("Review the errors above and fix any issues.")

    print("\n")


if __name__ == '__main__':
    main()
