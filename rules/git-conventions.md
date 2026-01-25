# Git Conventions

## Commit Messages

### Format
```
<type>: <short description>

[optional body with more detail]
```

### Types
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code change that neither fixes a bug nor adds a feature
- `docs:` - Documentation only
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Rules
- Keep subject line under 72 characters
- Use imperative mood ("Add feature" not "Added feature")
- No period at end of subject line
- Do NOT include Claude attribution or co-author tags
- Write as if the developer wrote it themselves

### Examples
```bash
# Good
feat: Add user notification preferences
fix: Resolve race condition in badge calculation
refactor: Extract shared validation logic

# Bad
Added new feature for users
Fix bug.
WIP
```

## Branching

### Branch Naming
- `feature/<name>` - New features
- `bugfix/<name>` - Bug fixes
- `hotfix/<name>` - Production emergency fixes
- `docs/<name>` - Documentation updates

### Workflow
1. Create branch from `main` (or current sprint branch)
2. Make changes with focused commits
3. Open PR for review
4. Squash and merge to main

## Pull Requests

### PR Title
Same format as commit messages: `<type>: <description>`

### PR Body Template
```markdown
## Summary
<1-3 bullet points describing the change>

## Test plan
- [ ] Test item 1
- [ ] Test item 2
```

## Dangerous Operations - NEVER Without Explicit Request

- `git push --force` - Can destroy remote history
- `git reset --hard` - Destroys local changes
- `git clean -f` - Permanently deletes untracked files
- `git branch -D` - Force deletes branch

## Submodule Handling

The `.claude/` directory is a submodule. When making changes:

```bash
# 1. Commit inside the submodule first
git -C .claude add .
git -C .claude commit -m "Your message"
git -C .claude push origin main

# 2. Update the main repo's reference
git add .claude
git commit -m "Update starview-agent submodule"
git push
```

## Pre-Commit Checks

Before committing:
1. Run tests: `djvenv/bin/python -m pytest`
2. Check for debug code: `grep -r "console.log\|print(" --include="*.py" --include="*.js"`
3. Verify no secrets: `git diff --cached | grep -i "password\|secret\|api_key"`
