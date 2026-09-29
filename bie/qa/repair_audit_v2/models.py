"""REPAIR012/013: immutable evidence and explicit, case-level repair obligations.

The operator supplies policies and executable registries outside candidate data.
A bounded local repair audit is never a full canonical regression or release.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from ..release_v2.contracts import (ArtifactRef, ContractError, token, integer,
    sha256, tuple_tokens, canonical_bytes, digest, choice)
from ..repair_v2.models import Snapshot, FailureBatch, Proposal, seq, unique

@dataclass(frozen=True, slots=True)
class CaseRule:
    check_id: str
    case_ids: tuple[str, ...]
    fixture_ids: tuple[str, ...]
    validator_digest: str
    def __post_init__(self):
        token(self.check_id, 'check_id')
        tuple_tokens(self.case_ids, 'case_ids', 1, 512)
        tuple_tokens(self.fixture_ids, 'fixture_ids', 1, 128)
        sha256(self.validator_digest, 'validator_digest')
        if self.validator_digest == '0'*64: raise ContractError('AUDIT_UNPINNED_VALIDATOR')

@dataclass(frozen=True, slots=True)
class TargetCase:
    failure_id: str
    check_id: str
    case_id: str
    def __post_init__(self):
        for k in ('failure_id', 'check_id', 'case_id'): token(getattr(self, k), k)

@dataclass(frozen=True, slots=True)
class AuditPolicy:
    policy_id: str
    checks: tuple[CaseRule, ...]
    targets: tuple[TargetCase, ...]
    protected_artifact_ids: tuple[str, ...]
    require_generation: bool = False
    max_receipt_age_seconds: int = 3600
    phase_timeout_seconds: int = 10
    max_evidence_bytes: int = 4194304
    def __post_init__(self):
        token(self.policy_id, 'policy_id')
        seq(self.checks, CaseRule, 'checks', 1, 128); unique(self.checks, 'check_id', 'checks')
        seq(self.targets, TargetCase, 'targets', 1, 4096)
        if len(set(self.targets)) != len(self.targets): raise ContractError('AUDIT_DUPLICATE_TARGET')
        rules={r.check_id: set(r.case_ids) for r in self.checks}
        if any(t.check_id not in rules or t.case_id not in rules[t.check_id] for t in self.targets):
            raise ContractError('AUDIT_UNKNOWN_TARGET_CASE')
        if len({(t.check_id,t.case_id) for t in self.targets}) != len(self.targets):
            raise ContractError('AUDIT_AMBIGUOUS_TARGET_CASE')
        tuple_tokens(self.protected_artifact_ids, 'protected_artifact_ids', 1, 512)
        if any(not set(r.fixture_ids) <= set(self.protected_artifact_ids) for r in self.checks):
            raise ContractError('AUDIT_FIXTURE_NOT_PROTECTED')
        if type(self.require_generation) is not bool: raise ContractError('AUDIT_BOOLEAN')
        integer(self.max_receipt_age_seconds, 'max_receipt_age_seconds', 1, 604800)
        integer(self.phase_timeout_seconds, 'phase_timeout_seconds', 1, 60)
        integer(self.max_evidence_bytes, 'max_evidence_bytes', 1024, 4194304)
    @property
    def content_digest(self): return digest(asdict(self))

@dataclass(frozen=True, slots=True)
class GenerationLink:
    job: ArtifactRef
    receipt: ArtifactRef
    domain_policy: ArtifactRef
    limits: ArtifactRef
    def __post_init__(self):
        for a in (self.job, self.receipt, self.domain_policy, self.limits):
            if type(a) is not ArtifactRef or a.role not in ('support','report'):
                raise ContractError('AUDIT_GENERATION_REF')

@dataclass(frozen=True, slots=True)
class AuditRequest:
    snapshot: Snapshot
    batch: FailureBatch
    proposal: Proposal
    attempt: ArtifactRef
    journal: ArtifactRef
    regression: ArtifactRef
    generation: tuple[GenerationLink, ...] = ()
    def __post_init__(self):
        for obj,cls in ((self.snapshot,Snapshot),(self.batch,FailureBatch),(self.proposal,Proposal)):
            if type(obj) is not cls: raise ContractError('AUDIT_INPUT_TYPE')
        for a in (self.attempt,self.journal,self.regression):
            if type(a) is not ArtifactRef or a.role != 'report': raise ContractError('AUDIT_REPORT_REF')
        seq(self.generation, GenerationLink, 'generation', 0, 1)
        refs=self.evidence_refs
        if len({a.artifact_id for a in refs})!=len(refs) or len({a.path for a in refs})!=len(refs):
            raise ContractError('AUDIT_EVIDENCE_ALIAS')
        current=self.snapshot.artifacts
        if {a.path for a in refs}&{a.path for a in current} or {a.artifact_id for a in refs}&{a.artifact_id for a in current}:
            raise ContractError('AUDIT_EVIDENCE_SNAPSHOT_ALIAS')
    @property
    def evidence_refs(self):
        refs=[self.attempt,self.journal,self.regression]
        for g in self.generation: refs.extend((g.job,g.receipt,g.domain_policy,g.limits))
        return tuple(refs)
    @property
    def content_digest(self): return digest(asdict(self))

@dataclass(frozen=True, slots=True)
class Observation:
    case_id: str
    status: str
    diagnostics: tuple[str, ...]
    witness: str
    def __post_init__(self):
        from ..source_v2.codec import loads
        token(self.case_id,'case_id'); choice(self.status,('PASS','FAIL','REVIEW','NOT_RUN','ERROR'),'status')
        tuple_tokens(self.diagnostics,'diagnostics',0,64)
        if (self.status=='PASS') != (not self.diagnostics): raise ContractError('AUDIT_CASE_REASON')
        if type(self.witness) is not str or not 2<=len(self.witness.encode('utf8'))<=32768:
            raise ContractError('AUDIT_CASE_WITNESS')
        obj=loads(self.witness.encode('utf8'))
        if type(obj) is not dict or not obj or canonical_bytes(obj).decode('utf8')!=self.witness:
            raise ContractError('AUDIT_CASE_WITNESS')
    @property
    def content_digest(self): return digest(asdict(self))

def candidate_for(snapshot: Snapshot, proposal: Proposal) -> Snapshot:
    """Derive exact permitted before/after bytes; no candidate-supplied inventory."""
    if type(snapshot) is not Snapshot or type(proposal) is not Proposal: raise ContractError('AUDIT_INPUT_TYPE')
    if (proposal.run_id,proposal.revision,proposal.base_digest)!=(snapshot.run_id,snapshot.revision,snapshot.content_digest):
        raise ContractError('AUDIT_BASE_BINDING')
    original={a.path:a for a in snapshot.artifacts}
    if any(r.path not in original or r.before_sha256!=original[r.path].sha256 for r in proposal.replacements):
        raise ContractError('AUDIT_REPLACEMENT_BINDING')
    changes={r.path:r.artifact for r in proposal.replacements}
    return Snapshot(snapshot.run_id,snapshot.revision,tuple(
        replace(a,sha256=changes[a.path].sha256,size=changes[a.path].size) if a.path in changes else a for a in snapshot.artifacts))

def run_binding(snapshot,proposal,repair_policy,audit_policy):
    return dict(run_id=snapshot.run_id,revision=snapshot.revision,base_digest=snapshot.content_digest,
        candidate_digest=candidate_for(snapshot,proposal).content_digest,proposal_digest=proposal.content_digest,
        repair_policy_digest=repair_policy.content_digest,audit_policy_digest=audit_policy.content_digest)
