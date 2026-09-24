import unittest,tempfile,json,shutil,threading,hashlib,os
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
from bie.audio.common import AudioError,fingerprint
from bie.audio.elevenlabs_provider import ElevenLabsProvider
from bie.audio.neural_transport import OfficialNeuralTransport
from bie.audio.neural_store import NeuralResponseStore,load_seal_key
from bie.audio.tts_generation import generate_speech
from bie.audio.tts_cache import TTSCache
from bie.audio.neural_pipeline import prepare_neural_sync
from bie.audio.caption_alignment import CaptionPolicy
from bie.audio.mix_pipeline import mix_synchronized,verify_mixed_source,export_mixed_captions
from tests.audio.neural_test_support import setup,plan,multi_plan,config,FixtureTransport,KEY

class NeuralCacheTests(unittest.TestCase):
    def setUp(self):
        from tests.audio.neural_test_support import enter_fixture_scope;enter_fixture_scope(self);
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.p,self.pr,self.rr,self.t=setup(self.root);self.r=self.rr[0]
    def test_cache_second_synthesis_no_http(self):
        one=generate_speech(self.r,self.pr);count=len(self.t.calls);two=generate_speech(self.r,self.pr)
        self.assertEqual(one.wav_bytes,two.wav_bytes);self.assertEqual(len(self.t.calls),count);self.assertEqual(self.pr.generation_count,1)
    def test_existing_tts_cache_hit_uses_same_response_timing(self):
        cache=TTSCache(self.root/'tts',namespace='test');a=cache.get_or_generate(self.r,self.pr);b=cache.get_or_generate(self.r,self.pr)
        self.assertFalse(a.cache_hit);self.assertTrue(b.cache_hit)
        self.assertEqual(self.pr.alignment_for(a.asset),self.pr.alignment_for(b.asset));self.assertEqual(self.pr.generation_count,1)
    def test_response_seal_detects_rehashed_metadata(self):
        generate_speech(self.r,self.pr);folder=self.pr.store.entries/self.r.fingerprint()[7:];p=folder/'seal.json'
        row=json.loads(p.read_text());row['record']['request_id']='different';p.write_text(json.dumps(row))
        with self.assertRaisesRegex(AudioError,'SEAL_MISMATCH'):generate_speech(self.r,self.pr)
    def test_response_bytes_tamper(self):
        generate_speech(self.r,self.pr);f=self.pr.store.entries/self.r.fingerprint()[7:]/'response.json';f.write_bytes(f.read_bytes()+b' ')
        with self.assertRaisesRegex(AudioError,'CACHE_BINDING'):generate_speech(self.r,self.pr)
    def test_missing_timing_never_regenerates_other_waveform(self):
        a=generate_speech(self.r,self.pr);count=len(self.t.calls);shutil.rmtree(self.pr.store.entries/self.r.fingerprint()[7:])
        with self.assertRaisesRegex(AudioError,'MISSING_NO_RESYNTHESIS'):self.pr.alignment_for(a)
        self.assertEqual(count,len(self.t.calls))
    def test_wrong_local_seal_key_rejected(self):
        generate_speech(self.r,self.pr);self.pr.store=NeuralResponseStore(self.root/'response',key=b'g'*32)
        with self.assertRaisesRegex(AudioError,'SEAL_MISMATCH'):generate_speech(self.r,self.pr)
    def test_pending_files_not_adopted(self):
        (self.pr.store.entries/'.pending-test').mkdir();generate_speech(self.r,self.pr);self.assertEqual(self.pr.generation_count,1)
    def test_cache_entry_extra_file_rejected(self):
        generate_speech(self.r,self.pr);(self.pr.store.entries/self.r.fingerprint()[7:]/'extra').write_text('x')
        with self.assertRaisesRegex(AudioError,'INCOMPLETE'):generate_speech(self.r,self.pr)
    def test_cache_entry_symlink_rejected(self):
        (self.pr.store.entries/self.r.fingerprint()[7:]).symlink_to(self.root,target_is_directory=True)
        with self.assertRaisesRegex(AudioError,'INCOMPLETE'):generate_speech(self.r,self.pr)
    def test_concurrent_threads_synthesize_once(self):
        with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(lambda _:generate_speech(self.r,self.pr),range(3)))
        self.assertEqual(len({r.wav_bytes for r in rows}),1);self.assertEqual(self.pr.generation_count,1)
    def test_remote_metadata_drift_blocks_before_post(self):
        self.t.model={**self.t.model,'description':'changed'}
        with self.assertRaisesRegex(AudioError,'METADATA_DRIFT'):generate_speech(self.r,self.pr)
        self.assertFalse(any(c[0]=='POST' for c in self.t.calls))
    def test_wrong_language_capability_rejected(self):
        self.t.model={**self.t.model,'languages':[]}
        with self.assertRaisesRegex(AudioError,'CAPABILITY'):generate_speech(self.r,self.pr)
    def test_remote_auth_rejection_not_retried(self):
        self.t.status=401
        with self.assertRaisesRegex(AudioError,'AUTH_REJECTED'):generate_speech(self.r,self.pr)
        self.assertEqual(len(self.t.calls),1)
    def test_remote_rate_limit_not_retried(self):
        self.t.status=429
        with self.assertRaisesRegex(AudioError,'RATE_LIMIT'):generate_speech(self.r,self.pr)
        self.assertEqual(len(self.t.calls),1)
    def test_late_transport_result_rejected(self):
        p,pr,rr,t=setup(self.root/'late',c=config(deadline_seconds=.1,socket_timeout_seconds=.05));t.delay=.2
        with self.assertRaisesRegex(AudioError,'DEADLINE'):generate_speech(rr[0],pr)
        self.assertEqual(list(pr.store.entries.iterdir()),[])
    def test_cache_cancelled_before_reuse(self):
        generate_speech(self.r,self.pr);c=Event();c.set()
        with self.assertRaisesRegex(AudioError,'CANCELLED'):generate_speech(self.r,self.pr,cancellation=c)
    def test_live_requires_explicit_opt_in(self):
        pr=ElevenLabsProvider(config(),self.pr.store)
        from bie.audio.voice_selection import select_voices,SelectionPolicy,requests_for
        from bie.audio.tts_contract import SynthesisSettings,AudioFormat
        c=pr.catalog();sel=select_voices(self.p,c,SelectionPolicy((pr.provider_id,),('neural-service-unverified',)),SynthesisSettings(format=AudioFormat(24000)))
        r=requests_for(self.p,c,sel)[0]
        with self.assertRaisesRegex(AudioError,'OPT_IN'):generate_speech(r,pr)
        self.assertEqual(pr.generation_count,0)
    def test_fixture_transport_cannot_claim_official(self):
        with self.assertRaisesRegex(AudioError,'AUTHORITY'):ElevenLabsProvider(config(),self.pr.store,transport=self.t)
    def test_fixture_must_not_receive_real_credential(self):
        with self.assertRaisesRegex(AudioError,'CREDENTIALS'):ElevenLabsProvider(config(),self.pr.store,transport=self.t,fixture=True,api_key='secret')
    def test_wrong_response_scope_rejected(self):
        self.t.reply_scope='OFFICIAL_HTTPS_RESPONSE'
        with self.assertRaisesRegex(AudioError,'SCOPE_MISMATCH'):generate_speech(self.r,self.pr)
    def test_private_key_create_permissions_and_reread(self):
        p=self.root/'private'/'seal.key';key=load_seal_key(p,create=True);self.assertEqual(key,load_seal_key(p));self.assertEqual(p.stat().st_mode&0o777,0o600)
    def test_public_or_symlink_key_rejected(self):
        p=self.root/'seal.key';load_seal_key(p,create=True);p.chmod(0o644)
        with self.assertRaisesRegex(AudioError,'PERMISSION'):load_seal_key(p)
        q=self.root/'link';q.symlink_to(p)
        with self.assertRaisesRegex(AudioError,'KEY_PATH'):load_seal_key(q)
    def test_neural_sync_uses_existing_clocks_and_mix(self):
        p,pr,_,_=setup(self.root/'pipeline',p=multi_plan(),context=True);cache=TTSCache(self.root/'pipeline-cache',namespace='test')
        s=prepare_neural_sync(p,pr,cache,caption_policy=CaptionPolicy(channel='display'),allow_fixture=True)
        self.assertEqual(s.receipt()['engine_replay_calls'],0);self.assertEqual(len(s.assets),3)
        m=mix_synchronized(s);verify_mixed_source(m,s)
        self.assertEqual(m.clock()['plan_fingerprint'],p.fingerprint());self.assertTrue(export_mixed_captions(m).startswith('WEBVTT'))
        self.assertFalse(m.receipt()['cinematic_quality_verified'])
    def test_fixture_not_default_pipeline(self):
        with self.assertRaisesRegex(AudioError,'FIXTURE_OPT_IN'):prepare_neural_sync(self.p,self.pr,TTSCache(self.root/'tts',namespace='test'))

    def test_multilingual_model_metadata_and_pcm_path(self):
        from tests.audio.neural_test_support import MODEL
        m={**MODEL,'model_id':'eleven_multilingual_v2','maximum_text_length_per_request':10000}
        t=FixtureTransport();t.model=m
        c=config(model_id='eleven_multilingual_v2',language_mode='provider_auto',model_metadata_fingerprint=fingerprint(m))
        p,pr,rr,t=setup(self.root/'v2',c=c,transport=t)
        a=generate_speech(rr[0],pr);pr.alignment_for(a)
        self.assertEqual(json.loads(t.calls[-1][2])['model_id'],'eleven_multilingual_v2')
        self.assertNotIn('language_code',json.loads(t.calls[-1][2]))
    def test_unsupported_style_never_silently_ignored(self):
        from bie.audio.neural_policy import NeuralSettings
        from tests.audio.neural_test_support import MODEL
        m={**MODEL,'can_use_style':False};t=FixtureTransport();t.model=m
        c=config(settings=NeuralSettings(style=.5),model_metadata_fingerprint=fingerprint(m))
        p,pr,rr,t=setup(self.root/'style',c=c,transport=t)
        with self.assertRaisesRegex(AudioError,'STYLE_CAPABILITY'):generate_speech(rr[0],pr)
        self.assertFalse(any(v[0]=='POST' for v in t.calls))
    def test_unsupported_speaker_boost_never_silently_ignored(self):
        self.t.model={**self.t.model,'can_use_speaker_boost':False}
        with self.assertRaisesRegex(AudioError,'SPEAKER_BOOST_CAPABILITY'):generate_speech(self.r,self.pr)

    def test_mutated_deployment_cannot_reuse_old_catalog(self):
        self.pr.config=replace(self.pr.config,deployment_revision='changed')
        with self.assertRaisesRegex(AudioError,'CONFIGURATION_CHANGED'):generate_speech(self.r,self.pr)
    def test_mutated_transport_does_not_bypass_scope(self):
        self.pr.transport=OfficialNeuralTransport()
        with self.assertRaisesRegex(AudioError,'AUTHORITY'):generate_speech(self.r,self.pr)
