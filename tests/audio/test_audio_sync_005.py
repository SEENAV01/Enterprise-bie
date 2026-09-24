from dataclasses import replace
import hashlib,unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.pause_sync import *
from bie.audio.caption_alignment import align_captions
from bie.audio.sync_contract import samples_for_ms
from bie.audio.scene_sync import assemble_scenes
from bie.audio.pcm_audio import validate_wav,encode_pcm
from tests.audio.sync_test_support import timeline_fixture

class PauseSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p,cls.a,cls.t,cls.line,cls.wav=timeline_fixture(values=('Alpha beta gamma.','Delta epsilon zeta.'),pause=350)
        cls.c=tuple(align_captions(a,t,require_measured=False) for a,t in zip(cls.a,cls.t))
    def make(self,**kw):return synchronize_pauses(kw.get('timeline',self.line),kw.get('wav',self.wav),kw.get('assets',self.a),kw.get('alignments',self.t),kw.get('captions',self.c),require_measured=kw.get('require_measured',False))
    def test_exact_additional_pause_count(self):self.assertEqual(len(self.make().windows),2)
    def test_exact_sample_count(self):self.assertTrue(all(w.end_sample-w.start_sample==samples_for_ms(350,22050) for w in self.make().windows))
    def test_original_pause_refs_retained(self):self.assertTrue(all(w.pause_refs==('source:pause',) for w in self.make().windows))
    def test_zero_pcm_hash(self):
        for w in self.make().windows:self.assertEqual(w.zero_pcm_sha256,hashlib.sha256(b'\0'*((w.end_sample-w.start_sample)*2)).hexdigest())
    def test_pause_starts_after_provider_samples(self):self.assertEqual(self.make().windows[0].start_sample,self.line.segments[0].provider_end_sample)
    def test_no_caption_on_pause(self):self.assertTrue(all(c.cues[-1].end_sample<=t.provider_samples for c,t in zip(self.c,self.t)))
    def test_pause_is_half_open(self):
        p=self.make();w=p.windows[0];self.assertEqual(p.at_sample(w.start_sample),(w,));self.assertEqual(p.at_sample(w.end_sample),())
    def test_seek_replay(self):
        p=self.make();samples=(0,60000,p.windows[0].start_sample,p.windows[0].end_sample)
        self.assertEqual({s:p.at_sample(s) for s in samples},{s:p.at_sample(s) for s in samples[::-1]})
    def test_changed_waveform_rejected(self):
        raw=bytearray(self.wav);raw[-1]=1
        with self.assertRaisesRegex(AudioError,'MEDIA_CHANGED'):self.make(wav=bytes(raw))
    def test_segment_pause_tamper_rejected(self):
        asset=self.a[0];raw=bytearray(asset.wav_bytes);raw[-1]=1;bad=replace(asset,wav_bytes=bytes(raw))
        with self.assertRaisesRegex(AudioError,'ASSET_'):self.make(assets=(bad,self.a[1]))
    def test_fake_count_rejected(self):
        with self.assertRaisesRegex(AudioError,'PAUSE_MISMATCH'):self.make(assets=(replace(self.a[0],requested_pause_samples=1),self.a[1]))
    def test_stale_caption_rejected(self):
        with self.assertRaisesRegex(AudioError,'CAPTION_OVER'):self.make(captions=(replace(self.c[0],alignment_fingerprint=fingerprint('old')),self.c[1]))
    def test_stale_request_rejected(self):
        asset=replace(self.a[0],request=replace(self.a[0].request,plan_fingerprint=fingerprint('old')))
        with self.assertRaisesRegex(AudioError,'STALE'):self.make(assets=(asset,self.a[1]))
    def test_missing_asset_rejected(self):
        with self.assertRaisesRegex(AudioError,'COVERAGE'):self.make(assets=self.a[:1])
    def test_missing_caption_rejected(self):
        with self.assertRaisesRegex(AudioError,'CAPTION_COVERAGE'):self.make(captions=self.c[:1])
    def test_unmeasured_rejected(self):
        with self.assertRaisesRegex(AudioError,'MEASURED'):self.make(require_measured=True)
    def test_zero_requested_pause_does_not_invent_window(self):
        p,a,t,line,wav=timeline_fixture(pause=0)
        self.assertEqual(synchronize_pauses(line,wav,a,t,require_measured=False).windows,())
    def test_actual_samples_not_float_ms_accumulation(self):
        _,pcm=validate_wav(self.wav,self.a[0].request.settings.format)
        self.assertEqual(len(pcm)//2,self.line.total_samples);self.assertEqual(self.make().timeline_fingerprint,self.line.fingerprint())
