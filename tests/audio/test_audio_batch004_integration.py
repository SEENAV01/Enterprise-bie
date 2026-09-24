"""MIX's actual SYNC/audio/clock boundaries, not full application acceptance."""
from dataclasses import asdict, replace
from fractions import Fraction
from pathlib import Path
import hashlib, json, tempfile, threading, unittest
from unittest.mock import patch
import numpy as np
from bie.audio.common import AudioError, fingerprint
from bie.audio.mix_contract import MixBuffer
from bie.audio.mix_meter import FFmpegMeter
from bie.audio.mix_pipeline import MixedAudio, MixPolicy, mix_synchronized, export_mixed_captions
from bie.audio.silence_trim import TrimPolicy
from bie.audio.loudness_normalization import LoudnessPolicy
from bie.audio.peak_control import PeakPolicy
from bie.audio.animation_sync import AnimationBinding, synchronize_animations
from bie.audio.tts_contract import AudioFormat
from .mix_test_support import real_sync, stem, tone


def anchored(sync):
    p, q = sync.timeline.segments[:2]
    b = AnimationBinding('mix:trace','graph:demo','trace',p.segment_id,0,q.segment_id,
                         len(sync.alignments[1].words)-1, sync.timeline.fingerprint(),
                         ('synthetic:audio-fixture:1',), ('synthetic:teaching-intent',),pause_mode='hold')
    return synchronize_animations(sync.timeline, sync.alignments, (b,))


def reseal(result,clock=None,receipt=None):
    c = clock if clock is not None else result.clock()
    r = receipt if receipt is not None else result.receipt()
    r['clock_fingerprint']=fingerprint(c);r.pop('fingerprint',None);r['fingerprint']=fingerprint(r)
    return replace(result,clock_json=json.dumps(c),receipt_json=json.dumps(r))


class MixIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sync=real_sync();cls.meter=FFmpegMeter();cls.animations=anchored(cls.sync)
        cls.result=mix_synchronized(cls.sync,meter=cls.meter,animations=cls.animations)
        cls.pcm=MixBuffer.from_wav(cls.result.wav_bytes,AudioFormat())
    def test_actual_source_to_wav(self):
        self.result.validate();self.assertTrue(self.result.wav_bytes.startswith(b'RIFF'))
        self.assertTrue(self.result.receipt()['final_loudness_target_reached'])
    def test_upstream_not_overwritten(self):
        before=fingerprint(self.sync.receipt());wav=self.sync.wav_bytes
        mix_synchronized(self.sync,meter=self.meter)
        self.assertEqual(fingerprint(self.sync.receipt()),before);self.assertEqual(wav,self.sync.wav_bytes)
    def test_trim_only_exact_zero_unprotected_edges(self):
        c=self.result.clock();x=MixBuffer.from_wav(self.sync.wav_bytes,AudioFormat()).array()
        self.assertGreater(self.sync.timeline.total_samples,c['total_samples'])
        self.assertFalse(np.any(x[:c['source_start_sample']]))
        self.assertFalse(np.any(x[c['source_end_sample']:]))
    def test_unity_clock_no_time_stretch(self):
        c=self.result.clock();self.assertEqual(self.pcm.frames,c['source_end_sample']-c['source_start_sample'])
        self.assertEqual(self.pcm.sample_rate,self.sync.timeline.sample_rate)
        self.assertEqual(self.result.receipt()['peak_control']['latency_samples'],0)
    def test_every_word_and_exact_source_map_preserved(self):
        c=self.result.clock();expected=[]
        for p,a in zip(self.sync.timeline.segments,self.sync.alignments):
            for w in a.words:expected.append((w.spoken,p.start_sample+w.start_sample-c['source_start_sample'],p.start_sample+w.end_sample-c['source_start_sample'],json.loads(json.dumps(asdict(w)))['source']))
        self.assertEqual([(w['spoken'],w['start_sample'],w['end_sample'],w['source']) for w in c['words']],expected)
    def test_captions_not_reworded(self):
        self.assertEqual([c['text'] for c in self.result.clock()['captions']],[c.text for t in self.sync.captions for c in t.cues])
    def test_pause_all_samples_zero(self):
        for p in self.result.clock()['pauses']:
            self.assertFalse(np.any(self.pcm.array()[p['start_sample']:p['end_sample']]))
    def test_pause_duration_not_double_counted(self):
        self.assertEqual([p['end_sample']-p['start_sample'] for p in self.result.clock()['pauses']],
                         [p.end_sample-p.start_sample for p in self.sync.pauses.windows])
    def test_scene_sample_and_frame_coverage(self):
        c=self.result.clock();scenes=c['scenes'];self.assertEqual(scenes[0]['start_sample'],0)
        self.assertEqual(scenes[-1]['end_sample'],c['total_samples']);self.assertEqual(scenes[-1]['end_frame'],c['duration_frames'])
        for a,b in zip(scenes,scenes[1:]):self.assertEqual(a['end_sample'],b['start_sample']);self.assertEqual(a['end_frame'],b['start_frame'])
    def test_animation_keyframe_identity(self):
        c=self.result.clock();shift=c['source_start_sample']
        for src,dst in zip(self.animations.tracks,c['animations']):
            self.assertEqual(dst['keyframes'],[[s-shift,n,d] for s,n,d in src.keyframes()])
            self.assertEqual(dst['binding'],json.loads(json.dumps(asdict(src.binding))))
    def test_animation_state_forward_reverse_uses_trimmed_clock(self):
        c=self.result.clock();indices=list(range(c['duration_frames']+1))
        states=[self.result.state_at_frame(f) for f in indices]
        self.assertEqual(states,list(reversed([self.result.state_at_frame(f) for f in reversed(indices)])))
        for f,state in zip(indices,states):
            source_sample=self.sync.timeline.fps.sample_at(f,c['sample_rate'])+c['source_start_sample']
            self.assertIn('animations',state)
            self.assertAlmostEqual(state['animations'][0]['progress'],float(self.animations.tracks[0].progress_at_sample(source_sample)))
    def test_webvtt_srt_exports(self):
        v=export_mixed_captions(self.result,'vtt');s=export_mixed_captions(self.result,'srt')
        self.assertTrue(v.startswith('WEBVTT'));self.assertIn('-->',s)
        self.assertEqual(v.count('-->'),len(self.result.clock()['captions']))
        with self.assertRaises(AudioError):export_mixed_captions(self.result,'ass')
    def test_final_pcm_meter_binding(self):
        r=self.result.receipt();self.assertEqual(r['peak_control']['after']['pcm_fingerprint'],self.pcm.fingerprint())
        self.assertLessEqual(r['peak_control']['after']['true_peak_dbtp'],r['policy']['peaks']['ceiling_dbtp'])
    def test_music_ducks_and_pause_mutes(self):
        voice=self.sync;bed=stem(tone(frames=voice.timeline.total_samples,amp=.025,hz=180),role='music',asset_id='bed')
        out=mix_synchronized(voice,(bed,),meter=self.meter);r=out.receipt()
        self.assertTrue(r['ducking']['windows']);self.assertEqual(len(r['music']['stems']),1)
        pcm=MixBuffer.from_wav(out.wav_bytes,AudioFormat())
        for p in out.clock()['pauses']:self.assertFalse(np.any(pcm.array()[p['start_sample']:p['end_sample']]))
    def test_sfx_at_requested_sample(self):
        s=stem(tone(frames=800,amp=.02),start_sample=4000,asset_id='cue')
        out=mix_synchronized(self.sync,(s,),meter=self.meter)
        self.assertEqual(out.receipt()['sfx']['stems'][0]['output_start'],4000)
        self.assertNotEqual(out.wav_bytes,self.result.wav_bytes)
    def test_sfx_over_protected_pause_blocked(self):
        p=self.sync.pauses.windows[0];s=stem(tone(frames=800),start_sample=p.start_sample)
        with self.assertRaisesRegex(AudioError,'SFX_OVER_REQUIRED_SILENCE'):mix_synchronized(self.sync,(s,),meter=self.meter)
    def test_explicit_narration_only_pause_may_contain_sfx(self):
        p=self.sync.pauses.windows[0];s=stem(tone(frames=800,amp=.01),start_sample=p.start_sample)
        out=mix_synchronized(self.sync,(s,),policy=MixPolicy(pause_mode='narration_only'),meter=self.meter)
        a=p.start_sample-out.clock()['source_start_sample'];pcm=MixBuffer.from_wav(out.wav_bytes,AudioFormat())
        self.assertTrue(np.any(pcm.array()[a:a+800]));self.assertEqual(out.receipt()['policy']['pause_mode'],'narration_only')
    def test_unity_trim_disabled(self):
        o=mix_synchronized(self.sync,policy=MixPolicy(trim=TrimPolicy(enabled=False)),meter=self.meter)
        self.assertEqual(o.clock()['total_samples'],self.sync.timeline.total_samples)
    def test_hindi_source_and_text_survive(self):
        s=real_sync('hindi');o=mix_synchronized(s,meter=self.meter)
        self.assertEqual([c['text'] for c in o.clock()['captions']],[c.text for t in s.captions for c in t.cues])
    def test_cancellation_before_native_work(self):
        c=threading.Event();c.set()
        with self.assertRaisesRegex(AudioError,'CANCELLED'):mix_synchronized(self.sync,meter=self.meter,cancellation=c)
    def test_changed_upstream_wav_blocked(self):
        raw=bytearray(self.sync.wav_bytes);raw[-2]^=1
        with self.assertRaisesRegex(AudioError,'UPSTREAM_CLOCK'):mix_synchronized(replace(self.sync,wav_bytes=bytes(raw)),meter=self.meter)
    def test_changed_upstream_caption_blocked(self):
        cap=self.sync.captions[0];cue=replace(cap.cues[0],text='X'*len(cap.cues[0].text),lines=('X'*len(cap.cues[0].text),))
        with self.assertRaises(AudioError):mix_synchronized(replace(self.sync,captions=(replace(cap,cues=(cue,)),*self.sync.captions[1:])),meter=self.meter)
    def test_changed_animation_binding_blocked(self):
        a=self.animations;t=a.tracks[0]
        bad=replace(a,tracks=(replace(t,end_sample=t.end_sample-2),))
        with self.assertRaises(AudioError):mix_synchronized(self.sync,meter=self.meter,animations=bad)
    def test_delivery_wav_tamper_rejected(self):
        raw=bytearray(self.result.wav_bytes);raw[-5]^=1
        with self.assertRaises(AudioError):replace(self.result,wav_bytes=bytes(raw)).validate()
    def test_delivery_clock_tamper_rejected(self):
        c=self.result.clock();c['total_samples']+=1
        with self.assertRaises(AudioError):replace(self.result,clock_json=json.dumps(c)).validate()
    def test_rehashed_outside_caption_rejected(self):
        c=self.result.clock();c['captions'][0]['end_sample']=c['total_samples']+1
        with self.assertRaises(AudioError):reseal(self.result,clock=c).validate()
    def test_rehashed_wrong_meter_identity_rejected(self):
        r=self.result.receipt();r['peak_control']['after']['pcm_fingerprint']='sha256:'+'0'*64
        with self.assertRaises(AudioError):reseal(self.result,receipt=r).validate()
    def test_acceptance_cannot_be_promoted(self):
        r=self.result.receipt();r['product_accepted']=True
        with self.assertRaises(AudioError):reseal(self.result,receipt=r).validate()
    def test_require_matching_source_on_revalidation(self):
        from bie.audio.mix_pipeline import verify_mixed_source
        self.assertIs(verify_mixed_source(self.result,self.sync,animations=self.animations),self.result)
        with self.assertRaises(AudioError):verify_mixed_source(self.result,real_sync('hindi'),animations=self.animations)
    def test_technical_output_not_acceptance(self):
        for key in ('cinematic_quality_verified','product_accepted','actual_remotion_render_verified','independent_acoustic_alignment_verified'):
            self.assertIs(self.result.receipt()[key],False)
    def test_rehashed_false_review_not_accepted(self):
        r=self.result.receipt();r['policy']['loudness']['target_lufs']=-10
        with self.assertRaisesRegex(AudioError,'LOUDNESS|REVIEW'):reseal(self.result,receipt=r).validate()
    def test_rehashed_peak_ceiling_mismatch_rejected(self):
        r=self.result.receipt();r['peak_control']['after']['true_peak_dbtp']=1
        with self.assertRaisesRegex(AudioError,'PEAK'):reseal(self.result,receipt=r).validate()
    def test_rehashed_invalid_policy_rejected(self):
        r=self.result.receipt();r['policy']['pause_mode']='discard-pauses'
        with self.assertRaises(AudioError):reseal(self.result,receipt=r).validate()
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(AudioError,'DUPLICATE_JSON'):replace(self.result,clock_json='{"a":1,"a":2}').validate()
    def test_post_peak_unmet_target_respects_fail_policy(self):
        from bie.audio.peak_control import control_peaks
        def constrained(*args,**kwargs):
            wav,r=control_peaks(*args,**kwargs);r['after']['integrated_lufs']=-35;return wav,r
        with patch('bie.audio.mix_pipeline.control_peaks',side_effect=constrained):
            with self.assertRaisesRegex(AudioError,'FINAL_LOUDNESS_TARGET_UNREACHABLE'):
                mix_synchronized(self.sync,policy=MixPolicy(loudness=LoudnessPolicy(unreachable='fail')),meter=self.meter)
