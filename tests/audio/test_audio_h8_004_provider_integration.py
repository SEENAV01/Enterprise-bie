import unittest,tempfile,json,hashlib
from pathlib import Path
from dataclasses import replace
from bie.audio.neural_authority import LiveProviderPolicy,LiveProviderAuthority
from bie.audio.neural_call_journal import PaidCallJournal
from bie.audio.neural_scheduler import ProviderCallScheduler
from bie.audio.neural_transport import OfficialNeuralTransport,HTTPReply
from bie.audio.neural_store import NeuralResponseStore,canonical
from bie.audio.elevenlabs_provider import ElevenLabsProvider
from bie.audio.tts_contract import ProviderFailure,AudioFormat,SynthesisSettings
from bie.audio.voice_selection import SelectionPolicy,select_voices,requests_for
from bie.audio.common import AudioError,fingerprint
from tests.audio.neural_test_support import config,plan,MODEL,VOICE_META,wire_response,KEY

class LiveFixtureWire:
    def __init__(self):self.calls=[];self.mode='success';self.count=0
    def __call__(self,method,path,body,**kw):
        self.calls.append((method,path,body,kw.get('api_key')));self.count+=1
        if method=='GET':
            row=[MODEL] if path=='/v1/models' else VOICE_META
            return HTTPReply(200,canonical(row),'meta-'+str(self.count))
        if self.mode=='network':raise ProviderFailure('NEURAL_NETWORK_UNCONFIRMED')
        if self.mode=='rate':return HTTPReply(429,b'{}','rate-'+str(self.count))
        payload=json.loads(body);return HTTPReply(200,canonical(wire_response(payload['text'])),'live-request-'+str(self.count))

