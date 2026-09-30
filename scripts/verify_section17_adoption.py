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


def verify() -> dict:
    mapping = json.loads((EVIDENCE / 'SOURCE_INTEGRATION_MAP.json').read_text(encoding='utf-8'))
    amendments = json.loads((EVIDENCE / 'ADOPTION_AMENDMENTS.json').read_text(encoding='utf-8'))
    if mapping.get('canonical_pin') != '8b8e500bf7b83addfcecce41c3fca08563eceb41':
        raise ValueError('WRONG_ADOPTION_BASE')
    if amendments.get('source_master_sha256') != '03043839a2290672a4b672cbb39952846e77ff99572a791bf0ca89cf14a51f4e':
        raise ValueError('WRONG_SOURCE_MASTER')
    changes = {row['path']: row for row in amendments['amendments']}
    if set(changes) != {
        'tools/run_section17_native_api_tests.py',
        'bie/evaluation/benchmarks/native_api/service.py',
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
        if not path.is_file() or not matches(path, expected):
            errors.append('ADOPTED_HASH_MISMATCH:' + relative)
    if (adopted, caches) != (780, 15):
        errors.append('ADOPTION_CENSUS_MISMATCH')
    if not matches(checked_path(CLI), CLI_SHA):
        errors.append('QA_CLI_PATCH_MISMATCH')
    return {'schema_version': 'bie.section17.adoption/1', 'adopted_files': adopted,
            'generated_caches_excluded': caches, 'reviewed_amendments': len(changes),
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
