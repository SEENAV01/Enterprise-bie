import unittest
from bie.visual_intelligence.semantic_constraint_engine import *
class T(unittest.TestCase):
 def test_all_33(self): self.assertEqual(len(POLICIES),33)
 def test_unknown(self):
  with self.assertRaises(SemanticPolicyError): evaluate({},["not-real"])
 def test_vector_frame(self): self.assertFalse(evaluate({"metadata":{}},["vectors require an explicit reference frame"]).passed)
 def test_crs(self): self.assertFalse(evaluate({"metadata":{}},["coordinate reference system is explicit"]).passed)
 def test_bond(self): self.assertFalse(evaluate({"relations":[{"id":"b","kind":"bond","payload":{}}]},["bond order is explicit"]).passed)
 def test_uncertainty(self): self.assertFalse(evaluate({"elements":[{"id":"x","role":"data","payload":{"uncertainty":.1}}]},["uncertainty/error values remain visible when supplied"]).passed)
 def test_flow(self): self.assertFalse(evaluate({"relations":[{"id":"f","kind":"flow","payload":{"declared_direction":"a","visual_direction":"b"}}]},["flow edges preserve declared direction"]).passed)
 def test_pass(self): self.assertTrue(evaluate({"metadata":{"reference_frame":"xy"}},["vectors require an explicit reference frame"]).passed)
