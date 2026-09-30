from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import argparse
import hashlib
import json
import sys


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("delivery", nargs="?", default=".")
    args=parser.parse_args()
    root=Path(args.delivery).resolve()
    errors=[]
    sums=root/"SHA256SUMS.txt"
    if not sums.is_file():
        errors.append("SHA256SUMS_MISSING")
    else:
        for line in sums.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            digest, name=line.split("  ",1)
            path=root/name
            if not path.is_file():
                errors.append("MISSING:"+name)
            elif sha256_file(path)!=digest:
                errors.append("HASH_MISMATCH:"+name)
    atomics=sorted((root/"atomics").glob("*.zip")) if (root/"atomics").is_dir() else []
    if len(atomics)!=10:
        errors.append(f"ATOMIC_COUNT:{len(atomics)}")
    for path in sorted(root.rglob("*.zip")):
        try:
            with ZipFile(path) as z:
                if len(z.namelist())!=len(set(z.namelist())):
                    errors.append("DUPLICATE_ZIP_MEMBER:"+path.name)
                bad=z.testzip()
                if bad:
                    errors.append("CRC:"+path.name+":"+bad)
        except Exception as exc:
            errors.append("ZIP_ERROR:"+path.name+":"+type(exc).__name__)
    try:
        verification=json.loads((root/"VERIFICATION.json").read_text(encoding="utf-8"))
        if verification.get("atomic_count")!=10 or not verification.get("all_tests_passed"):
            errors.append("VERIFICATION_NOT_PASS")
    except Exception:
        errors.append("VERIFICATION_UNREADABLE")
    result={
        "schema_version":"bie.section18.delivery-verifier/1",
        "status":"PASS" if not errors else "FAIL",
        "atomic_count":len(atomics),
        "zip_count":len(list(root.rglob("*.zip"))),
        "errors":errors,
        "product_accepted":False,
        "github_integrated":False,
    }
    print(json.dumps(result,indent=2))
    return 0 if not errors else 1


if __name__=="__main__":
    raise SystemExit(main())
