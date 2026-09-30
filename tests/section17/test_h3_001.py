import unittest,tempfile,shutil,json,hashlib,os
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict,replace
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import *
from h3_support import fixture,measure,measured,rater,context,TD,LIMITS,ROOT,media,sha,policy,report,CONTRACT

class GovernedProfileTests(unittest.TestCase):
    def test_three_explicit_profiles_validate(self):
        for n in (12,13,15):
            ref,c=fixture(n);self.assertEqual(ref,validate_reference(ref,ref['metric_id']));self.assertEqual(c,validate_candidate(c,ref['metric_id'],LIMITS))
    def test_unknown_metric_cannot_use_av_profile(self):
        ref,c=fixture();ref['metric_id']='BIE-EVAL-METRIC-011'
        with self.assertRaises(BenchmarkError):validate_reference(ref,ref['metric_id'])
    def test_unknown_schema_rejected(self):
        ref,c=fixture();ref['schema_version']='latest'
        with self.assertRaises(BenchmarkError):validate_reference(ref,ref['metric_id'])
    def test_unreviewed_reference_cannot_claim_golden(self):
        ref,c=fixture();ref['evidence_grade']='INDEPENDENTLY_REVIEWED_GOLDEN'
        with self.assertRaises(BenchmarkError):validate_reference(ref,ref['metric_id'])
    def test_unknown_reference_policy_field_rejected(self):
        ref,c=fixture();ref['skip_audio']=True
        with self.assertRaises(BenchmarkError):validate_reference(ref,ref['metric_id'])
    def test_reference_digest_cannot_be_candidate_owned(self):
        ref,c=fixture();pin=digest(ref);ref['av_policy']['max_dark_fraction']=1
        with self.assertRaisesRegex(BenchmarkError,'REFERENCE_SNAPSHOT_MISMATCH'):measure(ref=ref,candidate=c,expected_reference_sha256=pin)
    def test_candidate_digest_drift_blocks(self):
        ref,c=fixture();pin=digest(c);c['media']['sha256']='f'*64
        with self.assertRaisesRegex(BenchmarkError,'CANDIDATE_SNAPSHOT_MISMATCH'):measure(ref=ref,candidate=c,expected_candidate_sha256=pin)
    def test_boolean_size_is_not_integer(self):
        ref,c=fixture();c['media']['size_bytes']=True
        with self.assertRaises(BenchmarkError):validate_candidate(c,ref['metric_id'],LIMITS)
    def test_empty_artifact_rejected(self):
        ref,c=fixture();c['media']['size_bytes']=0
        with self.assertRaises(BenchmarkError):validate_candidate(c,ref['metric_id'],LIMITS)
    def test_same_path_media_and_captions_rejected(self):
        ref,c=fixture(15);c['captions']['path']=c['media']['path']
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_ARTIFACT_PATH'):validate_candidate(c,ref['metric_id'],LIMITS)
    def test_caption_format_without_caption_rejected(self):
        ref,c=fixture();c['caption_format']='srt'
        with self.assertRaises(BenchmarkError):validate_candidate(c,ref['metric_id'],LIMITS)
    def test_unsupported_caption_markup_rejected(self):
        ref,c=fixture(15);c['caption_format']='ass'
        with self.assertRaises(BenchmarkError):validate_candidate(c,ref['metric_id'],LIMITS)
    def test_unused_frame_oracle_rejected(self):
        ref,c=fixture();ref['frame_reference']={}
        with self.assertRaises(BenchmarkError):validate_reference(ref,ref['metric_id'])
    def test_structural_copy_does_not_alias_inputs(self):
        ref,c=fixture();out=validate_reference(ref,ref['metric_id']);out['av_policy']['width']=100;self.assertEqual(64,ref['av_policy']['width'])
    def test_resource_limit_change_requires_reference_update(self):
        with self.assertRaisesRegex(BenchmarkError,'AV_LIMITS_PIN_MISMATCH'):measure(limits=replace(LIMITS,deadline_s=31))
    def test_execution_context_not_accepted_as_dictionary(self):
        with self.assertRaisesRegex(BenchmarkError,'TRUSTED_AV_EXECUTION_CONTEXT_REQUIRED'):measure(execution_context={'artifact_root':str(TD)})
    def test_rename_does_not_change_content_identity(self):
        ref,c=fixture();c2=deepcopy(c);c2['media']['path']='different.mkv';self.assertEqual(content_identity(c),content_identity(c2))
    def test_modified_bytes_change_content_identity(self):
        ref,c=fixture();c2=deepcopy(c);c2['media']['sha256']='a'*64;self.assertNotEqual(content_identity(c),content_identity(c2))
