from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_zip(path: Path) -> int:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate member in {path.name}")
        for info in z.infolist():
            pp = PurePosixPath(info.filename)
            if pp.is_absolute() or ".." in pp.parts or "\\" in info.filename:
                raise ValueError(f"unsafe path in {path.name}")
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError(f"symlink in {path.name}")
        bad = z.testzip()
        if bad is not None:
            raise ValueError(f"CRC error {path.name}:{bad}")
        return len(names)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root")
    args = p.parse_args()
    root = Path(args.root).resolve()
    atomics = sorted((root / "atomics").glob("*.zip"))
    if len(atomics) != 10:
        raise SystemExit(f"expected 10 atomic zips, got {len(atomics)}")
    for item in atomics:
        safe_zip(item)
    master = root / "BIE_APP_SECTION18_BATCH001_MASTER_PACKAGE.zip"
    combined = root / "BIE_APP_SECTION18_BATCH001_COMBINED_SOURCE.zip"
    master_members = safe_zip(master)
    combined_members = safe_zip(combined)
    continuation = json.loads((root / "CONTINUATION.json").read_text())
    if continuation["completed_original_task_count"] != 10 or continuation["section_complete"]:
        raise SystemExit("continuation mismatch")
    print(json.dumps({
        "status": "PASS",
        "atomic_zips": 10,
        "master_members": master_members,
        "combined_members": combined_members,
        "master_sha256": sha(master),
        "section_complete": False,
    }, indent=2))


if __name__ == "__main__":
    main()
