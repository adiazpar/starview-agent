---
paths:
  - "**/starview_app/**/*.py"
  - "**/django_project/**/*.py"
  - "manage.py"
---

# Backend Development Rules

## Python Environment

- Always use `djvenv/bin/python` for Python commands
- Run Django management: `djvenv/bin/python manage.py <command>`
- Celery worker: `djvenv/bin/celery -A django_project worker --loglevel=info`

## Django Patterns

### Models
- Add indexes for frequently queried fields
- Use `select_related()` and `prefetch_related()` to prevent N+1 queries
- Define `Meta.ordering` for consistent results

### Views/ViewSets
- Use appropriate throttle classes from `throttling.py`
- Choose minimal serializer for lists, detailed for single items
- Filter querysets by user when applicable

### Serializers
- Create separate List and Detail serializers when needed
- Use `read_only_fields` for computed/auto fields

### Migrations
- Run `makemigrations` then `migrate` after model changes
- Never edit migration files manually

## Code Comments

Follow `.claude/backend/docs/DOCUMENTATION_STYLE.md`:
- Header comments focus on **WHY** and **WHAT**, not **HOW**
- Keep headers 10-20 lines maximum
- Avoid obvious comments

## Testing

- Test files: `.claude/backend/tests/`
- Run tests: `djvenv/bin/python -m pytest <path>`
- Don't modify production code to make tests pass without understanding why
