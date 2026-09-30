#!/usr/bin/env python3
"""Read-only, hash-pinned Section17 R1 collision preflight. Never installs or pushes.

Run from a clean integration checkout after an authorized git fetch:
  python -B scripts/section17_r1_preflight.py --master /path/to/R1.zip --repo .
The JSON result is a review plan, never a merge/section/product approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import unicodedata
import zipfile

BASE = '8b8e500bf7b83addfcecce41c3fca08563eceb41'
BRANCH = 'integration/section17-eval-r1-20260930'
MASTER_SHA = '03043839a2290672a4b672cbb39952846e77ff99572a791bf0ca89cf14a51f4e'
MASTER_BYTES = 383934041
CLI = 'bie/qa/lifecycle_quality_v2/__main__.py'
CLI_BASE = '58014fef4352224c772684b876a4e269459e2fa605235d2a2ad868c0faad0a0b'
CLI_NEXT = '7bc0c5b937d14a4918349f377716d213e9447812aac2f8d5f443bda0b7f6ee0e'
ORIGINS = {'https://github.com/SEENAV01/Enterprise-bie.git',
           'https://github.com/SEENAV01/Enterprise-bie',
           'git@github.com:SEENAV01/Enterprise-bie.git'}
SOURCE = 'SECTION17_SOURCE_COMPARE_AND_ADOPT'
TESTS = 'SECTION17_TESTS_REVIEW_REGISTRATION_AND_COLLISIONS'
SUPPORT = 'SUPPORTING_SECTION17_FILES_REVIEW_SCOPE'
DEPENDENCY = 'DEPENDENCY_OR_COMPATIBILITY_COMPARE_ONLY_DO_NOT_OVERWRITE'
HISTORY = 'HISTORICAL_EVIDENCE_OR_STANDALONE_METADATA_DO_NOT_USE_AS_GLOBAL_CONTINUATION'
PATCH = 'EXPLICIT_REVIEWED_CLI_PATCH'

class PreflightError(ValueError):
    pass

def require(ok, code):
    if not ok:
        raise PreflightError(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def pairs(values):
    result = {}
    for key, value in values:
        require(key not in result, 'DUPLICATE_JSON_KEY')
        result[key] = value
    return result

def load(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs)

def safe(name):
    require(type(name) is str and bool(name), 'EMPTY_PATH')
    path = PurePosixPath(name)
    require(str(path) == name and not path.is_absolute(), 'NONCANONICAL_PATH')
    require(not any(x in name for x in ('\\', ':', '\0')), 'UNSAFE_PATH')
    require(not any(ord(c) < 32 for c in name), 'CONTROL_IN_PATH')
    require(not any(p in ('.', '..') or p.endswith((' ', '.')) for p in path.parts), 'UNSAFE_COMPONENT')
    require(unicodedata.normalize('NFC', name) == name, 'NONCANONICAL_UNICODE')
    reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {f'{k}{i}' for k in ('COM', 'LPT') for i in range(1, 10)}
    require(not any(p.split('.')[0].upper() in reserved for p in path.parts), 'RESERVED_PATH')
    return path

def no_links(path):
    p = Path(os.path.abspath(path))
    require(not any(x.is_symlink() for x in (p, *p.parents)), 'SYMLINK_PATH')
    return p

def file_hash(path):
    p = no_links(path)
    require(p.is_file(), 'MISSING_REGULAR_FILE')
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def git(repo, *args):
    run = subprocess.run(['git', '-C', str(repo), *args], check=False,
                         capture_output=True, timeout=30)
    require(run.returncode == 0, 'GIT_COMMAND_FAILED:' + args[0])
    return run.stdout.decode('utf-8').strip()

def check_checkout(repo):
    root = no_links(repo)
    require(Path(git(root, 'rev-parse', '--show-toplevel')).resolve() == root.resolve(), 'NOT_REPO_ROOT')
    require(git(root, 'remote', 'get-url', 'origin') in ORIGINS, 'WRONG_ORIGIN')
    require(git(root, 'symbolic-ref', '--short', 'HEAD') == BRANCH, 'WRONG_BRANCH')
    require(not git(root, 'status', '--porcelain', '--untracked-files=all'), 'DIRTY_CHECKOUT')
    require(git(root, 'rev-parse', 'origin/main') == BASE, 'MAIN_CHANGED_REBASE_REVIEW_REQUIRED')
    git(root, 'merge-base', '--is-ancestor', BASE, 'HEAD')
    return {'head': git(root, 'rev-parse', 'HEAD'), 'base': BASE, 'branch': BRANCH,
            'tracking_ref_checked_not_live_fetch': True}

def verify_master(path):
    p = no_links(path)
    require(p.is_file() and p.stat().st_size == MASTER_BYTES, 'MASTER_SIZE_MISMATCH')
    require(file_hash(p) == MASTER_SHA, 'MASTER_HASH_MISMATCH')
    with zipfile.ZipFile(p) as z:
        infos = z.infolist()
        require(len(infos) <= 20000 and sum(i.file_size for i in infos) <= 1024**3, 'ARCHIVE_LIMIT')
        names = set()
        for i in infos:
            safe(i.filename)
            require(i.filename.casefold() not in names, 'DUPLICATE_MEMBER')
            names.add(i.filename.casefold())
            require(not i.is_dir() and not i.flag_bits & 1 and not stat.S_ISLNK(i.external_attr >> 16), 'SPECIAL_MEMBER')
        manifest = load(z.read('FILE_MANIFEST.json'))
        require(manifest.get('schema_version') == 1 and type(manifest.get('files')) is dict, 'MANIFEST_SCHEMA')
        expected = manifest['files']
        require(set(expected) == {i.filename for i in infos} - {'FILE_MANIFEST.json'}, 'MANIFEST_CENSUS')
        for name, item in expected.items():
            with z.open(name) as stream:
                h = hashlib.sha256(); count = 0
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    count += len(block); h.update(block)
            require(item == {'sha256': h.hexdigest(), 'size_bytes': count}, 'PAYLOAD_MISMATCH:' + name)
        mapping = load(z.read('integration/SOURCE_INTEGRATION_MAP.json'))
        require(mapping.get('canonical_pin') == BASE, 'WRONG_MAP_BASE')
        require(type(mapping.get('files')) is list, 'MAP_SCHEMA')
        paths = [row['path'] for row in mapping['files']]
        require(len(paths) == len(set(paths)), 'MAP_DUPLICATE')
        require(set('combined_source/' + x for x in paths) == {x for x in expected if x.startswith('combined_source/')}, 'MAP_CENSUS')
        for row in mapping['files']:
            safe(row['path'])
            require({'sha256': row['sha256'], 'size_bytes': row['bytes']} == expected['combined_source/' + row['path']], 'MAP_HASH')
        return mapping['files'], len(expected)

def classify(row, existing):
    path = row['path']; role = row['disposition']; safe(path)
    require(role in (SOURCE, TESTS, SUPPORT, DEPENDENCY, HISTORY, PATCH), 'UNKNOWN_DISPOSITION')
    if '__pycache__' in PurePosixPath(path).parts or path.endswith('.pyc'):
        return 'ARCHIVE_ONLY_GENERATED_CACHE'
    if role == HISTORY:
        return 'ARCHIVE_ONLY_NOT_GLOBAL_OVERLAY'
    if role == DEPENDENCY:
        return 'DEPENDENCY_IDENTICAL_DO_NOT_COPY' if existing == row['sha256'] else 'DEPENDENCY_REVIEW_DO_NOT_COPY'
    if role == PATCH:
        require(path == CLI and row['sha256'] == CLI_NEXT, 'UNEXPECTED_PATCH')
        if existing == CLI_BASE: return 'CLI_BASE_MATCH_REVIEW_PATCH'
        if existing == CLI_NEXT: return 'CLI_ALREADY_CANDIDATE'
        return 'CONFLICT_CLI'
    if role == SOURCE: require(path.startswith('bie/evaluation/benchmarks/'), 'SOURCE_SCOPE')
    if role == TESTS: require(path.startswith('tests/section17/'), 'TEST_SCOPE')
    if existing is None: return 'ADD_REVIEW_CANDIDATE'
    return 'IDENTICAL' if existing == row['sha256'] else 'CONFLICT_EXISTING_FILE'

def collision_plan(repo, rows):
    root = no_links(repo); output = []
    for row in rows:
        relative = safe(row['path']); target = root.joinpath(*relative.parts)
        no_links(target)
        require(not target.exists() or target.is_file(), 'TARGET_NOT_FILE:' + row['path'])
        current = file_hash(target) if target.exists() else None
        output.append({'path': row['path'], 'candidate_sha256': row['sha256'],
                       'current_sha256': current, 'disposition': classify(row, current)})
    return output

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--master', type=Path, required=True)
    p.add_argument('--repo', type=Path, default=Path.cwd())
    a = p.parse_args()
    try:
        checkout = check_checkout(a.repo)
        rows, count = verify_master(a.master)
        plan = collision_plan(a.repo, rows)
        conflicts = [r['path'] for r in plan if r['disposition'].startswith('CONFLICT')]
        dependency_review = [r['path'] for r in plan if r['disposition'] == 'DEPENDENCY_REVIEW_DO_NOT_COPY']
        print(json.dumps({'status': 'REVIEW_REQUIRED' if conflicts or dependency_review else 'PREFLIGHT_CLEAR_NOT_ADOPTED',
                          'checkout': checkout, 'master_sha256': MASTER_SHA, 'verified_payload_files': count,
                          'conflicts': conflicts, 'dependency_review': dependency_review, 'plan': plan,
                          'source_adopted': False, 'tests_run': False, 'main_modified': False,
                          'section_complete': False, 'product_accepted': False}, indent=2))
        return 2 if conflicts or dependency_review else 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, subprocess.SubprocessError) as e:
        print(json.dumps({'status': 'BLOCKED', 'error': str(e), 'source_adopted': False, 'product_accepted': False}))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
