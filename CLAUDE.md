# Project Instructions for Starview

## Quick Reference

| Resource | Location |
|----------|----------|
| Documentation nav | `.claude/README.md` |
| Backend architecture | `.claude/backend/ARCHITECTURE.md` |
| Frontend architecture | `.claude/frontend/ARCHITECTURE.md` |
| Style guide | `.claude/frontend/STYLE_GUIDE.md` |

## Modular Rules

Path-specific rules are loaded automatically from `.claude/rules/`:
- `backend.md` - Python/Django conventions
- `frontend.md` - React/TypeScript conventions
- `testing.md` - Testing patterns
- `security.md` - Security requirements (always loaded)
- `git-conventions.md` - Commit and PR standards
- `seo.md` - SEO, sitemap, robots.txt, and llms.txt maintenance

## Auto-Documentation System

Hooks track file changes and remind about documentation updates.

- **Session start reminder**: Acknowledge, complete task, offer `/update-docs`
- **Pre-commit reminder**: Ask user if they want to run `/update-docs` first

## Skills

| Skill | When to Use |
|-------|-------------|
| `/create-badge` | Add badges (user-invoked only) |
| `starview-api-endpoint` | Full-stack API endpoint creation |
| `starview-product-lab` | Feature ideation, product validation |
| `frontend-engineer` | Production-grade UI components |
| `seed-observatories` | Seed observatory data from Wikidata |
| `/update-docs` | Sync documentation after changes |

## MCP Servers

| Server | Purpose |
|--------|---------|
| `chrome-devtools` | Browser automation, snapshots, network inspection |

**Chrome DevTools**: Use `take_snapshot()` first, then use `uid` values (not CSS selectors).
**URL**: `http://localhost:5173` (Vite dev server)

## Project Stack

- Django 5.1.13 + DRF + PostgreSQL 17.6 + Redis 7.0
- React + Vite + TanStack Query
- Cloudflare R2 (media) + AWS SES (email)
- django-allauth (auth) + Celery (async tasks)

## Environment

- **Python**: `djvenv/bin/python`
- **Dev servers**: Always running (Django :8000, Vite :5173)
- **Tests**: `djvenv/bin/python -m pytest`

## Submodule

`.claude/` is a git submodule. Commit inside first, then update parent reference.

```bash
git -C .claude add . && git -C .claude commit -m "msg" && git -C .claude push origin main
git add .claude && git commit -m "Update starview-agent submodule"
```
