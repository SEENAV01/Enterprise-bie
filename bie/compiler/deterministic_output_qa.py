"""QA-003: repeated generation with exact file bytes and controlled input identity.

In-process generators are trusted application callbacks, not sandboxed user code.
The supplied QA CLI also repeats generation in independent Python processes.
MP4 hashes are deliberately not used as a proxy for scene/frame determinism.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Callable, Iterable
import json
import os
import tempfile
from .qa_common import CompilerQAError, QAFinding, digest, ordered_findings, source_files
from .artifact_hashing import safe_relative, require_sha256, confined_path
from .render_process import run_bounded_process

@dataclass(frozen=True)
class DeterminismContext:
    input_sha256: str
    compiler_version: str
    seed: int
    dependency_identity: str
    adapter_identity: str
    def __post_init__(self):
        from .qa_common import token
        require_sha256(self.input_sha256)
        require_sha256(self.dependency_identity)
        require_sha256(self.adapter_identity)
        token(self.compiler_version, "compiler_version")
        if type(self.seed) is not int:
            raise CompilerQAError("seed must be an integer")

@dataclass(frozen=True)
class GeneratedSnapshot:
    files: tuple[tuple[str, str, int], ...]
    files_sha256: str
    context_sha256: str
    bound_sha256: str


def snapshot_generated(files: Iterable, context: DeterminismContext) -> GeneratedSnapshot:
    entries = tuple((p, h, len(c.encode("utf-8"))) for p, c, h in source_files(files))
    tree = digest(entries)
    ctx = digest(asdict(context))
    return GeneratedSnapshot(entries, tree, ctx, digest({"files_sha256": tree, "context_sha256": ctx}))


def snapshot_directory(root: Path, context: DeterminismContext, *,
                       max_files: int = 5000, max_total_bytes: int = 64 * 1024 * 1024) -> GeneratedSnapshot:
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise CompilerQAError("snapshot root must be a non-symlink directory")
    files = []
    total = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise CompilerQAError("symlink in generated tree")
        if path.is_dir():
            continue
        if not path.is_file():
            raise CompilerQAError("nonregular generated file")
        relative = safe_relative(path.relative_to(root).as_posix())
        size = path.stat().st_size
        total += size
        if len(files) >= max_files or total > max_total_bytes:
            raise CompilerQAError("generated snapshot budget exceeded")
        data = path.read_bytes()
        if len(data) != size:
            raise CompilerQAError("generated file changed during snapshot")
        files.append((relative, sha256(data).hexdigest(), size))
    if not files:
        raise CompilerQAError("empty generated tree")
    entries = tuple(files)
    tree, ctx = digest(entries), digest(asdict(context))
    return GeneratedSnapshot(entries, tree, ctx, digest({"files_sha256": tree, "context_sha256": ctx}))

@dataclass(frozen=True)
class DeterministicOutputReceipt:
    runs_requested: int
    runs_completed: int
    snapshots: tuple[GeneratedSnapshot, ...]
    findings: tuple[QAFinding, ...]
    passed: bool
    execution_kind: str
    output_scope: str = "GENERATED_SOURCE_BYTES_NOT_VIDEO_FRAMES"
    accepted: bool = False


def compare_snapshots(snapshots: Iterable[GeneratedSnapshot], *, expected_runs: int,
                      execution_kind: str = "IN_PROCESS_REAL_GENERATOR") -> DeterministicOutputReceipt:
    if type(expected_runs) is not int or not 2 <= expected_runs <= 100:
        raise CompilerQAError("expected_runs must be 2..100")
    snapshots = tuple(snapshots)
    findings = []
    if len(snapshots) != expected_runs:
        findings.append(QAFinding("DETERMINISM_RUNS_INCOMPLETE", "ERROR", "Not all generation runs completed."))
    for i, snap in enumerate(snapshots):
        if not snap.files or len({x[0] for x in snap.files}) != len(snap.files):
            raise CompilerQAError("invalid or empty snapshot")
        for path, h, size in snap.files:
            safe_relative(path); require_sha256(h)
            if type(size) is not int or size < 0:
                raise CompilerQAError("invalid snapshot byte count")
        require_sha256(snap.context_sha256)
        if (snap.files != tuple(sorted(snap.files)) or digest(snap.files) != snap.files_sha256
                or digest({"files_sha256": snap.files_sha256, "context_sha256": snap.context_sha256}) != snap.bound_sha256):
            raise CompilerQAError("snapshot digest mismatch")
        if i == 0:
            continue
        first = snapshots[0]
        if first.context_sha256 != snap.context_sha256:
            findings.append(QAFinding("DETERMINISM_CONTEXT_MISMATCH", "ERROR", "Input/toolchain/seed/adapter identity differs between runs."))
        left, right = {x[0]: x[1:] for x in first.files}, {x[0]: x[1:] for x in snap.files}
        for path in sorted(left.keys() | right.keys()):
            if path not in left:
                code = "DETERMINISM_FILE_ADDED"
            elif path not in right:
                code = "DETERMINISM_FILE_MISSING"
            elif left[path] != right[path]:
                code = "DETERMINISM_BYTES_CHANGED"
            else:
                continue
            findings.append(QAFinding(code, "ERROR", f"Generated output differs in repeat {i + 1}.", path))
    ordered = ordered_findings(findings)
    return DeterministicOutputReceipt(expected_runs, len(snapshots), snapshots, ordered,
                                       not ordered and len(snapshots) >= 2, execution_kind)


def check_deterministic_generator(generator: Callable[[], Iterable], context: DeterminismContext,
                                  *, runs: int = 3) -> DeterministicOutputReceipt:
    if type(runs) is not int or not 2 <= runs <= 100:
        raise CompilerQAError("runs must be 2..100")
    snapshots, failure = [], None
    for index in range(runs):
        try:
            snapshots.append(snapshot_generated(generator(), context))
        except Exception as exc:
            # A trusted generator can fail in any stage; evidence must retain the failure.
            failure = QAFinding("DETERMINISM_GENERATION_FAILED", "ERROR",
                                f"Run {index + 1}: {type(exc).__name__}: {str(exc).replace(chr(10), ' ') or 'generation failed'}")
            break
    receipt = compare_snapshots(snapshots, expected_runs=runs)
    if failure:
        return DeterministicOutputReceipt(runs, len(snapshots), tuple(snapshots),
                ordered_findings((*receipt.findings, failure)), False, receipt.execution_kind)
    return receipt


def check_subprocess_generator(command_prefix: tuple[str, ...], *, request_file: Path,
                               context: DeterminismContext, working_directory: Path,
                               hash_seeds: tuple[int, ...] = (1, 73, 997),
                               timeout_s: float = 60) -> DeterministicOutputReceipt:
    """Execute a trusted worker as ``prefix request.json output-dir`` in fresh roots.

