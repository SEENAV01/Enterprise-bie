import unittest

from scripts.section17_gate import EXPECTED_METHODS, complete


class Section17GateTests(unittest.TestCase):
    def receipt(self):
        return {
            'all_passed': True,
            'source_changed_during_run': False,
            'native_module_origins_valid': True,
            'external_dependency_snapshot_used': False,
            'tests_run': EXPECTED_METHODS,
            'unique_test_method_ids': EXPECTED_METHODS,
            'records': [
                {'test_id': f'section17.test_{i}', 'status': 'PASS'}
                for i in range(EXPECTED_METHODS)
            ],
            'failed': 0,
            'errors': 0,
            'skipped': 0,
        }

    def test_complete_identity_passes(self):
        self.assertTrue(complete(self.receipt(), 0))

    def test_missing_original_method_fails(self):
        value = self.receipt()
        value['records'].pop()
        self.assertFalse(complete(value, 0))

    def test_duplicate_identity_fails(self):
        value = self.receipt()
        value['records'][0]['test_id'] = value['records'][1]['test_id']
        self.assertFalse(complete(value, 0))

    def test_failed_or_skipped_method_fails(self):
        for status in ('FAIL', 'ERROR', 'SKIP'):
            with self.subTest(status=status):
                value = self.receipt()
                value['records'][0]['status'] = status
                self.assertFalse(complete(value, 0))

    def test_source_change_fails(self):
        value = self.receipt()
        value['source_changed_during_run'] = True
        self.assertFalse(complete(value, 0))

    def test_runner_failure_fails(self):
        self.assertFalse(complete(self.receipt(), 1))

    def test_foreign_module_origin_fails(self):
        value = self.receipt()
        value['native_module_origins_valid'] = False
        self.assertFalse(complete(value, 0))

    def test_external_snapshot_fails(self):
        value = self.receipt()
        value['external_dependency_snapshot_used'] = True
        self.assertFalse(complete(value, 0))


if __name__ == '__main__':
    unittest.main()
