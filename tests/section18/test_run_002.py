import tempfile,unittest
from bie.product_app.operator_service import OperatorError
from tests.section18.helpers import CONFIG,PDF,service
class Run002(unittest.TestCase):
 def test_valid_pdf_is_cas_backed(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];v=s.import_source(rid,"book.pdf","application/pdf",PDF);self.assertTrue(v["stored"]);self.assertEqual(v["validation"]["status"],"VALID")
 def test_bad_magic_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"]
   with self.assertRaises(OperatorError):s.import_source(rid,"book.pdf","application/pdf",b"notpdf")
 def test_path_filename_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"]
   with self.assertRaises(OperatorError):s.import_source(rid,"../book.pdf","application/pdf",PDF)
 def test_wrong_media_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"]
   with self.assertRaises(OperatorError):s.import_source(rid,"book.pdf","text/plain",PDF)
 def test_validation_record_persisted_on_rejection(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"]
   with self.assertRaises(OperatorError):s.import_source(rid,"x.pdf","application/pdf",b"x")
   self.assertEqual(s.source_validation(rid)["status"],"INVALID")
 def test_source_artifact_bound_to_run(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];a=s.import_source(rid,"book.pdf","application/pdf",PDF)["artifact_id"];self.assertEqual(s.persistence.load_artifact(a).run_id,rid)
