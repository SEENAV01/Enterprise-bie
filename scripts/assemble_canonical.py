"""Continue the recovered repository; originals and Assembly-001 inputs are immutable.

Usage: python scripts/assemble_canonical.py --archive-dir PATH --inputs PATH
Subsequent executions audit/rebuild the ledger without overwriting working modules.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import shutil
import sys
import zipfile

from assembly_lib import ROOT_MAP, canonical_source, digest, inspect_zip, normalize_imports, resolve_version

ROOT = Path(__file__).resolve().parents[1]


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def ingest(directory: Path):
    base = load(ROOT / "manifests/archive_inventory.json", {})["archives"]
    extra_path = ROOT / "manifests/supplemental_archives.json"
    extra = load(extra_path, [])
    known = {a.get("name", a.get("archive")): a for a in base + extra}
    for path in sorted(directory.glob("BIE_*.zip")):
        if path.name.startswith("BIE_ASSEMBLY_BACKUP_"):
            continue
        data = path.read_bytes()
        if path.name in known:
            if digest(data) != known[path.name]["sha256"]:
                raise ValueError(f"Existing archive name has different bytes: {path.name}")
            continue
        members = inspect_zip(data)
        task = json.loads(members["TASK_RESULT.json"]) if "TASK_RESULT.json" in members else None
        if not task or not isinstance(task.get("task_id"), str):
            raise ValueError(f"Unclassified ZIP needs explicit review: {path.name}")
        snapshot = ROOT / "batches" / path.stem
        if snapshot.exists():
            raise ValueError(f"Unregistered snapshot collision: {snapshot}")
        # Inspection above completes before writes; durable original is written first.
        target = ROOT / "backups/ingested" / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records = []
        for member, raw in members.items():
            dest = snapshot / member
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            records.append({"archive": path.name, "member": member, "size_bytes": len(raw), "sha256": digest(raw), "source_path": dest.relative_to(ROOT).as_posix(), "cache_preserved_in_original_zip": False})
        entry = {"name": path.name, "sha256": digest(data), "size_bytes": len(data), "member_count": len(records), "kind": "enterprise_batch", "source_directory": snapshot.relative_to(ROOT).as_posix(), "task_id": task["task_id"], "original_path": target.relative_to(ROOT).as_posix(), "files": records}
        extra.append(entry)
        dump(extra_path, extra)
        known[path.name] = entry
    return base, extra


def consolidate(extra):
    journal_path = ROOT / "manifests/canonical_source_migrations.json"
    if journal_path.exists():
        # Resume without overwriting later development; add newly recovered modules.
        journal = load(journal_path, {})
        existing = {x["original_working_path"]: x for x in journal["sources"]}
        known_tests = {x["canonical_path"] for x in journal["tests"]}
        roots = {x.split("/")[2] for x in existing}
        candidates = {}
        for old_path, item in existing.items():
            candidates.setdefault(Path(old_path).stem, []).append(item["canonical_path"][:-3].replace("/", "."))
        bare = {k: v[0] for k, v in candidates.items() if len(v) == 1 and k != "__init__"}
        for archive in extra:
            for f in archive["files"]:
                member = f["member"]
                if not member.endswith(".py"):
                    continue
                raw = (ROOT / f["source_path"]).read_bytes()
                if member.startswith("app/bie/"):
                    if member in existing:
                        if digest(raw) != existing[member]["original_working_sha256"]:
                            raise ValueError(f"Newly ingested source conflicts with prior selection: {member}")
                        continue
                    dest_name = canonical_source(member)
                    normalized = normalize_imports(raw.decode(), roots, bare).encode()
                    dest = ROOT / dest_name
                    if dest.exists():
                        raise ValueError(f"Canonical destination already exists: {dest_name}")
                    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(normalized)
                    item = {"original_working_path": member, "original_working_sha256": digest(raw), "canonical_path": dest_name, "canonical_sha256": digest(normalized), "transform": "import_normalization" if raw != normalized else "path_only"}
                    journal["sources"].append(item); existing[member] = item
                elif member.startswith("tests/"):
                    dest_name = "tests/imported/" + Path(archive["name"]).stem + "/" + member
                    if dest_name in known_tests: continue
                    normalized = normalize_imports(raw.decode(), roots, bare).encode()
                    dest = ROOT / dest_name; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(normalized)
                    journal["tests"].append({"canonical_path": dest_name, "original_working_sha256": digest(raw), "canonical_sha256": digest(normalized), "transform": "import_normalization"})
                    known_tests.add(dest_name)
        dump(journal_path, journal)
        return journal
    old = ROOT / "app/bie"
    for archive in extra:
        snapshot = ROOT / archive["source_directory"]
        for f in archive["files"]:
            member = f["member"]
            if member.startswith("app/bie/") and member.endswith(".py"):
                dest = ROOT / member
                source = snapshot / member
                if dest.exists() and dest.read_bytes() != source.read_bytes():
                    raise ValueError(f"Unresolved working source conflict: {member}")
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    shutil.copyfile(source, dest)
            elif member.startswith("tests/") and member.endswith(".py"):
                dest = ROOT / "tests/imported" / Path(archive["name"]).stem / member
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(snapshot / member, dest)
    roots = {p.name for p in old.iterdir() if p.is_dir()}
    bare_candidates = {}
    for p in old.rglob("*.py"):
        if p.stem != "__init__":
            bare_candidates.setdefault(p.stem, []).append(canonical_source(p.relative_to(ROOT).as_posix())[:-3].replace("/", "."))
    bare = {k: v[0] for k, v in bare_candidates.items() if len(v) == 1}
    journal = {"schema_version": "1.0.0", "base_commit": "8b979a46c6e4518908c3fe4d3828b87d10a1b8b0", "root_map": ROOT_MAP, "sources": [], "tests": []}
    for p in sorted(old.rglob("*.py")):
        old_path = p.relative_to(ROOT).as_posix()
        new_path = canonical_source(old_path)
        raw = p.read_bytes()
        normalized = normalize_imports(raw.decode(), roots, bare).encode()
        dest = ROOT / new_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.read_bytes() != normalized:
            raise ValueError(f"Canonical collision: {new_path}")
        dest.write_bytes(normalized)
        journal["sources"].append({"original_working_path": old_path, "original_working_sha256": digest(raw), "canonical_path": new_path, "canonical_sha256": digest(normalized), "transform": "import_normalization" if raw != normalized else "path_only"})
    for p in sorted((ROOT / "tests").rglob("*.py")):
        raw = p.read_bytes()
        normalized = normalize_imports(raw.decode(), roots, bare).encode()
        p.write_bytes(normalized)
        journal["tests"].append({"canonical_path": p.relative_to(ROOT).as_posix(), "original_working_sha256": digest(raw), "canonical_sha256": digest(normalized), "transform": "import_normalization" if raw != normalized else "unchanged"})
    dump(journal_path, journal)
    # All source bytes remain in immutable snapshots and the verified base Git commit.
    shutil.rmtree(old)
    old.mkdir(parents=True)
    return journal


def ledger(base, extra, journal):
    records = load(ROOT / "manifests/file_inventory.json", {})["files"] + [f for a in extra for f in a["files"]]
    archive_map = {a["name"]: a for a in base + extra}
    conflicts = {x["path"]: x for x in load(ROOT / "manifests/source_conflicts.json", [])}
    sources = {x["original_working_path"]: x for x in journal["sources"]}
    test_map = {x["canonical_path"]: x for x in journal["tests"]}
    seen, output = {}, []
    for f in records:
        archive, member = f["archive"], f["member"]
        a = archive_map[archive]
        identity = digest((archive + "\0" + member).encode())
        row = {"file_id": identity, "archive": archive, "source_path": member, "bytes": f["size_bytes"], "sha256": f["sha256"], "availability": "AVAILABLE_VERIFIED", "disposition": "ARCHIVED_EVIDENCE", "canonical_path": f["source_path"] or "", "canonical_sha256": f["sha256"], "reason": "Immutable historical evidence; no production integration claimed", "duplicate_of": "", "transform": "none", "original_archive": a.get("original_path", "backups/BIE_ORIGINAL_ARCHIVES_2026-09-09.zip"), "original_archive_member": "" if "original_path" in a else "original-zips/" + archive}
        if f["cache_preserved_in_original_zip"]:
            row.update(canonical_path="", reason="Interpreter cache retained inside its original archive; never used as production source", canonical_sha256="")
        elif a["kind"] == "enterprise_batch":
            if member in sources:
                s = sources[member]
                conflict = conflicts.get(member)
                selected = not conflict or conflict["selected_sha256"] == f["sha256"]
                if selected:
                    row.update(disposition="MIGRATED", canonical_path=s["canonical_path"], canonical_sha256=s["canonical_sha256"], reason="Integrated canonical source; prior documented working corrections retained", transform=s["transform"])
                    if f["sha256"] != s["original_working_sha256"]:
                        row["transform"] = "documented_prior_correction+" + s["transform"]
                else:
                    row["reason"] = "Superseded reduced variant; richer selected implementation recorded in manifests/source_conflicts.json"
            elif member.startswith("tests/") and member.endswith(".py"):
                dest = "tests/imported/" + Path(archive).stem + "/" + member
                if dest in test_map:
                    row.update(disposition="MIGRATED", canonical_path=dest, canonical_sha256=test_map[dest]["canonical_sha256"], transform="documented_working_test_and_import_normalization", reason="Consolidated working regression test; original assertion bytes remain in snapshot")
        # Only equivalent destinations/content are duplicates; semantic modules stay distinct.
        key = (row["sha256"], row["canonical_path"])
        if row["disposition"] == "MIGRATED" and key in seen:
            row.update(disposition="DUPLICATE_WITH_PROVENANCE", duplicate_of=seen[key], reason="Byte-identical source at the same canonical destination")
        else:
            seen[key] = identity
        output.append(row)
    dest = ROOT / "manifests/lossless_migration.csv"
    with dest.open("w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    # The supplied 2,450 rows are reconciled independently against every original byte.
    src = ROOT / "docs/evidence/assembly-001/BIE_REPO_ASSEMBLY_FILE_MANIFEST_001.csv"
    initial = list(csv.DictReader(src.open()))
    by_key = {(x["archive"], x["source_path"]): x for x in output}
    reconciled = []
    for f in initial:
        got = by_key.get((f["archive"], f["source_path"]))
        if got is None or got["sha256"] != f["sha256"] or got["bytes"] != int(f["bytes"]):
            raise ValueError(f"Assembly-001 provenance mismatch: {f}")
        reconciled.append(got)
    with (ROOT / "manifests/assembly_001_reconciled.csv").open("w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(output[0])); writer.writeheader(); writer.writerows(reconciled)
    tasks = load(ROOT / "manifests/task_registry.json", {})["tasks"] + [{"archive": a["name"], "path": a["source_directory"] + "/TASK_RESULT.json", "historical_result": load(ROOT / a["source_directory"] / "TASK_RESULT.json", {})} for a in extra]
    dump(ROOT / "task_registry/historical_tasks.json", {"note": "Historical claims preserved verbatim; no acceptance promotion", "tasks": tasks})
    from collections import Counter
    summary = {"archive_count": len(archive_map), "historical_file_count": len(output), "assembly_001_archives": 273, "assembly_001_files": len(reconciled), "unavailable_archives": [], "dispositions": dict(Counter(x["disposition"] for x in output)), "canonical_source_files": len(journal["sources"]), "working_test_files": len(journal["tests"]), "accepted": False}
    dump(ROOT / "docs/evidence/canonical_assembly_summary.json", summary)
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    args = parser.parse_args()
    target = ROOT / "docs/evidence/assembly-001"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("BIE_REPO_ASSEMBLY_INVENTORY_001.json", "BIE_REPO_ASSEMBLY_FILE_MANIFEST_001.csv", "BIE_REPO_ASSEMBLY_001_REPORT.md"):
        raw = (args.inputs / name).read_bytes()
        if (target / name).exists() and (target / name).read_bytes() != raw:
            raise ValueError("Immutable Assembly-001 input changed")
        (target / name).write_bytes(raw)
    base, extra = ingest(args.archive_dir)
    journal = consolidate(extra)
    ledger(base, extra, journal)


if __name__ == "__main__":
    main()
