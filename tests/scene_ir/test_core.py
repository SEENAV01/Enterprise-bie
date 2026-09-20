import unittest
from bie.scene_ir.scene_ir_contract import *
def E(i="e"):return SceneElement(i,"text",("src",),("r",),{"text":"x"},{"alt":"x"})
def Tr(i="t",elem="e",en=100):return SceneTrack(i,elem,"reveal",0,en,{},("src",),("r",))
def S(**kw):
 d=dict(scene_id="s",schema_version="1.0.0",title="Scene",duration_ms=100,elements=(E(),),tracks=(Tr(),),source_refs=("src",),reasoning_refs=("r",));d.update(kw);return SceneIR(**d)
class TestCore(unittest.TestCase):
 def test_build(self):self.assertTrue(S().ir_fingerprint)
 def test_deterministic(self):self.assertEqual(S().ir_fingerprint,S().ir_fingerprint)
 def test_unknown_element(self):
  with self.assertRaises(SceneIRError):S(tracks=(Tr(elem="x"),))
 def test_duplicate_element(self):
  with self.assertRaises(SceneIRError):S(elements=(E(),E()))
 def test_duplicate_track(self):
  with self.assertRaises(SceneIRError):S(tracks=(Tr(),Tr()))
 def test_duration(self):
  with self.assertRaises(SceneIRError):S(tracks=(Tr(en=101),))
 def test_lineage(self):
  with self.assertRaises(SceneIRError):SceneElement("e","text",(),("r",))
 def test_version(self):
  with self.assertRaises(SceneIRError):S(schema_version="2.0.0")
 def test_not_accepted(self):self.assertFalse(S().accepted)
