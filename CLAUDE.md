# Project Instructions for Starview

## Auto-Documentation System

This project has an automated documentation system using Claude Code hooks. **You don't need to remember to update docs** - the system will remind you.

### How It Works

| Event | What Happens |
|-------|--------------|
| **You edit/create files** | `track-changes.sh` logs the change automatically |
| **You delete files** | `track-deletions.sh` logs the deletion automatically |
| **5 files modified** | Single gentle nudge to run `/update-docs` when task is complete |
| **You run `git commit`** | `pre-commit-check.sh` reminds you if docs need updating |
| **Session ends** | `doc-reminder.sh` shows pending documentation updates |
| **Session starts** | `session-start-reminder.sh` reminds about previous session's changes |

### When You See a Session-Start Reminder

**CRITICAL:** When a `<system-reminder>` contains "PENDING DOCUMENTATION UPDATE", you MUST include the documentation offer in your response. Do NOT forget this step.

**Required Response Structure:**

| Part | What to Include |
|------|-----------------|
| **Opening** | Acknowledge pending updates (one sentence) |
| **Body** | Answer the user's question / perform their task |
| **Closing** | Ask: "Would you like me to run `/update-docs` to sync the documentation?" |

**Before submitting your response, verify:**
- [ ] Opening mentions pending doc updates
- [ ] Body addresses the user's actual request
- [ ] Closing offers to run `/update-docs`

**Example:**
> I notice there are pending documentation updates from a previous session (global styles, component CSS).
>
> [Your full response to their question here...]
>
> Would you like me to run `/update-docs` to sync the documentation?

**What `/update-docs` does:**
1. Spawns an **Opus 4.5 subagent** to analyze changes
2. Updates relevant ARCHITECTURE.md files
3. Clears the reminder log
4. Reports what was updated

### Files Tracked

| File Pattern | Category | Documentation |
|--------------|----------|---------------|
| `starview_app/**/*.py` | `backend` | `.claude/backend/ARCHITECTURE.md` |
| `django_project/**/*.py` | `backend` | `.claude/backend/ARCHITECTURE.md` |
| `migrations/**/*.py` | `backend` | `.claude/backend/ARCHITECTURE.md` |
| `starview_frontend/src/**/*.jsx/tsx/js/ts` | `frontend` | `.claude/frontend/ARCHITECTURE.md` |
| `starview_frontend/src/styles/*.css` | `style` | `.claude/frontend/STYLE_GUIDE.md` |
| `starview_frontend/src/(components\|pages)/**/*.css` | `frontend-css` | Check `STYLE_GUIDE.md` if patterns change |

### Hook Configuration

Hooks are defined in `.claude/settings.json` and scripts in `.claude/hooks/`:
- `track-changes.sh` - Logs file edits and creations (PostToolUse: Write|Edit)
- `track-deletions.sh` - Logs file deletions (PreToolUse: Bash rm commands)
- `pre-commit-check.sh` - Pre-commit documentation check
- `session-start-reminder.sh` - Reminds at session start
- `doc-reminder.sh` - Reminds at session end

**Note:** Changes to `.claude/settings.json` require restarting Claude Code to take effect.

## Documentation Navigation

**START HERE:** `.claude/README.md` - Documentation navigation guide

## Backend Architecture Reference

**IMPORTANT:** Before working on any backend-related tasks, always consult `.claude/backend/ARCHITECTURE.md` for:
- Database models (20+ models)
- API endpoints and routing
- Service layer pattern
- Signal handlers
- Security features
- Performance optimizations

**Specialized docs** (in `.claude/backend/docs/`):
- `CELERY_GUIDE.md` - Async tasks (FREE vs PAID tier)
- `STORAGE_CONFIGURATION.md` - Cloudflare R2 media storage
- `RENDER_CRON_SETUP.md` - Production cronjobs
- `LOGGING_GUIDE.md` - Python logging best practices
- `badge_system/` - Badge system deep dive
- `email_monitoring/` - AWS SES bounce/complaint tracking

## Frontend Architecture Reference

**When to read frontend docs:**

