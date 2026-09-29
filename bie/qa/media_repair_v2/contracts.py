"""REPAIR008..011: operator-bound, data-only repair contracts.

No arbitrary Python/JS expressions, trust keys or executable names come from input.
Transforms produce proposals; they cannot rewrite observations, policies or source.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from ..release_v2.contracts import ArtifactRef,ContractError,token,integer,choice,sha256,digest,tuple_tokens
from ..repair_v2.models import mutable_path,seq,unique
from ..source_v2.models import Request,Policy
from ..visual_v2.models import Rect,VisualPolicy
from ..animation_v2.models import AnimationPolicy
from ..game_v2.models import GamePolicy

TASK_OWNERS={'BIE-QA-REPAIR-008':'VIS','BIE-QA-REPAIR-009':'ANI','BIE-QA-REPAIR-010':'COMP','BIE-QA-REPAIR-011':'GAME'}

@dataclass(frozen=True,slots=True)
class Limits:
    max_layout_visits:int=8192
    max_positions_per_object:int=256
    max_generated_bytes:int=2097152
    def __post_init__(self):
        integer(self.max_layout_visits,'layout_visits',1,100000)
        integer(self.max_positions_per_object,'positions',1,1024)
        integer(self.max_generated_bytes,'generated_bytes',1,16777216)
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class LayoutPermission:
    state_id:str
    object_id:str
    region:Rect
    max_shift_mpx:int
    def __post_init__(self):
        token(self.state_id,'state');token(self.object_id,'object')
        if type(self.region) is not Rect:raise ContractError('MEDIA_REPAIR_RECT_TYPE')
        integer(self.max_shift_mpx,'max_shift',0,32768000)

@dataclass(frozen=True,slots=True)
class VisualRepairPolicy:
    qa:VisualPolicy
    permissions:tuple[LayoutPermission,...]
    gap_mpx:int=1000
    def __post_init__(self):
        if type(self.qa) is not VisualPolicy:raise ContractError('MEDIA_REPAIR_VIS_POLICY')
        seq(self.permissions,LayoutPermission,'permissions',1,128)
        if len({(p.state_id,p.object_id) for p in self.permissions})!=len(self.permissions):raise ContractError('MEDIA_REPAIR_DUPLICATE_PERMISSION')
        states={s.state_id:s for s in self.qa.states}
        for p in self.permissions:
            if p.state_id not in states or p.object_id not in states[p.state_id].object_ids:raise ContractError('MEDIA_REPAIR_PERMISSION_SCOPE')
        integer(self.gap_mpx,'gap',0,1000000)
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class TrackWindow:
    track_id:str
    start_ms:int
    end_ms:int
    def __post_init__(self):
        token(self.track_id,'track');integer(self.start_ms,'start',0,86400000);integer(self.end_ms,'end',self.start_ms+1,86400000)

@dataclass(frozen=True,slots=True)
class AnimationRepairPolicy:
    qa:AnimationPolicy
    windows:tuple[TrackWindow,...]
    def __post_init__(self):
        if type(self.qa) is not AnimationPolicy:raise ContractError('MEDIA_REPAIR_ANI_POLICY')
        seq(self.windows,TrackWindow,'windows',1,256);unique(self.windows,'track_id','windows')
        if not {w.track_id for w in self.windows}<={t.track_id for t in self.qa.tracks}:raise ContractError('MEDIA_REPAIR_WINDOW_SCOPE')
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class ExportValue:
    name:str
    json_value:str
    def __post_init__(self):
        from .emitter import identifier,read_value
        identifier(self.name);read_value(self.json_value)

@dataclass(frozen=True,slots=True)
class CodePolicy:
    policy_id:str
    module_id:str
    source:Policy
    exports:tuple[ExportValue,...]
    source_claim_ids:tuple[str,...]
    def __post_init__(self):
        token(self.policy_id,'policy');token(self.module_id,'module')
        if type(self.source) is not Policy:raise ContractError('MEDIA_REPAIR_SOURCE_POLICY')
        seq(self.exports,ExportValue,'exports',1,256);unique(self.exports,'name','exports')
        tuple_tokens(self.source_claim_ids,'source_claim_ids',1,128)
        if sum(len(e.json_value) for e in self.exports)>1048576:raise ContractError('MEDIA_REPAIR_SPEC_LIMIT')
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class CodeRequest:
    schema_version:str
    source:Request
    module_id:str
    module:ArtifactRef
    def __post_init__(self):
        choice(self.schema_version,('1.0.0',),'schema_version');token(self.module_id,'module_id')
        if type(self.source) is not Request or type(self.module) is not ArtifactRef:raise ContractError('MEDIA_REPAIR_CODE_REQUEST')
        mutable_path(self.module.path)
        if self.module.role!='support' or not self.module.path.endswith('.ts'):raise ContractError('MEDIA_REPAIR_TS_MODULE_REQUIRED')
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class GameRepairPolicy:
    qa:GamePolicy
    def __post_init__(self):
        if type(self.qa) is not GamePolicy:raise ContractError('MEDIA_REPAIR_GAME_POLICY')
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class GameRepairRequest:
    schema_version:str
    source:Request
    game_id:str
    module:ArtifactRef
    def __post_init__(self):
        choice(self.schema_version,('1.0.0',),'schema_version');token(self.game_id,'game_id')
        if type(self.source) is not Request or type(self.module) is not ArtifactRef:raise ContractError('MEDIA_REPAIR_GAME_REQUEST')
        mutable_path(self.module.path)
        if self.module.role!='support' or not self.module.path.endswith('.ts'):raise ContractError('MEDIA_REPAIR_TS_MODULE_REQUIRED')
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class Job:
    job_id:str
    task_id:str
    request:ArtifactRef
    target:ArtifactRef
    snapshot_digest:str
    batch_digest:str
    repair_policy_digest:str
    domain_policy_digest:str
    limits_digest:str
    def __post_init__(self):
        token(self.job_id,'job');choice(self.task_id,tuple(TASK_OWNERS),'task')
        for a in (self.request,self.target):
            if type(a) is not ArtifactRef or a.role!='support':raise ContractError('MEDIA_REPAIR_JOB_ARTIFACT')
        mutable_path(self.target.path)
        if not self.request.path.endswith('.json'):raise ContractError('MEDIA_REPAIR_REQUEST_JSON')
        if self.task_id in ('BIE-QA-REPAIR-008','BIE-QA-REPAIR-009') and self.request!=self.target:raise ContractError('MEDIA_REPAIR_PLAN_TARGET')
        for k in ('snapshot_digest','batch_digest','repair_policy_digest','domain_policy_digest','limits_digest'):sha256(getattr(self,k),k)
    @property
    def content_digest(self):return digest(asdict(self))
