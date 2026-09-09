
import unittest
from bie.model_gateway.decision_evidence import *
class T(unittest.TestCase):
 def e(self,**k):
  d=dict(decision_id="d",candidate_ids=("a","b"),selected_id="a",reason_codes=("capability",),inputs_hash="a"*64);d.update(k);return DecisionEvidence(**d)
 def test_ok(self):self.assertTrue(validate(self.e()))
 def test_selected(self):
  with self.assertRaises(DecisionEvidenceError):validate(self.e(selected_id="x"))
 def test_reason(self):
  with self.assertRaises(DecisionEvidenceError):validate(self.e(reason_codes=()))
 def test_hash(self):
  with self.assertRaises(DecisionEvidenceError):validate(self.e(inputs_hash="x"))
if __name__=="__main__":unittest.main()
