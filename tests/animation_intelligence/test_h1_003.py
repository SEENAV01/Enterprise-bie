import unittest
from bie.animation_intelligence.ani_orchestrator import *
def H(block=None):
 d={}
 for s in STAGES:d[s]=(lambda x:(lambda a:(a+[x],StageReceipt(x,OWNERS[x],"BLOCKED" if x==block else "PASS",x))))(s)
 return d
class T(unittest.TestCase):
 def test_pass(self):self.assertTrue(run_pipeline(H(),[])[1].passed)
 def test_order(self):self.assertEqual(tuple(run_pipeline(H(),[])[0]),STAGES)
 def test_block(self):self.assertFalse(run_pipeline(H("DOMAIN"),[])[1].passed)
 def test_missing(self):
  d=H();d.pop("QA")
  with self.assertRaises(AniOrchestratorError):run_pipeline(d,[])
 def test_not_accepted(self):self.assertFalse(run_pipeline(H(),[])[1].accepted)
