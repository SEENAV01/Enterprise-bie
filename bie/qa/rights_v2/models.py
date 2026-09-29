"""Operator-controlled rights scope and immutable, byte-bound candidate records.

The caller, not the candidate, provisions policy and reviewer trust. License
meanings, grantor authority, exclusions and intended-use mapping need external
review. This module does not determine copyright ownership or legal exceptions.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from ..release_v2.contracts import ContractError,token,integer,tuple_tokens,choice,sha256,digest
from ..source_v2.models import text
from ..repair_v2.models import Snapshot,seq,unique

OPERATIONS=('READ','EXTRACT','QUOTE','ADAPT','SYNC','EMBED','DISPLAY','DISTRIBUTE','TRAIN','RETRIEVE')
DIMENSIONS=('COPYRIGHT','VOICE','LIKENESS','TRADEMARK','PRIVACY','DATABASE','PROVIDER_TERMS','OTHER')
BASES=('LICENSE','PERMISSION','OWNERSHIP','PUBLIC_DOMAIN','EXCEPTION')
MAX_TIME=2**53-1

def labels(values,name,lo=0,hi=128):
    tuple_tokens(values,name,lo,hi)

def enums(values,allowed,name,lo=1):
    labels(values,name,lo,len(allowed))
    for v in values:choice(v,allowed,name)

def boolean(value,name):
    if type(value) is not bool:raise ContractError('RIGHTS_BOOLEAN',name)

@dataclass(frozen=True,slots=True)
class Material:
    material_id:str
    artifact_id:str
    category:str
    extent_id:str
    origin:str
    origin_reference:str
    license_expression:str
    parent_ids:tuple[str,...]=()
    dimensions:tuple[str,...]=('COPYRIGHT',)
    def __post_init__(self):
        for n in ('material_id','artifact_id','extent_id'):token(getattr(self,n),n)
        if len(self.material_id)>80:raise ContractError('RIGHTS_ID_LENGTH')
        choice(self.category,('SOURCE','ASSET'),'category')
        choice(self.origin,('THIRD_PARTY','OWNED_CLAIM','GENERATED','PUBLIC_DOMAIN_CLAIM','UNKNOWN'),'origin')
        text(self.origin_reference,'origin_reference',2048);text(self.license_expression,'license_expression',2048)
        labels(self.parent_ids,'parent_ids');enums(self.dimensions,DIMENSIONS,'dimensions')
        if self.material_id in self.parent_ids:raise ContractError('RIGHTS_LINEAGE_SELF_CYCLE')

@dataclass(frozen=True,slots=True)
class Obligation:
    obligation_id:str
    kind:str
    required_text:str
    def __post_init__(self):
        token(self.obligation_id,'obligation_id')
        choice(self.kind,('ATTRIBUTION','LICENSE_NOTICE','CHANGE_NOTICE','SOURCE_OFFER','CUSTOM'),'obligation_kind')
        text(self.required_text,'required_text',32768)

@dataclass(frozen=True,slots=True)
class Grant:
    grant_id:str
    material_id:str
    license_atom:str
    basis:str
    grantor_id:str
    evidence_ids:tuple[str,...]
    operations:tuple[str,...]
    dimensions:tuple[str,...]
    grantees:tuple[str,...]
    territories:tuple[str,...]
    channels:tuple[str,...]
    commercial_allowed:bool
    valid_from:int
    valid_until:int
    obligations:tuple[Obligation,...]=()
    allowed_output_licenses:tuple[str,...]=()
    def __post_init__(self):
        for n in ('grant_id','material_id','grantor_id'):token(getattr(self,n),n)
        if len(self.grant_id)>80:raise ContractError('RIGHTS_ID_LENGTH')
        text(self.license_atom,'license_atom',2048);choice(self.basis,BASES,'basis')
        labels(self.evidence_ids,'evidence_ids',1);enums(self.operations,OPERATIONS,'operations');enums(self.dimensions,DIMENSIONS,'dimensions')
        for n in ('grantees','territories','channels'):labels(getattr(self,n),n,1)
        boolean(self.commercial_allowed,'commercial_allowed')
        integer(self.valid_from,'valid_from');integer(self.valid_until,'valid_until',self.valid_from+1)
        seq(self.obligations,Obligation,'obligations',0,64);unique(self.obligations,'obligation_id','obligations')
        seq(self.allowed_output_licenses,str,'allowed_output_licenses',0,32)
        if len(set(self.allowed_output_licenses))!=len(self.allowed_output_licenses):raise ContractError('RIGHTS_OUTPUT_LICENSE_DUPLICATE')
        for s in self.allowed_output_licenses:text(s,'output_license',2048)

@dataclass(frozen=True,slots=True)
class UseRequirement:
    use_id:str
    material_id:str
    output_artifact_id:str
    operations:tuple[str,...]
    output_license:str
    notice_artifact_ids:tuple[str,...]=()
    def __post_init__(self):
        for n in ('use_id','material_id','output_artifact_id'):token(getattr(self,n),n)
        if len(self.use_id)>80:raise ContractError('RIGHTS_ID_LENGTH')
        enums(self.operations,OPERATIONS,'operations');text(self.output_license,'output_license',2048)
        labels(self.notice_artifact_ids,'notice_artifact_ids')

@dataclass(frozen=True,slots=True)
class RightsPolicy:
    policy_id:str
    snapshot_digest:str
    grantee_id:str
    territories:tuple[str,...]
    channels:tuple[str,...]
    commercial:bool
    planned_from:int
    planned_until:int
    materials:tuple[Material,...]
    grants:tuple[Grant,...]
    requirements:tuple[UseRequirement,...]
    max_receipt_age_seconds:int=3600
    max_status_age_seconds:int=3600
    def __post_init__(self):
        token(self.policy_id,'policy_id');sha256(self.snapshot_digest,'snapshot_digest');token(self.grantee_id,'grantee_id')
        for n in ('territories','channels'):labels(getattr(self,n),n,1)
        boolean(self.commercial,'commercial');integer(self.planned_from,'planned_from');integer(self.planned_until,'planned_until',self.planned_from+1)
        seq(self.materials,Material,'materials',1,256);seq(self.grants,Grant,'grants',0,512);seq(self.requirements,UseRequirement,'requirements',1,256)
        for name,key in [('materials','material_id'),('grants','grant_id'),('requirements','use_id')]:unique(getattr(self,name),key,name)
        mids={m.material_id for m in self.materials}
        if any(g.material_id not in mids for g in self.grants) or any(u.material_id not in mids for u in self.requirements):raise ContractError('RIGHTS_UNKNOWN_MATERIAL')
        graph={m.material_id:set(m.parent_ids) for m in self.materials};done=set()
        while len(done)<len(graph):
            ready={m for m,parents in graph.items() if m not in done and parents<=done}
            if not ready:raise ContractError('RIGHTS_LINEAGE_CYCLE_OR_MISSING_PARENT')
            done|=ready
        if {u.material_id for u in self.requirements}!=mids:raise ContractError('RIGHTS_UNUSED_MATERIAL_SCOPE')
        # The same underlying source/extent is not given conflicting identities.
        if len({(m.artifact_id,m.extent_id) for m in self.materials})!=len(self.materials):raise ContractError('RIGHTS_DUPLICATE_MATERIAL_EXTENT')
        integer(self.max_receipt_age_seconds,'max_receipt_age_seconds',1,604800)
        integer(self.max_status_age_seconds,'max_status_age_seconds',1,604800)
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class NoticeProof:
    grant_id:str
    obligation_id:str
    artifact_id:str
    start:int
    end:int
    def __post_init__(self):
        for n in ('grant_id','obligation_id','artifact_id'):token(getattr(self,n),n)
        integer(self.start,'notice_start',0,16777216);integer(self.end,'notice_end',self.start+1,16777216)

@dataclass(frozen=True,slots=True)
class UseSelection:
    use_id:str
    grant_ids:tuple[str,...]
    notices:tuple[NoticeProof,...]=()
    def __post_init__(self):
        token(self.use_id,'use_id');labels(self.grant_ids,'grant_ids',0,128)
        seq(self.notices,NoticeProof,'notices',0,512)
        if len({(n.grant_id,n.obligation_id) for n in self.notices})!=len(self.notices):raise ContractError('RIGHTS_DUPLICATE_NOTICE')

@dataclass(frozen=True,slots=True)
class RightsRequest:
    job_id:str
    snapshot:Snapshot
    status_artifact_id:str
    selections:tuple[UseSelection,...]
    def __post_init__(self):
        token(self.job_id,'job_id');token(self.status_artifact_id,'status_artifact_id')
        if type(self.snapshot) is not Snapshot:raise ContractError('RIGHTS_SNAPSHOT_TYPE')
        seq(self.selections,UseSelection,'selections',0,256);unique(self.selections,'use_id','selections')
        refs={a.artifact_id:a for a in self.snapshot.artifacts}
        if self.status_artifact_id not in refs or refs[self.status_artifact_id].role!='report':raise ContractError('RIGHTS_STATUS_ARTIFACT')
    @property
    def content_digest(self):return digest(asdict(self))
