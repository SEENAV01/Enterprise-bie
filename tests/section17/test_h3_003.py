import unittest,tempfile,shutil,json,hashlib,os
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict,replace
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import *
from h3_support import fixture,measure,measured,rater,context,TD,LIMITS,ROOT,media,sha,policy,report,CONTRACT

from bie.evaluation.benchmarks.adoption.grading import grade
class FullRenderProfileTests(unittest.TestCase):
    def test_actual_render_profile_reads_all_frames(self):
        m=measured(12);self.assertEqual('PASS',m['outcome']);self.assertEqual(8,m['details']['av_receipt']['observations']['video']['decoded_frames'])
    def test_audio_samples_actually_observed(self):
        v=measured(12)['details']['av_receipt']['observations']['audio'];self.assertGreater(len(canonical_json(v)),50)
    def test_status_does_not_mean_native_acceptance(self):
        m=measured();self.assertFalse(m['product_accepted']);self.assertFalse(m['native_bie_execution_verified']);self.assertFalse(m['details']['semantic_teaching_quality_verified'])
    def test_injected_pass_evidence_rejected(self):
        with self.assertRaisesRegex(BenchmarkError,'AV_RECEIPT_INJECTION_REJECTED'):measure(source_artifacts={'receipt':measured()['details']['av_receipt']})
    def test_missing_context_no_disk_read(self):
        with patch('bie.evaluation.benchmarks.adoption.metric.frozen_bundle') as f,self.assertRaises(BenchmarkError):measure(execution_context=None)
        f.assert_not_called()
    def test_wrong_frame_count_fails_score(self):
        ref,c=fixture();ref['av_policy']['expected_frames']=9;v=measure(ref=ref,candidate=c);self.assertEqual('FAIL',v['outcome']);self.assertEqual('0',v['score_exact'])
    def test_wrong_dimensions_fail(self):
        ref,c=fixture();ref['av_policy']['width']=66;self.assertEqual('FAIL',measure(ref=ref,candidate=c)['outcome'])
    def test_candidate_bytes_must_match_declared_hash(self):
        ref,c=fixture();c['media']['sha256']='1'*64
        with self.assertRaisesRegex(BenchmarkError,'ADOPTION_HASH_MISMATCH'):measure(ref=ref,candidate=c)
    def test_corrupt_media_blocks_not_zero_quality_score(self):
        p=media('corrupt');ref,c=fixture();c['media']={'path':p.name,'sha256':sha(p),'size_bytes':p.stat().st_size}
        with self.assertRaisesRegex(BenchmarkError,'AV_COLLECTION_BLOCKED'):measure(ref=ref,candidate=c,root=p.parent)
    def test_missing_audio_fails_reference_policy(self):
        p=media('noaudio');ref,c=fixture();c['media']={'path':p.name,'sha256':sha(p),'size_bytes':p.stat().st_size}
        self.assertEqual('FAIL',measure(ref=ref,candidate=c,root=p.parent)['outcome'])
    def test_silent_audio_fails(self):
        p=media('silence');ref,c=fixture();c['media']={'path':p.name,'sha256':sha(p),'size_bytes':p.stat().st_size}
        self.assertEqual('FAIL',measure(ref=ref,candidate=c,root=p.parent)['outcome'])
    def test_rehashed_inconsistent_av_status_rejected(self):
        ref,c=fixture();av=measured()['details']['av_receipt'];av['reasons']=['FALSE_REASON'];av['status']='FAIL';av['receipt_sha256']=digest({k:v for k,v in av.items() if k!='receipt_sha256'})
        with self.assertRaisesRegex(BenchmarkError,'AV_DECISION_INCONSISTENT'):grade(ref['metric_id'],ref,c,av)
    def test_collector_mismatched_candidate_rejected(self):
        av=measured()['details']['av_receipt'];av['candidate_identity']['media_sha256']='e'*64;av['candidate_sha256']=digest(av['candidate_identity']);av['receipt_sha256']=digest({k:v for k,v in av.items() if k!='receipt_sha256'})
        with patch('bie.evaluation.benchmarks.adoption.metric.service.collect_and_evaluate',return_value=av),self.assertRaisesRegex(BenchmarkError,'AV_COLLECTOR_BINDING_MISMATCH'):measure()
    def test_all_pixels_inspection_label(self):
        self.assertEqual('ALL_PIXELS_RGB8_ALL_FRAMES',measured()['details']['av_receipt']['observations']['video']['inspection'])
