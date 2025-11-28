---
name: starview-badge-creator
description: Create new badges for the Starview badge system. Use when adding badges, creating achievement badges, or implementing new badge criteria. Guides through database migration, icon placement, signal handlers, and documentation updates.
---

# Badge Creator for Starview

Create new badges following the established badge system patterns.

## Prerequisites

Before starting, ensure you have:
- Badge name, slug, and description
- Badge category (EXPLORATION, CONTRIBUTION, QUALITY, REVIEW, COMMUNITY, SPECIAL, TENURE)
- Criteria type and value
- Icon file (.png, 256x256px) from user

## Reference Documentation

Read these before creating complex badges:
- `.claude/backend/docs/badge_system/BADGE_SYSTEM.md` - Full badge design and categories
- `.claude/backend/docs/badge_system/IMPLEMENTATION_GUIDE.md` - Technical implementation details

## Badge Creation Steps

### 1. Gather Badge Details

Collect from user:

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Display name | "Night Owl" |
| `slug` | URL-safe identifier | "night-owl" |
| `description` | User-facing description | "Visit 10 locations at night" |
| `category` | One of: EXPLORATION, CONTRIBUTION, QUALITY, REVIEW, COMMUNITY, SPECIAL, TENURE | "SPECIAL" |
| `criteria_type` | What triggers the badge | "LOCATION_VISITS" |
| `criteria_value` | Threshold to earn | 10 |
| `tier` | 1-5 progression level | 2 |

### 2. Create Data Migration

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

### 3. Place Icon File

Copy user-provided icon to:
```
starview_frontend/public/badges/{slug}.png
```

Requirements:
- 256x256px PNG with transparency
- Space-themed, colorful design
- Filename must match badge slug

### 4. Update BadgeService (If New Criteria Type)

If using a NEW criteria_type not in BadgeService, add check method to `starview_app/services/badge_service.py`:

```python
@staticmethod
def check_new_category_badges(user):
    """Check badges for new criteria type"""
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

### 5. Add Signal Handler (If New Trigger)

If badge needs a NEW trigger event, add to `starview_app/utils/signals.py`:

```python
@receiver(post_save, sender=NewModel)
def check_badges_on_new_event(sender, instance, created, **kwargs):
    if created:
        BadgeService.check_new_category_badges(instance.user)
```

### 6. Test the Badge

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
```

### 7. Update Documentation

Run `/update-docs` to sync documentation with changes.

## Existing Criteria Types

Use these existing types when possible:

| Criteria Type | Trigger Signal | Check Method |
|---------------|----------------|--------------|
| LOCATION_VISITS | LocationVisit post_save | check_exploration_badges |
| LOCATIONS_ADDED | Location post_save | check_contribution_badges |
| LOCATION_RATING | Review post_save | check_quality_badges |
| REVIEWS_WRITTEN | Review post_save | check_review_badges |
| UPVOTES_RECEIVED | Vote post_save | check_review_badges |
| HELPFUL_RATIO | Vote post_save | check_review_badges |
| COMMENTS_WRITTEN | ReviewComment post_save | check_community_badges |
| FOLLOWER_COUNT | Follow post_save | check_community_badges |
| PHOTOS_UPLOADED | ReviewPhoto post_save | check_special_badges |
| PIONEER | email_confirmed signal | check_pioneer_badge |

## Quick Reference: Existing Badges

- **Exploration (6):** First Light → Cosmic Voyager (1-100 visits)
- **Contribution (4):** Scout → Location Legend (1-25 locations)
- **Quality (4):** Quality Contributor → Elite Curator (3-24 high-rated locations)
- **Review (5):** Reviewer → Review Master (5-100 reviews with ratio)
- **Community (5):** Conversationalist → Ambassador (10-200 followers/comments)
- **Special (1):** Photographer (25 photos)
- **Tenure (1):** Pioneer (first 100 users)
