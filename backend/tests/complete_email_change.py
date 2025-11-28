#!/usr/bin/env python
"""
Complete Email Change Manually

This script completes the email change process that was started but not finished
due to the verification link being clicked before the updated code was deployed.
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


def complete_email_change_to_gmail():
    """Complete the email change from iCloud to Gmail"""

    print("=" * 80)
    print("COMPLETING EMAIL CHANGE: iCloud → Gmail")
    print("=" * 80)

    username = 'adiazpar'
    new_email = 'alexdiaz0923@gmail.com'

    try:
        user = User.objects.get(username=username)
        print(f"\n✅ Found user: {user.username}")
    except User.DoesNotExist:
        print(f"\n❌ User '{username}' not found.")
        return

    # Get the Gmail EmailAddress object
    try:
        gmail_email = EmailAddress.objects.get(user=user, email=new_email)
        print(f"✅ Found Gmail EmailAddress: {gmail_email.email}")
        print(f"   - Verified: {gmail_email.verified}")
        print(f"   - Primary: {gmail_email.primary}")
    except EmailAddress.DoesNotExist:
        print(f"❌ Gmail email address not found in EmailAddress table")
        return

    if not gmail_email.verified:
        print("\n❌ Gmail email is not verified yet. Cannot complete email change.")
        return

    print("\n" + "=" * 80)
    print("BEFORE STATE")
    print("=" * 80)
    print(f"User.email: {user.email}")
    all_emails = EmailAddress.objects.filter(user=user)
    for email in all_emails:
        status = []
        if email.verified:
            status.append("VERIFIED")
        if email.primary:
            status.append("PRIMARY")
        print(f"  - {email.email} [{', '.join(status) if status else 'UNVERIFIED'}]")

    # Perform the email change
    print("\n" + "=" * 80)
    print("PERFORMING EMAIL CHANGE")
    print("=" * 80)

    # Step 1: Set Gmail as primary
    print("1. Setting Gmail as primary...")
    gmail_email.set_as_primary()
    print("   ✅ Gmail is now primary")

    # Step 2: Update User.email
    print("2. Updating User.email...")
    user.email = new_email
    user.save()
    print(f"   ✅ User.email updated to {new_email}")

    # Step 3: Remove old emails
    print("3. Removing old email addresses...")
    deleted_count = EmailAddress.objects.filter(user=user).exclude(id=gmail_email.id).delete()[0]
    print(f"   ✅ Removed {deleted_count} old email address(es)")

    # Verify final state
    print("\n" + "=" * 80)
    print("AFTER STATE")
    print("=" * 80)
    user.refresh_from_db()
    print(f"User.email: {user.email}")
    all_emails = EmailAddress.objects.filter(user=user)
    print(f"\nEmailAddress records ({all_emails.count()}):")
    for email in all_emails:
        status = []
        if email.verified:
            status.append("VERIFIED")
        if email.primary:
            status.append("PRIMARY")
        print(f"  - {email.email} [{', '.join(status) if status else 'UNVERIFIED'}]")

    print("\n" + "=" * 80)
    print("✅ EMAIL CHANGE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\nYour email has been changed from iCloud to Gmail.")
    print("The old iCloud email has been removed.")
    print("\nYou can now log in with your Gmail address.")


if __name__ == '__main__':
    complete_email_change_to_gmail()
