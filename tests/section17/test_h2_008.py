import unittest,tempfile,copy,hashlib
from pathlib import Path
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.av.service import *
from h2_support import policy,media,sha,report
class H2008(unittest.TestCase):
 def run_case(self,kind='tone',**changes):
  p=policy(**changes);return collect_and_evaluate(media_path=media(kind),media_sha256=sha(media(kind)),policy=p,policy_sha256=digest(p),run_id='case')
 def test_actual_valid_candidate(self):self.assertEqual(report()['status'],'DIAGNOSTIC_PASS')
 def test_missing_audio_fails(self):r=self.run_case('noaudio');self.assertEqual(r['status'],'FAIL');self.assertIn('REQUIRED_AUDIO_MISSING',r['reasons'])
 def test_silence_fails(self):r=self.run_case('silence');self.assertIn('SILENT_CHANNEL_FLOOR',r['reasons']);self.assertNotEqual(r['status'],'DIAGNOSTIC_PASS')
 def test_clip_fails(self):self.assertIn('CLIPPED_AUDIO_FLOOR',self.run_case('clip')['reasons'])
 def test_black_fails(self):self.assertIn('DARK_FRAME_FLOOR',self.run_case('black')['reasons'])
 def test_corrupt_media_blocked(self):self.assertEqual(self.run_case('corrupt')['status'],'BLOCKED')
 def test_wrong_frame_reference_fails(self):self.assertIn('REFERENCE_FRAME_COUNT_MISMATCH',self.run_case(expected_frames=9)['reasons'])
 def test_missing_captions_fails(self):self.assertIn('REQUIRED_CAPTIONS_MISSING',self.run_case(require_captions=True,caption_text_sha256='a'*64)['reasons'])
 def test_policy_hash_mismatch(self):
  with self.assertRaises(BenchmarkError):collect_and_evaluate(media_path=media(),media_sha256=sha(media()),policy=policy(),policy_sha256='a'*64,run_id='case')
 def test_media_hash_mismatch(self):p=policy();r=collect_and_evaluate(media_path=media(),media_sha256='0'*64,policy=p,policy_sha256=digest(p),run_id='case');self.assertEqual(r['status'],'BLOCKED')
 def test_exact_policy_fields(self):
  with self.assertRaises(BenchmarkError):validate_policy(policy(pass_override=True))
 def test_boolean_score_limit_rejected(self):
  with self.assertRaises(BenchmarkError):validate_policy(policy(max_dark_fraction=True))
 def test_required_narration_cannot_be_empty(self):
  with self.assertRaises(BenchmarkError):validate_policy(policy(narration_intervals_s=[]))
 def test_receipt_tamper_detected(self):
  r=report();r['reference_sha256']='0'*64
  with self.assertRaises(BenchmarkError):verify_receipt(r)
 def test_no_acceptance_flags(self):
  r=report()
  for k in ('release_authorized','product_accepted','native_execution_verified','semantic_speech_verified'):self.assertIs(r[k],False)
 def test_caption_text_pin_actual(self):
  with tempfile.TemporaryDirectory() as td:
   cap=Path(td)/'a.srt';cap.write_text('1\n00:00:00,000 --> 00:00:02,000\nHello\n');p=policy(require_captions=True,caption_text_sha256=hashlib.sha256(b'Hello').hexdigest())
   r=collect_and_evaluate(media_path=media(),media_sha256=sha(media()),policy=p,policy_sha256=digest(p),run_id='cap',caption_path=cap,caption_sha256=sha(cap))
   self.assertEqual(r['status'],'DIAGNOSTIC_PASS')
 def test_unexpected_evaluator_failure_blocked(self):
  with patch('bie.evaluation.benchmarks.av.service.inspect',side_effect=RuntimeError('secret')):
   r=self.run_case();self.assertEqual(r['status'],'BLOCKED');self.assertNotIn('secret',str(r))
 def test_no_numeric_type_rewrite_of_reference(self):p=policy();self.assertEqual(digest(validate_policy(p)),digest(p))
 def test_native_flag_escalation_even_rehashed(self):
  r=report();r['native_execution_verified']=True;r.pop('receipt_sha256');r['receipt_sha256']=digest(r)
  with self.assertRaises(BenchmarkError):verify_receipt(r)
 def test_tools_have_actual_binary_identity(self):
  r=report();ids=r['observations']['tool_binary_identity'];self.assertEqual(set(ids),{'ffmpeg','ffprobe'})
  for entry in ids.values():self.assertEqual(len(entry['sha256']),64);self.assertGreater(entry['bytes'],0)
