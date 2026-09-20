import unittest
from bie.animation_intelligence.ani_realbook_harness import *
H="a"*64
def F(fid="physics:force",domain="physics",actions=("vector",)):
 return RealBookFixture(fid,domain,"REAL_BOOK","book://fixture","licensed_or_user_supplied",H,True,actions)
class T(unittest.TestCase):
 def test_validate(self):self.assertTrue(validate_fixture(F()))
 def test_pass(self):self.assertEqual(evaluate_realbook_case(F(),("vector",)).status,"PASS")
 def test_missing(self):self.assertEqual(evaluate_realbook_case(F(),()).status,"BLOCKED")
 def test_unexpected(self):self.assertEqual(evaluate_realbook_case(F(),("vector","camera")).status,"BLOCKED")
 def test_independent(self):
  with self.assertRaises(RealBookHarnessError):validate_fixture(RealBookFixture("x","physics","REAL_BOOK","x","x",H,False,("a",)))
 def test_source_kind(self):
  with self.assertRaises(RealBookHarnessError):validate_fixture(RealBookFixture("x","physics","SYNTHETIC","x","x",H,True,("a",)))
 def test_three_domains(self):
  rs=[evaluate_realbook_case(F("physics:a","physics",("a",)),("a",)),
      evaluate_realbook_case(F("biology:b","biology",("b",)),("b",)),
      evaluate_realbook_case(F("economics:c","economics",("c",)),("c",))]
  self.assertEqual(section_realbook_status(rs),"PASS")
 def test_empirical_notrun(self):self.assertEqual(evaluate_realbook_case(F(),("vector",)).empirical_render_status,"NOT_RUN")
 def test_not_accepted(self):self.assertFalse(evaluate_realbook_case(F(),("vector",)).accepted)
