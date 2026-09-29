from video_helpers import *
import os,sys,time
from bie.qa.video_v2.process import run_bounded,MediaTools
from bie.qa.video_v2.media import parse_probe

class TrustTests(FixtureCase):
    def test_testonly_key(self):v,k=signed(self.r,self.p,assurance='test_only');self.check_code('VIDEO_TEST_ONLY_REVIEW',extra=dict(reviews=v,verifier=k))
    def test_unknown_key(self):v,k=signed(self.r,self.p);self.check_code('VIDEO_UNKNOWN_REVIEW_KEY',extra=dict(reviews=v,verifier=ReviewVerifier()))
    def test_tampered_signature(self):v,k=signed(self.r,self.p);v=(replace(v[0],signature='0'*64),)+v[1:];self.check_code('VIDEO_BAD_REVIEW_SIGNATURE',extra=dict(reviews=v,verifier=k))
    def test_stale_review(self):v,k=signed(self.r,self.p);v=(replace(v[0],issued_at=NOW-4000,expires_at=NOW-1),)+v[1:];self.check_code('VIDEO_REVIEW_TIME_INVALID',extra=dict(reviews=v,verifier=k))
    def test_wrong_request_review(self):v,k=signed(replace(self.r,run_id='other'),self.p);self.check_code('VIDEO_REVIEW_REQUEST_MISMATCH',extra=dict(reviews=v,verifier=k))
    def test_wrong_policy_review(self):v,k=signed(self.r,replace(self.p,black_level=1));self.check_code('VIDEO_REVIEW_POLICY_MISMATCH',extra=dict(reviews=v,verifier=k))
    def test_negative_review_blocks(self):v,k=signed(self.r,self.p,verdict='REJECTED');self.check_code('VIDEO_REVIEW_REJECTED',extra=dict(reviews=v,verifier=k))
    def test_uncertain_review_not_accepted(self):v,k=signed(self.r,self.p,verdict='UNCERTAIN');self.check_code('VIDEO_REVIEW_UNCERTAIN',extra=dict(reviews=v,verifier=k))
    def test_duplicate_review(self):v,k=signed(self.r,self.p);self.assertRaises(ContractError,self.run_eval,extra=dict(reviews=v+(v[0],),verifier=k))
    def test_evidence_identity_review(self):v,k=signed(self.r,self.p);v=(replace(v[0],evidence_ids=('wrong',)),)+v[1:];self.check_code('VIDEO_REVIEW_EVIDENCE',extra=dict(reviews=v,verifier=k))
    def test_one_reviewer_not_two(self):self.check_code('VIDEO_EXECUTION_OR_SCOPE_REVIEW_REQUIRED',p=replace(self.p,minimum_independent_assessors=2))
    def test_link_file_rejected(self):p=self.root/'input.ts';p.unlink();p.symlink_to(self.root/'output.js');self.check_code('ARTIFACT_OPEN_OR_READ_FAILED')
    def test_hardlink_rejected(self):os.link(self.root/'input.ts',self.root/'another.ts');self.check_code('HARD_LINK_REJECTED')
    def test_root_symlink_rejected(self):
        link=self.root/'link';link.symlink_to(self.root,target_is_directory=True)
        with patch('bie.qa.video_v2.evaluator.inspect_bytes',return_value=self.obs):r=evaluate(self.r,link,self.p,as_of=NOW)
        self.assertIn('ARTIFACT_ROOT_UNAVAILABLE',self.codes(r))
    def test_nonregular_rejected(self):p=self.root/'input.ts';p.unlink();os.mkfifo(p);self.check_code('NOT_REGULAR_FILE')

class ProcessTests(unittest.TestCase):
    def test_collect_stdout_and_stderr(self):r=run_bounded([sys.executable,'-c','import sys; print("out"); print("err", file=sys.stderr)']);self.assertEqual(r.returncode,0);self.assertEqual(r.stdout,b'out\n');self.assertEqual(r.stderr,b'err\n')
    def test_returncode_not_masked(self):self.assertEqual(run_bounded([sys.executable,'-c','raise SystemExit(7)']).returncode,7)
    def test_stdout_cap(self):self.assertRaises(ContractError,run_bounded,[sys.executable,'-c','print("x"*10000)'],max_stdout=100)
    def test_stderr_cap(self):self.assertRaises(ContractError,run_bounded,[sys.executable,'-c','import sys;sys.stderr.write("x"*10000)'],max_stderr=100)
    def test_timeout(self):self.assertRaises(ContractError,run_bounded,[sys.executable,'-c','import time;time.sleep(10)'],timeout=1)
    def test_relative_command_rejected(self):self.assertRaises(ContractError,run_bounded,['python','-V'])
    def test_missing_tool_rejected(self):self.assertRaises(ContractError,MediaTools,'/nonexistent/ffmpeg','/nonexistent/ffprobe')
    def test_timeout_bool_rejected(self):self.assertRaises(ContractError,run_bounded,[sys.executable,'-V'],timeout=True)

class ProbeTests(FixtureCase):
    def raw(self):return {'streams':[dict(codec_type='video',width=32,height=24,codec_name='h264',pix_fmt='yuv420p',time_base='1/4',avg_frame_rate='4/1')], 'frames':[dict(media_type='video',best_effort_timestamp=i,duration=1,width=32,height=24) for i in range(8)]}
    def test_valid_probe(self):v,n,tb,fps,pts,dur=parse_probe(self.raw(),self.p);self.assertEqual(len(pts),8)
    def test_missing_timestamp(self):r=self.raw();del r['frames'][0]['best_effort_timestamp'];self.assertRaises(ContractError,parse_probe,r,self.p)
    def test_missing_duration(self):r=self.raw();del r['frames'][0]['duration'];self.assertRaises(ContractError,parse_probe,r,self.p)
    def test_no_video_stream(self):r=self.raw();r['streams']=[];self.assertRaises(ContractError,parse_probe,r,self.p)
    def test_extra_video_stream(self):r=self.raw();r['streams']*=2;self.assertRaises(ContractError,parse_probe,r,self.p)
    def test_wrong_dimensions(self):r=self.raw();r['streams'][0]['width']=64;self.assertRaises(ContractError,parse_probe,r,self.p)
    def test_display_rotation(self):r=self.raw();r['streams'][0]['side_data_list']=[dict(rotation=90)];self.assertRaises(ContractError,parse_probe,r,self.p)
    def test_non_square_pixels(self):r=self.raw();r['streams'][0]['sample_aspect_ratio']='2:1';self.assertRaises(ContractError,parse_probe,r,self.p)
    def test_interlaced(self):r=self.raw();r['streams'][0]['field_order']='tt';self.assertRaises(ContractError,parse_probe,r,self.p)
    def test_codec_change(self):r=self.raw();r['streams'][0]['codec_name']='other';self.assertRaises(ContractError,parse_probe,r,self.p)
    def test_no_frames(self):r=self.raw();r['frames']=[];self.assertRaises(ContractError,parse_probe,r,self.p)
    def test_dynamic_dimensions(self):r=self.raw();r['frames'][3]['height']=25;self.assertRaises(ContractError,parse_probe,r,self.p)
    def test_invalid_timebase(self):r=self.raw();r['streams'][0]['time_base']='0/0';self.assertRaises(ContractError,parse_probe,r,self.p)
