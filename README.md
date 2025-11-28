# .claude Documentation

**Project:** Starview - Stargazing Location Reviews
**Production:** https://starview.app
**Status:** 98% Complete

---

## For AI Agents: Start Here

1. **Backend work?** → Read `backend/ARCHITECTURE.md` (390 lines, covers everything)
2. **Frontend work?** → Read `frontend/ARCHITECTURE.md` + `frontend/docs/MCP_WORKFLOW.md`
3. **Need specifics?** → Check `backend/docs/` or `frontend/docs/` for deep dives

**MCP Servers Available:**
- **chrome-devtools** - Browser automation, debugging, performance analysis
- **puppeteer** - Alternative browser automation (incognito mode)
- **figma** - Design-to-code workflow (REMOTE, OAuth authenticated)

**Figma Setup:** Type `/mcp` → Select `figma` → Authenticate via browser

See `frontend/docs/MCP_WORKFLOW.md` for detailed usage.

**Frontend Status:** Audit complete - see `frontend/docs/AUDIT_REPORT.md` for refactoring plan.

---

## Directory Structure

```
.claude/
├── README.md                     # This file
├── documentation-style.md        # Code documentation standards
│
├── backend/
│   ├── ARCHITECTURE.md          # Primary backend reference (390 lines)
│   ├── docs/
│   │   ├── CELERY_GUIDE.md      # Async tasks (FREE vs PAID tier)
│   │   ├── STORAGE_CONFIGURATION.md  # Cloudflare R2 setup
│   │   ├── RENDER_CRON_SETUP.md # Production cronjobs
│   │   ├── LOGGING_GUIDE.md     # Python logging best practices
│   │   ├── EMAIL_SECURITY_SUMMARY.md  # OAuth/registration security
│   │   ├── badge_system/        # Badge system deep dive (4 files)
│   │   └── email_monitoring/    # AWS SES bounce tracking (3 files)
│   └── tests/                   # 140+ tests across 7 phases
│
├── frontend/
│   ├── ARCHITECTURE.md          # Frontend architecture guide (PRIMARY)
│   ├── STYLE_GUIDE.md           # Design system (Linear-inspired)
│   └── docs/
│       ├── API_GUIDE.md         # API reference for frontend
│       ├── MCP_WORKFLOW.md      # MCP servers (chrome-devtools, puppeteer, figma)
│       └── AUDIT_REPORT.md      # Comprehensive audit + refactoring plan
│
└── skills/
    └── frontend-dev/            # Frontend development skill (pending)
```

---

## Quick Reference

| Task | Read This |
|------|-----------|
| Any backend work | `backend/ARCHITECTURE.md` |
| **Frontend architecture** | `frontend/ARCHITECTURE.md` |
| **Frontend visual dev** | `frontend/docs/MCP_WORKFLOW.md` |
| **Design system** | `frontend/STYLE_GUIDE.md` |
| Frontend refactoring | `frontend/docs/AUDIT_REPORT.md` |
| Frontend API integration | `frontend/docs/API_GUIDE.md` |
| Async tasks/Celery | `backend/docs/CELERY_GUIDE.md` |
| Media storage | `backend/docs/STORAGE_CONFIGURATION.md` |
| Cronjobs | `backend/docs/RENDER_CRON_SETUP.md` |
| Badge system | `backend/docs/badge_system/` |
| Email bounce tracking | `backend/docs/email_monitoring/` |

---

## Production Infrastructure

**Render.com (~$24/month):**
- Web Service: Django/Gunicorn ($7)
- PostgreSQL 17.6 with daily backups ($7)
- Redis 7.0 for caching/sessions ($7)
- 3 Cronjobs ($3)
- Cloudflare R2 media storage (~$0.15)

**Security:** A+ grade on securityheaders.com

---

## Running Tests

```bash
# All tests use Django venv
djvenv/bin/python .claude/backend/tests/phase1/test_rate_limiting.py
djvenv/bin/python .claude/backend/tests/phase4/test_celery_tasks.py
djvenv/bin/python .claude/backend/tests/phase5/test_health_check.py
```

**Test Coverage:** 140+ tests across security, performance, infrastructure, and monitoring.
