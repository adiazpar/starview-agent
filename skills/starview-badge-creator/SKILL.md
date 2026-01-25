---
name: create-badge
description: Create new badges for the Starview badge system. Use when adding badges, creating achievement badges, or implementing new badge criteria.
user-invocable: true
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Edit, Write, Bash, EnterPlanMode, ExitPlanMode, AskUserQuestion, TodoWrite
model: sonnet
---

# Badge Creator

Create new badges for the Starview badge system following established patterns.

## Prerequisites

Before starting, you need:
- Badge concept (name, description, what it rewards)
- Icon file (.png, 256x256px with transparency)

## Workflow

### Phase 1: Planning

1. **Enter plan mode** using EnterPlanMode tool
2. **Read** `references/QUICK_REFERENCE.md` for existing criteria types and badges
3. **Analyze** existing badges to avoid conflicts (see planning workflow)
4. **Gather details** from user using AskUserQuestion
5. **Write plan** with badge specification and implementation steps
6. **Exit plan mode** after user approval

See `references/PLANNING_WORKFLOW.md` for detailed planning steps and questions to ask.

### Phase 2: Implementation

1. Place icon in `starview_frontend/public/badges/{slug}.png`
2. Create data migration in `starview_app/migrations/`
3. Run migration
4. Add BadgeService method (if new criteria type)
5. Add signal handler (if new trigger)
6. Test the badge
7. Run `/update-docs`

See `references/IMPLEMENTATION.md` for migration templates and code examples.

## Reference Files

| File | Contains | When to Read |
|------|----------|--------------|
| [PLANNING_WORKFLOW.md](references/PLANNING_WORKFLOW.md) | Plan mode steps, questions to ask | During planning phase |
| [IMPLEMENTATION.md](references/IMPLEMENTATION.md) | Migration templates, signals, testing | During implementation |
| [QUICK_REFERENCE.md](references/QUICK_REFERENCE.md) | Criteria types, existing badges | When checking for conflicts |

## External Documentation

For complex badges or deep dives:
- `.claude/backend/docs/badge_system/BADGE_SYSTEM.md` - Full badge system design
- `.claude/backend/docs/badge_system/IMPLEMENTATION_GUIDE.md` - Technical architecture
