import unittest,hashlib
from bie.animation_intelligence.simulation_execution_receipt import *
H=hashlib.sha256(b"x").hexdigest()
def R(**kw):
 d=dict(receipt_id="r",engine="sim",engine_version="1",model_fingerprint=H,seed=1,input_hash=H,output_hash=H,observed_execution=True,verified=True,deterministic=True);d.update(kw);return SimulationExecutionReceipt(**d)
class T(unittest.TestCase):
 def test_valid(self):self.assertTrue(validate_receipt(R()))
 def test_claim(self):self.assertEqual(classify_simulation_claim(R()),"VERIFIED_OBSERVED_EXECUTION")
 def test_declared(self):self.assertEqual(classify_simulation_claim(None,True),"DECLARED_MODEL_OUTPUT")
 def test_concept(self):self.assertEqual(classify_simulation_claim(),"CONCEPTUAL_ANIMATION")
 def test_unverified(self):
  with self.assertRaises(SimulationReceiptError):validate_receipt(R(verified=False))
 def test_hash(self):
  with self.assertRaises(SimulationReceiptError):validate_receipt(R(input_hash="x"))
 def test_seed(self):
  with self.assertRaises(SimulationReceiptError):validate_receipt(R(seed=True))
 def test_not_accepted(self):self.assertFalse(R().accepted)
