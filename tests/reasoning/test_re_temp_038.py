import unittest
from bie.reasoning.temporal_derived_lineage import *
class T(unittest.TestCase):
 def test_lineage(self):
  r=build_derived_temporal_result("r3","A before C",["r2","r1"],["e2","e1"])
  self.assertEqual(r.parent_result_ids,("r1","r2")); self.assertEqual(r.evidence_ids,("e1","e2"))
 def test_parent_required(self):
  with self.assertRaises(ValueError): build_derived_temporal_result("r","x",[])
 def test_self_parent(self):
  with self.assertRaises(ValueError): build_derived_temporal_result("r","x",["r"])
 def test_identity_required(self):
  with self.assertRaises(ValueError): build_derived_temporal_result("","x",["p"])
