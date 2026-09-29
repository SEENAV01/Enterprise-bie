"""REPAIR001..003: data-only repair governance; never a repository write contract.

Operator policy, reviewer keys and executable validators are supplied separately.
All identifiers/digests reuse the existing release/source evidence contracts.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from ..release_v2.contracts import (ArtifactRef, ContractError, token, integer,
    sha256, revision, choice, tuple_tokens, safe_relative_path, digest)

OWNERS = ('BI','KI','PR','RE','MATH','PED','DIR','VIS','ANI','COMP','AUDIO','GAME','INFRA','SEC','RIGHTS','QA')
CATEGORIES = ('CONTENT','ENVIRONMENT','EVIDENCE','SECURITY','RIGHTS','RESOURCE','UNKNOWN')
DENIED_ROOTS = ('bie','tests','evidence','history','policy','policies','task_registry','source','sources','docs')

def seq(v, cls, name, lo=0, hi=512):
    if type(v) is not tuple or not lo <= len(v) <= hi or any(type(x) is not cls for x in v):
        raise ContractError('REPAIR_COLLECTION', name)

def unique(v, key, name):
    if len({getattr(x,key) for x in v}) != len(v): raise ContractError('REPAIR_DUPLICATE',name)

def paths(v, name, lo=0):
    seq(v,str,name,lo)
    for p in v: safe_relative_path(p)
    if len(set(v)) != len(v): raise ContractError('REPAIR_DUPLICATE',name)

def mutable_path(p):
    safe_relative_path(p)
    if p.split('/')[0] in DENIED_ROOTS or any(x.startswith('.') for x in p.split('/')):
        raise ContractError('REPAIR_PROTECTED_PATH',p)
    # This lane replaces generated artifact files only, never canonical source/tests.
    if p.split('/')[0] != 'generated': raise ContractError('REPAIR_GENERATED_ROOT_REQUIRED',p)

@dataclass(frozen=True,slots=True)
class Snapshot:
    run_id: str
    revision: str
    artifacts: tuple[ArtifactRef,...]
    def __post_init__(self):
        token(self.run_id,'run_id');revision(self.revision)
        seq(self.artifacts,ArtifactRef,'artifacts',1);unique(self.artifacts,'path','paths');unique(self.artifacts,'artifact_id','ids')
        if sum(a.size for a in self.artifacts)>64*1024*1024: raise ContractError('REPAIR_SNAPSHOT_LIMIT')
        if any(a.size>16*1024*1024 for a in self.artifacts): raise ContractError('REPAIR_ARTIFACT_LIMIT')
    @property
    def content_digest(self):
        return digest(dict(run_id=self.run_id,revision=self.revision,
            artifacts=[asdict(a) for a in sorted(self.artifacts,key=lambda a:a.path)]))

@dataclass(frozen=True,slots=True)
class BoundReport:
    artifact: ArtifactRef
    task_id: str
    request_digest: str
    evaluator_policy_digest: str
    def __post_init__(self):
        if type(self.artifact) is not ArtifactRef or self.artifact.role!='report': raise ContractError('REPAIR_REPORT_REF')
        token(self.task_id,'task_id');sha256(self.request_digest,'request_digest');sha256(self.evaluator_policy_digest,'evaluator_policy_digest')

@dataclass(frozen=True,slots=True)
class FailureBatch:
    run_id: str
    revision: str
    snapshot_digest: str
    reports: tuple[BoundReport,...]
    def __post_init__(self):
        token(self.run_id,'run_id');revision(self.revision);sha256(self.snapshot_digest,'snapshot_digest')
        seq(self.reports,BoundReport,'reports',1,128)
        if len({r.artifact.path for r in self.reports})!=len(self.reports) or len({r.artifact.artifact_id for r in self.reports})!=len(self.reports): raise ContractError('REPAIR_DUPLICATE_REPORT')
        if len({r.task_id for r in self.reports})!=len(self.reports): raise ContractError('REPAIR_DUPLICATE_TASK_REPORT')
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class FailureRule:
    task_id: str
    code: str
    category: str
    owner: str
    automatic: bool
    def __post_init__(self):
        token(self.task_id,'task_id');token(self.code,'code');choice(self.category,CATEGORIES,'category');choice(self.owner,OWNERS,'owner')
        if type(self.automatic) is not bool:raise ContractError('REPAIR_BOOLEAN')
        if self.automatic and self.category!='CONTENT':raise ContractError('REPAIR_NONCONTENT_AUTOMATION')

@dataclass(frozen=True,slots=True)
class CheckNode:
    check_id: str
    dependencies: tuple[str,...]
    validator_digest: str = '0'*64
    def __post_init__(self):
        token(self.check_id,'check_id');tuple_tokens(self.dependencies,'dependencies',0,128);sha256(self.validator_digest,'validator_digest')

@dataclass(frozen=True,slots=True)
class OwnerRoute:
    owner: str
    mutable_paths: tuple[str,...]
    check_ids: tuple[str,...]
    def __post_init__(self):
        choice(self.owner,OWNERS,'owner');paths(self.mutable_paths,'mutable_paths',1)
        for p in self.mutable_paths:mutable_path(p)
        tuple_tokens(self.check_ids,'check_ids',1,128)

@dataclass(frozen=True,slots=True)
class RepairPolicy:
    policy_id: str
    rules: tuple[FailureRule,...]
    routes: tuple[OwnerRoute,...]
    checks: tuple[CheckNode,...]
    required_checks: tuple[str,...]
    max_attempts: int = 3
    max_replacement_bytes: int = 2*1024*1024
    max_total_replacement_bytes: int = 8*1024*1024
    max_changed_files: int = 8
    worker_timeout_seconds: int = 10
    max_total_worker_seconds: int = 60
    max_receipt_age_seconds: int = 3600
    def __post_init__(self):
        token(self.policy_id,'policy_id');seq(self.rules,FailureRule,'rules',1,4096);seq(self.routes,OwnerRoute,'routes',1,16)
        seq(self.checks,CheckNode,'checks',1,128);unique(self.routes,'owner','routes');unique(self.checks,'check_id','checks')
        if len({(r.task_id,r.code) for r in self.rules})!=len(self.rules):raise ContractError('REPAIR_AMBIGUOUS_RULE')
        owned=[p for r in self.routes for p in r.mutable_paths]
        if len(set(owned))!=len(owned):raise ContractError('REPAIR_AMBIGUOUS_PATH_OWNER')
        ids={c.check_id for c in self.checks};owners={r.owner for r in self.routes}
        tuple_tokens(self.required_checks,'required_checks',1,128)
        if not set(self.required_checks)<=ids or any(not set(r.check_ids)<=ids for r in self.routes):raise ContractError('REPAIR_UNKNOWN_CHECK')
        if any(r.automatic and r.owner not in owners for r in self.rules):raise ContractError('REPAIR_MISSING_OWNER_ROUTE')
        graph={c.check_id:c.dependencies for c in self.checks};done=set()
        while len(done)<len(graph):
            ready={k for k,v in graph.items() if k not in done and set(v)<=done}
            if not ready:raise ContractError('REPAIR_CHECK_CYCLE_OR_MISSING_DEPENDENCY')
            done|=ready
        for key,lo,hi in (('max_attempts',1,20),('max_replacement_bytes',1,16*1024*1024),('max_total_replacement_bytes',1,64*1024*1024),('max_changed_files',1,64),('worker_timeout_seconds',1,60),('max_total_worker_seconds',1,1200),('max_receipt_age_seconds',1,604800)):
            integer(getattr(self,key),key,lo,hi)
        if self.max_replacement_bytes>self.max_total_replacement_bytes:raise ContractError('REPAIR_BUDGET_INCONSISTENT')
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class Failure:
    failure_id: str
    task_id: str
    code: str
    subject_id: str
    severity: str
    category: str
    owner: str
    automatic: bool
    report_sha256: str
    def __post_init__(self):
        for k in ('failure_id','task_id','code','subject_id'):token(getattr(self,k),k)
        choice(self.severity,('BLOCKER','REVIEW'),'severity');choice(self.category,CATEGORIES,'category');choice(self.owner,OWNERS,'owner');sha256(self.report_sha256,'report_sha256')
        if type(self.automatic) is not bool:raise ContractError('REPAIR_BOOLEAN')

@dataclass(frozen=True,slots=True)
class RepairPlan:
    batch_digest: str
    snapshot_digest: str
    policy_digest: str
    failures: tuple[Failure,...]
    inspected_report_ids: tuple[str,...]
    authenticated: bool
    diagnostics: tuple[str,...]
    def __post_init__(self):
        for k in ('batch_digest','snapshot_digest','policy_digest'):sha256(getattr(self,k),k)
        seq(self.failures,Failure,'failures',0,4096);unique(self.failures,'failure_id','failures')
        tuple_tokens(self.inspected_report_ids,'reports',0,128);tuple_tokens(self.diagnostics,'diagnostics',0,256)
        if type(self.authenticated) is not bool:raise ContractError('REPAIR_BOOLEAN')
    @property
    def content_digest(self):return digest(asdict(self))
    @property
    def status(self):
        if self.diagnostics or not self.authenticated:return 'REVIEW_REQUIRED'
        if not self.failures:return 'NO_REPAIR_NEEDED'
        return 'ROUTED' if any(f.automatic for f in self.failures) else 'ESCALATION_REQUIRED'
    def to_dict(self):return dict(**asdict(self),status=self.status,product_accepted=False)

@dataclass(frozen=True,slots=True)
class Replacement:
    path: str
    before_sha256: str
    artifact: ArtifactRef
    def __post_init__(self):
        mutable_path(self.path);sha256(self.before_sha256,'before_sha256')
        if type(self.artifact) is not ArtifactRef or self.artifact.role not in ('support','video','game'):raise ContractError('REPAIR_REPLACEMENT_ROLE')

@dataclass(frozen=True,slots=True)
class Proposal:
    proposal_id: str
    run_id: str
    revision: str
    base_digest: str
    policy_digest: str
    plan_digest: str
    owner: str
    target_failure_ids: tuple[str,...]
    replacements: tuple[Replacement,...]
    def __post_init__(self):
        token(self.proposal_id,'proposal_id');token(self.run_id,'run_id');revision(self.revision);choice(self.owner,OWNERS,'owner')
        for k in ('base_digest','policy_digest','plan_digest'):sha256(getattr(self,k),k)
        tuple_tokens(self.target_failure_ids,'targets',1,4096);seq(self.replacements,Replacement,'replacements',1,64);unique(self.replacements,'path','replacement.paths')
        refs=[r.artifact for r in self.replacements]
        if len({a.artifact_id for a in refs})!=len(refs) or len({a.path for a in refs})!=len(refs):raise ContractError('REPAIR_REPLACEMENT_ALIAS')
    @property
    def content_digest(self):return digest(asdict(self))
    @property
    def effect_digest(self):
        return digest(dict(base=self.base_digest,changes=sorted((r.path,r.before_sha256,r.artifact.sha256) for r in self.replacements)))

@dataclass(frozen=True,slots=True)
class CheckOutcome:
    check_id: str
    candidate_digest: str
    policy_digest: str
    status: str
    diagnostics: tuple[str,...]
    witness_digest: str
    def __post_init__(self):
        token(self.check_id,'check_id');sha256(self.candidate_digest,'candidate_digest');sha256(self.policy_digest,'policy_digest');sha256(self.witness_digest,'witness_digest')
        choice(self.status,('PASS','FAIL','REVIEW','NOT_RUN','ERROR'),'status');tuple_tokens(self.diagnostics,'diagnostics',0,128)
        if self.status!='PASS' and not self.diagnostics:raise ContractError('REPAIR_MISSING_CHECK_REASON')
