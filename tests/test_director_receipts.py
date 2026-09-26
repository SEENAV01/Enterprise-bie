import unittest
from dataclasses import replace
from bie.game_engine.director_engine.fixtures import director_context
from bie.game_engine.director_engine.planner import plan_experience
from bie.game_engine.director_engine.studio_policy import audit_studio_quality
from bie.game_engine.director_engine.receipts import create_director_receipt
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_receipt(self):
  p=plan_experience(director_context());r=create_director_receipt(p,audit_studio_quality(p));self.assertEqual(r.plan_fingerprint,p.plan_fingerprint);self.assertEqual(len(r.component_fingerprints),10);self.assertFalse(r.product_accepted)
 def test_receipt_deterministic(self):
  p=plan_experience(director_context());q=audit_studio_quality(p);self.assertEqual(create_director_receipt(p,q),create_director_receipt(p,q))
 def test_receipt_schema_fail_closed(self):
  p=plan_experience(director_context());r=create_director_receipt(p,audit_studio_quality(p))
  with self.assertRaises(GameContractError):replace(r,schema_version='bad').validate()
