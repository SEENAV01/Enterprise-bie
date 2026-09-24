"""BIE-AUDIO-SYNC-003: sample-authoritative scene/audio assembly.

No WPM estimates, implicit speed-up, lossy resample or content truncation.
Scene frame boundaries share a single rational clock and never accumulate rounding.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from .common import AudioError, digest, fingerprint, integer, text
from .speech_contract import SpeechPlan,records
from .sync_contract import AlignedSpeech, FrameRate, MAX_SAMPLES, validate_alignment, validate_asset
from .pcm_audio import encode_pcm,validate_wav

@dataclass(frozen=True)
class SegmentPlacement:
    segment_id: str
    scene_id: str
    request_fingerprint: str
    alignment_fingerprint: str
    media_sha256: str
    start_sample: int
    provider_end_sample: int
    end_sample: int
    def __post_init__(self):
        text(self.segment_id,'segment id',2048);text(self.scene_id,'scene id',2048)
        digest(self.request_fingerprint);digest(self.alignment_fingerprint)
        if type(self.media_sha256)is not str or len(self.media_sha256)!=64:raise AudioError('PLACEMENT_HASH')
        for name in ('start_sample','provider_end_sample','end_sample'):integer(getattr(self,name),name,0,MAX_SAMPLES)
        if not self.start_sample<self.provider_end_sample<=self.end_sample:raise AudioError('SEGMENT_CLOCK')

@dataclass(frozen=True)
class SceneWindow:
    scene_id: str
    segment_ids: tuple[str,...]
    start_sample: int
    end_sample: int
    start_frame: int
    end_frame: int

@dataclass(frozen=True)
class SceneBudget:
    scene_id: str
    min_frames: int=1
    max_frames: int=432000
    def __post_init__(self):
        text(self.scene_id,'scene id',2048);integer(self.min_frames,'minimum',1,432000);integer(self.max_frames,'maximum',self.min_frames,432000)

@dataclass(frozen=True)
class AudioTimeline:
    plan_fingerprint: str
    audio_sha256: str
    sample_rate: int
    channels: int
    total_samples: int
    fps: FrameRate
    segments: tuple[SegmentPlacement,...]
    scenes: tuple[SceneWindow,...]
    schema_version: str='bie.audio.measured-scene-timeline/1'
    def __post_init__(self):
        digest(self.plan_fingerprint)
        if type(self.audio_sha256)is not str or len(self.audio_sha256)!=64:raise AudioError('TIMELINE_HASH')
        integer(self.sample_rate,'rate',8000,192000);integer(self.channels,'channels',1,2);integer(self.total_samples,'samples',1,MAX_SAMPLES)
        if type(self.fps)is not FrameRate or self.schema_version!='bie.audio.measured-scene-timeline/1':raise AudioError('TIMELINE_SCHEMA')
        records(self.segments,SegmentPlacement,'placements');records(self.scenes,SceneWindow,'scenes')
        cursor=0
        for s in self.segments:
            digest(s.request_fingerprint);digest(s.alignment_fingerprint)
            if not s.start_sample==cursor<s.provider_end_sample<=s.end_sample:raise AudioError('SEGMENT_CLOCK')
            cursor=s.end_sample
        if cursor!=self.total_samples or len({s.segment_id for s in self.segments})!=len(self.segments):raise AudioError('TIMELINE_COVERAGE')
        cursor=0;ids=[]
        for scene in self.scenes:
            selected=tuple(s for s in self.segments if s.scene_id==scene.scene_id)
            if not selected or scene.segment_ids!=tuple(s.segment_id for s in selected) or scene.start_sample!=selected[0].start_sample or scene.end_sample!=selected[-1].end_sample or scene.start_sample!=cursor:raise AudioError('SCENE_COVERAGE')
            if scene.start_frame!=self.fps.at_or_after(scene.start_sample,self.sample_rate) or scene.end_frame!=self.fps.at_or_after(scene.end_sample,self.sample_rate) or scene.start_frame>=scene.end_frame:raise AudioError('SCENE_FRAME_COLLAPSE')
            cursor=scene.end_sample;ids.extend(scene.segment_ids)
        if cursor!=self.total_samples or tuple(ids)!=tuple(s.segment_id for s in self.segments):raise AudioError('SCENE_ORDER')
    def fingerprint(self):return fingerprint(self)
    @property
    def duration_frames(self):return self.fps.at_or_after(self.total_samples,self.sample_rate)
    def scene_at_frame(self,frame):
        integer(frame,'frame',0,432000)
        return next((s.scene_id for s in self.scenes if s.start_frame<=frame<s.end_frame),None)


def assemble_scenes(plan:SpeechPlan,assets,alignments,*,fps=FrameRate(),budgets=(),require_measured=True):
    if type(plan)is not SpeechPlan or type(assets)is not tuple or type(alignments)is not tuple or len(assets)!=len(plan.segments) or len(alignments)!=len(assets):raise AudioError('SCENE_INPUT_COVERAGE')
    if type(fps)is not FrameRate:raise AudioError('FRAME_RATE_REQUIRED')
    plan.require_ready();records(budgets,SceneBudget,'scene budgets',required=False)
    if len({b.scene_id for b in budgets})!=len(budgets):raise AudioError('DUPLICATE_SCENE_BUDGET')
    if not assets:raise AudioError('SCENE_AUDIO_EMPTY')
    fmt=assets[0].request.settings.format; cursor=0;raw=[];placements=[];closed=set();current=None;scene_ids=[]
    for segment,asset,aligned in zip(plan.segments,assets,alignments):
        if asset.request.segment!=segment or asset.request.plan_fingerprint!=plan.fingerprint():raise AudioError('SCENE_REQUEST_MISMATCH')
        if asset.request.settings.format!=fmt:raise AudioError('SCENE_FORMAT_MIX','resampling requires a separate governed transform')
        validate_alignment(asset,aligned,require_measured=require_measured);info,pcm,_=validate_asset(asset)
        if segment.scene_id!=current:
            if segment.scene_id in closed:raise AudioError('SCENE_NONCONTIGUOUS')
            closed.add(segment.scene_id);current=segment.scene_id;scene_ids.append(current)
        end=cursor+info.samples_per_channel
        if end>fmt.sample_rate*1800 or end*fmt.channels*2>64000000:raise AudioError('SCENE_AUDIO_BUDGET','split the job; no truncation')
        placements.append(SegmentPlacement(segment.segment_id,segment.scene_id,asset.request.fingerprint(),aligned.fingerprint(),info.sha256,cursor,cursor+aligned.provider_samples,end))
        raw.append(pcm);cursor=end
    if set(b.scene_id for b in budgets)-set(scene_ids):raise AudioError('UNKNOWN_SCENE_BUDGET')
    constraints={b.scene_id:b for b in budgets};scenes=[]
    for scene_id in scene_ids:
        rows=[p for p in placements if p.scene_id==scene_id];a,b=rows[0].start_sample,rows[-1].end_sample
        fa,fb=fps.at_or_after(a,fmt.sample_rate),fps.at_or_after(b,fmt.sample_rate)
        constraint=constraints.get(scene_id,SceneBudget(scene_id))
        if fb-fa>constraint.max_frames:raise AudioError('SCENE_EXTENSION_REQUIRED',scene_id)
        if fb-fa<constraint.min_frames:raise AudioError('EXPLICIT_HOLD_REQUIRED',scene_id)
        scenes.append(SceneWindow(scene_id,tuple(p.segment_id for p in rows),a,b,fa,fb))
    wav=encode_pcm(b''.join(raw),fmt);info,_=validate_wav(wav,fmt,max_bytes=64001000,max_seconds=1800)
    timeline=AudioTimeline(plan.fingerprint(),info.sha256,fmt.sample_rate,fmt.channels,cursor,fps,tuple(placements),tuple(scenes))
    return timeline,wav


def validate_timeline_media(timeline,wav):
    from .tts_contract import AudioFormat
    if type(timeline)is not AudioTimeline:raise AudioError('TIMELINE_REQUIRED')
    AudioTimeline(**timeline.__dict__)
    info,_=validate_wav(wav,AudioFormat(timeline.sample_rate,timeline.channels),max_bytes=64001000,max_seconds=1800)
    if info.sha256!=timeline.audio_sha256 or info.samples_per_channel!=timeline.total_samples:raise AudioError('TIMELINE_MEDIA_CHANGED')
    return timeline
