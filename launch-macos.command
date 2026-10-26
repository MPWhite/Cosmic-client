#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/macos/common.sh"
if [ ! -x "$BROWSER_PYTHON" ] || [ ! -f "$BROWSER_ROOT/build/JourneyClient.wasm" ] || [ ! -f "$BROWSER_ASSETS/.manifest.json" ]; then
    echo "The browser client is not installed yet. Run ./setup-macos.sh first." >&2
    exit 1
fi
if ! nc -z -w 2 127.0.0.1 8484 2>/dev/null; then
    echo "Cosmic's login server is offline. Start ../Cosmic/launch-macos.command first." >&2
    exit 1
fi
echo "Starting the browser client at http://127.0.0.1:8000"
"$BROWSER_PYTHON" -u "$CLIENT_ROOT/macos/browser_services.py" start 2>&1 | tee -a "$STATE/browser.log"
