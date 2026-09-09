
import unittest
from bie.infrastructure.task_lifecycle import *
class T(unittest.TestCase):
 def test_plan_ready(self): self.assertEqual(transition("x","PLANNED","READY","deps met").to_status,"READY")
 def test_ready_progress(self): self.assertEqual(transition("x","READY","IN_PROGRESS","start").to_status,"IN_PROGRESS")
 def test_progress_impl(self): self.assertEqual(transition("x","IN_PROGRESS","IMPLEMENTED","code").to_status,"IMPLEMENTED")
 def test_skip_rejected(self):
  with self.assertRaises(LifecycleError): transition("x","PLANNED","ACCEPTED","x",["e"])
 def test_verified_needs_evidence(self):
  with self.assertRaises(LifecycleError): transition("x","IMPLEMENTED","UNIT_TESTED","tests")
 def test_verified_with_evidence(self): self.assertEqual(transition("x","IMPLEMENTED","UNIT_TESTED","tests",["e"]).to_status,"UNIT_TESTED")
 def test_accept_needs_evidence(self):
  with self.assertRaises(LifecycleError): transition("x","QA_VERIFIED","ACCEPTED","ok")
 def test_invalidate_accepted(self): self.assertEqual(transition("x","ACCEPTED","INVALIDATED","upstream changed").to_status,"INVALIDATED")
 def test_empty_reason(self):
  with self.assertRaises(LifecycleError): transition("x","PLANNED","READY","")
if __name__=="__main__": unittest.main()
