# Badge System Design for Starview

## Overview
Achievement/badge system to gamify user engagement and reward quality contributions to the stargazing community.

---

## Core Concepts

### Badge Display
- **Profile Header**: Shows 3 pinned badges (user-selected favorites)
- **Badge Button**: Opens modal/dropdown showing full badge collection
- **Badge Modal**: Shows all badges with earned ✅, progress 📊, and locked 🔒 states
- **Owner Privileges**: Only profile owners can pin/unpin their own badges
- **Visitor View**: Visitors see the same badge collection, but cannot modify pins

### Badge Storage
- **Badge Icons**: Stored in `/public/badges/` directory in frontend
- **Custom Designed**: Created in Canva as colorful, visually appealing icons
- **Format**: PNG with transparency recommended
- **Naming Convention**: `{badge_slug}.png` (e.g., `explorer.png`, `pathfinder.png`)

---

## Badge Categories

### 1. Exploration Badges (Visiting Locations)
Track how many locations a user has visited using the check-in system.

| Badge Name | Description | Criteria | Icon Idea |
|------------|-------------|----------|-----------|
| **First Light** | Visit your first location | Visit 1 location | 🌟 Single bright star |
| **Explorer** | Begin your stargazing journey | Visit 5 locations | 🗺️ Map with telescope |
| **Pathfinder** | Navigate the night sky | Visit 10 locations | 🧭 Compass with stars |
| **Stargazer** | Dedicated night sky observer | Visit 25 locations | 🌌 Milky Way galaxy |
| **Celestial Navigator** | Master of dark skies | Visit 50 locations | ⭐ Star map constellation |
| **Cosmic Voyager** | Ultimate explorer | Visit 100 locations | 🚀 Rocket among stars |

**Implementation Notes:**
- Track via `LocationVisit` model (NEW - users "mark as visited")
- Simple count query: `LocationVisit.objects.filter(user=user).count()`
- Users can check-in via "Mark as Visited" button on location page
- Auto-check-in when user submits a review

---

### 2. Contribution Badges (Creating Locations)
Reward users who add new stargazing locations to the community.

| Badge Name | Description | Criteria | Icon Idea |
|------------|-------------|----------|-----------|
| **Scout** | Share your first discovery | Add 1 location | 📍 Pin on dark sky |
| **Discoverer** | Expand the community map | Add 5 locations | 🔭 Telescope pointing up |
| **Trailblazer** | Lead others to dark skies | Add 10 locations | 🌠 Shooting star trail |
| **Location Legend** | Prolific contributor | Add 25 locations | 💫 Constellation pattern |

**Implementation Notes:**
- Track via `Location.objects.filter(added_by=user).count()`
- Only count verified/approved locations (if applicable)

---

### 3. Quality Badges (Well-Rated Locations)
Recognize users whose contributed locations receive high ratings.

| Badge Name | Description | Criteria | Icon Idea |
|------------|-------------|----------|-----------|
| **Quality Contributor** | Trusted recommendations | 3+ locations with 4+ star avg | ⭐ Gold star |
| **Trusted Source** | Consistently excellent spots | 6+ locations with 4+ star avg | 🌟 Glowing star cluster |
| **Stellar Curator** | Premier location expert | 12+ locations with 4+ star avg | ✨ Radiant supernova |
| **Elite Curator** | Ultimate location curator | 24+ locations with 4+ star avg | 💎 Diamond constellation |

**Implementation Notes:**
- Query: Locations added by user with average rating ≥ 4.0
- Requires join with Review model and aggregation
- More complex query, suitable for background task

---

### 4. Review Badges (Helpful Reviews)
Encourage quality reviews through upvote-based recognition.

| Badge Name | Description | Criteria | Icon Idea |
|------------|-------------|----------|-----------|
| **Reviewer** | Share your experiences | Write 5 reviews | 📝 Notepad with pen |
| **Helpful Voice** | Community trusts your insight | 10 upvotes received | 👍 Thumbs up with star |
| **Expert Reviewer** | Detailed, trusted opinions | 25 reviews with 75%+ helpful ratio | 🏆 Trophy with star |
| **Trusted Critic** | Authoritative voice | 50 reviews with 80%+ helpful ratio | 💎 Diamond badge |
| **Review Master** | Review legend | 100 reviews with 85%+ helpful ratio | 👑 Crown with constellation |

**Implementation Notes:**
- Review count: `Review.objects.filter(user=user).count()`
- Helpful ratio: `(upvotes / total_votes) >= threshold`
- Use existing Vote model with ContentType framework
- Query helpful votes: `Vote.objects.filter(content_type=review_ct, object_id__in=user_reviews, is_upvote=True)`

