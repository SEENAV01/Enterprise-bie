import unittest
from bie.game_engine.mechanics_engine import parameter
from bie.game_engine.mechanics_engine.common import sample_context
class ReceiptTests(unittest.TestCase):
 def test_action_changes_receipt(self):
  _,_,a=parameter.execute(sample_context(),{'value':1},1,(0,10));_,_,b=parameter.execute(sample_context(),{'value':1},2,(0,10));self.assertNotEqual(a.receipt_id,b.receipt_id);self.assertNotEqual(a.action_fingerprint,b.action_fingerprint)
 def test_same_action_same_receipt(self):
  _,_,a=parameter.execute(sample_context(),{'value':1},1,(0,10));_,_,b=parameter.execute(sample_context(),{'value':1},1,(0,10));self.assertEqual(a,b)
