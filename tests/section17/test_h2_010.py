import unittest,tempfile,copy,subprocess,sys,json
from pathlib import Path
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.av.ledger import AVRunStore
from bie.evaluation.benchmarks.av.service import code_sha256
from bie.evaluation.benchmarks.av.custody import Limits
from h2_support import policy,media,sha,ROOT
class H2010(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.db=Path(self.t.name)/'av.sqlite';self.s=AVRunStore(self.db);self.addCleanup(self.s.close)
 def run_case(self,run_id='r1',campaign_id='c1',**changes):
  p=policy(**changes);return self.s.execute(campaign_id=campaign_id,run_id=run_id,media_path=media(),media_sha256=sha(media()),policy=p,policy_sha256=digest(p))
 def reserve(self):
  with patch('bie.evaluation.benchmarks.av.ledger.collect_and_evaluate',side_effect=RuntimeError('abandoned')):
   with self.assertRaises(RuntimeError):self.run_case()
  return digest({'media_sha256':sha(media()),'caption_sha256':None,'caption_format':None}),digest(policy())
 def test_actual_persist_reopen(self):
  r=self.run_case()
  with AVRunStore(self.db) as s:self.assertEqual(s.get('r1'),r)
 def test_duplicate_candidate_reservation(self):
  self.run_case()
  with self.assertRaises(BenchmarkError):self.run_case(run_id='r2')
 def test_duplicate_run_id_across_campaigns(self):
  self.run_case()
  with self.assertRaises(BenchmarkError):self.run_case(campaign_id='c2')
 def test_policy_cannot_change_in_campaign(self):
  self.run_case()
  with self.assertRaises(BenchmarkError) as e:self.run_case(run_id='r2',max_dark_fraction=.2)
  self.assertEqual(e.exception.code,'AV_CAMPAIGN_PINS_CHANGED')
 def test_source_code_pin_change_blocked(self):
  self.run_case()
  with patch('bie.evaluation.benchmarks.av.ledger.code_sha256',return_value='f'*64),self.assertRaises(BenchmarkError):self.run_case(run_id='r2')
 def test_limits_pin_change_blocked(self):
  self.run_case();p=policy()
  with self.assertRaises(BenchmarkError):self.s.execute(campaign_id='c1',run_id='r2',media_path=media(),media_sha256=sha(media()),policy=p,policy_sha256=digest(p),limits=Limits(deadline_s=5))
 def test_unfinished_get_blocked(self):
  self.reserve()
  with self.assertRaises(BenchmarkError):self.s.get('r1')
 def test_recovery_terminal_blocked(self):
  c,p=self.reserve();r=self.s.recover('r1',candidate_sha256=c,policy_sha256=p,operator_reason='WORKER_STOPPED');self.assertEqual(r['status'],'BLOCKED');self.assertEqual(r['candidate_sha256'],c);self.assertEqual(self.s.get('r1'),r)
 def test_recovery_wrong_pins(self):
  c,p=self.reserve()
  with self.assertRaises(BenchmarkError):self.s.recover('r1',candidate_sha256='f'*64,policy_sha256=p,operator_reason='WORKER_STOPPED')
 def test_recovery_cannot_replace_final(self):
  r=self.run_case()
  with self.assertRaises(BenchmarkError):self.s.recover('r1',candidate_sha256=r['candidate_sha256'],policy_sha256=r['reference_sha256'],operator_reason='WORKER_STOPPED')
 def test_tampered_stored_bytes(self):
  self.run_case();self.s.db.execute('UPDATE av_h2_runs SET receipt=? WHERE run_id=?',('{"bad":1}','r1'))
  with self.assertRaises(BenchmarkError):self.s.get('r1')
 def test_row_pin_tamper(self):
  self.run_case();self.s.db.execute('UPDATE av_h2_runs SET candidate_sha=? WHERE run_id=?',('f'*64,'r1'))
  with self.assertRaises(BenchmarkError):self.s.get('r1')
 def test_unknown_run(self):
  with self.assertRaises(BenchmarkError):self.s.get('missing')
 def test_cli_get_matches_database(self):
  r=self.run_case();p=subprocess.run([sys.executable,'-m','bie.evaluation.benchmarks.av','get','--database',str(self.db),'--run-id','r1'],cwd=ROOT,capture_output=True,timeout=5);self.assertEqual(p.returncode,0);self.assertEqual(json.loads(p.stdout),r)
 def test_cli_missing_database_no_creation(self):
  absent=self.db.with_name('absent.sqlite');p=subprocess.run([sys.executable,'-m','bie.evaluation.benchmarks.av','get','--database',str(absent),'--run-id','r'],cwd=ROOT,capture_output=True,timeout=5);self.assertEqual(p.returncode,2);self.assertFalse(absent.exists())
 def test_bad_policy_before_reservation(self):
  with self.assertRaises(BenchmarkError):self.run_case(expected_frames=False)
  self.assertEqual(self.s.db.execute('SELECT count(*) FROM av_h2_runs').fetchone()[0],0)
