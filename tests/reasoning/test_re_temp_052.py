import unittest,tempfile
from pathlib import Path
from bie.reasoning.temporal_package_inventory_audit import *

class T(unittest.TestCase):
    def test_ready(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bie/reasoning"; p.mkdir(parents=True); (p/"a.py").write_text("")
            r=audit_temporal_package(d,["a.py"]); self.assertTrue(r["ready"])
    def test_misplaced(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"app/bie/reasoning"; p.mkdir(parents=True); (p/"a.py").write_text("")
            r=audit_temporal_package(d,["a.py"]); self.assertEqual(r["misplaced"],("a.py",))
    def test_missing(self):
        with tempfile.TemporaryDirectory() as d:
            r=audit_temporal_package(d,["a.py"]); self.assertEqual(r["missing"],("a.py",))