The worker emits only source artifacts. PYTHONHASHSEED variation checks process-level
ordering behavior. Receipt/log directories are not silently removed from snapshots.
"""
    if not 2 <= len(hash_seeds) <= 20 or len(set(hash_seeds)) != len(hash_seeds):
        raise CompilerQAError("at least two distinct hash seeds are required")
    if not command_prefix or any(not isinstance(x, str) or not x for x in command_prefix):
        raise CompilerQAError("trusted worker command must be an argv tuple")
    if any(type(x) is not int or not 0 <= x <= 4294967295 for x in hash_seeds):
        raise CompilerQAError("invalid PYTHONHASHSEED")
    request_file = Path(request_file).resolve()
    if not request_file.is_file():
        raise CompilerQAError("worker request missing")
    snapshots, failures = [], []
    with tempfile.TemporaryDirectory(prefix="bie-determinism-") as tmp:
        for index, seed in enumerate(hash_seeds):
            out = Path(tmp) / f"run-{index}"
            out.mkdir()
            command = ("env", f"PYTHONHASHSEED={seed}", *command_prefix, str(request_file), str(out))
            process = run_bounded_process(command, cwd=Path(working_directory).resolve(),
                                           timeout_s=timeout_s, max_output_bytes=131072)
            if not process.process.passed or process.outcome != "SUCCEEDED":
                failures.append(QAFinding("DETERMINISM_WORKER_FAILED", "ERROR",
                    f"Worker {index + 1} failed: {process.outcome}; {process.process.stderr[-2000:].replace(chr(10), ' ')}"))
                break
            try:
                snapshots.append(snapshot_directory(out, context))
            except (ValueError, OSError) as exc:
                failures.append(QAFinding("DETERMINISM_WORKER_OUTPUT_INVALID", "ERROR", str(exc)))
                break
    receipt = compare_snapshots(snapshots, expected_runs=len(hash_seeds), execution_kind="FRESH_PROCESS_REAL_GENERATOR")
    return DeterministicOutputReceipt(receipt.runs_requested, receipt.runs_completed, receipt.snapshots,
             ordered_findings((*receipt.findings, *failures)), receipt.passed and not failures, receipt.execution_kind)
