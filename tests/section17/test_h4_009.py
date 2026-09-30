import unittest,tempfile
from pathlib import Path
from bie.evaluation.benchmarks.browser.ledger import BrowserStore
from bie.evaluation.benchmarks.models import digest
from h4_support import reference,candidate,context,assert_error
class H4009(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'runs.sqlite';self.db=BrowserStore(self.path);self.r=reference();self.c=candidate();self.ctx=context()
 def tearDown(self):self.db.close();self.tmp.cleanup()
 def reserve(self,run='one',campaign='campaign'):
  return self.db.reserve(run,campaign,self.r,self.c,expected_reference_sha256=digest(self.r),expected_candidate_sha256=digest(self.c),context=self.ctx)
 def test_committed_reservation_visible(self):
  self.reserve()
  with BrowserStore(self.path) as other:self.assertEqual(other.db.execute('SELECT state FROM browser_runs').fetchone()[0],'RUNNING')
 def test_duplicate_attempt_blocked(self):self.reserve();assert_error(self,lambda:self.reserve('two'),'BROWSER_ATTEMPT_DUPLICATE')
 def test_reference_drift_blocked(self):
  self.reserve();self.r['rubric_id']='changed';assert_error(self,lambda:self.reserve('two'),'BROWSER_CAMPAIGN_PIN_CHANGED')
 def test_running_not_a_result(self):self.reserve();assert_error(self,lambda:self.db.get('one'),'BROWSER_RUN_NOT_FINAL')
 def test_recovery_is_terminal_blocked(self):
  a=self.reserve();r=self.db.recover('one',expected_reservation_sha256=digest(a),reason='worker-interrupted');self.assertEqual(r['result']['status'],'BLOCKED')
 def test_recovery_wrong_pin_blocks(self):self.reserve();assert_error(self,lambda:self.db.recover('one',expected_reservation_sha256='0'*64,reason='interrupted'),'BROWSER_RECOVERY_SCOPE')
 def test_recovery_cannot_overwrite(self):
  a=self.reserve();self.db.recover('one',expected_reservation_sha256=digest(a),reason='interrupted');assert_error(self,lambda:self.db.recover('one',expected_reservation_sha256=digest(a),reason='again'),'BROWSER_RECOVERY_SCOPE')
 def test_actual_browser_result_reopens(self):
  x=self.db.execute('one','campaign',self.r,self.c,expected_reference_sha256=digest(self.r),expected_candidate_sha256=digest(self.c),context=self.ctx)
  self.assertEqual(x['result']['outcome'],'PASS')
  with BrowserStore(self.path) as other:self.assertEqual(other.get('one'),x)
 def test_receipt_tamper_detected(self):
  a=self.reserve();self.db.recover('one',expected_reservation_sha256=digest(a),reason='interrupted');self.db.db.execute("UPDATE browser_runs SET receipt='{}'");assert_error(self,lambda:self.db.get('one'),'BROWSER_STORE_INTEGRITY')
 def test_campaign_pin_tamper_detected(self):
  a=self.reserve();self.db.recover('one',expected_reservation_sha256=digest(a),reason='interrupted');self.db.db.execute("UPDATE browser_campaigns SET code_sha='tamper'");assert_error(self,lambda:self.db.get('one'),'BROWSER_STORE_INTEGRITY')
 def test_unknown_result(self):assert_error(self,lambda:self.db.get('unknown'),'BROWSER_RUN_UNKNOWN')
