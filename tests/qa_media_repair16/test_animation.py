from media_helpers import *
class AnimationTests(Base):
 def test_timing_and_motion_fixed(self):
  c=self.context(9);b,w=c.preview();r=read_request(c.task,b);result=eval_animation(r,c.root,c.dp.qa,as_of=NOW,**ah.options(r,c.dp.qa));self.assertEqual(result.temporal.status,'CHECKS_PASSED');self.assertEqual(result.motion.status,'CHECKS_PASSED')
 def test_values_unchanged(self):
  c=self.context(9);r=read_request(c.task,c.preview()[0]);self.assertEqual([[k.value for k in t.keyframes] for t in r.tracks],[[k.value for k in t.keyframes] for t in c.bad.tracks])
 def test_no_new_semantics(self):
  c=self.context(9);r=read_request(c.task,c.preview()[0]);self.assertEqual(r.objects,c.bad.objects);self.assertEqual(r.cues,c.bad.cues);self.assertEqual(r.source,c.bad.source)
 def test_unselected_tracks_unchanged(self):
  c=self.context(9);r=read_request(c.task,c.preview()[0]);self.assertEqual(r.tracks[1:],c.bad.tracks[1:])
 def test_integer_affine_key_clock(self):
  c=self.context(9);t=c.bad.tracks[0];r=replace(c.bad,tracks=(replace(t,keyframes=(t.keyframes[0],Keyframe(50,120000),t.keyframes[1])),)+c.bad.tracks[1:]);a=read_request(c.task,c.preview(r)[0]);self.assertEqual(a.tracks[0].keyframes[1].time_ms,1000)
 def test_fractional_key_clock_escalates(self):
  c=self.context(9);t=c.bad.tracks[0];r=replace(c.bad,tracks=(replace(t,keyframes=(t.keyframes[0],Keyframe(1,50000),Keyframe(3,200000))),)+c.bad.tracks[1:]);self.assertError('MEDIA_REPAIR_NONINTEGRAL_KEY_CLOCK',c.preview,r)
 def test_cubic_not_guessed(self):
  c=self.context(9);r=replace(c.bad,tracks=(replace(c.bad.tracks[0],interpolation='cubic_bezier'),)+c.bad.tracks[1:]);self.assertError('MEDIA_REPAIR_UNSUPPORTED_EASING',c.preview,r)
 def test_spring_not_guessed(self):
  c=self.context(9);r=replace(c.bad,tracks=(replace(c.bad.tracks[0],interpolation='spring'),)+c.bad.tracks[1:]);self.assertError('MEDIA_REPAIR_UNSUPPORTED_EASING',c.preview,r)
 def test_cues_not_silently_moved(self):
  c=self.context(9);r=replace(c.bad,cues=(replace(c.bad.cues[0],end_ms=2500),));self.assertError('MEDIA_REPAIR_ANIMATION_SCOPE',c.preview,r)
 def test_lifetimes_not_extended(self):
  c=self.context(9);r=replace(c.bad,objects=(replace(c.bad.objects[0],end_ms=2500),));self.assertError('MEDIA_REPAIR_ANIMATION_SCOPE',c.preview,r)
 def test_track_identity_not_rewritten(self):
  c=self.context(9);r=replace(c.bad,tracks=(replace(c.bad.tracks[0],semantic_id='backwards'),)+c.bad.tracks[1:]);self.assertError('MEDIA_REPAIR_TRACK_IDENTITY',c.preview,r)
 def test_missing_essential_track(self):
  c=self.context(9);self.assertError('MEDIA_REPAIR_TRACK_SCOPE',c.preview,replace(c.bad,tracks=c.bad.tracks[:1]))
 def test_bad_endpoint_not_repaired_by_deleting_it(self):
  c=self.context(9);t=c.bad.tracks[0];r=replace(c.bad,tracks=(replace(t,keyframes=(t.keyframes[0],Keyframe(100,-200000))),)+c.bad.tracks[1:]);self.assertError('MEDIA_REPAIR_ANI_POSTCHECK_BLOCKED',c.preview,r)
 def test_reversals_not_removed(self):
  c=self.context(9);t=c.bad.tracks[0];r=replace(c.bad,tracks=(replace(t,keyframes=(t.keyframes[0],Keyframe(50,250000),t.keyframes[1])),)+c.bad.tracks[1:]);self.assertError('MEDIA_REPAIR_ANI_POSTCHECK_BLOCKED',c.preview,r)
 def test_late_window_rejected(self):
  c=self.context(9);p=replace(c.dp,windows=(TrackWindow('move-x',0,5000),));self.assertError('MEDIA_REPAIR_ANI_POSTCHECK_BLOCKED',c.preview,p=p)
 def test_fast_window_not_approved_by_metadata(self):
  c=self.context(9);p=replace(c.dp,windows=(TrackWindow('move-x',0,100),));self.assertError('MEDIA_REPAIR_ANI_POSTCHECK_BLOCKED',c.preview,p=p)
 def test_original_immutable(self):
  c=self.context(9);c.preview();self.assertEqual((c.root/c.target.path).read_bytes(),c.original[c.target.path])
 def test_deterministic(self):
  c=self.context(9);self.assertEqual(c.preview(),c.preview())
 def test_full_media_unverified(self):
  c=self.context(9);w=c.preview()[1];self.assertFalse(w['actual_audio_sync_verified']);self.assertFalse(w['actual_playback_verified'])
