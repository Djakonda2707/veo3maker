#!/usr/bin/env bash
#
# Start the veo3maker bot in a detached tmux session.
#
# Usage:
#   bash scripts/run.sh            # starts or restarts the 'subsbot' session
#   tmux attach -t subsbot         # watch the logs interactively
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

if [ ! -f .env ]; then
  echo "ERROR: .env not found. Run scripts/install.sh first and edit .env." >&2
  exit 1
fi

if ! command -v tmux >/dev/null 2>&1; then
  echo "Installing tmux..." >&2
  apt-get install -y tmux
fi

# Kill any existing session with the same name before starting fresh.
tmux kill-session -t subsbot 2>/dev/null || true

# Also nuke any stray bot.py from a previous manual run.
pkill -f "python.*bot\\.py" 2>/dev/null || true

tmux new-session -d -s subsbot \
  "cd '$REPO_DIR' && . .venv/bin/activate && python -u bot.py 2>&1 | tee -a /tmp/subsbot.log"

sleep 1
echo
echo "Bot started in tmux session 'subsbot'."
echo "  Attach:   tmux attach -t subsbot"
echo "  Detach:   Ctrl+B then D"
echo "  Logs:     tail -f /tmp/subsbot.log"
