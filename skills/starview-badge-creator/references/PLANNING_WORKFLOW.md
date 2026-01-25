# Badge Planning Workflow

Step-by-step workflow for planning a new badge before implementation.

## Step 1: Enter Plan Mode

**IMPORTANT:** Use the EnterPlanMode tool before proceeding. Badge creation requires planning to avoid conflicts with existing badges.

## Step 2: Read Badge System Documentation

Read these files to understand the current badge system:
- `references/QUICK_REFERENCE.md` - Criteria types and existing badges
- `.claude/backend/docs/badge_system/BADGE_SYSTEM.md` - Full badge design (for complex badges)
- `.claude/backend/docs/badge_system/IMPLEMENTATION_GUIDE.md` - Technical details

## Step 3: Analyze Existing Badges

Query the database or read migrations to understand:
- Current badge tiers and criteria values (avoid conflicts)
- Existing criteria types (prefer reusing existing types)
- Display order within categories

```bash
djvenv/bin/python manage.py shell -c "
from starview_app.models import Badge
for b in Badge.objects.all().order_by('category', 'tier'):
    print(f'{b.category}: {b.name} (tier {b.tier}, {b.criteria_type}={b.criteria_value})')
"
```

## Step 4: Ask Clarification Questions

Use AskUserQuestion to gather badge details:

### Question 1 - Basic Info
- Badge name (display name, e.g., "Night Owl")
- Badge slug (URL-safe, e.g., "night-owl")
- Description (user-facing, e.g., "Visit 10 locations at night")

### Question 2 - Category
- EXPLORATION (visiting locations)
- CONTRIBUTION (adding locations)
- QUALITY (well-rated locations)
- REVIEW (writing reviews)
- COMMUNITY (social engagement)
- SPECIAL (unique achievements)
- TENURE (membership milestones)

### Question 3 - Criteria
- Criteria type (see `references/QUICK_REFERENCE.md` for existing types)
- Criteria value (threshold to earn)
- Flag any conflicts with existing badges

### Question 4 - Tier & Display
- Tier (1-5, where 1=bronze, 5=master)
- Is this a rare badge?
- Display order within category

### Question 5 - Icon
- Does user have icon file ready? (256x256 PNG with transparency)
- Where is the icon file located?

## Step 5: Write Implementation Plan

In your plan file, include:
1. Badge specification (all fields)
2. Any conflicts identified and how to resolve
3. Whether new criteria type or signal handler is needed
4. Migration file name and content preview
5. Testing steps

## Step 6: Exit Plan Mode

After user approves the plan, exit plan mode and follow `references/IMPLEMENTATION.md` to execute:
1. Copy icon to `starview_frontend/public/badges/{slug}.png`
2. Create migration in `starview_app/migrations/`
3. Run migration
4. Verify badge in database
5. Restart server to clear badge cache
6. Run `/update-docs` to update documentation
