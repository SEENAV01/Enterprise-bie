import unittest,json
from dataclasses import replace
import numpy as np
from bie.audio.common import AudioError,fingerprint
from bie.audio.qa_missing_audio import missing_audio_qa
from bie.audio.qa_signal_replay import replay_mix
from .qa_test_support import native,reseal,change_pcm

class MissingAudioQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s,cls.m,cls.stems=native()
    def test_actual_complete_narration(self):self.assertEqual(missing_audio_qa(self.m,self.s).status,'PASS')
    def test_exact_segment_coverage(self):self.assertEqual(json.loads(missing_audio_qa(self.m,self.s).metrics_json)['source_segment_count'],len(self.s.plan.segments))
    def test_dry_sample_replay(self):self.assertEqual(replay_mix(self.m,self.s)['maximum_pcm16_sample_difference'],0)
    def test_real_sfx_sample_replay(self):
        s,m,w=native(True);self.assertTrue(replay_mix(m,s,w)['matched'])
    def test_missing_stem_bytes_block(self):
        s,m,w=native(True)
        with self.assertRaisesRegex(AudioError,'STEM_BYTES_MISSING'):missing_audio_qa(m,s)
    def test_wrong_stem_bytes_block(self):
        s,m,w=native(True)
        with self.assertRaises(AudioError):missing_audio_qa(m,s,(self.m.wav_bytes,))
    def test_source_audio_tamper_block(self):
        with self.assertRaises(AudioError):missing_audio_qa(self.m,replace(self.s,wav_bytes=self.s.wav_bytes[:-2]))
    def test_source_segment_loss_block(self):
        with self.assertRaises(AudioError):missing_audio_qa(self.m,replace(self.s,assets=self.s.assets[:-1]))
    def test_source_order_change_block(self):
        with self.assertRaises(AudioError):missing_audio_qa(self.m,replace(self.s,assets=tuple(reversed(self.s.assets))))
    def test_output_segments_loss_block(self):
        c=self.m.clock();c['segments']=c['segments'][:-1]
        with self.assertRaises(AudioError):missing_audio_qa(reseal(self.m,c),self.s)
    def test_output_zero_segment_detected(self):
        def zero(a,c):
            p=c['segments'][0];a[p['start_sample']:p['provider_end_sample']]=0
        bad=change_pcm(self.m,zero);r=missing_audio_qa(bad,self.s)
        self.assertEqual(r.status,'FAIL');self.assertIn('SEGMENT_SILENT',[f.code for f in r.findings])
    def test_nonzero_background_cannot_replace_speech(self):
        def wrong(a,c):
            p=c['segments'][0];n=p['provider_end_sample']-p['start_sample'];a[p['start_sample']:p['provider_end_sample'],0]=.001*np.sin(2*np.pi*400*np.arange(n)/c['sample_rate'])
        bad=change_pcm(self.m,wrong);r=missing_audio_qa(bad,self.s);self.assertEqual(r.status,'FAIL');self.assertIn('MIX_REPLAY_MISMATCH',[f.code for f in r.findings])
    def test_sample_change_rehashed_still_fails_replay(self):
        bad=change_pcm(self.m,lambda a,c:a.__setitem__((10000,0),a[10000,0]+.002));self.assertFalse(replay_mix(bad,self.s)['matched'])
    def test_huge_repeat_rejected_before_allocation(self):
        s,m,w=native(True);r=m.receipt();r['sfx']['stems'][0]['repeat']=10**12
        with self.assertRaises(AudioError):replay_mix(reseal(m,r=r),s,w)
    def test_bool_start_rejected(self):
        s,m,w=native(True);r=m.receipt();r['sfx']['stems'][0]['start_sample']=True
        with self.assertRaises(AudioError):replay_mix(reseal(m,r=r),s,w)
    def test_nonnarration_bus_wrong_role_rejected(self):
        s,m,w=native(True);r=m.receipt();r['sfx']['stems'][0]['role']='music'
        with self.assertRaises(AudioError):replay_mix(reseal(m,r=r),s,w)
    def test_semantic_acceptance_not_claimed(self):self.assertFalse(json.loads(missing_audio_qa(self.m,self.s).metrics_json)['semantic_transcript_verified'])
    def test_no_input_mutation(self):
        before=self.m.receipt_json,fingerprint(self.s.receipt());missing_audio_qa(self.m,self.s);self.assertEqual(before,(self.m.receipt_json,fingerprint(self.s.receipt())))
