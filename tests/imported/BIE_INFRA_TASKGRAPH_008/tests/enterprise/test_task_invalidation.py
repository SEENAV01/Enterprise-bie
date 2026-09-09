
import unittest
from enterprise.task_invalidation import *
class T(unittest.TestCase):
 def test_invalidate_accepted(self): self.assertEqual(invalidate("x","ACCEPTED","upstream").previous_status,"ACCEPTED")
 def test_source_recorded(self): self.assertEqual(invalidate("x","QA_VERIFIED","dep","y").source_task_id,"y")
 def test_reason_required(self):
  with self.assertRaises(InvalidationError): invalidate("x","READY","")
 def test_double_rejected(self):
  with self.assertRaises(InvalidationError): invalidate("x","INVALIDATED","x")
 def test_reset(self):
  r=invalidate("x","ACCEPTED","change"); self.assertEqual(reset_after_invalidation(r,2)["status"],"PLANNED")
 def test_reset_version(self):
  r=invalidate("x","ACCEPTED","change")
  with self.assertRaises(InvalidationError): reset_after_invalidation(r,0)
if __name__=="__main__": unittest.main()
