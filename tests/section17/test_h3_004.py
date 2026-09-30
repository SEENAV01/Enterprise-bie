import unittest,tempfile,shutil,json,hashlib,os
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict,replace
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import *
from h3_support import fixture,measure,measured,rater,context,TD,LIMITS,ROOT,media,sha,policy,report,CONTRACT

from bie.evaluation.benchmarks.adoption.grading import grade
class FullFrameReferenceTests(unittest.TestCase):
    def test_exact_full_sequence_matches(self):self.assertEqual('PASS',measured(13)['outcome'])
    def test_three_independent_units(self):self.assertEqual(3,measured(13)['unit_count'])
    def test_wrong_full_rgb_hash_fails(self):
        ref,c=fixture(13);ref['frame_reference']['decoded_sha256']='0'*64
        self.assertEqual('FAIL',measure(13,ref,c)['outcome'])
    def test_wrong_frame_chain_fails(self):
        ref,c=fixture(13);ref['frame_reference']['frame_chain_sha256']='0'*64
        self.assertEqual('FAIL',measure(13,ref,c)['outcome'])
    def test_decoder_mismatch_blocks_oracle(self):
        ref,c=fixture(13);ref['frame_reference']['ffmpeg_sha256']='0'*64
        with self.assertRaisesRegex(BenchmarkError,'FRAME_ORACLE_DECODER_CHANGED'):measure(13,ref,c)
    def test_missing_reference_frame_hash_blocks(self):
        ref,c=fixture(13);ref['frame_reference'].pop('decoded_sha256')
        with self.assertRaises(BenchmarkError):validate_reference(ref,ref['metric_id'])
    def test_candidate_cannot_supply_reference_frames(self):
        ref,c=fixture(13);c['frame_reference']=ref['frame_reference']
        with self.assertRaises(BenchmarkError):validate_candidate(c,ref['metric_id'],LIMITS)
    def test_pixel_sequence_is_order_sensitive(self):
        self.assertNotEqual(hashlib.sha256(b'frameAframeB').hexdigest(),hashlib.sha256(b'frameBframeA').hexdigest())
    def test_same_frame_hash_does_not_excuse_bad_av_policy(self):
        ref,c=fixture(13);ref['av_policy']['expected_frames']=16
        self.assertEqual('FAIL',measure(13,ref,c)['outcome'])
    def test_frame_scope_does_not_claim_perceptual_quality(self):
        self.assertFalse(measured(13)['details']['perceptual_quality_certified']);self.assertIn('EXACT_REFERENCE',measured(13)['details']['scope'])
    def test_oracle_bytes_are_pinned_in_rubric(self):
        ref,c=fixture(13);pin=digest(ref);ref['frame_reference']['decoded_sha256']='a'*64
        with self.assertRaisesRegex(BenchmarkError,'REFERENCE_SNAPSHOT_MISMATCH'):measure(13,ref,c,expected_reference_sha256=pin)
    def test_all_frame_hash_is_not_only_first_and_last(self):
        v=measured(13)['details']['av_receipt']['observations']['video'];self.assertNotEqual(v['decoded_sha256'],v['first_frame_sha256']);self.assertNotEqual(v['decoded_sha256'],v['last_frame_sha256'])
