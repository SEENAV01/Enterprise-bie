
import unittest
from bie.infrastructure.run_timeline import *
class T(unittest.TestCase):
 def test_seq(self): self.assertEqual(RunTimeline().add("r","start",1).seq,1)
 def test_stage(self): self.assertEqual(RunTimeline().add("r","x",1,"s").stage_id,"s")
 def test_filter(self):
  t=RunTimeline();t.add("r","a",1);t.add("q","a",2);self.assertEqual(len(t.for_run("r")),1)
 def test_nonmono(self):
  t=RunTimeline();t.add("r","a",2)
  with self.assertRaises(TimelineError): t.add("r","b",1)
 def test_required(self):
  with self.assertRaises(TimelineError): RunTimeline().add("","a",1)
if __name__=="__main__": unittest.main()
