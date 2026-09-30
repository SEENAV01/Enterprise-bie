from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "section18_batch001"
WORK = DIST / "work"
DELIVERY = DIST / "delivery"
BASELINE = "47cafba8975061555764c3c579ae6daad696ae64"
REGISTRY = ROOT / "task_registry" / "section18_batch001.json"
FIXED_ZIP_TIME = (2026, 10, 1, 0, 0, 0)

TASK_DEPENDENCIES = {
    "BIE-APP-RUN-001": [],
    "BIE-APP-RUN-002": ["BIE-APP-RUN-001"],
    "BIE-APP-RUN-003": ["BIE-APP-RUN-002"],
    "BIE-APP-RUN-004": ["BIE-APP-RUN-001", "BIE-APP-RUN-002"],
    "BIE-APP-RUN-005": ["BIE-APP-RUN-004"],
    "BIE-APP-RUN-006": ["BIE-APP-RUN-004"],
    "BIE-APP-RUN-007": ["BIE-APP-RUN-006"],
    "BIE-APP-RUN-008": ["BIE-APP-RUN-004"],
    "BIE-APP-GRAPH-001": [],
    "BIE-APP-GRAPH-002": [],
}

CANONICAL_DEPENDENCIES = [
    "apps/api/job_service.py",
    "bie/infrastructure/artifact_store.py",
    "bie/infrastructure/durable_task_queue.py",
    "bie/infrastructure/idempotency_store.py",
    "bie/infrastructure/persistence.py",
    "bie/knowledge_intelligence/knowledge_graph_query.py",
    "bie/knowledge_intelligence/knowledge_graph_validate.py",
    "bie/prerequisite_intelligence/graph.py",
]

BATCH_INTEGRATION_FILES = [
    "apps/api/section18_operator.py",
    "apps/api/section18_dev_app.py",
    "apps/web/__init__.py",
    "apps/web/section18_views.py",
]

NEW_SOURCE_ROOTS = [
    "bie/product_app_v1",
]

