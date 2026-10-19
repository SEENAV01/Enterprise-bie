"""Task 037B: the Remotion tree report separates real version drift from nested foreign packages."""
from pathlib import Path
import contextlib, io, json, sys, tempfile, unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import remotion_tree_report as tree


def lock(**entries):
    return {'lockfileVersion': 3, 'packages': {'': {}, **{k: {'version': v} for k, v in entries.items()}}}


class RemotionTreeReport(unittest.TestCase):
    def test_consistent_tree_passes(self):
        result = tree.report(lock(**{'node_modules/remotion': '4.0.506', 'node_modules/@remotion/cli': '4.0.506',
                                     'node_modules/zod': '4.5.0'}))
        self.assertEqual(result, {'remotion': '4.0.506', 'pairing_check_passes': True,
                                  'remotion_packages': [], 'nested_foreign_packages': []})

    def test_nested_foreign_package_is_named_separately_from_remotion_drift(self):
        result = tree.report(lock(**{
            'node_modules/remotion': '4.0.506',
            'node_modules/@remotion/studio': '4.0.506',
            'node_modules/@remotion/studio/node_modules/zod': '4.4.3',
            'node_modules/@remotion/player': '4.0.507',
            'node_modules/@remotion/studio/node_modules/@remotion/media': '4.0.507'}))
        self.assertFalse(result['pairing_check_passes'])
        self.assertEqual(result['nested_foreign_packages'], ['node_modules/@remotion/studio/node_modules/zod@4.4.3'])
        self.assertEqual(result['remotion_packages'], ['node_modules/@remotion/player@4.0.507',
                                                       'node_modules/@remotion/studio/node_modules/@remotion/media@4.0.507'])

    def test_main_prints_one_annotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'package-lock.json'
            path.write_text(json.dumps(lock(**{'node_modules/remotion': '4.0.506',
                                               'node_modules/@remotion/studio/node_modules/zod': '4.4.3'})))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(tree.main(['canary: latest', str(path)]), 0)
            missing = io.StringIO()
            with contextlib.redirect_stdout(missing):
                tree.main(['installed', str(Path(tmp) / 'absent.json')])
        self.assertTrue(out.getvalue().startswith('::warning title=Remotion tree canary%3A latest::'))
        self.assertIn('"error": "FileNotFoundError"', missing.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
