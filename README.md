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

## Using as a Template

This `.claude` directory is designed to be **reusable as a template** for other projects.

### Quick Start for New Projects

1. Copy this directory to your new project
2. Remove project-specific content:
   - Delete `backend/` and `frontend/` docs (create your own)
   - Clear `skills/starview-*` (keep generic skills)
   - Update `CLAUDE.md` with your project context
3. Keep the foundation:
   - `settings.json` - Environment optimizations and hooks
   - `rules/` - Modular rules (adapt paths for your project)
   - `hooks/` - Documentation automation
   - Generic skills (`code-reviewer`, `frontend-engineer`)

### Template Features

| Feature | Location | Purpose |
|---------|----------|---------|
| **Settings Optimization** | `settings.json` | Tool search, thinking tokens, permissions |
| **Modular Rules** | `rules/` | Path-specific instructions |
| **Documentation Hooks** | `hooks/` | Auto-tracking and reminders |
| **Skill Framework** | `skills/` | Reusable workflow templates |
| **MCP Configuration** | `.mcp.json` | Browser automation |

---

## Directory Structure

```
.claude/
├── CLAUDE.md                    # Main agent instructions (Claude reads first)
├── CLAUDE.local.md.example      # Template for personal preferences
├── README.md                    # This file
├── settings.json                # Team settings (hooks, env, permissions)
├── settings.local.json          # Personal overrides (gitignored)
├── .mcp.json                    # MCP server configurations
│
├── rules/                       # Modular, path-specific rules
│   ├── backend.md               # Python/Django conventions
│   ├── frontend.md              # React/TypeScript conventions
│   ├── testing.md               # Testing patterns
│   ├── security.md              # Security requirements
│   └── git-conventions.md       # Commit/PR standards
│
├── hooks/                       # Automation scripts
│   ├── track-changes.sh         # Logs file modifications
│   ├── track-deletions.sh       # Logs file deletions
│   ├── doc-reminder.sh          # Session-end doc check
│   ├── session-start-reminder.sh # Pending update reminders
│   ├── pre-commit-check.sh      # Pre-commit documentation gate
│   └── subagent-monitor.sh      # Track subagent usage
│
├── skills/                      # Complex workflow guides
│   ├── code-reviewer/           # Parallel code review (generic)
│   ├── frontend-engineer/       # Design engineering (generic)
│   ├── update-docs/             # Documentation sync
│   ├── starview-api-endpoint/   # Full-stack API development
│   ├── starview-badge-creator/  # Badge system integration
│   ├── starview-product-lab/    # Product validation
│   └── seed-observatories/      # Wikidata observatory seeding
│
├── backend/                     # Backend architecture docs
│   ├── ARCHITECTURE.md          # Models, views, services, APIs
│   ├── tests/                   # Test files (140+ tests)
│   └── docs/                    # Deep-dive documentation
│
├── frontend/                    # Frontend architecture docs
│   ├── ARCHITECTURE.md          # Components, hooks, services
│   ├── STYLE_GUIDE.md           # Design system
│   └── docs/                    # Frontend-specific guides
│
└── plans/                       # Implementation plans
```

---

## Settings Configuration

### Environment Optimizations (`settings.json`)

```json
{
  "env": {
    "ENABLE_TOOL_SEARCH": "auto:5",
    "MAX_THINKING_TOKENS": "31999",
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "70"
  }
}
```

| Setting | Purpose |
|---------|---------|
| `ENABLE_TOOL_SEARCH` | Dynamic MCP tool loading (5% threshold) |
| `MAX_THINKING_TOKENS` | Extended thinking for complex planning |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Trigger compaction at 70% context |

### Permission Denylists

The settings include deny rules to prevent accidental destructive operations:

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)",
      "Read(.env)",
      "Read(**/secrets/**)"
    ]
  }
}
```

### Personal Preferences

Copy `CLAUDE.local.md.example` to `CLAUDE.local.md` for personal preferences:
- Local URLs and test data
- Personal shortcuts and aliases
- Notes and reminders

This file is auto-gitignored.

---

## Modular Rules System

Rules in `rules/` are loaded based on file paths being worked on:

```yaml
# Example: rules/backend.md
---
paths:
  - "**/starview_app/**/*.py"
  - "**/django_project/**/*.py"
---

