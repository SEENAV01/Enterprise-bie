from video_helpers import *
from bie.qa.video_v2.metrics import *
from bie.qa.video_v2.codec import *
from bie.qa.video_v2.evaluator import decode_log
from bie.qa.video_v2.media import parse_probe

class MetricTests(FixtureCase):
    def test_sampling_first_last(self):s=sample_indices(self.p);self.assertEqual((s[0],s[-1]),(0,7))
    def test_boundary_neighbors(self):s=sample_indices(replace(self.p,boundaries=(4,)));self.assertTrue({3,4,5}<=set(s))
    def test_cuts_neighbors(self):s=sample_indices(replace(self.p,cuts=(2,)));self.assertTrue({1,2,3}<=set(s))
    def test_sample_unique(self):s=sample_indices(self.p);self.assertEqual(tuple(sorted(set(s))),s)
    def test_exact_pixel_error(self):a=Image.new('RGB',(2,2),(0,0,0));b=Image.new('RGB',(2,2),(255,255,255));self.assertEqual(error_ppm(a,b),1000000)
    def test_pixel_identity(self):a=image(self.frames[0],32,24);self.assertEqual(error_ppm(a,a),0)
    def test_rgb_shape(self):
        with self.assertRaises(ContractError):image(b'wrong',32,24)
    def test_compare_shape(self):
        with self.assertRaises(ContractError):error_ppm(Image.new('RGB',(2,2)),Image.new('RGB',(3,3)))
    def test_black_fraction(self):self.assertEqual(blank_metrics(Image.new('RGB',(2,2)),8)['black_fraction_ppm'],1000000)
    def test_white_not_black(self):self.assertEqual(blank_metrics(Image.new('RGB',(2,2),'white'),8)['black_fraction_ppm'],0)
    def test_uniform_color(self):self.assertEqual(blank_metrics(Image.new('RGB',(2,2),(50,80,120)),8)['max_channel_span'],0)
    def test_clock_healthy(self):self.assertEqual(clock_errors(self.obs,self.p),())
    def test_clock_wrong_fps(self):self.assertIn('VIDEO_FPS',clock_errors(replace(self.obs,fps=Fraction(5)),self.p))
    def test_clock_duplicate_pts(self):self.assertIn('VIDEO_NONMONOTONIC_PTS',clock_errors(replace(self.obs,pts=(0,1,2,2,4,5,6,7)),self.p))
    def test_clock_gap_pts(self):self.assertIn('VIDEO_FRAME_CADENCE',clock_errors(replace(self.obs,pts=(0,1,2,4,5,6,7,8)),self.p))
    def test_clock_first_offset(self):self.assertIn('VIDEO_START_TIME',clock_errors(replace(self.obs,pts=tuple(range(3,11))),self.p))
    def test_clock_duration(self):self.assertIn('VIDEO_RENDER_DURATION',clock_errors(replace(self.obs,durations=(1,)*7+(4,)),self.p))
    def test_clock_packet_duration(self):self.assertIn('VIDEO_PACKET_DURATION',clock_errors(replace(self.obs,durations=(4,)+(1,)*7),self.p))
    def test_fractional_fps(self):
        p=replace(self.p,fps_numerator=30000,fps_denominator=1001);o=replace(self.obs,time_base=Fraction(1,30000),fps=Fraction(30000,1001),pts=tuple(i*1001 for i in range(8)),durations=(1001,)*8);self.assertEqual(clock_errors(o,p),())
    def test_region_profile_rejects_rgba(self):
        buf=io.BytesIO();Image.new('RGBA',(4,4)).save(buf,format='PNG')
        with self.assertRaises(ContractError):region_error(image(self.frames[0],32,24),self.p.regions[0],buf.getvalue())
    def test_region_bad_png(self):
        with self.assertRaises(ContractError):region_error(image(self.frames[0],32,24),self.p.regions[0],b'invalid')
    def test_region_pixel_template_match(self):self.assertEqual(region_error(image(self.frames[0],32,24),self.p.regions[0],(self.root/'template.png').read_bytes()),0)

