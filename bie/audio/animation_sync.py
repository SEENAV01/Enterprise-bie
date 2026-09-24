"""BIE-AUDIO-SYNC-004: explicit narration anchors -> actual sample/frame tracks.

Pure seek evaluation is provided; these tracks do not assert a video was rendered.
Frame rounding is ceiling at both boundaries. Pauses cannot be crossed accidentally.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from .common import AudioError,digest,fingerprint,integer,refs,text
from .speech_contract import records
from .sync_contract import AlignedSpeech,samples_for_ms,MAX_SAMPLES
from .scene_sync import AudioTimeline

@dataclass(frozen=True)
class AnimationBinding:
    binding_id: str
    target_id: str
    action: str
    start_segment_id: str
    first_word: int
    end_segment_id: str
    last_word: int
    timeline_fingerprint: str
    source_refs: tuple[str,...]
    reasoning_refs: tuple[str,...]
    start_offset_ms: int=0
    end_offset_ms: int=0
    minimum_frames: int=1
    pause_mode: str='forbid'
    after: tuple[str,...]=()
    def __post_init__(self):
        for n in ('binding_id','target_id','action','start_segment_id','end_segment_id'):text(getattr(self,n),n,2048)
        integer(self.first_word,'first word',0,19999);integer(self.last_word,'last word',0,19999)
        digest(self.timeline_fingerprint);refs(self.source_refs,'sources');refs(self.reasoning_refs,'reasoning')
        integer(self.start_offset_ms,'start offset',-10000,10000);integer(self.end_offset_ms,'end offset',-10000,10000)
        integer(self.minimum_frames,'minimum frames',1,2400);refs(self.after,'dependencies',False)
        if self.pause_mode not in ('forbid','hold','continue'):raise AudioError('ANIMATION_PAUSE_POLICY')

@dataclass(frozen=True)
class SyncedTrack:
    binding: AnimationBinding
    scene_id: str
    start_sample: int
    end_sample: int
    start_frame: int
    end_frame: int
    holds: tuple[tuple[int,int],...]
    def progress_at_sample(self,sample):
        integer(sample,'sample',0,MAX_SAMPLES)
        if sample<=self.start_sample:return Fraction(0)
        if sample>=self.end_sample:return Fraction(1)
        total=self.end_sample-self.start_sample-sum(b-a for a,b in self.holds)
        elapsed=sample-self.start_sample-sum(max(0,min(sample,b)-a) for a,b in self.holds if sample>a)
        return Fraction(elapsed,total)
    def keyframes(self):
        times=sorted({self.start_sample,self.end_sample,*(n for pair in self.holds for n in pair)})
        return tuple((s,self.progress_at_sample(s).numerator,self.progress_at_sample(s).denominator) for s in times)

@dataclass(frozen=True)
class AnimationSync:
    timeline_fingerprint: str
    tracks: tuple[SyncedTrack,...]
    def fingerprint(self):return fingerprint(self)
    def state_at_frame(self,timeline,frame):
        if timeline.fingerprint()!=self.timeline_fingerprint:raise AudioError('ANIMATION_STALE_TIMELINE')
        sample=timeline.fps.sample_at(frame,timeline.sample_rate)
        return tuple({'binding_id':t.binding.binding_id,'target_id':t.binding.target_id,
                      'active':t.start_frame<=frame<t.end_frame,'progress':float(t.progress_at_sample(sample))} for t in self.tracks)


def _offset(ms,rate):return (1 if ms>=0 else -1)*samples_for_ms(abs(ms),rate)


def synchronize_animations(timeline:AudioTimeline,alignments,bindings,*,require_measured=True):
    if type(timeline)is not AudioTimeline or type(alignments)is not tuple:raise AudioError('ANIMATION_TIMELINE_REQUIRED')
    records(bindings,AnimationBinding,'animation bindings',limit=4096,required=False)
    if len(alignments)!=len(timeline.segments):raise AudioError('ANIMATION_ALIGNMENT_COVERAGE')
    by={p.segment_id:(p,a) for p,a in zip(timeline.segments,alignments)}
    for p,a in by.values():
        if type(a)is not AlignedSpeech or p.alignment_fingerprint!=a.fingerprint():raise AudioError('ANIMATION_STALE_ALIGNMENT')
        if require_measured and a.basis not in ('ESPEAK_ENGINE_EVENTS_PCM_REPLAY','ESPEAK_MARK_EVENTS_SAME_PCM'):raise AudioError('MEASURED_WORD_TIMING_REQUIRED')
    if len({b.binding_id for b in bindings})!=len(bindings):raise AudioError('DUPLICATE_ANIMATION_BINDING')
    tracks=[];tf=timeline.fingerprint();windows={s.scene_id:s for s in timeline.scenes}
    for b in bindings:
        if b.timeline_fingerprint!=tf:raise AudioError('ANIMATION_STALE_TIMELINE')
        if b.start_segment_id not in by or b.end_segment_id not in by:raise AudioError('ANIMATION_UNKNOWN_SEGMENT')
        sp,sa=by[b.start_segment_id];ep,ea=by[b.end_segment_id]
        if sp.scene_id!=ep.scene_id or sp.start_sample>ep.start_sample:raise AudioError('ANIMATION_SCENE_ORDER')
        if b.first_word>=len(sa.words) or b.last_word>=len(ea.words):raise AudioError('ANIMATION_UNKNOWN_WORD')
        if b.start_segment_id==b.end_segment_id and b.last_word<b.first_word:raise AudioError('ANIMATION_WORD_ORDER')
        sw,ew=sa.words[b.first_word],ea.words[b.last_word]
        selected=[]
        for placement,alignment in by.values():
            if placement.scene_id==sp.scene_id and sp.start_sample<=placement.start_sample<=ep.start_sample:
                lower=b.first_word if placement.segment_id==sp.segment_id else 0
                upper=b.last_word+1 if placement.segment_id==ep.segment_id else len(alignment.words)
                selected.extend(alignment.words[lower:upper])
        available={r for w in selected for s in w.source for r in s.source_refs}
        if not set(b.source_refs)<=available:raise AudioError('ANIMATION_UNBOUND_SOURCE')
        start=sp.start_sample+sw.start_sample+_offset(b.start_offset_ms,timeline.sample_rate)
        end=ep.start_sample+ew.end_sample+_offset(b.end_offset_ms,timeline.sample_rate)
        window=windows[sp.scene_id]
        if not window.start_sample<=start<end<=window.end_sample:raise AudioError('ANIMATION_OUTSIDE_SCENE')
        fs,fe=timeline.fps.at_or_after(start,timeline.sample_rate),timeline.fps.at_or_after(end,timeline.sample_rate)
        if fe-fs<b.minimum_frames:raise AudioError('ANIMATION_UNDERSAMPLED','extend/replan explicitly; do not compress semantics')
        pauses=tuple((max(start,p.provider_end_sample),min(end,p.end_sample)) for p in timeline.segments if max(start,p.provider_end_sample)<min(end,p.end_sample))
        if pauses and b.pause_mode=='forbid':raise AudioError('ANIMATION_CROSSES_PEDAGOGICAL_PAUSE')
        holds=pauses if b.pause_mode=='hold' else ()
        if end-start<=sum(y-x for x,y in holds):raise AudioError('ANIMATION_NO_ACTIVE_TIME')
        tracks.append(SyncedTrack(b,sp.scene_id,start,end,fs,fe,holds))
    index={t.binding.binding_id:t for t in tracks}
    for t in tracks:
        for predecessor in t.binding.after:
            if predecessor not in index or index[predecessor].end_sample>t.start_sample or index[predecessor].end_frame>t.start_frame:
                raise AudioError('ANIMATION_DEPENDENCY_ORDER')
    # Same target/action owns one writer at a time. Different actions remain explicit upstream contracts.
    ordered=sorted(tracks,key=lambda t:(t.binding.target_id,t.binding.action,t.start_frame,t.binding.binding_id))
    for a,b in zip(ordered,ordered[1:]):
        if a.binding.target_id==b.binding.target_id and a.binding.action==b.binding.action and a.end_frame>b.start_frame:
            raise AudioError('ANIMATION_WRITER_COLLISION')
    return AnimationSync(tf,tuple(tracks))
