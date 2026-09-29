"""Positive and seeded-negative controls for QA candidate evidence ownership."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('section16_gate_under_test', ROOT / 'scripts/section16_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class Section16GateTests(unittest.TestCase):
    def row(self):
        return dict(run=2, passed_tests=2, test_ids=['a', 'b'], origins_valid=True,
                    failures=0, errors=0, skipped=0, expected_failures=0, unexpected_successes=0)

    def test_exact_inherited_denominator(self):
        self.assertEqual(len(gate.SUITES), 32)
        self.assertEqual(sum(count for _, count in gate.SUITES), 4856)
        self.assertEqual(len(set(n for n, _ in gate.SUITES)), 32)

    def test_original_tests_map_to_canonical_migration(self):
        self.assertEqual(gate.ORIGINAL, 'tests/imported/BIE_QA_RELEASE_001/tests/qa')
        self.assertEqual(dict(gate.SUITES)['original'], 10)

    def test_exact_adoption_verifies(self):
        result = gate.verify_adoption(ROOT)
        self.assertTrue(result['passed'])
        self.assertEqual(result['paths'], 817)

    def changed_manifest(self, mutate, code):
        data = copy.deepcopy(gate.read_json(ROOT / gate.MANIFEST))
        mutate(data)
        with patch.object(gate, 'read_json', return_value=data):
            with self.assertRaisesRegex(ValueError, code):
                gate.verify_adoption(ROOT)

    def test_missing_manifest_row_rejected(self):
        self.changed_manifest(lambda d: d['paths'].pop(), 'ADOPTION_COUNT')

    def test_duplicate_row_rejected(self):
        self.changed_manifest(lambda d: d['paths'].__setitem__(1, d['paths'][0]), 'DUPLICATE_PATH')

    def test_changed_bytes_rejected(self):
        self.changed_manifest(lambda d: d['paths'][0].update(sha256='0'*64), 'ADOPTION_BYTES')

    def test_boolean_size_rejected(self):
        self.changed_manifest(lambda d: d['paths'][0].update(size=True), 'ADOPTION_BYTES')

    def test_source_overwrite_not_authorized(self):
        self.changed_manifest(lambda d: d.update(source_overwrites=['bie/qa/__init__.py']), 'MANIFEST_SCOPE')

    def test_product_claim_rejected(self):
        self.changed_manifest(lambda d: d.update(product_accepted=True), 'MANIFEST_SCOPE')

    def test_manifest_version_rejected(self):
        self.changed_manifest(lambda d: d.update(schema_version='unknown'), 'MANIFEST_VERSION')

    def test_positive_result(self):
        self.assertTrue(gate.valid_result(self.row(), 2))

    def test_boolean_count_fails(self):
        row = self.row(); row['errors'] = False
        self.assertFalse(gate.valid_result(row, 2))

    def test_invalid_id_type_fails(self):
        row = self.row(); row['test_ids'] = ['a', None]
        self.assertFalse(gate.valid_result(row, 2))

    def test_missing_ids_fail(self):
        row = self.row(); row.pop('test_ids')
        self.assertFalse(gate.valid_result(row, 2))

    def test_duplicate_ids_fail(self):
        row = self.row(); row['test_ids'] = ['a', 'a']
        self.assertFalse(gate.valid_result(row, 2))

    def test_count_change_fails(self):
        self.assertFalse(gate.valid_result(self.row(), 3))

    def test_skipped_test_fails(self):
        row = self.row(); row['skipped'] = 1
        self.assertFalse(gate.valid_result(row, 2))

    def test_expected_failure_is_not_pass(self):
        row = self.row(); row['expected_failures'] = 1
        self.assertFalse(gate.valid_result(row, 2))

    def test_error_is_not_pass(self):
        row = self.row(); row['errors'] = 1
        self.assertFalse(gate.valid_result(row, 2))

    def test_failure_is_not_pass(self):
        row = self.row(); row['failures'] = 1
        self.assertFalse(gate.valid_result(row, 2))

    def test_foreign_module_origin_fails(self):
        row = self.row(); row['origins_valid'] = False
        self.assertFalse(gate.valid_result(row, 2))

    def test_unsafe_paths_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('../outside', '/absolute', 'C:/drive', 'a\\b', 'a//b', './a', ''):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    gate.safe_path(Path(tmp), name)

    def test_safe_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(gate.safe_path(Path(tmp), 'x/y.py'), Path(tmp) / 'x/y.py')

    def test_duplicate_json_keys_fail(self):
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_JSON_KEY'):
            json.loads('{"passed":false,"passed":true}', object_pairs_hook=gate.unique_pairs)


if __name__ == '__main__':
    unittest.main()
