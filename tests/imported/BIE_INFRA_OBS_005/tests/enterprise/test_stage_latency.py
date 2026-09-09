
import unittest
from enterprise.stage_latency import *
class T(unittest.TestCase):
 def test_empty(self): self.assertEqual(StageLatency().summary("x")["count"],0)
 def test_one(self): m=StageLatency();m.record("x",2);self.assertEqual(m.summary("x")["avg"],2)
 def test_many(self): m=StageLatency();m.record("x",1);m.record("x",3);self.assertEqual(m.summary("x")["avg"],2)
 def test_negative(self):
  with self.assertRaises(LatencyError): StageLatency().record("x",-1)
 def test_stage_required(self):
  with self.assertRaises(LatencyError): StageLatency().record("",1)
if __name__=="__main__": unittest.main()
