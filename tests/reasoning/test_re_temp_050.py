import unittest, tempfile
from pathlib import Path
from bie.reasoning.temporal_canonical_namespace_migration import *

class T(unittest.TestCase):
    def test_migrates_modules(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"app/bie/reasoning"; p.mkdir(parents=True)
            (p/"__init__.py").write_text("")
            (p/"x.py").write_text("X=1")
            out=migrate_temporal_module_tree(d)
            self.assertEqual(out,("bie/reasoning/x.py",))
            self.assertTrue((Path(d)/"bie/reasoning/x.py").exists())
    def test_skips_init(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"app/bie/reasoning"; p.mkdir(parents=True)
            (p/"__init__.py").write_text("BAD=1")
            self.assertEqual(migrate_temporal_module_tree(d),())
    def test_missing_source(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                migrate_temporal_module_tree(d)
