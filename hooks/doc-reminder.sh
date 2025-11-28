#!/bin/bash
# doc-reminder.sh
# Stop hook that reminds about documentation updates
# Checks if significant files were modified during the session

CHANGES_LOG="${CLAUDE_PROJECT_DIR}/.claude/hooks/.session-changes.log"

# Check if changes log exists and has content
if [ ! -f "$CHANGES_LOG" ] || [ ! -s "$CHANGES_LOG" ]; then
    # No significant changes, exit silently
    exit 0
fi

# Count changes by type (separate assignment from fallback to avoid "0\n0" bug)
BACKEND_CHANGES=$(grep -c "^backend:" "$CHANGES_LOG" 2>/dev/null) || BACKEND_CHANGES=0
FRONTEND_CHANGES=$(grep -c "^frontend:" "$CHANGES_LOG" 2>/dev/null) || FRONTEND_CHANGES=0
STYLE_CHANGES=$(grep -c "^style:" "$CHANGES_LOG" 2>/dev/null) || STYLE_CHANGES=0
FRONTEND_CSS_CHANGES=$(grep -c "^frontend-css:" "$CHANGES_LOG" 2>/dev/null) || FRONTEND_CSS_CHANGES=0
TOTAL_CHANGES=$((BACKEND_CHANGES + FRONTEND_CHANGES + STYLE_CHANGES + FRONTEND_CSS_CHANGES))

# Build reminder message
if [ "$TOTAL_CHANGES" -gt 0 ]; then
    echo ""
    echo "=================================================="
    echo "  DOCUMENTATION REMINDER"
    echo "=================================================="
    echo ""

    if [ "$BACKEND_CHANGES" -gt 0 ]; then
        echo "  Backend files modified: $BACKEND_CHANGES"
        echo "    -> Update .claude/backend/ARCHITECTURE.md"
    fi

    if [ "$FRONTEND_CHANGES" -gt 0 ]; then
        echo "  Frontend JS/JSX files modified: $FRONTEND_CHANGES"
        echo "    -> Update .claude/frontend/ARCHITECTURE.md"
    fi

    if [ "$STYLE_CHANGES" -gt 0 ]; then
        echo "  Global styles modified: $STYLE_CHANGES"
        echo "    -> UPDATE .claude/frontend/STYLE_GUIDE.md"
    fi

    if [ "$FRONTEND_CSS_CHANGES" -gt 0 ]; then
        echo "  Component CSS files modified: $FRONTEND_CSS_CHANGES"
        echo "    -> Check STYLE_GUIDE.md if patterns changed"
    fi

    echo ""
    echo "  Run /update-docs to sync documentation"
    echo "=================================================="
    echo ""
fi

# NOTE: Don't delete the log - SessionStart hook will remind next session
# The log is cleared when /update-docs is run

exit 0
