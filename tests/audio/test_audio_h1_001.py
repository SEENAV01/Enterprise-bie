import unittest,tempfile,json
from dataclasses import replace,asdict
from bie.audio.common import AudioError,fingerprint
from bie.audio.neural_policy import *
from bie.audio.voice_selection import select_voices,SelectionPolicy
from bie.audio.tts_contract import SynthesisSettings
from tests.audio.neural_test_support import config,plan,setup,multi_plan

class NeuralPolicyTests(unittest.TestCase):
    def setUp(self):from tests.audio.neural_test_support import enter_fixture_scope;enter_fixture_scope(self);self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
    def test_config_roundtrip(self):
        c=config();self.assertEqual(NeuralDeployment.from_dict(json.loads(json.dumps(asdict(c)))),c)
    def test_unknown_config_field_rejected(self):
        d=json.loads(json.dumps(asdict(config())));d['extra']=1
        with self.assertRaises(AudioError):NeuralDeployment.from_dict(d)
    def test_explicit_supported_model(self):
        with self.assertRaisesRegex(AudioError,'MODEL_NOT_ADOPTED'):config(model_id='eleven_v3')
    def test_voice_id_not_path(self):
        with self.assertRaises(AudioError):config(voice_id='../other')
    def test_dialect_not_falsely_enforced(self):
        with self.assertRaisesRegex(AudioError,'LOCALE_UNSUPPORTED'):config(language='en-US')
    def test_phoneme_forcing_not_advertised(self):
        v=neural_catalog(config()).voices[0];self.assertNotIn('phoneme:ipa',v.features);self.assertFalse(v.same_voice_code_switching)
    def test_no_production_quality_claim(self):self.assertEqual(neural_catalog(config()).voices[0].quality_class,'neural-service-unverified')
    def test_fixture_cannot_share_runtime_identity(self):self.assertNotEqual(neural_catalog(config()),neural_catalog(config(),fixture=True))
    def test_every_expressive_setting_changes_identity(self):
        base=neural_catalog(config()).fingerprint()
        for k,v in [('stability',.2),('similarity_boost',.9),('style',.3),('speed',1.1),('seed',7),('use_speaker_boost',False)]:
            with self.subTest(k=k):self.assertNotEqual(base,neural_catalog(config(settings=replace(NeuralSettings(),**{k:v}))).fingerprint())
    def test_nonfinite_and_bool_setting_rejected(self):
        for v in [True,float('nan'),float('inf'),-1,2]:
            with self.subTest(v=v),self.assertRaises(AudioError):NeuralSettings(stability=v)
    def test_speed_bounds(self):
        for v in [.6,1.3,True]:
            with self.assertRaises(AudioError):NeuralSettings(speed=v)
    def test_privacy_policy_in_cache_identity(self):self.assertNotEqual(neural_catalog(config()).fingerprint(),neural_catalog(config(enable_provider_logging=False)).fingerprint())
    def test_prepared_text_exact_wire_payload(self):
        _,pr,rr,_=setup(self.tmp.name);r=rr[0];wire=request_payload(r,pr.config)
        self.assertEqual(wire['text'],r.segment.spoken_text);self.assertEqual(wire['apply_text_normalization'],'off')
        self.assertEqual(wire['language_code'],'en');self.assertNotIn('phoneme',wire)
    def test_generic_wpm_not_silently_mapped(self):
        _,pr,rr,_=setup(self.tmp.name);r=replace(rr[0],settings=replace(rr[0].settings,rate_wpm=170))
        with self.assertRaisesRegex(AudioError,'GENERIC_SETTINGS_UNSUPPORTED'):request_payload(r,pr.config)
    def test_source_markup_not_instructions(self):
        for t in ('Read <break/> next.','[laughs] Explain now.'):
            with self.subTest(t=t):
                _,pr,rr,_=setup(self.tmp.name,p=plan(t))
                with self.assertRaisesRegex(AudioError,'MARKUP'):request_payload(rr[0],pr.config)
    def test_source_bound_neighbor_context(self):
        p,pr,rr,_=setup(self.tmp.name,p=multi_plan(),context=True)
        self.assertEqual(json.loads(pr._payload(rr[0]))['next_text'],p.segments[1].spoken_text)
        self.assertNotIn('next_text',json.loads(pr._payload(rr[1])))
    def test_context_identity_invalidates_cache(self):
        p,pr,rr,_=setup(self.tmp.name,p=multi_plan(),context=True)
        self.assertNotEqual(pr.catalog().fingerprint(),neural_catalog(pr.config,fixture=True).fingerprint())
    def test_context_never_truncated(self):
        _,pr,rr,_=setup(self.tmp.name)
        with self.assertRaisesRegex(AudioError,'CONTEXT_BUDGET'):request_payload(rr[0],pr.config,context={'next_text':'x'*4001})
    def test_allowlist_no_quality_fallback(self):
        p,pr,_,_=setup(self.tmp.name)
        with self.assertRaisesRegex(AudioError,'NO_COMPATIBLE_VOICE'):select_voices(p,pr.catalog(),SelectionPolicy((pr.provider_id,),('cinematic-approved',)))
    def test_rights_revision_changes_identity(self):self.assertNotEqual(neural_catalog(config()).fingerprint(),neural_catalog(config(rights_refs=('new:rights',))).fingerprint())

    def test_multilingual_v2_auto_language_explicit(self):
        c=config(model_id='eleven_multilingual_v2',language_mode='provider_auto')
        _,pr,rr,_=setup(self.tmp.name,c=c)
        self.assertNotIn('language_code',request_payload(rr[0],c))
    def test_multilingual_cannot_claim_forced_language(self):
        with self.assertRaisesRegex(AudioError,'LANGUAGE_CAPABILITY'):config(model_id='eleven_multilingual_v2',language_mode='enforced')
