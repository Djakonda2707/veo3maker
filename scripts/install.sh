#!/usr/bin/env bash
#
# Native installer for the veo3maker bot on Ubuntu 22.04 / 24.04.
#
# Usage:
#   cd ~/veo3maker
#   bash scripts/install.sh
#
# Idempotent: safe to re-run. Stops any running bot.py, installs system
# dependencies, sets up the Python venv + Remotion node_modules, and
# leaves you ready to edit .env and launch the bot.
set -euo pipefail

log() { printf '\n\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\n\033[1;33m[warn]\033[0m %s\n' "$*"; }

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

# ---------------------------------------------------------------------------
# 0. Stop any old bot that might be running
# ---------------------------------------------------------------------------
log "Stopping any previous bot.py process"
if pgrep -f "python.*bot\\.py" >/dev/null 2>&1; then
  pkill -f "python.*bot\\.py" || true
  sleep 1
  if pgrep -f "python.*bot\\.py" >/dev/null 2>&1; then
    warn "bot.py still running, sending SIGKILL"
    pkill -9 -f "python.*bot\\.py" || true
  fi
fi

# Also detach any tmux/screen session named 'subsbot' if present.
if command -v tmux >/dev/null 2>&1; then
  tmux kill-session -t subsbot 2>/dev/null || true
fi
if command -v screen >/dev/null 2>&1; then
  screen -S subsbot -X quit 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
log "apt-get update"
apt-get update

log "Installing system packages (Python, ffmpeg, Chrome runtime libs)"
apt-get install -y \
  python3 python3-pip python3-venv python3-dev \
  ffmpeg git curl ca-certificates gnupg \
  fonts-noto-core fonts-noto-color-emoji \
  libnss3 libxss1 libatk-bridge2.0-0 libgtk-3-0 libgbm1 \
  libdrm2 libxcomposite1 libxdamage1 libxrandr2 libxkbcommon0 \
  libpango-1.0-0 libcairo2

# libasound2 was renamed to libasound2t64 on Ubuntu 24.04; try both.
apt-get install -y libasound2t64 2>/dev/null || apt-get install -y libasound2 || true

# ---------------------------------------------------------------------------
# 2. Node 20 via NodeSource
# ---------------------------------------------------------------------------
if ! command -v node >/dev/null 2>&1 || [ "$(node -v | sed 's/v\([0-9]*\).*/\1/')" -lt 20 ]; then
  log "Installing Node 20 via NodeSource"
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
else
  log "Node already installed: $(node -v)"
fi

# ---------------------------------------------------------------------------
# 3. Python venv + requirements
# ---------------------------------------------------------------------------
log "Creating Python venv"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate

log "Installing Python requirements"
pip install --upgrade pip
pip install -r requirements.txt

# ---------------------------------------------------------------------------
# 4. Remotion node_modules
# ---------------------------------------------------------------------------
log "Installing Remotion dependencies (npm install)"
(cd remotion && npm install)

# ---------------------------------------------------------------------------
# 5. .env scaffold
# ---------------------------------------------------------------------------
if [ ! -f .env ]; then
  log "Creating .env from .env.example"
  cp .env.example .env
else
  log ".env already exists — not overwriting"
fi

# ---------------------------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------------------------
echo
echo "=========================================="
echo " ВСЁ УСТАНОВЛЕНО"
echo "=========================================="
echo "node:    $(node -v)"
echo "npm:     $(npm -v)"
echo "python:  $(python3 --version)"
echo "ffmpeg:  $(ffmpeg -version | head -1)"
echo
echo "Next steps:"
echo "  1) nano $REPO_DIR/.env    # paste BOT_TOKEN"
echo "  2) bash scripts/run.sh    # start the bot in a tmux session"
