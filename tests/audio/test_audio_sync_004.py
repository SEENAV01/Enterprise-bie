from dataclasses import replace
from fractions import Fraction
import unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.animation_sync import *
from tests.audio.sync_test_support import timeline_fixture

class AnimationSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p,cls.a,cls.t,cls.line,cls.wav=timeline_fixture(values=('Alpha beta gamma.','Delta epsilon zeta.'),scenes=('scene:A','scene:A'),pause=400)
    def binding(self,**kw):
        base=AnimationBinding('anim1','target1','reveal',self.p.segments[0].segment_id,0,self.p.segments[0].segment_id,2,
            self.line.fingerprint(),('source:p1',),('reason:teaching',))
        return replace(base,**kw)
    def make(self,b=None):return synchronize_animations(self.line,self.t,(b or self.binding(),),require_measured=False)
    def test_exact_word_start(self):self.assertEqual(self.make().tracks[0].start_sample,self.t[0].words[0].start_sample)
    def test_exact_word_end(self):self.assertEqual(self.make().tracks[0].end_sample,self.t[0].words[-1].end_sample)
    def test_frame_bounds_from_same_clock(self):
        t=self.make().tracks[0];self.assertEqual(t.start_frame,self.line.fps.at_or_after(t.start_sample,22050))
    def test_stale_timeline_rejected(self):
        with self.assertRaisesRegex(AudioError,'STALE_TIMELINE'):self.make(self.binding(timeline_fingerprint=fingerprint('old')))
    def test_stale_alignment_rejected(self):
        with self.assertRaisesRegex(AudioError,'STALE_ALIGNMENT'):synchronize_animations(self.line,(replace(self.t[0],event_fingerprint=fingerprint('changed')),self.t[1]),(self.binding(),),require_measured=False)
    def test_unknown_segment_rejected(self):
        with self.assertRaisesRegex(AudioError,'UNKNOWN_SEGMENT'):self.make(self.binding(start_segment_id='unknown'))
    def test_unknown_word_rejected(self):
        with self.assertRaisesRegex(AudioError,'UNKNOWN_WORD'):self.make(self.binding(last_word=100))
    def test_reversed_words_rejected(self):
        with self.assertRaisesRegex(AudioError,'WORD_ORDER'):self.make(self.binding(first_word=2,last_word=0))
    def test_reversed_segment_order_rejected(self):
        with self.assertRaisesRegex(AudioError,'SCENE_ORDER'):self.make(self.binding(start_segment_id=self.p.segments[1].segment_id))
    def test_required_references(self):
        with self.assertRaises(AudioError):self.binding(reasoning_refs=())
    def test_unbound_source_rejected(self):
        with self.assertRaisesRegex(AudioError,'UNBOUND_SOURCE'):self.make(self.binding(source_refs=('source:absent',)))
    def test_negative_anticipation_outside_scene_rejected(self):
        with self.assertRaisesRegex(AudioError,'OUTSIDE_SCENE'):self.make(self.binding(start_offset_ms=-100))
    def test_authorized_hold_offset_changes_end(self):
        b=self.binding(end_offset_ms=100);self.assertEqual(self.make(b).tracks[0].end_sample,self.t[0].words[-1].end_sample+2205)
    def test_under_sampled_rejected(self):
        with self.assertRaisesRegex(AudioError,'UNDERSAMPLED'):self.make(self.binding(minimum_frames=200))
    def test_duplicate_binding_rejected(self):
        with self.assertRaisesRegex(AudioError,'DUPLICATE'):synchronize_animations(self.line,self.t,(self.binding(),self.binding()),require_measured=False)
    def test_conflicting_writer_rejected(self):
        with self.assertRaisesRegex(AudioError,'WRITER_COLLISION'):synchronize_animations(self.line,self.t,(self.binding(),self.binding(binding_id='a2')),require_measured=False)
    def test_unknown_predecessor_rejected(self):
        with self.assertRaisesRegex(AudioError,'DEPENDENCY_ORDER'):self.make(self.binding(after=('absent',)))
    def test_self_dependency_rejected(self):
        with self.assertRaisesRegex(AudioError,'DEPENDENCY_ORDER'):self.make(self.binding(after=('anim1',)))
    def test_cross_pause_requires_policy(self):
        with self.assertRaisesRegex(AudioError,'PEDAGOGICAL_PAUSE'):self.make(self.binding(end_segment_id=self.p.segments[1].segment_id))
    def test_hold_progress_is_frozen(self):
        sync=self.make(self.binding(end_segment_id=self.p.segments[1].segment_id,pause_mode='hold'));track=sync.tracks[0];a,b=track.holds[0]
        self.assertEqual(track.progress_at_sample(a),track.progress_at_sample((a+b)//2));self.assertEqual(track.progress_at_sample(a),track.progress_at_sample(b))
    def test_continue_is_explicit(self):
        track=self.make(self.binding(end_segment_id=self.p.segments[1].segment_id,pause_mode='continue')).tracks[0]
        self.assertFalse(track.holds);a=self.line.segments[0].provider_end_sample;b=self.line.segments[0].end_sample
        self.assertLess(track.progress_at_sample(a),track.progress_at_sample(b))
    def test_keyframes_encode_holds(self):
        track=self.make(self.binding(end_segment_id=self.p.segments[1].segment_id,pause_mode='hold')).tracks[0];points=track.keyframes()
        self.assertEqual(len(points),4);self.assertEqual(points[1][1:],points[2][1:]);self.assertEqual(points[-1][1:],(1,1))
    def test_reverse_seek_independent(self):
        sync=self.make();frames=list(range(self.line.duration_frames));a={f:sync.state_at_frame(self.line,f) for f in frames};b={f:sync.state_at_frame(self.line,f) for f in frames[::-1]};self.assertEqual(a,b)
    def test_measured_default_rejects_fixture(self):
        with self.assertRaisesRegex(AudioError,'MEASURED'):synchronize_animations(self.line,self.t,(self.binding(),))
    def test_empty_tracks_are_valid_no_fake_animation(self):self.assertEqual(synchronize_animations(self.line,self.t,(),require_measured=False).tracks,())
