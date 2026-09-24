#!/usr/bin/env python3
"""Apply the verified AUDIO Section 14 payload to the canonical BIE feature branch.

This is an integration adapter, not product acceptance. It never imports or copies
standalone dependency_snapshot content into canonical source.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / ".integration" / "audio-section-14"
TRANSPORT = STAGE / "transport"
EXPECTED_MAIN = "dfc1ef9b59bf7d3a8f099a8ad2fb4a93895257e8"
EXPECTED_PAYLOAD_SHA256 = "2a3dbd4bec30e19c51f2af43263e5b42b0bde9dcf1df8704aae01c86b541c5a6"
EXPECTED_CHECKPOINT = "BIE-AUDIO-H11-001"
MANIFEST_PATH = "docs/evidence/audio-integration-001/INTEGRATION_MANIFEST.json"
BINDING_PATH = ROOT / "docs/evidence/audio-integration-001/CANONICAL_DEPENDENCY_BINDING.json"
FINAL_WORKFLOW_TEMPLATE = STAGE / "audio-section-14-final.yml"
FINAL_WORKFLOW = ROOT / ".github/workflows/audio-section-14.yml"

PROTECTED = [
    ("dir_inherited", "bie/director/contract_validation.py", "efd4ac7cb2667f5f67e8b0ae9bc62b0a60e06004"),
    ("dir_inherited", "bie/director/script_plan.py", "93d5920d20535ea9a7727add67789e70fc84ba96"),
    ("dir_inherited", "bie/director/speech_timing.py", "cb8f894868bafa41e32a7d7f20bc24b6348f7400"),
    ("dir_inherited", "bie/director/timing_contract.py", "fb2935e52c6939412a38fed5b5e785a885be79f5"),
    ("dir_inherited", "bie/director/voiceover_generation.py", "de36162cc46a5451f5bac7085daa3fdd9cb1369b"),
    ("durable_canonical", "bie/director/director_durable_recovery.py", "a06ca9bb25fd3492e1d053fcc88f97449675c646"),
    ("durable_canonical", "bie/director/director_artifacts.py", "441a0948319ff331e4218670cb11259f1296139a"),
    ("durable_canonical", "bie/bie_core/artifact_contracts.py", "7d7bf7944ff2f3cb1121b38399652a968b89a0b5"),
    ("durable_canonical", "bie/infrastructure/artifact_store.py", "5ab0fbf90e6981585fdd4dfbe6aa6ddc6ebfa2f4"),
    ("durable_canonical", "bie/infrastructure/idempotency_store.py", "bbfa38c261e67d142ad96ee96baebdc211b21507"),
    ("compiler_canonical", "bie/compiler/artifact_hashing.py", "50303c4228dc0d5388928f0240206000f44f45d8"),
    ("compiler_canonical", "bie/compiler/build_common.py", "574b1a26dc3a3eb6dbd6a58eb8b70f721e72b305"),
    ("compiler_canonical", "bie/compiler/host_toolchain.py", "9c113ec948a9324cf76032f2de937a6ae27e8cf5"),
    ("compiler_canonical", "bie/compiler/linux_worker.py", "c73f537dc0945bb691d40b75a68d7dafa55928ab"),
    ("compiler_canonical", "bie/compiler/namespace_launcher.py", "c2c7fd2a52682aca5af8cc1e333d8402e80cf32c"),
    ("compiler_canonical", "bie/compiler/qa_common.py", "94f6ac7c55d5ba4752c65fc0c1e0dbb27d91a6be"),
    ("compiler_canonical", "bie/compiler/render_logs.py", "d92d279094d9aedd34792525875c1f3d11710165"),
    ("compiler_canonical", "bie/compiler/render_process.py", "b140256eb6eb62cfc4d18dc7142911a5d356020d"),
]

H10_COMPAT = [
    ("bie/compiler/frame_runtime_contract.py", "e8a713f05fe6042b02b712f6f99d1e400d168ab9"),
    ("bie/compiler/narration_consumer.py", "63ce70dc16b304f7c4051bcbd624efda81015e33"),
    ("bie/compiler/qa_scene_compile.py", "10ecd8e7485256b8b3e313c2b4935543544f487c"),
    ("bie/compiler/media_presentation.py", "30f4ce61b968886be4c7b3b540bb8fc92447615e"),
]


def fail(message: str) -> "NoReturn":
    raise SystemExit(message)


def git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if p.returncode:
        fail(f"GIT_FAILED {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout.strip()


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def verify_git_state() -> None:
    branch = git("branch", "--show-current")
    if branch != "integrate/audio-section-14-001":
        fail(f"WRONG_BRANCH:{branch}")
    if not git("merge-base", "--is-ancestor", EXPECTED_MAIN, "HEAD") == "":
        # git merge-base --is-ancestor emits no stdout on success; git() already fails otherwise.
        pass
    changed = set(git("diff", "--name-only", EXPECTED_MAIN, "HEAD").splitlines())
    allowed_prefixes = {".integration/audio-section-14/", ".github/workflows/audio-section-14.yml"}
    unexpected = sorted(p for p in changed if p and not any(p.startswith(a) for a in allowed_prefixes))
    if unexpected:
        fail("UNEXPECTED_PREINTEGRATION_CHANGES:" + ",".join(unexpected))


def verify_protected() -> dict:
    rows = []
    for group, rel, expected_blob in PROTECTED:
        path = ROOT / rel
        if path.is_symlink() or not path.is_file():
            fail("PROTECTED_PATH_INVALID:" + rel)
        data = path.read_bytes()
        actual_blob = blob_sha(data)
        git_blob = git("hash-object", "--", rel)
        if actual_blob != expected_blob or git_blob != expected_blob:
            fail(f"PROTECTED_BLOB_MISMATCH:{rel}:{git_blob}:{expected_blob}")
        rows.append({
            "group": group,
            "path": rel,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "expected_git_blob": expected_blob,
        })
    compat = []
    for rel, expected_blob in H10_COMPAT:
        path = ROOT / rel
        data = path.read_bytes()
        actual_blob = blob_sha(data)
        git_blob = git("hash-object", "--", rel)
        if actual_blob != expected_blob or git_blob != expected_blob:
            fail(f"H10_COMPAT_BLOB_MISMATCH:{rel}:{git_blob}:{expected_blob}")
        compat.append({"path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "expected_git_blob": expected_blob})
    return {"files": rows, "h10_compatibility_files": compat}


def reconstruct_payload() -> bytes:
    parts = sorted(TRANSPORT.glob("part_*.txt"))
    expected_names = [f"part_{i:03d}.txt" for i in range(55)]
    if [p.name for p in parts] != expected_names:
        fail("TRANSPORT_PART_SET_MISMATCH")
    encoded = "".join(p.read_text(encoding="ascii") for p in parts)
    try:
        data = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        fail("TRANSPORT_BASE64_INVALID:" + type(exc).__name__)
    if hashlib.sha256(data).hexdigest() != EXPECTED_PAYLOAD_SHA256:
        fail("PAYLOAD_SHA256_MISMATCH")
    return data


def verify_payload(data: bytes) -> tuple[zipfile.ZipFile, dict]:
    z = zipfile.ZipFile(io.BytesIO(data))
    names = [n for n in z.namelist() if not n.endswith("/")]
    if MANIFEST_PATH not in names:
        fail("INTEGRATION_MANIFEST_MISSING")
    manifest = json.loads(z.read(MANIFEST_PATH))
    if manifest.get("checkpoint") != EXPECTED_CHECKPOINT:
        fail("CHECKPOINT_MISMATCH")
    listed = manifest.get("files")
    if type(listed) is not dict:
        fail("MANIFEST_FILE_MAP_INVALID")
    expected = set(listed) | {MANIFEST_PATH}
    if set(names) != expected or len(names) != len(expected):
        fail("PAYLOAD_FILE_SET_MISMATCH")
    for name, meta in listed.items():
        b = z.read(name)
        if len(b) != meta.get("bytes") or hashlib.sha256(b).hexdigest() != meta.get("sha256"):
            fail("PAYLOAD_FILE_IDENTITY_MISMATCH:" + name)
    for name in names:
        parts = Path(name).parts
        if "__pycache__" in parts or name.endswith(".pyc") or parts[0] in {"dependency_snapshot", "lineage", "history"}:
            fail("FORBIDDEN_PAYLOAD_PATH:" + name)
    return z, manifest


def copy_payload(z: zipfile.ZipFile, manifest: dict) -> None:
    names = sorted(set(manifest["files"]) | {MANIFEST_PATH})
    for rel in names:
        target = ROOT / rel
        if target.exists():
            fail("PAYLOAD_TARGET_ALREADY_EXISTS:" + rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(z.read(rel))


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        fail(f"PATCH_ANCHOR_MISMATCH:{path.relative_to(ROOT)}:{text.count(old)}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def patch_canonical_test_discovery() -> None:
    p = ROOT / "scripts/test_enterprise.py"
    replace_once(
        p,
        "for family in ('visual_intelligence', 'animation_intelligence', 'scene_ir', 'compiler', 'post_dir'):\n",
        "for family in ('visual_intelligence', 'animation_intelligence', 'scene_ir', 'compiler', 'post_dir', 'audio'):\n",
    )
    replace_once(
        p,
        '            if path.is_relative_to(ROOT / "tests/compiler"):\n                module.__package__ = "tests.compiler"\n',
        '            if path.is_relative_to(ROOT / "tests/compiler"):\n                module.__package__ = "tests.compiler"\n            if path.is_relative_to(ROOT / "tests/audio"):\n                module.__package__ = "tests.audio"\n',
    )


def canonical_verify_snippet(indent: str = "    ") -> str:
    return (
        f'{indent}binding=ROOT/"docs/evidence/audio-integration-001/CANONICAL_DEPENDENCY_BINDING.json"\n'
        f'{indent}snapshot=ROOT/"dependency_snapshot"\n'
        f'{indent}if binding.is_file() and not snapshot.exists():\n'
        f'{indent}    manifest=json.loads(binding.read_text())\n'
        f'{indent}    for row in manifest["files"]:\n'
        f'{indent}        path=ROOT/row["path"]\n'
        f'{indent}        if path.is_symlink() or not path.is_file():raise ValueError("CANONICAL_DEPENDENCY_PATH")\n'
        f'{indent}        data=path.read_bytes();blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\\0"+data).hexdigest()\n'
        f'{indent}        if len(data)!=row["bytes"] or hashlib.sha256(data).hexdigest()!=row["sha256"] or blob!=row["expected_git_blob"]:raise ValueError("CANONICAL_DEPENDENCY_IDENTITY")\n'
        f'{indent}    return\n'
    )


def patch_snapshot_verifiers() -> None:
    for rel in ("scripts/audio_kernel.py", "scripts/audio_durable.py"):
        p = ROOT / rel
        replace_once(p, "def verify_dependencies():\n", "def verify_dependencies():\n" + canonical_verify_snippet())


def patch_integration_tests() -> None:
    p = ROOT / "tests/audio/test_audio_batch001_integration.py"
    replace_once(
        p,
        "        root=Path(__file__).resolve().parents[2];m=json.loads((root/'DEPENDENCY_SNAPSHOT.json').read_text())\n        for item in m['files']:\n            b=(root/'dependency_snapshot'/item['path']).read_bytes();self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\\0'+b).hexdigest(),item['expected_git_blob'])\n",
        "        root=Path(__file__).resolve().parents[2];m=json.loads((root/'docs/evidence/audio-integration-001/CANONICAL_DEPENDENCY_BINDING.json').read_text())\n        rows=[x for x in m['files'] if x['group']=='dir_inherited'];self.assertEqual(len(rows),5)\n        for item in rows:\n            b=(root/item['path']).read_bytes();self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\\0'+b).hexdigest(),item['expected_git_blob'])\n",
    )

    p = ROOT / "tests/audio/test_audio_h3_001.py"
    replace_once(
        p,
        "        m=json.loads((root/'CANONICAL_AUDIO_DEPENDENCIES.json').read_text())\n        self.assertEqual(len(m['files']),5)\n        for row in m['files']:\n",
        "        m=json.loads((root/'docs/evidence/audio-integration-001/CANONICAL_DEPENDENCY_BINDING.json').read_text())\n        rows=[x for x in m['files'] if x['group']=='durable_canonical'];self.assertEqual(len(rows),5)\n        for row in rows:\n",
    )

    p = ROOT / "tests/audio/test_audio_h4r_005.py"
    replace_once(
        p,
        "        rows=sum(len(json.loads((ROOT/n).read_text())['files']) for n in ('DEPENDENCY_SNAPSHOT.json','CANONICAL_AUDIO_DEPENDENCIES.json','CANONICAL_AUDIO_KERNEL_DEPENDENCIES.json'))\n        self.assertEqual(rows,18)\n",
        "        binding=json.loads((ROOT/'docs/evidence/audio-integration-001/CANONICAL_DEPENDENCY_BINDING.json').read_text())\n        self.assertEqual(len(binding['files']),18)\n",
    )


def write_binding(binding: dict) -> None:
    payload = {
        "schema_version": "bie.audio.canonical-dependency-binding/1",
        "canonical_repository": "SEENAV01/Enterprise-bie",
        "canonical_main": EXPECTED_MAIN,
        "checkpoint": EXPECTED_CHECKPOINT,
        "standalone_dependency_snapshot_copied": False,
        "files": binding["files"],
        "h10_compatibility_files": binding["h10_compatibility_files"],
        "product_accepted": False,
    }
    BINDING_PATH.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def finalize_workflow_and_remove_transport() -> None:
    if not FINAL_WORKFLOW_TEMPLATE.is_file():
        fail("FINAL_WORKFLOW_TEMPLATE_MISSING")
    FINAL_WORKFLOW.write_bytes(FINAL_WORKFLOW_TEMPLATE.read_bytes())
    shutil.rmtree(STAGE)


def main() -> int:
    verify_git_state()
    binding = verify_protected()
    data = reconstruct_payload()
    z, manifest = verify_payload(data)
    copy_payload(z, manifest)
    write_binding(binding)
    patch_canonical_test_discovery()
    patch_snapshot_verifiers()
    patch_integration_tests()
    finalize_workflow_and_remove_transport()
    # Explicit no-overwrite boundaries.
    forbidden = ["apps/android", "apps/api"]
    changed = git("diff", "--name-only").splitlines()
    if any(any(p == f or p.startswith(f + "/") for f in forbidden) for p in changed):
        fail("ANDROID_OR_API_MODIFIED")
    print(json.dumps({
        "checkpoint": EXPECTED_CHECKPOINT,
        "payload_sha256": EXPECTED_PAYLOAD_SHA256,
        "payload_files": len(manifest["files"]) + 1,
        "protected_files_verified": len(binding["files"]),
        "h10_compatibility_files_verified": len(binding["h10_compatibility_files"]),
        "canonical_audio_test_discovery_enabled": True,
        "dependency_snapshot_copied": False,
        "product_accepted": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())