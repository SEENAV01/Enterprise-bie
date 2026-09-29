"""REL001..004 typed publication contracts. No key or authority comes from input JSON."""
from __future__ import annotations
from dataclasses import asdict,dataclass,field
from typing import Any
from ..release_v2.contracts import (ArtifactRef, ContractError, EvidenceBundle, canonical_bytes,
    choice,digest,integer,sha256,token,tuple_tokens)
from ..release_v2.policy import ReleasePolicy,enterprise_policy
from ..release_v2.codec import _object,_no_float
import json
from .report_policy import TerminalRequirement, REGISTRY_VERSION
from ..governance_v2.contracts import InventoryAuthority

SCHEMA='bie.qa.publication/1'
PROOF_SCHEMA='bie.qa.release-proof/1'
EXIT_SCHEMA='bie.qa.section-exit/1'
PURPOSES=('inventory','evidence_and_section_exit','release_authorization')
STAGES=('audit','hardening','reaudit')
MAX_METADATA=4*1024*1024

def strict_json(data:bytes)->dict:
    if type(data)is not bytes or not 0<len(data)<=MAX_METADATA:raise ContractError('PUBLICATION_JSON_SIZE')
    try:
        value=json.loads(data.decode('utf-8'),object_pairs_hook=_object,parse_float=_no_float,parse_constant=_no_float)
        canonical_bytes(value)
        if type(value)is not dict:raise ContractError('PUBLICATION_JSON_OBJECT')
        return value
    except ContractError:raise
    except (ValueError,UnicodeError,RecursionError) as exc:raise ContractError('PUBLICATION_JSON_INVALID') from exc

def shape(value:Any,keys:tuple[str,...])->dict:
    if type(value)is not dict or set(value)!=set(keys):raise ContractError('PUBLICATION_FIELDS')
    return value

def seq(value:Any,name:str,limit:int=4096)->tuple:
    if type(value)is not list or len(value)>limit:raise ContractError('PUBLICATION_ARRAY',name)
    return tuple(value)

def typed_tuple(value,kind,name,maximum=4096):
    if type(value)is not tuple or len(value)>maximum or any(type(x)is not kind for x in value):
        raise ContractError('PUBLICATION_TYPED_TUPLE',name)

@dataclass(frozen=True,slots=True)
class Lineage:
    artifact_id:str
    parent_ids:tuple[str,...]
    def __post_init__(self):
        token(self.artifact_id,'lineage.artifact');tuple_tokens(self.parent_ids,'lineage.parents',1)

@dataclass(frozen=True,slots=True)
class OpenItem:
    item_id:str
    owner:str
    code:str
    artifact_ids:tuple[str,...]=()
    def __post_init__(self):
        for n in ('item_id','owner','code'):token(getattr(self,n),n)
        tuple_tokens(self.artifact_ids,'open_item.artifact_ids')

@dataclass(frozen=True,slots=True)
class PublicationRequest:
    schema_version:str
    release_id:str
    release_version:str
    bundle:EvidenceBundle
    lineage:tuple[Lineage,...]
    governance:tuple[ArtifactRef,...]=()
    open_items:tuple[OpenItem,...]=()
    inventory:ArtifactRef|None=None
    def __post_init__(self):
        if self.schema_version!=SCHEMA:raise ContractError('PUBLICATION_SCHEMA')
        token(self.release_id,'release_id');token(self.release_version,'release_version')
        if type(self.bundle)is not EvidenceBundle:raise ContractError('PUBLICATION_BUNDLE')
        typed_tuple(self.lineage,Lineage,'lineage',2048);typed_tuple(self.governance,ArtifactRef,'governance',3)
        typed_tuple(self.open_items,OpenItem,'open_items',2048)
        if self.inventory is not None and (type(self.inventory)is not ArtifactRef or self.inventory.role!='report'):raise ContractError('PUBLICATION_INVENTORY_REF')
        if any(a.role!='report' for a in self.governance):raise ContractError('PUBLICATION_GOVERNANCE_ROLE')
        for rows,attr in ((self.lineage,'artifact_id'),(self.governance,'artifact_id'),(self.open_items,'item_id')):
            if len({getattr(x,attr) for x in rows})!=len(rows):raise ContractError('PUBLICATION_DUPLICATE')
    def to_dict(self):
        return dict(schema_version=self.schema_version,release_id=self.release_id,release_version=self.release_version,
            bundle=self.bundle.to_dict(),lineage=[dict(artifact_id=x.artifact_id,parent_ids=sorted(x.parent_ids)) for x in sorted(self.lineage,key=lambda x:x.artifact_id)],
            governance=[x.to_dict() for x in sorted(self.governance,key=lambda x:x.artifact_id)],
            open_items=[asdict(x) for x in sorted(self.open_items,key=lambda x:x.item_id)],inventory=self.inventory.to_dict() if self.inventory else None)
    @property
    def content_digest(self):return digest(self.to_dict())

