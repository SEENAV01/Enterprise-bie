import tempfile,subprocess,unittest,json,struct
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
from bie.compiler.audio_preparation import *
from bie.compiler.hardened_scene_compile import publish_h3_scene,require_h3_workspace
from tests.compiler.h6_test_support import wav_signal,narration_scene,write_assets,BIG

def seg(a='a',start=0,trim=0,count=100,gain=.5,sid='s'):
    return {'segment_id':sid,'asset_id':a,'start_sample':start,'trim_sample':trim,'sample_count':count,'gain':gain}

class ActualAudioProducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);cls.wav=wav_signal();(cls.root/'source.wav').write_bytes(cls.wav)
        r=subprocess.run(['/usr/bin/ffmpeg','-nostdin','-v','error','-i',str(cls.root/'source.wav'),'-c:a','libmp3lame','-b:a','128k',str(cls.root/'source.mp3')],capture_output=True,text=True,timeout=30)
        if r.returncode:raise AssertionError(r.stderr)
        cls.mp3=cls.root/'source.mp3';cls.h=sha256(cls.mp3.read_bytes()).hexdigest()
        cls.data,cls.receipt=normalize_local_audio(cls.mp3,expected_sha256=cls.h,sample_rate=48000,channels=1)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_actual_decode_runs(self):self.assertTrue(self.receipt['decoder_ran']);self.assertEqual(self.receipt['source_codec'],'mp3')
    def test_decode_namespace_enforced(self):self.assertTrue(all(r['kernel_policy']['kernel_enforced'] for r in self.receipt['executions']))
    def test_pcm_clock_verified(self):meta,_=inspect_pcm(self.data);self.assertEqual(meta['frame_count'],96000);self.assertEqual(meta['sample_rate'],48000)
    def test_source_hash_bound(self):self.assertEqual(self.receipt['input_sha256'],self.h);self.assertEqual(self.receipt['output_sha256'],sha256(self.data).hexdigest())
    def test_source_speech_not_claimed(self):self.assertFalse(self.receipt['accepted']);self.assertEqual(self.receipt['speech_alignment'],'NOT_VERIFIED')
    def test_wrong_hash_block(self):self.assertRaisesRegex(ValueError,'IDENTITY',normalize_local_audio,self.mp3,expected_sha256='0'*64,sample_rate=48000,channels=1)
    def test_symlink_input_block(self):
        link=self.root/'link';link.symlink_to(self.mp3)
        try:self.assertRaisesRegex(ValueError,'PATH',normalize_local_audio,link,expected_sha256=self.h,sample_rate=48000,channels=1)
        finally:link.unlink()
    def test_undeclared_channel_remap_block(self):self.assertRaisesRegex(ValueError,'REMAPPING',normalize_local_audio,self.mp3,expected_sha256=self.h,sample_rate=48000,channels=2)
    def test_bad_stream_block(self):
        f=self.root/'bad';f.write_bytes(b'no audio bytes');self.assertRaisesRegex(ValueError,'PROBE_BLOCKED',normalize_local_audio,f,expected_sha256=sha256(f.read_bytes()).hexdigest(),sample_rate=48000,channels=1)
    def test_normalized_asset_adopts_existing_publication(self):
        p,_=narration_scene();d=asset_descriptor(self.data,asset_id='signal',rights_ref='test-tone',source_refs=p['source_refs'],reasoning_refs=p['reasoning_refs']);p['metadata']['compiler_h6']['audio_assets']=[d]
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);r=publish_h3_scene(p,root/'s',target=BIG,asset_root=write_assets(root/'a',{d['public_path']:self.data}));self.assertEqual(r,require_h3_workspace(root/'s'))

class SampleMixTests(unittest.TestCase):
    def setUp(self):self.a=wav_bytes(struct.pack('<h',10000)*100,48000,1);self.b=wav_bytes(struct.pack('<h',2000)*100,48000,1)
    def mix(self,segs=None,assets=None,**kw):return mix_pcm_segments(assets or {'a':self.a,'b':self.b},segs or [seg(),seg('b',start=50,count=100,sid='b')],sample_rate=48000,channels=1,total_samples=200,**kw)
    def test_exact_sample_overlap(self):data,r=self.mix();_,pcm=inspect_pcm(data);v=struct.unpack('<200h',pcm);self.assertEqual(v[:50],(5000,)*50);self.assertEqual(v[50:100],(6000,)*50);self.assertEqual(v[100:150],(1000,)*50);self.assertEqual(v[150:],(0,)*50)
    def test_order_independent(self):a,_=self.mix();b,_=self.mix([seg('b',start=50,count=100,sid='b'),seg()]);self.assertEqual(a,b)
    def test_source_hashes_preserved(self):_,r=self.mix();self.assertEqual(r['input_hashes']['a'],sha256(self.a).hexdigest());self.assertFalse(r['accepted'])
    def test_clipping_rejected_not_limited(self):
        loud=wav_bytes(struct.pack('<h',30000)*100,48000,1)
        self.assertRaisesRegex(ValueError,'CLIPPING',self.mix,[seg(gain=1),seg('b',gain=1,sid='b')],{'a':loud,'b':loud})
    def test_range_overrun_block(self):self.assertRaisesRegex(ValueError,'RANGE',self.mix,[seg(count=101),seg('b',sid='b')])
    def test_clock_mismatch_block(self):self.assertRaisesRegex(ValueError,'CLOCK',self.mix,assets={'a':self.a,'b':wav_bytes(b'\0'*200,44100,1)})
    def test_unknown_fields_block(self):s=seg();s['normalize']=True;self.assertRaises(ValueError,self.mix,[s,seg('b',sid='b')])
    def test_nan_gain_block(self):self.assertRaises(ValueError,self.mix,[seg(gain=float('nan')),seg('b',sid='b')])
    def test_unused_asset_block(self):self.assertRaisesRegex(ValueError,'UNUSED',self.mix,[seg()])
    def test_negative_start_block(self):self.assertRaises(ValueError,self.mix,[seg(start=-1),seg('b',sid='b')])
    def test_duplicate_ids_block(self):self.assertRaisesRegex(ValueError,'IDENTITY',self.mix,[seg(),seg('b')])
    def test_output_is_existing_asset_contract(self):data,r=self.mix();d=asset_descriptor(data,asset_id='mix',rights_ref='test',source_refs=['s'],reasoning_refs=['r']);self.assertEqual(d['frame_count'],200);self.assertTrue(d['public_path'].endswith('.wav'))
