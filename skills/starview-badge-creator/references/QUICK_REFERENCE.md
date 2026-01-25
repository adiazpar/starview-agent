# Badge Quick Reference

Quick lookup for criteria types, categories, and database queries.

## Query Current Badges

**Always query the database for the current badge list** - documentation may be out of date.

```bash
# List all badges with criteria
djvenv/bin/python manage.py shell -c "
from starview_app.models import Badge
for b in Badge.objects.all().order_by('category', 'tier'):
    print(f'{b.category}: {b.name} (tier {b.tier}, {b.criteria_type}={b.criteria_value})')
"

# Check for conflicts with a specific criteria
djvenv/bin/python manage.py shell -c "
from starview_app.models import Badge
criteria_type = 'LOCATION_VISITS'  # Change as needed
for b in Badge.objects.filter(criteria_type=criteria_type).order_by('criteria_value'):
    print(f'{b.name}: {b.criteria_value}')
"
```

## Criteria Types

Use existing criteria types when possible (no new code required):

| Criteria Type | Trigger Signal | Check Method | Use For |
|---------------|----------------|--------------|---------|
| LOCATION_VISITS | LocationVisit post_save | check_exploration_badges | Visiting locations |
| LOCATIONS_ADDED | Location post_save | check_contribution_badges | Creating locations |
| LOCATION_RATING | Review post_save | check_quality_badges | High-rated locations |
| REVIEWS_WRITTEN | Review post_save | check_review_badges | Writing reviews |
| UPVOTES_RECEIVED | Vote post_save | check_review_badges | Getting upvotes |
| HELPFUL_RATIO | Vote post_save | check_review_badges | Upvote percentage |
| COMMENTS_WRITTEN | ReviewComment post_save | check_community_badges | Writing comments |
| FOLLOWER_COUNT | Follow post_save | check_community_badges | Social following |
| PHOTOS_UPLOADED | ReviewPhoto post_save | check_special_badges | Uploading photos |
| PIONEER | email_confirmed signal | check_pioneer_badge | First 100 users |
| PROFILE_COMPLETE | profile update | check_profile_complete_badge | Profile fields filled |

## Badge Categories

| Category | Purpose | Example Use Case |
|----------|---------|------------------|
| EXPLORATION | Visiting locations | Reward users for checking in |
| CONTRIBUTION | Adding locations | Reward users for growing the database |
| QUALITY | Well-rated locations | Reward users whose spots get good reviews |
| REVIEW | Writing reviews | Reward prolific and helpful reviewers |
| COMMUNITY | Social engagement | Reward followers and commenters |
| SPECIAL | Unique achievements | One-off achievements (photos, profile) |
| TENURE | Membership milestones | Early adopters, anniversaries |

## Example Badges (One Per Category)

These are examples to show the pattern - **query the database for the full list**.

| Category | Example Badge | Criteria Type | Example Value |
|----------|---------------|---------------|---------------|
| EXPLORATION | First Light | LOCATION_VISITS | 1 |
| CONTRIBUTION | Scout | LOCATIONS_ADDED | 1 |
| QUALITY | Quality Contributor | LOCATION_RATING | 3 |
| REVIEW | Reviewer | REVIEWS_WRITTEN | 5 |
| COMMUNITY | Conversationalist | COMMENTS_WRITTEN | 10 |
| SPECIAL | Photographer | PHOTOS_UPLOADED | 25 |
| TENURE | Pioneer | PIONEER | 100 |

## Tier Guidelines

| Tier | Difficulty | Typical Threshold Range |
|------|------------|------------------------|
| 1 | Bronze | Entry level (1-5) |
| 2 | Silver | Beginner (5-15) |
| 3 | Gold | Intermediate (15-50) |
| 4 | Platinum | Advanced (50-100) |
| 5 | Master | Expert (100+) |

## Adding a New Badge

Before creating a new badge:

1. **Query existing badges** to check for criteria value conflicts
2. **Prefer existing criteria types** - new types require code changes
3. **Follow tier progression** - higher tiers should have higher thresholds
4. **Check category fit** - use the most appropriate category
