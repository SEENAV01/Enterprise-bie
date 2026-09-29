from audio_helpers import *
from bie.qa.audio_v2.pcm import read_pcm
from bie.qa.audio_v2.captions import parse_captions,time_ms
from bie.qa.audio_v2.codec import load_request,load_policy,loads,decode
from fractions import Fraction

class ParserTests(unittest.TestCase):
    def test_pcm_durations_exact(self):
        for rate in (8000,16000,22050,44100,48000):
            for count in (1,37,999):
                with self.subTest(rate=rate,count=count):self.assertEqual(read_pcm(wav_bytes(rate=rate,samples=count)).duration_ms,Fraction(count*1000,rate))
    def test_stereo_phase_cancellation_not_silence(self):self.assertGreater(read_pcm(wav_bytes(channels=2,mode='opposed')).stats()['nonzero'],0)
    def test_riff_truncated(self):
        b=wav_bytes()
        for cut in (0,1,4,12,43,len(b)-1):
            with self.subTest(cut=cut),self.assertRaises(ContractError):read_pcm(b[:cut])
    def test_riff_wrong_size(self):
        b=wav_bytes();b=b[:4]+struct.pack('<I',1)+b[8:]
        with self.assertRaises(ContractError):read_pcm(b)
    def test_riff_unsupported_format(self):
        b=bytearray(wav_bytes());struct.pack_into('<H',b,20,3)
        with self.assertRaises(ContractError):read_pcm(bytes(b))
    def test_riff_bad_rate(self):
        b=bytearray(wav_bytes());struct.pack_into('<I',b,24,4000)
        with self.assertRaises(ContractError):read_pcm(bytes(b))
    def test_riff_duplicate_chunk(self):
        b=wav_bytes();b=b+b'JUNK'+struct.pack('<I',0)+b'JUNK'+struct.pack('<I',0);b=b[:4]+struct.pack('<I',len(b)-8)+b[8:]
        with self.assertRaises(ContractError):read_pcm(b)
    def test_sample_window_limits(self):
        a=read_pcm(wav_bytes())
        for x,y in ((-1,1),(1,1),(0,8001)):
            with self.subTest(start=x,end=y),self.assertRaises(ContractError):a.has_signal(x,y)
    def test_timestamp_round_trip(self):
        for m in range(0,1000,37):
            with self.subTest(ms=m):self.assertEqual(time_ms(f'00:00:01,{m:03}','srt'),1000+m)
    def test_timestamp_bad(self):
        for x in ('00:60:00,000','00:00:60,000','-00:00:00,000','00:00:01.000','00:00:01,1','nan','00:00:01,000 align:start'):
            with self.subTest(value=x),self.assertRaises(ContractError):time_ms(x,'srt')
    def test_webvtt_missing_header(self):
        with self.assertRaises(ContractError):parse_captions(b'1\n00:00:00.000 --> 00:00:01.000\nx','webvtt')
    def test_caption_markup_rejected(self):
        with self.assertRaises(ContractError):parse_captions(b'1\n00:00:00,000 --> 00:00:01,000\n<b>x</b>','srt')
    def test_caption_bidi_rejected(self):
        with self.assertRaises(ContractError):parse_captions('1\n00:00:00,000 --> 00:00:01,000\nx\u202e'.encode(),'srt')
    def test_caption_duplicate_id(self):
        with self.assertRaises(ContractError):parse_captions(b'1\n00:00:00,000 --> 00:00:01,000\nx\n\n1\n00:00:01,000 --> 00:00:02,000\ny','srt')
    def test_caption_empty(self):
        with self.assertRaises(ContractError):parse_captions(b'','srt')
    def test_caption_invalid_utf8(self):
        with self.assertRaises(ContractError):parse_captions(b'\xff','srt')
    def test_hindi_captions_preserved(self):
        s='बल वस्तु को गति देता है।';c=parse_captions(('1\n00:00:00,000 --> 00:00:03,000\n'+s).encode(),'srt');self.assertEqual(c[0].text,s)

class ContractTests(FixtureCase):
    def test_json_roundtrip(self):self.assertEqual(load_request(canonical_bytes(asdict(self.r))),self.r);self.assertEqual(load_policy(canonical_bytes(asdict(self.p))),self.p)
    def test_json_extra_field(self):
        d=asdict(self.r);d['product_accepted']=True
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_duplicate_json_key(self):
        with self.assertRaises(ContractError):loads(b'{"x":1,"x":2}')
    def test_bool_not_time(self):
        with self.assertRaises(ContractError):replace(self.r.clips[0],start_ms=True)
    def test_float_not_time(self):
        with self.assertRaises(ContractError):replace(self.r.clips[0],start_ms=0.2)
    def test_invalid_policy_ranges(self):
        for field,val in (('max_caption_chars_per_second',0),('max_caption_lines',0),('caption_tolerance_ms',-1),('max_clipped_ppm',100001),('minimum_independent_assessors',0)):
            with self.subTest(field=field),self.assertRaises(ContractError):replace(self.p,**{field:val})
    def test_duplicate_clips(self):
        with self.assertRaises(ContractError):replace(self.r,clips=self.r.clips*2)
    def test_duplicate_artifact_paths(self):
        with self.assertRaises(ContractError):replace(self.r,clips=(replace(self.r.clips[0],timing=self.r.clips[0].wav),))
    def test_term_original_text(self):
        with self.assertRaises(ContractError):replace(self.p,terms=(replace(self.p.terms[0],text='Wrong'),))
    def test_word_order(self):
        with self.assertRaises(ContractError):self.timing(words=(Word(1,0,5,'Force',0,2000),))
    def test_word_overlap(self):
        with self.assertRaises(ContractError):self.timing(words=(Word(0,0,5,'Force',0,2000),Word(1,6,11,'moves',1999,4000)))
    def test_policy_unknown_cue_clip(self):
        with self.assertRaises(ContractError):replace(self.p,cues=(replace(self.p.cues[0],clip_id='missing'),))
