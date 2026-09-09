import unittest
from bie.knowledge_intelligence.crossmodal_corroboration import *
class T(unittest.TestCase):
 def test_contract(self):
  r=fuse([{"semantic_key":"k","modality":"TEXT","confidence":.8},{"semantic_key":"k","modality":"FIGURE","confidence":.7}]);self.assertEqual(r["status"],"CORROBORATED")
  self.assertGreater(r["confidence"],.8)
  self.assertEqual(fuse([{"semantic_key":"k","modality":"TEXT","confidence":.8}])["status"],"SINGLE_SOURCE")
  with self.assertRaises(E):fuse([])
