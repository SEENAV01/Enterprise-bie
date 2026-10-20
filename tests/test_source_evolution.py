"""Task 037C: working source may evolve after adoption; evidence stays byte-exact.

These tests run the real ledger verifiers on the real repository and change the bytes they
read in memory only (no file is written): a changed working-source file must pass and be
reported as evolved, while a changed evidence file must still fail.
"""
from contextlib import contextmanager
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))
import source_evolution as policy  # noqa: E402

PINNED_CODE = 'bie/model_gateway/model_interface.py'          # in manifests/lossless_migration.csv
PINNED_EVIDENCE = 'batches/BIE_AST_001/TASK_RESULT.json'       # archived evidence row, same ledger
SECTION17_CODE = 'bie/evaluation/benchmarks/__init__.py'        # Section 17 adoption map
CHAIN_CODE = 'bie/compiler/real_paint.py'                        # read by the compiler amendment chain


@contextmanager
def changed(*relatives):
    """Every read of the given files returns their bytes plus one extra line."""
    targets = {(ROOT / r).resolve() for r in relatives}
    original = Path.read_bytes

    def read_bytes(self):
        data = original(self)
        try:
            hit = self.resolve() in targets
        except OSError:
            hit = False
        return data + b'\n# changed in memory by tests/test_source_evolution.py\n' if hit else data

    with patch.object(Path, 'read_bytes', read_bytes):
        yield


class Policy(unittest.TestCase):
    def test_working_source_prefixes_only(self):
        for path in ('bie/model_gateway/model_interface.py', 'apps/api/main.py', 'tests/x/test_y.py',
                     'tools/run.py', 'scripts/audit_canonical.py'):
            self.assertTrue(policy.is_working_source(path), path)
        for path in ('batches/x.json', 'historical/x.py', 'backups/a.zip', 'docs/evidence/x.py',
                     'docs/productization/x.before', 'manifests/lossless_migration.csv', '.gitattributes',
                     'metadata/section17/x.json', '../bie/x.py', '/bie/x.py', 'bie/../manifests/x', '', 'bie\\x.py'):
            self.assertFalse(policy.is_working_source(path), path)

    def test_accepts_exact_bytes_anywhere_and_changed_bytes_only_for_working_source(self):
        self.assertTrue(policy.accepts('docs/evidence/x', 'a' * 64, 'a' * 64))
        self.assertFalse(policy.accepts('docs/evidence/x', 'a' * 64, 'b' * 64))
        self.assertTrue(policy.accepts('bie/x.py', 'a' * 64, 'b' * 64))


class LedgerVerifiers(unittest.TestCase):
    def audit(self):
        import audit_canonical
        return audit_canonical.audit(ROOT)

    def test_lossless_ledger_accepts_evolved_code(self):
        clean = self.audit()
        self.assertTrue(clean['passed'], clean['errors'][:5])
        # Working source evolves through reviewed PRs, so the live tree may already report evolved files.
        before = set(clean['working_source_evolved_paths'])
        self.assertNotIn(PINNED_CODE, before)
        with changed(PINNED_CODE):
            result = self.audit()
        self.assertTrue(result['passed'], result['errors'][:5])
        self.assertEqual(set(result['working_source_evolved_paths']), before | {PINNED_CODE})
        self.assertEqual(result['working_source_evolved_since_adoption'], len(before) + 1)

    def test_lossless_ledger_still_rejects_changed_evidence(self):
        with changed(PINNED_EVIDENCE):
            result = self.audit()
        self.assertFalse(result['passed'])
        self.assertIn('Canonical content mismatch: ' + PINNED_EVIDENCE, result['errors'])

    def test_section17_adoption_accepts_evolved_code_and_rejects_changed_preimage(self):
        import verify_section17_adoption as section17
        with changed(SECTION17_CODE):
            result = section17.verify()
        self.assertTrue(result['passed'], result['errors'][:5])
        self.assertIn(SECTION17_CODE, result['working_source_evolved_paths'])
        with changed(section17.MAINTENANCE_DIR + '/runtime.py.before'):
            with self.assertRaises(ValueError):
                section17.verify()


class CompilerAmendmentChain(unittest.TestCase):
    def validators(self):
        import importlib
        names = ('compiler_capture_observation_amendment', 'compiler_media_policy_observation_amendment',
                 'compiler_monitor_snapshot_amendment', 'compiler_stitch_input_amendment')
        return [importlib.import_module(name).validate for name in names]

    def test_chain_authenticates_the_baseline_copy_not_the_live_file(self):
        self.assertEqual(policy.verify_baseline(ROOT), [])
        with changed(CHAIN_CODE, 'scripts/verify_post_dir.py'):
            for validate in self.validators():
                validate(ROOT)

    def test_changed_baseline_copy_fails_the_chain_and_the_inventory(self):
        copy = policy.BASELINE_DIR + CHAIN_CODE
        with changed(copy):
            self.assertEqual(policy.verify_baseline(ROOT), ['SOURCE_BASELINE_BYTES:' + CHAIN_CODE])
            with self.assertRaises(ValueError):
                for validate in self.validators():
                    validate(ROOT)

    def test_baseline_covers_only_working_source(self):
        import json
        manifest = json.loads((ROOT / policy.BASELINE_DIR / 'BASELINE.json').read_text(encoding='utf-8'))
        self.assertTrue(manifest['files'])
        self.assertTrue(all(policy.is_working_source(row['path']) for row in manifest['files']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
