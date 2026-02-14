#!/bin/bash
# Claude Code Status Line
# Model | Directory | Branch | Token Usage Bar | Cost

input=$(cat)

# Extract values
MODEL=$(echo "$input" | jq -r '.model.display_name // "?"')
CURRENT_DIR=$(echo "$input" | jq -r '.workspace.current_dir // "."')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
LINES_ADD=$(echo "$input" | jq -r '.cost.total_lines_added // 0')
LINES_DEL=$(echo "$input" | jq -r '.cost.total_lines_removed // 0')

# Git branch
BRANCH=$(cd "$CURRENT_DIR" 2>/dev/null && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git")

# Directory basename
DIR=$(basename "$CURRENT_DIR")

# Progress bar (10 chars)
PCT=${PCT:-0}
FILLED=$((PCT * 10 / 100))
[ "$FILLED" -gt 10 ] && FILLED=10
EMPTY=$((10 - FILLED))
BAR=""
[ "$FILLED" -gt 0 ] && BAR=$(printf "%${FILLED}s" | tr ' ' '▓')
[ "$EMPTY" -gt 0 ] && BAR="${BAR}$(printf "%${EMPTY}s" | tr ' ' '░')"

# Color based on usage (green < 50%, yellow 50-79%, red >= 80%)
if [ "$PCT" -ge 80 ]; then
  BAR_COLOR='\033[1;31m'  # Bold Red
elif [ "$PCT" -ge 50 ]; then
  BAR_COLOR='\033[1;33m'  # Bold Yellow
else
  BAR_COLOR='\033[1;32m'  # Bold Green
fi

# Format cost
COST_FMT=$(printf '$%.2f' "$COST")

# Format lines changed
LINES=""
if [ "$LINES_ADD" -gt 0 ] || [ "$LINES_DEL" -gt 0 ]; then
  LINES=" | \033[32m+${LINES_ADD}\033[0m \033[31m-${LINES_DEL}\033[0m"
fi

RESET='\033[0m'
BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'

printf "${BLUE}%s${RESET} | ${GREEN}%s${RESET} | ${YELLOW}%s${RESET} | ${BAR_COLOR}%s${RESET} %s%% | ${CYAN}%s${RESET}%b" \
  "$MODEL" "$DIR" "$BRANCH" "$BAR" "$PCT" "$COST_FMT" "$LINES"
