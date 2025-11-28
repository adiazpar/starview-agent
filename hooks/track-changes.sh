#!/bin/bash
# track-changes.sh
# PostToolUse hook that tracks file changes for documentation reminder
# Triggers after Write/Edit tools to log significant file modifications

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Extract file path from tool input using jq
FILE_PATH=$(echo "$HOOK_INPUT" | jq -r '.tool_input.file_path // empty')

# Exit if no file path (shouldn't happen, but be safe)
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Define the changes log file (session-specific using PID or temp)
CHANGES_LOG="${CLAUDE_PROJECT_DIR}/.claude/hooks/.session-changes.log"

# Check if file is significant (backend or frontend code)
NEEDS_DOC_UPDATE=false
DOC_TYPE=""

# Backend Python files
if echo "$FILE_PATH" | grep -qE "starview_app/.*\.py$"; then
    NEEDS_DOC_UPDATE=true
    DOC_TYPE="backend"
fi

# Frontend styles (CSS in src/styles/) -> STYLE_GUIDE.md
if echo "$FILE_PATH" | grep -qE "starview_frontend/src/styles/.*\.css$"; then
    NEEDS_DOC_UPDATE=true
    DOC_TYPE="style"
fi

# Frontend component CSS -> may need STYLE_GUIDE.md if patterns change
if echo "$FILE_PATH" | grep -qE "starview_frontend/src/(components|pages)/.*\.css$"; then
    NEEDS_DOC_UPDATE=true
    DOC_TYPE="frontend-css"
fi

# Frontend source files (JS/JSX/TS/TSX)
if echo "$FILE_PATH" | grep -qE "starview_frontend/src/.*\.(jsx?|tsx?)$"; then
    NEEDS_DOC_UPDATE=true
    DOC_TYPE="frontend"
fi

# Migrations (badge-related)
if echo "$FILE_PATH" | grep -qE "migrations/.*\.py$"; then
    NEEDS_DOC_UPDATE=true
    DOC_TYPE="backend"
fi

# Log the change if significant
if [ "$NEEDS_DOC_UPDATE" = true ]; then
    echo "${DOC_TYPE}:${FILE_PATH}" >> "$CHANGES_LOG"

    # Single gentle reminder after 5 files, then trust Claude's judgment
    TOTAL_CHANGES=$(wc -l < "$CHANGES_LOG" | tr -d ' ')
    if [ "$TOTAL_CHANGES" -eq 5 ]; then
        echo ""
        echo "📝 Documentation tracking active (5 files modified). Run /update-docs when this task is complete."
        echo ""
    fi
fi

exit 0
