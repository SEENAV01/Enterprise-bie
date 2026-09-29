"""HARD041: rights-safe correction-memory export, never implicit training/reuse.

Actual before/after/source/validation bytes are re-read. An independently reviewed
correction is a retrieval candidate, not fact proof or reusable PASS evidence.
Export writes one new file only. No mutation of model memory, datasets or GitHub.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from .common import *
from .authority import AuthoritySession
from .rights import verify_inventory

@dataclass(frozen=True)
class RightsContext:
    request:object
    root:object
    rights_policy:object
    inventory_policy:object
    binding:Binding
    legacy_reviews:tuple=()
    legacy_verifier:object=None
    session:object=None
    clearance:object=None
    observations:tuple=()
    capture_root:object=None
    def verify(self):
        require(type(self.session) is AuthoritySession,'H8_MEMORY_RIGHTS_SESSION')
        lo,hi=self.session.window()
        return verify_inventory(self.request,self.root,self.rights_policy,self.inventory_policy,self.binding,
            as_of=(hi+999)//1000,legacy_reviews=self.legacy_reviews,legacy_verifier=self.legacy_verifier,
            session=self.session,clearance=self.clearance,observations=self.observations,capture_root=self.capture_root)

@dataclass(frozen=True)
class CorrectionPlan:
    correction_id:str
    source:ArtifactRef
    before:ArtifactRef
    after:ArtifactRef
    validation:ArtifactRef
    domain:str
    language:str
    audience:str
    source_revision:str
    required_cases:tuple[str,...]
    target_cases:tuple[str,...]
    rerun_gates:tuple[str,...]
    rights_scope_digest:str
    max_export_bytes:int=1024*1024
    def __post_init__(self):
        for n in ('correction_id','domain','language','audience','source_revision'):token(getattr(self,n),n)
        for n in ('source','before','after','validation'):require(type(getattr(self,n)) is ArtifactRef,'H8_CORRECTION_REF')
        require(self.source.role=='source' and self.validation.role=='report','H8_CORRECTION_ROLE')
        require(len({getattr(self,n).artifact_id for n in ('source','before','after','validation')})==4,'H8_CORRECTION_ALIAS')
        require(self.before.sha256!=self.after.sha256,'H8_CORRECTION_NO_CHANGE')
        exact_strings(self.required_cases,'H8_CORRECTION_CASES',1);exact_strings(self.target_cases,'H8_CORRECTION_TARGETS',1)
        require(set(self.target_cases)<=set(self.required_cases),'H8_TARGET_NOT_REGISTERED')
        exact_strings(self.rerun_gates,'H8_REUSE_GATES',1)
        require({'source','semantic','regression'}<=set(self.rerun_gates),'H8_REUSE_GATE_WAIVER')
        sha256(self.rights_scope_digest,'rights.scope');integer(self.max_export_bytes,'export.limit',1,4*1024*1024)
    @property
    def content_digest(self):return digest(asdict(self))

def correction_subject(plan,binding):
    return digest({'plan':asdict(plan),'binding':asdict(binding),'operation':'export_correction'})

def inspect_correction(root,plan,binding):
    require(type(plan) is CorrectionPlan and type(binding) is Binding and binding.policy_digest==plan.content_digest,'H8_CORRECTION_BINDING')
    blobs={}
    for name in ('source','before','after','validation'):
        a=getattr(plan,name);data=regular_bytes(root,a.path)
        require(identity(data)==a.sha256 and len(data)==a.size,'H8_CORRECTION_BYTES_CHANGED');blobs[name]=data
    require(len(blobs['after'])<=plan.max_export_bytes,'H8_CORRECTION_EXPORT_LIMIT')
    v=strict_object(blobs['validation'])
    fields(v,('schema_version','source_sha256','before_sha256','after_sha256','revision','cases','conditions_preserved'),'H8_CORRECTION_VALIDATION_FIELDS')
    require(v['schema_version']=='bie.qa.correction-validation/1','H8_CORRECTION_VALIDATION_SCHEMA')
    require(v['source_sha256']==plan.source.sha256 and v['before_sha256']==plan.before.sha256 and
        v['after_sha256']==plan.after.sha256 and v['revision']==binding.revision,'H8_CORRECTION_VALIDATION_BINDING')
    require(v['conditions_preserved'] is True,'H8_CORRECTION_LOST_CONDITIONS')
    rows=v['cases'];require(type(rows) is list and len(rows)==len(plan.required_cases),'H8_CORRECTION_CASE_CENSUS')
    require({r['case_id'] for r in rows}==set(plan.required_cases),'H8_CORRECTION_CASE_CENSUS')
    for r in rows:
        fields(r,('case_id','before','after'),'H8_CORRECTION_CASE_FIELDS')
        require(r['before'] in ('PASS','FAIL') and r['after']=='PASS','H8_CORRECTION_REGRESSION')
        if r['case_id'] in plan.target_cases:require(r['before']=='FAIL','H8_CORRECTION_FAILURE_NOT_REPRODUCED')
    return blobs,v

def prepare_export(root,output,plan,binding,*,rights,session,envelopes):
    blobs,validation=inspect_correction(root,plan,binding)
    require(type(rights) is RightsContext and type(session) is AuthoritySession and session.binding==binding,'H8_CORRECTION_AUTHORITY')
    rr=rights.verify()
    require(rr['technical_checks_clear'] and not any(f['severity']!='ADVISORY' for f in rr['report']['findings']
        if f['code']!='OPERATIONAL_INDEPENDENT_ACCEPTANCE_REQUIRED'),'H8_CORRECTION_RIGHTS_NOT_CLEARED')
    require(rr['details']['rights_scope_digest']==plan.rights_scope_digest,'H8_CORRECTION_RIGHTS_BINDING')
    materials={m.material_id:m for m in rights.rights_policy.materials}
    retrieved={materials[u.material_id].artifact_id for u in rights.rights_policy.requirements if 'RETRIEVE' in u.operations}
    require({plan.source.artifact_id,plan.after.artifact_id}<=retrieved,'H8_CORRECTION_RETRIEVAL_NOT_PERMITTED')
    expected_refs={a.artifact_id:a for a in rights.request.snapshot.artifacts}
    for a in (plan.source,plan.after):require(expected_refs.get(a.artifact_id)==a,'H8_CORRECTION_PERMISSION_BYTES')
    who=session.verify_roles(envelopes,correction_subject(plan,binding),required=('review','memory'))
    try:correction_text=blobs['after'].decode('utf-8')
    except UnicodeError as exc:raise ContractError('H8_CORRECTION_TEXT_ENCODING') from exc
    record={'schema_version':'bie.qa.correction-export/1','plan':asdict(plan),'binding':asdict(binding),
        'correction_text':correction_text,'validation_digest':identity(blobs['validation']),
        'rights_result_digest':digest(rr),'rights_scope_digest':plan.rights_scope_digest,
        'approval_identities':who,'approval_envelopes':list(envelopes),
        'diagnostic_only':session.policy.mode=='diagnostic' or rights.session.policy.mode=='diagnostic',
        'rerun_gates':list(plan.rerun_gates),'training_allowed':False,'automatic_ingestion':False,
        'retrieval_candidate_only':True,'product_accepted':False}
    record['content_digest']=digest(record)
    output=Path(output).absolute()
    require(not output.is_relative_to(Path(root).absolute()),'H8_EXPORT_OVERLAPS_SOURCE')
    write_new(output,record)
    # Return bytes metadata, never invoke code from the exported content.
    return {'status':'DIAGNOSTIC_EXPORT' if record['diagnostic_only'] else 'REVIEWED_EXPORT',
        'path':str(output),'sha256':identity(output.read_bytes()),'content_digest':record['content_digest'],
        'training_performed':False,'live_memory_mutated':False,'product_accepted':False}

def check_reuse(record,plan,binding,*,session,envelopes,rights,current_source_sha256,source_root):
    require(type(record) is dict and record.get('schema_version')=='bie.qa.correction-export/1','H8_REUSE_SCHEMA')
    require(digest({k:v for k,v in record.items() if k!='content_digest'})==record.get('content_digest'),'H8_REUSE_RECORD_CHANGED')
    require(canonical_bytes(record['plan'])==canonical_bytes(asdict(plan)) and record['binding']==asdict(binding),'H8_REUSE_CONTEXT_CHANGED')
    require(record['training_allowed'] is False and record['automatic_ingestion'] is False and record['retrieval_candidate_only'] is True,'H8_REUSE_SCOPE_CHANGED')
    require(record['rerun_gates']==list(plan.rerun_gates),'H8_REUSE_GATE_WAIVER')
    require(identity(record['correction_text'].encode('utf-8'))==plan.after.sha256,'H8_REUSE_CORRECTION_CHANGED')
    require(current_source_sha256==plan.source.sha256,'H8_REUSE_STALE_SOURCE')
    original=regular_bytes(source_root,plan.source.path)
    require(identity(original)==plan.source.sha256 and len(original)==plan.source.size,'H8_REUSE_STALE_SOURCE')
    require(type(session) is AuthoritySession and session.binding==binding,'H8_REUSE_AUTHORITY')
    if session.policy.mode=='production':require(record['diagnostic_only'] is False,'H8_REUSE_DIAGNOSTIC')
    require(type(rights) is RightsContext,'H8_REUSE_RIGHTS')
    rr=rights.verify();require(rr['technical_checks_clear'],'H8_REUSE_RIGHTS_BLOCKED')
    require(rr['details']['rights_scope_digest']==plan.rights_scope_digest,'H8_REUSE_RIGHTS_BINDING')
    require(not any(f['severity']!='ADVISORY' for f in rr['report']['findings'] if f['code']!='OPERATIONAL_INDEPENDENT_ACCEPTANCE_REQUIRED'),'H8_REUSE_RIGHTS_REVIEW')
    subject=digest({'record_digest':record['content_digest'],'binding':asdict(binding),'operation':'reuse_candidate'})
    session.verify_roles(envelopes,subject,required=('review','memory'))
    return {'status':'REVALIDATION_REQUIRED','required_gates':list(plan.rerun_gates),
        'can_execute_or_release':False,'training_allowed':False,'learning_improvement_claimed':False}
