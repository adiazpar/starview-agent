#!/bin/bash
# subagent-monitor.sh
# SubagentStop hook that tracks subagent usage for cost monitoring
# Logs subagent completions with timestamps for analysis

LOG_FILE="${CLAUDE_PROJECT_DIR}/.claude/hooks/subagent.log"

# Read the hook input from stdin
INPUT=$(cat)

# Extract subagent information (if available in the hook context)
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Log the subagent completion
echo "[$TIMESTAMP] Subagent completed" >> "$LOG_FILE"

# Keep log file manageable - only keep last 100 entries
if [ -f "$LOG_FILE" ]; then
    LINES=$(wc -l < "$LOG_FILE")
    if [ "$LINES" -gt 100 ]; then
        tail -100 "$LOG_FILE" > "${LOG_FILE}.tmp"
        mv "${LOG_FILE}.tmp" "$LOG_FILE"
    fi
fi

exit 0
