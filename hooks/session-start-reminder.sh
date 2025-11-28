#!/bin/bash
# session-start-reminder.sh
# SessionStart hook that reminds Claude about pending documentation updates
# Checks if previous session had changes that weren't documented

CHANGES_LOG="${CLAUDE_PROJECT_DIR}/.claude/hooks/.session-changes.log"

# Check if changes log exists from previous session
if [ ! -f "$CHANGES_LOG" ] || [ ! -s "$CHANGES_LOG" ]; then
    # No pending changes, exit silently
    exit 0
fi

# Count changes by type (separate assignment from fallback to avoid "0\n0" bug)
BACKEND_CHANGES=$(grep -c "^backend:" "$CHANGES_LOG" 2>/dev/null) || BACKEND_CHANGES=0
FRONTEND_CHANGES=$(grep -c "^frontend:" "$CHANGES_LOG" 2>/dev/null) || FRONTEND_CHANGES=0
STYLE_CHANGES=$(grep -c "^style:" "$CHANGES_LOG" 2>/dev/null) || STYLE_CHANGES=0
FRONTEND_CSS_CHANGES=$(grep -c "^frontend-css:" "$CHANGES_LOG" 2>/dev/null) || FRONTEND_CSS_CHANGES=0
TOTAL_CHANGES=$((BACKEND_CHANGES + FRONTEND_CHANGES + STYLE_CHANGES + FRONTEND_CSS_CHANGES))

# Output reminder for Claude to see
if [ "$TOTAL_CHANGES" -gt 0 ]; then
    echo ""
    echo "=================================================="
    echo "  PENDING DOCUMENTATION UPDATE"
    echo "=================================================="
    echo ""
    echo "  Previous session modified files that may need documentation updates:"
    echo ""

    if [ "$BACKEND_CHANGES" -gt 0 ]; then
        echo "  - Backend files: $BACKEND_CHANGES -> ARCHITECTURE.md"
    fi

    if [ "$FRONTEND_CHANGES" -gt 0 ]; then
        echo "  - Frontend JS/JSX: $FRONTEND_CHANGES -> ARCHITECTURE.md"
    fi

    if [ "$STYLE_CHANGES" -gt 0 ]; then
        echo "  - Global styles: $STYLE_CHANGES -> STYLE_GUIDE.md"
    fi

    if [ "$FRONTEND_CSS_CHANGES" -gt 0 ]; then
        echo "  - Component CSS: $FRONTEND_CSS_CHANGES -> check STYLE_GUIDE.md"
    fi

    echo ""
    echo "  ACTION REQUIRED: Run /update-docs to sync documentation"
    echo "  After running, the reminder will be cleared."
    echo "=================================================="
    echo ""
fi

exit 0
