import tempfile,unittest
from bie.product_app.operator_service import OperatorError
from tests.section18.helpers import CONFIG,fail_stage,service
class Run007(unittest.TestCase):
 def test_failed_stage_gets_new_ready_attempt(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];fail_stage(s,rid);r=s.retry_stage(rid,"PDF_INSPECTION","operator retry");self.assertEqual((r["attempt"],r["state"]),(2,"READY"));self.assertTrue(r["dispatch_required"])
 def test_nonfailed_retry_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"]
   with self.assertRaises(OperatorError):s.retry_stage(rid,"PDF_INSPECTION","retry")
 def test_retry_reason_required(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];fail_stage(s,rid)
   with self.assertRaises(OperatorError):s.retry_stage(rid,"PDF_INSPECTION","")
 def test_retry_preserves_previous_attempt(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];fail_stage(s,rid);s.retry_stage(rid,"PDF_INSPECTION","retry");a=s.persistence.load_run_state(rid)["stages"]["PDF_INSPECTION"]["attempts"];self.assertEqual([x["state"] for x in a],["FAILED","READY"])
