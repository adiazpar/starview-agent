---
description: Create a new badge for the Starview badge system
---

# Badge Creation Workflow

**IMPORTANT:** You MUST enter plan mode before proceeding. Use the EnterPlanMode tool now.

## Plan Mode Instructions

Once in plan mode, follow these steps:

### Step 1: Read Badge System Documentation

Read these files to understand the current badge system:
- `.claude/skills/starview-badge-creator/SKILL.md` - Badge creation guide
- `.claude/backend/docs/badge_system/BADGE_SYSTEM.md` - Full badge design (if complex badge)

### Step 2: Analyze Existing Badges

Query the database or read migrations to understand:
- Current badge tiers and criteria values (avoid conflicts)
- Existing criteria types (prefer reusing existing types)
- Display order within categories

### Step 3: Ask Clarification Questions

Use AskUserQuestion to gather badge details:

**Question 1 - Basic Info:**
- Badge name (display name, e.g., "Night Owl")
- Badge slug (URL-safe, e.g., "night-owl")
- Description (user-facing, e.g., "Visit 10 locations at night")

**Question 2 - Category:**
- EXPLORATION (visiting locations)
- CONTRIBUTION (adding locations)
- QUALITY (well-rated locations)
- REVIEW (writing reviews)
- COMMUNITY (social engagement)
- SPECIAL (unique achievements)
- TENURE (membership milestones)

**Question 3 - Criteria:**
- Criteria type (see existing types in skill guide)
- Criteria value (threshold to earn)
- Flag any conflicts with existing badges

**Question 4 - Tier & Display:**
- Tier (1-5, where 1=bronze, 5=master)
- Is this a rare badge?
- Display order within category

**Question 5 - Icon:**
- Does user have icon file ready? (256x256 PNG with transparency)
- Where is the icon file located?

### Step 4: Write Implementation Plan

In your plan file, include:
1. Badge specification (all fields)
2. Any conflicts identified and how to resolve
3. Whether new criteria type or signal handler is needed
4. Migration file name and content preview
5. Testing steps

### Step 5: Exit Plan Mode

After user approves the plan, exit plan mode and execute:
1. Copy icon to `starview_frontend/public/badges/{slug}.png`
2. Create migration in `starview_app/migrations/`
3. Run migration
4. Verify badge in database
5. Restart server to clear badge cache
6. Run `/update-docs` to update documentation

## Existing Criteria Types (for reference)

| Type | Trigger | Use For |
|------|---------|---------|
| LOCATION_VISITS | LocationVisit post_save | Visiting locations |
| LOCATIONS_ADDED | Location post_save | Creating locations |
| LOCATION_RATING | Review post_save | High-rated locations |
| REVIEWS_WRITTEN | Review post_save | Writing reviews |
| UPVOTES_RECEIVED | Vote post_save | Getting upvotes |
| HELPFUL_RATIO | Vote post_save | Upvote percentage |
| COMMENTS_WRITTEN | ReviewComment post_save | Writing comments |
| FOLLOWER_COUNT | Follow post_save | Social following |
| PHOTOS_UPLOADED | ReviewPhoto post_save | Uploading photos |
| PIONEER | email_confirmed signal | First 100 users |
