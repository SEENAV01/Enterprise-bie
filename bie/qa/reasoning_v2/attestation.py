"""Purpose-scoped, content-bound review authentication. No built-in trusted keys.

A shared-secret adapter authenticates an operator-provisioned reviewer; it does
not prove reviewer correctness, independence, calibration or remote execution.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from types import MappingProxyType
import hmac, hashlib
from ..release_v2.contracts import ContractError, token, integer, choice, tuple_tokens, sha256, canonical_bytes, digest
from ..source_v2.models import text
from ..semantic_v2.attestation import Authentication
from .models import ReasoningRequest, ReasoningPolicy
PURPOSES=('inventory','teaching','mastery','mapping','inference','support','calibration','disclosure')

@dataclass(frozen=True, slots=True)
class Review:
    review_id: str
    request_digest: str
    policy_digest: str
    subject_id: str
    purpose: str
    verdict: str
    evidence_ids: tuple[str,...]
    confidence_ppm: int
    rationale: str
    evaluator_id: str
    evaluator_version: str
    issued_at: int
    expires_at: int
    key_id: str
    signature: str = ''
    def __post_init__(self):
        for f in ('review_id','subject_id','evaluator_id','evaluator_version','key_id'):token(getattr(self,f),f)
        for f in ('request_digest','policy_digest'):sha256(getattr(self,f),f)
        choice(self.purpose,PURPOSES,'purpose');choice(self.verdict,('VERIFIED','REJECTED','UNCERTAIN'),'verdict')
        tuple_tokens(self.evidence_ids,'review.evidence_ids',1,4096)
        integer(self.confidence_ppm,'review.confidence_ppm',0,1000000);text(self.rationale,'rationale',8192)
        integer(self.issued_at,'issued_at');integer(self.expires_at,'expires_at',self.issued_at+1)
        if type(self.signature) is not str:raise ContractError('INVALID_REVIEW_SIGNATURE')
        if self.signature:sha256(self.signature,'signature')
    def signing_bytes(self):
        d=asdict(self);del d['signature']
        return b'BIE-QA-PR-RE-REVIEW-V1\x00'+canonical_bytes(d)

@dataclass(frozen=True, slots=True)
class ReviewKey:
    key_id: str
    secret: bytes = field(repr=False)
    evaluator_id: str
    evaluator_version: str
    independence_group: str
    purposes: tuple[str,...]
    assurance: str = 'test_only'
    enabled: bool = True
    def __post_init__(self):
        for f in ('key_id','evaluator_id','evaluator_version','independence_group'):token(getattr(self,f),f)
        if type(self.secret) is not bytes or not 32<=len(self.secret)<=128:raise ContractError('INVALID_REVIEW_KEY')
        tuple_tokens(self.purposes,'purposes',1,len(PURPOSES))
        for p in self.purposes:choice(p,PURPOSES,'purpose')
        choice(self.assurance,('test_only','operator_managed'),'assurance')
        if type(self.enabled) is not bool:raise ContractError('INVALID_REVIEW_KEY_STATE')

class ReviewVerifier:
    def __init__(self, keys: tuple[ReviewKey,...]=()):
        if type(keys) is not tuple or len(keys)>1024 or any(type(k) is not ReviewKey for k in keys):raise ContractError('INVALID_REVIEW_KEYS')
        if len({k.key_id for k in keys})!=len(keys):raise ContractError('DUPLICATE_REVIEW_KEY')
        groups={};secrets={}
        for k in keys:
            if k.evaluator_id in groups and groups[k.evaluator_id]!=k.independence_group:raise ContractError('INCONSISTENT_REVIEW_INDEPENDENCE')
            fp=hashlib.sha256(k.secret).hexdigest()
            if fp in secrets and secrets[fp]!=k.independence_group:raise ContractError('SHARED_SECRET_NOT_INDEPENDENT')
            groups[k.evaluator_id]=k.independence_group;secrets[fp]=k.independence_group
        self._keys=MappingProxyType({k.key_id:k for k in keys})
    @property
    def configuration_digest(self):
        return digest([dict(key_id=k.key_id,fingerprint=hashlib.sha256(k.secret).hexdigest(),evaluator_id=k.evaluator_id,
            evaluator_version=k.evaluator_version,independence_group=k.independence_group,purposes=k.purposes,
            assurance=k.assurance,enabled=k.enabled) for k in sorted(self._keys.values(),key=lambda k:k.key_id)])
    def verify(self,review: Review,request: ReasoningRequest,policy: ReasoningPolicy,now: int):
        if type(request) is not ReasoningRequest or type(policy) is not ReasoningPolicy:raise ContractError('INVALID_REVIEW_CONTEXT')
        return self.verify_bound(review,request.content_digest,policy.content_digest,policy.max_receipt_age_seconds,now)
    def verify_bound(self,a,request_digest,policy_digest,max_age,now):
        if type(a) is not Review:raise ContractError('INVALID_REVIEW')
        integer(now,'now');integer(max_age,'max_age',1,604800)
        sha256(request_digest,'request_digest');sha256(policy_digest,'policy_digest')
        k=self._keys.get(a.key_id);code='AUTHENTICATED'
        if a.request_digest!=request_digest:code='REVIEW_REQUEST_MISMATCH'
        elif a.policy_digest!=policy_digest:code='REVIEW_POLICY_MISMATCH'
        elif a.issued_at>now or a.expires_at<=now:code='REVIEW_TIME_INVALID'
        elif now-a.issued_at>max_age or a.expires_at-a.issued_at>max_age:code='REVIEW_LIFETIME_EXCEEDED'
        elif k is None:code='UNKNOWN_REVIEW_KEY'
        elif not k.enabled:code='REVOKED_REVIEW_KEY'
        elif (a.evaluator_id,a.evaluator_version)!=(k.evaluator_id,k.evaluator_version):code='UNAUTHORIZED_REVIEWER'
        elif a.purpose not in k.purposes:code='UNAUTHORIZED_REVIEW_PURPOSE'
        elif not hmac.compare_digest(a.signature,hmac.new(k.secret,a.signing_bytes(),hashlib.sha256).hexdigest()):code='BAD_REVIEW_SIGNATURE'
        ok=code=='AUTHENTICATED'
        return Authentication(code,ok,bool(ok and k.assurance=='operator_managed'),k.independence_group if ok else '')


def review_targets(request: ReasoningRequest):
    """Exact required evidence identities; authority remains external."""
    statements={s.statement_id:s for s in request.statements}
    targets={('inventory','reasoning-scope'):tuple(sorted(c.claim_id for c in request.source.claims))}
    for e in request.events:
        if e.kind in ('teach','bridge'):targets[('teaching',e.event_id)]=tuple(sorted(e.claim_ids))
    for m in request.masteries:targets[('mastery',m.observation_id)]=(m.artifact.artifact_id,)
    for a in request.arguments:targets[('mapping',a.argument_id)]=tuple(sorted({statements[s].claim_id for s in a.statement_ids if s in statements}))
    for step in request.steps:
        if step.method!='deductive':targets[('inference',step.step_id)]=tuple(sorted({statements[s].claim_id for s in step.premise_ids+(step.conclusion_id,) if s in statements}))
    for e in request.evidence:targets[('support',e.evidence_id)]=tuple(sorted(e.citation_ids))
    for c in request.calibrations:targets[('calibration',c.calibration_id)]=(c.artifact.artifact_id,)
    for d in request.decisions:
        if d.disclosure_claim_ids:targets[('disclosure',d.argument_id)]=tuple(sorted(d.disclosure_claim_ids))
    return targets
