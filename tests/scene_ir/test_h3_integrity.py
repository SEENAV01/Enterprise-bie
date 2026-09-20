import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.document_integrity import *
class T(unittest.TestCase):
 def doc(self):
  e=UnifiedElement("e","text",{"text":"x","nested":{"a":[1,2]}},("s",),("r",))
  t=UnifiedTrack("t","e","reveal",0,10,{"opacity":[0,1]},("s",),("r",))
  return UnifiedSceneIRDocument("s","1.0.0","T",10,(e,),(t,),("s",),("r",),metadata={"x":{"y":[1]}})
 def test_pass(self):self.assertTrue(inspect_document_integrity(self.doc()).passed)
 def test_deep(self):self.assertTrue(inspect_document_integrity(self.doc()).deep_immutable)
 def test_mutation_blocked(self):
  d=self.doc()
  with self.assertRaises(TypeError):d.metadata["x"]["y"]=()
 def test_fp(self):self.assertEqual(inspect_document_integrity(self.doc()).stored_fingerprint,inspect_document_integrity(self.doc()).recomputed_fingerprint)
 def test_require(self):self.assertTrue(require_integrity(inspect_document_integrity(self.doc())))
 def test_not_accepted(self):self.assertFalse(inspect_document_integrity(self.doc()).accepted)