| Task | Read This |
|------|-----------|
| Any frontend work | `ARCHITECTURE.md` (always start here) |
| Creating/modifying components | `ARCHITECTURE.md` → Component Pattern section |
| Adding new routes | `ARCHITECTURE.md` → Routes section |
| API calls from frontend | `API_GUIDE.md` |
| Styling, colors, design tokens | `STYLE_GUIDE.md` |
| Visual debugging, screenshots | `MCP_WORKFLOW.md` |

**Do NOT read frontend docs for:**
- Backend-only changes (models, views, serializers)
- Database migrations
- Django admin changes

**Documentation** (in `.claude/frontend/`):
- `ARCHITECTURE.md` - Directory structure, data flow, hooks, services, patterns
- `STYLE_GUIDE.md` - Design system (colors, typography, spacing, components)
- `docs/API_GUIDE.md` - Frontend API endpoint reference
- `docs/MCP_WORKFLOW.md` - Browser automation for visual development

**Reference Images:** `.claude/frontend/references/` - Design inspiration and baseline screenshots

**Skills** (use `/skill` command):
| Skill | When to Use |
|-------|-------------|
| `example-skills:frontend-design` | Building new components/pages from scratch, creating polished UI |
| `example-skills:skill-creator` | Creating or updating custom skills |
| `starview-badge-creator` | Adding new badges to the badge system (local skill in `.claude/skills/`) |
| `starview-api-endpoint` | Full-stack API development: DRF backend + frontend services + React Query hooks |

**Auto-invoke workflows:** When the user mentions any of these, automatically start the corresponding workflow:
- "create a badge", "new badge", "add a badge" → Enter plan mode, then run `/create-badge` command

## Building New Features

When building features that involve data flow between backend and frontend:
1. **Explore first** - Read relevant architecture docs to understand existing patterns
2. **Check for existing endpoints** - The backend may already have what you need
3. **Use the `starview-api-endpoint` skill** when you determine a new API endpoint is needed - it handles the full workflow from Django serializer to React Query hook

## MCP Servers for Frontend Development

**IMPORTANT:** Two MCP servers are configured for visual frontend development. See `.claude/frontend/docs/MCP_WORKFLOW.md` for detailed usage.

### Available MCP Servers

| Server | Purpose | Key Tools |
|--------|---------|-----------|
| **puppeteer** | Browser automation, screenshots, form testing | `puppeteer_navigate`, `puppeteer_screenshot`, `puppeteer_click`, `puppeteer_fill` |
| **chrome-devtools** | Console logs, network requests, performance analysis | `list_console_messages`, `list_network_requests`, `performance_analyze_insight`, `take_screenshot` |

### Frontend Development Workflow

**Before making UI changes:**
1. Navigate to `http://localhost:5173` using chrome-devtools or puppeteer
2. Take a screenshot to see current state
3. Check console for errors with `list_console_messages`

**After making UI changes:**
1. Take a new screenshot to verify changes
2. Check console for new errors
3. Test interactions (click, fill forms) if applicable

