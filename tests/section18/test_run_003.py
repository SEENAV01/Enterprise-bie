import tempfile,unittest
from bie.product_app.html_views import source_validation_html
from tests.section18.helpers import CONFIG,PDF,service
class Run003(unittest.TestCase):
 def test_missing_validation_is_truthful(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];self.assertEqual(s.source_validation(rid)["status"],"MISSING")
 def test_valid_view_html_has_live_status(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];s.import_source(rid,"book.pdf","application/pdf",PDF);h=source_validation_html(s.source_validation(rid));self.assertIn('role="status"',h);self.assertIn("VALID",h)
 def test_html_escapes_errors(self):
  h=source_validation_html({"status":"INVALID","errors":["<script>x</script>"]});self.assertNotIn("<script>",h)
 def test_validation_never_claims_product_acceptance(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];self.assertFalse(s.source_validation(rid)["product_accepted"])