@dataclass(frozen=True,slots=True)
class PublicationPolicy:
    environment_id:str
    release_policy:ReleasePolicy=field(default_factory=enterprise_policy)
    mode:str='diagnostic'
    max_certificate_lifetime_seconds:int=3600
    max_review_lifetime_seconds:int=86400
    terminal_requirements:tuple[TerminalRequirement,...]=()
    inventory_authority:InventoryAuthority|None=None
    def __post_init__(self):
        token(self.environment_id,'environment_id')
        if self.inventory_authority is not None and type(self.inventory_authority)is not InventoryAuthority:raise ContractError('INVENTORY_AUTHORITY_TYPE')
        if type(self.release_policy)is not ReleasePolicy:raise ContractError('PUBLICATION_RELEASE_POLICY')
        choice(self.mode,('diagnostic','production'),'mode')
        integer(self.max_certificate_lifetime_seconds,'certificate_ttl',1,86400)
        integer(self.max_review_lifetime_seconds,'review_ttl',1,604800)
        typed_tuple(self.terminal_requirements,TerminalRequirement,'terminal_requirements',256)
        keys=[(r.subject_type,r.subject_id) for r in self.terminal_requirements]
        if len(keys)!=len(set(keys)):raise ContractError('DUPLICATE_TERMINAL_REQUIREMENT')
        gates={g.gate_id for g in self.release_policy.gates}
        if any(r.subject_id not in (gates if r.subject_type=='gate' else STAGES) for r in self.terminal_requirements):
            raise ContractError('UNKNOWN_TERMINAL_REQUIREMENT_SUBJECT')
    def to_dict(self):return dict(environment_id=self.environment_id,release_policy=self.release_policy.to_dict(),mode=self.mode,
        max_certificate_lifetime_seconds=self.max_certificate_lifetime_seconds,max_review_lifetime_seconds=self.max_review_lifetime_seconds,inventory_authority=self.inventory_authority.to_dict() if self.inventory_authority else None,terminal_registry_version=REGISTRY_VERSION,terminal_requirements=[r.to_dict() for r in sorted(self.terminal_requirements,key=lambda r:(r.subject_type,r.subject_id))])
    @property
    def content_digest(self):return digest(self.to_dict())

@dataclass(frozen=True,slots=True)
class Approval:
    approval_id:str
    purpose:str
    principal_id:str
    key_id:str
    assessment_digest:str
    created_at:int
    expires_at:int
    decision:str
    signature:str=''
    def __post_init__(self):
        for n in ('approval_id','principal_id','key_id'):token(getattr(self,n),n)
        choice(self.purpose,PURPOSES,'purpose');choice(self.decision,('APPROVE','REJECT'),'decision')
        sha256(self.assessment_digest,'assessment_digest');integer(self.created_at,'created_at');integer(self.expires_at,'expires_at',self.created_at+1)
        if self.signature:sha256(self.signature,'signature')
        elif type(self.signature)is not str:raise ContractError('PUBLICATION_SIGNATURE')
    def to_dict(self):return asdict(self)
    def signing_bytes(self):
        d=self.to_dict();del d['signature'];return b'BIE-RELEASE-APPROVAL-1\x00'+canonical_bytes(d)

@dataclass(frozen=True,slots=True)
class AuthorityKey:
    key_id:str
    principal_id:str
    secret:bytes=field(repr=False)
    purposes:tuple[str,...]=PURPOSES
    assurance:str='test_only'
    enabled:bool=True
    not_before:int=0
    not_after:int=2**53-1
    def __post_init__(self):
        token(self.key_id,'key_id');token(self.principal_id,'principal_id')
        if type(self.secret)is not bytes or not 32<=len(self.secret)<=128:raise ContractError('PUBLICATION_SECRET')
        tuple_tokens(self.purposes,'purposes',1,4)
        for p in self.purposes:choice(p,PURPOSES+('issuer',),'purpose')
        choice(self.assurance,('test_only','operator_managed'),'assurance')
        if type(self.enabled)is not bool:raise ContractError('PUBLICATION_ENABLED')
        integer(self.not_before,'key_start');integer(self.not_after,'key_end',self.not_before+1)
