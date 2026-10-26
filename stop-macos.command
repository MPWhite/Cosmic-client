#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/macos/common.sh"
if [ -x "$BROWSER_PYTHON" ]; then
    "$BROWSER_PYTHON" "$CLIENT_ROOT/macos/browser_services.py" stop
else
    echo "The browser client has not been set up yet."
fi