class H8ProviderIntegrationTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def build(self,wire=None):
        p=plan();c=replace(config(),provider_data_transfer_approved=True);store=NeuralResponseStore(self.root/'responses',key=KEY)
        env={'ELEVENLABS_API_KEY':'fixture_secret_123'};policy=LiveProviderPolicy('ops-live-v1',True,max_session_calls=32,max_session_chars=10000,max_inflight=1,admission_timeout_seconds=.5)
        auth=LiveProviderAuthority(policy,environment=env);journal=PaidCallJournal(self.root/'journal');scheduler=ProviderCallScheduler(self.root/'slots',max_inflight=1,admission_timeout_seconds=.5)
        t=OfficialNeuralTransport();wire=wire or LiveFixtureWire();t.request=wire
        provider=ElevenLabsProvider(c,store,allow_live=True,transport=t,context_plan=p,authority=auth,journal=journal,scheduler=scheduler)
        cat=provider.catalog();sel=select_voices(p,cat,SelectionPolicy((provider.provider_id,),('neural-service-unverified',)),SynthesisSettings(format=AudioFormat(c.sample_rate,1)));r=requests_for(p,cat,sel)[0]
        return provider,r,wire,journal,auth
    def test_live_requires_control_objects(self):
        c=replace(config(),provider_data_transfer_approved=True);store=NeuralResponseStore(self.root/'r',key=KEY)
        with self.assertRaisesRegex(AudioError,'LIVE_CONTROL_REQUIRED'):ElevenLabsProvider(c,store,allow_live=True)
    def test_direct_api_key_injection_disabled(self):
        c=replace(config(),provider_data_transfer_approved=True);store=NeuralResponseStore(self.root/'r',key=KEY)
        with self.assertRaisesRegex(AudioError,'DIRECT_SECRET'):ElevenLabsProvider(c,store,api_key='fixture_secret_123')
    def test_preflight_is_full_workload(self):
        pr,r,_,_,_=self.build();out=pr.preflight((r,));self.assertEqual(out['calls'],1);self.assertFalse(out['truncated'])
    def test_successful_paid_call_is_confirmed_and_cached(self):
        pr,r,w,j,_=self.build();asset=pr.synthesize(r);self.assertTrue(asset.wav_bytes);state=j.safe_states()[0];self.assertEqual(state['state'],'CONFIRMED');self.assertTrue(state['provider_request_id'])
        posts=sum(1 for m,_,_,_ in w.calls if m=='POST');asset2=pr.synthesize(r);self.assertEqual(asset.wav_bytes,asset2.wav_bytes);self.assertEqual(posts,sum(1 for m,_,_,_ in w.calls if m=='POST'))
    def test_cached_response_reconciles_journal(self):
        pr,r,w,j,_=self.build();asset=pr.synthesize(r);key=j.safe_states()[0]['call_key'];self.assertEqual(j.safe_state(key)['state'],'CONFIRMED');pr.synthesize(r);self.assertEqual(j.safe_state(key)['state'],'CONFIRMED')
    def test_network_uncertainty_blocks_second_post(self):
        w=LiveFixtureWire();w.mode='network';pr,r,w,j,_=self.build(w)
        with self.assertRaisesRegex(ProviderFailure,'NETWORK_UNCONFIRMED'):pr.synthesize(r)
        self.assertEqual(j.safe_states()[0]['state'],'UNCERTAIN');posts=sum(1 for m,_,_,_ in w.calls if m=='POST')
        with self.assertRaisesRegex(ProviderFailure,'REISSUE_REQUIRES_RESOLUTION'):pr.synthesize(r)
        self.assertEqual(posts,sum(1 for m,_,_,_ in w.calls if m=='POST'))
    def test_rate_limit_is_rejected_and_requires_resolution(self):
        w=LiveFixtureWire();w.mode='rate';pr,r,w,j,_=self.build(w)
        with self.assertRaisesRegex(ProviderFailure,'RATE_LIMIT'):pr.synthesize(r)
        state=j.safe_states()[0];self.assertEqual(state['state'],'REJECTED');self.assertEqual(state['http_status'],429)
        with self.assertRaisesRegex(ProviderFailure,'REISSUE_REQUIRES_RESOLUTION'):pr.synthesize(r)
    def test_authorized_reissue_can_make_one_new_attempt(self):
        w=LiveFixtureWire();w.mode='network';pr,r,w,j,_=self.build(w)
        with self.assertRaises(ProviderFailure):pr.synthesize(r)
        key=j.safe_states()[0]['call_key'];j.authorize_reissue(key,resolution_ref='provider-support:no-completion:ticket-1',authority_revision='ops-r2');w.mode='success'
        asset=pr.synthesize(r);self.assertTrue(asset.wav_bytes);state=j.safe_state(key);self.assertEqual(state['state'],'CONFIRMED');self.assertEqual(state['attempt_no'],2)
    def test_no_secret_in_safe_state_or_provider_repr(self):
        pr,r,w,j,a=self.build();pr.synthesize(r);text=repr(j.safe_states())+repr(pr)+repr(a.receipt());self.assertNotIn('fixture_secret_123',text)
    def test_authority_fingerprint_is_in_alignment_evidence(self):
        pr,r,_,_,a=self.build();from bie.audio.tts_generation import generate_speech;asset=generate_speech(r,pr);_,e=pr.alignment_for(asset);self.assertEqual(e['live_authority_fingerprint'],a.policy.fingerprint())
    def test_fixture_provider_still_works_without_live_controls(self):
        from tests.audio.neural_test_support import setup,enter_fixture_scope
        class Dummy(unittest.TestCase):pass
        d=Dummy();cm=None
        with tempfile.TemporaryDirectory() as td:
            from bie.audio.fixture_scope import synthetic_timing_scope
            with synthetic_timing_scope():
                _,p,rs,_=setup(Path(td));self.assertTrue(p.synthesize(rs[0]).wav_bytes)
    def test_live_metadata_gets_are_authorized_but_not_journaled_as_paid_calls(self):
        pr,r,w,j,a=self.build();pr.synthesize(r);self.assertEqual(len(j.safe_states()),1);self.assertGreaterEqual(a.calls_authorized,3)
    def test_confirmed_remote_missing_cache_blocks_duplicate_after_store_loss(self):
        pr,r,w,j,_=self.build();pr.synthesize(r);posts=sum(1 for m,_,_,_ in w.calls if m=='POST')
        # Remove response cache only, retaining paid-call journal. This simulates local loss.
        import shutil
        shutil.rmtree(pr.store.entries);pr.store.entries.mkdir(mode=0o700)
        with self.assertRaisesRegex(ProviderFailure,'CONFIRMED_REMOTE_RESPONSE'):pr.synthesize(r)
        self.assertEqual(posts,sum(1 for m,_,_,_ in w.calls if m=='POST'))
    def test_provider_never_falls_back_to_local_engine(self):
        pr,r,w,j,_=self.build();w.mode='network'
        with self.assertRaises(ProviderFailure):pr.synthesize(r)
        self.assertFalse(any('espeak' in repr(x).lower() for x in w.calls))
    def test_live_output_diagnostics_keep_acceptance_false(self):
        pr,r,_,_,_=self.build();asset=pr.synthesize(r);self.assertIn('NEURAL_LISTENING_ACCEPTANCE_PENDING',asset.diagnostics)

if __name__=='__main__':unittest.main()
