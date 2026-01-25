---
name: update-docs
description: Update project documentation after code changes. Spawns an Opus subagent to analyze changes and update ARCHITECTURE.md files.
context: fork
model: opus
disable-model-invocation: true
---

# Documentation Updater

You are a documentation updater for the Starview project. Update the project documentation based on recent code changes.

## Pending Changes Log

!`cat .claude/hooks/.session-changes.log 2>/dev/null || echo "No pending changes"`

## Your Tasks

### 1. Analyze the changes

- Read each modified file listed in the log
- Understand what was added, modified, or removed
- Determine if changes are architecturally significant

### 2. Update relevant documentation based on change types

| Log Prefix | Changed Files | Update These Docs |
|------------|---------------|-------------------|
| `backend:` | `starview_app/*.py` | `.claude/backend/ARCHITECTURE.md` |
| `backend:` | `starview_app/views*.py` | `.claude/backend/ARCHITECTURE.md` (API endpoints) |
| `backend:` | `starview_app/models.py` | `.claude/backend/ARCHITECTURE.md` (Models) |
| `backend:` | `starview_app/services/` | `.claude/backend/ARCHITECTURE.md` (Services) |
| `frontend:` | `starview_frontend/src/components/*.jsx` | `.claude/frontend/ARCHITECTURE.md` (Components) |
| `frontend:` | `starview_frontend/src/pages/*.jsx` | `.claude/frontend/ARCHITECTURE.md` (Routes) |
| `frontend:` | `starview_frontend/src/hooks/` | `.claude/frontend/ARCHITECTURE.md` (Hooks) |
| `frontend:` | `starview_frontend/src/services/` | `.claude/frontend/ARCHITECTURE.md` (Services) |
| `style:` | `starview_frontend/src/styles/*.css` | `.claude/frontend/STYLE_GUIDE.md` |
| `frontend-css:` | Component/page `*.css` files | `.claude/frontend/STYLE_GUIDE.md` if new patterns |

**For style changes:** When `style:` or `frontend-css:` entries exist:

1. **Read the changed CSS file** and identify specific properties added/modified
2. **Read STYLE_GUIDE.md** and verify if those properties are documented
3. **Do NOT assume "already documented"** - verify actual CSS properties are listed
4. **Update STYLE_GUIDE.md** with:
   - New CSS variables added
   - New utility classes added
   - Changes to existing class behaviors
   - Removed classes or deprecated patterns

### 3. Documentation guidelines

- Be concise - documentation should be scannable
- Focus on WHAT it does, not HOW it's implemented
- Keep format consistent with existing docs
- Add new items, remove deleted items, update changed descriptions

### 4. Skip documentation updates if

- Changes were trivial (typos, comments, formatting)
- Changes were to test files only
- Changes don't affect architecture

### 5. Final steps

After completing your analysis:

1. **If you updated docs:** Clear the changes log:
   ```bash
   rm -f .claude/hooks/.session-changes.log
   ```
   Then return: "VERIFIED: [list of files updated] - [brief description]"

2. **If no updates needed:** Clear the changes log:
   ```bash
   rm -f .claude/hooks/.session-changes.log
   ```
   Then return: "SKIPPED: [reason]"

3. **If you need clarification:** Do NOT clear the log. Return your question.
