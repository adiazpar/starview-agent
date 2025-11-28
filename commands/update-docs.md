---
description: Update project documentation after code changes
---

# Documentation Update Command

This command spawns an Opus 4.5 subagent to update project documentation, keeping your main conversation context clean.

## Instructions

1. **Read the pending changes log first:**
   ```bash
   cat .claude/hooks/.session-changes.log 2>/dev/null || echo "No pending changes"
   ```

2. **Spawn an Opus 4.5 subagent** using the Task tool with these parameters:
   - `subagent_type`: "general-purpose"
   - `model`: "opus"
   - `description`: "Update project documentation"
   - `prompt`: Use the prompt template below, inserting the pending changes

3. **After the subagent returns**, check if it successfully updated docs:
   - If YES: Clear the log with `rm -f .claude/hooks/.session-changes.log`
   - If NO (subagent asked for clarification): Do NOT clear the log, relay the question to the user

---

## Subagent Prompt Template

```
You are a documentation updater for the Starview project. Update the project documentation based on recent code changes.

## Pending Changes Log
[INSERT CONTENTS OF .session-changes.log HERE]

## Your Tasks

1. **Analyze the changes:**
   - Read each modified file listed in the log
   - Understand what was added, modified, or removed
   - Determine if changes are architecturally significant

2. **Update relevant documentation based on change types:**

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
   | `style:` | `starview_frontend/src/styles/*.css` | `.claude/frontend/STYLE_GUIDE.md` (Design tokens, utility classes) |
   | `frontend-css:` | Component/page `*.css` files | `.claude/frontend/STYLE_GUIDE.md` if new patterns introduced |

   **IMPORTANT for style changes:** When `style:` or `frontend-css:` entries exist:

   a. **Read the changed CSS file** and identify the specific properties that were added/modified

   b. **Read STYLE_GUIDE.md** and verify if those specific properties are documented

   c. **Do NOT assume "already documented"** just because a class name is mentioned. Verify the actual CSS properties are listed. For example:
      - If `.auth-page__card` gained `animation: fadeInUp` and `text-align: center`, check that STYLE_GUIDE.md documents these specific behaviors
      - If a utility class changed from `padding: 12px` to `padding: var(--space-md)`, that's a pattern fix worth noting

   d. **Update STYLE_GUIDE.md** with:
      - New CSS variables added
      - New utility classes added
      - Changes to existing class behaviors (new properties, changed values)
      - Removed classes or deprecated patterns
      - Any class that now has animation, centering, or other behavioral changes

3. **Documentation guidelines:**
   - Be concise - documentation should be scannable
   - Focus on WHAT it does, not HOW it's implemented
   - Keep format consistent with existing docs
   - Add new items, remove deleted items, update changed descriptions

4. **Skip documentation updates if:**
   - Changes were trivial (typos, comments, formatting)
   - Changes were to test files only
   - Changes don't affect architecture

5. **Return a summary:**
   - List which doc files you updated (or state "No updates needed: [reason]")
   - Brief description of changes made
   - State "VERIFIED" if you updated docs, or "SKIPPED: [reason]" if no updates needed
```

---

## After Subagent Returns

Based on the subagent's response:

- **If "VERIFIED" or "SKIPPED"**: Clear the log:
  ```bash
  rm -f .claude/hooks/.session-changes.log
  ```
  Then report the summary to the user.

- **If subagent needs clarification**: Do NOT clear the log. Ask the user the subagent's question.
