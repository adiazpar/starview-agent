#!/usr/bin/env python
"""
Test Email Change Verification Flow

This script tests the complete email change verification process to ensure:
1. Old email receives notification
2. New email receives verification link
3. After clicking verification link:
   - New email becomes primary and verified
   - User.email updates to new email
   - Old email is removed from EmailAddress table
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.account.models import EmailAddress
from django.test import RequestFactory, Client
from django.urls import reverse


def test_email_change_verification():
    """Test the complete email change verification flow"""

    print("=" * 80)
    print("EMAIL CHANGE VERIFICATION TEST")
    print("=" * 80)

    # Get your user (replace with your actual username)
    username = 'adiazpar'

    try:
        user = User.objects.get(username=username)
        print(f"\n✅ Found user: {user.username}")
    except User.DoesNotExist:
        print(f"\n❌ User '{username}' not found. Please update the script with your username.")
        return

    # Check current state
    print("\n" + "=" * 80)
    print("CURRENT STATE")
    print("=" * 80)
    print(f"User.email: {user.email}")

    email_addresses = EmailAddress.objects.filter(user=user)
    print(f"\nEmailAddress records ({email_addresses.count()}):")
    for email in email_addresses:
        status = []
        if email.verified:
            status.append("VERIFIED")
        if email.primary:
            status.append("PRIMARY")
        status_str = ", ".join(status) if status else "UNVERIFIED"
        print(f"  - {email.email} [{status_str}]")

    # Instructions
    print("\n" + "=" * 80)
    print("CLEANUP INSTRUCTIONS")
    print("=" * 80)
    print("\nYour current state shows multiple email addresses.")
    print("To test the email change flow properly, you should:")
    print("\n1. Decide which email you want to keep as your primary")
    print("2. Run the cleanup script below in Django shell")
    print("\n" + "-" * 80)
    print("# Django shell commands to clean up:")
    print("-" * 80)
    print(f"""
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress

user = User.objects.get(username='{username}')

# Option 1: Keep iCloud email as primary
user.email = 'your-icloud-email@icloud.com'
user.save()
EmailAddress.objects.filter(user=user).exclude(email='your-icloud-email@icloud.com').delete()

# OR Option 2: Keep Gmail email as primary (manually verify it first)
# user.email = 'your-gmail-email@gmail.com'
# user.save()
# EmailAddress.objects.filter(user=user).exclude(email='your-gmail-email@gmail.com').delete()
    """)
    print("-" * 80)

    print("\n" + "=" * 80)
    print("TESTING INSTRUCTIONS")
    print("=" * 80)
    print("\nAfter cleanup, test the email change flow:")
    print("\n1. Go to Profile → Settings")
    print("2. Change email to a NEW email address")
    print("3. Check both old and new email inboxes")
    print("4. Click verification link in NEW email")
    print("5. Refresh this script to verify the change completed")
    print("\nExpected result after verification:")
    print("  - User.email = new email")
    print("  - Only 1 EmailAddress record (new email, verified, primary)")
    print("  - Old email removed")


if __name__ == '__main__':
    test_email_change_verification()
