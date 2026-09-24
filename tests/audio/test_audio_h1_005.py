import unittest,tempfile,subprocess,sys,os,json,ast,hashlib
from pathlib import Path
from dataclasses import asdict,replace
from bie.audio.neural_pipeline import prepare_neural_sync
from bie.audio.tts_cache import TTSCache
from bie.audio.mix_pipeline import mix_synchronized
from bie.audio.mix_io import publish_mix
from bie.audio.qa_source import load_published_mix
from bie.audio.qa_pipeline import audit_mix
from bie.audio.neural_store import canonical
from tests.audio.neural_test_support import setup,multi_plan,plan,config

ROOT=Path(__file__).resolve().parents[2]
class NeuralEndToEndTests(unittest.TestCase):
    def setUp(self):from tests.audio.neural_test_support import enter_fixture_scope;enter_fixture_scope(self);self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def run_cli(self,*args,env=None):
        return subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_neural.py'),*args,'--standalone-fixture'],text=True,capture_output=True,env=env,timeout=15)
    def test_cli_requires_opt_in(self):
        r=self.run_cli('--output',str(self.root/'out'));self.assertEqual(r.returncode,2);self.assertIn('OPT_IN',r.stderr);self.assertFalse((self.root/'out').exists())
    def test_cli_missing_credential_no_network(self):
        env=dict(os.environ);env.pop('ELEVENLABS_API_KEY',None)
        r=self.run_cli('--allow-live-provider','--output',str(self.root/'out'),env=env)
        self.assertEqual(r.returncode,2);self.assertIn('CREDENTIALS_NOT_CONFIGURED',r.stderr);self.assertFalse((self.root/'out').exists())
    def test_cli_invalid_template_blocks_before_post(self):
        c=self.root/'c.json';c.write_text(json.dumps(asdict(config())));env={**os.environ,'ELEVENLABS_API_KEY':'fixture-not-real-secret'}
        r=self.run_cli(str(ROOT/'examples/audio/english.json'),'--deployment',str(c),'--output',str(self.root/'out'),
                       '--cache',str(self.root/'cache'),'--seal-key-file',str(self.root/'key'),'--allow-live-provider',env=env)
        self.assertEqual(r.returncode,2);self.assertIn('APPROVAL_REQUIRED',r.stderr);self.assertNotIn('fixture-not-real-secret',r.stderr)
    def test_cli_help_runs(self):
        r=self.run_cli('--help');self.assertEqual(r.returncode,0);self.assertIn('allow-live-provider',r.stdout)
    def test_programmatic_publish_reload_qa_existing_paths(self):
        p,pr,_,_=setup(self.root,p=multi_plan());s=prepare_neural_sync(p,pr,TTSCache(self.root/'tts',namespace='test'),allow_fixture=True)
        m=mix_synchronized(s);out=self.root/'output'
        publish_mix(m,out,sync=s,allow_review=True)
        loaded,ls,_=load_published_mix(out);self.assertEqual(loaded.wav_bytes,m.wav_bytes);self.assertEqual(ls.receipt(),s.receipt())
        report,captions=audit_mix(loaded,ls)
        self.assertEqual(report['status'],'REVIEW');self.assertFalse(report['product_accepted'])
    def test_preexisting_output_not_replaced(self):
        p=self.root/'out';p.mkdir();(p/'keep').write_text('keep')
        env={**os.environ,'ELEVENLABS_API_KEY':'fixture-not-real-secret'}
        r=self.run_cli('--allow-live-provider','--output',str(p),env=env)
        self.assertEqual(r.returncode,2);self.assertEqual((p/'keep').read_text(),'keep')
    def test_old_providers_source_byte_identical(self):
        import zipfile
        # Pinned original parent hashes, not dependent on an external parent ZIP.
        preservation=ROOT/'docs/audio/hardening_h1/PARENT_SOURCE_HASHES.json'
        row=json.loads(preservation.read_text())
        for name in ('espeak_provider.py','timed_espeak_provider.py','tts_generation.py','tts_cache.py','voice_selection.py'):
            p=ROOT/'bie/audio'/name;self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['bie/audio/'+name])
    def test_hindi_returned_media_in_same_pipeline(self):
        p,pr,_,_=setup(self.root,p=plan('यह एक परीक्षण है।',language='hi',pause=200))
        s=prepare_neural_sync(p,pr,TTSCache(self.root/'tts',namespace='hindi'),allow_fixture=True)
        self.assertEqual(s.alignments[0].words[0].spoken,'यह');self.assertEqual(s.assets[0].requested_pause_samples,4800)
        self.assertFalse(s.receipt()['cinematic_quality_verified'])
    def test_second_preparation_reuses_bytes_no_resynthesis(self):
        p,pr,_,_=setup(self.root);cache=TTSCache(self.root/'tts',namespace='second')
        first=prepare_neural_sync(p,pr,cache,allow_fixture=True);n=pr.request_count
        second=prepare_neural_sync(p,pr,cache,allow_fixture=True)
        self.assertEqual(first.wav_bytes,second.wav_bytes);self.assertTrue(all(second.cache_hits));self.assertEqual(n,pr.request_count)
    def test_fixture_words_not_pretended_acoustically_verified(self):
        p,pr,_,_=setup(self.root);s=prepare_neural_sync(p,pr,TTSCache(self.root/'tts',namespace='test'),allow_fixture=True)
        self.assertFalse(s.alignments[0].receipt()['acoustic_alignment_verified']);self.assertEqual(s.engine_evidence[0]['scope'],'CONTRACT_FIXTURE')
    def test_legacy_timing_acceptance_flags_remain_false(self):
        from bie.audio.sync_contract import AlignedSpeech
        self.assertIn('acoustic_alignment_verified',str(AlignedSpeech.receipt.__code__.co_consts))
    def test_source_has_no_github_write_or_eval(self):
        for path in list((ROOT/'bie/audio').glob('neural_*.py'))+[ROOT/'scripts/audio_neural.py']:
            tree=ast.parse(path.read_text())
            calls=[n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
            self.assertNotIn('eval',calls);self.assertNotIn('exec',calls)

    def test_response_provenance_export_contains_no_credentials(self):
        from bie.audio.neural_pipeline import provider_evidence_files
        p,pr,_,_=setup(self.root);s=prepare_neural_sync(p,pr,TTSCache(self.root/'tts',namespace='test'),allow_fixture=True)
        files=provider_evidence_files(s,pr);report=json.loads(files['neural-evidence.json'])
        self.assertEqual(report['items'][0]['response_sha256'],hashlib.sha256(files['neural-response-00000.json']).hexdigest())
        self.assertNotIn('api_key',report);self.assertNotIn('key',report);self.assertFalse(report['provider_signature_verified'])
        out=self.root/'publish';m=mix_synchronized(s);publish_mix(m,out,sync=s,inputs=files,allow_review=True)
        _,_,restored=load_published_mix(out);self.assertEqual(restored['inputs/neural-response-00000.json'],files['neural-response-00000.json'])

    def test_canonical_cli_without_opt_in_has_stable_error(self):
        env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','ELEVENLABS_API_KEY')}
        r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_neural.py')],env=env,text=True,capture_output=True,timeout=15)
        self.assertEqual(r.returncode,2);self.assertEqual(json.loads(r.stderr)['error_code'],'NEURAL_LIVE_OPT_IN_REQUIRED')
        self.assertNotIn('Traceback',r.stderr)

    def test_fixture_publication_reload_requires_diagnostic_scope(self):
        from bie.audio.fixture_scope import synthetic_timing_scope
        p,pr,_,_=setup(self.root);s=prepare_neural_sync(p,pr,TTSCache(self.root/'tts',namespace='test'),allow_fixture=True)
        out=self.root/'published';publish_mix(mix_synchronized(s),out,sync=s,allow_review=True)
        with synthetic_timing_scope(enabled=False):
            with self.assertRaisesRegex(ValueError,'DIAGNOSTIC_OPT_IN_REQUIRED'):load_published_mix(out)
