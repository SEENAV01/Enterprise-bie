"""HARD006 operator-owned inventories. No authority is decoded from a request.

Exact candidate bytes and requirements are pinned by the operator before audit.
Policy rotation invalidates every dependent closure (conservatively, not selectively).
These contracts do not discover arbitrary omitted source content or grant acceptance.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from ..release_v2.contracts import (ArtifactRef, ContractError, canonical_bytes, digest,
    token, tuple_tokens, sha256, integer, choice)
from ..publication_v2.report_policy import TerminalRequirement

INVENTORY_SCHEMA = 'bie.qa.authoritative-inventory/1'
CLOSURE_SCHEMA = 'bie.qa.obligation-closure/1'
AUTHORITY_SCHEMA = 'bie.qa.inventory-authority/1'
OPEN_STATUSES = ('OPEN','EXTERNAL_PENDING','PARTIALLY_ADDRESSED_OPEN','PENDING','BLOCKED')


def typed(values, cls, name, lower=0, upper=4096):
    if type(values) is not tuple or not lower <= len(values) <= upper or any(type(x) is not cls for x in values):
        raise ContractError('INVENTORY_TYPED_ARRAY', name)


@dataclass(frozen=True, slots=True)
class Obligation:
    obligation_id: str
    owner: str
    scope: str
    definition_digest: str
    required_check_ids: tuple[str,...]
    evaluator_policy_digest: str
    affected_artifact_ids: tuple[str,...]
    evidence_scope: str = 'NATIVE_PRODUCT'
    def __post_init__(self):
        for name in ('obligation_id','owner','scope'): token(getattr(self,name),name)
        for name in ('definition_digest','evaluator_policy_digest'): sha256(getattr(self,name),name)
        tuple_tokens(self.required_check_ids,'obligation.checks',1,4096)
        tuple_tokens(self.affected_artifact_ids,'obligation.artifacts',1,2048)
        choice(self.evidence_scope,('NATIVE_PRODUCT','DIAGNOSTIC'),'obligation.evidence_scope')
    def to_dict(self):
        d=asdict(self)
        for name in ('required_check_ids','affected_artifact_ids'):d[name]=sorted(d[name])
        return d


@dataclass(frozen=True, slots=True)
class ClosureKey:
    key_id: str
    principal_id: str
    independence_group: str
    secret: bytes = field(repr=False)
    obligation_ids: tuple[str,...] = ()
    not_before: int = 0
    not_after: int = 2**53-1
    enabled: bool = True
    assurance: str = 'test_only'
    def __post_init__(self):
        for name in ('key_id','principal_id','independence_group'):token(getattr(self,name),name)
        if type(self.secret) is not bytes or not 32<=len(self.secret)<=128:raise ContractError('CLOSURE_KEY_SECRET')
        tuple_tokens(self.obligation_ids,'key.obligations',1,4096)
        integer(self.not_before,'key.not_before');integer(self.not_after,'key.not_after',self.not_before+1)
        if type(self.enabled) is not bool:raise ContractError('CLOSURE_KEY_ENABLED')
        choice(self.assurance,('test_only','operator_managed'),'key.assurance')
    def public_dict(self):
        import hashlib
        return dict(key_id=self.key_id,principal_id=self.principal_id,independence_group=self.independence_group,
            credential_fingerprint=hashlib.sha256(self.secret).hexdigest(),obligation_ids=sorted(self.obligation_ids),
            not_before=self.not_before,not_after=self.not_after,enabled=self.enabled,assurance=self.assurance)


@dataclass(frozen=True, slots=True)
class InventoryAuthority:
    authority_id: str
    version: str
    profile: str
    artifacts: tuple[ArtifactRef,...]
    task_ids: tuple[str,...]
    check_requirements: tuple[TerminalRequirement,...]
    obligations: tuple[Obligation,...]
    closure_keys: tuple[ClosureKey,...] = field(default=(),repr=False)
    minimum_independent_closers: int = 1
    max_lifetime_seconds: int = 86400
    catalog_digest: str = ''
    def __post_init__(self):
        token(self.authority_id,'authority_id');token(self.version,'version')
        choice(self.profile,('DIAGNOSTIC','SECTION16'),'inventory.profile')
        typed(self.artifacts,ArtifactRef,'artifacts',1,2048)
        tuple_tokens(self.task_ids,'task_ids',1,512)
        typed(self.check_requirements,TerminalRequirement,'check_requirements',1,256)
        typed(self.obligations,Obligation,'obligations',0,2048)
        typed(self.closure_keys,ClosureKey,'closure_keys',0,128)
        integer(self.minimum_independent_closers,'closers',1,8)
        integer(self.max_lifetime_seconds,'inventory.max_lifetime',1,604800)
        sha256(self.catalog_digest,'catalog_digest')
        for rows,attr in ((self.artifacts,'artifact_id'),(self.artifacts,'path'),(self.obligations,'obligation_id'),(self.closure_keys,'key_id')):
            if len({getattr(x,attr) for x in rows})!=len(rows):raise ContractError('INVENTORY_DUPLICATE',attr)
        keys=[(r.subject_type,r.subject_id) for r in self.check_requirements]
        if len(keys)!=len(set(keys)):raise ContractError('INVENTORY_DUPLICATE_CHECK_SUBJECT')
        if any(r.subject_type not in ('gate','section_exit') for r in self.check_requirements):raise ContractError('INVENTORY_CHECK_SUBJECT')
        artifacts={a.artifact_id for a in self.artifacts};ids={o.obligation_id for o in self.obligations}
        if any(not set(o.affected_artifact_ids)<=artifacts for o in self.obligations):raise ContractError('INVENTORY_UNKNOWN_ARTIFACT')
        if any(not set(k.obligation_ids)<=ids for k in self.closure_keys):raise ContractError('INVENTORY_KEY_UNKNOWN_OBLIGATION')
        principals={};secrets={}
        for k in self.closure_keys:
            if k.principal_id in principals and principals[k.principal_id]!=k.independence_group:raise ContractError('CLOSURE_PRINCIPAL_GROUP')
            if k.secret in secrets and secrets[k.secret]!=(k.principal_id,k.independence_group):raise ContractError('CLOSURE_SHARED_SECRET')
            principals[k.principal_id]=k.independence_group;secrets[k.secret]=(k.principal_id,k.independence_group)
        if self.profile=='SECTION16':
            from .catalog import ORIGINAL_TASK_IDS,HARDENING_TASK_IDS,BASELINE_OBLIGATIONS,CATALOG_DIGEST
            if not set(ORIGINAL_TASK_IDS+HARDENING_TASK_IDS)<=set(self.task_ids):raise ContractError('SECTION16_TASK_BASELINE_MISSING')
            if not set(BASELINE_OBLIGATIONS)<=ids:raise ContractError('SECTION16_OBLIGATION_BASELINE_MISSING')
            for o in self.obligations:
                if o.obligation_id in BASELINE_OBLIGATIONS and o.definition_digest!=BASELINE_OBLIGATIONS[o.obligation_id]:
                    raise ContractError('SECTION16_OBLIGATION_DEFINITION_CHANGED')
            if self.catalog_digest!=CATALOG_DIGEST:raise ContractError('SECTION16_CATALOG_MISMATCH')
    def to_dict(self):
        return dict(schema_version=AUTHORITY_SCHEMA,authority_id=self.authority_id,version=self.version,profile=self.profile,
            artifacts=[a.to_dict() for a in sorted(self.artifacts,key=lambda a:a.artifact_id)],task_ids=sorted(self.task_ids),
            check_requirements=[r.to_dict() for r in sorted(self.check_requirements,key=lambda r:(r.subject_type,r.subject_id))],
            obligations=[o.to_dict() for o in sorted(self.obligations,key=lambda o:o.obligation_id)],
            closure_keys=[k.public_dict() for k in sorted(self.closure_keys,key=lambda k:k.key_id)],
            minimum_independent_closers=self.minimum_independent_closers,max_lifetime_seconds=self.max_lifetime_seconds,catalog_digest=self.catalog_digest)
    @property
    def content_digest(self):return digest(self.to_dict())


def closure_signing_bytes(raw:dict)->bytes:
    # Every field except the approvals (including evidence refs) is signed.
    return b'BIE-QA-OBLIGATION-CLOSURE-H2\x00'+canonical_bytes({k:v for k,v in raw.items() if k!='approvals'})
