---
paths:
  - "**/tests/**"
  - "**/*test*.py"
  - "**/*.test.js"
  - "**/*.test.jsx"
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "**/*.spec.*"
---

# Testing Conventions

## General Principles

- Write tests that document behavior, not implementation
- Test edge cases and error conditions
- Keep tests focused - one concept per test
- Use descriptive test names: `test_<action>_<condition>_<expected_result>`

## Python/Django Testing

### Test Runner
```bash
# Run all tests
djvenv/bin/python -m pytest

# Run specific test file
djvenv/bin/python -m pytest path/to/test_file.py

# Run specific test
djvenv/bin/python -m pytest path/to/test_file.py::test_name

# Run with verbose output
djvenv/bin/python -m pytest -v

# Run with coverage
djvenv/bin/python -m pytest --cov=starview_app
```

### Test Organization
- Tests live in `.claude/backend/tests/` organized by phase
- Use `@pytest.fixture` for shared setup
- Use `@pytest.mark.django_db` for database tests

### Mocking
- Mock external services (email, storage, APIs)
- Use `unittest.mock.patch` or `pytest-mock`
- Don't mock the thing you're testing

## JavaScript/React Testing

### Test Runner
```bash
# Run all tests
npm test

# Run with watch mode
npm test -- --watch

# Run specific file
npm test -- path/to/file.test.js
```

### React Component Testing
- Use React Testing Library
- Test user behavior, not implementation
- Query by role, label, or text (not test IDs)

## When to Write Tests

- New features: Write tests alongside implementation
- Bug fixes: Write test that reproduces bug first
- Refactoring: Ensure existing tests pass throughout

## When NOT to Write Tests

- Trivial getters/setters
- Framework code (Django admin, migrations)
- One-off scripts
