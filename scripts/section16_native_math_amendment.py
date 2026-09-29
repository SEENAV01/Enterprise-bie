"""Exact, lossless ledger redirection for one repaired native math parser.

The sealed source ledger is never edited. This preserves the original migrated
bytes while separately verifying the repaired canonical owner. No acceptance
or Section 16 sign-off is implied.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

MANIFEST = 'manifests/qa_section16_native_math_ledger_amendment.json'
LEDGER = 'manifests/lossless_migration.csv'
LEDGER_SHA256 = 'f981c9c11834f4136052306613de16bbb241ca4d980b96fec675d3ca767b76d1'
ENTRY = {
    'file_id': '8d9276307e603599341c6a264beea315c1571632ce0b54ab5faf1b4e157c979b',
    'active_path': 'bie/math_intelligence/expression_ast.py',
    'active_sha256': '8b13a200725e07abc389d3750643b38f8800868de50ecd83e5f2aff79baeee27',
    'before_image': 'docs/evidence/qa-section16/predecessors/bie/math_intelligence/expression_ast.py',
    'before_sha256': 'c36c5980be5c8bf7973429c3f9d781db5808a1f9da9963c7417ecf7fc69793b4',
    'original_sha256': 'c36c5980be5c8bf7973429c3f9d781db5808a1f9da9963c7417ecf7fc69793b4',
    'original_bytes': '605',
}
REASON = ('Preserve the exact original migrated parser bytes while the separately '
          'hash-pinned active owner repairs reproduced silent token truncation.')


def _regular_bytes(root: Path, relative: str) -> bytes:
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('QA_NATIVE_MATH_AMENDMENT_PATH')
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError('QA_NATIVE_MATH_AMENDMENT_SYMLINK')
    if not path.is_file():
        raise ValueError('QA_NATIVE_MATH_AMENDMENT_MISSING:' + relative)
    return path.read_bytes()


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('QA_NATIVE_MATH_AMENDMENT_DUPLICATE_KEY')
        result[key] = value
    return result


def resolve(root: Path, rows: list[dict]) -> list[dict]:
    """Redirect only the exact preserved row, rejecting any identity drift."""
    root = root.resolve()
    manifest = json.loads(_regular_bytes(root, MANIFEST), object_pairs_hook=_unique_json)
    expected = {
        'schema_version': 'bie.qa.section16.native-math-ledger-amendment/1',
        'original_ledger_sha256': LEDGER_SHA256,
        'source_archive_sha256': 'd4a3160e93f47ec510c8162309580b3df4fa3a8346211eb4197905a0399e24f1',
        'candidate_base_commit': '1ba9e25ff97822ef901bcb116afd90b4a76a8290',
        'scope': 'NATIVE_MATH_PARSER_SILENT_TRUNCATION_REPAIR',
        'product_accepted': False,
        'section16_signed_off': False,
        'entry': ENTRY,
        'reason': REASON,
    }
    if manifest != expected:
        raise ValueError('QA_NATIVE_MATH_AMENDMENT_IDENTITY')
    if hashlib.sha256(_regular_bytes(root, LEDGER)).hexdigest() != LEDGER_SHA256:
        raise ValueError('QA_NATIVE_MATH_AMENDMENT_LEDGER')
    selected = [row for row in rows if row['file_id'] == ENTRY['file_id']]
    if len(selected) != 1:
        raise ValueError('QA_NATIVE_MATH_AMENDMENT_COVERAGE')
    row = selected[0]
    if (row['canonical_path'], row['canonical_sha256'], row['sha256'], row['bytes'], row['disposition']) != (
        ENTRY['active_path'], ENTRY['before_sha256'], ENTRY['original_sha256'], ENTRY['original_bytes'], 'MIGRATED'
    ):
        raise ValueError('QA_NATIVE_MATH_AMENDMENT_ORIGINAL_IDENTITY')
    for path, digest in ((ENTRY['active_path'], ENTRY['active_sha256']),
                         (ENTRY['before_image'], ENTRY['before_sha256'])):
        if hashlib.sha256(_regular_bytes(root, path)).hexdigest() != digest:
            raise ValueError('QA_NATIVE_MATH_AMENDMENT_BYTES:' + path)
    replacement = {
        **row,
        'canonical_path': ENTRY['before_image'],
        'disposition': 'ARCHIVED_EVIDENCE',
        'reason': REASON,
        'transform': 'Section 16 exact native math parser repair; original canonical bytes preserved',
    }
    return [replacement if item['file_id'] == ENTRY['file_id'] else item for item in rows]
