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
- `docs/RENDER_CRON_SETUP.md` - Production cron jobs (cleanup, archival)
- `docs/badge_system/` - Badge system deep dive
- `docs/email_monitoring/` - AWS SES bounce/complaint tracking

### Frontend (`.claude/frontend/`)
- `ARCHITECTURE.md` - Directory structure, data flow, hooks, services, patterns
- `STYLE_GUIDE.md` - Design system (colors, typography, spacing)
- `docs/API_GUIDE.md` - Frontend API endpoint reference
- `docs/MCP_WORKFLOW.md` - Browser automation for visual development
- `docs/PMTILES_GUIDE.md` - PMTiles + Cloudflare R2 for light pollution tiles
- `references/` - Design inspiration and baseline screenshots

**When to read frontend docs:** Any frontend work, component creation, routing, styling
**Skip frontend docs for:** Backend-only changes, migrations, Django admin

## Skills and Workflows

| Skill | When to Use |
|-------|-------------|
| `starview-badge-creator` | Adding new badges to the badge system |
| `starview-api-endpoint` | Full-stack API: DRF backend + frontend services + React Query |
| `starview-product-lab` | Feature ideation, product validation, competitive analysis, identity refinement |
| `frontend-engineer` | Create distinctive, production-grade frontend interfaces. Use for web components, dashboards, React components, HTML/CSS layouts. Combines design thinking with systematic engineering (typography, color algorithms, cognitive UX laws). |
| `seed-observatories` | Seed observatory locations from Wikidata with AI-validated images. Orchestrated pipeline with sub-agents for image validation via Chrome DevTools MCP. Includes optional description generation step. |

**Auto-invoke triggers:**
- "create a badge", "new badge", "add a badge" → Enter plan mode, then run `/create-badge`
- "brainstorm features", "what should we build", "product direction" → Use `starview-product-lab` skill
- "seed observatories", "add observatories" → Use `seed-observatories` skill

## UX Research (`.claude/skills/starview-product-lab/ux-research/`)

Gemini Deep Research reports for product decisions. **Dynamic discovery** - new files are automatically detected.

| File Pattern | Contains |
|--------------|----------|
| `gemini-output-pain-points-*.md` | User frustrations from Reddit, forums, app reviews |
| `gemini-output-positioning-*.md` | Market sizing, personas, positioning strategies |
| `gemini-output-competitors-*.md` | Competitive landscape analysis |
| `gemini-output-{new-topic}-*.md` | Future research (auto-discovered) |

**How it works:** The `starview-product-lab` skill spawns Haiku subagents to read source files on-demand. No cached summaries - always fresh from source.

**Adding research:** Save new Gemini output as `gemini-output-{topic}-YYYY-MM-DD.md` and it's automatically available.

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

**URL:** Always use `http://localhost:5173` when navigating with Chrome DevTools MCP (Vite dev server).

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

**Dev Servers:** Django (port 8000) and Vite (port 5173) are always running in a separate terminal. Do not start them.

**Celery Worker:** `djvenv/bin/celery -A django_project worker --loglevel=info`

**Test Coverage:** 140+ tests across 7 phases, all passing
