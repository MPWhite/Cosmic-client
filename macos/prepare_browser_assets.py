#!/usr/bin/env python3
"""Convert the checked-out WZ data without changing the source assets."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / '.local'
ASSETS = STATE / 'browser-assets'
NAMES = ('Base', 'Character', 'Effect', 'Etc', 'Item', 'Map', 'Mob', 'Morph',
         'Npc', 'Quest', 'Reactor', 'Skill', 'Sound', 'String', 'TamingMob', 'UI')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_nx(path):
    with path.open('rb') as stream:
        header = stream.read(52)
    if len(header) != 52:
        raise ValueError(f'Truncated NX file: {path}')
    magic, nodes, node_offset, strings, string_offset, bitmaps, bitmap_offset, audio, audio_offset = struct.unpack('<4sIQIQIQIQ', header)
    if magic != b'PKG4' or not nodes:
        raise ValueError(f'Invalid NX file: {path}')
    size = path.stat().st_size
    for count, offset, width in ((nodes, node_offset, 20), (strings, string_offset, 8),
                                 (bitmaps, bitmap_offset, 8), (audio, audio_offset, 8)):
        if count and (offset < 52 or offset + count * width > size):
            raise ValueError(f'Incomplete NX table: {path}')


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    manifest_path = ASSETS / '.manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    converter = STATE / 'wz-converter/NoLifeWzToNx'
    converter_version = digest(ROOT / 'macos/patches/wz-converter-macos.patch')
    for name in NAMES:
        source = ROOT / 'cosmic-wz' / f'{name}.wz'
        if not source.exists():
            source = STATE / 'game' / f'{name}.wz'
        if not source.exists():
            raise FileNotFoundError(f'Missing {source}; rerun setup-macos.sh')
        stamp = {'source': digest(source), 'converter': converter_version}
        target = ASSETS / f'{name}.nx'
        if manifest.get(name) == stamp and target.exists():
            validate_nx(target)
            print(f'{name}.nx is current.', flush=True)
            continue
        print(f'Converting {name}.wz...', flush=True)
        # The converter writes beside its input. Work in a temporary directory
        # so a failed conversion never replaces a previously usable NX file.
        with tempfile.TemporaryDirectory(prefix='.convert-', dir=ASSETS) as scratch:
            work = Path(scratch)
            (work / source.name).symlink_to(source)
            result = subprocess.run([str(converter), source.name, '-c'], cwd=work,
                                    capture_output=True, text=True)
            log = result.stdout + result.stderr
            detail = work / 'NoLifeWzToNx.log'
            if detail.exists():
                log += detail.read_text(errors='replace')
            (STATE / f'asset-{name}.log').write_text(log)
            if result.returncode or 'Error converting' in log:
                raise RuntimeError(f'{name} conversion failed; see {STATE / f"asset-{name}.log"}')
            converted = work / f'{name}.nx'
            validate_nx(converted)
            converted.replace(target)
        manifest[name] = stamp
        temporary = manifest_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(manifest, indent=2) + '\n')
        temporary.replace(manifest_path)
    print('All 16 browser asset files are ready.', flush=True)


if __name__ == '__main__':
    main()