class ContractTests(FixtureCase):
    def test_request_roundtrip(self):self.assertEqual(load_request(canonical_bytes(asdict(self.r))),self.r)
    def test_policy_roundtrip(self):self.assertEqual(load_policy(canonical_bytes(asdict(self.p))),self.p)
    def test_receipt_roundtrip(self):self.assertEqual(load_receipt(canonical_bytes(asdict(self.cr))),self.cr)
    def test_extra_fields_rejected(self):d=asdict(self.r);d['accepted']=True;self.assertRaises(ContractError,load_request,canonical_bytes(d))
    def test_missing_fields_rejected(self):d=asdict(self.r);del d['video'];self.assertRaises(ContractError,load_request,canonical_bytes(d))
    def test_bool_not_integer(self):d=asdict(self.p);d['width']=True;self.assertRaises(ContractError,load_policy,canonical_bytes(d))
    def test_duplicate_json_keys(self):self.assertRaises(ContractError,load_request,b'{"a":1,"a":2}')
    def test_float_policy_rejected(self):d=asdict(self.p);d['width']=3.5;self.assertRaises(ContractError,load_policy,json.dumps(d).encode())
    def test_unknown_schema(self):self.assertRaises(ContractError,replace,self.r,schema_version='next')
    def test_video_role(self):self.assertRaises(ContractError,replace,self.r,video=replace(self.movie,role='support'))
    def test_duplicate_request_artifact(self):self.assertRaises(ContractError,replace,self.r,build_outputs=(self.code,))
    def test_empty_inputs(self):self.assertRaises(ContractError,replace,self.r,inputs=())
    def test_empty_outputs(self):self.assertRaises(ContractError,replace,self.r,build_outputs=())
    def test_fps_canonical(self):self.assertRaises(ContractError,replace,self.p,fps_numerator=8,fps_denominator=2)
    def test_zero_rate(self):self.assertRaises(ContractError,replace,self.p,fps_numerator=0)
    def test_bounded_decode(self):self.assertRaises(ContractError,replace,self.p,max_decoded_bytes=100)
    def test_window_positive(self):self.assertRaises(ContractError,Window,3,3)
    def test_window_overlap(self):self.assertRaises(ContractError,replace,self.p,blank_allowances=(Window(0,4),Window(3,5)))
    def test_boundary_order(self):self.assertRaises(ContractError,replace,self.p,boundaries=(5,3))
    def test_boundary_range(self):self.assertRaises(ContractError,replace,self.p,cuts=(8,))
    def test_empty_commands(self):self.assertRaises(ContractError,replace,self.cr,command=())
    def test_command_control_chars(self):self.assertRaises(ContractError,replace,self.cr,command=('tsc\nrm',))
    def test_empty_tool_version(self):self.assertRaises(ContractError,replace,self.cr,tool_version='')
    def test_log_empty_preserved(self):self.assertEqual(decode_log(encode_log(b'')),b'')
    def test_log_arbitrary_bytes_preserved(self):data=bytes(range(256));self.assertEqual(decode_log(encode_log(data)),data)
    def test_log_digest_corruption(self):d=json.loads(encode_log(b'abc'));d['sha256']='0'*64;self.assertRaises(ContractError,decode_log,canonical_bytes(d))
    def test_log_base64_corruption(self):d=json.loads(encode_log(b'abc'));d['data']='!';self.assertRaises(ContractError,decode_log,canonical_bytes(d))
    def test_property_pixel_difference_symmetry(self):
        for i in range(0,255,17):
            with self.subTest(i=i):
                a=Image.new('RGB',(2,2),(i,10,20));b=Image.new('RGB',(2,2),(20,i,30));self.assertEqual(error_ppm(a,b),error_ppm(b,a));self.assertTrue(0<=error_ppm(a,b)<=1000000)
    def test_property_sampling_all_durations(self):
        for n in range(1,40):
            with self.subTest(n=n):
                p=replace(self.p,expected_frames=n,regions=(),expected_motion=(),sample_stride=3);s=sample_indices(p);self.assertEqual(s[0],0);self.assertEqual(s[-1],n-1);self.assertTrue(all(0<=i<n for i in s))
