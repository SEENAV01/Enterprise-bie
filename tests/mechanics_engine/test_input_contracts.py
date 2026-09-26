import unittest
from bie.game_engine.mechanics_engine.input_contracts import *
class InputContractTests(unittest.TestCase):
 def test_classification_item(self):self.assertEqual(ClassificationItem.from_mapping({'id':'i','class':'A'}).category,'A')
 def test_model_part(self):self.assertEqual(ModelPart.from_mapping({'id':'arm','requires':['base']}).requires,('base',))
 def test_simulation_model(self):self.assertEqual(SimulationModel.from_mapping({'kind':'linear','parameters':{'coefficient':2,'offset':1}}).coefficient,2)
 def test_timeline_event(self):self.assertEqual(TimelineEvent.from_mapping({'id':'e','time':2}).time,2)
 def test_sourced_location(self):self.assertEqual(SourcedMapLocation.from_mapping('A',{'coord':(1,2),'source_ref':'s'}).source_ref,'s')
 def test_diagnostic_step(self):self.assertEqual(DiagnosticStep.from_mapping({'actual':1,'expected':2,'evidence_ref':'s'},0).step_id,'step:0')
 def test_retrieval_item(self):self.assertEqual(RetrievalItem.from_mapping({'id':'i','prompt_ref':'p','answer_ref':'a','evidence_ref':'s'}).answer_ref,'a')
 def test_bad_location_fails(self):
  with self.assertRaises(Exception):SourcedMapLocation.from_mapping('A',{'coord':(100,0),'source_ref':'s'})
