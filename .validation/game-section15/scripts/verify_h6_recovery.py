"""Run the portable recovered DSL gate and existing core regressions honestly."""
from pathlib import Path
import hashlib
import io
import json
import platform
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.verify_dsl_traceability import verify

def run():
    report = {'schema_version': 'bie.game.h6.recovery-verification/1',
              'python': platform.python_version(), 'platform': platform.platform(),
              'traceability': verify(ROOT), 'groups': {},
              'h6_complete': False, 'github_integrated': False, 'product_accepted': False}
    groups = {'dsl_core': 'tests/dsl_core', 'h6_hardening': 'tests/hardening_h6',
              'state': 'tests/state_engine', 'mechanics': 'tests/mechanics_engine'}
    evidence = ROOT / 'evidence/h6_recovery'
    evidence.mkdir(parents=True, exist_ok=True)
    source_rows = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted((ROOT / 'bie').rglob('*.py'))}
    source_bytes = json.dumps(source_rows, sort_keys=True, separators=(',', ':')).encode()
    report['source_inventory_sha256'] = hashlib.sha256(source_bytes).hexdigest()
    (evidence / 'source_hashes.json').write_bytes(source_bytes + b'\n')
    for name, folder in groups.items():
        log = io.StringIO()
        suite = unittest.TestLoader().discover(str(ROOT / folder), top_level_dir=str(ROOT))
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
        (evidence / (name + '.log')).write_text(log.getvalue(), encoding='utf-8')
        report['groups'][name] = {'run': result.testsRun, 'failures': len(result.failures),
                                'errors': len(result.errors), 'skips': len(result.skipped),
                                'passed': result.wasSuccessful() and not result.skipped}
        print(name, report['groups'][name], flush=True)
    excluded = {'test_real_html_browser_smoke.py': 'Historical browser test disables the Chromium sandbox; not accepted as H6 browser evidence.',
                'test_real_typescript_compile.py': 'Requires tsc on PATH; strict compilation executed separately with the exact locked TypeScript dependency.'}
    log = io.StringIO()
    modules = ['tests.compiler_engine.' + p.stem for p in sorted((ROOT / 'tests/compiler_engine').glob('test_*.py')) if p.name not in excluded]
    suite = unittest.TestLoader().loadTestsFromNames(modules)
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (evidence / 'compiler_portable.log').write_text(log.getvalue(), encoding='utf-8')
    report['groups']['compiler_portable'] = {'run': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skips': len(result.skipped), 'passed': result.wasSuccessful() and not result.skipped}
    report['compiler_exclusions'] = excluded
    print('compiler_portable', report['groups']['compiler_portable'], flush=True)
    report['full_runtime_regression'] = {'status': 'NOT_RUN',
        'reason': 'Inherited bounded process runner imports Linux resource/prctl and requires a Linux Chromium sandbox; no configured Linux runtime is available on this Windows host.'}
    report['tests_run'] = sum(g['run'] for g in report['groups'].values())
    report['portable_gate_passed'] = all(g['passed'] for g in report['groups'].values())
    (evidence / 'RESULT.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return 0 if report['portable_gate_passed'] else 1

if __name__ == '__main__':
    raise SystemExit(run())
