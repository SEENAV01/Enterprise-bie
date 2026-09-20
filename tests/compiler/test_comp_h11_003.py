import unittest
from copy import deepcopy
from dataclasses import replace
from bie.compiler.media_presentation import video_schedule,source_video_frame,media_presentations
from bie.compiler.visual_assets import _video_metadata
from bie.compiler.media_compiler import compile_image_or_video_element
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.frame_layout import iter_frame_layers
from tests.compiler.h11_test_support import scene,asset,T

class ExactVideoSchedule(unittest.TestCase):
    def plan(self,p=None):
        p=p or scene('trim-video');return video_schedule(p['elements'][0],asset(p),T,p['duration_ms'])
    def bad(self,change,code):
        p=scene('trim-video');change(p);self.assertRaisesRegex(ValueError,code,self.plan,p)
    def test_exact_window_in_composition_frames(self):
        p=self.plan();self.assertEqual((p['display_start_frame'],p['display_end_frame_exclusive']),(6,18));self.assertEqual((p['trim_before_composition_frames'],p['trim_after_composition_frames']),(12,24))
    def test_every_frame_source_reference(self):
        p=self.plan();self.assertEqual([source_video_frame(p,f) for f in range(24)],[None]*6+list(range(12,24))+[None]*6)
    def test_reverse_seek_reference_matches(self):
        p=self.plan();self.assertEqual([source_video_frame(p,f) for f in reversed(range(24))][::-1],[source_video_frame(p,f) for f in range(24)])
    def test_source_rate_differs_from_composition_rate(self):
        p=scene('trim-video');asset(p)['media'].update(fps_num=24,frame_count=72);self.assertEqual([source_video_frame(self.plan(p),f) for f in range(6,18)],list(range(24,48,2)))
    def test_non_aligned_trim_cannot_round_silently(self):self.bad(lambda p:p['elements'][0]['props'].update(trim_start_ms=1),'NOT_FRAME_ALIGNED')
    def test_non_aligned_display_time_cannot_round_silently(self):self.bad(lambda p:p['elements'][0]['props'].update(timeline_start_ms=1),'NOT_FRAME_ALIGNED')
    def test_reversed_trim_is_rejected(self):self.bad(lambda p:p['elements'][0]['props'].update(trim_start_ms=2000,trim_end_ms=1000),'TRIM_RANGE')
    def test_trim_beyond_source_rejected(self):self.bad(lambda p:p['elements'][0]['props'].update(trim_end_ms=4000),'TRIM_RANGE')
    def test_clip_beyond_scene_rejected(self):self.bad(lambda p:p['elements'][0]['props'].update(timeline_start_ms=1500),'EXCEEDS_SCENE')
    def test_unspecified_audio_handling_rejected(self):self.bad(lambda p:p['elements'][0]['props'].pop('audio_policy'),'AUDIO_POLICY_REQUIRED')
    def test_muting_requires_bound_reason(self):self.bad(lambda p:p['elements'][0]['props'].update(audio_policy='muted'),'MUTE_REASON_UNBOUND')
    def test_explicit_muting_retained(self):
        p=scene('trim-video');p['elements'][0]['props'].update(audio_policy='muted',audio_reason_ref='reasoning:h11');b=media_presentations(p,T)['rows'][0];s=compile_image_or_video_element(p['elements'][0],presentation=b).source_text;self.assertIn('muted={true}',s)
    def test_unknown_loop_does_not_get_ignored(self):self.bad(lambda p:p['elements'][0]['props'].update(loop=True),'PROPERTY_UNCONSUMED')
    def test_speed_change_does_not_get_ignored(self):self.bad(lambda p:p['elements'][0]['props'].update(playbackRate=2),'PROPERTY_UNCONSUMED')
    def test_preserve_mode_does_not_silently_mute(self):
        p=scene('trim-video');b=media_presentations(p,T)['rows'][0];s=compile_image_or_video_element(p['elements'][0],presentation=b).source_text;self.assertIn('muted={false}',s);self.assertIn('trimBefore={12}',s);self.assertIn('trimAfter={24}',s);self.assertIn('onError={() => "fail"}',s)
    def test_direct_trim_cannot_be_ignored(self):self.assertRaisesRegex(ValueError,'TRIM_BINDING_REQUIRED',compile_image_or_video_element,scene('trim-video')['elements'][0])
    def test_video_dependency_is_bound_to_existing_pin(self):
        c=compile_h3_scene(scene('trim-video'),target=T);self.assertTrue(c.receipt.source_gate_passed);s=next(f.content for f in c.codegen.files if f.path=='package.json');self.assertIn('"@remotion/media": "4.0.506"',s)
    def test_layout_uses_the_same_video_lifecycle(self):
        rows=list(iter_frame_layers(scene('trim-video'),T));self.assertEqual([r[0]['visible_conservative'] for r in rows],[False]*6+[True]*12+[False]*6)
    def test_open_end_uses_actual_verified_duration(self):
        p=scene('trim-video');p['duration_ms']=3000;p['elements'][0]['props'].update(trim_end_ms=None,timeline_start_ms=0);self.assertEqual(self.plan(p)['trim_after_composition_frames'],36)
    def test_fractional_fps_duration_must_be_declared(self):
        p=scene('trim-video');p['elements'][0]['props']['trim_end_ms']=None;asset(p)['media'].update(fps_num=25,frame_count=31);self.assertRaisesRegex(ValueError,'END_NOT_FRAME_ALIGNED',self.plan,p)
    def test_temporal_alias_not_accepted_by_metadata_parser(self):
        s={'codec_type':'video','codec_name':'h264','pix_fmt':'yuv420p','sample_aspect_ratio':'1:1','avg_frame_rate':'12/1','r_frame_rate':'12/1','time_base':'1/12','width':96,'height':64,'duration_ts':3,'nb_frames':'3'}
        self.assertRaisesRegex(ValueError,'CFR_ZERO_ORIGIN',_video_metadata,[s],[{'best_effort_timestamp':i} for i in [0,1,3]])
    def test_rotated_stream_rejected(self):
        s={'codec_type':'video','codec_name':'h264','pix_fmt':'yuv420p','tags':{'rotate':'90'}};self.assertRaisesRegex(ValueError,'ROTATION',_video_metadata,[s],[])
    def test_extra_stream_rejected(self):self.assertRaisesRegex(ValueError,'STREAMS_UNSUPPORTED',_video_metadata,[{'codec_type':'subtitle'}],[])

    def test_external_caption_reference_not_treated_as_rendered(self):
        self.bad(lambda p:p['elements'][0]['props'].update(captions_ref='unresolved'), 'CAPTIONS_BINDING_REQUIRED')
    def test_implicit_embedded_audio_mix_rejected(self):
        p=scene('trim-video');asset(p)['media']['audio_streams']=1;p['narration_cues']=[{'cue_id':'test'}]
        self.assertRaisesRegex(ValueError,'AUDIO_MIX_POLICY_REQUIRED',media_presentations,p,T)
