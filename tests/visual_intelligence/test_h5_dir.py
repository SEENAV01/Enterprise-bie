import unittest
from bie.visual_intelligence.canonical_dir_codec import *
def rec(v=False):return CanonicalDirSourceReceipt(CANONICAL_DIR_COMMIT,CANONICAL_DIR_TREE,71,59,683,v)
def raw(**kw):
 d={'handoff_id':'d','revision':1,'source_id':'book','source_revision':1,'narration_revision':1,'current':True,'invalidated_by':[],'visual_intents':[{'intent_id':'i','intent_type':'vector','evidence_refs':['e'],'reasoning_refs':['r'],'payload':{}}],'timing_cues':[{'cue_id':'c','intent_id':'i','start_ms':0,'end_ms':10,'narration_revision':1,'cue_type':'visual'}]};d.update(kw);return d
class T(unittest.TestCase):
 def test_fixture(self):self.assertEqual(decode_canonical_dir_packet(raw(),rec(),False).source_id,'book')
 def test_strict(self):
  with self.assertRaises(ExactDirSourceUnavailableError):decode_canonical_dir_packet(raw(),rec(),True)
 def test_verified(self):self.assertFalse(decode_canonical_dir_packet(raw(),rec(True),True).accepted)
 def test_commit(self):
  with self.assertRaises(CanonicalDirCodecError):decode_canonical_dir_packet(raw(),CanonicalDirSourceReceipt('x',CANONICAL_DIR_TREE,71,59,683,True),True)
 def test_stale(self):
  with self.assertRaises(StaleCanonicalDirArtifactError):decode_canonical_dir_packet(raw(current=False),rec(True),True)
