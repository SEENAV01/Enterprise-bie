import unittest,tempfile,zipfile,json,hashlib
from pathlib import Path
from unittest.mock import patch
from h5_support import *
from bie.evaluation.benchmarks.browser.ledger import BrowserStore
from bie.evaluation.benchmarks.browser.served.export import export_run,verify_export
from bie.evaluation.benchmarks.models import canonical_json
class H5009(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.store=BrowserStore(str(self.root/'runs.sqlite'))
  res=self.store.reserve('r','c',reference(),candidate(),expected_reference_sha256=digest(reference()),expected_candidate_sha256=digest(candidate()),context=context())
  self.store._finish(res,result_blocked())
 def tearDown(self):self.store.close();self.t.cleanup()
 def export(self):p=self.root/'evidence.zip';export_run(self.store,'r',p);return p
 def repack(self,p,edit):
  with zipfile.ZipFile(p) as z:data={n:z.read(n) for n in z.namelist()}
  edit(data)
  with zipfile.ZipFile(p,'w') as z:
   for n,raw in data.items():z.writestr(n,raw)
 def test_export_actual_sqlite_readback(self):self.assertTrue(verify_export(self.export())['verified'])
 def test_export_blocked_not_promoted(self):self.assertEqual(verify_export(self.export())['result_status'],'BLOCKED')
 def test_export_never_production_approval(self):self.assertFalse(verify_export(self.export())['production_approval'])
 def test_existing_output_not_overwritten(self):
  p=self.export()
  with self.assertRaises(FileExistsError):export_run(self.store,'r',p)
 def test_changed_run_bytes_rejected(self):
  p=self.export();self.repack(p,lambda d:d.update({'run.json':b'{}'}));assert_error(self,lambda:verify_export(p),'HTTP_EXPORT_HASH_MISMATCH')
 def test_path_traversal_rejected(self):
  p=self.export();self.repack(p,lambda d:d.update({'../x':b'x'}));assert_error(self,lambda:verify_export(p),'HTTP_EXPORT_UNSAFE_PATH')
 def test_extra_rehashed_member_rejected(self):
  p=self.export()
  def change(d):
   d['extra.js']=b'x';m=json.loads(d['MANIFEST.json']);m['files']['extra.js']={'size_bytes':1,'sha256':hashlib.sha256(b'x').hexdigest()};d['MANIFEST.json']=canonical_json(m).encode()
  self.repack(p,change);assert_error(self,lambda:verify_export(p),'HTTP_EXPORT_UNEXPECTED_MEMBER')
 def test_identical_export_bytes(self):
  p=self.export();q=self.root/'second.zip';export_run(self.store,'r',q);self.assertEqual(p.read_bytes(),q.read_bytes())
 def test_database_tamper_prevents_export(self):
  self.store.db.execute("UPDATE browser_runs SET receipt='{}' WHERE run_id='r'")
  assert_error(self,lambda:export_run(self.store,'r',self.root/'bad.zip'),'BROWSER_STORE_INTEGRITY')
 def test_actual_classic_browser_screenshot_export(self):
  import h4_support as old
  r=old.reference();c=old.candidate()
  run=self.store.execute('classic','classic-campaign',r,c,expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c),context=old.context())
  self.assertEqual(run['result']['outcome'],'PASS')
  p=self.root/'classic.zip';export_run(self.store,'classic',p)
  self.assertEqual(verify_export(p)['result_status'],'MEASURED')
  with zipfile.ZipFile(p) as z:self.assertTrue(z.read('screenshots/000.png').startswith(b'\x89PNG'))
