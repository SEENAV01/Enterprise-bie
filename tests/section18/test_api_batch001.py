import os,tempfile,unittest
from fastapi.testclient import TestClient
from apps.api.main import app
class ApiBatch001(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=os.environ.get("BIE_DATA_ROOT");os.environ["BIE_DATA_ROOT"]=self.tmp.name;self.client=TestClient(app)
 def tearDown(self):
  if self.old is None:os.environ.pop("BIE_DATA_ROOT",None)
  else:os.environ["BIE_DATA_ROOT"]=self.old
  self.tmp.cleanup()
 def create(self):
  r=self.client.post("/v1/operator/runs",json={"config_hash":"a"*64});self.assertEqual(r.status_code,201);return r.json()["run_id"]
 def test_create_status_and_source(self):
  rid=self.create();self.assertEqual(self.client.get(f"/v1/operator/runs/{rid}").json()["run_state"],"CREATED")
  r=self.client.post(f"/v1/operator/runs/{rid}/source",headers={"content-type":"application/pdf","x-bie-filename":"book.pdf"},content=b"%PDF-1.7\n%%EOF\n");self.assertEqual(r.status_code,201)
 def test_invalid_create_fails(self):
  self.assertEqual(self.client.post("/v1/operator/runs",json={"config_hash":"bad"}).status_code,400)
 def test_source_validation_html(self):
  rid=self.create();r=self.client.get(f"/v1/operator/runs/{rid}/source-validation",headers={"accept":"text/html"});self.assertEqual(r.status_code,200);self.assertIn("Source validation",r.text)
 def test_unknown_run_is_not_500(self):
  self.assertEqual(self.client.get("/v1/operator/runs/app-run-ffffffffffffffff").status_code,404)
 def test_capabilities_still_disclaim_acceptance(self):
  self.assertFalse(self.client.get("/v1/capabilities").json()["product_accepted"])
