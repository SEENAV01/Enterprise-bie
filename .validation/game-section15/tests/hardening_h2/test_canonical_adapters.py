import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.handoff_engine.canonical_adapters import adapt_canonical_upstream,CANONICAL_BLOBS
from bie.game_engine.director_engine.planner import plan_experience
from tests.hardening_h2.support import *
class Tests(unittest.TestCase):
 def test_adapts_current_canonical_shapes(self):
  r=adapt_canonical_upstream(*canonical_inputs());self.assertEqual(r.canonical_blob_ids,CANONICAL_BLOBS);self.assertEqual(r.director_context.decision.primary.value,'manipulation');self.assertFalse(r.product_accepted)
 def test_preserves_evidence_ids(self):
  r=adapt_canonical_upstream(*canonical_inputs());self.assertTrue({'source:book','reason:ped','obj:motion','mis:direction'}<=set(r.evidence_ids))
 def test_director_plan_from_canonical_adapter(self):self.assertTrue(plan_experience(adapt_canonical_upstream(*canonical_inputs()).director_context).plan_fingerprint.startswith('sha256:'))
 def test_review_required_fails_closed(self):
  with self.assertRaises(GameContractError):adapt_canonical_upstream(*canonical_inputs(review=True))
 def test_low_confidence_fails_closed(self):
  with self.assertRaises(GameContractError):adapt_canonical_upstream(*canonical_inputs(confidence=.5))
 def test_unresolved_status_fails_closed(self):
  with self.assertRaises(GameContractError):adapt_canonical_upstream(*canonical_inputs(status='AMBIGUOUS'))
 def test_missing_digest_fails_closed(self):
  gh,rg,pp,d=canonical_inputs()
  with self.assertRaises(GameContractError):adapt_canonical_upstream(gh,rg,pp,d[:-1])
 def test_unknown_mechanic_fails_closed(self):
  gh,rg,pp,d=canonical_inputs();
  with self.assertRaises(GameContractError):adapt_canonical_upstream(gh,replace(rg,mechanic='unknown'),pp,d)
 def test_map_requires_coordinates_instead_of_guessing(self):
  gh,rg,pp,d=canonical_inputs(mechanic='map_interaction')
  with self.assertRaisesRegex(GameContractError,'GAME_UPSTREAM_MAP_COORDINATES_REQUIRED'):adapt_canonical_upstream(gh,rg,pp,d)
 def test_blob_identities_are_pinned(self):self.assertEqual(len(CANONICAL_BLOBS),3);self.assertTrue(all(len(sha)==40 for _,sha in CANONICAL_BLOBS))
