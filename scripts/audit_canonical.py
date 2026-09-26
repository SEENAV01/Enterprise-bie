"""Independent lossless reconciliation: original ZIP bytes, ledger and canonical files."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
import io
import json
from pathlib import Path
import sys
import zipfile

from assembly_lib import TERMINAL_STATES, digest

ROOT = Path(__file__).resolve().parents[1]


def audit(root=ROOT):
    errors = []
    rows = list(csv.DictReader((root / "manifests/lossless_migration.csv").open()))
    from game_initializer_amendment import resolve
    try: rows = resolve(root, rows)
    except (ValueError, OSError, KeyError) as exc: errors.append(str(exc))
    original = json.loads((root / "manifests/archive_inventory.json").read_text())["archives"]
    supplemental = json.loads((root / "manifests/supplemental_archives.json").read_text())
    expected_members = json.loads((root / "manifests/file_inventory.json").read_text())["files"] + [f for a in supplemental for f in a["files"]]
    keys = [(x["archive"], x["source_path"]) for x in rows]
    expected_keys = [(x["archive"], x["member"]) for x in expected_members]
    if Counter(keys) != Counter(expected_keys) or len(keys) != len(set(keys)):
        errors.append("Ledger is not a one-to-one accounting of all original files")
    if len({x["file_id"] for x in rows}) != len(rows):
        errors.append("Duplicate ledger file identity")
    by_key = dict(zip(keys, rows))
    by_id = {x["file_id"]: x for x in rows}
    raw_archives = {}
    bundle_info = json.loads((root / "manifests/original_backup.json").read_text())
    bundle_data = (root / bundle_info["path"]).read_bytes()
    if digest(bundle_data) != bundle_info["sha256"]:
        errors.append("Original ZIP collection checksum mismatch")
    with zipfile.ZipFile(io.BytesIO(bundle_data)) as bundle:
        if len(bundle.namelist()) != len(original):
            errors.append("Original ZIP collection member count mismatch")
        for a in original:
            raw_archives[a["name"]] = bundle.read("original-zips/" + a["name"])
    for a in supplemental:
        raw_archives[a["name"]] = (root / a["original_path"]).read_bytes()
    original_checked = 0
    for a in original + supplemental:
        data = raw_archives[a["name"]]
        if digest(data) != a["sha256"]:
            errors.append("Archive SHA mismatch: " + a["name"])
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            members = [i for i in z.infolist() if not i.is_dir()]
            if len(members) != a["member_count"]:
                errors.append("Archive member count mismatch: " + a["name"])
            for info in members:
                key = (a["name"], info.filename)
                row = by_key.get(key)
                if row is None:
                    errors.append("Original member absent from ledger: " + repr(key)); continue
                data = z.read(info)
                if digest(data) != row["sha256"] or len(data) != int(row["bytes"]):
                    errors.append("Member provenance mismatch: " + repr(key))
                original_checked += 1
    verified_paths = {}
    for row in rows:
        if row["disposition"] not in TERMINAL_STATES or not row["reason"].strip():
            errors.append("Nonterminal or unexplained disposition: " + row["file_id"])
        if row["availability"] != "AVAILABLE_VERIFIED":
            errors.append("Unresolved source availability: " + row["file_id"])
        path = row["canonical_path"]
        if path:
            p = root / path
            if not p.resolve().is_relative_to(root.resolve()) or p.is_symlink():
                errors.append("Unsafe canonical path: " + path); continue
            if path not in verified_paths:
                verified_paths[path] = digest(p.read_bytes()) if p.is_file() else None
            if verified_paths[path] != row["canonical_sha256"]:
                errors.append("Canonical content mismatch: " + path)
        elif row["disposition"] in {"MIGRATED", "DUPLICATE_WITH_PROVENANCE"}:
            errors.append("Migration lacks canonical destination: " + row["file_id"])
        if row["disposition"] == "DUPLICATE_WITH_PROVENANCE":
            target = by_id.get(row["duplicate_of"])
            if not target or target["sha256"] != row["sha256"] or target["canonical_path"] != path or target["disposition"] == "DUPLICATE_WITH_PROVENANCE":
                errors.append("Invalid duplicate provenance: " + row["file_id"])
    initial = list(csv.DictReader((root / "docs/evidence/assembly-001/BIE_REPO_ASSEMBLY_FILE_MANIFEST_001.csv").open()))
    inventory = json.loads((root / "docs/evidence/assembly-001/BIE_REPO_ASSEMBLY_INVENTORY_001.json").read_text())
    for a in inventory["archives"]:
        if a["archive"] not in raw_archives or digest(raw_archives[a["archive"]]) != a["sha256"]:
            errors.append("Assembly-001 archive missing or mismatched: " + a["archive"])
    for item in initial:
        row = by_key.get((item["archive"], item["source_path"]))
        if not row or row["sha256"] != item["sha256"] or row["bytes"] != item["bytes"]:
            errors.append("Assembly-001 row mismatch: " + item["source_path"])
    schema = json.loads((root / "schemas/canonical-monorepo.json").read_text())
    for path in schema["required_directories"]:
        if not (root / path).is_dir(): errors.append("Required directory absent: " + path)
    for path in schema["required_files"]:
        if not (root / path).is_file(): errors.append("Required file absent: " + path)
    working = list((root / "bie").rglob("*.py")) + list((root / "tests").rglob("*.py"))
    for p in working:
        try:
            tree = ast.parse(p.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app.bie") and "test_grounded_integration" not in p.name:
                    errors.append("Legacy production import: " + p.relative_to(root).as_posix())
        except SyntaxError as exc:
            errors.append(f"Syntax error in {p}: {exc}")
    return {"passed": not errors, "errors": sorted(set(errors)), "archive_count": len(original) + len(supplemental), "original_member_files_checked": original_checked, "ledger_rows": len(rows), "assembly_001_files_checked": len(initial), "dispositions": dict(Counter(x["disposition"] for x in rows)), "canonical_destinations_checked": len(verified_paths), "working_python_files_parsed": len(working), "acceptance": "NOT_ACCEPTED", "scope": "Source preservation, canonical layout, import syntax and manifest integrity; not real-book E2E"}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--output", default="validation/canonical_integrity.json"); args = parser.parse_args()
    result = audit()
    p = ROOT / args.output; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
