#!/bin/bash
set -euo pipefail
CLIENT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
STATE="$CLIENT_ROOT/.local"
GAME_DIR="$STATE/game"
BROWSER_ROOT="$STATE/browser-client"
BROWSER_ASSETS="$STATE/browser-assets"
BROWSER_PYTHON="$STATE/browser-venv/bin/python"
