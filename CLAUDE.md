# Project Instructions for Starview

## Auto-Documentation System

This project has automated documentation hooks. **You don't need to remember to update docs** - the system reminds you.

**When you see "PENDING DOCUMENTATION UPDATE" in a session-start reminder:**
Acknowledge it briefly, complete the user's task, then offer to run `/update-docs`.

**When you see "PRE-COMMIT: DOCUMENTATION CHECK" during a commit:**
Pause and ask the user if they want to run `/update-docs` before proceeding.

**What `/update-docs` does:** Spawns an Opus 4.5 subagent to analyze changes and update relevant ARCHITECTURE.md files.

## Documentation Navigation

**START HERE:** `.claude/README.md` - Documentation navigation guide

### Backend (`.claude/backend/`)
- `ARCHITECTURE.md` - Models (20+), API endpoints, services, signals, security
- `docs/CELERY_GUIDE.md` - Async tasks (FREE vs PAID tier)
- `docs/STORAGE_CONFIGURATION.md` - Cloudflare R2 media storage
- `docs/LOGGING_GUIDE.md` - Python logging best practices
- `docs/badge_system/` - Badge system deep dive
- `docs/email_monitoring/` - AWS SES bounce/complaint tracking

### Frontend (`.claude/frontend/`)
- `ARCHITECTURE.md` - Directory structure, data flow, hooks, services, patterns
- `STYLE_GUIDE.md` - Design system (colors, typography, spacing)
- `docs/API_GUIDE.md` - Frontend API endpoint reference
- `docs/MCP_WORKFLOW.md` - Browser automation for visual development
- `references/` - Design inspiration and baseline screenshots

**When to read frontend docs:** Any frontend work, component creation, routing, styling
**Skip frontend docs for:** Backend-only changes, migrations, Django admin

## Skills and Workflows

| Skill | When to Use |
|-------|-------------|
| `starview-badge-creator` | Adding new badges to the badge system |
| `starview-api-endpoint` | Full-stack API: DRF backend + frontend services + React Query |

**Auto-invoke:** When user mentions "create a badge", "new badge", "add a badge" → Enter plan mode, then run `/create-badge`

## Building New Features

1. **Explore first** - Read relevant architecture docs
2. **Check for existing endpoints** - Backend may already have what you need
3. **Use `starview-api-endpoint` skill** when a new API endpoint is needed

## MCP Servers

Two MCP servers for visual frontend development. See `docs/MCP_WORKFLOW.md` for details.

| Server | Purpose |
|--------|---------|
| **puppeteer** | Browser automation, screenshots, form testing |
| **chrome-devtools** | Console logs, network requests, performance analysis |

**IMPORTANT:** Chrome DevTools MCP uses `uid` values from the accessibility tree, NOT CSS selectors. Always call `take_snapshot()` first to get element `uid` values.

## Environment Configuration

**Read `.env` when working on:** Security configs, API integrations (Mapbox, AWS SES), deployment settings, database connections.

## Documentation Standards

**Python code comments** must follow `.claude/backend/docs/DOCUMENTATION_STYLE.md`:
- Header comments focus on **WHY** and **WHAT**, not **HOW**
- Keep headers high-level (10-20 lines maximum)

## Project Context

Django web application for stargazing location reviews:
- Django 5.1.13 + Django REST Framework
- PostgreSQL 17.6 + Redis 7.0
- Cloudflare R2 (media.starview.app)
- AWS SES (noreply@starview.app)
- Celery (optional async tasks)
- django-allauth (email verification + Google OAuth)

## Git Commits

**When committing:**
- Do NOT include Claude attribution in commit messages
- Do NOT add "Co-Authored-By: Claude" or similar
- Do NOT add the robot emoji or "Generated with Claude Code" footer
- Write clean, conventional commit messages as if the user wrote them

## Submodule: .claude Directory

The `.claude/` directory is a Git submodule (`starview-agent`).

**When committing changes inside `.claude/`:**

```bash
# 1. Commit inside the submodule first
git -C .claude add .
git -C .claude commit -m "Your commit message"
git -C .claude push origin main

# 2. Then update the main repo's submodule reference
git add .claude
git commit -m "Update starview-agent submodule"
git push
```

## Code Testing

**Test Location:** `.claude/backend/tests/` (phases 1-7: security, performance, infrastructure, monitoring, auth, badges)

**Python Environment:** Always use `djvenv/bin/python`

**Server:** Always running at http://127.0.0.1:8000/

**Celery Worker:** `djvenv/bin/celery -A django_project worker --loglevel=info`

**Test Coverage:** 140+ tests across 7 phases, all passing
