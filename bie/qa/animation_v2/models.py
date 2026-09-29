"""Bounded animation contracts. Milliseconds, milli-pixels and exact rational FPS.

The operator supplies inventory, semantic obligations and thresholds independently
of the candidate. These are declared 2-D tracks, not arbitrary CSS/3-D physics.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from math import gcd
from ..release_v2.contracts import ArtifactRef, ContractError, token, integer, choice, tuple_tokens, digest
from ..source_v2.models import Request, Policy, records

MAX_TIME = 86_400_000
PROPERTIES = ('x_mpx','y_mpx','rotation_mdeg','scale_ppm','opacity_ppm','progress_ppm','value_milli')

def rows(value, cls, name, key, minimum=0, maximum=256):
    records(value, cls, name, key, minimum)
    if len(value)>maximum: raise ContractError('ANI_COLLECTION_LIMIT',name)

def interval(start, end):
    integer(start,'start_ms',0,MAX_TIME); integer(end,'end_ms',start+1,MAX_TIME)

@dataclass(frozen=True, slots=True)
class FrameRate:
    numerator: int
    denominator: int = 1
    def __post_init__(self):
        integer(self.numerator,'fps.numerator',1,240000)
        integer(self.denominator,'fps.denominator',1,10000)
        if gcd(self.numerator,self.denominator)!=1 or not 1<=self.numerator/self.denominator<=240:
            raise ContractError('ANI_FRAME_RATE_RANGE_OR_CANONICAL')

@dataclass(frozen=True, slots=True)
class Mode:
    mode_id: str
    kind: str
    duration_ms: int
    fps: FrameRate
    width_px: int
    height_px: int
    def __post_init__(self):
        token(self.mode_id,'mode_id'); choice(self.kind,('standard','reduced'),'mode.kind')
        integer(self.duration_ms,'duration_ms',1,MAX_TIME)
        if type(self.fps) is not FrameRate: raise ContractError('ANI_FPS_TYPE')
        integer(self.width_px,'width_px',64,8192); integer(self.height_px,'height_px',64,8192)

@dataclass(frozen=True, slots=True)
class ObjectSpec:
    object_id: str
    semantic_id: str
    role: str
    start_ms: int
    end_ms: int
    claim_ids: tuple[str,...]
    def __post_init__(self):
        token(self.object_id,'object_id'); token(self.semantic_id,'semantic_id')
        choice(self.role,('object','label','camera','decoration'),'object.role')
        interval(self.start_ms,self.end_ms)
        tuple_tokens(self.claim_ids,'object.claim_ids',0 if self.role=='decoration' else 1,128)

@dataclass(frozen=True, slots=True)
class Keyframe:
    time_ms: int
    value: int
    def __post_init__(self):
        integer(self.time_ms,'key.time_ms',0,MAX_TIME)
        integer(self.value,'key.value',-1_000_000_000,1_000_000_000)

@dataclass(frozen=True, slots=True)
class Track:
    track_id: str
    mode_id: str
    object_id: str
    property: str
    semantic_id: str
    purpose: str
    keyframes: tuple[Keyframe,...]
    interpolation: str = 'linear'
    def __post_init__(self):
        for n in ('track_id','mode_id','object_id','semantic_id','purpose'):token(getattr(self,n),n)
        choice(self.property,PROPERTIES,'track.property')
        rows(self.keyframes,Keyframe,'keyframes','time_ms',2,128)
        if tuple(sorted(self.keyframes,key=lambda k:k.time_ms))!=self.keyframes:
            raise ContractError('ANI_KEYFRAME_ORDER')
        choice(self.interpolation,('linear','step_end','cubic_bezier','spring','external'),'interpolation')
    @property
    def start_ms(self):return self.keyframes[0].time_ms
    @property
    def end_ms(self):return self.keyframes[-1].time_ms

@dataclass(frozen=True, slots=True)
class Cue:
    cue_id: str
    mode_id: str
    start_ms: int
    end_ms: int
    claim_ids: tuple[str,...]
    def __post_init__(self):
        token(self.cue_id,'cue_id');token(self.mode_id,'mode_id');interval(self.start_ms,self.end_ms)
        tuple_tokens(self.claim_ids,'cue.claim_ids',1,128)

@dataclass(frozen=True, slots=True)
class TrackRequirement:
    track_id: str
    mode_id: str
    object_id: str
    property: str
    semantic_id: str
    purpose: str
    claim_ids: tuple[str,...]
    essential: bool
    minimum_value: int
    maximum_value: int
    trend: str = 'any'
    start_value: int = 0
    end_value: int = 0
    endpoints_required: bool = False
    tolerance: int = 0
    disclosure_cue_ids: tuple[str,...] = ()
    def __post_init__(self):
        for n in ('track_id','mode_id','object_id','semantic_id','purpose'):token(getattr(self,n),n)
        choice(self.property,PROPERTIES,'requirement.property')
        tuple_tokens(self.claim_ids,'track.claim_ids',1,128)
        if type(self.essential) is not bool or type(self.endpoints_required) is not bool:raise ContractError('ANI_BOOLEAN_REQUIRED')
        integer(self.minimum_value,'minimum_value',-1_000_000_000,1_000_000_000)
        integer(self.maximum_value,'maximum_value',self.minimum_value,1_000_000_000)
        choice(self.trend,('any','increasing','decreasing','constant'),'trend')
        for n in ('start_value','end_value'):integer(getattr(self,n),n,-1_000_000_000,1_000_000_000)
        integer(self.tolerance,'tolerance',0,1_000_000)
        tuple_tokens(self.disclosure_cue_ids,'disclosure_cues',0,64)

@dataclass(frozen=True, slots=True)
class TimingRule:
    rule_id: str
    left_track_id: str
    right_id: str
    right_kind: str
    relation: str
    tolerance_ms: int = 0
    minimum_overlap_ms: int = 1
    def __post_init__(self):
        for n in ('rule_id','left_track_id','right_id'):token(getattr(self,n),n)
        choice(self.right_kind,('track','cue'),'right_kind')
        choice(self.relation,('before','after','start_sync','end_sync','covers','overlaps'),'relation')
        integer(self.tolerance_ms,'tolerance_ms',0,60000); integer(self.minimum_overlap_ms,'minimum_overlap_ms',1,MAX_TIME)
        if self.right_kind=='track' and self.left_track_id==self.right_id:raise ContractError('ANI_SELF_TIMING_RULE')

@dataclass(frozen=True, slots=True)
class Invariant:
    invariant_id: str
    mode_id: str
    kind: str
    track_ids: tuple[str,...]
    start_ms: int
    end_ms: int
    value: int
    tolerance: int = 0
    def __post_init__(self):
        token(self.invariant_id,'invariant_id');token(self.mode_id,'mode_id')
        choice(self.kind,('sum_constant','ordered','equal'),'invariant.kind')
        tuple_tokens(self.track_ids,'invariant.track_ids',2,16);interval(self.start_ms,self.end_ms)
        integer(self.value,'invariant.value',-1_000_000_000,1_000_000_000)
        integer(self.tolerance,'invariant.tolerance',0,1_000_000)

@dataclass(frozen=True, slots=True)
class MotionLimits:
    max_speed_mpx_per_second: int = 600_000
    max_rotation_mdeg_per_second: int = 180_000
    max_scale_ppm_per_second: int = 1_000_000
    max_opacity_ppm_per_second: int = 2_000_000
    max_progress_ppm_per_second: int = 1_000_000
    max_simultaneous_objects: int = 3
    max_sum_normalized_rate_ppm: int = 2_000_000
    max_jump_ppm: int = 250_000
    max_reversals: int = 4
    reduced_max_speed_mpx_per_second: int = 30_000
    reduced_max_rotation_mdeg_per_second: int = 10_000
    reduced_max_scale_ppm_per_second: int = 50_000
    reduced_max_jump_ppm: int = 10_000
    def __post_init__(self):
        for n,v in asdict(self).items():integer(v,n,0,1_000_000_000)
        if self.max_simultaneous_objects>256 or self.max_reversals>4096:raise ContractError('ANI_LIMIT_RANGE')

@dataclass(frozen=True, slots=True)
class CaptureRequirement:
    mode_id: str
    frame_indices: tuple[int,...]
    required: bool = False
    tolerance_mpx: int = 1500
    opacity_tolerance_ppm: int = 1000
    def __post_init__(self):
        token(self.mode_id,'mode_id')
        if type(self.frame_indices) is not tuple or not 2<=len(self.frame_indices)<=96:raise ContractError('ANI_CAPTURE_FRAME_COUNT')
        for v in self.frame_indices:integer(v,'frame_index',0,20_736_000)
        if tuple(sorted(set(self.frame_indices)))!=self.frame_indices:raise ContractError('ANI_CAPTURE_FRAME_ORDER')
        if type(self.required) is not bool:raise ContractError('ANI_BOOLEAN_REQUIRED')
        integer(self.tolerance_mpx,'capture_tolerance',0,10000);integer(self.opacity_tolerance_ppm,'opacity_tolerance',0,100000)

@dataclass(frozen=True, slots=True)
class CaptureRef:
    capture_id: str
    mode_id: str
    html: ArtifactRef
    observations: ArtifactRef
    screenshots: tuple[ArtifactRef,...]
    def __post_init__(self):
        token(self.capture_id,'capture_id');token(self.mode_id,'mode_id')
        if type(self.html) is not ArtifactRef or type(self.observations) is not ArtifactRef:raise ContractError('ANI_CAPTURE_REF_TYPE')
        rows(self.screenshots,ArtifactRef,'screenshots','artifact_id',2,96)
        refs=(self.html,self.observations)+self.screenshots
        if any(a.role!='support' for a in refs):raise ContractError('ANI_CAPTURE_ROLE')
        if len({a.artifact_id for a in refs})!=len(refs):raise ContractError('ANI_CAPTURE_ALIAS')

@dataclass(frozen=True, slots=True)
class AnimationRequest:
    schema_version: str
    source: Request
    lesson_id: str
    modes: tuple[Mode,...]
    objects: tuple[ObjectSpec,...]
    tracks: tuple[Track,...]
    cues: tuple[Cue,...] = ()
    captures: tuple[CaptureRef,...] = ()
    def __post_init__(self):
        choice(self.schema_version,('1.0.0',),'schema_version');token(self.lesson_id,'lesson_id')
        if type(self.source) is not Request:raise ContractError('ANI_SOURCE_TYPE')
        rows(self.modes,Mode,'modes','mode_id',1,8);rows(self.objects,ObjectSpec,'objects','object_id',1,128)
        rows(self.tracks,Track,'tracks','track_id',1,256);rows(self.cues,Cue,'cues','cue_id',0,256)
        rows(self.captures,CaptureRef,'captures','capture_id',0,8)
        if len({c.mode_id for c in self.captures})!=len(self.captures):raise ContractError('ANI_DUPLICATE_CAPTURE_MODE')
        ids=[t.track_id for t in self.tracks]+[c.cue_id for c in self.cues]
        if len(ids)!=len(set(ids)) or 'animation-scope' in ids:raise ContractError('ANI_ID_ALIAS')
        if sum(len(t.keyframes) for t in self.tracks)>8192:raise ContractError('ANI_KEYFRAME_WORK_LIMIT')
        if len(self.tracks)*sum(len(t.keyframes) for t in self.tracks)>1_048_576:raise ContractError('ANI_WORK_LIMIT')
        refs=[s.artifact for s in self.source.sources]+[o.artifact for o in self.source.outputs]
        refs += [a for c in self.captures for a in (c.html,c.observations)+c.screenshots]
        byid={};bypath={}
        for a in refs:
            if a.artifact_id in byid and byid[a.artifact_id]!=a or a.path in bypath and bypath[a.path]!=a:raise ContractError('ANI_ARTIFACT_ALIAS')
            byid[a.artifact_id]=a;bypath[a.path]=a
        if sum(a.size for a in byid.values())>64*1024*1024:raise ContractError('ANI_ARTIFACT_BYTE_BUDGET')
    @property
    def content_digest(self):return digest(asdict(self))
    @property
    def plan_digest(self):
        # Captures must not hash themselves. Final release binding is verified separately.
        d=asdict(self);d.pop('captures');d['source'].pop('candidate_digest')
        return digest(d)

@dataclass(frozen=True, slots=True)
class AnimationPolicy:
    policy_id: str
    source: Policy
    lesson_id: str
    modes: tuple[Mode,...]
    objects: tuple[ObjectSpec,...]
    tracks: tuple[TrackRequirement,...]
    cues: tuple[Cue,...] = ()
    timing_rules: tuple[TimingRule,...] = ()
    invariants: tuple[Invariant,...] = ()
    captures: tuple[CaptureRequirement,...] = ()
    limits: MotionLimits = MotionLimits()
    max_receipt_age_seconds: int = 3600
    minimum_review_confidence_ppm: int = 900000
    minimum_independent_assessors: int = 1
    def __post_init__(self):
        token(self.policy_id,'policy_id');token(self.lesson_id,'lesson_id')
        if type(self.source) is not Policy or type(self.limits) is not MotionLimits:raise ContractError('ANI_POLICY_TYPE')
        rows(self.modes,Mode,'modes','mode_id',1,8);rows(self.objects,ObjectSpec,'objects','object_id',1,128)
        rows(self.tracks,TrackRequirement,'requirements','track_id',1,256);rows(self.cues,Cue,'cues','cue_id',0,256)
        rows(self.timing_rules,TimingRule,'timing_rules','rule_id',0,512);rows(self.invariants,Invariant,'invariants','invariant_id',0,128)
        rows(self.captures,CaptureRequirement,'captures','mode_id',0,8)
        integer(self.max_receipt_age_seconds,'max_age',1,604800);integer(self.minimum_review_confidence_ppm,'minimum_confidence',0,1000000)
        integer(self.minimum_independent_assessors,'assessor_quorum',1,8)
        modes={m.mode_id:m for m in self.modes};objects={o.object_id:o for o in self.objects};tracks={t.track_id:t for t in self.tracks};cues={c.cue_id:c for c in self.cues}
        for t in self.tracks:
            if t.mode_id not in modes or t.object_id not in objects or not set(t.disclosure_cue_ids)<=set(cues):raise ContractError('ANI_POLICY_REFERENCE')
            if any(cues[c].mode_id!=t.mode_id for c in t.disclosure_cue_ids):raise ContractError('ANI_DISCLOSURE_MODE')
        for c in self.cues:
            if c.mode_id not in modes or c.end_ms>modes[c.mode_id].duration_ms:raise ContractError('ANI_POLICY_CUE_REFERENCE')
        for rule in self.timing_rules:
            right=tracks if rule.right_kind=='track' else cues
            if rule.left_track_id not in tracks or rule.right_id not in right:raise ContractError('ANI_POLICY_TIMING_REFERENCE')
            if tracks[rule.left_track_id].mode_id!=right[rule.right_id].mode_id:raise ContractError('ANI_POLICY_TIMING_MODE')
        for rule in self.invariants:
            if rule.mode_id not in modes or any(i not in tracks or tracks[i].mode_id!=rule.mode_id for i in rule.track_ids):raise ContractError('ANI_POLICY_INVARIANT_REFERENCE')
            if len({tracks[i].property for i in rule.track_ids})!=1:raise ContractError('ANI_INVARIANT_UNIT_MISMATCH')
            if rule.end_ms>modes[rule.mode_id].duration_ms:raise ContractError('ANI_INVARIANT_WINDOW')
        for c in self.captures:
            if c.mode_id not in modes:raise ContractError('ANI_POLICY_CAPTURE_MODE')
            m=modes[c.mode_id]
            if c.frame_indices[-1]*1000*m.fps.denominator>m.duration_ms*m.fps.numerator:raise ContractError('ANI_CAPTURE_FRAME_OUTSIDE_MODE')
        essential=[{t.semantic_id for t in self.tracks if t.mode_id==m.mode_id and t.essential} for m in self.modes]
        if any(s!=essential[0] for s in essential):raise ContractError('ANI_MODE_EDUCATIONAL_PARITY')
        if len(self.invariants)*len(self.tracks)*128>4_194_304:raise ContractError('ANI_INVARIANT_WORK_LIMIT')
    @property
    def content_digest(self):return digest(asdict(self))
