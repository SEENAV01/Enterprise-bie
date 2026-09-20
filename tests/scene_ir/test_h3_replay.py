import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.replay_currentness import *
class T(unittest.TestCase):
 def doc(self,text="x",rev=1):
  e=UnifiedElement("e","text",{"text":text},("s",),("r",))
  return UnifiedSceneIRDocument("scene","1.0.0","T",10,(e,),(),("s",),("r",),upstream_revision=rev)
 def vec(self,rev=1):return DSLVersionVector(rev,"1.0.0","web","prov:1","asset:1")
 def test_current(self):
  d=self.doc();r=make_replay_record(d,"input",self.vec(),{"ani":"a","source":"b"});self.assertTrue(evaluate_currentness(r,d,self.vec(),{"ani":"a","source":"b"}).current)
 def test_dep(self):
  d=self.doc();r=make_replay_record(d,"input",self.vec(),{"ani":"a"});x=evaluate_currentness(r,d,self.vec(),{"ani":"changed"});self.assertFalse(x.current);self.assertEqual(x.invalidated_dependencies,("ani",))
 def test_vector(self):
  d=self.doc();r=make_replay_record(d,"input",self.vec(),{});self.assertFalse(evaluate_currentness(r,d,self.vec(2),{}).current)
 def test_output(self):
  d=self.doc();r=make_replay_record(d,"input",self.vec(),{});self.assertFalse(evaluate_currentness(r,self.doc("changed"),self.vec(),{}).current)
 def test_require(self):
  d=self.doc();r=make_replay_record(d,"input",self.vec(),{});self.assertTrue(require_current(evaluate_currentness(r,d,self.vec(),{})))
 def test_not_accepted(self):
  d=self.doc();r=make_replay_record(d,"input",self.vec(),{});self.assertFalse(r.accepted)
