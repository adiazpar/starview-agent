# Badge System Implementation Guide

Complete guide for using, testing, and managing the Starview badge system.

**Status:** ✅ Production Ready (2025-11-12)

---

## Quick Start

### Viewing Badges in Django Admin

**Location:** Django Admin → STARVIEW_APP → Badges / User badges / Location visits

**What you'll see:**
- **Badges:** All 26 badges with categories, criteria, and award counts
- **User badges:** Which users have which badges and when they earned them
- **Location visits:** All user check-ins with timestamps

**Useful Admin Features:**
- Color-coded categories (Exploration, Contribution, Quality, Review, Community, Special, Tenure)
- Filter by category, tier, rarity
- Search by username, badge name
- User registration rank column (for Pioneer badge)

---

## Management Commands

### Award Pioneer Badges

The Pioneer badge is awarded to the first 100 verified users (historical snapshot).

**Preview who will get badges:**
```bash
djvenv/bin/python manage.py award_pioneer_badges --dry-run
```

**Award badges:**
```bash
djvenv/bin/python manage.py award_pioneer_badges
```

**When to use:**
- One-time after deploying badge system to production
- After first 100 users verify their emails

**How it works:**
- Queries users by `date_joined` timestamp (NOT user ID)
- Awards badge to first 100 users by registration order
- Uses `get_or_create()` to prevent duplicates
- Email verification must be complete

### Audit Badges

Verify all users' badges meet current criteria and remove invalid badges.

**Preview mode (safe, no changes):**
```bash
djvenv/bin/python manage.py audit_badges
```

**Fix mode (revokes invalid badges):**
```bash
djvenv/bin/python manage.py audit_badges --fix
```

**Audit specific user:**
```bash
djvenv/bin/python manage.py audit_badges --user username [--fix]
```

**When to use:**
- After bulk deletions (locations, reviews, etc.)
- Periodic maintenance (monthly/quarterly)
- Debugging individual user badge issues
- One-time cleanup after deploying badge revocation

