#!/usr/bin/env python3
"""Restore the exact released print assets into a source checkout."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import urllib.request
import zipfile


ARCHIVE_URL = (
    "https://github.com/thisisformuchfun/nestforge/releases/download/v1.0.0/"
    "NestForge-Complete-Collection-v1.0.0.zip"
)
ARCHIVE_SHA256 = "e95d1838ec7ddf99900c56ce904a223ac665f8e01ee5dc5261be0aa37c33142b"
ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PREFIXES = (
    "dist/models/", "dist/vendor/", "dist/assets/", "archive/", "docs/artwork/",
)
PAYLOAD_FILES = {
    "dist/downloads/NestForge-CAD-Source.zip",
    "cad-source/cad/assets/artec-dragon-printable.stl",
    "review/themes-preview-2026-10-24.jpg",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def restore(archive: Path) -> None:
    print("Verifying the complete collection download...")
    if digest(archive) != ARCHIVE_SHA256:
        raise SystemExit("The archive checksum does not match the v1.0.0 collection.")
    restored = existing = 0
    with zipfile.ZipFile(archive) as package:
        selected = []
        for item in package.infolist():
            if item.is_dir():
                continue
            name = item.filename
            path = PurePosixPath(name)
            mode = stat.S_IFMT(item.external_attr >> 16)
            if (path.is_absolute() or ".." in path.parts or "\\" in name
                    or str(path) != name or mode not in (0, stat.S_IFREG)
                    or ".git" in path.parts or ".github" in path.parts):
                raise SystemExit(f"Unexpected archive path: {name}")
            if name in PAYLOAD_FILES or name.startswith(PAYLOAD_PREFIXES):
                target = ROOT.joinpath(*path.parts)
                if not target.resolve().is_relative_to(ROOT):
                    raise SystemExit(f"Destination escapes checkout: {name}")
                selected.append((item, target))
        # Check existing files before writing so a user's edits are preserved.
        for item, target in selected:
            if target.exists():
                with package.open(item) as stream:
                    h = hashlib.sha256()
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        h.update(block)
                if not target.is_file() or digest(target) != h.hexdigest():
                    raise SystemExit(f"Existing file differs; preserve or move it first: {target}")
        for item, target in selected:
            if target.exists():
                existing += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with package.open(item) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output, 1024 * 1024)
            restored += 1
    print(f"Restored {restored} files; {existing} identical files already present.")
    print("Ready: python -m http.server 8000 --bind 127.0.0.1 --directory dist")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Use an already-downloaded complete collection ZIP.")
    args = parser.parse_args()
    if args.archive:
        restore(args.archive.resolve())
        return
    with tempfile.TemporaryDirectory(prefix="nestforge-download-") as directory:
        archive = Path(directory) / "collection.zip"
        print("Downloading the complete v1.0.0 collection (about 504 MB)...")
        request = urllib.request.Request(ARCHIVE_URL, headers={"User-Agent": "NestForge-collection-fetcher/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output, 1024 * 1024)
        restore(archive)


if __name__ == "__main__":
    main()
