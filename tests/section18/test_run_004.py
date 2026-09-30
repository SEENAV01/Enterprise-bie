import tempfile,unittest
from bie.product_app.operator_service import OperatorError
from tests.section18.helpers import CONFIG,service
class Run004(unittest.TestCase):
 def test_status_comes_from_persisted_state(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];self.assertEqual(s.status(rid)["stages"][0]["state"],"PENDING")
 def test_unknown_run_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(OperatorError):service(t).status("app-run-ffffffffffffffff")
 def test_status_exposes_config_binding(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];self.assertEqual(s.status(rid)["config_hash"],CONFIG)
 def test_status_has_no_invented_percent(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];self.assertIsNone(s.status(rid)["progress_percent"])
