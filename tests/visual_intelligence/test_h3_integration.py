import unittest,hashlib
from bie.visual_intelligence.uncertainty_propagation import *
from bie.visual_intelligence.asset_lifecycle import *
from bie.visual_intelligence.accessibility_integration import *
from bie.visual_intelligence.qa_trace_matrix import *
from bie.visual_intelligence.replay_currentness import *
class T(unittest.TestCase):
 def test_h3_path(self):
  u=propagate_uncertainty(claim_id='force',evidence=[UncertaintyEvidence('e',.95,'source')],stage_confidences={'rep':.9});self.assertTrue(enforce_visual_certainty(u,{'asserted_certain':False,'uncertainty_visible':False}))
  a=AssetLifecycle('a');a=transition(a,'REUSE_CANDIDATE','src');a=transition(a,'ACQUIRED','acq',uri='file://a',content_sha256=hashlib.sha256(b'a').hexdigest(),provenance_refs=('e',));a=transition(a,'GROUNDING_CHECKED','g',grounding_score=.9);a=transition(a,'RIGHTS_VERIFIED','r',rights_status='source-permitted');a=transition(a,'QUALITY_VERIFIED','q',quality_score=.9);a=transition(a,'READY','ready');self.assertTrue(production_ready(a))
  acc=integrate_accessibility([AccessibleVisualNode('v','diagram',font_px=20,alt_required=True,alt_mode='long_description')],contrast_results={'v':True});self.assertTrue(assert_accessible_for_handoff(acc))
  self.assertTrue(audit_trace([TraceRow('v',True,('e',),('r',),'rep','g','l',None,'a',('qa',),True)]).passed)
  vec=VersionVector(1,1,'1.0.0','1.0.0','web');rr=make_replay_record('run',vec,'input','output',('dir','grammar','asset'));self.assertTrue(assert_current(rr,vec,'input',('asset','dir','grammar')))
