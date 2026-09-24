import unittest
from dataclasses import replace
from unittest.mock import patch
from bie.audio.common import AudioError,fingerprint
from bie.audio.pipeline_contract import validate_request,request_key,PipelineLimits,prepare_document,build_request
from bie.audio.pipeline_profile import validate_profile,engine_sources,probe_profile
from bie.audio.durable_contract import DurablePolicy
from .pipeline_test_support import context,request,clone

class Contracts(unittest.TestCase):
    def test_01_source_preparation_preserved(self):
        c=context();p=validate_request(c['request']);self.assertEqual(p,prepare_document(c['source']))
    def test_02_declared_provenance(self):
        self.assertEqual(context()['request']['source_refs'],['synthetic:audio-fixture:1'])
    def test_03_stable_request_identity(self):
        self.assertEqual(request(),request())
    def test_04_modified_source_does_not_validate(self):
        r=clone(request());r['source']['drafts'][0]['text']='Changed';
        with self.assertRaises(AudioError):validate_request(r)
    def test_05_same_job_revision_changed_source_conflicts(self):
        raw=clone(context()['source']);raw['drafts'][0]['text']='Another exact source.';r=request(source=raw)
        self.assertNotEqual(r['fingerprint'],request()['fingerprint']);self.assertEqual(request_key(r),request_key(request()))
    def test_06_new_revision_new_key(self):self.assertNotEqual(request_key(request(revision='r2')),request_key(request()))
    def test_07_unknown_fields(self):
        r=request();r['command']='sh'
        with self.assertRaises(AudioError):validate_request(r)
    def test_08_acceptance_escalation(self):
        r=request();r['product_accepted']=True;r['fingerprint']=fingerprint({k:v for k,v in r.items() if k!='fingerprint'})
        with self.assertRaises(AudioError):validate_request(r)
    def test_09_rehashed_prepared_plan(self):
        r=request();r['plan_fingerprint']='sha256:'+'0'*64
        with self.assertRaises(AudioError):validate_request(r)
    def test_10_bad_uuid(self):
        with self.assertRaises(AudioError):request(run_id='not-a-run')
    def test_11_empty_key_id(self):
        with self.assertRaises(AudioError):request(key_id='')
    def test_12_segment_char_budget(self):
        with self.assertRaises(AudioError):request(limits=PipelineLimits(max_spoken_chars=4))
    def test_13_boolean_limits_rejected(self):
        with self.assertRaises(AudioError):PipelineLimits(max_segments=True)
    def test_14_duration_limits_rejected(self):
        with self.assertRaises(AudioError):PipelineLimits(max_audio_seconds=301)
    def test_15_invalid_bundle_policy(self):
        with self.assertRaises(AudioError):PipelineLimits(max_file_bytes=20000,max_bundle_bytes=10000)
    def test_16_storage_budget_binding(self):
        with self.assertRaises(AudioError):request(durable_policy=DurablePolicy(max_artifact_bytes=4096))
    def test_17_unknown_preparation_profile(self):
        with self.assertRaises(AudioError):request(preparation_profile='arbitrary')
    def test_18_review_input_blocked(self):
        raw=clone(context()['source']);raw['drafts'][0]['requires_review']=True
        with self.assertRaises((ValueError,AudioError)):request(source=raw)
    def test_19_profile_exact_reprobe(self):
        c=context();self.assertEqual(c['profile'],validate_profile(c['profile']))
    def test_20_profile_runtime_tamper(self):
        p=clone(context()['profile']);p['provider_runtime_fingerprint']='sha256:'+'0'*64
        with self.assertRaises(AudioError):validate_profile(p)
    def test_21_shadowed_launcher_rejected(self):
        with patch('bie.audio.pipeline_profile.shutil.which',return_value='/tmp/unshare'):
            with self.assertRaises(AudioError):probe_profile()
    def test_22_engine_closure_has_unchanged_dsp_and_native_child(self):
        paths=engine_sources()
        for n in ('bie/audio/mix_pipeline.py','bie/audio/timed_espeak_provider.py','bie/audio/espeak_timing_worker.py','bie/director/director_artifacts.py'):
            self.assertIn(n,paths)
    def test_23_host_and_namespace_identities_explicit(self):
        p=context()['profile'];self.assertIn('host_discovery_identity',p);self.assertIn('ACTUAL_CANONICAL_NAMESPACE',p['discovery_scope'])
    def test_24_segment_count_not_truncated(self):
        raw=clone(context()['source']);raw['drafts'][0]['text']='One. Two. Three.';raw['policy']['max_chars']=6
        with self.assertRaises(AudioError):request(source=raw,limits=PipelineLimits(max_segments=1))

    def test_25_canonical_api_sources_resolve_from_installed_modules(self):
        import importlib.util
        from bie.audio.pipeline_profile import engine_sources
        sources=engine_sources()
        for name in ('bie.infrastructure.artifact_store','bie.director.director_artifacts','bie.bie_core.artifact_contracts'):
            self.assertEqual(sources[name.replace('.','/')+'.py'],__import__('pathlib').Path(importlib.util.find_spec(name).origin))