**For debugging:**
- Use `list_network_requests` to debug API calls to Django backend (http://127.0.0.1:8000)
- Use `evaluate_script` to run JavaScript in the browser
- Use `performance_analyze_insight` for performance issues

### Quick Reference

```
# Navigate to app
mcp__chrome-devtools__new_page(url="http://localhost:5173")

# Take snapshot to get element uid values
mcp__chrome-devtools__take_snapshot()

# Take screenshot
mcp__chrome-devtools__take_screenshot()

# Check console errors
mcp__chrome-devtools__list_console_messages()

# Check network requests
mcp__chrome-devtools__list_network_requests(resourceTypes=["fetch", "xhr"])

# Click element (use uid from snapshot)
mcp__chrome-devtools__click(uid="123")

# Fill form field (use uid from snapshot)
mcp__chrome-devtools__fill(uid="456", value="test@example.com")
```

**IMPORTANT:** Chrome DevTools MCP uses `uid` values from the accessibility tree, NOT CSS selectors. Always call `take_snapshot()` first to get element `uid` values.


## Environment Configuration

**CRITICAL:** Always read and validate the `.env` file when working on:
- Security configurations
- API integrations (Mapbox, AWS SES)
- Deployment settings
- Database connections

**Key Environment Variables:**

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DEBUG` | Debug mode (False in production) |
| `ALLOWED_HOSTS` | Allowed hostnames |
| `CORS_ALLOWED_ORIGINS` | Frontend dev servers |
| `MAPBOX_TOKEN` | Mapbox API key |
| `VITE_MAPBOX_TOKEN` | Frontend Mapbox API key |
| `AWS_ACCESS_KEY_ID` | R2 storage credentials |
| `AWS_SECRET_ACCESS_KEY` | R2 storage credentials |
| `USE_R2_STORAGE` | False=local, True=R2 |
| `AWS_SES_ACCESS_KEY_ID` | Email credentials |
| `AWS_SES_SECRET_ACCESS_KEY` | Email credentials |
| `DEFAULT_FROM_EMAIL` | noreply@starview.app |
| `CELERY_ENABLED` | Async tasks (False=FREE tier) |
| `REDIS_URL` | Redis connection |
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth |

## Documentation Standards

**Python code comments** in `starview_app/` must follow `.claude/backend/docs/DOCUMENTATION_STYLE.md`:
- Header comments focus on **WHY** and **WHAT**, not **HOW**
- Keep headers high-level (10-20 lines maximum)
- Boxed comments for complex functions
- One-liners for configuration classes

**Keeping docs in sync:** After completing complex changes or new features, run `/update-docs` to update architecture documentation. This analyzes git diff and updates relevant docs in `.claude/`.

## Project Context

Django web application for stargazing location reviews:
- Django 5.1.13 + Django REST Framework
- PostgreSQL 17.6 + Redis 7.0
- Cloudflare R2 (media.starview.app)
- AWS SES (noreply@starview.app)
- Celery (optional async tasks)
- django-allauth (email verification + Google OAuth)

## Code Quality

- Follow Django best practices
- Use Django's built-in utilities over custom implementations
- Maintain separation of concerns (models, views, services, signals)
- Keep code DRY

## Git Commits

**When the user asks to commit and push changes:**
- Do NOT include Claude attribution in commit messages
- Do NOT add "Co-Authored-By: Claude" or similar
- Do NOT add the robot emoji or "Generated with Claude Code" footer
- Write clean, conventional commit messages as if the user wrote them

## Submodule: .claude Directory

**IMPORTANT:** The `.claude/` directory is a Git submodule (`starview-agent`), not part of the main repository.

**When committing changes to files inside `.claude/`:**

1. **Commit inside the submodule first:**
   ```bash
   git -C .claude add .
   git -C .claude commit -m "Your commit message"
   git -C .claude push origin main
   ```

2. **Then update the main repo's submodule reference:**
   ```bash
   git add .claude
   git commit -m "Update starview-agent submodule"
   git push
   ```

**Why this matters:**
- Changes to `.claude/` files are tracked in the `starview-agent` repo
- The main repo only tracks which commit of the submodule to use
- Forgetting step 1 means your changes exist only locally
- Forgetting step 2 means others won't see your submodule updates

## Backend Status

**Status:** 98% Complete | **Production:** https://starview.app | **Security:** A+

**Remaining Work:**
- Database index optimization (~2-3 hours)
- Sentry integration (optional)

## Code Testing

**Test Location:** `.claude/backend/tests/`
- `phase1/` - Security (rate limiting, XSS, file upload)
- `phase2/` - Performance (N+1, caching)
- `phase4/` - Infrastructure (lockout, audit, Celery)
- `phase5/` - Monitoring (health check)
- `phase6/` - Authentication (password reset)
- `phase7/` - Badge fixes

**Python Environment:**
- **ALWAYS use:** `djvenv/bin/python`
- Example: `djvenv/bin/python .claude/backend/tests/phase1/test_rate_limiting.py`

**Server:** Always running at http://127.0.0.1:8000/

**Celery Worker (for async tasks):**
```bash
djvenv/bin/celery -A django_project worker --loglevel=info
```

**Test Coverage:** 140+ tests across 7 phases, all passing
