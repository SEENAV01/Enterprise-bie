import tempfile,unittest
from bie.product_app.operator_service import OperatorError
from tests.section18.helpers import CONFIG,service
class Run001(unittest.TestCase):
 def test_create_persists_canonical_run(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);r=s.create_run(CONFIG);self.assertEqual(r["run_state"],"CREATED");self.assertEqual(r["profile"],"pdf_inspection_v1")
 def test_config_hash_required(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(OperatorError):service(t).create_run("bad")
 def test_unsupported_profile_fails_closed(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(OperatorError):service(t).create_run(CONFIG,"fake")
 def test_no_fake_progress(self):
  with tempfile.TemporaryDirectory() as t:self.assertIsNone(service(t).create_run(CONFIG)["progress_percent"])
 def test_product_acceptance_false(self):
  with tempfile.TemporaryDirectory() as t:self.assertFalse(service(t).create_run(CONFIG)["product_accepted"])
