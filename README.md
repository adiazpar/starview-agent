# Starview Agent

**An AI agent configuration specifically built for the Starview project.**

This directory is a Git submodule (`starview-agent`) that provides Claude Code with project-specific knowledge, workflows, and automation hooks to work effectively on the Starview codebase.

---

## Why This Exists

Claude Code is a general-purpose AI coding assistant. Without context, it must rediscover patterns, make assumptions about architecture, and ask repetitive questions each session.

**Starview Agent solves this by providing:**

| Problem | Solution |
|---------|----------|
| Claude doesn't know the codebase | Architecture docs (`backend/`, `frontend/`) |
| Claude forgets between sessions | `CLAUDE.md` with persistent instructions |
| Documentation drifts from code | Auto-tracking hooks that remind about updates |
| Repetitive workflows | Skills and commands for common tasks |
| No visual feedback for UI work | MCP servers for browser automation |

---

## Why It's a Submodule

The agent configuration lives in a separate repository for several reasons:

1. **Clean separation** - Agent config evolves independently from application code
2. **Reusability** - Same agent patterns can be adapted for other projects
3. **Version control** - Track agent improvements separately from feature work
4. **Smaller diffs** - Documentation updates don't clutter the main repo history
5. **Selective updates** - Pin to stable agent versions during critical development

**Repository:** The submodule points to the `starview-agent` repository, which is updated separately and pulled into the main Starview repo as needed.

---

## Directory Structure

```
.claude/
├── CLAUDE.md                    # Main agent instructions (Claude reads this first)
├── README.md                    # This file
├── settings.json                # Hook configurations
├── settings.local.json          # Local overrides (gitignored)
├── .mcp.json                    # MCP server configurations
│
├── backend/
│   ├── ARCHITECTURE.md          # Django models, views, services, APIs
│   ├── docs/                    # Deep-dive documentation
│   │   ├── CELERY_GUIDE.md      # Async task configuration
│   │   ├── STORAGE_CONFIGURATION.md
│   │   ├── RENDER_CRON_SETUP.md
│   │   ├── LOGGING_GUIDE.md
│   │   ├── badge_system/        # Badge system design (4 files)
│   │   └── email_monitoring/    # AWS SES tracking (3 files)
│   └── tests/                   # 140+ test files across 7 phases
│
├── frontend/
│   ├── ARCHITECTURE.md          # React components, hooks, services
│   ├── STYLE_GUIDE.md           # Design system (colors, typography)
│   └── docs/
│       ├── API_GUIDE.md         # Frontend API reference
│       └── MCP_WORKFLOW.md      # Browser automation guide
│
├── hooks/                       # Automation scripts
│   ├── track-changes.sh         # Logs file modifications
│   ├── doc-reminder.sh          # Session-end documentation check
│   ├── session-start-reminder.sh # Reminds about pending updates
│   └── pre-commit-check.sh      # Pre-commit documentation gate
│
├── commands/                    # Slash commands (/command-name)
│   ├── update-docs.md           # Spawns Opus 4.5 to update docs
│   └── create-badge.md          # Guided badge creation workflow
│
└── skills/                      # Complex workflow guides
    ├── starview-api-endpoint/   # Full-stack API development
    └── starview-badge-creator/  # Badge system integration
```

---

## Available Tools

### MCP Servers (Browser Automation)

Three MCP servers are configured for visual frontend development:

| Server | Purpose | Key Capabilities |
|--------|---------|------------------|
| **chrome-devtools** | Primary browser automation | Screenshots, snapshots, console logs, network requests, performance analysis |
| **puppeteer** | Alternative browser (incognito) | Navigation, screenshots, form filling, clicking |
| **figma** | Design-to-code workflow | Extract design context, screenshots, Code Connect |

