import unittest,json
from dataclasses import replace
from bie.audio.common import AudioError,fingerprint
from bie.audio.qa_sync import sync_qa
from bie.audio.mix_clock import state_at_sample
from .qa_test_support import native,reseal

class SyncQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s,cls.m,_=native()
    def test_real_engine_clock_checked_not_acoustic_pass(self):self.assertEqual(sync_qa(self.m,self.s).status,'REVIEW')
    def test_exact_source_replay(self):self.assertTrue(json.loads(sync_qa(self.m,self.s).metrics_json)['forward_reverse_equal'])
    def test_boundary_positions_nonempty(self):self.assertGreater(json.loads(sync_qa(self.m,self.s).metrics_json)['boundary_sample_positions'],20)
    def test_shifted_word_rehashed_rejected(self):
        c=self.m.clock();c['words'][0]['start_sample']+=1
        with self.assertRaises(AudioError):sync_qa(reseal(self.m,c),self.s)
    def test_changed_caption_rehashed_rejected(self):
        c=self.m.clock();c['captions'][0]['lines'][0]='changed'
        with self.assertRaises(AudioError):sync_qa(reseal(self.m,c),self.s)
    def test_missing_caption_rejected(self):
        c=self.m.clock();c['captions']=[]
        with self.assertRaises(AudioError):sync_qa(reseal(self.m,c),self.s)
    def test_scene_frame_change_rejected(self):
        c=self.m.clock();c['scenes'][0]['end_frame']+=1
        with self.assertRaises(AudioError):sync_qa(reseal(self.m,c),self.s)
    def test_animation_progress_change_rejected(self):
        c=self.m.clock();c['animations'][0]['keyframes'][0][1]=1
        with self.assertRaises(AudioError):sync_qa(reseal(self.m,c),self.s)
    def test_pause_missing_rejected(self):
        c=self.m.clock();c['pauses']=[]
        with self.assertRaises(AudioError):sync_qa(reseal(self.m,c),self.s)
    def test_source_alignment_loss_rejected(self):
        with self.assertRaises(AudioError):sync_qa(self.m,replace(self.s,alignments=self.s.alignments[:-1]))
    def test_no_video_success_claim(self):self.assertFalse(json.loads(sync_qa(self.m,self.s).metrics_json)['rendered_video_verified'])
    def test_no_acoustic_success_claim(self):self.assertFalse(json.loads(sync_qa(self.m,self.s).metrics_json)['acoustic_alignment_verified'])
    def test_all_frames_reverse_seek(self):
        frames=range(self.m.clock()['duration_frames']+1);states=[self.m.state_at_frame(f) for f in frames];self.assertEqual(states,list(reversed([self.m.state_at_frame(f) for f in reversed(frames)])))
    def test_half_open_caption_end(self):
        c=self.m.clock();q=c['captions'][0];self.assertNotIn(q['text'],state_at_sample(c,q['end_sample'])['captions'])
    def test_pause_hold_actual_progress(self):
        c=self.m.clock();p=c['pauses'][0]
        self.assertEqual(state_at_sample(c,p['start_sample'])['animations'][0]['progress'],state_at_sample(c,p['end_sample']-1)['animations'][0]['progress'])
    def test_existing_source_unmodified(self):
        before=fingerprint(self.s.receipt());sync_qa(self.m,self.s);self.assertEqual(before,fingerprint(self.s.receipt()))
