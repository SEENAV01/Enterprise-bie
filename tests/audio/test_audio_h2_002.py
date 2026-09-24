import unittest,tempfile,threading,time,json,subprocess
from pathlib import Path
from unittest.mock import patch
from bie.audio.common import AudioError,fingerprint
from bie.audio.acoustic_contract import AcousticPolicy,build_job
from bie.audio.acoustic_runtime import probe_local_runtime,verify_runtime,run_native
from bie.audio.acoustic_evidence import validate_measurement
from .acoustic_test_support import context,silent_context,clone,rehash
from .qa_test_support import native

class IndependentRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s,cls.m,cls.j,cls.r,cls.result,*_=context()
    def test_three_independent_searches_executed(self):
        self.assertTrue(all([x['mode'] for x in s['native_passes']]==['fsg','allphone','lm'] for s in self.result['segments']))
    def test_real_sample_all_segments_measured(self):self.assertTrue(all(s['status']=='MEASURED' for s in self.result['segments']))
    def test_word_windows_measured_not_provider_copy(self):
        self.assertTrue(any(a['start_sample']!=b['start_sample'] for s,j in zip(self.result['segments'],self.j['segments']) for a,b in zip(s['words'],j['provider_words'])))
    def test_independent_phones_present(self):self.assertTrue(any(p['observed_phones'] for s in self.result['segments'] for p in s['phone_comparisons']))
    def test_no_claimed_confidence_or_acceptance(self):
        self.assertFalse(self.result['pronunciation_verified']);self.assertFalse(self.result['alignment_accepted']);self.assertFalse(self.result['product_accepted'])
        self.assertTrue(all(p['confidence'] is None for s in self.result['segments'] for p in s['phone_comparisons']))
    def test_runtime_model_identity(self):self.assertEqual(verify_runtime(self.r),self.r)
    def test_missing_runtime_file_blocks(self):
        r=clone(self.r);r['files'].pop('phone_lm');rehash(r)
        with self.assertRaises(AudioError):verify_runtime(r)
    def test_rehashed_runtime_drift_blocks(self):
        r=clone(self.r);r['files']['dictionary']['sha256']='0'*64;rehash(r)
        with self.assertRaises(AudioError):verify_runtime(r)
    def test_runtime_implementation_drift_blocks(self):
        r=clone(self.r);r['implementation_fingerprint']=fingerprint('other-code');rehash(r)
        with self.assertRaises(AudioError):verify_runtime(r)
    def test_symlink_native_file_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'model';p.symlink_to(self.r['files']['dictionary']['path']);r=clone(self.r);r['files']['dictionary']['path']=str(p);rehash(r)
            with self.assertRaises(AudioError):verify_runtime(r)
    def test_cancel_before_start(self):
        e=threading.Event();e.set()
        with self.assertRaisesRegex(AudioError,'CANCELLED'):run_native(self.j,self.m.wav_bytes,self.r,cancellation=e)
    def test_cancel_running_real_child(self):
        e=threading.Event();t=threading.Timer(.25,e.set());t.start()
        try:
            with self.assertRaisesRegex(AudioError,'CANCELLED'):run_native(self.j,self.m.wav_bytes,self.r,cancellation=e)
        finally:t.cancel()
    def test_short_deadline_kills_work(self):
        j=build_job(self.m,self.s,AcousticPolicy(deadline_seconds=1))
        with self.assertRaisesRegex(AudioError,'TIMEOUT|WORKER_FAILED'):run_native(j,self.m.wav_bytes,self.r)
    def test_exact_silence_does_not_align_expected_words(self):
        m,j,r,rec=silent_context();self.assertTrue(all(s['status']=='NO_SIGNAL' and not s['words'] for s in r['segments']))
    def test_hindi_explicitly_unsupported_not_english_fallback(self):
        s,m,_=native(language='hindi');result=run_native(build_job(m,s),m.wav_bytes,self.r)
        self.assertTrue(all(s['status']=='UNSUPPORTED_LANGUAGE' and not s['native_passes'] for s in result['segments']))
    def test_repeated_native_measurement_reproducible(self):self.assertEqual(run_native(self.j,self.m.wav_bytes,self.r),self.result)
    def test_forged_native_word_timing_rejected(self):
        r=clone(self.result);r['segments'][0]['words'][0]['start_sample']+=1;rehash(r)
        with self.assertRaises(AudioError):validate_measurement(r,self.j)
    def test_calibration_boolean_cannot_promote(self):
        r=clone(self.result);r['pronunciation_verified']=True;rehash(r)
        with self.assertRaises(AudioError):validate_measurement(r,self.j)
    def test_allphone_metric_rehash_not_accepted(self):
        r=clone(self.result);r['segments'][0]['phone_comparisons'][0]['minimum_edit_distance']+=1;rehash(r)
        with self.assertRaises(AudioError):validate_measurement(r,self.j)
    def test_partial_word_coverage_rejected(self):
        r=clone(self.result);r['segments'][0]['words'].pop();rehash(r)
        with self.assertRaises(AudioError):validate_measurement(r,self.j)
    def test_missing_native_pass_rejected(self):
        r=clone(self.result);r['segments'][0]['native_passes'].pop();rehash(r)
        with self.assertRaises(AudioError):validate_measurement(r,self.j)
