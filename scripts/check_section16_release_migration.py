"""Explicit current-worktree release migration tests; never load ZIP source."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import platform
import sys
import unittest


class RecordedResult(unittest.TextTestResult):
    def startTest(self, test):
        if not hasattr(self, 'ids'):
            self.ids = []
        self.ids.append(test.id())
        super().startTest(test)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('checkout', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    root = args.checkout.resolve()
    if root != Path(__file__).resolve().parents[1]:
        raise ValueError('Run only against this script\'s canonical checkout')
    args.output.mkdir(parents=True, exist_ok=False)
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(root), str(root / 'tests/director')]
    paths = {
        'tests/imported/BIE_QA_RELEASE_001/tests/qa/test_release_contracts.py': 10,
        'tests/director/test_qa_contracts.py': 8,
        'tests/test_section16_release_migration.py': 15,
        'tests/assembly/test_section16_release_amendment.py': 14,
    }
    all_results = []
    for relative, count in paths.items():
        name = 'candidate_' + hashlib.sha256(relative.encode()).hexdigest()[:16]
        spec = importlib.util.spec_from_file_location(name, root / relative)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        log = io.StringIO()
        result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=RecordedResult).run(
            unittest.defaultTestLoader.loadTestsFromModule(module))
        (args.output / (name + '.txt')).write_text(log.getvalue(), encoding='utf-8', newline='\n')
        row = dict(path=relative, tests_run=result.testsRun, expected=count,
            failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
            test_ids=result.ids, passed=result.wasSuccessful() and result.testsRun==count and not result.skipped)
        all_results.append(row)
        print(json.dumps({key: value for key, value in row.items() if key!='test_ids'}), flush=True)
    import bie.qa.release_contracts as actual
    assert Path(actual.__file__).resolve() == root / 'bie/qa/release_contracts.py'
    ids = [test for row in all_results for test in row['test_ids']]
    bound_paths = list(paths) + ['scripts/check_section16_release_migration.py', 'bie/qa/release_contracts.py', 'scripts/audit_canonical.py',
        'scripts/section16_release_amendment.py', 'manifests/qa_section16_release_amendment.json',
        'manifests/lossless_migration.csv']
    receipt = dict(schema_version='bie.qa.release-migration-test/1',
        executed_at_utc=datetime.now(timezone.utc).isoformat(), platform=platform.platform(),
        python=sys.version, scope='CURRENT_CANONICAL_WORKTREE_RELEASE_COMPATIBILITY_ONLY',
        tests_run=len(ids), unique_tests=len(set(ids)), results=all_results,
        passed=all(row['passed'] for row in all_results) and len(ids)==len(set(ids)),
        file_sha256={path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in bound_paths},
        full_canonical_regression=False, section_signed_off=False, product_accepted=False)
    (args.output / 'TEST_RESULT.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: value for key, value in receipt.items() if key not in ('results', 'file_sha256')}))
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
