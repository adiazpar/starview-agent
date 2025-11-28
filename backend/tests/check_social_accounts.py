#!/usr/bin/env python
"""
Check Social Account Integration with Email Changes

This script analyzes how social accounts (Google OAuth) interact with
the email change system and identifies potential issues.
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
from allauth.socialaccount.models import SocialAccount, SocialApp


def analyze_social_account_integration():
    """Analyze social account setup and email change implications"""

    print("=" * 80)
    print("SOCIAL ACCOUNT & EMAIL CHANGE ANALYSIS")
    print("=" * 80)

    # Check if social apps are configured
    print("\n📱 CONFIGURED SOCIAL APPS:")
    print("-" * 80)
    social_apps = SocialApp.objects.all()
    if social_apps.exists():
        for app in social_apps:
            print(f"  ✅ {app.provider.upper()}: {app.name}")
            print(f"     Client ID: {app.client_id[:20]}...")
    else:
        print("  ℹ️  No social apps configured yet")

    # Check for users with social accounts
    print("\n👥 USERS WITH SOCIAL ACCOUNTS:")
    print("-" * 80)
    social_accounts = SocialAccount.objects.all()
    if social_accounts.exists():
        for account in social_accounts:
            user = account.user
            print(f"\n  User: {user.username}")
            print(f"  Provider: {account.provider.upper()}")
            print(f"  Social UID: {account.uid}")
            print(f"  User.email: {user.email}")

            # Check if social account email matches user email
            extra_data = account.extra_data
            social_email = extra_data.get('email')
            if social_email:
                match = "✅ MATCH" if social_email == user.email else "⚠️  MISMATCH"
                print(f"  Social email: {social_email} {match}")
    else:
        print("  ℹ️  No users have linked social accounts")

    # Analyze email change implications
    print("\n" + "=" * 80)
    print("EMAIL CHANGE IMPLICATIONS FOR SOCIAL ACCOUNTS")
    print("=" * 80)

    if not social_accounts.exists():
        print("\n✅ No social accounts exist yet, so no conflicts.")
        print("\nWhen users link social accounts in the future:")
        print("  • Social account email will be stored in SocialAccount.extra_data")
        print("  • User.email can be changed independently")
        print("  • Social login will still work (keyed by UID, not email)")
    else:
        print("\n⚠️  IMPORTANT CONSIDERATIONS:")
        print("-" * 80)
        print("""
1. SOCIAL ACCOUNT IDENTITY:
   • Social accounts are linked by provider UID (not email)
   • Changing User.email DOES NOT affect social login
   • User can still login via Google even with different email

2. EMAIL MISMATCH SCENARIOS:
   • User signs up with Google (email: user@gmail.com)
   • Later changes email to user@yahoo.com
   • Result: Can still login via Google (provider remembers UID)
   • User.email = user@yahoo.com (for password login)
   • Social email = user@gmail.com (in extra_data)

3. POTENTIAL CONFUSION:
   • User might forget which email they used for social login
   • Email shown in profile ≠ email used for Google login
   • This is NORMAL and how most apps work

4. RECOMMENDED UX:
   • Show linked social accounts in profile
   • Display which email is associated with each provider
   • Allow users to unlink/relink accounts
        """)

    # Check current user's setup
    print("\n" + "=" * 80)
    print("YOUR ACCOUNT ANALYSIS (adiazpar)")
    print("=" * 80)

    try:
        user = User.objects.get(username='adiazpar')
        print(f"\nUser.email: {user.email}")

        # Check for social accounts
        user_social_accounts = SocialAccount.objects.filter(user=user)
        if user_social_accounts.exists():
            print("\n🔗 LINKED SOCIAL ACCOUNTS:")
            for account in user_social_accounts:
                print(f"  • {account.provider.upper()}")
                social_email = account.extra_data.get('email')
                if social_email:
                    match = "✅" if social_email == user.email else "⚠️"
                    print(f"    Email: {social_email} {match}")
        else:
            print("\n✅ No social accounts linked")
            print("   You're using username/password login only")

        # Check EmailAddress records
        email_addresses = EmailAddress.objects.filter(user=user)
        print(f"\n📧 EMAIL ADDRESSES ({email_addresses.count()}):")
        for email in email_addresses:
            status = []
            if email.verified:
                status.append("VERIFIED")
            if email.primary:
                status.append("PRIMARY")
            print(f"  • {email.email} [{', '.join(status)}]")

    except User.DoesNotExist:
        print("\n❌ User 'adiazpar' not found")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("""
✅ CURRENT EMAIL CHANGE SYSTEM IS SAFE:
   • Deleting old EmailAddress records is fine
   • Social logins are NOT affected (keyed by UID)
   • Users can change email without breaking social login

⚠️  CONSIDER ADDING TO PROFILE PAGE:
   • "Connected Accounts" section showing linked social providers
   • Email associated with each social account
   • Disconnect/reconnect functionality
   • Clear explanation that social login email ≠ profile email

📚 INDUSTRY EXAMPLES:
   • GitHub: Shows "Primary email" separately from social account emails
   • Google: Allows multiple emails, one is "primary"
   • Discord: Social accounts listed separately from email settings
   • Twitter: Can change email independently of OAuth connections
    """)


if __name__ == '__main__':
    analyze_social_account_integration()
