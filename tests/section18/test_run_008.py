import tempfile,unittest
from bie.product_app.operator_service import OperatorError
from tests.section18.helpers import CONFIG,service
class Run008(unittest.TestCase):
 def active(self,t):
  s=service(t);rid=s.create_run(CONFIG)["run_id"];s.persistence.set_run_state(rid,"ACTIVE");return s,rid
 def test_pause_is_request_until_worker_ack(self):
  with tempfile.TemporaryDirectory() as t:
   s,rid=self.active(t);r=s.request_control(rid,"PAUSE","maintenance");self.assertFalse(r["effective"]);self.assertTrue(r["worker_ack_required"])
 def test_ack_makes_control_effect_explicit(self):
  with tempfile.TemporaryDirectory() as t:
   s,rid=self.active(t);r=s.request_control(rid,"PAUSE","maintenance");a=s.acknowledge_control(r["request_id"],"worker-1");self.assertTrue(a["effective"])
 def test_resume_requires_effective_pause(self):
  with tempfile.TemporaryDirectory() as t:
   s,rid=self.active(t)
   with self.assertRaises(OperatorError):s.request_control(rid,"RESUME","resume")
 def test_resume_after_ack_is_request(self):
  with tempfile.TemporaryDirectory() as t:
   s,rid=self.active(t);p=s.request_control(rid,"PAUSE","pause");s.acknowledge_control(p["request_id"],"worker-1");r=s.request_control(rid,"RESUME","resume");self.assertEqual(r["action"],"RESUME")
 def test_cancel_completed_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];s.persistence.set_run_state(rid,"EXECUTION_COMPLETE")
   with self.assertRaises(OperatorError):s.request_control(rid,"CANCEL","stop")
 def test_second_pending_control_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   s,rid=self.active(t);s.request_control(rid,"PAUSE","pause")
   with self.assertRaises(OperatorError):s.request_control(rid,"CANCEL","cancel")
