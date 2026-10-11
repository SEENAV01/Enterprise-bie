"""Exact test-profile compatibility; not a dependency or native-source waiver.

Fixed reviewed replacements are authenticated, never blessed from current bytes.
Only the canonical checkout-history option differs from the original workflow.
The historical map remains authority; a v2 AFTER witness states actual identity.
"""
from hashlib import sha1, sha256
import json
from pathlib import Path
import stat

DIRECTORY = "docs/productization/task036-ci-history-amendment/"
WORKFLOW = ".github/workflows/post-dir-canonical-catchup.yml"
GUARD = "tests/productization/animation/verify_post_dir_provisioning.py"
EXPECTED = {
    "schema": "bie.task036.canonical-history-profile-amendment/1",
    "scope": "EXACT_TEST_PROFILE_CHECKOUT_HISTORY_COMPATIBILITY_ONLY",
    "base": "5b1cafc766c9df9c3e0748f459e6beb9b8f1f243",
    "workflow": {"path": WORKFLOW, "preimage": DIRECTORY + "post-dir-canonical-catchup.yml.before",
        "original_blob": "3f95bbff25fa7e9cd18d054eb5bee04d76933655", "original_bytes": 9418,
        "original_sha256": "22763cd888f9434bd2ad544ab40bf55bfd5837bc87ead3d549012ba33f652e3e",
        "active_blob": "26577340fc2935c169202bf48c622fe0c30c4b99", "active_bytes": 9443,
        "active_sha256": "c35d09469afedc7393ed217bbb87c3fd7fa000a27094d1c21e130cf45b3e4847"},
    "guard": {"path": GUARD, "preimage": DIRECTORY + "verify_post_dir_provisioning.py.before",
        "original_blob": "57d32e0c7b93e2c2c4a71ee05239c3630c21f60f", "original_bytes": 20244,
        "original_sha256": "488673c818ee3eb4d869391e95708ea50ddeaaaad20a5aa543d5cda61e6a5b97"},
    "original_m1_amendment_sha256": "b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c",
    "change": "CANONICAL_CHECKOUT_FETCH_DEPTH_ZERO_ONLY",
    "historical_profile_pins_changed": False, "requirements_installers_changed": False,
    "native_source_changed": False, "mandatory_gates_replaced": False, "product_accepted": False,
}


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("TASK036_PROFILE_DUPLICATE_KEY")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("TASK036_PROFILE_NONFINITE")


def read_regular(root, relative, limit):
    """Fixed checkout-relative files only; reject links and changing reads."""
    root = Path(root).resolve(strict=True)
    parts = Path(relative).parts
    if Path(relative).is_absolute() or any(part in {"..", "."} for part in parts):
        raise ValueError("TASK036_PROFILE_PATH")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("TASK036_PROFILE_LINK")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= limit:
        raise ValueError("TASK036_PROFILE_FILE_BOUND")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino) or len(data) != before.st_size:
        raise ValueError("TASK036_PROFILE_CHANGED_READ")
    return data


def blob(data):
    return sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def witness():
    document = json.dumps(EXPECTED, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"schema": "bie.task036.canonical-history-profile-witness/1",
        "amendment_content_sha256": sha256(document).hexdigest(),
        "historical_workflow_blob": EXPECTED["workflow"]["original_blob"],
        "actual_workflow_blob": EXPECTED["workflow"]["active_blob"],
        "actual_workflow_sha256": EXPECTED["workflow"]["active_sha256"],
        "guard_trust_role": "REVIEWED_GIT_BOOTSTRAP_WITH_SEPARATE_FIXED_SOURCE_ATTESTATION",
        "historical_guard_sha256": EXPECTED["guard"]["original_sha256"],
        "profile_map_role": "HISTORICAL_AUTHORITY_NOT_CURRENT_WORKFLOW_BYTES",
        "change": EXPECTED["change"], "requirements_installers_changed": False,
        "native_source_changed": False, "mandatory_gates_replaced": False,
        "product_accepted": False}


def validate_witness(value):
    expected = witness()
    return (type(value) is dict and set(value) == set(expected)
        and all(type(value[key]) is type(item) and value[key] == item for key, item in expected.items()))


def authenticate(root):
    raw = read_regular(root, DIRECTORY + "AMENDMENT.json", 16384)
    document = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    # Exact canonical representation rejects coercions, extra/duplicate entries,
    # unknown paths and bool/int equivalence, without recomputing expected source.
    if json.dumps(document, sort_keys=True, separators=(",", ":")) != json.dumps(EXPECTED, sort_keys=True, separators=(",", ":")):
        raise ValueError("TASK036_PROFILE_AMENDMENT_IDENTITY")
    for name in ("workflow", "guard"):
        row = EXPECTED[name]
        before = read_regular(root, row["preimage"], 65536)
        if (len(before) != row["original_bytes"] or sha256(before).hexdigest() != row["original_sha256"]
                or blob(before) != row["original_blob"]):
            raise ValueError("TASK036_PROFILE_PREIMAGE_IDENTITY")
        if name == "workflow":
            active = read_regular(root, row["path"], 65536).replace(b"\r\n", b"\n")
            if len(active) != row["active_bytes"] or sha256(active).hexdigest() != row["active_sha256"]:
                raise ValueError("TASK036_PROFILE_REPLACEMENT_IDENTITY")
            line = b"          fetch-depth: 0\n"
            if blob(active) != row["active_blob"] or active.count(line) != 1 or active.replace(line, b"", 1) != before:
                raise ValueError("TASK036_PROFILE_WORKFLOW_SEMANTICS")
    return witness()
