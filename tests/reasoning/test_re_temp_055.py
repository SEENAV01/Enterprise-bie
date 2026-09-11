import unittest, tempfile, sys
from pathlib import Path
from bie.reasoning.temporal_unittest_bridge_014_018 import *

class T(unittest.TestCase):
    def test_discovers_functions(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"mymod.py"
            p.write_text("def test_a():\n    assert True\ndef helper():\n    pass\n")
            sys.path.insert(0,d)
            try:
                funcs=load_legacy_test_functions("mymod")
                self.assertEqual([x[0] for x in funcs],["test_a"])
            finally:
                sys.path.remove(d); sys.modules.pop("mymod",None)

    def test_builds_unittest_case(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"mymod2.py"
            p.write_text("def test_a():\n    assert 1+1==2\n")
            sys.path.insert(0,d)
            try:
                case=build_unittest_case("mymod2")
                suite=unittest.defaultTestLoader.loadTestsFromTestCase(case)
                result=unittest.TestResult(); suite.run(result)
                self.assertEqual(result.testsRun,1)
                self.assertEqual(len(result.failures)+len(result.errors),0)
            finally:
                sys.path.remove(d); sys.modules.pop("mymod2",None)

    def test_empty_module(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"mymod3.py"; p.write_text("x=1\n")
            sys.path.insert(0,d)
            try:
                case=build_unittest_case("mymod3")
                suite=unittest.defaultTestLoader.loadTestsFromTestCase(case)
                self.assertEqual(suite.countTestCases(),0)
            finally:
                sys.path.remove(d); sys.modules.pop("mymod3",None)
