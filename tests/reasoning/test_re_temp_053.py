import unittest,tempfile
from pathlib import Path
from bie.reasoning.temporal_import_rewrite import *

class T(unittest.TestCase):
    def test_from_rewrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"t.py"; p.write_text("from app.bie.reasoning.x import y\n")
            self.assertTrue(rewrite_temporal_imports(str(p)))
            self.assertIn("from bie.reasoning.x import y",p.read_text())
    def test_import_rewrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"t.py"; p.write_text("import app.bie.reasoning.x\n")
            rewrite_temporal_imports(str(p))
            self.assertIn("import bie.reasoning.x",p.read_text())
    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"t.py"; p.write_text("from bie.reasoning.x import y\n")
            self.assertFalse(rewrite_temporal_imports(str(p)))
