from pathlib import Path
import io
import tempfile
from types import SimpleNamespace
import unittest

from tools.run_section17_native_api_tests import ROOT, RecordedResult, native_module_origins


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
            key.startswith('setUpClass') and row['status'] == 'ERROR'
            for key, row in result.records.items()
        ))


if __name__ == '__main__':
    unittest.main()
