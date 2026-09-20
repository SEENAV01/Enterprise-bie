import unittest
from bie.visual_intelligence.actual_visual_e2e import *
from bie.visual_intelligence.canonical_dir_codec import *
def rec(v=False):return CanonicalDirSourceReceipt(CANONICAL_DIR_COMMIT,CANONICAL_DIR_TREE,71,59,683,v)
def d():return {'handoff_id':'d','revision':1,'source_id':'book','source_revision':1,'narration_revision':1,'current':True,'invalidated_by':[],'visual_intents':[{'intent_id':'i','intent_type':'vector','evidence_refs':['e'],'reasoning_refs':['r'],'payload':{}}],'timing_cues':[{'cue_id':'c','intent_id':'i','start_ms':0,'end_ms':10,'narration_revision':1,'cue_type':'visual'}]}
def r():return {'decision_id':'rep','domain':'physics','representation':'vector_diagram','confidence':.9,'evidence_refs':['e'],'reasoning_refs':['r'],'tags':['vector']}
GI={'vectors':[{'id':'F','direction':[1,0],'source_ids':['e']}],'frame_id':'xy','scale':1.0}
class T(unittest.TestCase):
 def test_strict_dir_block(self):self.assertEqual(run_actual_visual_e2e(dir_raw=d(),dir_receipt=rec(False),rep_raw=r(),rep_archives_verified=False,grammar_inputs=GI).status,'BLOCKED')
 def test_strict_rep_block(self):self.assertEqual(run_actual_visual_e2e(dir_raw=d(),dir_receipt=rec(True),rep_raw=r(),rep_archives_verified=False,grammar_inputs=GI).status,'BLOCKED')
 def test_fixture_runs_actual_families(self):
  x=run_actual_visual_e2e(dir_raw=d(),dir_receipt=rec(False),rep_raw=r(),rep_archives_verified=False,grammar_inputs=GI,allow_contract_fixture=True);self.assertIn('QA',x.completed_stages);self.assertEqual(x.family_status,'PASS');self.assertEqual(x.status,'REVIEW')
 def test_verified(self):self.assertEqual(run_actual_visual_e2e(dir_raw=d(),dir_receipt=rec(True),rep_raw=r(),rep_archives_verified=True,grammar_inputs=GI).status,'PASS')
 def test_not_accepted(self):self.assertFalse(run_actual_visual_e2e(dir_raw=d(),dir_receipt=rec(True),rep_raw=r(),rep_archives_verified=True,grammar_inputs=GI).accepted)