# Backend Rules
- Use djvenv/bin/python for Python commands
- Follow DOCUMENTATION_STYLE.md for comments
```

| Rule File | Applied To | Contains |
|-----------|------------|----------|
| `backend.md` | `*.py` files | Django/Python conventions |
| `frontend.md` | `*.js, *.jsx, *.tsx` | React/TypeScript patterns |
| `testing.md` | `**/tests/**` | Testing conventions |
| `security.md` | All files | Security requirements |
| `git-conventions.md` | All files | Commit/PR standards |

---

## Hooks System

Hooks run automatically at specific events:

| Hook | Event | Purpose |
|------|-------|---------|
| `track-changes.sh` | PostToolUse (Write/Edit) | Log modified files |
| `track-deletions.sh` | PreToolUse (Bash) | Log deletions |
| `session-start-reminder.sh` | SessionStart | Show pending updates |
| `doc-reminder.sh` | Stop | Show undocumented changes |
| `pre-commit-check.sh` | PreToolUse (Bash) | Gate commits |
| `subagent-monitor.sh` | SubagentStop | Track subagent usage |

### Hook Flow

```
Session Start → Check pending docs → User works → Track changes →
Session End → Remind about updates → Next session picks up
```

---

## Skills

### Generic Skills (Reusable)

| Skill | Purpose | Frontmatter |
|-------|---------|-------------|
| `code-reviewer` | Parallel code review | `context: fork`, `model: sonnet` |
| `frontend-engineer` | Design engineering with references | `model: opus` |
| `update-docs` | Sync documentation | `context: fork`, `model: opus` |

### Project-Specific Skills

| Skill | Purpose |
|-------|---------|
| `starview-api-endpoint` | Full-stack API development |
| `starview-badge-creator` | Badge system integration |
| `starview-product-lab` | Product validation with UX research |
| `seed-observatories` | Wikidata observatory seeding |

### Skill Frontmatter Reference

```yaml
---
name: skill-name
description: Clear description for Claude to know when to use
user-invocable: true              # Can invoke with /skill-name
disable-model-invocation: false   # Claude can auto-invoke
allowed-tools: Read, Grep, Glob   # Restrict tool access
context: fork                     # Run in isolated context
model: sonnet                     # Override model (sonnet/opus/haiku)
---
```

---

## MCP Servers

### Configured Servers

| Server | Purpose | Key Tools |
|--------|---------|-----------|
| `chrome-devtools` | Browser automation | `take_snapshot`, `take_screenshot`, `click`, `fill` |

### Chrome DevTools Usage

```bash
# Always take snapshot first to get UIDs
mcp__chrome-devtools__take_snapshot()

# Navigate
mcp__chrome-devtools__new_page(url="http://localhost:5173")

# Interact using UIDs (not CSS selectors)
mcp__chrome-devtools__click(uid="element-uid")
```

---

## Session Flow

```
┌─────────────────┐
│  Session Start  │
└────────┬────────┘
         ↓
┌─────────────────────────────────────────┐
│  session-start-reminder.sh              │
│  Shows pending doc updates              │
└────────┬────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Claude reads CLAUDE.md + rules/        │
│  Loads path-specific rules              │
└────────┬────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  User gives task                        │
│  Claude uses architecture docs          │
└────────┬────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Claude edits files                     │
│  track-changes.sh logs each edit        │
│  subagent-monitor.sh tracks subagents   │
└────────┬────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Session End                            │
│  doc-reminder.sh shows summary          │
└─────────────────────────────────────────┘
```

---

## Plugin Configuration

### LSP (Language Server Protocol)

For optimal performance, enable LSP plugins for your languages:

```bash
/plugins
```

Benefits:
- 900x faster code navigation
- 90%+ fewer file reads
- Automatic type error detection

---

## Quick Reference

| Task | What to Use |
|------|-------------|
| Backend work | `backend/ARCHITECTURE.md` + `rules/backend.md` |
| Frontend work | `frontend/ARCHITECTURE.md` + `rules/frontend.md` |
| Styling | `frontend/STYLE_GUIDE.md` |
| Visual debugging | `frontend/docs/MCP_WORKFLOW.md` |
| Add API endpoint | Skill: `starview-api-endpoint` |
| Build UI components | Skill: `frontend-engineer` |
| Review code | Skill: `code-reviewer` |
| Update docs | Skill: `/update-docs` |
| Run tests | `djvenv/bin/python -m pytest` |

---

## Project Context (Starview-Specific)

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

---

## Maintenance

### Update the Agent

```bash
cd .claude
git pull origin main
cd ..
git add .claude
git commit -m "Update starview-agent submodule"
```

### Test Hooks

```bash
# Simulate session start
.claude/hooks/session-start-reminder.sh

# Check changes log
cat .claude/hooks/.session-changes.log
```

### Clear Documentation Reminders

```bash
rm -f .claude/hooks/.session-changes.log
```
