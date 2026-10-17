"""Exact test-profile compatibility; not a dependency or native-source waiver.

Fixed replacements are authenticated, never blessed from current bytes.
The sealed v1 checkout-history rule remains intact. Owner D6 adds only two
job deadlines through an exact v2 chain, not independent review or acceptance.
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

# Historical EXPECTED remains byte-for-byte unchanged. These fixed Git
# preimages are the immediate predecessor, not newly computed expectations.
V2_DIRECTORY = "docs/productization/task036-ci-history-amendment-v2/"
SECTION18 = ".github/workflows/section18-implementation.yml"
HELPER = "tests/productization/scene_ir/canonical_history_profile.py"
REVIEW_HELPER = "bie/productization/scene_ir_m1_review.py"
V2_PREIMAGES = {
    WORKFLOW: ("post-dir-canonical-catchup.yml.before", 9443,
        "c35d09469afedc7393ed217bbb87c3fd7fa000a27094d1c21e130cf45b3e4847",
        "26577340fc2935c169202bf48c622fe0c30c4b99"),
    SECTION18: ("section18-implementation.yml.before", 21397,
        "02152f8a36317a752248ad1bce8b3766c1e457fffbc1da959e71f991a47a1d5d",
        "5b4559d6e4f89656eaa2c602635ca5a4192e6f8c"),
    GUARD: ("verify_post_dir_provisioning.py.before", 23564,
        "2bbd0c6c7df6e5f5d2b98235cb1bceab1c5fcb1024a4d40e6ce870cbecdac517",
        "415e3d057654ba0f381b8a4b6ed392c7c6e815f8"),
    HELPER: ("canonical_history_profile.py.before", 5828,
        "2ee292eba7bfcb47e39f25a14aa5e8a85af1a316ecb664d4760222fe5e95a92e",
        "3bb4dd683307ec3f3cad91f0c710b72da8348b19"),
    REVIEW_HELPER: ("scene_ir_m1_review.py.before", 13004,
        "388639b22850280455efc2b523c0108cf8f8e257a3f4a2d406ef63542d4bd5d2",
        "e78a8ddd2f00be143991b92cea06a860aeeeca4d"),
}
V2_WORKFLOWS = {
    WORKFLOW: {"bytes": 9443, "sha256": "5ea0ddd06147fb7fcd82a77c30ad5601d7a95b74e12d059a19fca6f0d7b302bd",
        "git_blob": "6dd94b3f99e7e34d55875a3a206bb75864320538", "old_minutes": 45, "new_minutes": 75},
    SECTION18: {"bytes": 21398, "sha256": "804d89297a8e7b3ba0bba784f38635bfc237babaff01313441f48d068bf44ef4",
        "git_blob": "d93a3a8b68aa8013b66bd6f07bb1e056998ddc70", "old_minutes": 90, "new_minutes": 120},
}
EXPECTED_V2 = {
    "schema": "bie.task036.canonical-history-profile-amendment/2",
    "status": "DRAFT_PENDING_REVIEW_NOT_APPROVAL",
    "scope": "EXACT_TWO_CANONICAL_JOB_DEADLINES_ONLY",
    "owner_decision": "D6",
    "base": "4d5a284c9a51f4e3536852453d6e7543447d2e68",
    "base_tree": "ab2b9a733f5dc7ec4d0f269db517d44eca58f271",
    "previous_amendment_sha256": "639e87119a2cf8f6cf35e8062dbd66df4b021f05b689a5602674e9eb4992df00",
    "previous_replacements_sha256": "67afd0ce2f0540922eca99110c6d2935c4a72ffe3ca8a40a75ef232ab126b927",
    "original_m1_amendment_sha256": EXPECTED["original_m1_amendment_sha256"],
    "preimages": {p: {"path": V2_DIRECTORY + r[0], "bytes": r[1], "sha256": r[2], "git_blob": r[3]}
                  for p, r in V2_PREIMAGES.items()},
    "workflows": V2_WORKFLOWS,
    "capacity_decision_not_performance_fix": True,
    "historical_profile_pins_changed": False, "requirements_installers_changed": False,
    "native_source_changed": False, "mandatory_gates_replaced": False,
    "child_limits_changed": False, "product_accepted": False,
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
    return {"schema": "bie.task036.canonical-history-profile-witness/2",
        "amendment_content_sha256": sha256(document).hexdigest(),
        "historical_workflow_blob": EXPECTED["workflow"]["original_blob"],
        "v1_workflow_blob": EXPECTED["workflow"]["active_blob"],
        "actual_workflow_blob": V2_WORKFLOWS[WORKFLOW]["git_blob"],
        "actual_workflow_sha256": V2_WORKFLOWS[WORKFLOW]["sha256"],
        "actual_section18_blob": V2_WORKFLOWS[SECTION18]["git_blob"],
        "actual_section18_sha256": V2_WORKFLOWS[SECTION18]["sha256"],
        "v2_amendment_content_sha256": sha256(json.dumps(EXPECTED_V2, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "approval_role": "INTEGRITY_ONLY_INDEPENDENT_PRODUCT_ADMISSION_REQUIRED",
        "guard_trust_role": "FIXED_SOURCE_INTEGRITY_NOT_INDEPENDENT_APPROVAL",
        "historical_guard_sha256": EXPECTED["guard"]["original_sha256"],
        "profile_map_role": "HISTORICAL_AUTHORITY_NOT_CURRENT_WORKFLOW_BYTES",
        "change": "V1_FETCH_DEPTH_THEN_D6_TWO_DEADLINES_ONLY", "requirements_installers_changed": False,
        "native_source_changed": False, "mandatory_gates_replaced": False,
        "product_accepted": False}


def validate_witness(value):
    expected = witness()
    return (type(value) is dict and set(value) == set(expected)
        and all(type(value[key]) is type(item) and value[key] == item for key, item in expected.items()))


def authenticate(root):
    raw = read_regular(root, DIRECTORY + "AMENDMENT.json", 16384)
    document = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    if sha256(raw).hexdigest() != EXPECTED_V2["previous_amendment_sha256"]:
        raise ValueError("TASK036_PROFILE_AMENDMENT_IDENTITY")
    previous = read_regular(root, DIRECTORY + "REPLACEMENTS.json", 16384)
    if sha256(previous).hexdigest() != EXPECTED_V2["previous_replacements_sha256"]:
        raise ValueError("TASK036_PROFILE_PREVIOUS_ATTESTATION")
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
            active = read_regular(root, V2_DIRECTORY + V2_PREIMAGES[WORKFLOW][0], 65536)
            if len(active) != row["active_bytes"] or sha256(active).hexdigest() != row["active_sha256"]:
                raise ValueError("TASK036_PROFILE_REPLACEMENT_IDENTITY")
            line = b"          fetch-depth: 0\n"
            if blob(active) != row["active_blob"] or active.count(line) != 1 or active.replace(line, b"", 1) != before:
                raise ValueError("TASK036_PROFILE_WORKFLOW_SEMANTICS")
    raw = read_regular(root, V2_DIRECTORY + "AMENDMENT.json", 16384)
    document = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    if json.dumps(document, sort_keys=True, separators=(",", ":")) != json.dumps(EXPECTED_V2, sort_keys=True, separators=(",", ":")):
        raise ValueError("TASK036_PROFILE_V2_AMENDMENT_IDENTITY")
    for path, row in EXPECTED_V2["preimages"].items():
        before = read_regular(root, row["path"], 65536)
        if (len(before), sha256(before).hexdigest(), blob(before)) != (row["bytes"], row["sha256"], row["git_blob"]):
            raise ValueError("TASK036_PROFILE_V2_PREIMAGE_IDENTITY")
        if path not in V2_WORKFLOWS:
            continue
        target = V2_WORKFLOWS[path]
        active = read_regular(root, path, 65536).replace(b"\r\n", b"\n")
        old = ("    timeout-minutes: %d\n" % target["old_minutes"]).encode()
        new = ("    timeout-minutes: %d\n" % target["new_minutes"]).encode()
        if before.count(old) != 1 or active != before.replace(old, new, 1):
            raise ValueError("TASK036_PROFILE_V2_WORKFLOW_SEMANTICS")
        if (len(active), sha256(active).hexdigest(), blob(active)) != (target["bytes"], target["sha256"], target["git_blob"]):
            raise ValueError("TASK036_PROFILE_V2_REPLACEMENT_IDENTITY")
    return witness()
