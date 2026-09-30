import unittest,tempfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from h5_support import *
from bie.evaluation.benchmarks.browser.ledger import BrowserStore
from bie.evaluation.benchmarks.browser.service import execute,BrowserCollectionBlocked
from bie.evaluation.benchmarks import metrics
class H5008(unittest.TestCase):
 def test_existing_metric_dispatch(self):
  with patch('bie.evaluation.benchmarks.browser.metric.evaluate',return_value='dispatched') as f:
   out=metrics.evaluate('BIE-EVAL-METRIC-014',reference(),candidate(),expected_reference_sha256=digest(reference()),expected_candidate_sha256=digest(candidate()),execution_context=context())
   self.assertEqual(out,'dispatched');f.assert_called_once()
 def test_wrong_reference_pin(self):assert_error(self,lambda:metrics.evaluate('BIE-EVAL-METRIC-014',reference(),candidate(),expected_reference_sha256='0'*64,expected_candidate_sha256=digest(candidate()),execution_context=context()),'REFERENCE_SNAPSHOT_MISMATCH')
 def test_injected_evidence_rejected(self):assert_error(self,lambda:metrics.evaluate('BIE-EVAL-METRIC-014',reference(),candidate(),expected_reference_sha256=digest(reference()),expected_candidate_sha256=digest(candidate()),execution_context=context(),source_artifacts={'passed':True}),'BROWSER_INJECTED_EVIDENCE_REJECTED')
 def test_legacy_cannot_dispatch_http_candidate(self):
  r=old_reference();self.assertEqual(execute(r,candidate(),context())['error_code'],'HTTP_REFERENCE_PROFILE_REQUIRED')
 def test_http_pin_in_receipt(self):self.assertEqual(runtime()['http_contract']['reference'],reference())
 def test_store_terminal_block_reopens(self):
  with tempfile.TemporaryDirectory() as t:
   db=str(Path(t)/'x.sqlite')
   with BrowserStore(db) as s:
    s.execute('r','c',reference(),candidate(),expected_reference_sha256=digest(reference()),expected_candidate_sha256=digest(candidate()),context=replace(context(),chromium_sha256='0'*64))
   with BrowserStore(db) as s:self.assertEqual(s.get('r')['result']['status'],'BLOCKED')
 def test_renamed_candidate_path_cannot_repeat(self):
  with tempfile.TemporaryDirectory() as t, BrowserStore(str(Path(t)/'x.sqlite')) as s:
   kw=dict(expected_reference_sha256=digest(reference()),expected_candidate_sha256=digest(candidate()),context=context())
   s.reserve('a','campaign',reference(),candidate(),**kw)
   assert_error(self,lambda:s.reserve('b','campaign',reference(),candidate(),**kw),'BROWSER_ATTEMPT_DUPLICATE')
 def test_deterministic_rater_retains_collection_failure(self):
  from bie.evaluation.benchmarks.release.deterministic import execute as run,service_code_sha256
  r=reference();c=candidate();ctx={'run_id':'r','case_id':'case','domain':'MATH','metric_id':r['metric_id'],'candidate_sha256':digest(c),
    'reference_sha256':digest(r),'rubric_sha256':digest(r),'dataset_sha256':digest('data'),'environment_sha256':digest('env'),'split':'DEVELOPMENT'}
  with patch('bie.evaluation.benchmarks.browser.metric.execute',return_value={**runtime()}):
   v=run(ctx,r,c,expected_code_sha256=service_code_sha256(),execution_context=context())
  if runtime()['status']=='BLOCKED':self.assertEqual(v['status'],'BLOCKED');self.assertIn('browser_collection',v['evidence'])
  else:self.assertFalse(v['product_accepted'])
