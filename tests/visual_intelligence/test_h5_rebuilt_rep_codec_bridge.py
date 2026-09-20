import unittest
from bie.visual_intelligence.representation_core import SemanticIntent
from bie.visual_intelligence.rep001_candidates import generate
from bie.visual_intelligence.rep_original_codec import decode_rep_decision
class T(unittest.TestCase):
 def test_rebuilt_rep_candidate_enters_h5_codec(self):
  intent=SemanticIntent("force","physics",("force",),("e",),("r",),("structure",))
  c=generate(intent)[0]
  raw={"decision_id":c.candidate_id,"revision":1,"domain":intent.domain,"representation":c.representation,
       "confidence":c.base_confidence,"evidence_refs":c.evidence_refs,"reasoning_refs":c.reasoning_refs,
       "required_capabilities":c.capabilities,"tags":intent.semantic_tags,"current":True}
  x=decode_rep_decision(raw,source_archives_verified=True,require_exact_source=True)
  self.assertTrue(x.source_archives_verified);self.assertEqual(x.evidence_refs,("e",))
