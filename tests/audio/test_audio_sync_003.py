from dataclasses import replace
from fractions import Fraction
import unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.scene_sync import *
from bie.audio.pcm_audio import validate_wav
from tests.audio.sync_test_support import fixture,timeline_fixture

class Scenes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.p,cls.a,cls.t,cls.line,cls.wav=timeline_fixture(values=('Alpha beta gamma.','Delta epsilon zeta.'),pause=250)
    def test_complete_segment_coverage(self):self.assertEqual(len(self.line.segments),2);self.assertEqual(len(self.line.scenes),2)
    def test_actual_pcm_concatenation(self):
        _,pcm=validate_wav(self.wav,self.a[0].request.settings.format)
        self.assertEqual(pcm,b''.join(validate_wav(a.wav_bytes,a.request.settings.format)[1] for a in self.a))
    def test_no_pause_loss(self):self.assertEqual(self.line.total_samples,sum(a.info.samples_per_channel for a in self.a))
    def test_shared_frame_boundaries(self):self.assertEqual(self.line.scenes[0].end_frame,self.line.scenes[1].start_frame)
    def test_integer_fps(self):self.assertEqual(FrameRate(25).at_or_after(22050,22050),25)
    def test_rational_fps(self):self.assertEqual(FrameRate(30000,1001).at_or_after(22050,22050),30)
    def test_fraction_boundary_never_early(self):
        fps=FrameRate(30000,1001)
        for sample in (0,1,999,22050,726123):
            frame=fps.at_or_after(sample,22050);self.assertGreaterEqual(Fraction(frame*1001,30000),Fraction(sample,22050))
            if frame:self.assertLess(Fraction((frame-1)*1001,30000),Fraction(sample,22050))
    def test_zero_fps_rejected(self):
        with self.assertRaises(AudioError):FrameRate(0)
    def test_nonreduced_fraction_rejected(self):
        with self.assertRaises(AudioError):FrameRate(60,2)
    def test_float_fps_rejected(self):
        with self.assertRaises(AudioError):FrameRate(29.97)
    def test_unknown_scene_budget(self):
        with self.assertRaisesRegex(AudioError,'UNKNOWN_SCENE'):assemble_scenes(self.p,self.a,self.t,budgets=(SceneBudget('absent'),),require_measured=False)
    def test_duplicate_scene_budget(self):
        with self.assertRaisesRegex(AudioError,'DUPLICATE'):assemble_scenes(self.p,self.a,self.t,budgets=(SceneBudget('scene:0'),SceneBudget('scene:0')),require_measured=False)
    def test_audio_cannot_be_speeded_to_fit(self):
        with self.assertRaisesRegex(AudioError,'EXTENSION_REQUIRED'):assemble_scenes(self.p,self.a,self.t,budgets=(SceneBudget('scene:0',1,2),),require_measured=False)
    def test_explicit_hold_required(self):
        with self.assertRaisesRegex(AudioError,'HOLD_REQUIRED'):assemble_scenes(self.p,self.a,self.t,budgets=(SceneBudget('scene:0',200,300),),require_measured=False)
    def test_assets_reordered_rejected(self):
        with self.assertRaisesRegex(AudioError,'REQUEST_MISMATCH'):assemble_scenes(self.p,self.a[::-1],self.t[::-1],require_measured=False)
    def test_assets_missing_rejected(self):
        with self.assertRaisesRegex(AudioError,'COVERAGE'):assemble_scenes(self.p,self.a[:1],self.t[:1],require_measured=False)
    def test_alignment_stale_rejected(self):
        t=(replace(self.t[0],segment_fingerprint=fingerprint('changed')),self.t[1])
        with self.assertRaisesRegex(AudioError,'STALE'):assemble_scenes(self.p,self.a,t,require_measured=False)
    def test_unmeasured_default_rejected(self):
        with self.assertRaisesRegex(AudioError,'MEASURED'):assemble_scenes(self.p,self.a,self.t)
    def test_timeline_media_hash(self):self.assertIs(validate_timeline_media(self.line,self.wav),self.line)
    def test_media_edit_rejected(self):
        b=bytearray(self.wav);b[50]^=1
        with self.assertRaisesRegex(AudioError,'MEDIA_CHANGED'):validate_timeline_media(self.line,bytes(b))
    def test_repeated_scene_noncontiguous_rejected(self):
        p,a,t=fixture(('One two.','Three four.','Five six.'),scenes=('A','B','C'))
        p=replace(p,segments=p.segments[:2]+(replace(p.segments[2],scene_id='A'),))
        a=tuple(replace(x,request=replace(x.request,segment=s,plan_fingerprint=p.fingerprint())) for s,x in zip(p.segments,a))
        t=tuple(replace(x,request_fingerprint=y.request.fingerprint(),segment_fingerprint=y.request.segment.fingerprint()) for x,y in zip(t,a))
        with self.assertRaisesRegex(AudioError,'NONCONTIGUOUS'):assemble_scenes(p,a,t,require_measured=False)
    def test_reverse_seek_same_scene(self):
        frames=range(self.line.duration_frames)
        forward={f:self.line.scene_at_frame(f) for f in frames};backward={f:self.line.scene_at_frame(f) for f in reversed(frames)}
        self.assertEqual(forward,backward);self.assertIsNone(self.line.scene_at_frame(self.line.duration_frames))
