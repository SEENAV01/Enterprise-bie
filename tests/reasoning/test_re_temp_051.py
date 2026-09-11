import unittest, tempfile
from pathlib import Path
from bie.reasoning.temporal_test_runner_compatibility import *

class T(unittest.TestCase):
    def write(self,text):
        f=tempfile.NamedTemporaryFile("w",delete=False,suffix=".py"); f.write(text); f.close(); return f.name
    def test_unittest(self):
        p=self.write("import unittest\nclass T(unittest.TestCase):\n def test_x(self): pass\n")
        self.assertEqual(classify_test_file(p),"UNITTEST_COMPATIBLE")
    def test_pytest_only(self):
        p=self.write("def test_x():\n    assert True\n")
        self.assertEqual(classify_test_file(p),"PYTEST_FUNCTION_ONLY")
    def test_none(self):
        p=self.write("x=1\n")
        self.assertEqual(classify_test_file(p),"NO_DISCOVERABLE_TESTS")
