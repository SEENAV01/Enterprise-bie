import unittest,hashlib
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.provenance_resolution import *
class T(unittest.TestCase):
 def doc(self):
  e=UnifiedElement("e","text",{"text":"x"},("src",),("reason",))
  t=UnifiedTrack("t","e","reveal",0,10,{},("src",),("reason",))
  return UnifiedSceneIRDocument("s","1.0.0","T",10,(e,),(t,),("src",),("reason",))
 def regs(self):
  h="a"*64
  return {"src":{"current":True,"confidence":.9,"evidence_hash":h}},{"reason":{"current":True,"confidence":.8,"evidence_hash":h}}
 def test_pass(self):
  s,r=self.regs();self.assertTrue(resolve_provenance(self.doc(),s,r).passed)
 def test_missing(self):
  s,r=self.regs();s={};self.assertIn("source_ref_unresolved:src",resolve_provenance(self.doc(),s,r).blockers)
 def test_stale(self):
  s,r=self.regs();s["src"]["current"]=False;self.assertFalse(resolve_provenance(self.doc(),s,r).passed)
 def test_confidence(self):
  s,r=self.regs();r["reason"]["confidence"]=.1;self.assertFalse(resolve_provenance(self.doc(),s,r,min_confidence=.5).passed)
 def test_hash(self):
  s,r=self.regs();s["src"]["evidence_hash"]="";self.assertFalse(resolve_provenance(self.doc(),s,r).passed)
 def test_not_accepted(self):
  s,r=self.regs();self.assertFalse(resolve_provenance(self.doc(),s,r).accepted)
