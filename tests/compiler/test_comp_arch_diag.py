import unittest
from bie.compiler.compiler_diagnostics import *
class T(unittest.TestCase):
 def test_pass(self):self.assertTrue(build_diagnostic_report([make_diagnostic("I","INFO","load","ok")]).passed)
 def test_error(self):self.assertFalse(build_diagnostic_report([make_diagnostic("E","ERROR","load","bad")]).passed)
 def test_counts(self):
  r=build_diagnostic_report([make_diagnostic("E","ERROR","a","x"),make_diagnostic("W","WARNING","b","y")]);self.assertEqual((r.error_count,r.warning_count),(1,1))
 def test_dedupe(self):
  d=make_diagnostic("E","ERROR","a","x");self.assertEqual(len(build_diagnostic_report([d,d]).diagnostics),1)
 def test_exception(self):self.assertEqual(diagnostic_from_exception(ValueError("x"),"codegen").severity,"ERROR")
 def test_require(self):
  with self.assertRaises(ValueError):require_no_errors(build_diagnostic_report([make_diagnostic("E","ERROR","a","x")]))