INHERITED_GROUPS = {
    "canonical_pdf_api": ["tests/productization/api/test_pdf_inspection_api.py"],
    "canonical_persistent_jobs": ["tests/productization/api/test_persistent_pdf_jobs.py"],
    "canonical_knowledge_graph_validate": ["tests/imported/BIE_KI_GRAPH_002/tests/test_knowledge_graph_validate.py"],
    "canonical_knowledge_graph_query": ["tests/imported/BIE_KI_GRAPH_008/tests/test_knowledge_graph_query.py"],
    "canonical_prerequisite_graph": ["tests/imported/BIE_PR_006/tests/test_pr_006.py"],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def run_command(argv: list[str], *, timeout: int = 300) -> dict[str, object]:
    start = time.monotonic()
    proc = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    combined = proc.stdout + proc.stderr
    match = re.search(r"Ran (\d+) tests? in ", combined)
    return {
        "argv": argv,
        "exit_code": proc.returncode,
        "duration_seconds": time.monotonic() - start,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "combined": combined,
        "tests_run": int(match.group(1)) if match else None,
    }


def run_test_file(path: str) -> dict[str, object]:
    name = Path(path).name
    return run_command(
        [
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            str(Path(path).parent),
            "-p",
            name,
            "-v",
        ],
        timeout=180,
    )


def safe_clean() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    WORK.mkdir(parents=True)
    DELIVERY.mkdir(parents=True)


def copy_file(src_rel: str, target: Path) -> None:
    src = ROOT / src_rel
    if not src.is_file():
        raise RuntimeError(f"missing file: {src_rel}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)


def manifest_for(root: Path, *, exclude: set[str] | None = None) -> dict[str, dict[str, object]]:
    exclude = exclude or set()
    out = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel in exclude:
            continue
        out[rel] = {"size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
    return out


def write_integrity(root: Path) -> None:
    manifest = manifest_for(root, exclude={"MANIFEST.json", "SHA256SUMS.txt"})
    (root / "MANIFEST.json").write_text(
        json.dumps({"schema_version": "bie.section18.atomic-manifest/1", "files": manifest}, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [f"{row['sha256']}  {name}" for name, row in sorted(manifest.items())]
    (root / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def deterministic_zip(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target, "w", ZIP_DEFLATED, compresslevel=9, allowZip64=True) as z:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(source).as_posix()
            info = ZipInfo(rel, FIXED_ZIP_TIME)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = ZIP_DEFLATED
            z.writestr(info, path.read_bytes())
    with ZipFile(target) as z:
        if len(z.namelist()) != len(set(z.namelist())):
            raise RuntimeError(f"duplicate zip names: {target}")
        bad = z.testzip()
        if bad:
            raise RuntimeError(f"zip crc failure: {target}: {bad}")


def dependency_hashes() -> dict[str, str]:
    return {path: sha256_file(ROOT / path) for path in CANONICAL_DEPENDENCIES}


def task_package(task: dict[str, object], dependency_hash_map: dict[str, str]) -> dict[str, object]:
    task_id = str(task["task_id"])
    stage = WORK / "atomics" / task_id
    stage.mkdir(parents=True)
    test_path = str(task["test"])
    result = run_test_file(test_path)
    (stage / "TEST_RESULT.txt").write_text(result["combined"], encoding="utf-8")
    if result["exit_code"] != 0 or result["tests_run"] is None:
        raise RuntimeError(f"{task_id} tests failed\n{result['combined'][-8000:]}")

    copy_file(str(task["spec"]), stage / "docs" / "SPEC.md")
    copy_file(test_path, stage / "tests" / Path(test_path).name)
    copy_file("tests/section18/batch001_support.py", stage / "tests" / "batch001_support.py")
    for source in task["owned_files"]:
        copy_file(str(source), stage / str(source))

    deps = {
        "schema_version": "bie.section18.atomic-dependencies/1",
        "task_id": task_id,
        "canonical_baseline": BASELINE,
        "task_dependencies": TASK_DEPENDENCIES[task_id],
        "canonical_dependency_sha256": dependency_hash_map,
        "batch_integration_files_not_owned_by_task": BATCH_INTEGRATION_FILES,
        "requires_canonical_checkout_for_execution": True,
    }
    (stage / "DEPENDENCIES.json").write_text(json.dumps(deps, indent=2) + "\n", encoding="utf-8")
    (stage / "PATCH_SCOPE.json").write_text(
        json.dumps(
            {
                "task_id": task_id,
                "owned_files": task["owned_files"],
                "test": test_path,
                "spec": task["spec"],
                "overwrites_canonical_baseline_files": False,
                "github_integrated": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    receipt = {
        "schema_version": "bie.section18.task-result/1",
        "task_id": task_id,
        "capability": task["capability"],
        "classification": "ORIGINAL_REGISTRY_TASK",
        "batch": "001",
        "canonical_baseline": BASELINE,
        "build_commit": os.environ.get("GITHUB_SHA", "LOCAL_BUILD"),
        "status": "IMPLEMENTED_LOCAL_VERIFIED",
        "tests_run": result["tests_run"],
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "task_dependencies": TASK_DEPENDENCIES[task_id],
        "canonical_integration_complete": False,
        "section18_complete": False,
        "product_accepted": False,
        "release_authorized": False,
    }
    (stage / "TASK_RESULT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    write_integrity(stage)
    zip_name = task_id.replace("-", "_") + ".zip"
    target = DELIVERY / "atomics" / zip_name
    deterministic_zip(stage, target)
    return {
        "task_id": task_id,
        "zip": target.relative_to(DELIVERY).as_posix(),
        "sha256": sha256_file(target),
        "size_bytes": target.stat().st_size,
        "tests_run": result["tests_run"],
    }


def collect_source_files(registry: dict[str, object]) -> list[str]:
    paths = set(BATCH_INTEGRATION_FILES)
    for root in NEW_SOURCE_ROOTS:
        for path in (ROOT / root).rglob("*.py"):
            if "__pycache__" not in path.parts:
                paths.add(path.relative_to(ROOT).as_posix())
    for task in registry["tasks"]:
        paths.update(str(x) for x in task["owned_files"])
    return sorted(paths)


def build_master(registry: dict[str, object], atomics: list[dict[str, object]], dependency_hash_map: dict[str, str]) -> tuple[Path, dict[str, object]]:
    master = WORK / "master"
    master.mkdir()
    source_files = collect_source_files(registry)
    for path in source_files:
        copy_file(path, master / path)
    for path in sorted((ROOT / "tests" / "section18").glob("*.py")):
        copy_file(path.relative_to(ROOT).as_posix(), master / path.relative_to(ROOT))
    for path in sorted((ROOT / "docs" / "section18").rglob("*")):
        if path.is_file():
            copy_file(path.relative_to(ROOT).as_posix(), master / path.relative_to(ROOT))
    copy_file("task_registry/section18_batch001.json", master / "task_registry" / "section18_batch001.json")
    for item in atomics:
        copy_file(item["zip"], master / item["zip"])

    full = run_command(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests/section18", "-p", "test_*.py", "-v"],
        timeout=600,
    )
    (master / "evidence" / "BATCH001_TEST_RESULT.txt").parent.mkdir(parents=True, exist_ok=True)
    (master / "evidence" / "BATCH001_TEST_RESULT.txt").write_text(full["combined"], encoding="utf-8")
    if full["exit_code"] != 0 or full["tests_run"] is None:
        raise RuntimeError("Batch 001 suite failed\n" + full["combined"][-12000:])

    inherited = {}
    for name, files in INHERITED_GROUPS.items():
        logs = []
        tests = 0
        for path in files:
            row = run_test_file(path)
            logs.append(row["combined"])
            if row["exit_code"] != 0 or row["tests_run"] is None:
                raise RuntimeError(f"inherited regression failed: {name}\n{row['combined'][-8000:]}")
            tests += int(row["tests_run"])
        inherited[name] = {"tests_run": tests, "failures": 0, "errors": 0, "skipped": 0}
        (master / "evidence" / f"INHERITED_{name}.txt").write_text("\n".join(logs), encoding="utf-8")

    report = f"""# BIE Section 18 — Batch 001 verified delivery

Canonical baseline: `{BASELINE}`

## Original tasks in this batch

""" + "\n".join(
        f"- {row['task_id']} — {row['capability']} — {next(x['tests_run'] for x in atomics if x['task_id']==row['task_id'])} task-specific tests"
        for row in registry["tasks"]
    ) + f"""

## Verification

- Distinct Batch 001 Section 18 test methods: **{full['tests_run']}**
- Failures/errors/skips: **0 / 0 / 0**
- Task-specific atomic ZIPs: **10**
- Canonical API/job and graph regression groups: **{sum(x['tests_run'] for x in inherited.values())} tests**, all passing.
- Source/product layer uses persisted canonical job/queue/CAS/graph state; it does not fabricate stage completion or progress percentages.
- No Section 18 GitHub integration, PR, merge, production deployment or product-acceptance claim is made by this ZIP build.

## Architecture boundary

The operator metadata store is a read-model/control-plane overlay only. Raw source bytes and engine artifacts remain in canonical BIE stores. Batch 001 supports real persisted PDF-job creation/import/status/timeline/failure/retry and safe pre-delivery pause/resume/cancel. In-flight worker termination is intentionally unsupported and fails closed.

The concept and prerequisite viewers validate canonical graph structures and render deterministic accessible SVG/text views without inventing provenance.

## Remaining Section 18 scope

23 original registry tasks remain, followed by completeness audit, justified hardening, re-audit, browser/native verification and governed GitHub integration.
"""
    (master / "REPORT.md").write_text(report, encoding="utf-8")

    continuation = {
        "schema_version": "bie.section18.continuation/1",
        "section": 18,
        "batch_completed": "001",
        "canonical_baseline": BASELINE,
        "completed_original_task_ids": [x["task_id"] for x in registry["tasks"]],
        "next_batch_task_ids": [
            "BIE-APP-GRAPH-003",
            "BIE-APP-LESSON-001","BIE-APP-LESSON-002","BIE-APP-LESSON-003",
            "BIE-APP-LESSON-004","BIE-APP-LESSON-005",
            "BIE-APP-ART-001","BIE-APP-ART-002","BIE-APP-ART-003","BIE-APP-ART-004",
        ],
        "original_section18_tasks_total": 33,
        "original_tasks_completed": 10,
        "original_tasks_remaining": 23,
        "github_integration_started": False,
        "task028": "PAUSED_UNCHANGED",
        "section18_complete": False,
        "final_master_requirement": "At section closure combine every original/hardening atomic ZIP, source, tests, audit/fix evidence, manifests, checksums and integration instructions into one verified master package.",
    }
    (master / "CONTINUATION.json").write_text(json.dumps(continuation, indent=2) + "\n", encoding="utf-8")

    verification = {
        "schema_version": "bie.section18.batch001-verification/1",
        "canonical_baseline": BASELINE,
        "build_commit": os.environ.get("GITHUB_SHA", "LOCAL_BUILD"),
        "batch_tests": {
            "tests_run": full["tests_run"],
            "failures": 0,
            "errors": 0,
            "skipped": 0,
        },
        "atomic_tasks": atomics,
        "inherited_regressions": inherited,
        "canonical_dependency_sha256": dependency_hash_map,
        "new_source_files": source_files,
        "source_files_count": len(source_files),
        "section18_complete": False,
        "product_accepted": False,
        "release_authorized": False,
    }
    (master / "VERIFICATION.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    write_integrity(master)

    master_zip = DELIVERY / "BIE_APP_SECTION18_BATCH001_MASTER_PACKAGE.zip"
    deterministic_zip(master, master_zip)

    source_stage = WORK / "combined_source"
    source_stage.mkdir()
    for path in source_files:
        copy_file(path, source_stage / path)
    for path in sorted((ROOT / "tests" / "section18").glob("*.py")):
        copy_file(path.relative_to(ROOT).as_posix(), source_stage / path.relative_to(ROOT))
    source_zip = DELIVERY / "BIE_APP_SECTION18_BATCH001_COMBINED_SOURCE.zip"
    deterministic_zip(source_stage, source_zip)

    return master_zip, {
        "full_tests": full["tests_run"],
        "inherited": inherited,
        "master_zip_sha256": sha256_file(master_zip),
        "master_zip_size_bytes": master_zip.stat().st_size,
        "source_zip_sha256": sha256_file(source_zip),
        "source_zip_size_bytes": source_zip.stat().st_size,
    }


def finish_delivery(master_meta: dict[str, object], atomics: list[dict[str, object]]) -> None:
    verification = {
        "schema_version": "bie.section18.batch001-delivery/1",
        "canonical_baseline": BASELINE,
        "build_commit": os.environ.get("GITHUB_SHA", "LOCAL_BUILD"),
        "atomic_count": len(atomics),
        "atomics": atomics,
        **master_meta,
        "all_tests_passed": True,
        "section18_complete": False,
        "github_integrated": False,
        "product_accepted": False,
    }
    (DELIVERY / "VERIFICATION.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    (DELIVERY / "CONTINUATION.json").write_text(
        json.dumps(
            {
                "next_batch": "002",
                "next_task_ids": [
                    "BIE-APP-GRAPH-003",
                    "BIE-APP-LESSON-001","BIE-APP-LESSON-002","BIE-APP-LESSON-003",
                    "BIE-APP-LESSON-004","BIE-APP-LESSON-005",
                    "BIE-APP-ART-001","BIE-APP-ART-002","BIE-APP-ART-003","BIE-APP-ART-004",
                ],
                "preserve_batch001": True,
                "final_section18_master_required": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    lines = []
    for path in sorted(DELIVERY.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(f"{sha256_file(path)}  {path.relative_to(DELIVERY).as_posix()}")
    (DELIVERY / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    safe_clean()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if registry["canonical_baseline"] != BASELINE or len(registry["tasks"]) != 10:
        raise RuntimeError("registry baseline/count mismatch")
    dependency_hash_map = dependency_hashes()
    atomics = [task_package(task, dependency_hash_map) for task in registry["tasks"]]
    master_zip, master_meta = build_master(registry, atomics, dependency_hash_map)
    finish_delivery(master_meta, atomics)
    print(json.dumps({
        "status": "PASS",
        "atomic_count": len(atomics),
        "batch_tests": master_meta["full_tests"],
        "inherited_tests": sum(x["tests_run"] for x in master_meta["inherited"].values()),
        "master_zip": master_zip.name,
        "master_sha256": master_meta["master_zip_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
