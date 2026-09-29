"""REG001..005: operator-owned comparison scope, separate from candidate data."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from ..release_v2.contracts import (ArtifactRef, ContractError, token, integer,
    sha256, tuple_tokens, digest)
from ..repair_v2.models import Snapshot, seq, unique
from ..repair_audit_v2.models import Observation

@dataclass(frozen=True, slots=True)
class SuiteCheck:
    check_id: str
    validator_digest: str
    case_ids: tuple[str,...]
    fixture_ids: tuple[str,...]
    def __post_init__(self):
        token(self.check_id,'check_id');sha256(self.validator_digest,'validator_digest')
        if self.validator_digest=='0'*64:raise ContractError('REG_UNPINNED_VALIDATOR')
        tuple_tokens(self.case_ids,'case_ids',1,4096);tuple_tokens(self.fixture_ids,'fixture_ids',1,512)

@dataclass(frozen=True, slots=True)
class ChangePermit:
    artifact_id: str
    before_ref_digest: str
    after_ref_digest: str
    reason: str
    def __post_init__(self):
        token(self.artifact_id,'artifact_id')
        for x in (self.before_ref_digest,self.after_ref_digest):
            if x:sha256(x,'reference_digest')
        if not (self.before_ref_digest or self.after_ref_digest) or self.before_ref_digest==self.after_ref_digest:
            raise ContractError('REG_EMPTY_CHANGE_PERMIT')
        if type(self.reason) is not str or not self.reason.strip() or len(self.reason)>2048:
            raise ContractError('REG_CHANGE_REASON')

@dataclass(frozen=True, slots=True)
class SemanticRule:
    artifact_id: str
    required_claim_ids: tuple[str,...]
    required_concept_ids: tuple[str,...]
    def __post_init__(self):
        token(self.artifact_id,'artifact_id')
        tuple_tokens(self.required_claim_ids,'required_claim_ids',1,2048)
        tuple_tokens(self.required_concept_ids,'required_concept_ids',1,2048)

@dataclass(frozen=True, slots=True)
class Box:
    x: int
    y: int
    width: int
    height: int
    def __post_init__(self):
        integer(self.x,'x',0,8192);integer(self.y,'y',0,8192)
        integer(self.width,'width',1,8192);integer(self.height,'height',1,8192)
    def contains(self,x,y):return self.x<=x<self.x+self.width and self.y<=y<self.y+self.height
    def intersects(self,b):return self.x<b.x+b.width and b.x<self.x+self.width and self.y<b.y+b.height and b.y<self.y+self.height

@dataclass(frozen=True, slots=True)
class VisualRule:
    artifact_id: str
    sample_key: str
    width: int
    height: int
    channel_tolerance: int = 0
    changed_pixel_limit_ppm: int = 0
    masks: tuple[Box,...] = ()
    critical_regions: tuple[Box,...] = ()
    max_mask_ppm: int = 50000
    def __post_init__(self):
        token(self.artifact_id,'artifact_id');token(self.sample_key,'sample_key')
        integer(self.width,'width',1,4096);integer(self.height,'height',1,4096)
        if self.width*self.height>2097152:raise ContractError('REG_PIXEL_BUDGET')
        integer(self.channel_tolerance,'channel_tolerance',0,32)
        integer(self.changed_pixel_limit_ppm,'changed_pixel_limit_ppm',0,100000)
        integer(self.max_mask_ppm,'max_mask_ppm',0,100000)
        seq(self.masks,Box,'masks',0,32);seq(self.critical_regions,Box,'critical_regions',0,32)
        if len(set(self.masks))!=len(self.masks) or len(set(self.critical_regions))!=len(self.critical_regions):
            raise ContractError('REG_DUPLICATE_REGION')
        for b in self.masks+self.critical_regions:
            if b.x+b.width>self.width or b.y+b.height>self.height:raise ContractError('REG_REGION_OUTSIDE')
        if any(m.intersects(c) for m in self.masks for c in self.critical_regions):raise ContractError('REG_CRITICAL_MASK')
        # Conservative sum bound deliberately refuses excess overlap rather than
        # granting a larger mask. No candidate-supplied ignore zones exist.
        if sum(b.width*b.height for b in self.masks)*1000000>self.width*self.height*self.max_mask_ppm:
            raise ContractError('REG_MASK_BUDGET')

@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    seed: int
    action_ids: tuple[str,...]
    def __post_init__(self):
        token(self.scenario_id,'scenario_id');integer(self.seed,'seed',0,2147483647)
        seq(self.action_ids,str,'action_ids',1,4096)
        for a in self.action_ids:token(a,'action')
        if self.action_ids[0]!='INIT':raise ContractError('REG_INITIAL_ACTION')

@dataclass(frozen=True, slots=True)
class GameRule:
    artifact_id: str
    scenarios: tuple[Scenario,...]
    def __post_init__(self):
        token(self.artifact_id,'artifact_id');seq(self.scenarios,Scenario,'scenarios',1,128)
        if len({(s.scenario_id,s.seed) for s in self.scenarios})!=len(self.scenarios):raise ContractError('REG_DUPLICATE_SCENARIO')

@dataclass(frozen=True, slots=True)
class RegressionPolicy:
    policy_id: str
    checks: tuple[SuiteCheck,...]
    protected_artifact_ids: tuple[str,...]
    change_permits: tuple[ChangePermit,...]
    semantic: tuple[SemanticRule,...]
    visual: tuple[VisualRule,...]
    game: tuple[GameRule,...]
    max_receipt_age_seconds: int = 3600
    phase_timeout_seconds: int = 10
    max_evidence_bytes: int = 4194304
    def __post_init__(self):
        token(self.policy_id,'policy_id');seq(self.checks,SuiteCheck,'checks',1,128);unique(self.checks,'check_id','checks')
        tuple_tokens(self.protected_artifact_ids,'protected_artifact_ids',1,512)
        if not {x for c in self.checks for x in c.fixture_ids}<=set(self.protected_artifact_ids):raise ContractError('REG_FIXTURE_PROTECTION')
        seq(self.change_permits,ChangePermit,'change_permits',0,512);unique(self.change_permits,'artifact_id','change_permits')
        if set(self.protected_artifact_ids)&{p.artifact_id for p in self.change_permits}:raise ContractError('REG_PROTECTED_PERMIT')
        for name,cls in (('semantic',SemanticRule),('visual',VisualRule),('game',GameRule)):
            seq(getattr(self,name),cls,name,1,128);unique(getattr(self,name),'artifact_id',name)
        if sum(v.width*v.height for v in self.visual)>8388608:raise ContractError('REG_TOTAL_PIXEL_BUDGET')
        integer(self.max_receipt_age_seconds,'max_receipt_age_seconds',1,604800)
        integer(self.phase_timeout_seconds,'phase_timeout_seconds',1,60)
        integer(self.max_evidence_bytes,'max_evidence_bytes',1024,4194304)
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True, slots=True)
class RegressionRequest:
    comparison_id: str
    baseline: Snapshot
    candidate: Snapshot
    execution: ArtifactRef
    def __post_init__(self):
        token(self.comparison_id,'comparison_id')
        if type(self.baseline) is not Snapshot or type(self.candidate) is not Snapshot:raise ContractError('REG_SNAPSHOT_TYPE')
        if type(self.execution) is not ArtifactRef or self.execution.role!='report':raise ContractError('REG_EXECUTION_REF')
        for s in (self.baseline,self.candidate):
            if self.execution.artifact_id in {a.artifact_id for a in s.artifacts} or self.execution.path in {a.path for a in s.artifacts}:
                raise ContractError('REG_EXECUTION_ALIAS')
    @property
    def content_digest(self):return digest(asdict(self))

def binding(comparison_id,baseline,candidate,policy):
    token(comparison_id,'comparison_id')
    return dict(comparison_id=comparison_id,baseline_digest=baseline.content_digest,
        candidate_digest=candidate.content_digest,policy_digest=policy.content_digest)
