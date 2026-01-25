# Badge Implementation Guide

Technical implementation steps for creating a new badge.

## 1. Place Icon File

Copy user-provided icon to:
```
starview_frontend/public/badges/{slug}.png
```

Requirements:
- 256x256px PNG with transparency
- Space-themed, colorful design
- Filename must match badge slug

## 2. Create Data Migration

Generate migration in `starview_app/migrations/`:

```python
from django.db import migrations

def create_badge(apps, schema_editor):
    Badge = apps.get_model('starview_app', 'Badge')
    Badge.objects.create(
        name='Badge Name',
        slug='badge-slug',
        description='Badge description',
        category='CATEGORY',
        criteria_type='CRITERIA_TYPE',
        criteria_value=10,
        tier=1,
        icon_path='/badges/badge-slug.png',
    )

def remove_badge(apps, schema_editor):
    Badge = apps.get_model('starview_app', 'Badge')
    Badge.objects.filter(slug='badge-slug').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('starview_app', 'XXXX_previous_migration'),
    ]
    operations = [
        migrations.RunPython(create_badge, remove_badge),
    ]
```

Run migration:
```bash
djvenv/bin/python manage.py migrate
```

## 3. Update BadgeService (If New Criteria Type)

If using a NEW criteria_type not in BadgeService, add check method to `starview_app/services/badge_service.py`:

```python
@staticmethod
def check_new_category_badges(user):
    """Check badges for new criteria type."""
    count = SomeModel.objects.filter(user=user).count()

    badges = Badge.objects.filter(
        category='NEW_CATEGORY',
        criteria_type='NEW_CRITERIA_TYPE'
    ).order_by('criteria_value')

    for badge in badges:
        if count >= badge.criteria_value:
            BadgeService.award_badge(user, badge)
        else:
            break
```

## 4. Add Signal Handler (If New Trigger)

If badge needs a NEW trigger event, add to `starview_app/utils/signals.py`:

```python
@receiver(post_save, sender=NewModel)
def check_badges_on_new_event(sender, instance, created, **kwargs):
    if created:
        BadgeService.check_new_category_badges(instance.user)
```

## 5. Test the Badge

```bash
djvenv/bin/python manage.py shell
```

```python
from starview_app.models import Badge
from starview_app.services.badge_service import BadgeService
from django.contrib.auth.models import User

# Verify badge exists
badge = Badge.objects.get(slug='badge-slug')
print(f"Badge: {badge.name}, Category: {badge.category}")

# Test awarding (with test user)
user = User.objects.get(username='testuser')
BadgeService.award_badge(user, badge)

# Verify it was awarded
from starview_app.models import UserBadge
ub = UserBadge.objects.filter(user=user, badge=badge).first()
print(f"Awarded: {ub.awarded_at if ub else 'NOT AWARDED'}")
```

## 6. Clear Badge Cache

Restart the Django server to clear the badge cache:

```bash
# If using runserver
# Ctrl+C and restart

# If using Render/production
# Redeploy or restart the service
```

## 7. Update Documentation

Run `/update-docs` to sync documentation with changes.
