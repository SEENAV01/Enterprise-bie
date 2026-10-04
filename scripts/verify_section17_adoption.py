"""Verify every adopted R1 file and its reviewed integration amendments."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/section17/integration-r1'
ROLES = {
    'SECTION17_SOURCE_COMPARE_AND_ADOPT',
    'SECTION17_TESTS_REVIEW_REGISTRATION_AND_COLLISIONS',
    'SUPPORTING_SECTION17_FILES_REVIEW_SCOPE',
}
TEXT_SUFFIXES = {'.py', '.json', '.md', '.txt', '.html', '.js', '.mjs', '.css', '.srt', '.yaml', '.yml'}
CLI = 'bie/qa/lifecycle_quality_v2/__main__.py'
CLI_SHA = '7bc0c5b937d14a4918349f377716d213e9447812aac2f8d5f443bda0b7f6ee0e'
MAINTENANCE_DIR = 'docs/section18/maintenance-campaign-sidecar'
MAINTENANCE_SHA = 'b1e37fe21c203980a8ebf4feb4b7b1789ed822a3f18459672038e14849d60d0d'
CAMPAIGN_PATH = 'bie/evaluation/benchmarks/native_campaign/runtime.py'
CAMPAIGN_ORIGINAL = 'd471bb8372696fa471dfd386d13b8003ed0e8980fb7057991819955fb1477a82'
CAMPAIGN_REPLACEMENT = '22de09eeab7b7d7091d5c3a7a493d27d865faebeda696bc90b1abfb5a00c387a'


def checked_path(relative: str) -> Path:
    path = PurePosixPath(relative)
    if (not relative or str(path) != relative or path.is_absolute()
            or any(part in ('.', '..') for part in path.parts)
            or '\\' in relative or ':' in relative):
        raise ValueError('UNSAFE_ADOPTION_PATH')
    target = ROOT.joinpath(*path.parts)
    if not target.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('ADOPTION_PATH_ESCAPE')
    if any(p.is_symlink() for p in (target, *target.parents) if p != ROOT.parent):
        raise ValueError('ADOPTION_LINK')
    return target


def matches(path: Path, expected: str) -> bool:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() == expected:
        return True
    if path.suffix.lower() not in TEXT_SUFFIXES or b'\r\n' not in raw:
        return False
    # Windows core.autocrlf materializes an otherwise exact LF Git blob.
    if b'\r' in raw.replace(b'\r\n', b''):
        return False
    return hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() == expected


def verified_maintenance() -> dict[str, str]:
    """One reviewed cross-section correction, never an arbitrary hash override.

    The immutable R1 map and its fourteen amendments remain authoritative.
    Both the extra amendment document and the genuine original byte preimage
    are pinned separately. All other adopted paths retain their original gate.
    """
    path = checked_path(MAINTENANCE_DIR + '/AMENDMENT.json')
    if not path.exists():
        return {}
    if not path.is_file() or path.stat().st_size > 4096 or not matches(path, MAINTENANCE_SHA):
        raise ValueError('MAINTENANCE_DOCUMENT_TAMPERED')
    body = json.loads(path.read_text(encoding='utf-8'))
    if (body['path'] != CAMPAIGN_PATH or body['original_adopted_sha256'] != CAMPAIGN_ORIGINAL
            or body['replacement_sha256'] != CAMPAIGN_REPLACEMENT
            or body['original_section17_test_methods'] != 2023):
        raise ValueError('MAINTENANCE_SCOPE_OR_PIN')
    before = checked_path(MAINTENANCE_DIR + '/runtime.py.before')
    if not before.is_file() or before.stat().st_size > 32*1024:
        raise ValueError('MAINTENANCE_PREIMAGE_MISSING')
    raw = before.read_bytes()
    # Either exact Windows checkout bytes or their exact LF Git blob. No source
    # reconstruction, ignored region, or relaxed semantic comparison is used.
    if (hashlib.sha256(raw).hexdigest() not in
            {body['before_image_sha256'], CAMPAIGN_ORIGINAL}
            or hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != CAMPAIGN_ORIGINAL):
        raise ValueError('MAINTENANCE_PREIMAGE_TAMPERED')
    return {CAMPAIGN_PATH: CAMPAIGN_REPLACEMENT}


def verify_h1_preimages(delta: dict, recovery: dict) -> list[str]:
    """Require all fourteen original byte preimages, not only their metadata."""
    expected = {row['preimage']: row for row in delta['changed_original_files']}
    recovered = {row['path']: row for row in recovery['files']}
    if (len(expected) != 14 or len(recovered) != len(recovery['files'])
            or set(recovered) != set(expected)
            or recovery.get('source_master_sha256') != '03043839a2290672a4b672cbb39952846e77ff99572a791bf0ca89cf14a51f4e'
            or recovery.get('status') != 'RECOVERED_EXACT_BYTES'
            or recovery.get('bytes_reconstructed') is not False):
        return ['H1_PREIMAGE_RECOVERY_CENSUS_OR_ORIGIN']
    errors = []
    for relative, original in expected.items():
        row = recovered[relative]
        path = checked_path(relative)
        if (row['original_path'] != original['path']
                or row['sha256'] != original['before_sha256']
                or not path.is_file() or not matches(path, original['before_sha256'])):
            errors.append('H1_PREIMAGE_BYTES_OR_BINDING:' + relative)
    return errors


def verify() -> dict:
    mapping = json.loads((EVIDENCE / 'SOURCE_INTEGRATION_MAP.json').read_text(encoding='utf-8'))
    amendments = json.loads((EVIDENCE / 'ADOPTION_AMENDMENTS.json').read_text(encoding='utf-8'))
    if mapping.get('canonical_pin') != '8b8e500bf7b83addfcecce41c3fca08563eceb41':
        raise ValueError('WRONG_ADOPTION_BASE')
    if amendments.get('source_master_sha256') != '03043839a2290672a4b672cbb39952846e77ff99572a791bf0ca89cf14a51f4e':
        raise ValueError('WRONG_SOURCE_MASTER')
    changes = {row['path']: row for row in amendments['amendments']}
    maintenance = verified_maintenance()
    if set(changes) != {
        'tools/run_section17_native_api_tests.py',
        'bie/evaluation/benchmarks/native_api/service.py',
        'tests/section17/h2_support.py',
        'tests/section17/h4_support.py',
        'tests/section17/test_bio_001.py',
        'tests/section17/test_bio_002.py',
        'tests/section17/test_bio_003.py',
        'tests/section17/test_chem_001.py',
        'tests/section17/test_chem_002.py',
        'tests/section17/test_chem_003.py',
        'tests/section17/test_geo_001.py',
        'tests/section17/test_hist_001.py',
        'tests/section17/test_hist_002.py',
        'tests/section17/test_hist_003.py',
    }:
        raise ValueError('UNREVIEWED_AMENDMENT_SET')
    seen = set()
    adopted = 0
    caches = 0
    errors = []
    for row in mapping['files']:
        relative = row['path']
        if relative in seen:
            raise ValueError('DUPLICATE_ADOPTION_PATH')
        seen.add(relative)
        if row['disposition'] not in ROLES:
            continue
        path = checked_path(relative)
        if '__pycache__' in PurePosixPath(relative).parts or relative.endswith('.pyc'):
            caches += 1
            if path.exists():
                errors.append('GENERATED_CACHE_ADOPTED:' + relative)
            continue
        adopted += 1
        amendment = changes.get(relative)
        if amendment and amendment['original_sha256'] != row['sha256']:
            errors.append('AMENDMENT_PREIMAGE_MISMATCH:' + relative)
        expected = amendment['replacement_sha256'] if amendment else row['sha256']
        if relative in maintenance:
            if amendment or row['sha256'] != CAMPAIGN_ORIGINAL:
                errors.append('MAINTENANCE_ORIGINAL_BINDING:' + relative)
            expected = maintenance[relative]
        if not path.is_file() or not matches(path, expected):
            errors.append('ADOPTED_HASH_MISMATCH:' + relative)
    if (adopted, caches) != (780, 15):
        errors.append('ADOPTION_CENSUS_MISMATCH')
    if not matches(checked_path(CLI), CLI_SHA):
        errors.append('QA_CLI_PATCH_MISMATCH')
    delta = json.loads((ROOT / 'metadata/section17/H1_WORKSPACE_DELTA.json').read_text(encoding='utf-8'))
    recovery = json.loads((EVIDENCE / 'H1_PREIMAGE_RECOVERY.json').read_text(encoding='utf-8'))
    errors.extend(verify_h1_preimages(delta, recovery))
    return {'schema_version': 'bie.section17.adoption/1', 'adopted_files': adopted,
            'generated_caches_excluded': caches, 'reviewed_amendments': len(changes),
            'reviewed_section18_maintenance_amendments': len(maintenance),
            'recovered_h1_preimages': len(recovery['files']),
            'errors': errors, 'passed': not errors, 'section_complete': False,
            'product_accepted': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
