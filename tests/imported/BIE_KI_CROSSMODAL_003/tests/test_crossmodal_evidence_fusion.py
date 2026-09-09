import unittest
from bie.knowledge_intelligence.crossmodal_evidence_fusion import *
class T(unittest.TestCase):
 def test_contract(self):
  i=[{"semantic_key":"k","modality":"TEXT","confidence":.9,"anchor_id":"p1"},{"semantic_key":"k","modality":"FIGURE","confidence":.8,"anchor_id":"p2"}];r=fuse(i)
  self.assertEqual(r["semantic_key"],"k")
  self.assertEqual(r["anchors"],("p1","p2"))
  self.assertGreater(r["confidence"],.8)
  with self.assertRaises(E):fuse([])
