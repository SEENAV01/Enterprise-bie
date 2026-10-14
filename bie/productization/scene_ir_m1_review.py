"""Authenticate genuine current M1 review without rewriting its historical authority."""
from pathlib import Path
from hashlib import sha1
import os
import stat

from .contracts import require, sha, strict_json

DIRECTORY = "docs/productization/m1-review/"
HISTORICAL = DIRECTORY + "REVIEW_87320CB0.json"
FINAL = DIRECTORY + "REVIEW_A24EF1CD.json"
ADDENDUM = DIRECTORY + "BINDINGS_A24EF1CD.json"
CHAIN = DIRECTORY + "SOURCE_CHAIN_A24EF1CD.json"
HISTORICAL_SHA = "33458799eaf58951aa474a08d412b6b56361ec2f08aebdc23f150976a92410a5"
FINAL_SHA = "9eb3ff17a7e128d5dd9ac6da6210c9461dfbecf6002c33bb499c8215a492612a"
ADDENDUM_SHA = "dbed506a90958c88263dad9280eb2575ec285e79a960952c5c62b4c9f8da53ad"
CHAIN_SHA = "1b60a9dc298e62b2c34a75c0959222abab2738801ba3d6dc2ce2e22e76f658ed"
CANDIDATE = "a24ef1cdce0bb56401837f2dd060f590d1ddda78"
TREE = "6e2675731f6cfb0eb134e41dd8c48db9921bdff6"
REVIEWER = "/root/task036_external_reviewer_replacement_001"
DECISION = "APPROVED_FOR_BOUNDED_M1_TASK036_PREREQUISITE"
PREFIXES = ("bie/compiler/", "scripts/compiler_", "docs/productization/task036-")
DOCUMENT_BYTES = {HISTORICAL: 149689, FINAL: 22161, ADDENDUM: 63445, CHAIN: 90540}


