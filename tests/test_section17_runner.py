from pathlib import Path
import io
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.run_section17_native_api_tests import ROOT, RecordedResult, browser_environment, native_module_origins


class Section17RunnerOriginTests(unittest.TestCase):
    def test_canonical_file_and_namespace_pass(self):
        modules = {
            'bie': SimpleNamespace(__file__=str(ROOT / 'bie/__init__.py')),
            'bie.evaluation': SimpleNamespace(__path__=[str(ROOT / 'bie/evaluation')]),
        }
        origins, valid = native_module_origins(modules)
        self.assertTrue(valid)
        self.assertEqual(origins['bie'], ['bie/__init__.py'])

    def test_external_bie_module_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            foreign = Path(directory) / 'source.py'
            foreign.write_text('fixture = True\n')
            origins, valid = native_module_origins({'bie.foreign': SimpleNamespace(__file__=str(foreign))})
        self.assertFalse(valid)
        self.assertEqual(origins['bie.foreign'], ['OUTSIDE_CANONICAL_SOURCE'])

    def test_mixed_namespace_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            _, valid = native_module_origins({
                'bie.evaluation': SimpleNamespace(__path__=[str(ROOT / 'bie/evaluation'), directory]),
            })
        self.assertFalse(valid)

    def test_missing_or_empty_origins_rejected(self):
        self.assertFalse(native_module_origins({})[1])
        self.assertFalse(native_module_origins({'bie.unknown': SimpleNamespace()})[1])

    def test_fixture_level_error_is_preserved(self):
        class BrokenFixture(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise RuntimeError('fixture boom')
            def test_never_runs(self):
                pass

        result = unittest.TextTestRunner(
            stream=io.StringIO(),
            verbosity=0,
            resultclass=RecordedResult,
        ).run(unittest.defaultTestLoader.loadTestsFromTestCase(BrokenFixture))
        self.assertEqual(len(result.errors), 1)
        self.assertTrue(any(
            row['test_id'].startswith('setUpClass') and row['status'] == 'ERROR'
            for row in result.fixture_events
        ))


class Section17FailureRecordingTests(unittest.TestCase):
    @staticmethod
    def run_cases(*cases):
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in cases)
        return unittest.TextTestRunner(stream=io.StringIO(), resultclass=RecordedResult).run(suite)

    def test_setup_error_is_recorded_and_next_class_runs(self):
        class Broken(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise RuntimeError('seeded setup error')
            def test_not_run(self):
                self.fail('setup should prevent execution')
        class Good(unittest.TestCase):
            def test_runs(self):
                pass
        result = self.run_cases(Broken, Good)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.fixture_events[0]['status'], 'ERROR')
        self.assertEqual(next(iter(result.records.values()))['status'], 'PASS')

    def test_teardown_error_keeps_method_identity(self):
        class Broken(unittest.TestCase):
            def test_runs(self):
                pass
            @classmethod
            def tearDownClass(cls):
                raise RuntimeError('seeded teardown error')
        result = self.run_cases(Broken)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(result.testsRun, len(result.records))
        self.assertEqual(result.fixture_events[0]['status'], 'ERROR')

    def test_class_skip_is_recorded_separately(self):
        class Skipped(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise unittest.SkipTest('seeded class skip')
            def test_not_run(self):
                pass
        result = self.run_cases(Skipped)
        self.assertEqual(result.testsRun, 0)
        self.assertEqual(result.records, {})
        self.assertEqual(result.fixture_events[0]['status'], 'SKIP')

    def test_expected_failure_is_not_recorded_as_pass(self):
        class Expected(unittest.TestCase):
            @unittest.expectedFailure
            def test_failure(self):
                self.fail('seeded expected failure')
        result = self.run_cases(Expected)
        self.assertEqual(next(iter(result.records.values()))['status'], 'EXPECTED_FAILURE')

    def test_browser_directories_are_private_and_restored(self):
        original = {'XDG_CONFIG_HOME': 'existing-config', 'XDG_CACHE_HOME': 'existing-cache'}
        with patch.dict(os.environ, original):
            with browser_environment():
                paths = [Path(os.environ[key]) for key in original]
                self.assertTrue(all(path.is_dir() for path in paths))
                self.assertTrue(all(str(path) != original[key] for key, path in zip(original, paths)))
            self.assertEqual({key: os.environ[key] for key in original}, original)
            self.assertTrue(all(not path.exists() for path in paths))

    def test_browser_environment_restored_after_failure(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'seeded'):
                with browser_environment():
                    raise RuntimeError('seeded')
            self.assertNotIn('XDG_CONFIG_HOME', os.environ)
            self.assertNotIn('XDG_CACHE_HOME', os.environ)


if __name__ == '__main__':
    unittest.main()
