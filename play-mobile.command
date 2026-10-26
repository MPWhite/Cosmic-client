#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/macos/common.sh"
exec python3 "$CLIENT_ROOT/macos/enable_mobile.py"