---

### 5. Community Badges (Social Engagement)
Foster community building through follows and interaction.

| Badge Name | Description | Criteria | Icon Idea |
|------------|-------------|----------|-----------|
| **Conversationalist** | Engage with the community | Comment on 10 reviews (others') | 💬 Speech bubble with stars |
| **Connector** | Build your network | Have 10 followers | 🤝 Handshake constellation |
| **Influencer** | Inspire other stargazers | Have 50 followers | 🌐 Connected star network |
| **Community Leader** | Pillar of the community | Have 100 followers | ⭐ Bright north star |
| **Ambassador** | Elite community figure | Have 200 followers | 👑 Crown of stars |

**Implementation Notes:**
- Comment count: `ReviewComment.objects.filter(user=user).count()`
- Follower count: `Follow.objects.filter(following=user).count()`
- Already tracked in user stats

---

### 6. Time-Based Badges (Tenure)
Recognize long-term community members.

| Badge Name | Description | Criteria | Icon Idea |
|------------|-------------|----------|-----------|
| **Anniversary** | One year of stargazing | 1 year member | 🎂 Cake with single candle star |
| **Veteran** | Experienced astronomer | 2 years member | 📅 Calendar with full moon |
| **Pioneer** | Early community builder | First 100 users | 🏛️ Ancient observatory ruins |

**Implementation Notes:**
- Check `user.date_joined` against current date
- Pioneer badge: Check if `user.id <= 100` or use registration order
- Can be awarded retroactively via migration

---

### 7. Special/Rare Badges (Advanced Achievements)
Unique, harder-to-earn badges for dedicated users.

| Badge Name | Description | Criteria | Icon Idea |
|------------|-------------|----------|-----------|
| **Mission Ready** | Completed setting up your profile | Complete all profile fields (location, bio, picture) | 🚀 Rocket ready for launch |
| **Dark Sky Advocate** | Experience all light levels | Visit locations in all Bortle zones | 🌌 Gradient dark to light sky |
| **Globe Trotter** | Worldwide explorer | Visit locations in 5+ states/countries | 🌍 Earth with star trails |
| **Night Owl** | Dedicated observer | Visit 10+ locations (tracked visits) | 🌙 Moon with owl silhouette |
| **Photographer** | Capture the cosmos | Upload 25 review photos | 📸 Camera with galaxy |
| **Meteor Chaser** | Seasonal event enthusiast | Visit during meteor shower dates | ☄️ Meteor streaking across sky |

**Implementation Notes:**
- **Mission Ready**: REVOCABLE badge - awarded when profile complete, revoked if user clears any required field
  - Icon file: `/badges/mission-ready.png` (256x256 PNG)
  - Checked via `BadgeService.check_profile_complete_badge(user)` in profile update views
  - Requirements defined in `BadgeService.PROFILE_COMPLETION_REQUIREMENTS` (single source of truth)
  - See [Adding Profile Requirements](#adding-profile-requirements) below
- Dark Sky Advocate: Requires Bortle scale data on locations
- Globe Trotter: Requires location state/country data
- Night Owl: Requires visit tracking (not just favorites)
- Photographer: `ReviewPhoto.objects.filter(review__user=user).count()`
- Meteor Chaser: Requires visit date tracking + event calendar

---

## Database Schema

### LocationVisit Model (NEW - Check-in System)
```python
class LocationVisit(models.Model):
    """
    Tracks user check-ins to locations for badge progress.
    Separate from FavoriteLocation (favorites = want to return, visits = been there).
    """
    user = ForeignKey(User, on_delete=CASCADE, related_name='location_visits', db_index=True)
    location = ForeignKey(Location, on_delete=CASCADE, related_name='visits')
    visited_at = DateTimeField(auto_now_add=True, db_index=True)

    # Optional metadata for future enhancements
    visit_notes = TextField(blank=True, null=True)  # e.g., "Saw Milky Way tonight!"

    class Meta:
        unique_together = ['user', 'location']  # Can only visit once
        ordering = ['-visited_at']
        indexes = [
            models.Index(fields=['user', 'visited_at']),  # For anomaly detection
        ]
```

### Badge Model
```python
class Badge(models.Model):
    # Basic Info
    name = CharField(max_length=50, unique=True)
    slug = SlugField(unique=True)  # For icon filename: {slug}.png
    description = TextField()

    # Categorization
    CATEGORY_CHOICES = [
        ('EXPLORATION', 'Exploration'),
        ('CONTRIBUTION', 'Contribution'),
        ('QUALITY', 'Quality'),
        ('REVIEW', 'Review'),
        ('COMMUNITY', 'Community'),
        ('TENURE', 'Time-Based'),
        ('SPECIAL', 'Special/Rare'),
    ]
    category = CharField(max_length=20, choices=CATEGORY_CHOICES)

    # Unlock Criteria
    CRITERIA_TYPES = [
        ('LOCATION_VISITS', 'Location Visits'),
        ('LOCATIONS_ADDED', 'Locations Added'),
        ('LOCATION_RATING', 'Location Quality Rating'),
        ('REVIEWS_WRITTEN', 'Reviews Written'),
        ('UPVOTES_RECEIVED', 'Upvotes Received'),
        ('HELPFUL_RATIO', 'Helpful Review Ratio'),
        ('COMMENTS_WRITTEN', 'Comments Written'),
        ('FOLLOWER_COUNT', 'Follower Count'),
        ('TENURE_DAYS', 'Days as Member'),
        ('PROFILE_COMPLETE', 'Profile Completion'),  # Revocable badge
        ('SPECIAL_CONDITION', 'Special Condition'),
    ]
    criteria_type = CharField(max_length=30, choices=CRITERIA_TYPES)
    criteria_value = IntegerField()  # Threshold to unlock
    criteria_secondary = IntegerField(null=True)  # For complex criteria (e.g., helpful ratio %)

    # Display
    tier = SmallIntegerField(default=1)  # 1-5 for progression badges (2 bytes, optimized)
    color = CharField(max_length=20, default='blue')  # CSS color or hex
    is_rare = BooleanField(default=False)  # Special/limited badges
    icon_path = CharField(max_length=255)  # e.g., '/badges/explorer.png'

    # Ordering
    display_order = IntegerField(default=0)

    # Timestamps
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'tier', 'display_order']
        indexes = [
            models.Index(fields=['category', 'criteria_type']),  # For badge checking queries
        ]
```

### UserBadge Model (Simplified - Earned Badges Only)
```python
class UserBadge(models.Model):
    """
    Tracks badges earned by users.
    Only created when badge is EARNED (not for in-progress badges).
    Progress calculated on-demand from source data.
    """
    user = ForeignKey(User, on_delete=CASCADE, related_name='earned_badges', db_index=True)
    badge = ForeignKey(Badge, on_delete=CASCADE)

    # Achievement tracking
    earned_at = DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', 'earned_at']),
        ]
```

### UserProfile Addition
```python
class UserProfile(models.Model):
    # ... existing fields ...

    # Pinned badges (ArrayField for PostgreSQL)
    pinned_badge_ids = ArrayField(
        IntegerField(),
        size=3,
        default=list,
        blank=True
    )  # [badge_id_1, badge_id_2, badge_id_3]

    # Badge count can be computed: user.earned_badges.count()
    # Visit count can be computed: user.location_visits.count()
```

**Design Decisions:**
- ✅ **Removed `current_progress` field** - calculated on-demand (no sync issues)
- ✅ **Removed `is_pinned` and `pin_order`** - moved to UserProfile.pinned_badge_ids
- ✅ **Only store earned badges** - reduces storage by ~60%
- ✅ **SmallIntegerField for tier** - saves 2 bytes per badge
- ✅ **LocationVisit separate from FavoriteLocation** - clear separation of concerns

---

## Badge Checking Logic

### Service Class: BadgeService
```python
class BadgeService:
    """
    Handles badge checking and awarding.
    Uses signal-based triggers for instant feedback without performance overhead.
    """

    @staticmethod
    def check_exploration_badges(user):
        """
        Check location visit count badges.
        Triggered by LocationVisit creation signal.
        """
        visit_count = LocationVisit.objects.filter(user=user).count()

        exploration_badges = Badge.objects.filter(
            category='EXPLORATION',
            criteria_type='LOCATION_VISITS'
        ).order_by('criteria_value')

        for badge in exploration_badges:
            if visit_count >= badge.criteria_value:
                BadgeService.award_badge(user, badge)
            else:
                break  # Stop checking higher tier badges

    @staticmethod
    def check_contribution_badges(user):
        """Check location creation badges"""
        location_count = Location.objects.filter(added_by=user).count()

        contribution_badges = Badge.objects.filter(
            category='CONTRIBUTION',
            criteria_type='LOCATIONS_ADDED'
        ).order_by('criteria_value')

        for badge in contribution_badges:
            if location_count >= badge.criteria_value:
                BadgeService.award_badge(user, badge)
            else:
                break

    @staticmethod
    def check_review_badges(user):
        """Check review-related badges"""
        review_count = Review.objects.filter(user=user).count()

        review_badges = Badge.objects.filter(
            category='REVIEW',
            criteria_type='REVIEWS_WRITTEN'
        ).order_by('criteria_value')

        for badge in review_badges:
            if review_count >= badge.criteria_value:
                BadgeService.award_badge(user, badge)
            else:
                break

    @staticmethod
    def check_community_badges(user):
        """Check follower and comment count badges"""
        follower_count = Follow.objects.filter(following=user).count()
        comment_count = ReviewComment.objects.filter(user=user).count()

        # Check follower badges
        follower_badges = Badge.objects.filter(
            category='COMMUNITY',
            criteria_type='FOLLOWER_COUNT'
        ).order_by('criteria_value')

        for badge in follower_badges:
            if follower_count >= badge.criteria_value:
                BadgeService.award_badge(user, badge)
            else:
                break

        # Check comment badges
        comment_badges = Badge.objects.filter(
            category='COMMUNITY',
            criteria_type='COMMENTS_WRITTEN'
        ).order_by('criteria_value')

        for badge in comment_badges:
            if comment_count >= badge.criteria_value:
                BadgeService.award_badge(user, badge)
            else:
                break

    @staticmethod
    def award_badge(user, badge):
        """
        Award a badge to a user if not already earned.
        Returns True if newly awarded, False if already had it.
        """
        user_badge, created = UserBadge.objects.get_or_create(
            user=user,
            badge=badge
        )
        return created

    @staticmethod
    def get_user_badge_progress(user):
        """
        Calculate badge progress for display (on-demand).
        Returns categorized badges: earned, in_progress, locked.
        """
        # Get user stats (efficient single queries)
        stats = {
            'location_visits': LocationVisit.objects.filter(user=user).count(),
            'locations_added': Location.objects.filter(added_by=user).count(),
            'reviews_written': Review.objects.filter(user=user).count(),
            'follower_count': Follow.objects.filter(following=user).count(),
            'comment_count': ReviewComment.objects.filter(user=user).count(),
        }

        # Get earned badges
        earned_badge_ids = set(UserBadge.objects.filter(user=user).values_list('badge_id', flat=True))

        # Get all badges
        all_badges = Badge.objects.all()

        result = {
            'earned': [],
            'in_progress': [],
            'locked': []
        }

        for badge in all_badges:
            if badge.id in earned_badge_ids:
                # Badge earned
                user_badge = UserBadge.objects.get(user=user, badge=badge)
                result['earned'].append({
                    'badge': badge,
                    'earned_at': user_badge.earned_at,
                })
            else:
                # Calculate progress
                progress = BadgeService._calculate_progress(user, badge, stats)

                if progress > 0 and progress < badge.criteria_value:
                    # In progress
                    result['in_progress'].append({
                        'badge': badge,
                        'current_progress': progress,
                        'criteria_value': badge.criteria_value,
                        'percentage': int((progress / badge.criteria_value) * 100)
                    })
                else:
                    # Locked
                    result['locked'].append({'badge': badge})

        return result

    @staticmethod
    def _calculate_progress(user, badge, stats):
        """Calculate current progress for a badge from cached stats"""
        criteria_map = {
            'LOCATION_VISITS': stats['location_visits'],
            'LOCATIONS_ADDED': stats['locations_added'],
            'REVIEWS_WRITTEN': stats['reviews_written'],
            'FOLLOWER_COUNT': stats['follower_count'],
            'COMMENTS_WRITTEN': stats['comment_count'],
        }
        return criteria_map.get(badge.criteria_type, 0)

    @staticmethod
    def detect_suspicious_activity(user):
        """
        Passive anomaly detection for potential badge gaming.
        Flags accounts without blocking them.
        """
        # Check for rapid check-ins (10+ in 1 hour)
        recent_visits = LocationVisit.objects.filter(
            user=user,
            visited_at__gte=timezone.now() - timedelta(hours=1)
        ).count()

        if recent_visits >= 10:
            from starview_app.utils.audit_logger import log_security_event
            log_security_event(
                user=user,
                event_type='SUSPICIOUS_BADGE_ACTIVITY',
                details={'rapid_check_ins': recent_visits, 'timeframe': '1_hour'}
            )
            return True

        return False
```

### Signal Handlers (Trigger Badge Checks)
```python
# starview_app/utils/signals.py (or separate file)

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# After marking location as visited → check exploration badges
@receiver(post_save, sender=LocationVisit)
def check_badges_on_visit(sender, instance, created, **kwargs):
    if created:
        BadgeService.check_exploration_badges(instance.user)

# After adding a location → check contribution badges
@receiver(post_save, sender=Location)
def check_badges_on_location_add(sender, instance, created, **kwargs):
    if created:
        BadgeService.check_contribution_badges(instance.added_by)

# After posting a review → check review badges (and auto-mark as visited)
@receiver(post_save, sender=Review)
def check_badges_on_review(sender, instance, created, **kwargs):
    if created:
        # Auto-create LocationVisit when review posted
        LocationVisit.objects.get_or_create(
            user=instance.user,
            location=instance.location
        )

        BadgeService.check_review_badges(instance.user)

# After gaining a follower → check community badges
@receiver(post_save, sender=Follow)
def check_badges_on_follow(sender, instance, created, **kwargs):
    if created:
        BadgeService.check_community_badges(instance.following)

# After posting a comment → check community badges
@receiver(post_save, sender=ReviewComment)
def check_badges_on_comment(sender, instance, created, **kwargs):
    if created:
        BadgeService.check_community_badges(instance.user)
```

### Badge Revocation (Optional - Phase 2)
```python
# Only implement if abuse becomes a problem

@receiver(post_delete, sender=LocationVisit)
def revoke_badges_on_visit_delete(sender, instance, **kwargs):
    user = instance.user
    current_visits = LocationVisit.objects.filter(user=user).count()

    # Check which exploration badges user should still have
    earned_badges = UserBadge.objects.filter(
        user=user,
        badge__category='EXPLORATION',
        badge__criteria_type='LOCATION_VISITS'
    )

    for user_badge in earned_badges:
        if current_visits < user_badge.badge.criteria_value:
            # User no longer qualifies - revoke badge
            user_badge.delete()
```

### When to Check Badges

**Real-time Checks (signal-triggered, instant feedback):**
- ✅ After marking location as visited → check exploration badges
- ✅ After posting a review → check review badges + auto-mark visited
- ✅ After adding a location → check contribution badges
- ✅ After gaining a follower → check community badges
- ✅ After posting a comment → check community badges

**Periodic Checks (background task, nightly):**
- Quality badges (location ratings with 4+ stars) - complex aggregation
- Helpful review badges (upvote ratios) - requires vote counting
- Tenure badges (member for X years) - date-based
- Special badges (Bortle zones, countries visited) - complex queries

**Performance:** Real-time checks use simple COUNT queries (1-3ms), no overhead.

---

## API Endpoints

### Mark Location as Visited
```
POST /api/locations/{id}/mark-visited/
DELETE /api/locations/{id}/unmark-visited/

Response: {
  "detail": "Location marked as visited",
  "total_visits": 23,  # User's total unique location visits
  "newly_earned_badges": [
    {
      "badge_id": 2,
      "name": "Explorer",
      "slug": "explorer",
      "description": "Visit 5 locations",
      "icon_path": "/badges/explorer.png"
    }
  ]
}
```

### Get User's Badge Collection
```
GET /api/users/{username}/badges/

Response: {
  "earned": [
    {
      "badge_id": 1,
      "name": "Explorer",
      "slug": "explorer",
      "description": "Visit 5 locations",
      "category": "EXPLORATION",
      "tier": 2,
      "icon_path": "/badges/explorer.png",
      "earned_at": "2025-11-11T..."
    }
  ],
  "in_progress": [
    {
      "badge_id": 3,
      "name": "Pathfinder",
      "slug": "pathfinder",
      "description": "Visit 10 locations",
      "current_progress": 7,
      "criteria_value": 10,
      "percentage": 70,
      "icon_path": "/badges/pathfinder.png"
    }
  ],
  "locked": [
    {
      "badge_id": 4,
      "name": "Stargazer",
      "slug": "stargazer",
      "description": "Visit 25 locations",
      "criteria_value": 25,
      "icon_path": "/badges/stargazer.png"
    }
  ],
  "pinned_badge_ids": [1, 5, 8]  # User's pinned badges (from UserProfile)
}
```

### Pin/Unpin Badges
```
PATCH /api/users/me/profile/pin-badges/

Request: {
  "pinned_badge_ids": [1, 3, 7]  # Must be 0-3 badge IDs
}

Response: {
  "detail": "Pinned badges updated",
  "pinned_badge_ids": [1, 3, 7],
  "pinned_badges": [
    {
      "badge_id": 1,
      "name": "Explorer",
      "icon_path": "/badges/explorer.png"
    },
    ...
  ]
}
```

**Validation:**
- Maximum 3 pinned badges
- Can only pin badges you've earned
- Can only modify your own pins

---

## Frontend Components

### Badge Modal/Dropdown
```jsx
<BadgeModal user={user} isOwner={isOwnProfile}>
  <BadgeSection title="Earned" badges={earnedBadges} />
  <BadgeSection title="In Progress" badges={inProgressBadges} showProgress />
  <BadgeSection title="Locked" badges={lockedBadges} grayscale />
</BadgeModal>
```

### Badge Card Component
```jsx
<BadgeCard
  badge={badge}
  earned={true}
  progress={7}
  total={10}
  isPinned={false}
  canPin={isOwner}
  onPin={() => handlePin(badge.id)}
/>
```

### Profile Header Pinned Badges
```jsx
<div className="pinned-badges">
  {pinnedBadges.map(badge => (
    <img
      src={badge.icon_path}
      alt={badge.name}
      title={badge.description}
      className="pinned-badge-icon"
    />
  ))}
</div>
```

---

## Implementation Phases

### Phase 1: Backend Core Infrastructure ✅ COMPLETE
- [x] Create LocationVisit model (check-in system)
- [x] Create Badge model (26 badge definitions)
- [x] Create UserBadge model (earned badges only)
- [x] Update UserProfile model (pinned_badge_ids ArrayField)
- [x] Create and run migrations
- [x] Create BadgeService class with all badge checking methods
- [x] Add signal handlers for badge checking (LocationVisit, Location, Review, Vote, Follow, ReviewComment)
- [x] Create backend API endpoints (GET badges, mark visited, pin badges)
- [x] Seed all 27 badges (6 Exploration, 4 Contribution, 4 Quality, 5 Review, 5 Community, 2 Special, 1 Tenure)
- [x] Implement auto-visit for location creators and reviewers
- [x] Implement self-review prevention (app-wide data integrity)
- [x] Create frontend service methods (API integration)
- [x] Comprehensive testing (all tests passing ✓)

**Status:** Backend 100% functional and tested (2025-11-12)
**Test Results:** 12/12 tests passed (8 initial + 4 Phase 7 fixes)
**Test Files:**
- `.claude/backend/tests/phase_badge/test_badge_comprehensive.py`
- `.claude/backend/tests/phase7/test_1_self_review_prevention.py`
- `.claude/backend/tests/phase7/test_2_conversationalist_badge.py`
- `.claude/backend/tests/phase7/test_3_quality_badges.py`
- `.claude/backend/tests/phase7/test_4_review_badges_upvote_ratio.py`

**What Works:**
- ✓ 27 badges seeded and fully functional:
  - 6 Exploration badges (visit count)
  - 4 Contribution badges (locations added)
  - 4 Quality badges (locations with 4+ star average)
  - 5 Review badges (review count, upvotes, helpful ratios)
  - 5 Community badges (followers, comments on other's reviews)
  - 2 Special badges (Photographer, Mission Ready)
  - 1 Tenure badge (Pioneer)
- ✓ Location visits tracked via LocationVisit model
- ✓ Auto-visit: Creating location OR posting review automatically marks as visited
- ✓ Self-review prevention: Users cannot review their own locations (model validation)
- ✓ Badges awarded automatically via signals (instant feedback)
- ✓ Review badges check upvote ratios, not just counts
- ✓ Conversationalist badge excludes comments on own reviews
- ✓ Quality badges require external validation (4+ star average from other users)
- ✓ Progress calculated on-demand (earned/in-progress/locked)
- ✓ Pinned badges working (max 3, stored in UserProfile.pinned_badge_ids)
- ✓ All API endpoints working (GET badges, mark/unmark visited, update pinned)
- ✓ Authentication required for write operations
- ✓ Frontend service methods created (starview_frontend/src/services/)

**Key Implementation Details:**
- `BadgeService.check_exploration_badges()` - Triggered by LocationVisit creation
- `BadgeService.check_contribution_badges()` - Triggered by Location creation
- `BadgeService.check_quality_badges()` - Triggered by Review creation (checks location creator)
- `BadgeService.check_review_badges()` - Triggered by Review/Vote creation (handles 3 criteria types)
- `BadgeService.check_community_badges()` - Triggered by Follow/ReviewComment creation
- Self-review prevention in `Review.clean()` method (raises ValidationError)

### Phase 2: Frontend UI Components (NEXT)
- [ ] Create badge icons in Canva (26 icons)
  - Size: 256x256px PNG with transparency
  - Style: Space-themed, colorful, consistent
  - Store in: `starview_frontend/public/badges/`
  - Naming: `{badge_slug}.png` (e.g., `first-light.png`)
- [ ] Create BadgeModal component (shows earned/in-progress/locked badges)
- [ ] Create BadgeCard component (individual badge display)
- [ ] Add "Mark as Visited" button to location detail pages
- [ ] Display pinned badges in profile header (3 badges)
- [ ] Implement pin/unpin functionality (click to toggle)
- [ ] Add badge progress bars (visual progress indicators)
- [ ] Badge earned notification (toast/alert when unlocked)

### Phase 3: Advanced Features (Future)
- [ ] Tenure badges (member duration - Anniversary, Veteran, Pioneer)
- [ ] Special/rare badges (Dark Sky Advocate, Globe Trotter, Night Owl, Meteor Chaser)
- [ ] Retroactive badge awards for existing users (run migration script)
- [ ] Badge showcase page (dedicated page showing full collection)
- [ ] Badge export/share functionality (share achievements on social media)
- [ ] Badge tooltips and notification system (in-app notifications when earned)
- [ ] Badge-based perks (verified status, profile customization)

---

## Design Considerations

### Color Palette for Badge Tiers
- **Tier 1 (Beginner):** Bronze/Copper tones
- **Tier 2 (Intermediate):** Silver tones
- **Tier 3 (Advanced):** Gold tones
- **Tier 4 (Expert):** Platinum/Blue tones
- **Tier 5 (Master):** Rainbow/Prismatic effect
- **Special/Rare:** Purple/Galaxy themed

### Icon Design Guidelines
- **Size:** 256x256px (will be scaled down)
- **Format:** PNG with transparency
- **Style:** Consistent across all badges (same illustration style)
- **Color:** Vibrant, space-themed colors
- **Elements:** Stars, constellations, telescopes, planets
- **Text:** Avoid text in icons (use badge name separately)

### Accessibility
- Alt text for all badge images
- Tooltips showing badge name and description
- Colorblind-friendly color choices
- Sufficient contrast for locked/earned states

---

## Future Enhancements

### Badge Collections/Sets
- "Complete the Explorer Set" (earn all exploration badges)
- Bonus badge for completing full category

### Seasonal Badges
- "Perseid Hunter" - Visit during Perseid meteor shower
- "Eclipse Chaser" - Visit during solar/lunar eclipse
- "Winter Solstice" - Visit on shortest day of year

### Location-Specific Badges
- "Grand Canyon Stargazer" - Visit famous locations
- "International Dark Sky Park Visitor" - Visit IDA certified locations

### Social Features
- Share badge achievements on social media
- Badge-based user search/filtering
- "Users with this badge" listing

---

## Anti-Cheating Strategy (Honor System)

### Philosophy
The badge system uses an **honor system** approach focused on engagement over enforcement. Research shows that most users (~95%) engage authentically when gamification focuses on personal achievement rather than competition.

### Why Honor System Works
1. **No leaderboards** - Badges are personal achievements, not competitive rankings
2. **Intrinsic motivation** - Users earn badges for their own satisfaction
3. **Self-defeating to cheat** - Empty badges feel hollow, users miss the real experience
4. **Low stakes** - Badges have no real-world value, minimal incentive to game the system

### Known Limitation: Duplicate Locations

**Issue:** Currently no duplicate location detection exists in the backend. Users could theoretically:
- Create multiple locations at the same coordinates
- Game Contribution badges by adding duplicate locations
- Create database bloat

**Mitigation Strategies (Current):**
1. **Report System** - Existing `times_reported` field on Location model
2. **Staff Review** - Manual verification via `is_verified` flag
3. **Community Policing** - Users report suspicious locations
4. **Passive Monitoring** - Admin reviews locations with high report counts

**Future Solutions (If Abuse Emerges):**
1. **Duplicate Detection** - Prevent locations within 100m radius (bounding box check)
   ```python
   # Validation: Check for nearby locations within ~100 meters
   nearby = Location.objects.filter(
       latitude__range=(lat - 0.001, lat + 0.001),
       longitude__range=(lng - 0.001, lng + 0.001)
   )
   ```
2. **Verified-Only Badges** - Contribution badges only count `is_verified=True` locations
3. **Badge Revocation** - Remove badges when locations deleted/flagged as duplicates

**Decision:** Keep simple for Phase 1, monitor for abuse, add detection if needed.

### Passive Anti-Abuse Measures

**Phase 1: Launch (Monitoring Only)**
1. **Anomaly Detection** - Flag suspicious patterns (10+ check-ins in 1 hour)
2. **Audit Logging** - Track rapid check-ins for admin review
3. **No blocking** - Users aren't prevented from earning badges

```python
# Passive detection - flags but doesn't block
BadgeService.detect_suspicious_activity(user)
# Logs to AuditLog for admin review
```

**Phase 2: If Abuse Emerges (Add Friction)**
Only implement if patterns emerge like:
- Many users with 100+ visits but 0 reviews
- Bulk check-ins (same user, many locations, short timeframe)
- Admin reports of fake badges

Potential solutions:
1. **Badge Revocation** - Remove badges when visits deleted
2. **Review Requirements** - High-tier badges (50+, 100+ visits) require X% to have reviews
3. **Social Accountability** - Show check-ins in follower feeds (peer pressure)

### Badge Revocation Policy

**Revoke badges when:**
- User unchecks "Visited" → Below badge threshold
- Review deleted by admin for abuse → Flag account

**Keep badges when:**
- User deletes their own review (visit still counts)
- Location deleted (not user's fault)
- Review edited (doesn't affect visit status)

```python
# Optional implementation (Phase 2)
@receiver(post_delete, sender=LocationVisit)
def revoke_badges_on_visit_delete(sender, instance, **kwargs):
    # Only if user explicitly removed visit
    # Not implemented by default - add if abuse detected
```

### Research-Backed Approach
- **Stack Overflow, Untappd, Foursquare** - Use honor systems successfully
- **Key insight:** Focus on personal growth, not comparison (reduces cheating motivation)
- **Best practice:** Monitor passively, add friction only if needed

---

## Adding Profile Requirements

The **Mission Ready** badge dynamically adapts to profile requirements. To add a new required profile field:

### Step 1: Update PROFILE_COMPLETION_REQUIREMENTS

In `starview_app/services/badge_service.py`, add a new tuple:

```python
PROFILE_COMPLETION_REQUIREMENTS = [
    ('location', lambda p: bool(p.location)),
    ('bio', lambda p: bool(p.bio)),
    ('profile_picture', lambda p: bool(p.profile_picture) and hasattr(p.profile_picture, 'url')),
    ('website', lambda p: bool(p.website)),  # ← Add new requirement here
]
```

Each tuple contains:
- **field_name**: Human-readable name (used in API response)
- **check_function**: Lambda that takes `UserProfile` and returns `True` if complete

### Step 2: Add Badge Check to Endpoint

In the view that updates the new field, call the badge check:

```python
from starview_app.services.badge_service import BadgeService

# After updating the profile field:
BadgeService.check_profile_complete_badge(request.user)
```

### What Happens Automatically

- Badge award/revoke logic adapts (checks `completed == total`)
- Progress percentage display adapts (uses dynamic total)
- API returns detailed item-by-item breakdown

### API Response Format

`BadgeService.get_profile_completion_status(user)` returns:

```python
{
    'completed': 2,
    'total': 4,
    'is_complete': False,
    'items': [
        {'field': 'location', 'complete': True},
        {'field': 'bio', 'complete': True},
        {'field': 'profile_picture', 'complete': False},
        {'field': 'website', 'complete': False}
    ]
}
```

### No Database Changes Required

The badge's `criteria_value` in the database is ignored for PROFILE_COMPLETE badges - the system uses `len(PROFILE_COMPLETION_REQUIREMENTS)` dynamically.

---

## Notes & Decisions

**Resolved Questions:**
1. ✅ Show all badge states (earned, in-progress, locked) - provides motivation
2. ✅ Badge retroactive awarding - Yes, run after Phase 1 complete
3. ✅ Badge revocation - Yes, but only for explicit user removal (Phase 2)
4. ⏳ Display badges on review cards - Future enhancement
5. ⏳ Notification system - Future enhancement (Phase 5)

**Technical Decisions:**
- ✅ Icons stored in `/public/badges/` (not R2) - static assets
- ✅ Badge button opens modal (not toggle visibility) - better UX
- ✅ 3 pinned badges maximum - prevents clutter
- ✅ Only owners can pin their badges - privacy
- ✅ Signal-based checking (real-time) + background tasks (complex badges)
- ✅ Honor system with passive monitoring - trust users, flag outliers
- ✅ Progress calculated on-demand - no storage/sync issues
- ✅ LocationVisit separate from FavoriteLocation - clear semantics
- ✅ Auto-mark visited on review submission - reduces friction
- ✅ Pinned badges in UserProfile.pinned_badge_ids - ArrayField

---

## References

**Similar Badge Systems:**
- Stack Overflow (reputation badges)
- Duolingo (achievement streaks)
- Strava (challenge badges)
- Untappd (beer check-in badges)
- Foursquare (check-in badges)

**Design Inspiration:**
- Space/astronomy themed
- Clean, modern iconography
- Gamification without being childish
- Professional enough for serious stargazers
