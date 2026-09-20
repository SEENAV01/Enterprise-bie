"""H1-005 checked source publication and revalidation for the render CLI.

This is a source-level gate, not product authorization or an untrusted-code sandbox.
No receipt supplied by the caller is trusted in place of recomputing the source.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import json
import os
import tempfile
import shutil
from .artifact_hashing import canonical_json, confined_path
from .qa_common import CompilerQAError, QAFinding, ordered_findings
from .qa_scene_compile import CompilerQATarget, compile_scene_for_qa
from .generated_code_regression import probe_typescript_sources
from .deterministic_codegen import write_codegen_plan

@dataclass(frozen=True)
class CheckedSceneReceipt:
    scene_fingerprint: str
    manifest_sha256: str
    status: str
    source_gate_passed: bool
    findings: tuple[QAFinding, ...]
    parser_status: str
    compiler_version: str
    full_compile_verified: bool = False
    real_render_status: str = "NOT_RUN"
    accepted: bool = False

def compile_scene_checked(payload, *, target: CompilerQATarget | None = None):
    target = target or CompilerQATarget()
    bundle = compile_scene_for_qa(payload, target=target)
    probe = probe_typescript_sources(bundle.codegen.files)
    findings = ordered_findings((*bundle.findings, *probe.findings))
    passed = bundle.source_contract_passed and probe.status == "PASS" and not any(f.severity == "ERROR" for f in findings)
    receipt = CheckedSceneReceipt(bundle.scene_fingerprint, bundle.codegen.manifest_sha256,
                "SOURCE_GATE_PASS_NOT_PRODUCT_ACCEPTED" if passed else "SOURCE_GATE_BLOCKED",
                passed, findings, probe.status, target.compiler_version)
    return bundle, receipt

def publish_checked_scene(payload, destination: Path, *, target: CompilerQATarget | None = None) -> CheckedSceneReceipt:
    target = target or CompilerQATarget()
    bundle, receipt = compile_scene_checked(payload, target=target)
    if not receipt.source_gate_passed:
        raise CompilerQAError("SOURCE_PUBLICATION_BLOCKED: " + ", ".join(f.code for f in receipt.findings if f.severity == "ERROR"))
    destination = Path(destination).absolute()
    # Local trusted working directory only; refuse existing destinations and symlink parents.
    if destination.exists() or destination.is_symlink() or any(p.is_symlink() for p in destination.parents):
        raise CompilerQAError("destination exists or has symlink parents")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".bie-checked-", dir=destination.parent))
    try:
        write_codegen_plan(bundle.codegen, staging)
        envelope = {"schema_version": "bie.checked-scene.v1", "document": payload,
                    "target": asdict(target), "receipt": asdict(receipt), "accepted": False}
        (staging / "CHECKED_SCENE.json").write_bytes(canonical_json(envelope))
        # Avoid overwriting files by reserving the directory name, then replacing our empty reservation.
        destination.mkdir(exist_ok=False)
        try:
            os.replace(staging, destination)
        except BaseException:
            destination.rmdir()
            raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return receipt

def verify_checked_workspace(root: Path, *, expected_scene_fingerprint: str | None = None) -> CheckedSceneReceipt:
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir() or any(p.is_symlink() for p in root.parents):
        raise CompilerQAError("checked workspace must be a regular directory without symlink parents")
    marker = root / "CHECKED_SCENE.json"
    if marker.is_symlink() or not marker.is_file() or marker.stat().st_size > 4 * 1024 * 1024:
        raise CompilerQAError("CHECKED_SCENE_REQUIRED: ungoverned source cannot enter this render path")
    raw = json.loads(marker.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "bie.checked-scene.v1" or raw.get("accepted") is not False:
        raise CompilerQAError("invalid checked-scene schema/acceptance")
    bundle, receipt = compile_scene_checked(raw["document"], target=CompilerQATarget(**raw["target"]))
    if not receipt.source_gate_passed:
        raise CompilerQAError("REVALIDATION_BLOCKED: " + ", ".join(f.code for f in receipt.findings if f.severity == "ERROR"))
    if expected_scene_fingerprint is not None and expected_scene_fingerprint != receipt.scene_fingerprint:
        raise CompilerQAError("scene identity mismatch")
    # Caller-modified receipts cannot fake codegen identity or acceptance.
    if raw.get("receipt") != asdict(receipt):
        # Dataclass tuple findings serialize as a list. Compare canonical JSON instead.
        if canonical_json(raw.get("receipt")) != canonical_json(asdict(receipt)):
            raise CompilerQAError("checked receipt mismatch")
    expected = {f.path: f for f in bundle.codegen.files}
    for rel, f in expected.items():
        path = confined_path(root, rel)
        if not path.is_file() or path.is_symlink() or sha256(path.read_bytes()).hexdigest() != f.sha256:
            raise CompilerQAError("GENERATED_SOURCE_TAMPERED: " + rel)
    # No hidden executable/config/asset may be added between generation and render.
    allowed_extra = {"CHECKED_SCENE.json", "CODEGEN_MANIFEST.json", "package-lock.json", "smoke-request.json", "full-request.json"}
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if rel.parts[0] == "node_modules":
            continue  # Actual pinned dependency verification is a separate full-compile gate.
        if path.is_symlink():
            raise CompilerQAError("workspace symlink forbidden: " + rel.as_posix())
        if path.is_file() and rel.as_posix() not in expected and rel.as_posix() not in allowed_extra:
            raise CompilerQAError("UNINSPECTED_WORKSPACE_FILE: " + rel.as_posix())
    return receipt
