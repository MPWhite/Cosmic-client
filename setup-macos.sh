#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/macos/common.sh"
if [ "$(uname -s)" != Darwin ]; then
    echo "This setup script is for macOS." >&2
    exit 1
fi
if ! command -v brew >/dev/null 2>&1; then
    echo "Install Homebrew from https://brew.sh, then rerun this script." >&2
    exit 1
fi
brew install git-lfs sevenzip cmake lz4
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import hashlib; assert hasattr(hashlib, "file_digest")' 2>/dev/null; then
    brew install python@3.13
    export PATH="$(brew --prefix python@3.13)/libexec/bin:$PATH"
fi
cd "$CLIENT_ROOT"
mkdir -p "$STATE"
git lfs install --local
git lfs pull
for asset in MapleGlobal-v83-setup.exe cosmic-wz/*.wz; do
    if [ ! -f "$asset" ] || [ "$(stat -f '%z' "$asset")" -lt 1024 ]; then
        echo "Missing game data or an unexpanded Git LFS pointer: $asset" >&2
        exit 1
    fi
done

# Pin source versions so rerunning setup cannot silently change the client.
checkout_source() {
    local target="$1" url="$2" revision="$3"
    if [ ! -d "$target/.git" ]; then
        if [ -e "$target" ]; then
            echo "Expected a source checkout at $target; move that directory before rerunning setup." >&2
            exit 1
        fi
        git init -q "$target"
        git -C "$target" remote add origin "$url"
        git -C "$target" fetch --depth 1 origin "$revision"
        git -C "$target" checkout -q --detach FETCH_HEAD
    fi
    if [ "$(git -C "$target" rev-parse HEAD)" != "$revision" ]; then
        echo "Unexpected source revision in $target. Preserve your changes and use the pinned revision $revision." >&2
        exit 1
    fi
}
apply_local_patch() {
    local target="$1" patch="$2"
    if git -C "$target" apply --reverse --check "$patch" 2>/dev/null; then
        return
    fi
    git -C "$target" apply --check "$patch"
    git -C "$target" apply "$patch"
}
checkout_source "$BROWSER_ROOT" https://github.com/nmnsnv/maplestory-wasm.git 9eef4c730ff5639089eeccae51bf6266c878c30c
checkout_source "$STATE/wz-converter" https://github.com/ryantpayton/NoLifeWzToNx.git 73bddde1214445795d0a5cd4c3d431fe15eb49eb
checkout_source "$STATE/emsdk" https://github.com/emscripten-core/emsdk.git d7b4130688bfa348392b921ab04015aa15c4f154
# Later patches overlap earlier hunks. Check the final layer before migrating
# either a fresh checkout or an existing desktop-only installation.
if ! git -C "$BROWSER_ROOT" apply --reverse --check "$CLIENT_ROOT/macos/patches/browser-mobile.patch" 2>/dev/null; then
    if ! git -C "$BROWSER_ROOT" apply --reverse --check "$CLIENT_ROOT/macos/patches/browser-ui-v83.patch" 2>/dev/null; then
        apply_local_patch "$BROWSER_ROOT" "$CLIENT_ROOT/macos/patches/browser-v83.patch"
        apply_local_patch "$BROWSER_ROOT" "$CLIENT_ROOT/macos/patches/browser-ui-v83.patch"
    fi
    apply_local_patch "$BROWSER_ROOT" "$CLIENT_ROOT/macos/patches/browser-mobile.patch"
fi
apply_local_patch "$BROWSER_ROOT" "$CLIENT_ROOT/macos/patches/browser-resident-movement.patch"
apply_local_patch "$STATE/wz-converter" "$CLIENT_ROOT/macos/patches/wz-converter-macos.patch"

if [ ! -f "$GAME_DIR/Base.wz" ] || [ ! -f "$GAME_DIR/Morph.wz" ] || [ ! -f "$GAME_DIR/TamingMob.wz" ]; then
    python3 macos/extract_installer.py MapleGlobal-v83-setup.exe "$GAME_DIR"
fi
LZ4_PREFIX="$(brew --prefix lz4)"
(
    cd "$STATE/wz-converter"
    clang++ -std=c++17 -O2 -Wno-deprecated-declarations \
        -Iincludes/libsquish -I"$LZ4_PREFIX/include" \
        NoLifeWzToNx.cpp Keys.cpp includes/libsquish/*.cpp \
        -L"$LZ4_PREFIX/lib" -lz -llz4 -o NoLifeWzToNx
)
python3 macos/prepare_browser_assets.py

"$STATE/emsdk/emsdk" install 4.0.21
"$STATE/emsdk/emsdk" activate 4.0.21
# Emsdk's environment script is not compatible with bash's nounset option.
set +u
source "$STATE/emsdk/emsdk_env.sh" >/dev/null 2>&1
set -u
(
    cd "$BROWSER_ROOT"
    ./scripts/build_wasm.sh --jobs "${COSMIC_BUILD_JOBS:-8}"
)
if [ ! -x "$BROWSER_PYTHON" ]; then
    python3 -m venv "$STATE/browser-venv"
fi
"$BROWSER_PYTHON" -m pip install -r "$BROWSER_ROOT/web/requirements.txt"
echo "Browser client setup complete. Start ../Cosmic/launch-macos.command, then ./launch-macos.command."
