import unittest,tempfile
from dataclasses import asdict
from pathlib import Path
from h5_support import *
from bie.evaluation.benchmarks.browser.served.worker import collect
from bie.evaluation.benchmarks.browser.service import execute
class H5004(unittest.TestCase):
 def test_actual_runtime_does_not_authorize(self):self.assertFalse(runtime()['product_accepted'])
 def test_actual_browser_outcome_honest(self):
  v=runtime();self.assertIn(v['status'],('COLLECTED','BLOCKED'))
  if v['status']=='BLOCKED':self.assertTrue(v['error_code']);self.assertNotIn('observed',v)
  else:self.assertEqual(v['observed']['transport'],'REAL_LOOPBACK_HTTP_MODULE_APP')
 def test_parent_retains_worker_failure(self):
  v=runtime()
  if v['status']=='BLOCKED' and 'worker_error' in v:self.assertEqual(v['worker_error']['status'],'BLOCKED')
  else:self.assertIn('custody',v)
 def test_non_authored_scope_blocks(self):
  c=candidate();c['origin_kind']='CANONICAL_LAYOUT_UNVERIFIED'
  self.assertEqual(execute(reference(),c,context())['error_code'],'HTTP_NONAUTHORED_RUNTIME_NOT_ADMITTED')
 def test_wrong_binary_pin_blocks(self):
  from dataclasses import replace
  self.assertEqual(execute(reference(),candidate(),replace(context(),chromium_sha256='0'*64))['error_code'],'BROWSER_TOOL_PIN_MISMATCH')
 def test_worker_checks_actual_snapshot(self):
  with tempfile.TemporaryDirectory() as t:
   for row in candidate()['files']:(Path(t)/row['path']).write_bytes(b'changed')
   cfg={'reference':reference(),'candidate':candidate(),'snapshot_root':t,'limits':asdict(BrowserLimits()),
        'chromium_executable':BROWSER,'allow_unsandboxed_diagnostic':True}
   assert_error(self,lambda:collect(cfg),'HTTP_SNAPSHOT_CHANGED')
 def test_no_document_fallback_in_worker(self):
  from bie.evaluation.benchmarks.browser.served import worker
  text=Path(worker.__file__).read_text();self.assertNotIn('page.set_content(',text);self.assertNotIn('ignore_default_args',text)
 def test_all_original_assets_in_custody(self):self.assertEqual(len(runtime()['custody']['files']),len(candidate()['files']))
