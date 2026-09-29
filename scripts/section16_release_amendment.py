"""Two explicit QA amendments; never rewrite the sealed original ledger.

This only redirects the two original dispositions to byte-exact before-images.
The replacement source and migrated assertions are independently hash-pinned.
It does not authorize release, section sign-off, or product acceptance.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

MANIFEST = 'manifests/qa_section16_release_amendment.json'
LEDGER = 'manifests/lossless_migration.csv'
LEDGER_SHA256 = 'f981c9c11834f4136052306613de16bbb241ca4d980b96fec675d3ca767b76d1'
ANCHOR = 'a68e054025b8fe7756a71e998d9e9103dad8e0f4'
SOURCE_ARCHIVE_SHA256 = 'd4a3160e93f47ec510c8162309580b3df4fa3a8346211eb4197905a0399e24f1'
ENTRIES = (
    {
        'file_id': '6aee875a0974150e981e86f165519d72460b956aa8bd2b092ca4ea2eb0fcc9c8',
        'active_path': 'bie/qa/release_contracts.py',
        'active_sha256': '4ae3347fa0ee58afbf6d3e2949a3972c679efa1a68b47da1e007fe767e203a3c',
        'before_image': 'docs/evidence/qa-section16/predecessors/bie/qa/release_contracts.py',
        'before_sha256': '3e721b622855667f7898097bb5bcbe26855a39f24d1f335b2312af7c34846b3b',
        'original_sha256': '3e721b622855667f7898097bb5bcbe26855a39f24d1f335b2312af7c34846b3b',
        'original_bytes': '8045',
    },
    {
        'file_id': 'd4940ef65757fd0a9c3558636f5b87361823a1411b52b233fb73bf65206423bc',
        'active_path': 'tests/imported/BIE_QA_RELEASE_001/tests/qa/test_release_contracts.py',
        'active_sha256': '62bdaf4c673a0a23ba94a487a96ab107c3d7ec8164334efe8023d59ff754b37c',
        'before_image': 'docs/evidence/qa-section16/predecessors/tests/imported/BIE_QA_RELEASE_001/tests/qa/test_release_contracts.py',
        'before_sha256': 'a5b23162a757c074e2a1c35aef152555d408c27ca827328b005fc1358c90db55',
        'original_sha256': 'bbf1e21131862011156ecd8fb6ce3891c2f99b6a93a55956400f69ee46902cda',
        'original_bytes': '3814',
    },
)


def _regular_bytes(root: Path, relative: str) -> bytes:
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('QA_RELEASE_AMENDMENT_PATH')
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError('QA_RELEASE_AMENDMENT_SYMLINK')
    if not path.is_file():
        raise ValueError('QA_RELEASE_AMENDMENT_MISSING:' + relative)
    return path.read_bytes()


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('QA_RELEASE_AMENDMENT_DUPLICATE_KEY')
        result[key] = value
    return result


def resolve(root: Path, rows: list[dict]) -> list[dict]:
    """Verify an exact reviewed amendment, preserving every other ledger row."""
    root = root.resolve()
    amendment = json.loads(_regular_bytes(root, MANIFEST), object_pairs_hook=_unique_json)
    expected = {
        'schema_version': 'bie.qa.legacy-release-amendment/1',
        'comparison_anchor': ANCHOR,
        'original_ledger_sha256': LEDGER_SHA256,
        'source_archive_sha256': SOURCE_ARCHIVE_SHA256,
        'scope': 'LEGACY_METADATA_ONLY_COMPATIBILITY',
        'product_accepted': False,
        'section_signed_off': False,
        'entries': list(ENTRIES),
        'reason': 'Metadata-only evidence is CONTRACT_ONLY, never release authorization; preserve original source and strengthen the current caller assertion.',
    }
    if amendment != expected or amendment.get('product_accepted') is not False or amendment.get('section_signed_off') is not False:
        raise ValueError('QA_RELEASE_AMENDMENT_IDENTITY')
    if hashlib.sha256(_regular_bytes(root, LEDGER)).hexdigest() != LEDGER_SHA256:
        raise ValueError('QA_RELEASE_AMENDMENT_LEDGER')
    replacement = {}
    for entry in ENTRIES:
        selected = [row for row in rows if row['file_id'] == entry['file_id']]
        if len(selected) != 1:
            raise ValueError('QA_RELEASE_AMENDMENT_COVERAGE')
        row = selected[0]
        if (row['canonical_path'], row['canonical_sha256'], row['sha256'], row['bytes'], row['disposition']) != (
            entry['active_path'], entry['before_sha256'], entry['original_sha256'], entry['original_bytes'], 'MIGRATED'
        ):
            raise ValueError('QA_RELEASE_AMENDMENT_ORIGINAL_IDENTITY')
        for path, digest in ((entry['active_path'], entry['active_sha256']),
                             (entry['before_image'], entry['before_sha256'])):
            if hashlib.sha256(_regular_bytes(root, path)).hexdigest() != digest:
                raise ValueError('QA_RELEASE_AMENDMENT_BYTES:' + path)
        replacement[entry['file_id']] = {
            **row,
            'canonical_path': entry['before_image'],
            'disposition': 'ARCHIVED_EVIDENCE',
            'reason': expected['reason'],
            'transform': 'Section 16 explicit legacy-release amendment; original canonical bytes preserved',
        }
    return [replacement.get(row['file_id'], row) for row in rows]
