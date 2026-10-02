"""Explicit supported-POSIX repair and inherited symlink gates; never a stub.

The repair cases use canonical synthetic proposals and the real native journal,
controller and worker. They do not establish real-book or product acceptance.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import io
import json
import os
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(relative):
    path = ROOT / relative
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(1, parent)
    name = 's18_posix_' + hashlib.sha256(relative.encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scope', choices=('all', 'repair', 'game', 'render'), default='all')
    args = parser.parse_args()
    if os.name != 'posix' or not hasattr(os, 'O_NOFOLLOW'):
        raise SystemExit('NOT_RUN: supported POSIX required; no security fallback')
    cases = []
    if args.scope in ('all', 'repair'):
        repair = load('tests/section18/test_posix_assurance.py')
        release = load('tests/section17/test_rel_004.py')
        cases.extend(unittest.defaultTestLoader.loadTestsFromTestCase(repair.NativePosixRepair))
        cases.extend(release.ReleaseLedger004(name) for name in
                     ('test_symlink_database_refused', 'test_symlink_parent_refused'))
    if args.scope in ('all', 'game'):
        game = load('tests/section18/test_native_preview_game.py')
        cases.extend(unittest.defaultTestLoader.loadTestsFromTestCase(game.NativePreviewGame))
    if args.scope in ('all', 'render'):
        render = load('tests/section18/test_native_preview_render.py')
        cases.extend(unittest.defaultTestLoader.loadTestsFromTestCase(render.NativePreviewRender))
    ids = [case.id() for case in cases]
    expected = dict(all=11, repair=5, game=3, render=3)[args.scope]
    assert len(ids) == len(set(ids)) == expected
    transcript = io.StringIO()
    result = unittest.TextTestRunner(stream=transcript, verbosity=2).run(unittest.TestSuite(cases))
    origins = {}
    for name, module in list(sys.modules.items()):
        filename = getattr(module, '__file__', None)
        if filename and name.startswith(('bie.', 'apps.')):
            path = Path(filename).resolve()
            assert path.is_relative_to(ROOT), 'EXTERNAL_MODULE_ORIGIN:' + name
            origins[name] = dict(path=path.relative_to(ROOT).as_posix(),
                                 sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    receipt = dict(schema='bie.section18.posix-validation/1', tests_run=result.testsRun,
                   unique_method_ids=ids, failures=len(result.failures), errors=len(result.errors),
                   skipped=len(result.skipped), passed=result.wasSuccessful() and not result.skipped,
                   origins=origins, scope=args.scope,
                   real_native_repair_methods=3 if args.scope in ('all', 'repair') else 0,
                   real_native_game_methods=3 if args.scope in ('all', 'game') else 0,
                   real_native_render_methods=3 if args.scope in ('all', 'render') else 0,
                   inherited_symlink_methods=2 if args.scope in ('all', 'repair') else 0,
                   security_guards_modified=False, synthetic_evidence=True,
                   real_book_acceptance=False, product_accepted=False)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'TEST_RESULT.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (args.output / 'TEST_RESULT.txt').write_text(transcript.getvalue(), encoding='utf-8')
    print(json.dumps({key: value for key, value in receipt.items() if key not in
                      ('origins', 'unique_method_ids')}, sort_keys=True))
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
