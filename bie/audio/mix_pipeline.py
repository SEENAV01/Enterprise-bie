"""MIX composition over existing measured SYNC artifacts; originals are never rewritten."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from html import escape
import hashlib,json,numpy as np
from .common import AudioError,fingerprint,integer,strict_json
from .mix_contract import MixBuffer,SampleSpan
from .mix_meter import FFmpegMeter
from .loudness_normalization import LoudnessPolicy,normalize_loudness
from .music_ducking import DuckingPolicy,duck_music
from .sfx_mixing import Stem,place_stems,silence_music_windows,sum_buses
from .silence_trim import TrimPolicy,TrimPlan,plan_silence_trim,apply_silence_trim
from .peak_control import PeakPolicy,control_peaks
from .sync_pipeline import SynchronizedAudio
from .scene_sync import assemble_scenes
from .caption_alignment import align_captions,timestamp
from .pause_sync import synchronize_pauses
from .animation_sync import AnimationBinding,AnimationSync,synchronize_animations
from .sync_contract import FrameRate,samples_for_ms
from .tts_contract import AudioFormat
@dataclass(frozen=True)
class MixPolicy:
    loudness:LoudnessPolicy=LoudnessPolicy()
    ducking:DuckingPolicy=DuckingPolicy()
    trim:TrimPolicy=TrimPolicy()
    peaks:PeakPolicy=PeakPolicy()
    pause_mode:str='all_stems_silent'
    pause_fade_ms:int=30
    def __post_init__(self):
        for v,cls in ((self.loudness,LoudnessPolicy),(self.ducking,DuckingPolicy),(self.trim,TrimPolicy),(self.peaks,PeakPolicy)):
            if type(v)is not cls:raise AudioError('MIX_POLICY_TYPE')
            cls(**asdict(v))
        if self.pause_mode not in ('all_stems_silent','narration_only'):raise AudioError('MIX_PAUSE_MODE')
        integer(self.pause_fade_ms,'pause fade',0,2000)
        if self.peaks.ceiling_dbtp>self.loudness.true_peak_ceiling_dbtp:raise AudioError('MIX_PEAK_POLICY_CONFLICT')
@dataclass(frozen=True)
class MixedAudio:
    wav_bytes:bytes
    clock_json:str
    receipt_json:str
    def clock(self):return strict_json(self.clock_json)
    def receipt(self):return strict_json(self.receipt_json)
    def validate(self):
        try:return self._validate()
        except (ValueError,TypeError,KeyError,AttributeError) as e:
            if isinstance(e,AudioError):raise
            raise AudioError('MIX_INVALID_RESULT',str(e)[:160]) from e
    def _validate(self):
        c=self.clock();r=self.receipt();h=r.pop('fingerprint',None)
        if h!=fingerprint(r):raise AudioError('MIX_RECEIPT_CHANGED')
        if r.get('schema_version')!='bie.audio.mix-run/1' or c.get('schema_version')!='bie.audio.mixed-clock/1':raise AudioError('MIX_SCHEMA_CHANGED')
        for k in ('product_accepted','cinematic_quality_verified','independent_acoustic_alignment_verified','actual_remotion_render_verified'):
            if r.get(k)is not False:raise AudioError('MIX_ACCEPTANCE_NOT_ESTABLISHED')
        h=hashlib.sha256(self.wav_bytes).hexdigest()
        if c['output_audio_sha256']!=h or r['output_audio_sha256']!=h or r['clock_fingerprint']!=fingerprint(c):raise AudioError('MIX_MEDIA_CHANGED')
        pcm=MixBuffer.from_wav(self.wav_bytes,AudioFormat(c['sample_rate'],c['channels']))
        if pcm.frames!=c['total_samples'] or pcm.info()!=r['delivery_pcm']:raise AudioError('MIX_CLOCK_CHANGED')
        policy=r['policy']
        checked=MixPolicy(loudness=LoudnessPolicy(**policy['loudness']),ducking=DuckingPolicy(**policy['ducking']),
                          trim=TrimPolicy(**policy['trim']),peaks=PeakPolicy(**policy['peaks']),
                          pause_mode=policy['pause_mode'],pause_fade_ms=policy['pause_fade_ms'])
        final=r['peak_control']['after']
        tp=final['true_peak_dbtp'];il=final['integrated_lufs']
        if tp is not None and (type(tp) not in (int,float) or not np.isfinite(tp) or tp>checked.peaks.ceiling_dbtp):raise AudioError('MIX_PEAK_CEILING')
        reached=il is not None and type(il) in (int,float) and np.isfinite(il) and abs(il-checked.loudness.target_lufs)<=checked.loudness.tolerance_lu
        expected=[]
        if not reached:expected.append('FINAL_LOUDNESS_TARGET_UNMET')
        if r['narration_normalization']['requires_review']:expected.append('NARRATION_LOUDNESS_CONSTRAINED')
        if r['final_loudness_target_reached'] is not bool(reached) or r['requires_review'] is not bool(expected) or r['review_reasons']!=expected:raise AudioError('MIX_LOUDNESS_REVIEW_CHANGED')
        if not reached and checked.loudness.unreachable=='fail':raise AudioError('FINAL_LOUDNESS_TARGET_UNREACHABLE')
        from .mix_clock import validate_mixed_clock
        validate_mixed_clock(c,r,pcm)
        return self
    def state_at_sample(self,sample):
        self.validate()
        from .mix_clock import state_at_sample
        return state_at_sample(self.clock(),sample)
    def state_at_frame(self,frame):
        integer(frame,'frame',0,432000);c=self.clock()
        return self.state_at_sample(FrameRate(**c['fps']).sample_at(frame,c['sample_rate']))


def _verified_sync(sync):
    if type(sync)is not SynchronizedAudio:raise AudioError('MIX_SYNCHRONIZED_AUDIO_REQUIRED')
    timeline,wav=assemble_scenes(sync.plan,sync.assets,sync.alignments,fps=sync.timeline.fps)
    if timeline!=sync.timeline or wav!=sync.wav_bytes:raise AudioError('MIX_UPSTREAM_CLOCK_CHANGED')
    if len(sync.captions)!=len(sync.assets):raise AudioError('MIX_UPSTREAM_CAPTIONS')
    for asset,aligned,caption in zip(sync.assets,sync.alignments,sync.captions):
        if align_captions(asset,aligned,caption.policy)!=caption:raise AudioError('MIX_UPSTREAM_CAPTIONS')
    if synchronize_pauses(timeline,wav,sync.assets,sync.alignments,sync.captions)!=sync.pauses:raise AudioError('MIX_UPSTREAM_PAUSES')
    return timeline

def _derive_clock(sync,trim,output_hash,animations):
    t=sync.timeline;fps=t.fps;rate=t.sample_rate
    c={'schema_version':'bie.audio.mixed-clock/1','source_timeline_fingerprint':t.fingerprint(),'source_audio_sha256':t.audio_sha256,
       'plan_fingerprint':sync.plan.fingerprint(),'output_audio_sha256':output_hash,'sample_rate':rate,'channels':t.channels,
       'total_samples':trim.output_frames,'fps':asdict(fps),'duration_frames':fps.at_or_after(trim.output_frames,rate),
       'source_start_sample':trim.keep_start,'source_end_sample':trim.keep_end,'time_transform':'source_sample minus keep_start; no resampling or latency',
       'words':[],'captions':[],'pauses':[],'scenes':[],'segments':[],'animations':[]}
    for s in t.scenes:
        a=max(s.start_sample,trim.keep_start)-trim.keep_start;b=min(s.end_sample,trim.keep_end)-trim.keep_start
        if a>=b or fps.at_or_after(a,rate)>=fps.at_or_after(b,rate):raise AudioError('TRIM_COLLAPSES_SCENE')
        c['scenes'].append({**asdict(s),'start_sample':a,'end_sample':b,'start_frame':fps.at_or_after(a,rate),'end_frame':fps.at_or_after(b,rate)})
    for p,a,track in zip(t.segments,sync.alignments,sync.captions):
        c['segments'].append({**asdict(p),'source_start_sample':p.start_sample,'start_sample':max(p.start_sample,trim.keep_start)-trim.keep_start,
                              'end_sample':min(p.end_sample,trim.keep_end)-trim.keep_start,'provider_end_sample':min(p.provider_end_sample,trim.keep_end)-trim.keep_start})
        for w in a.words:c['words'].append({**asdict(w),'segment_id':p.segment_id,'alignment_fingerprint':a.fingerprint(),
           'start_sample':trim.map_sample(p.start_sample+w.start_sample),'end_sample':trim.map_sample(p.start_sample+w.end_sample)})
        for cue in track.cues:c['captions'].append({**asdict(cue),'segment_id':p.segment_id,'track_fingerprint':track.fingerprint(),
           'start_sample':trim.map_sample(p.start_sample+cue.start_sample),'end_sample':trim.map_sample(p.start_sample+cue.end_sample)})
    for p in sync.pauses.windows:c['pauses'].append({**asdict(p),'start_sample':trim.map_sample(p.start_sample),'end_sample':trim.map_sample(p.end_sample)})
    if animations:
        for track in animations.tracks:
            a,b=trim.map_sample(track.start_sample),trim.map_sample(track.end_sample)
            c['animations'].append({'binding':asdict(track.binding),'source_track_fingerprint':fingerprint(track),
              'start_sample':a,'end_sample':b,'start_frame':fps.at_or_after(a,rate),'end_frame':fps.at_or_after(b,rate),
              'holds':[(trim.map_sample(x),trim.map_sample(y)) for x,y in track.holds],
              'keyframes':[(trim.map_sample(s),n,d) for s,n,d in track.keyframes()]})
    return c

def mix_synchronized(sync,stems=(),*,policy=MixPolicy(),meter=None,animations=None,cancellation=None):
    if type(policy)is not MixPolicy:raise AudioError('MIX_POLICY_TYPE')
    MixPolicy(**policy.__dict__);t=_verified_sync(sync)
    if animations is not None:
        if type(animations)is not AnimationSync or synchronize_animations(t,sync.alignments,tuple(x.binding for x in animations.tracks))!=animations:raise AudioError('MIX_ANIMATION_CHANGED')
    raw=MixBuffer.from_wav(sync.wav_bytes,AudioFormat(t.sample_rate,t.channels));protected=[]
    for p,a,track in zip(t.segments,sync.alignments,sync.captions):
        for w in a.words:protected.append(SampleSpan(p.start_sample+w.start_sample,p.start_sample+w.end_sample,'word:'+p.segment_id,tuple(sorted({r for s in w.source for r in s.source_refs}))))
        for cue in track.cues:protected.append(SampleSpan(p.start_sample+cue.start_sample,p.start_sample+cue.end_sample,'caption:'+p.segment_id,('caption:'+track.fingerprint(),)))
    pauses=tuple(SampleSpan(p.start_sample,p.end_sample,'pause:'+p.segment_id,p.pause_refs) for p in sync.pauses.windows);protected.extend(pauses)
    required=pauses if policy.pause_mode=='all_stems_silent' else ()
    music,music_r=place_stems(stems,rate=t.sample_rate,channels=t.channels,frames=raw.frames,role='music')
    sfx,sfx_r=place_stems(stems,rate=t.sample_rate,channels=t.channels,frames=raw.frames,role='sfx',protected_silence=required)
    for s in stems:protected.append(SampleSpan(s.start_sample,s.start_sample+s.length,'asset:'+s.asset_id,s.source_refs))
    if animations:
        for a in animations.tracks:protected.append(SampleSpan(a.start_sample,a.end_sample,'animation:'+a.binding.binding_id,a.binding.source_refs))
    trim=plan_silence_trim(raw,policy.trim,tuple(protected));dry,trim_r=apply_silence_trim(raw,trim)
    music=music.slice(trim.keep_start,trim.keep_end);sfx=sfx.slice(trim.keep_start,trim.keep_end);meter=meter or FFmpegMeter()
    voice,voice_r=normalize_loudness(dry,meter,policy.loudness,cancellation=cancellation);music,duck_r=duck_music(music,voice,policy.ducking)
    mapped=tuple(SampleSpan(trim.map_sample(p.start),trim.map_sample(p.end),p.owner,p.source_refs) for p in pauses)
    music,silence_r=silence_music_windows(music,mapped if required else (),fade_samples=samples_for_ms(policy.pause_fade_ms,t.sample_rate))
    total=sum_buses(voice,music,sfx);normalized,programme_r=normalize_loudness(total,meter,policy.loudness,cancellation=cancellation)
    wav,peak_r=control_peaks(normalized,meter,policy.peaks,dual_mono=policy.loudness.dual_mono,cancellation=cancellation)
    delivered=MixBuffer.from_wav(wav,AudioFormat(t.sample_rate,t.channels));h=hashlib.sha256(wav).hexdigest()
    if required and any(np.any(delivered.array()[p.start:p.end]) for p in mapped):raise AudioError('MIX_REQUIRED_SILENCE_LOST')
    clock=_derive_clock(sync,trim,h,animations);il=peak_r['after']['integrated_lufs'];reached=il is not None and abs(il-policy.loudness.target_lufs)<=policy.loudness.tolerance_lu
    if not reached and policy.loudness.unreachable=='fail':raise AudioError('FINAL_LOUDNESS_TARGET_UNREACHABLE')
    review=[]
    if not reached:review.append('FINAL_LOUDNESS_TARGET_UNMET')
    if voice_r['requires_review']:review.append('NARRATION_LOUDNESS_CONSTRAINED')
    r={'schema_version':'bie.audio.mix-run/1','source_sync_fingerprint':fingerprint(sync.receipt()),'source_timeline_fingerprint':t.fingerprint(),
       'source_audio_sha256':t.audio_sha256,'output_audio_sha256':h,'clock_fingerprint':fingerprint(clock),'delivery_pcm':delivered.info(),
       'policy':asdict(policy),'meter_identity':meter.identity,'numpy_version':np.__version__,'trim':trim_r,'narration_normalization':voice_r,
       'music':music_r,'sfx':sfx_r,'ducking':duck_r,'pause_music_automation':silence_r,'programme_normalization':programme_r,'peak_control':peak_r,
       'final_loudness_target_reached':reached,'requires_review':bool(review),'review_reasons':review,'source_sync_receipts_rewritten':False,
       'independent_acoustic_alignment_verified':False,'cinematic_quality_verified':False,'actual_remotion_render_verified':False,'product_accepted':False}
    r['fingerprint']=fingerprint(r);result=MixedAudio(wav,json.dumps(clock,ensure_ascii=False,sort_keys=True,allow_nan=False),json.dumps(r,ensure_ascii=False,sort_keys=True,allow_nan=False));result.validate();return result

def export_mixed_captions(result,format='vtt'):
    result.validate()
    if format not in ('vtt','srt'):raise AudioError('MIX_CAPTION_FORMAT')
    c=result.clock();rate=c['sample_rate'];out=['WEBVTT',''] if format=='vtt' else [];last=0
    for i,cue in enumerate(c['captions'],1):
        a,b=cue['start_sample'],cue['end_sample'];ams=(a*1000+rate//2)//rate;bms=(b*1000+rate//2)//rate
        if ams<last or bms<=ams:raise AudioError('MIX_CAPTION_ROUNDING')
        sep='.' if format=='vtt' else ',';out.extend([str(i),f'{timestamp(a,rate,sep)} --> {timestamp(b,rate,sep)}','\n'.join(escape(x,quote=False) for x in cue['lines']),'']);last=bms
    return '\n'.join(out)+'\n'


def verify_mixed_source(result,sync,*,animations=None):
    """Replay the derived clock against actual source media, not caller hashes alone.

    Does not re-run DSP metering, authenticate an author, or award QA acceptance.
    """
    result.validate();_verified_sync(sync);r=result.receipt();c=result.clock()
    if r['source_sync_fingerprint']!=fingerprint(sync.receipt()):raise AudioError('MIX_PUBLICATION_SOURCE_MISMATCH')
    if animations is None and c['animations']:
        bindings=[]
        for row in c['animations']:
            b=dict(row['binding'])
            for k in ('source_refs','reasoning_refs','after'):b[k]=tuple(b[k])
            bindings.append(AnimationBinding(**b))
        animations=synchronize_animations(sync.timeline,sync.alignments,tuple(bindings))
    elif animations is not None:
        if type(animations)is not AnimationSync or synchronize_animations(sync.timeline,sync.alignments,tuple(t.binding for t in animations.tracks))!=animations:raise AudioError('MIX_ANIMATION_CHANGED')
    p=dict(r['trim']['plan']);p['policy']=TrimPolicy(**p['policy'])
    p['protected']=tuple(SampleSpan(**{**v,'source_refs':tuple(v['source_refs'])}) for v in p['protected'])
    plan=TrimPlan(**p);source=MixBuffer.from_wav(sync.wav_bytes,AudioFormat(sync.timeline.sample_rate,sync.timeline.channels))
    apply_silence_trim(source,plan)
    if json.loads(json.dumps(_derive_clock(sync,plan,r['output_audio_sha256'],animations)))!=c:raise AudioError('MIX_DERIVED_CLOCK_MISMATCH')
    return result
