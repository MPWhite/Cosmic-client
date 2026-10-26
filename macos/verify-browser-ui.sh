#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
# Tests use the converted v83 files read-only. UI_83 is an alias required by
# upstream tests that also support a separate modern UI asset set.
export COSMIC_UI_FIXTURE="$STATE/ui-test-assets"
export COSMIC_UI_ASSETS="$BROWSER_ASSETS"
python3 - <<'PY'
import os
from pathlib import Path
source = Path(os.environ['COSMIC_UI_ASSETS'])
fixture = Path(os.environ['COSMIC_UI_FIXTURE'])
fixture.mkdir(parents=True, exist_ok=True)
for name in ('Character', 'Etc', 'Item', 'Npc', 'Quest', 'String', 'UI', 'UI_83'):
    target = source / ('UI.nx' if name == 'UI_83' else name + '.nx')
    if not target.is_file():
        raise SystemExit(f'Missing {target}; run setup-macos.sh first.')
    link = fixture / (name + '.nx')
    if link.is_symlink():
        if link.resolve() == target.resolve():
            continue
        link.unlink()
    elif link.exists():
        raise SystemExit(f'Refusing to replace non-symlink fixture: {link}')
    link.symlink_to(target.resolve())
PY
cd "$BROWSER_ROOT"
TEST_ASSET_DIR="$COSMIC_UI_FIXTURE" ./scripts/run_tests.sh --assets --jobs "${COSMIC_BUILD_JOBS:-8}" "$@"
