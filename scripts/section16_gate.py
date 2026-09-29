"""Explicit Section 16 candidate regression. Passing is not product acceptance.

Each suite has a fresh process, an inherited test-count denominator, test IDs,
bounded execution and captured failures. The original ten release tests reuse
the governed canonical migration instead of being copied or counted twice.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import signal
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'manifests/qa_section16_adoption.json'
AMENDMENTS = 'manifests/qa_section16_amendments.json'
NATIVE_MATH_REPAIR = 'manifests/qa_section16_native_math_parser_001.json'
ADOPTION_MANIFEST_SHA256 = '9804d0102f516d1daeb709a572b0f529e70c68e1dfafe953837c103b367906ba'
APPROVED_FIXTURE_SHA256 = 'eb0fd64790178ce213dfca346fa9acf3c5cebd786e62f969cf3d1d98d22e058d'
NATIVE_MATH_REPAIR_SHA256 = '421bf85f0b69999040659c9029d2b4e48f3f6d5698a04da8faada3ff03c24e67'
NATIVE_MATH_PATH = 'bie/math_intelligence/expression_ast.py'
NATIVE_MATH_BEFORE_SHA256 = 'c36c5980be5c8bf7973429c3f9d781db5808a1f9da9963c7417ecf7fc69793b4'
NATIVE_MATH_EXPECTATION_PATHS = frozenset({
    'tests/qa_hardening_h4/test_h4_parser.py',
    'tests/qa_hardening_h4/test_h4_interfaces.py',
    'tests/qa_math16/test_io_adapters_bridge.py',
})
SUITES = (
    ('qa_section16', 132), ('qa_source16', 146), ('qa_semantic16', 134),
    ('qa_reasoning16', 217), ('qa_math16', 276), ('qa_pedagogy16', 193),
    ('qa_director16', 239), ('qa_visual16', 187), ('qa_animation16', 206),
    ('qa_audio16', 117), ('qa_video16', 159), ('qa_game16', 157),
    ('qa_repair16', 183), ('qa_domain_repair16', 116), ('qa_media_repair16', 113),
    ('qa_repair_audit16', 110), ('qa_regression16', 150), ('qa_repro18', 103),
    ('qa_rights19', 143), ('qa_security20', 154), ('qa_performance21', 129),
    ('qa_publication22', 155), ('qa_hardening_h1', 118), ('qa_hardening_h2', 133),
    ('qa_hardening_h3', 174), ('qa_hardening_h4', 211), ('qa_hardening_h5', 162),
    ('qa_hardening_h6', 137), ('qa_hardening_h7', 147), ('qa_hardening_h8', 155),
    ('qa_reaudit_002', 90), ('original', 10),
)
ORIGINAL = 'tests/imported/BIE_QA_RELEASE_001/tests/qa'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_pairs)


def safe_path(root, name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('UNSAFE_PATH')
    p = PurePosixPath(name)
    if p.is_absolute() or p.as_posix() != name or any(x in ('..', '.') for x in p.parts):
        raise ValueError('UNSAFE_PATH')
    target = root / name
    for component in (target, *target.parents):
        if component == root:
            break
        if component.is_symlink():
            raise ValueError('SYMLINK_REJECTED')
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('PATH_ESCAPE')
    return target


def verify_adoption(root):
    data = read_json(root / MANIFEST)
    if data.get('schema_version') != 'bie.qa.section16.adoption/1':
        raise ValueError('MANIFEST_VERSION')
    if data.get('source_overwrites') != [] or data.get('product_accepted') is not False:
        raise ValueError('MANIFEST_SCOPE')
    amendment = read_json(root / AMENDMENTS)
    if (amendment.get('schema_version') != 'bie.qa.section16.amendments/1'
            or amendment.get('status') != 'SCOPED_SYNTHETIC_FIXTURE_REPAIR_NOT_SECTION_ACCEPTANCE'
            or amendment.get('product_accepted') is not False
            or amendment.get('original_manifest_sha256') != ADOPTION_MANIFEST_SHA256
            or sha((root / MANIFEST).read_bytes()) != ADOPTION_MANIFEST_SHA256
            or amendment.get('source_archive_sha256') != data['source_archive_sha256']):
        raise ValueError('AMENDMENT_SCOPE')
    patches = amendment.get('paths')
    if (type(patches) is not list or len(patches) != 1 or type(patches[0]) is not dict
            or patches[0].get('path') != 'tests/qa_hardening_h8/h8_helpers.py'
            or patches[0].get('reason_code') != 'PYTHON_STDLIB_SHADOWING_IN_SYNTHETIC_STAGE_FIXTURE'
            or patches[0].get('failed_workflow_run') != 36521339502
            or patches[0].get('failed_artifact_sha256') != '951f4824c06cae1c9893726464c0c13b5a50de313c340dba7f39471082811990'
            or patches[0].get('after_sha256') != APPROVED_FIXTURE_SHA256
            or patches[0].get('after_size') != 9523):
        raise ValueError('AMENDMENT_SCOPE')
    patch = patches[0]
    repair = read_json(root / NATIVE_MATH_REPAIR)
    repair_rows = repair.get('paths')
    if (sha((root / NATIVE_MATH_REPAIR).read_bytes()) != NATIVE_MATH_REPAIR_SHA256
            or repair.get('schema_version') != 'bie.qa.section16.native-math-parser-amendment/1'
            or repair.get('status') != 'NATIVE_PARSER_TRUNCATION_REPAIR_PENDING_HOSTED_REAUDIT'
            or repair.get('original_adoption_manifest_sha256') != ADOPTION_MANIFEST_SHA256
            or repair.get('source_archive_sha256') != data['source_archive_sha256']
            or repair.get('candidate_base_commit') != '1ba9e25ff97822ef901bcb116afd90b4a76a8290'
            or repair.get('reason_code') != 'NATIVE_EXPRESSION_PARSER_SILENT_TOKEN_TRUNCATION'
            or repair.get('product_accepted') is not False
            or repair.get('section16_signed_off') is not False
            or type(repair_rows) is not list or len(repair_rows) != 4
            or {r.get('path') for r in repair_rows if type(r) is dict}
                != NATIVE_MATH_EXPECTATION_PATHS | {NATIVE_MATH_PATH}):
        raise ValueError('NATIVE_MATH_REPAIR_SCOPE')
    repair_by_path = {r['path']: r for r in repair_rows}
    native = repair_by_path[NATIVE_MATH_PATH]
    native_payload = safe_path(root, NATIVE_MATH_PATH).read_bytes()
    if (native.get('role') != 'NATIVE_OWNER_REPAIR'
            or native.get('before_sha256') != NATIVE_MATH_BEFORE_SHA256
            or native.get('before_size') != 605
            or len(native_payload) != native.get('after_size')
            or sha(native_payload) != native.get('after_sha256')):
        raise ValueError('NATIVE_MATH_REPAIR_BYTES')
    rows = data['paths']
    if len(rows) != 817:
        raise ValueError('ADOPTION_COUNT')
    seen, roles = set(), Counter()
    for row in rows:
        name = row['path']
        if name.casefold() in seen:
            raise ValueError('DUPLICATE_PATH')
        seen.add(name.casefold())
        payload = safe_path(root, name).read_bytes()
        if name == patch['path']:
            if (patch.get('before_sha256') != row['sha256']
                    or patch.get('before_size') != row['size']
                    or type(patch.get('after_size')) is not int
                    or len(payload) != patch['after_size']
                    or sha(payload) != patch.get('after_sha256')):
                raise ValueError('AMENDMENT_BYTES:' + name)
        elif name in NATIVE_MATH_EXPECTATION_PATHS:
            migrated = repair_by_path[name]
            if (migrated.get('role') != 'INHERITED_QA_EXPECTATION_MIGRATION'
                    or migrated.get('before_sha256') != row['sha256']
                    or migrated.get('before_size') != row['size']
                    or len(payload) != migrated.get('after_size')
                    or sha(payload) != migrated.get('after_sha256')):
                raise ValueError('NATIVE_MATH_EXPECTATION_BYTES:' + name)
        elif type(row['size']) is not int or len(payload) != row['size'] or sha(payload) != row['sha256']:
            raise ValueError('ADOPTION_BYTES:' + name)
        roles[row['role']] += 1
    if roles != Counter(QA_PRODUCTION_ADDITION=278, QA_TEST=180, QA_SCHEMA=50,
                        QA_SPEC=184, QA_TASK=106, SCHEMA_GENERATOR=1, INHERITED_TEST_RESOURCE=18):
        raise ValueError('ROLE_COVERAGE')
    actual = {p.relative_to(root).as_posix() for p in (root / 'bie/qa').rglob('*')
              if p.is_file() and '__pycache__' not in p.parts}
    expected = {r['path'] for r in rows if r['role'] == 'QA_PRODUCTION_ADDITION'}
    if actual != expected | {'bie/qa/__init__.py', 'bie/qa/release_contracts.py'}:
        raise ValueError('QA_SOURCE_INVENTORY')
    test_paths = {p.relative_to(root).as_posix() for name, _ in SUITES if name != 'original'
                  for p in (root / 'tests' / name).rglob('*')
                  if p.is_file() and '__pycache__' not in p.parts}
    if test_paths != {r['path'] for r in rows if r['role'] == 'QA_TEST'}:
        raise ValueError('TEST_INVENTORY')
    actual_dirs = {p.name for p in (root / 'tests').glob('qa_*') if p.is_dir()}
    # qa_engine is the existing Section 15 GAME suite, not this QA delivery.
    # Confirm its exact ownership rather than excluding arbitrary qa_* paths.
    game = read_json(root / 'manifests/game_section15_adoption.json')
    game_tests = {p.relative_to(root).as_posix() for p in (root / 'tests/qa_engine').rglob('test*.py')}
    if not game_tests or game_tests != {p for p in game['test_paths'] if p.startswith('tests/qa_engine/')}:
        raise ValueError('EXISTING_GAME_QA_OWNERSHIP')
    if actual_dirs != {name for name, _ in SUITES if name != 'original'} | {'qa_engine'}:
        raise ValueError('UNDISCOVERED_SUITE')
    return dict(passed=True, paths=len(rows), roles=dict(roles),
                manifest_sha256=sha((root / MANIFEST).read_bytes()),
                amendment_manifest_sha256=sha((root / AMENDMENTS).read_bytes()),
                native_math_repair_manifest_sha256=sha((root / NATIVE_MATH_REPAIR).read_bytes()),
                amended_paths=[patch['path'], *sorted(NATIVE_MATH_EXPECTATION_PATHS)],
                native_owner_repair_path=NATIVE_MATH_PATH)


def git(root, *args):
    # The approved Linux supervisor is root while checkout belongs to runner.
    # Trust only this exact candidate for this invocation, never global '*'.
    return subprocess.check_output(['git', '-c', 'safe.directory=' + str(root), '-C', str(root), *args], text=True).strip()


def candidate_binding(root, allow_dirty):
    status = git(root, 'status', '--porcelain', '--untracked-files=all')
    if status and not allow_dirty:
        raise ValueError('DIRTY_CANDIDATE')
    # Bind the whole active engine tree, not archived dependency copies.
    names = set(git(root, 'ls-files').splitlines())
    names.update(r['path'] for r in read_json(root / MANIFEST)['paths'])
    names.update((MANIFEST, 'scripts/section16_gate.py', 'tests/assembly/test_section16_gate.py'))
    names.update(p.relative_to(root).as_posix() for p in (root / 'bie').rglob('*.py'))
    hashes = {}
    for name in sorted(names):
        p = safe_path(root, name)
        if p.is_file() and (name.startswith(('bie/', 'apps/', 'scripts/', 'tests/', 'manifests/'))
                            or name.startswith('requirements') or name == 'pyproject.toml'):
            hashes[name] = sha(p.read_bytes())
    return dict(commit=git(root, 'rev-parse', 'HEAD'), tree=git(root, 'rev-parse', 'HEAD^{tree}'),
                dirty=bool(status), tracked_and_engine_hashes=hashes,
                files_digest=sha(json.dumps(hashes, sort_keys=True).encode()))


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids = []
        self.successes = []

    def startTest(self, test):
        self.ids.append(test.id())
        super().startTest(test)

    def addSuccess(self, test):
        self.successes.append(test.id())
        super().addSuccess(test)


def valid_result(row, expected):
    ids = row.get('test_ids', [])
    counts = ('run', 'passed_tests', 'failures', 'errors', 'skipped', 'expected_failures', 'unexpected_successes')
    return (all(type(row.get(k)) is int for k in counts)
            and isinstance(ids, list) and all(isinstance(i, str) and i for i in ids)
            and row.get('run') == expected and len(ids) == expected and len(set(ids)) == expected
            and row.get('passed_tests') == expected and row.get('origins_valid') is True
            and all(row.get(k) == 0 for k in ('failures', 'errors', 'skipped', 'expected_failures', 'unexpected_successes')))


def child(name, output):
    expected = dict(SUITES)[name]
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(ROOT))
    sys.dont_write_bytecode = True
    path = ROOT / (ORIGINAL if name == 'original' else 'tests/' + name)
    pattern = 'test_release_contracts.py' if name == 'original' else 'test_*.py'
    with (output / 'tests.log').open('w', encoding='utf-8') as log:
        suite = unittest.defaultTestLoader.discover(str(path), pattern=pattern)
        result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=RecordedResult).run(suite)
    origins = {}
    for key, module in tuple(sys.modules.items()):
        if key == 'bie' or key.startswith('bie.'):
            origin = getattr(module, '__file__', None)
            if origin:
                origins[key] = Path(origin).resolve()
    valid_origins = bool(origins) and all(p.is_relative_to((ROOT / 'bie').resolve()) for p in origins.values())
    row = dict(suite=name, expected=expected, run=result.testsRun, passed_tests=len(result.successes),
               failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
               expected_failures=len(result.expectedFailures), unexpected_successes=len(result.unexpectedSuccesses),
               test_ids=result.ids, origins_valid=valid_origins,
               module_origins={k: p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else 'OUTSIDE_CANONICAL_TREE'
                               for k, p in origins.items()})
    row['passed'] = valid_result(row, expected)
    (output / 'result.json').write_text(json.dumps(row, indent=2) + '\n', encoding='utf-8')
    return 0 if row['passed'] else 1


def run_suite(name, expected, output, timeout):
    started = time.monotonic()
    with (output / (name + '.log')).open('w', encoding='utf-8') as log:
        command = [sys.executable, '-B', str(Path(__file__).resolve()), '--child', name,
                   '--output', str(output / name)]
        proc = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(ROOT)},
                                start_new_session=os.name == 'posix')
        timed_out = False
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == 'posix':
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
            code = proc.wait()
    receipt = output / name / 'result.json'
    try:
        row = read_json(receipt) if receipt.exists() else dict(suite=name, expected=expected, run=0, passed=False)
        if not isinstance(row, dict) or row.get('suite') != name:
            raise ValueError('CHILD_RECEIPT_IDENTITY')
    except (OSError, ValueError, TypeError):
        row = dict(suite=name, expected=expected, run=0, passed=False, receipt_error='INVALID_CHILD_RECEIPT')
    row.update(exit_code=code, timeout=timed_out, duration_seconds=round(time.monotonic()-started, 3))
    row['passed'] = bool(code == 0 and not timed_out and valid_result(row, expected))
    print(f'{name}: {row.get("run", 0)}/{expected}, passed={row["passed"]}', flush=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    ap.add_argument('--verify-only', action='store_true')
    ap.add_argument('--child', choices=dict(SUITES))
    ap.add_argument('--suite', choices=dict(SUITES))
    ap.add_argument('--allow-dirty', action='store_true', help='local diagnostic only, recorded in receipt')
    ap.add_argument('--timeout', type=int, default=600)
    a = ap.parse_args()
    if a.child:
        if not a.output:
            ap.error('child output required')
        return child(a.child, a.output)
    adoption = verify_adoption(ROOT)
    if a.verify_only:
        print(json.dumps(adoption, indent=2))
        return 0
    if not a.output or a.output.exists() or a.timeout < 1 or a.timeout > 1800:
        ap.error('fresh output and timeout 1..1800 required')
    if not a.suite and platform.system() != 'Linux':
        ap.error('complete QA requires the approved Linux/native isolation profile; no Windows security fallback')
    before = candidate_binding(ROOT, a.allow_dirty)
    a.output.mkdir(parents=True)
    suites = [(a.suite, dict(SUITES)[a.suite])] if a.suite else SUITES
    rows = [run_suite(name, expected, a.output, a.timeout) for name, expected in suites]
    after_error = None
    try:
        after = candidate_binding(ROOT, a.allow_dirty)
        verify_adoption(ROOT)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        after = None
        after_error = type(exc).__name__ + ': ' + str(exc)
    ids = [r['suite'] + '::' + i for r in rows for i in r.get('test_ids', [])]
    passed = all(r['passed'] for r in rows) and before == after and len(ids) == len(set(ids))
    data = dict(schema_version='bie.qa.canonical-candidate-tests/1', passed=passed,
                candidate=before, candidate_unchanged=before == after, adoption=adoption,
                post_run_integrity_error=after_error,
                python=sys.version, platform=platform.platform(), suites=rows,
                executed_tests=sum(r.get('run', 0) for r in rows), unique_test_ids=len(set(ids)),
                full_section_suite=not bool(a.suite), full_canonical_regression=False,
                original_10_overlap_canonical=True, product_accepted=False)
    (a.output / 'TEST_RESULT.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in data.items() if k not in ('candidate', 'suites')}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