**What it checks:**
- Exploration badges (location visit count)
- Contribution badges (locations added)
- Quality badges (4+ star average locations)
- Review badges (count, upvotes, helpful ratio)
- Community badges (followers, comments on others' reviews)
- Photographer badge (review photos uploaded)
- Pioneer badge is NEVER revoked (historical achievement)

**Example output:**
```
======================================================================
BADGE AUDIT REPORT
======================================================================

📋 PREVIEW MODE: No changes will be made

Auditing all users (10 total)

👤 User: john_doe
   Invalid badges found: 2
   ⚠ WOULD REVOKE: Trailblazer (CONTRIBUTION)
      Reason: Has 3 locations, needs 5
   ⚠ WOULD REVOKE: Sky Seeker (EXPLORATION)
      Reason: Has 4 visits, needs 5

======================================================================
AUDIT SUMMARY
======================================================================
Users checked: 10
Users with invalid badges: 1
Total invalid badges: 2

⚠️  Run with --fix to revoke 2 invalid badge(s)
```

---

## Pioneer Badge Logic

### How It Works

**Criteria:** First 100 users by `date_joined` timestamp

**Field Used:** `User.date_joined` (Django's built-in timestamp)

**Calculation:**
```python
registration_rank = User.objects.filter(
    date_joined__lte=user.date_joined
).count()

qualifies = registration_rank <= 100
```

**Why NOT user ID?**
- User IDs have gaps due to deletions
- `date_joined` always reflects true registration order
- Historical snapshot (permanent)

### Registration Rank

**View in Django Admin:**
1. Go to Django Admin → Users
2. Click "Date joined" column to sort
3. First 100 users qualify for Pioneer badge

**Check in Django shell:**
```python
from django.contrib.auth.models import User

# Get user's registration rank
user = User.objects.get(username='adiazpar')
rank = User.objects.filter(date_joined__lte=user.date_joined).count()
print(f"{user.username} is user #{rank}")

# Check if qualifies for Pioneer
qualifies = rank <= 100
print(f"Qualifies for Pioneer: {qualifies}")
```

### Historical Snapshot

**Q: What happens when users delete accounts?**

**A:** Badge slots are "wasted" - no backfill.

**Example:**
```
Day 1: Users #1-100 register → All get Pioneer badge
Day 2: User #50 deletes account
Day 3: User #101 registers

Question: Does user #101 get Pioneer badge now that only 99 users exist?
Answer: NO - Badge slots are permanent
```

**Why?**
- Prevents gaming (can't delete/re-register)
- Historical accuracy ("first 100 to register" is a fixed point in time)
- Simplicity (no need to recalculate when users delete)
- Fairness (early adopters earned their badges)

### Email Verification Requirement

Pioneer badge is awarded AFTER email verification:

**Signal trigger:**
```python
from allauth.account.signals import email_confirmed

@receiver(email_confirmed)
def award_pioneer_badge_on_verification(sender, email_address, **kwargs):
    user = email_address.user
    BadgeService.check_pioneer_badge(user)
```

**Why?**
- Prevents spam accounts from claiming Pioneer badges
- Ensures only real users get the badge
- Leverages existing security (rate limiting, email verification)

---

## Testing

### Test Coverage

**Phase Badge Tests** (`.claude/backend/tests/phase_badge/`):
- `test_badge_comprehensive.py` - End-to-end system test (8/8 passing)

**Phase 7 Critical Fixes** (`.claude/backend/tests/phase7/`):
- `test_1_self_review_prevention.py` - Users cannot review own locations
- `test_2_conversationalist_badge.py` - Comments on others' reviews only
- `test_3_quality_badges.py` - 4+ star average validation
- `test_4_review_badges_upvote_ratio.py` - Upvote ratio calculation

**Performance Tests:**
- `badge_performance_test.py` - Query execution time benchmarks
- `n1_query_test.py` - N+1 query elimination verification
- `contenttype_cache_test.py` - ContentType caching metrics
- `medium_issue5_before/after.py` - Vote query optimization
- `medium_issue7_before/after.py` - Badge progress caching

**Integration Tests:**
- `test_badge_progress_integration.py` - Badge progress API (5/5 passing)
- `test_badge_progress_caching.py` - Redis cache behavior (9/9 passing)
- `test_review_badges_functional.py` - Review badge logic (9/9 passing)
- `contenttype_functional_test.py` - Signal handler edge cases (4/4 passing)

**Total:** 60+ tests, all passing ✅

### Running Tests

**Single test file:**
```bash
djvenv/bin/python .claude/backend/tests/phase_badge/test_badge_comprehensive.py
```

**All badge tests:**
```bash
djvenv/bin/python -m pytest .claude/backend/tests/phase_badge/
djvenv/bin/python -m pytest .claude/backend/tests/phase7/
```

**Performance tests:**
```bash
djvenv/bin/python .claude/backend/tests/badge_performance_test.py
djvenv/bin/python .claude/backend/tests/n1_query_test.py
```

---

## Badge Progress Calculation

### API Endpoint

**GET** `/api/badges/user/<username>/`

**Response:**
```json
{
  "earned": [
    {
      "badge_id": 1,
      "name": "First Light",
      "slug": "first-light",
      "description": "Visit your first location",
      "category": "EXPLORATION",
      "tier": 1,
      "icon_path": "/badges/first-light.png",
      "earned_at": "2025-11-01T10:00:00Z"
    }
  ],
  "in_progress": [
    {
      "badge_id": 2,
      "name": "Explorer",
      "slug": "explorer",
      "description": "Visit 5 locations",
      "current_progress": 3,
      "criteria_value": 5,
      "percentage": 60
    }
  ],
  "locked": [
    {
      "badge_id": 3,
      "name": "Pathfinder",
      "description": "Visit 10 locations"
    }
  ],
  "pinned_badge_ids": [1]
}
```

### Checking in Code

```python
from starview_app.services.badge_service import BadgeService
from django.contrib.auth.models import User

user = User.objects.get(username='stony')

# Get user's badge progress
progress = BadgeService.get_user_badge_progress(user)

print(f"Earned: {len(progress['earned'])} badges")
print(f"In Progress: {len(progress['in_progress'])} badges")
print(f"Locked: {len(progress['locked'])} badges")

# Check specific badge category
for badge_data in progress['in_progress']:
    badge = badge_data['badge']
    if badge.category == 'EXPLORATION':
        current = badge_data['current_progress']
        needed = badge_data['criteria_value']
        print(f"{badge.name}: {current}/{needed} ({badge_data['percentage']}%)")
```

---

## Pinning Badges

### Profile Display

Users can pin up to 3 badges to display on their profile header.

**Storage:** `UserProfile.pinned_badge_ids` (ArrayField)

**API Endpoint:**
```
PATCH /api/users/me/profile/pin-badges/

Request:
{
  "pinned_badge_ids": [1, 5, 8]
}

Response:
{
  "detail": "Pinned badges updated",
  "pinned_badge_ids": [1, 5, 8]
}
```

**Validation:**
- Maximum 3 badges
- Can only pin badges you've earned
- Can only modify your own pins

### Checking Pinned Badges

```python
from starview_app.models import UserProfile

user_profile = UserProfile.objects.get(user=user)
print(f"Pinned badge IDs: {user_profile.pinned_badge_ids}")

# Get full badge objects
from starview_app.models import Badge
pinned_badges = Badge.objects.filter(id__in=user_profile.pinned_badge_ids)
for badge in pinned_badges:
    print(f"- {badge.name} ({badge.category})")
```

---

## Common Tasks

### Check User's Badge Status

```python
from django.contrib.auth.models import User
from starview_app.models import UserBadge, Badge

user = User.objects.get(username='stony')

# Get all earned badges
earned_badges = UserBadge.objects.filter(user=user).select_related('badge')
print(f"{user.username} has {earned_badges.count()} badges:")

for user_badge in earned_badges:
    print(f"- {user_badge.badge.name} (earned {user_badge.earned_at})")
```

### Manually Award Badge (Testing Only)

```python
from starview_app.services.badge_service import BadgeService
from starview_app.models import Badge
from django.contrib.auth.models import User

user = User.objects.get(username='testuser')
badge = Badge.objects.get(slug='first-light')

# Award badge
created = BadgeService.award_badge(user, badge)
if created:
    print(f"Awarded {badge.name} to {user.username}")
else:
    print(f"{user.username} already has {badge.name}")
```

### Check Who Has Specific Badge

```python
from starview_app.models import UserBadge, Badge

pioneer = Badge.objects.get(slug='pioneer')
pioneer_users = UserBadge.objects.filter(badge=pioneer).select_related('user')

print(f"Pioneer badge awarded to {pioneer_users.count()} users:")
for ub in pioneer_users.order_by('user__date_joined'):
    rank = User.objects.filter(date_joined__lte=ub.user.date_joined).count()
    print(f"#{rank:3d} - {ub.user.username:20s} - earned {ub.earned_at}")
```

### Verify Badge Criteria

```python
from django.contrib.auth.models import User
from starview_app.models import LocationVisit, Location, Review

user = User.objects.get(username='stony')

# Check exploration progress
visit_count = LocationVisit.objects.filter(user=user).count()
print(f"Location visits: {visit_count}")

# Check contribution progress
location_count = Location.objects.filter(added_by=user).count()
print(f"Locations added: {location_count}")

# Check review progress
review_count = Review.objects.filter(user=user).count()
print(f"Reviews written: {review_count}")

# Check quality progress
quality_count = Location.objects.filter(
    added_by=user,
    average_rating__gte=4.0
).count()
print(f"Locations with 4+ stars: {quality_count}")
```

---

## Badge Revocation

### Automatic Revocation

Badges are automatically revoked when users no longer meet criteria:

**Signal handlers:**
```python
# When location visit deleted
@receiver(post_delete, sender=LocationVisit)
def revoke_badges_on_visit_delete(sender, instance, **kwargs):
    BadgeService.revoke_exploration_badges_if_needed(instance.user)

# When location deleted
@receiver(post_delete, sender=Location)
def revoke_badges_on_location_delete(sender, instance, **kwargs):
    BadgeService.revoke_contribution_badges_if_needed(instance.added_by)

# When review deleted
@receiver(post_delete, sender=Review)
def revoke_badges_on_review_delete(sender, instance, **kwargs):
    BadgeService.revoke_review_badges_if_needed(instance.user)

# When vote deleted
@receiver(post_delete, sender=Vote)
def revoke_badges_on_vote_delete(sender, instance, **kwargs):
    # Revokes review badges if upvote ratio drops

# When follow deleted
@receiver(post_delete, sender=Follow)
def revoke_badges_on_follow_delete(sender, instance, **kwargs):
    BadgeService.revoke_community_badges_if_needed(instance.following)
```

### Manual Revocation

```python
from starview_app.models import UserBadge

# Revoke specific badge from user
UserBadge.objects.filter(user=user, badge=badge).delete()

# Revoke all badges from user (don't do this in production!)
UserBadge.objects.filter(user=user).delete()
```

### Preventing Revocation

**Pioneer badge is NEVER revoked:**
```python
def revoke_tenure_badges_if_needed(user):
    # Pioneer badge is historical - never revoke
    # (No revocation logic exists for Pioneer)
    pass
```

---

## Troubleshooting

### Badge Not Awarded

**1. Check user meets criteria:**
```python
from starview_app.services.badge_service import BadgeService

user = User.objects.get(username='username')
BadgeService.check_exploration_badges(user)  # Manually trigger check
```

**2. Check badge exists:**
```python
from starview_app.models import Badge

badge = Badge.objects.filter(slug='first-light').first()
if not badge:
    print("Badge doesn't exist - run migrations")
```

**3. Check signal fired:**
```python
# Enable logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Create LocationVisit and watch logs
LocationVisit.objects.create(user=user, location=location)
```

### Badge Progress Incorrect

**1. Verify stats:**
```python
from starview_app.models import LocationVisit, Location, Review

user = User.objects.get(username='username')

print(f"Visits: {LocationVisit.objects.filter(user=user).count()}")
print(f"Locations: {Location.objects.filter(added_by=user).count()}")
print(f"Reviews: {Review.objects.filter(user=user).count()}")
```

**2. Clear badge progress cache:**
```python
from django.core.cache import cache

cache.delete(f'badge_progress:{user.id}')
```

**3. Recalculate progress:**
```python
from starview_app.services.badge_service import BadgeService

progress = BadgeService.get_user_badge_progress(user)
print(progress)
```

### Pioneer Badge Not Awarded

**1. Check registration rank:**
```python
from django.contrib.auth.models import User

user = User.objects.get(username='username')
rank = User.objects.filter(date_joined__lte=user.date_joined).count()

print(f"Registration rank: {rank}")
print(f"Qualifies: {rank <= 100}")
```

**2. Check email verification:**
```python
print(f"Email verified: {user.emailaddress_set.filter(verified=True).exists()}")
```

**3. Manually award if needed:**
```python
from starview_app.services.badge_service import BadgeService

BadgeService.check_pioneer_badge(user)
```

---

## Best Practices

### For Developers

1. **Never manually create UserBadge records** - Always use `BadgeService.award_badge()`
2. **Test badge logic thoroughly** - Use automated tests, not production data
3. **Monitor badge awarding rates** - Unusual spikes indicate issues
4. **Cache badge progress** - Already implemented via Redis
5. **Use audit command for cleanup** - Don't manually delete UserBadge records

### For Admins

1. **Run audit command after bulk deletions** - Ensures badge integrity
2. **Monitor registration rank in admin** - Verify Pioneer badge eligibility
3. **Check badge statistics regularly** - Identify popular badges
4. **Review flagged accounts** - Anomaly detection logs suspicious activity
5. **Don't manually revoke Pioneer badges** - Historical achievement

### For Production

1. **Enable Redis caching** - 90% query reduction
2. **Monitor cache hit rates** - Alert if < 80%
3. **Track badge awarding frequency** - Detect anomalies
4. **Review audit logs periodically** - Security monitoring
5. **Test signal handlers after deployments** - Verify automatic awarding

---

## Reference

### Badge Categories

| Category | Count | Examples |
|----------|-------|----------|
| **Exploration** | 6 | First Light (1 visit) → Cosmic Voyager (100 visits) |
| **Contribution** | 4 | Scout (1 location) → Location Legend (25 locations) |
| **Quality** | 4 | Quality Contributor (3 well-rated) → Elite Curator (24) |
| **Review** | 5 | Reviewer (5 reviews) → Review Master (100 + 85% ratio) |
| **Community** | 5 | Conversationalist (10 comments) → Ambassador (200 followers) |
| **Special** | 1 | Photographer (25 photos) |
| **Tenure** | 1 | Pioneer (first 100 verified users) |

### Complete Badge List

#### Exploration Badges (6)
1. **First Light** - Visit 1 location
2. **Explorer** - Visit 5 locations
3. **Pathfinder** - Visit 10 locations
4. **Stargazer** - Visit 25 locations
5. **Celestial Navigator** - Visit 50 locations
6. **Cosmic Voyager** - Visit 100 locations

#### Contribution Badges (4)
1. **Scout** - Add 1 location
2. **Discoverer** - Add 5 locations
3. **Trailblazer** - Add 10 locations
4. **Location Legend** - Add 25 locations

#### Quality Badges (4)
1. **Quality Contributor** - 3+ locations with 4+ star average
2. **Trusted Source** - 6+ locations with 4+ star average
3. **Stellar Curator** - 12+ locations with 4+ star average
4. **Elite Curator** - 24+ locations with 4+ star average

#### Review Badges (5)
1. **Reviewer** - Write 5 reviews
2. **Helpful Voice** - Receive 10 upvotes
3. **Expert Reviewer** - 25+ reviews with 75%+ helpful ratio
4. **Trusted Critic** - 50+ reviews with 80%+ helpful ratio
5. **Review Master** - 100+ reviews with 85%+ helpful ratio

#### Community Badges (5)
1. **Conversationalist** - Comment on 10 reviews (others' reviews only)
2. **Connector** - Have 10 followers
3. **Influencer** - Have 50 followers
4. **Community Leader** - Have 100 followers
5. **Ambassador** - Have 200 followers

#### Special Badges (1)
1. **Photographer** - Upload 25 review photos

#### Tenure Badges (1)
1. **Pioneer** - First 100 verified users (by registration date)

### Key Files

| Component | Location |
|-----------|----------|
| **Models** | `starview_app/models/model_badge.py`, `model_user_badge.py`, `model_location_visit.py` |
| **Service** | `starview_app/services/badge_service.py` |
| **Signals** | `starview_app/utils/signals.py` (lines 286-650) |
| **Admin** | `starview_app/admin.py` (BadgeAdmin, UserBadgeAdmin, etc.) |
| **API Views** | `starview_app/views/views_badge.py` |
| **Tests** | `.claude/backend/tests/phase_badge/`, `phase7/` |
| **Management** | `starview_app/management/commands/award_pioneer_badges.py`, `audit_badges.py` |

---

**Last Updated:** 2025-11-27
**Status:** Production Ready ✅
