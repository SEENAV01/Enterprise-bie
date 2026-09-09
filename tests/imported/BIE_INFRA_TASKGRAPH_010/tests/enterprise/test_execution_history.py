
import unittest
from enterprise.execution_history import *
class T(unittest.TestCase):
 def test_sequence(self):
  h=ExecutionHistory(); self.assertEqual(h.append("x","START","IN_PROGRESS","worker").seq,1)
 def test_increment(self):
  h=ExecutionHistory(); h.append("x","A","READY","w"); self.assertEqual(h.append("x","B","IN_PROGRESS","w").seq,2)
 def test_filter(self):
  h=ExecutionHistory(); h.append("x","A","READY","w"); h.append("y","A","READY","w"); self.assertEqual(len(h.for_task("x")),1)
 def test_latest(self):
  h=ExecutionHistory(); h.append("x","A","READY","w"); self.assertEqual(h.latest("x").status,"READY")
 def test_missing_latest(self): self.assertIsNone(ExecutionHistory().latest("x"))
 def test_evidence(self):
  h=ExecutionHistory(); self.assertEqual(h.append("x","TEST","UNIT_TESTED","ci",["e"]).evidence_refs,("e",))
 def test_required(self):
  with self.assertRaises(HistoryError): ExecutionHistory().append("","A","READY","w")
if __name__=="__main__": unittest.main()
