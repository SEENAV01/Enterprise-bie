import unittest
from bie.scene_ir.unified_scene_ir_contract import UnifiedElement,UnifiedTrack,UnifiedSceneIRDocument
from bie.scene_ir.provenance_resolution import resolve_provenance
from bie.scene_ir.asset_contract import AssetRegistry,AssetRecord,resolve_assets
from bie.scene_ir.document_integrity import inspect_document_integrity
from bie.scene_ir.replay_currentness import DSLVersionVector,make_replay_record,evaluate_currentness
from bie.scene_ir.dsl_orchestrator import validate_scene_ir_document

class T(unittest.TestCase):
 def doc(self):
  img=UnifiedElement("img","image",{"asset_ref":"asset:img"},("src",),("reason",),{"alt":"Cell"})
  tr=UnifiedTrack("t","img","reveal",0,100,{},("src",),("reason",))
  return UnifiedSceneIRDocument("scene","1.0.0","Title",100,(img,),(tr,),("src",),("reason",),upstream_revision=3)

 def test_trust_chain(self):
  d=self.doc()
  h="a"*64
  p=resolve_provenance(d,{"src":{"current":True,"confidence":.95,"evidence_hash":h}},{"reason":{"current":True,"confidence":.9,"evidence_hash":h}})
  self.assertTrue(p.passed)

  ar=AssetRegistry()
  ar.register(AssetRecord("asset:img","asset://img","b"*64,"licensed","image/png",True,"src"))
  self.assertTrue(resolve_assets(d,ar).passed)
  self.assertTrue(inspect_document_integrity(d).passed)
  self.assertTrue(validate_scene_ir_document(d).passed)

  vec=DSLVersionVector(3,"1.0.0","web","prov:snapshot","asset:snapshot")
  replay=make_replay_record(d,"ani-input",vec,{"ani":"ani-fp","source":"source-fp"})
  self.assertTrue(evaluate_currentness(replay,d,vec,{"ani":"ani-fp","source":"source-fp"}).current)

 def test_changed_dependency_invalidates(self):
  d=self.doc()
  vec=DSLVersionVector(3,"1.0.0","web","prov:snapshot","asset:snapshot")
  replay=make_replay_record(d,"ani-input",vec,{"ani":"ani-fp"})
  receipt=evaluate_currentness(replay,d,vec,{"ani":"changed"})
  self.assertFalse(receipt.current)
  self.assertEqual(receipt.invalidated_dependencies,("ani",))
