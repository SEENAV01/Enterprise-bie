import unittest
from bie.visual_intelligence.realbook_fixtures import *
class T(unittest.TestCase):
 def test_reference_pack(self):
  f=reference_nonacceptance_fixtures();self.assertTrue(validate_fixture_pack(f));self.assertEqual(len(f),6)
 def test_domains(self):self.assertEqual(set(x.domain for x in reference_nonacceptance_fixtures()),set(DOMAINS))
 def test_not_acceptance(self):self.assertEqual(acceptance_coverage(reference_nonacceptance_fixtures())["acceptance_eligible"],0)
 def test_source_required(self):
  f=RealBookFixture("x","physics",SourceSpan("s","sp",""),("c",),"vector","g",(),"synthetic_reference",False)
  with self.assertRaises(RealBookFixtureError):validate_fixture(f)
 def test_acceptance_origin(self):
  f=RealBookFixture("x","physics",SourceSpan("s","sp","text"),("c",),"vector","g",(),"synthetic_reference",True)
  with self.assertRaises(RealBookFixtureError):validate_fixture(f)
 def test_verified_eligible(self):
  f=RealBookFixture("x","physics",SourceSpan("book","p1","verified excerpt","uri"),("c",),"vector","g",(),"verified_textbook_excerpt",True);self.assertTrue(validate_fixture(f))
 def test_duplicate(self):
  f=reference_nonacceptance_fixtures()[0]
  with self.assertRaises(RealBookFixtureError):validate_fixture_pack([f,f],require_domains=False)
