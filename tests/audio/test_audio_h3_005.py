import json,os,subprocess,sys,time,threading
from pathlib import Path
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,NoEncryption
from bie.audio.mix_io import publish_mix
from bie.audio.acoustic_io import verify_publication
from bie.audio.durable_contract import build_request,DurablePolicy
from bie.audio.durable_jobs import AudioJobCoordinator
from .durable_test_support import *
ROOT=Path(__file__).resolve().parents[2]

class DurableCLITests(DurableCase):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_durable.py'),*map(str,args),
            '--with-dir-snapshot'],capture_output=True,text=True,timeout=120)
    def prepare(self):
        source=self.root/'mix';publish_mix(self.mix,source,sync=self.sync,allow_review=True)
        trust=clone(self.trust);now=int(time.time())
        trust['issuers'][0]['not_before']=now-60;trust['issuers'][0]['not_after']=now+3600
        (self.root/'runtime.json').write_bytes(canonical(self.runtime))
        (self.root/'trust.json').write_bytes(canonical(trust))
        key=self.root/'private.key';key.write_bytes(self.signer.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption()));key.chmod(0o600)
        args=['evaluate','--store',self.root/'service','--input',source,'--runtime',self.root/'runtime.json',
            '--trust-file',self.root/'trust.json','--private-key-file',key,'--key-id',KEY_ID,
            '--run-id',RUN_ID,'--job-id','scene-1','--revision','1','--allow-local-diagnostic']
        return args,trust
    def test_help(self):
        r=self.run_cli('--help');self.assertEqual(r.returncode,0);self.assertIn('allow-local-diagnostic',r.stdout)
    def test_inspect_no_acceptance_claim(self):
        r=self.run_cli('inspect','--store',self.root/'service');self.assertEqual(r.returncode,0);self.assertFalse(json.loads(r.stdout)['product_accepted'])
    def test_missing_opt_in_is_blocked(self):
        r=self.run_cli('evaluate','--store',self.root/'service');self.assertEqual(r.returncode,2);self.assertIn('OPT_IN',r.stderr)
    def test_missing_arguments_are_blocked(self):
        r=self.run_cli('evaluate','--store',self.root/'service','--allow-local-diagnostic');self.assertEqual(r.returncode,2);self.assertIn('ARGUMENTS',r.stderr)
    def test_two_cold_cli_processes_evaluate_then_reuse(self):
        args,trust=self.prepare();a=self.run_cli(*args,'--output',self.root/'qa1');b=self.run_cli(*args,'--output',self.root/'qa2')
        self.assertEqual(a.returncode,3,a.stderr);self.assertEqual(b.returncode,3,b.stderr)
        one,two=json.loads(a.stdout),json.loads(b.stdout)
        self.assertFalse(one['cache_hit']);self.assertTrue(two['cache_hit']);self.assertEqual(two['native_evaluations'],0)
        self.assertEqual(one['artifact_ref'],two['artifact_ref'])
        for folder in ('qa1','qa2'):self.assertTrue(verify_publication(self.root/folder,self.mix,self.sync,trust)['passed'])
    def test_authority_files_cannot_overlap_store(self):
        args,_=self.prepare();i=args.index('--store');args[i+1]=self.root
        r=self.run_cli(*args,'--output',self.root/'qa');self.assertEqual(r.returncode,2);self.assertIn('OVERLAP',r.stderr)
    def test_key_permissions_rejected(self):
        args,_=self.prepare();(self.root/'private.key').chmod(0o644)
        r=self.run_cli(*args,'--output',self.root/'qa');self.assertEqual(r.returncode,2);self.assertIn('PERMISSIONS',r.stderr)
    def test_symlink_input_rejected(self):
        args,_=self.prepare();p=self.root/'mix-link';p.symlink_to(self.root/'mix',target_is_directory=True);args[args.index('--input')+1]=p
        r=self.run_cli(*args,'--output',self.root/'qa');self.assertEqual(r.returncode,2);self.assertIn('SYMLINK',r.stderr)
    def test_existing_output_blocked_before_work(self):
        args,_=self.prepare();(self.root/'qa').mkdir()
        r=self.run_cli(*args,'--output',self.root/'qa');self.assertEqual(r.returncode,2);self.assertIn('OUTPUT_EXISTS',r.stderr)
        self.assertFalse((self.root/'service').exists())
    def test_private_key_never_leaks_in_errors(self):
        args,_=self.prepare();args[args.index('--key-id')+1]='wrong-key'
        r=self.run_cli(*args,'--output',self.root/'qa');self.assertEqual(r.returncode,2)
        raw=(self.root/'private.key').read_bytes();self.assertNotIn(raw.hex(),r.stderr)
    def test_real_killed_claim_process_can_be_reclaimed(self):
        policy=DurablePolicy(lease_ttl_seconds=3,heartbeat_seconds=1)
        req=build_request(self.job,run_id=RUN_ID,job_id='kill-test',revision='1',runtime_fingerprint=self.runtime['fingerprint'],key_id=KEY_ID,policy=policy)
        f=self.root/'request.json';f.write_bytes(canonical(req));root=self.root/'killed'
        code='''import json,sys,time
from bie.audio.durable_jobs import AudioJobCoordinator
from bie.audio.durable_contract import DurablePolicy
r=json.load(open(sys.argv[1]));j=AudioJobCoordinator(sys.argv[2],policy=DurablePolicy(**r['policy']))
t=j.acquire(r);print(t.lease.epoch,flush=True);time.sleep(60)
'''
        env={**os.environ,'PYTHONPATH':os.pathsep.join([str(ROOT),str(ROOT/'dependency_snapshot')]),'PYTHONDONTWRITEBYTECODE':'1'}
        p=subprocess.Popen([sys.executable,'-B','-c',code,str(f),str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
        try:
            self.assertEqual(p.stdout.readline().strip(),'1');p.kill();p.wait(timeout=10);time.sleep(3.1)
            recovered=AudioJobCoordinator(root,policy=policy).acquire(req)
            self.assertEqual(recovered.lease.epoch,2)
        finally:
            if p.poll() is None:p.kill();p.wait(timeout=10)
            p.stdout.close();p.stderr.close()
    def test_source_media_never_rewritten(self):
        args,_=self.prepare();before=(self.root/'mix/master.wav').read_bytes()
        self.run_cli(*args,'--output',self.root/'qa')
        self.assertEqual(before,(self.root/'mix/master.wav').read_bytes())
