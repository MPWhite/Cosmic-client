#!/usr/bin/env python3
"""Extract the two embedded CAB volumes from the original, pinned v83 installer.

7-Zip sees only the first CAB when given the EXE directly. Split both volumes
with their original names so it can follow files spanning the volume boundary.
Only vanilla assets absent from cosmic-wz and the game DLLs are needed.
"""

import hashlib
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

INSTALLER_SHA256 = "1a1128ac97e11c7845aacec1a5484e650558a67da94b94147d72292e1568366d"
CABINETS = ((3371141, 1048576000), (1051947141, 711654917))


def extract(installer: Path, destination: Path) -> None:
    with installer.open("rb") as source:
        checksum = hashlib.file_digest(source, "sha256").hexdigest()
        if checksum != INSTALLER_SHA256:
            raise ValueError("Installer checksum mismatch. Run git lfs pull to get the original v83 installer.")
        destination.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cosmic-cabs-", dir=destination.parent) as scratch:
            for index, (offset, length) in enumerate(CABINETS, start=1):
                source.seek(offset)
                header = source.read(36)
                if header[:4] != b"MSCF" or struct.unpack_from("<I", header, 8)[0] != length:
                    raise ValueError(f"Invalid cabinet {index} in installer")
                source.seek(offset)
                with (Path(scratch) / f"MapleStory_{index}.cab").open("wb") as cabinet:
                    remaining = length
                    while remaining:
                        chunk = source.read(min(1024 * 1024, remaining))
                        if not chunk:
                            raise ValueError("Truncated installer")
                        cabinet.write(chunk)
                        remaining -= len(chunk)
            sevenzip = shutil.which("7zz")
            if not sevenzip:
                raise RuntimeError("7-Zip is missing. Install it with brew install sevenzip.")
            subprocess.run([
                sevenzip, "x", str(Path(scratch) / "MapleStory_1.cab"),
                f"-o{destination.resolve()}", "-y", "-bsp0",
                "*.dll", "*.acm", "Base.wz", "Effect.wz", "Morph.wz", "Sound.wz", "TamingMob.wz", "-xr!HShield",
            ], check=True)
    for filename in ("Base.wz", "Effect.wz", "Morph.wz", "Sound.wz", "TamingMob.wz", "Gr2D_DX8.dll", "PCOM.dll", "ijl15.dll"):
        if not (destination / filename).is_file():
            raise RuntimeError(f"Extraction did not produce {filename}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: extract_installer.py INSTALLER.exe DESTINATION")
    try:
        extract(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
