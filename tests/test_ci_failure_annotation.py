"""Task 037B: CI failure summaries surface as bounded, escaped GitHub annotations."""
from pathlib import Path
import contextlib, io, json, sys, tempfile, unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import ci_failure_annotation as annotate

TRANSCRIPT = """test_ok (m.C.test_ok) ... ok
test_bad (m.C.test_bad) ... FAIL

======================================================================
FAIL: test_bad (m.C.test_bad)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "m.py", line 3, in test_bad
    self.assertEqual(1, 2)
AssertionError: 1 != 2 : child stderr follows
RuntimeError: test barrier timeout

======================================================================
ERROR: test_boom (m.C.test_boom)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "m.py", line 5, in test_boom
    raise RuntimeError('x')
RuntimeError: x

----------------------------------------------------------------------
Ran 3 tests in 0.1s

FAILED (failures=1, errors=1)
"""


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = annotate.main(list(args))
    return code, out.getvalue().splitlines()


class CiFailureAnnotation(unittest.TestCase):
    def test_failing_receipts_become_single_line_annotations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lane = root / 'native' / 'resource-controls'
            lane.mkdir(parents=True)
            (root / 'native' / 'VALIDATION.json').write_text(json.dumps({'passed': False, 'lanes': [
                {'name': 'resource-controls', 'exit_code': 1, 'duration_s': 4.2, 'passed': False}]}))
            (root / 'native' / 'resource-controls.stderr.log').write_text('line 1\n100% done\nboom: last\n')
            (lane / 'TEST_RESULT.json').write_text(json.dumps({'passed': False, 'tests_run': 3, 'failures': 1, 'errors': 1}))
            (lane / 'TEST_RESULT.txt').write_text(TRANSCRIPT)
            (root / 'ok').mkdir()
            (root / 'ok' / 'TEST_RESULT.json').write_text(json.dumps({'passed': True, 'tests_run': 9}))
            code, lines = run('Section 18: native, render', str(root), str(root / 'missing'))
        self.assertEqual(code, 0)
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(line.startswith('::error title=') for line in lines))
        self.assertIn('Section 18%3A native%2C render (native/VALIDATION.json)::', lines[0])
        self.assertIn('resource-controls=FAIL(exit 1, 4.2s)', lines[0])
        self.assertIn('100%25 done%0Aboom: last', lines[0])
        self.assertIn('FAIL: test_bad (m.C.test_bad) :: AssertionError: 1 != 2 : child stderr follows%0ARuntimeError: test barrier timeout', lines[1])
        self.assertNotIn('Ran 3 tests', lines[1])
        self.assertIn('ERROR: test_boom (m.C.test_boom) :: RuntimeError: x', lines[1])

    def test_generic_failed_receipt_reports_failure_and_last_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'render-cellular-standard.json').write_text(json.dumps({'passed': False,
                'failure': {'code': 'CHILD_GATE'}, 'proof': {'passed': False, 'failure': {'code': 'NPM_SETUP'},
                'cases': [{'preferences': [{'phase': 'H3_SOURCE'}, {'phase': 'H3_TEST_PUBLICATION'}]}]}}))
            (root / 'other.json').write_text(json.dumps({'passed': True}))
            _, lines = run('M1 render', tmp)
        self.assertEqual(len(lines), 1)
        self.assertIn('M1 render (render-cellular-standard.json)', lines[0].replace('%3A', ':'))
        self.assertIn('"proof_failure": {"code": "NPM_SETUP"}', lines[0])
        self.assertIn('"last_phase": "H3_TEST_PUBLICATION"', lines[0])

    def test_no_failing_receipt_still_leaves_a_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, lines = run('Gate', tmp)
        self.assertEqual((code, len(lines)), (0, 1))
        self.assertIn('No failing evidence receipt found', lines[0])

    def test_canonical_summary_lists_failed_files_and_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results = [{'path': f'tests/t{i}.py', 'passed': False, 'failures': 1, 'errors': 0} for i in range(30)]
            (root / 'integrated_tests.json').write_text(json.dumps({'summary': {'passed': False, 'tests_run': 5,
                'failures': 30, 'errors': 0, 'skipped': 0, 'failed_files': 30}, 'results': results}))
            _, lines = run('Canonical', tmp)
        self.assertEqual(len(lines), 1)
        self.assertIn('tests/t9.py', lines[0])
        self.assertNotIn('tests/t10.py', lines[0])
        self.assertLess(len(lines[0]), annotate.MESSAGE_LIMIT + 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
