
import unittest
from bie.infrastructure.evidence_api import *
class S:
 def __init__(self):self.x=[{"ref":"e","run_id":"r","gate":"render"}]
 def get(self,k):return self.x[0] if k=="e" else None
 def for_run(self,r):return [x for x in self.x if x["run_id"]==r]
class T(unittest.TestCase):
 def test_get(self):self.assertEqual(EvidenceAPI(S()).get("e")["gate"],"render")
 def test_missing(self):
  with self.assertRaises(EvidenceAPIError):EvidenceAPI(S()).get("x")
 def test_run(self):self.assertEqual(len(EvidenceAPI(S()).for_run("r")),1)
 def test_gate(self):self.assertEqual(len(EvidenceAPI(S()).for_gate("r","render")),1)
 def test_gate_none(self):self.assertEqual(len(EvidenceAPI(S()).for_gate("r","game")),0)
if __name__=="__main__":unittest.main()