def read_regular(root, relative, limit=262144):
    """Fixed authenticated checkout paths; no symlink or changing-read admission."""
    require(type(relative) is str and "\\" not in relative, "scene_ir_m1_source_identity")
    parts = relative.split("/")
    require(parts and all(p and p not in (".", "..") and ":" not in p for p in parts),
            "scene_ir_m1_source_identity")
    root = Path(root).resolve()
    path = root
    try:
        for part in parts:
            path = path / part
            require(not path.is_symlink(), "scene_ir_m1_source_identity")
        require(path.resolve().is_relative_to(root), "scene_ir_m1_source_identity")
        before = path.stat()
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= limit,
                "scene_ir_m1_source_identity")
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1 and
                (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) ==
                (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns),
                "scene_ir_m1_source_identity")
            data = stream.read(limit + 1)
            closed = os.fstat(stream.fileno())
        after = path.stat()
    except OSError:
        require(False, "scene_ir_m1_source_identity")
    require(after.st_nlink == closed.st_nlink == 1 and
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (closed.st_dev, closed.st_ino, closed.st_size, closed.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and
            path.resolve().is_relative_to(root) and len(data) == before.st_size,
            "scene_ir_m1_source_identity")
    return data


def authenticated_document(root, relative, expected):
    require(relative in DOCUMENT_BYTES, "scene_ir_m1_review_identity")
    raw = read_regular(root, relative, DOCUMENT_BYTES[relative])
    require(len(raw) == DOCUMENT_BYTES[relative] and sha(raw) == expected,
            "scene_ir_m1_review_identity")
    return strict_json(raw)


def keyed(rows, count):
    require(type(rows) is list and len(rows) == count and all(type(r) is dict for r in rows),
            "scene_ir_m1_source_identity")
    result = {r["path"]: r for r in rows}
    require(len(result) == count, "scene_ir_m1_source_identity")
    return result


def verified_source_chain(root):
    """Fixed committed-object index, not runtime-derived expected hashes.

    Original and current actual reviewers verified the canonical amendment
    chain. This index binds its complete current compiler inventory and every
    original seal/preimage/audit seam to that same Git tree. It cannot permit
    arbitrary future edits, partial rollback or unlisted source. Full canonical
    ledger/adoption execution remains an independently required hosted gate.
    """
    chain = authenticated_document(root, CHAIN, CHAIN_SHA)
    require(set(chain) == {"schema", "role", "candidate", "tree", "base",
        "historical_review_sha256", "current_review_sha256", "binding_addendum_sha256",
        "compiler_paths", "files", "ledger", "product_accepted"} and
        chain["schema"] == "bie.task036.reviewed-source-chain-index/1" and
        chain["role"] == "EXACT_ALREADY_REVIEWED_GIT_OBJECT_INDEX_NOT_AN_APPROVAL" and
        chain["candidate"] == CANDIDATE and chain["tree"] == TREE and
        chain["base"] == "5b1cafc766c9df9c3e0748f459e6beb9b8f1f243" and
        chain["historical_review_sha256"] == HISTORICAL_SHA and
        chain["current_review_sha256"] == FINAL_SHA and
        chain["binding_addendum_sha256"] == ADDENDUM_SHA and
        chain["product_accepted"] is False, "scene_ir_m1_source_identity")
    rows = keyed(chain["files"], 210)
    # The original motion review/index remains immutable authority for every
    # unchanged source. Only the exactly approved later monitor may replace its
    # old census row, after current review, complete metadata-chain and raw
    # preimage checks. Missing later authority cannot fall back to the old row.
    from .scene_ir_monitor_review import verified_review,WORKER,BASELINE_SHA
    monitor = verified_review(root,read=read_regular)
    require(rows[WORKER]["sha256"]==BASELINE_SHA and rows[WORKER]["bytes"]==28552,
        "scene_ir_m1_monitor_source_identity")
    expected = chain["compiler_paths"]
    require(type(expected) is list and len(expected) == len(set(expected)) == 143 and
        set(expected) == {p for p in rows if p.startswith("bie/compiler/")},
        "scene_ir_m1_source_identity")
    folder = Path(root) / "bie/compiler"
    actual = set()
    for p in folder.rglob("*"):
        if "__pycache__" in p.parts:
            continue
        require(not p.is_symlink(), "scene_ir_m1_source_identity")
        if p.is_file():
            actual.add(p.relative_to(root).as_posix())
    require(actual == set(expected), "scene_ir_m1_source_identity")
    for path, row in rows.items():
        if path==WORKER:
            row=monitor
        raw = read_regular(root, path)
        require(set(row) == {"path", "git_blob", "raw_git_bytes", "raw_git_sha256",
            "mode", "bytes", "sha256"}, "scene_ir_m1_source_identity")
        mode = "RAW_IMMUTABLE" if path.startswith("docs/") else "CRLF_TO_LF_ONLY"
        require(row["mode"] == mode, "scene_ir_m1_source_identity")
        data = raw if mode == "RAW_IMMUTABLE" else raw.replace(b"\r\n", b"\n")
        require(type(row["bytes"]) is int and len(data) == row["bytes"] and
            sha(data) == row["sha256"], "scene_ir_m1_source_identity")
        if mode == "RAW_IMMUTABLE":
            require(len(raw) == row["raw_git_bytes"] and sha(raw) == row["raw_git_sha256"] and
                sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
                == row["git_blob"], "scene_ir_m1_source_identity")
    ledger = chain["ledger"]
    require(ledger == {"path": "manifests/post_dir_integration_004.json", "bytes": 40505121,
        "sha256": "33c579d83186d0a11319984e6d047cb41bfea804a6477e5902b77f0432d71c7f"},
        "scene_ir_m1_source_identity")
    # Same canonical ledger bound/conversion, no archive traversal or repeated
    # recursive resolver parsing. It remains the exact immutable authority.
    data = read_regular(root, ledger["path"], 42 * 1024**2).replace(b"\r\n", b"\n")
    require(len(data) == ledger["bytes"] and sha(data) == ledger["sha256"],
        "scene_ir_m1_source_identity")
    return CHAIN_SHA


def verified_m1_review(root):
    """Fixed later source authority plus the intact original review, never a bool waiver."""
    old = authenticated_document(root, HISTORICAL, HISTORICAL_SHA)
    final = authenticated_document(root, FINAL, FINAL_SHA)
    newer = authenticated_document(root, ADDENDUM, ADDENDUM_SHA)
    require(old["decision"] == DECISION and old["blocking_findings_remaining"] == 0 and
            old["reviewer"]["execution_identity"] == "/root/m1_external_technical_reviewer_001",
            "scene_ir_m1_review_required")
    require(final["decision"] == DECISION and type(final["blocking_findings_in_bounded_M1_scope"]) is int and
            final["blocking_findings_in_bounded_M1_scope"] == 0 and
            final["reviewer"]["execution_identity"] == REVIEWER and
            final["reviewer"]["implementation_execution"] == "/root" and
            final["reviewer"]["type"] == "GENUINELY_SEPARATE_AI_ASSISTED_REPLACEMENT_EXECUTION" and
            final["exact_source"]["candidate"] == CANDIDATE and final["exact_source"]["tree"] == TREE,
            "scene_ir_m1_review_required")
    require(newer["decision"] == DECISION and newer["reviewer_execution"] == REVIEWER and
            newer["actual_separate_ai_assisted_execution"] is True and
            newer["blocking_findings_in_bounded_M1_scope"] == 0 and
            newer["exact_reviewed_candidate"]["head"] == CANDIDATE and
            newer["exact_reviewed_candidate"]["tree"] == TREE and
            newer["final_review"]["sha256"] == FINAL_SHA and
            newer["historical_review"]["sha256"] == HISTORICAL_SHA,
            "scene_ir_m1_review_required")
    historical = keyed([r for r in old["cumulative_source_review"]["exact_reviewed_file_bindings"]
                        if r["path"].startswith(PREFIXES)], 52)
    current = keyed(newer["exact_reviewed_file_bindings"], 52)
    raw_bindings = keyed(newer["raw_git_file_bindings"], 52)
    changes = keyed(newer["reviewed_correction"]["changed_historical_bindings"], 4)
    require(set(current) == set(historical) == set(raw_bindings), "scene_ir_m1_source_identity")
    for path, row in current.items():
        if path in changes:
            require(changes[path]["historical_binding"] == historical[path] and
                    changes[path]["current_binding"] == row, "scene_ir_m1_source_identity")
        else:
            require(row == historical[path], "scene_ir_m1_source_identity")
    followon = keyed(newer["authenticated_followon_file_bindings"], 11)
    auxiliary = keyed(newer["auxiliary_reviewed_authority_bindings"], 3)
    require(not (set(current) & set(followon) or set(current) & set(auxiliary) or
                 set(followon) & set(auxiliary)), "scene_ir_m1_source_identity")
    for row in (*current.values(), *followon.values(), *auxiliary.values()):
        raw = read_regular(root, row["path"])
        data = raw.replace(b"\r\n", b"\n")
        require(type(row["bytes"]) is int and len(data) == row["bytes"] and
                sha(data) == row["sha256"], "scene_ir_m1_source_identity")
        if row["path"] in current:
            raw_row = raw_bindings[row["path"]]
            require(raw_row["git_blob"] == row["git_blob"] and
                    raw_row["lf_normalized_bytes"] == row["bytes"] and
                    raw_row["lf_normalized_sha256"] == row["sha256"],
                    "scene_ir_m1_source_identity")
        else:
            raw_row = row
        # These reviewed records are sealed documents, attributes and immutable
        # preimages, NOT portable working source. Their raw Git identities must
        # not be waived by the ordinary source's LF-only checkout convention.
        if row["path"].startswith("docs/productization/task036-"):
            require(type(raw_row["raw_git_bytes"]) is int and
                    len(raw) == raw_row["raw_git_bytes"] and
                    sha(raw) == raw_row["raw_git_sha256"] and
                    sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
                    == raw_row["git_blob"], "scene_ir_m1_source_identity")
    # Complete fixed identity equality subsumes the already-reviewed native
    # subset's constant schema/parent/preimage/active-byte checks. Reopen and
    # authenticate ALL 210 rows, compiler census and immutable ledger once;
    # never reuse a proof across operations. The reader retains the native
    # single-link/containment requirements and strengthens changing-read checks.
    # Full canonical native audit execution remains an independent CI gate.
    chain_identity = verified_source_chain(root)
    return dict(m1_review=HISTORICAL_SHA, m1_current_review=FINAL_SHA,
                m1_current_source_bindings=ADDENDUM_SHA, m1_source_chain=chain_identity)