**Usage example:**
```
# Take a snapshot to get element UIDs
mcp__chrome-devtools__take_snapshot()

# Navigate and screenshot
mcp__chrome-devtools__new_page(url="http://localhost:5173")
mcp__chrome-devtools__take_screenshot()

# Check for errors
mcp__chrome-devtools__list_console_messages()
```

### Hooks (Automatic Behaviors)

Hooks run automatically at specific events:

| Hook | Trigger | Purpose |
|------|---------|---------|
| `track-changes.sh` | After Write/Edit | Logs modified files for doc tracking |
| `session-start-reminder.sh` | Session start | Reminds about pending doc updates |
| `doc-reminder.sh` | Session end | Shows summary of undocumented changes |
| `pre-commit-check.sh` | Before git commit | Gates commits if docs need updating |

### Slash Commands

Type these in Claude Code to trigger workflows:

| Command | Description |
|---------|-------------|
| `/update-docs` | Spawns Opus 4.5 subagent to update architecture docs |
| `/create-badge` | Guided workflow for adding new badges |

### Skills

Complex workflows invoked via the Skill tool:

| Skill | When to Use |
|-------|-------------|
| `starview-api-endpoint` | Building new API endpoints (backend + frontend) |
| `starview-badge-creator` | Adding badges to the achievement system |

---

## How the Agent Works

### Session Flow

```
┌─────────────────┐
│  Session Start  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  session-start-reminder.sh runs         │
│  Shows any pending doc updates          │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Claude reads CLAUDE.md                 │
│  Understands project context            │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  User gives task                        │
│  Claude uses architecture docs          │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Claude edits files                     │
│  track-changes.sh logs each edit        │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  After 5 files: gentle nudge            │
│  "Run /update-docs when done"           │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Session End                            │
│  doc-reminder.sh shows summary          │
└─────────────────────────────────────────┘
```

### Documentation Sync

The agent maintains documentation parity through:

1. **Tracking** - Every backend/frontend file edit is logged
2. **Reminders** - Gentle nudges at milestones (5 files) and session boundaries
3. **Subagent** - `/update-docs` spawns an Opus 4.5 agent to analyze changes and update docs
4. **Gating** - Pre-commit hook can block commits if docs are stale

---

## Getting Started

### For Claude Code Users

1. Clone the Starview repo (submodule auto-initializes)
2. Open the project in Claude Code
3. Claude automatically reads `.claude/CLAUDE.md`
4. Ask questions or assign tasks - Claude knows the architecture

### For Maintainers

**Update the agent:**
```bash
cd .claude
git pull origin main
cd ..
git add .claude
git commit -m "Update starview-agent submodule"
```

**Test hooks locally:**
```bash
# Simulate session start
.claude/hooks/session-start-reminder.sh

# Check changes log
cat .claude/hooks/.session-changes.log
```

---

## Project Context

**Starview** is a Django web application for stargazing location reviews:

| Layer | Technology |
|-------|------------|
| Backend | Django 5.1 + Django REST Framework |
| Database | PostgreSQL 17.6 + Redis 7.0 |
| Frontend | React + Vite + TanStack Query |
| Storage | Cloudflare R2 (media.starview.app) |
| Email | AWS SES (noreply@starview.app) |
| Tasks | Celery (optional async) |
| Auth | django-allauth (email + Google OAuth) |

**Production:** https://starview.app
**Status:** 98% complete | Security: A+ grade

---

## Quick Reference

| Task | What to Read/Use |
|------|------------------|
| Backend work | `backend/ARCHITECTURE.md` |
| Frontend work | `frontend/ARCHITECTURE.md` |
| Styling | `frontend/STYLE_GUIDE.md` |
| Visual debugging | `frontend/docs/MCP_WORKFLOW.md` |
| Add API endpoint | Skill: `starview-api-endpoint` |
| Add badge | Command: `/create-badge` |
| Update docs | Command: `/update-docs` |
| Run tests | `djvenv/bin/python .claude/backend/tests/<test>.py` |
