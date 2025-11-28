#!/bin/bash
# track-deletions.sh
# PreToolUse hook that tracks file deletions for documentation reminder
# Triggers before Bash commands to detect rm operations on tracked files

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Extract the command from tool input using jq
COMMAND=$(echo "$HOOK_INPUT" | jq -r '.tool_input.command // empty')

# Exit if no command or not a delete operation
if [ -z "$COMMAND" ]; then
    exit 0
fi

# Check if this is an rm command (handles rm, rm -f, rm -rf, etc.)
if ! echo "$COMMAND" | grep -qE '^\s*rm\s'; then
    exit 0
fi

# Define the changes log file
CHANGES_LOG="${CLAUDE_PROJECT_DIR}/.claude/hooks/.session-changes.log"

# Extract potential file paths from rm command
# Remove the rm command and flags, keep the file arguments
FILES=$(echo "$COMMAND" | sed -E 's/^\s*rm\s+(-[rfivI]+\s+)*//g')

# Function to check if a file path should be tracked
check_and_log_file() {
    local FILE_PATH="$1"
    local DOC_TYPE=""

    # Backend Python files (starview_app/)
    if echo "$FILE_PATH" | grep -qE "starview_app/.*\.py$"; then
        DOC_TYPE="backend"
    fi

    # Django project Python files
    if echo "$FILE_PATH" | grep -qE "django_project/.*\.py$"; then
        DOC_TYPE="backend"
    fi

    # Frontend styles
    if echo "$FILE_PATH" | grep -qE "starview_frontend/src/styles/.*\.css$"; then
        DOC_TYPE="style"
    fi

    # Frontend component CSS
    if echo "$FILE_PATH" | grep -qE "starview_frontend/src/(components|pages)/.*\.css$"; then
        DOC_TYPE="frontend-css"
    fi

    # Frontend source files
    if echo "$FILE_PATH" | grep -qE "starview_frontend/src/.*\.(jsx?|tsx?)$"; then
        DOC_TYPE="frontend"
    fi

    # Migrations
    if echo "$FILE_PATH" | grep -qE "migrations/.*\.py$"; then
        DOC_TYPE="backend"
    fi

    # Log if tracked file type
    if [ -n "$DOC_TYPE" ]; then
        echo "deleted:${DOC_TYPE}:${FILE_PATH}" >> "$CHANGES_LOG"
    fi
}

# Process each potential file path (space-separated)
# Handle quoted paths and multiple files
for FILE in $FILES; do
    # Remove quotes if present
    FILE=$(echo "$FILE" | sed "s/['\"]//g")

    # Skip if empty or looks like a flag we missed
    if [ -z "$FILE" ] || [[ "$FILE" == -* ]]; then
        continue
    fi

    check_and_log_file "$FILE"
done

exit 0
