"""Exact follow-on capture evidence amendment; prior ledgers/pins stay sealed.

Only two native failure-observation seams and their exact audit wiring change.
This authenticates active replacements AND exact f9e preimages before the prior
validator checks its historical version. No runtime hash can self-authorize.
"""
from hashlib import sha256, sha1
import json
from pathlib import Path

DOCUMENT = "docs/productization/task036-capture-observation-amendment/AMENDMENT.json"
DOCUMENT_SHA256 = "1526b7588616a16d468e98e8047823a19619fd9bbe555005856f3757b76e1024"
M1_DOCUMENT = "docs/productization/task036-motion-amendment/AMENDMENT.json"
M1_SHA256 = "b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c"
TARGETS = frozenset({"bie/compiler/qa_support/remotion_raster_capture.cjs", "bie/compiler/real_paint.py",
                     "scripts/compiler_cache_source_amendment.py"})
NATIVE_TARGETS = TARGETS - {"scripts/compiler_cache_source_amendment.py"}


def validate(root):
    try:
        from compiler_cache_source_amendment import regular, unique, MANIFEST_SHA, MANIFEST
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular, unique, MANIFEST_SHA, MANIFEST
    root = Path(root).resolve()
    raw = regular(root, DOCUMENT, 16 * 1024).replace(b"\r\n", b"\n")
    if b"\r" in raw or sha256(raw).hexdigest() != DOCUMENT_SHA256:
        raise ValueError("CAPTURE_AMENDMENT_DOCUMENT_IDENTITY")
    doc = json.loads(raw, object_pairs_hook=unique)
    if (set(doc) != {"schema", "authority", "scope", "parent_commit", "parent_tree", "original_m1_sha256",
        "original_manifest_sha256", "replacements", "native_calls_and_limits_unchanged", "product_accepted",
        "independent_review_status"} or doc["schema"] != "bie.task036.capture-observation-source-amendment/1" or
        doc["original_m1_sha256"] != M1_SHA256 or doc["original_manifest_sha256"] != MANIFEST_SHA or
        doc["product_accepted"] is not False or doc["native_calls_and_limits_unchanged"] is not True or
        len(doc["replacements"]) != 3 or {r["path"] for r in doc["replacements"]} != TARGETS):
        raise ValueError("CAPTURE_AMENDMENT_SCOPE")
    for path, expected, budget in ((M1_DOCUMENT, M1_SHA256, 256 * 1024),
            ("manifests/" + MANIFEST, MANIFEST_SHA, 42 * 1024**2)):
        original = regular(root, path, budget).replace(b"\r\n", b"\n")
        if b"\r" in original or sha256(original).hexdigest() != expected:
            raise ValueError("CAPTURE_AMENDMENT_PREVIOUS_IDENTITY")
    for row in doc["replacements"]:
        if set(row) != {"path", "preimage", "original_bytes", "original_sha256", "original_git_blob", "active_bytes", "active_sha256"}:
            raise ValueError("CAPTURE_AMENDMENT_ROW")
        original = regular(root, row["preimage"], 64 * 1024)
        blob = sha1(b"blob " + str(len(original)).encode() + b"\0" + original).hexdigest()
        if len(original) != row["original_bytes"] or sha256(original).hexdigest() != row["original_sha256"] or blob != row["original_git_blob"]:
            raise ValueError("CAPTURE_AMENDMENT_PREIMAGE")
        active = regular(root, row["path"], 64 * 1024).replace(b"\r\n", b"\n")
        if b"\r" in active or len(active) != row["active_bytes"] or sha256(active).hexdigest() != row["active_sha256"]:
            raise ValueError("CAPTURE_AMENDMENT_ACTIVE_BYTES")
    return doc


def authenticated_previous_bytes(root, path, previous_sha256):
    """Exact two-path chain; never an arbitrary source override or wildcard."""
    if path not in NATIVE_TARGETS:
        raise ValueError("CAPTURE_AMENDMENT_UNLISTED_TARGET")
    doc = validate(root)
    row, = [r for r in doc["replacements"] if r["path"] == path]
    if row["original_sha256"] != previous_sha256:
        raise ValueError("CAPTURE_AMENDMENT_PARENT_IDENTITY")
    # Reauthenticate the exact bytes returned, rather than opening a potentially
    # replaced preimage after the earlier validation and trusting that read.
    try:
        from compiler_cache_source_amendment import regular
    except ImportError:
        from scripts.compiler_cache_source_amendment import regular
    original = regular(Path(root).resolve(), row["preimage"], 64 * 1024)
    blob = sha1(b"blob " + str(len(original)).encode() + b"\0" + original).hexdigest()
    if (len(original) != row["original_bytes"] or sha256(original).hexdigest() != previous_sha256
            or blob != row["original_git_blob"]):
        raise ValueError("CAPTURE_AMENDMENT_PREIMAGE")
    return original
