#!/bin/bash
# pre-commit-check.sh
# PreToolUse hook for Bash commands containing "git commit"
# Reminds about pending documentation updates BEFORE committing

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Extract the command from tool input
COMMAND=$(echo "$HOOK_INPUT" | jq -r '.tool_input.command // empty')

# Only check for git commit commands
if ! echo "$COMMAND" | grep -qE "git\s+commit"; then
    exit 0
fi

# Check if there are pending documentation changes
CHANGES_LOG="${CLAUDE_PROJECT_DIR}/.claude/hooks/.session-changes.log"

if [ ! -f "$CHANGES_LOG" ] || [ ! -s "$CHANGES_LOG" ]; then
    # No pending changes, proceed with commit
    exit 0
fi

# Count changes by type (separate assignment from fallback to avoid "0\n0" bug)
BACKEND_CHANGES=$(grep -c "^backend:" "$CHANGES_LOG" 2>/dev/null) || BACKEND_CHANGES=0
FRONTEND_CHANGES=$(grep -c "^frontend:" "$CHANGES_LOG" 2>/dev/null) || FRONTEND_CHANGES=0
STYLE_CHANGES=$(grep -c "^style:" "$CHANGES_LOG" 2>/dev/null) || STYLE_CHANGES=0
FRONTEND_CSS_CHANGES=$(grep -c "^frontend-css:" "$CHANGES_LOG" 2>/dev/null) || FRONTEND_CSS_CHANGES=0
TOTAL_CHANGES=$((BACKEND_CHANGES + FRONTEND_CHANGES + STYLE_CHANGES + FRONTEND_CSS_CHANGES))

if [ "$TOTAL_CHANGES" -gt 0 ]; then
    echo ""
    echo "=================================================="
    echo "  PRE-COMMIT: DOCUMENTATION CHECK"
    echo "=================================================="
    echo ""
    echo "  You have uncommitted documentation updates:"
    echo ""

    if [ "$BACKEND_CHANGES" -gt 0 ]; then
        echo "  - Backend files modified: $BACKEND_CHANGES -> ARCHITECTURE.md"
    fi

    if [ "$FRONTEND_CHANGES" -gt 0 ]; then
        echo "  - Frontend JS/JSX modified: $FRONTEND_CHANGES -> ARCHITECTURE.md"
    fi

    if [ "$STYLE_CHANGES" -gt 0 ]; then
        echo "  - Global styles modified: $STYLE_CHANGES -> STYLE_GUIDE.md"
    fi

    if [ "$FRONTEND_CSS_CHANGES" -gt 0 ]; then
        echo "  - Component CSS modified: $FRONTEND_CSS_CHANGES -> check STYLE_GUIDE.md"
    fi

    echo ""
    echo "  RECOMMENDATION: Run /update-docs before committing"
    echo "  This ensures documentation stays in sync with code."
    echo "=================================================="
    echo ""
fi

exit 0
