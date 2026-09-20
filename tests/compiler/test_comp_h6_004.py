from copy import deepcopy
from hashlib import sha256
import unittest
from bie.compiler.frame_runtime_contract import plan_frame_runtime,CompilerQAError
from bie.compiler.narration_consumer import emit_narration,cue_schedule
from bie.compiler.hardened_scene_compile import compile_h3_scene
from tests.compiler.h6_test_support import *

class NarrationScheduleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p,cls.a=narration_scene();cls.r=compile_h3_scene(cls.p,target=BIG);cls.plan=plan_frame_runtime(cls.r.effective_document,BIG);cls.data=execute(cls.r)
    def reject(self,change,code):
        p=deepcopy(self.p);change(p)
        with self.assertRaisesRegex(CompilerQAError,code):plan_frame_runtime(p,BIG)
    def test_sequence_owns_schedule(self):
        s=emit_narration(self.plan).content;self.assertIn('from={c.start_frame}',s);self.assertIn('durationInFrames={c.end_frame-c.start_frame}',s);self.assertNotIn('Audio from=',s)
    def test_audio_and_caption_active_same_frames(self):
        for row in self.data['trees']:
            voices=[n for n in nodes(row['tree']) if n.get('props',{}).get('data-bie-test-audio')]
            self.assertEqual(len(voices),len(row['state']['active_cue_ids']))
            if voices:self.assertNotEqual(row['state']['caption_text'],'')
    def test_source_seek_relative_to_sequence_start(self):
        for row in self.data['trees']:
            c=next((c for c in self.plan['narration'] if c['start_frame']<=row['frame']<c['end_frame']),None)
            if c:
                a=next(n['props'] for n in nodes(row['tree']) if n.get('props',{}).get('data-bie-test-audio'))
                self.assertEqual(a['data-source-frame'],c['trim_before_frames']+row['frame']-c['start_frame'])
    def test_no_ghost_caption_between_cues(self):
        for f in [0,5,24,29]:self.assertEqual(self.data['trees'][f]['state']['caption_text'],'')
    def test_volume_and_trim_preserved(self):
        for row in self.data['trees']:
            for n in nodes(row['tree']):
                if n.get('props',{}).get('data-bie-test-audio'):self.assertEqual(n['props']['data-volume'],.5);self.assertEqual(n['props']['data-trim-after'],18)
    def test_harness_does_not_claim_audio_playback(self):self.assertFalse(self.data['audio_played']);self.assertFalse(self.data['real_remotion'])
    def test_fractional_ms_quantization_recorded(self):
        p=deepcopy(self.p);p['narration_cues'][0]['start_ms']=251;r=cue_schedule(plan_frame_runtime(p,BIG))
        self.assertGreater(r['entries'][0]['start_drift_ms'],0);self.assertLess(r['entries'][0]['start_drift_ms'],1000/BIG.fps)
    def test_revision_mismatch_rejected(self):self.reject(lambda p:p['narration_cues'][0].update(narration_revision=2),'STALE')
    def test_transcript_tamper_rejected(self):self.reject(lambda p:p['metadata']['compiler_h6']['narration_texts']['text:c1'].update(text='wrong words'),'TRANSCRIPT_HASH')
    def test_orphan_segment_rejected(self):
        self.reject(lambda p:p['metadata']['compiler_h6']['audio_segments'].append({**p['metadata']['compiler_h6']['audio_segments'][0],'cue_id':'orphan'}),'COVERAGE')
    def test_segment_duplicate_rejected(self):self.reject(lambda p:p['metadata']['compiler_h6']['audio_segments'].append(p['metadata']['compiler_h6']['audio_segments'][0]),'SEGMENT_DUPLICATE')
    def test_narration_overlap_rejected(self):self.reject(lambda p:p['narration_cues'][1].update(start_ms=750),'OVERLAP')
    def test_zero_frame_cue_rejected(self):self.reject(lambda p:p['narration_cues'][0].update(start_ms=251,end_ms=252),'COLLAPSED')
    def test_audio_too_short_rejected(self):self.reject(lambda p:p['metadata']['compiler_h6']['audio_assets'][0].update(frame_count=100),'TOO_SHORT')
    def test_nonpositive_gain_rejected(self):self.reject(lambda p:p['metadata']['compiler_h6']['audio_segments'][0].update(volume=0),'FRAME_RUNTIME_NUMBER')
    def test_remote_or_escape_asset_path_rejected(self):
        for path in ['../x.wav','https://example.com/a.wav','/absolute.wav','narration/%2e%2e.wav']:
            with self.subTest(path=path):self.reject(lambda p:p['metadata']['compiler_h6']['audio_assets'][0].update(public_path=path),'ASSET_PATH')
    def test_no_caption_target_invention(self):self.reject(lambda p:p['metadata']['compiler_h6'].update(caption_target_id='missing'),'CAPTION_TARGET')
    def test_caption_initial_content_bound(self):self.reject(lambda p:p['elements'][1]['props'].update(text='different'),'CAPTION_INITIAL')
    def test_caption_cannot_compete_with_state_binding(self):
        self.reject(lambda p:p['state_bindings'].append({**p['state_bindings'][0],'target_id':'captions','binding_id':'caption-state'}),'TEXT_INITIAL_MISMATCH|CAPTION_CONFLICT')
    def test_no_claimed_speech_or_render_acceptance(self):
        s=cue_schedule(self.plan);self.assertFalse(s['accepted']);self.assertEqual(s['real_remotion_render'],'NOT_RUN');self.assertEqual(s['entries'][0]['speech_alignment'],'NOT_VERIFIED')
    def test_asset_trim_cannot_read_past_end(self):self.reject(lambda p:p['metadata']['compiler_h6']['audio_segments'][0].update(trim_before_frames=100),'TOO_SHORT')
    def test_no_unrequested_audio_for_state_only(self):self.assertIsNone(emit_narration(plan_frame_runtime(state_scene(),BIG)))

if __name__=='__main__':unittest.main()
