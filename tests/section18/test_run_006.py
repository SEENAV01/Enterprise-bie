import tempfile,unittest
from tests.section18.helpers import CONFIG,fail_stage,service
class Run006(unittest.TestCase):
 def test_failure_view_has_diagnostics_evidence_owner(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];fail_stage(s,rid);f=s.failures(rid)["failures"][0];self.assertEqual(f["diagnostics"],["synthetic failure"]);self.assertEqual(f["evidence_refs"],["evidence:test"]);self.assertEqual(f["remediation_owner"],"QA")
 def test_no_failure_returns_empty(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];self.assertTrue(s.failures(rid)["empty"])
 def test_failure_state_is_not_hidden(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];fail_stage(s,rid);self.assertEqual(s.failures(rid)["failures"][0]["state"],"FAILED")
 def test_failure_view_not_acceptance(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];self.assertFalse(s.failures(rid)["product_accepted"])
