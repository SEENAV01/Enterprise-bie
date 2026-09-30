import unittest,tempfile,shutil,json,hashlib,os
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict,replace
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import *
from h3_support import fixture,measure,measured,rater,context,TD,LIMITS,ROOT,media,sha,policy,report,CONTRACT

class HybridAccessibilityTests(unittest.TestCase):
    def test_actual_caption_audio_and_static_controls_pass(self):self.assertEqual('PASS',measured(15)['outcome'])
    def test_static_checks_retained_in_units(self):
        keys=[u['id'] for u in measured(15)['units']];self.assertTrue(any(k.startswith('static:contrast') for k in keys));self.assertTrue(any(k.startswith('static:control') for k in keys))
    def test_metadata_only_cannot_pass_missing_caption_bytes(self):
        ref,c=fixture(15);c['captions']=None;c['caption_format']=None;self.assertEqual('FAIL',measure(15,ref,c)['outcome'])
    def test_contrast_failure_not_hidden_by_av_pass(self):
        ref,c=fixture(15);c['a11y_candidate']['text_styles'][0].update(foreground=[255]*3,background=[255]*3)
        m=measure(15,ref,c);self.assertEqual('FAIL',m['outcome']);self.assertEqual('DIAGNOSTIC_PASS',m['details']['av_receipt']['status'])
    def test_focus_trap_fails_hybrid(self):
        ref,c=fixture(15);control=c['a11y_candidate']['controls'][0];control['next_id']=control['id'];self.assertEqual('FAIL',measure(15,ref,c)['outcome'])
    def test_missing_alt_text_fails(self):
        ref,c=fixture(15);c['a11y_candidate']['alts']=[];self.assertEqual('FAIL',measure(15,ref,c)['outcome'])
    def test_wrong_static_caption_text_fails(self):
        ref,c=fixture(15);c['a11y_candidate']['captions'][0]['text']='Wrong words';self.assertEqual('FAIL',measure(15,ref,c)['outcome'])
    def test_reference_cannot_disable_audio(self):
        ref,c=fixture(15);ref['av_policy']['require_audio']=False
        with self.assertRaisesRegex(BenchmarkError,'CAPTION_AUDIO_POLICY_INCONSISTENT'):validate_reference(ref,ref['metric_id'])
    def test_reference_cannot_disable_captions(self):
        ref,c=fixture(15);ref['av_policy']['require_captions']=False;ref['av_policy']['caption_text_sha256']=None
        with self.assertRaises(BenchmarkError):validate_reference(ref,ref['metric_id'])
    def test_static_and_decoded_duration_must_agree(self):
        ref,c=fixture(15);ref['a11y_reference']['duration_ms']=3000
        with self.assertRaisesRegex(BenchmarkError,'ACCESSIBILITY_DURATION_BINDING_MISMATCH'):measure(15,ref,c)
    def test_absent_static_reference_blocks(self):
        ref,c=fixture(15);ref['a11y_reference']=None
        with self.assertRaises(BenchmarkError):validate_reference(ref,ref['metric_id'])
    def test_no_browser_or_speech_semantic_certification(self):
        m=measured(15);self.assertFalse(m['details']['browser_runtime_verified']);self.assertFalse(m['details']['static_accessibility']['wcag_conformance_certified']);self.assertFalse(m['details']['av_receipt']['semantic_speech_verified'])

    def test_metadata_caption_cannot_describe_different_observed_text(self):
        ref,c=fixture(15);ref['a11y_reference']['speech'][0]['transcript']='Different words';c['a11y_candidate']['captions'][0]['text']='Different words'
        self.assertEqual('FAIL',measure(15,ref,c)['outcome'])
