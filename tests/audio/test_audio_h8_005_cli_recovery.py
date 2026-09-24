import unittest,tempfile,subprocess,sys,json,os
from pathlib import Path
from bie.audio.neural_call_journal import PaidCallJournal
from bie.audio.common import fingerprint

ROOT=Path(__file__).resolve().parents[2]
class H8RecoveryCliTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.cache=self.root/'cache'
    def run_cli(self,*args):return subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_neural_recovery.py'),'--cache',str(self.cache),*args],text=True,capture_output=True,timeout=10)
    def make_uncertain(self):
        j=PaidCallJournal(self.cache/'paid-call-journal');t=j.prepare(request_fingerprint=fingerprint('r'),deployment_fingerprint=fingerprint('d'),payload_sha256='a'*64);j.mark_in_flight(t);j.mark_uncertain(t);return j,t
    def test_list_empty(self):
        r=self.run_cli('list');self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout)['result'],[])
    def test_inspect_safe_state(self):
        j,t=self.make_uncertain();r=self.run_cli('inspect',t.call_key);self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout)['result']['state'],'UNCERTAIN')
    def test_authorize_reissue_records_evidence_only(self):
        j,t=self.make_uncertain();r=self.run_cli('authorize-reissue',t.call_key,'--resolution-ref','provider-ticket:123','--authority-revision','ops-r2');self.assertEqual(r.returncode,0);row=json.loads(r.stdout);self.assertEqual(row['result']['state'],'REISSUE_AUTHORIZED');self.assertFalse(row['remote_call_performed'])
    def test_unknown_call_key_is_safe_error(self):
        r=self.run_cli('inspect','sha256:'+'0'*64);self.assertEqual(r.returncode,2);self.assertIn('NEURAL_CALL_NOT_FOUND',r.stderr);self.assertNotIn('Traceback',r.stderr)
    def test_output_does_not_contain_secret(self):
        j,t=self.make_uncertain();env=os.environ.copy();env['ELEVENLABS_API_KEY']='fixture_secret_123';r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_neural_recovery.py'),'--cache',str(self.cache),'inspect',t.call_key],text=True,capture_output=True,env=env,timeout=10);self.assertNotIn('fixture_secret_123',r.stdout+r.stderr)
    def test_neural_cli_missing_secret_contract_preserved(self):
        env=os.environ.copy();env.pop('ELEVENLABS_API_KEY',None);r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_neural.py'),'--allow-live-provider','--output',str(self.root/'out'),'--standalone-fixture'],text=True,capture_output=True,env=env,timeout=10);self.assertEqual(r.returncode,2);self.assertIn('CREDENTIALS_NOT_CONFIGURED',r.stderr)
    def test_neural_cli_help_mentions_authority_revision(self):
        r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_neural.py'),'--help'],text=True,capture_output=True,timeout=10);self.assertEqual(r.returncode,0);self.assertIn('live-authority-revision',r.stdout)
    def test_recovery_tool_has_no_retry_command(self):
        r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_neural_recovery.py'),'--help'],text=True,capture_output=True,timeout=10);self.assertNotIn(' retry ',r.stdout.lower());self.assertIn('authorize-reissue',r.stdout)
    def test_journal_persists_across_process_invocations(self):
        j,t=self.make_uncertain();a=self.run_cli('inspect',t.call_key);b=self.run_cli('inspect',t.call_key);self.assertEqual(json.loads(a.stdout)['result'],json.loads(b.stdout)['result'])
    def test_h6_pipeline_summary_contract_is_backward_compatible(self):
        from tests.audio.pipeline_test_support import actual,context
        from bie.audio.pipeline_bundle import validate_bundle
        files,_=actual();c=context();result=validate_bundle(files,c['request'],c['profile'])
        self.assertEqual(result['summary']['mix_stems'],0);self.assertEqual(result['summary']['mix_stems_fingerprint'],c['request']['mix_stems_fingerprint'])
    def test_no_product_acceptance_claim(self):
        r=self.run_cli('list');self.assertFalse(json.loads(r.stdout)['product_accepted'])

if __name__=='__main__':unittest.main()
