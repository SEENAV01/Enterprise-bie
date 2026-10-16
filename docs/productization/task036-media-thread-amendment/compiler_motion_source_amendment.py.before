"""Exact M1 + Addendum A source amendment; sealed historical ledgers unchanged.

The document hash is a reviewed constant, never computed from current source to
bless it. Both original Git bytes and the exact new implementation are required.
"""
from pathlib import Path
import hashlib
import json
try:
    from compiler_cache_source_amendment import regular, unique, MANIFEST, MANIFEST_SHA
except ImportError:
    from scripts.compiler_cache_source_amendment import regular, unique, MANIFEST, MANIFEST_SHA

DOCUMENT = "docs/productization/task036-motion-amendment/AMENDMENT.json"
DOCUMENT_SHA256 = "b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c"
TARGETS = frozenset("bie/compiler/" + name for name in (
    "animation_behavior.py", "animation_track_compiler.py", "qa_scene_compile.py", "reduced_motion.py"))
ADDITIONS = frozenset("bie/compiler/" + name for name in (
    "governed_motion.py", "governed_motion_emitter.py", "producer_motion_admission.py"))


def sha(value):
    return hashlib.sha256(value).hexdigest()


def lf(value):
    value = value.replace(b"\r\n", b"\n")
    if b"\r" in value:
        raise ValueError("M1_AMENDMENT_NONSTANDARD_NEWLINE")
    return value


def validate(root):
    root = Path(root).resolve()
    sealed_bytes = lf(regular(root, "manifests/" + MANIFEST, 42 * 1024**2))
    if sha(sealed_bytes) != MANIFEST_SHA:
        raise ValueError("M1_AMENDMENT_ORIGINAL_MANIFEST")
    sealed = json.loads(sealed_bytes, object_pairs_hook=unique)
    raw = lf(regular(root, DOCUMENT, 256 * 1024))
    if sha(raw) != DOCUMENT_SHA256:
        raise ValueError("M1_AMENDMENT_DOCUMENT_IDENTITY")
    doc = json.loads(raw, object_pairs_hook=unique)
    if (doc["schema"] != "bie.task036.motion-source-amendment/1" or
        doc["original_manifest_sha256"] != MANIFEST_SHA or
        len(doc["replacements"]) != 4 or
        {r["path"] for r in doc["replacements"]} != TARGETS or
        set(doc["additions"]) != ADDITIONS or doc["product_accepted"] is not False):
        raise ValueError("M1_AMENDMENT_SCOPE")
    for row in doc["replacements"]:
        original = regular(root, row["preimage"], 64 * 1024)
        blob = hashlib.sha1(b"blob " + str(len(original)).encode() + b"\0" + original).hexdigest()
        if len(original) != row["original_bytes"] or sha(original) != row["original_sha256"] or blob != row["original_git_blob"]:
            raise ValueError("M1_AMENDMENT_PREIMAGE")
        active = lf(regular(root, row["path"], 128 * 1024))
        if len(active) != row["active_bytes"] or sha(active) != row["active_sha256"]:
            raise ValueError("M1_AMENDMENT_ACTIVE_BYTES")
    for path, expected in doc["additions"].items():
        active = lf(regular(root, path, 128 * 1024))
        if sha(active) != expected:
            raise ValueError("M1_AMENDMENT_NEW_MODULE_BYTES")
    actual = {p.relative_to(root).as_posix() for p in (root / "bie/compiler").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts}
    if actual != set(doc["compiler_paths"]):
        raise ValueError("M1_AMENDMENT_UNEXPECTED_COMPILER_PATH")
    return sealed, doc


def _redirect(original, current, replacements, *, members):
    result = list(current)
    for row in replacements:
        old = [r for r in original if r["canonical_path"] == row["path"]]
        active = [r for r in result if r["canonical_path"] == row["path"]]
        if len(old) != 1 or active != old or old[0]["canonical_sha256"] != row["original_sha256"]:
            raise ValueError("M1_AMENDMENT_SEALED_ROW")
        new = dict(old[0], canonical_path=row["preimage"])
        if members:
            new.update(state="ARCHIVED_EVIDENCE", transformation="Exact M1/Addendum A versioned compiler seam; sealed original Git preimage retained")
        result = [new if r == old[0] else r for r in result]
    return result


def resolve(root, manifest_path, manifest):
    if manifest_path.name != MANIFEST:
        return manifest, 0
    sealed, doc = validate(root)
    rows = _redirect(sealed["members"], manifest["members"], doc["replacements"], members=True)
    return dict(manifest, members=rows), 4


def resolve_source_members(root, manifest_path, manifest, previous_rows):
    if manifest_path.name != MANIFEST:
        raise ValueError("M1_AMENDMENT_SOURCE_MANIFEST")
    sealed, doc = validate(root)
    if manifest != sealed:
        raise ValueError("M1_AMENDMENT_SOURCE_INVENTORY")
    return _redirect(sealed["source_members"], previous_rows, doc["replacements"], members=False)
