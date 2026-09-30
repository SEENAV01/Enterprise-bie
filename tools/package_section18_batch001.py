from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = (2026, 9, 30, 0, 0, 0)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def write_zip(path: Path, files: dict[str, bytes]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", allowZip64=True) as z:
        for name in sorted(files):
            pp = PurePosixPath(name)
            if pp.is_absolute() or ".." in pp.parts or "\\" in name:
                raise ValueError("unsafe zip path")
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise RuntimeError("zip CRC verification failed")
        if len(z.namelist()) != len(set(z.namelist())):
            raise RuntimeError("duplicate zip member")


def manifest(rows: dict[str, bytes]):
    return {
        "schema_version": "bie.section18.package-manifest/1",
        "files": {
            name: {"size_bytes": len(data), "sha256": sha(data)}
            for name, data in sorted(rows.items())
        },
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence-dir", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--base-sha", required=True)
    args = p.parse_args()
    evidence = Path(args.evidence_dir).resolve()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    registry = json.loads((ROOT / "metadata/section18/BATCH001_TASKS.json").read_text())
    test_result = json.loads((evidence / "TEST_RESULT.json").read_text())
    if not test_result["all_passed"]:
        raise SystemExit("refusing to package failing tests")
    records = test_result["records"]

    atomics = []
    for task in registry["tasks"]:
        module = Path(task["test_file"]).stem
        selected = [r for r in records if f".{module}." in r["test_id"]]
        if not selected or any(r["status"] != "PASS" for r in selected):
            raise SystemExit(f"task test evidence missing or failing: {task['task_id']}")
        rows = {}
        for rel in sorted(set(task["source_files"] + task["support_files"] + [task["test_file"]])):
            rows[rel] = (ROOT / rel).read_bytes()
        spec = ROOT / "docs/section18/tasks" / f"{task['task_id']}.md"
        rows["docs/SPEC.md"] = spec.read_bytes()
        task_result = {
            "schema_version": "bie.atomic-task-result/1",
            "section": 18,
            "batch": "001",
            "task_id": task["task_id"],
            "original_capability": task["original_capability"],
            "canonical_base_commit": args.base_sha,
            "implementation_status": "IMPLEMENTED_LOCAL_VERIFIED",
            "selected_test_count": len(selected),
            "selected_tests_passed": len(selected),
            "section_complete": False,
            "product_accepted": False,
            "github_integration_performed_by_this_package": False,
        }
        rows["TASK_RESULT.json"] = (json.dumps(task_result, indent=2) + "\n").encode()
        rows["TEST_RESULT.json"] = (json.dumps({
            "task_id": task["task_id"], "records": selected, "all_passed": True
        }, indent=2) + "\n").encode()
        rows["TEST_RESULT.txt"] = ("\n".join(f"PASS {r['test_id']}" for r in selected) + "\n").encode()
        rows["MANIFEST.json"] = (json.dumps(manifest(rows), indent=2) + "\n").encode()
        atomic_name = task["task_id"].replace("-", "_") + ".zip"
        atomic_path = output / "atomics" / atomic_name
        write_zip(atomic_path, rows)
        atomics.append({
            "task_id": task["task_id"],
            "filename": f"atomics/{atomic_name}",
            "size_bytes": atomic_path.stat().st_size,
            "sha256": file_sha(atomic_path),
            "selected_test_count": len(selected),
        })

    combined = {}
    for rel_root in ("bie/app_product", "tests/section18", "docs/section18", "metadata/section18"):
        for path in sorted((ROOT / rel_root).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                combined[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for tool in ("tools/run_section18_batch001_tests.py", "tools/package_section18_batch001.py", "tools/verify_section18_batch001.py"):
        combined[tool] = (ROOT / tool).read_bytes()
    combined["MANIFEST.json"] = (json.dumps(manifest(combined), indent=2) + "\n").encode()
    combined_zip = output / "BIE_APP_SECTION18_BATCH001_COMBINED_SOURCE.zip"
    write_zip(combined_zip, combined)

    continuation = {
        "schema_version": "bie.section18.continuation/1",
        "section": 18,
        "canonical_base_commit": args.base_sha,
        "completed_original_task_ids": [x["task_id"] for x in registry["tasks"]],
        "completed_original_task_count": 10,
        "original_task_count": 33,
        "next_task_ids": registry["next_batch_task_ids"],
        "section_complete": False,
        "hardening_started": False,
        "github_integration_performed": False,
        "task028": "PAUSED",
        "final_package_requirement": "After all original tasks plus justified hardening/re-audit, combine every batch, atomic ZIP, source, tests, evidence, manifests and continuation into one Section 18 master.",
    }
    report = f"""# BIE Section 18 — Batch 001 verified delivery

Canonical base: {args.base_sha}

Implemented original tasks: 10/33.
Test methods: {test_result['tests_run']}; passed: {test_result['passed']}; failures/errors/skips: {test_result['failed']}/{test_result['errors']}/{test_result['skipped']}.

The batch reuses canonical persisted PDF jobs, queues, CAS and graph types. It does not
claim Section 18 completion, product acceptance, production deployment, running-task
preemption, authentication or completion of the remaining 23 original tasks.

Next batch: {", ".join(registry["next_batch_task_ids"])}.
"""
    master_rows = {}
    for path in sorted((output / "atomics").glob("*.zip")):
        master_rows[f"atomics/{path.name}"] = path.read_bytes()
    master_rows["combined/BIE_APP_SECTION18_BATCH001_COMBINED_SOURCE.zip"] = combined_zip.read_bytes()
    master_rows["evidence/TEST_RESULT.json"] = (evidence / "TEST_RESULT.json").read_bytes()
    master_rows["evidence/TEST_RESULT.txt"] = (evidence / "TEST_RESULT.txt").read_bytes()
    master_rows["evidence/INVENTORY.json"] = (evidence / "INVENTORY.json").read_bytes()
    master_rows["TASK_REGISTRY.json"] = (ROOT / "metadata/section18/BATCH001_TASKS.json").read_bytes()
    master_rows["CONTINUATION.json"] = (json.dumps(continuation, indent=2) + "\n").encode()
    master_rows["REPORT.md"] = report.encode()
    master_rows["ATOMIC_INDEX.json"] = (json.dumps(atomics, indent=2) + "\n").encode()
    master_rows["MANIFEST.json"] = (json.dumps(manifest(master_rows), indent=2) + "\n").encode()

    master = output / "BIE_APP_SECTION18_BATCH001_MASTER_PACKAGE.zip"
    write_zip(master, master_rows)

    sums = []
    for path in sorted(output.rglob("*.zip")):
        sums.append(f"{file_sha(path)}  {path.relative_to(output).as_posix()}")
    (output / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
    (output / "CONTINUATION.json").write_text(json.dumps(continuation, indent=2) + "\n")
    (output / "REPORT.md").write_text(report)
    (output / "ATOMIC_INDEX.json").write_text(json.dumps(atomics, indent=2) + "\n")
    print(json.dumps({
        "atomic_count": len(atomics),
        "master": master.name,
        "master_sha256": file_sha(master),
        "combined_source": combined_zip.name,
        "tests": test_result["tests_run"],
        "passed": test_result["passed"],
    }, indent=2))


if __name__ == "__main__":
    main()
