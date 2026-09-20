import unittest
from bie.visual_intelligence.director_handoff_adoption import *
def h(**kw):
 i=VisualIntent("i","diagram",("e",),("r",),{}); d=dict(handoff_id="d",revision=2,source_id="book",source_revision=7,narration_revision=3,intents=(i,),cues=(TimingCue("c","i",0,100,3),),current=True,invalidated_by=()); d.update(kw); return DirectorHandoff(**d)
class T(unittest.TestCase):
 def test_adopt(self): self.assertEqual(adopt(h(),"book",7).handoff_revision,2)
 def test_stale(self):
  with self.assertRaises(StaleDirectorHandoffError): adopt(h(current=False),"book",7)
 def test_invalidated(self):
  with self.assertRaises(StaleDirectorHandoffError): adopt(h(invalidated_by=("source",)),"book",7)
 def test_source_mismatch(self):
  with self.assertRaises(StaleDirectorHandoffError): adopt(h(),"book",8)
 def test_token(self): self.assertEqual(h().currentness_token,currentness(h()))
 def test_stage(self): self.assertEqual(stage_ref(adopt(h(),"book",7)).stage,"DIR_ADOPT")
