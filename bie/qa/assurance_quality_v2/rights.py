"""HARD037: operational inventory and output-notice evidence adapter.

Actual artifact census is checked against independently approved provenance rows.
Calls the existing RIGHTS evaluator; an H8 approval cannot cancel its blockers.
External public signatures authenticate captures/clearance, not legal ownership.
No license is inferred, fetched, or selected from a filename or model response.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from .common import *
from .authority import AuthoritySession
from ..rights_v2.evaluator import evaluate as evaluate_rights
from ..rights_v2.models import RightsPolicy,RightsRequest

@dataclass(frozen=True)
class NoticeRequirement:
    notice_id:str
    material_id:str
    output_artifact_id:str
    required_text:str
    channels:tuple[str,...]
    def __post_init__(self):
        for n in ('notice_id','material_id','output_artifact_id'):token(getattr(self,n),n)
        text(self.required_text,'notice.text',32768)
        exact_strings(self.channels,'H8_NOTICE_CHANNELS',1)
        require(set(self.channels)<= {'VIDEO','GAME','TEXT','SOURCE_OFFER'},'H8_NOTICE_CHANNEL')

@dataclass(frozen=True)
class InventoryPolicy:
    policy_id:str
    rights_policy_digest:str
    files:tuple[dict,...]
    provenance:tuple[dict,...]
    notices:tuple[NoticeRequirement,...]
    required_provider_ids:tuple[str,...]=()
    def __post_init__(self):
        token(self.policy_id,'inventory');sha256(self.rights_policy_digest,'rights.policy');checked_rows(self.files)
        require(type(self.provenance) is tuple and len(self.provenance)==len(self.files),'H8_PROVENANCE_CENSUS')
        ids=[];paths=[]
        for r in self.provenance:
            fields(r,('artifact_id','path','role','material_id','provider_ids','parent_ids'),'H8_PROVENANCE_FIELDS')
            token(r['artifact_id'],'artifact');safe_relative_path(r['path']);token(r['material_id'],'material')
            require(r['role'] in ('SOURCE','ASSET','DEPENDENCY','PROVIDER_TERMS','OUTPUT','EVIDENCE'),'H8_MATERIAL_ROLE')
            exact_strings(r['parent_ids'],'H8_PARENT_IDS');exact_strings(r['provider_ids'],'H8_PROVIDER_IDS')
            ids.append(r['artifact_id']);paths.append(r['path'])
        require(len(set(ids))==len(ids) and set(paths)=={r['path'] for r in self.files},'H8_PROVENANCE_ALIAS')
        require(all(set(r['parent_ids'])<=set(ids) for r in self.provenance),'H8_MISSING_PARENT')
        by={r['artifact_id']:r for r in self.provenance};done=set();active=set()
        def walk(a):
            require(a not in active,'H8_PROVENANCE_CYCLE')
            if a in done:return
            active.add(a)
            for p in by[a]['parent_ids']:walk(p)
            active.remove(a);done.add(a)
        for a in ids:walk(a)
        exact_strings(self.required_provider_ids,'H8_REQUIRED_PROVIDERS')
        require({p for r in self.provenance for p in r['provider_ids']}==set(self.required_provider_ids),'H8_PROVIDER_CENSUS')
        require(type(self.notices) is tuple and len(self.notices)<=4096 and all(type(n) is NoticeRequirement for n in self.notices),'H8_NOTICES')
        require(len({n.notice_id for n in self.notices})==len(self.notices),'H8_NOTICE_ALIAS')
        require(all(n.output_artifact_id in by for n in self.notices),'H8_NOTICE_OUTPUT_MISSING')
    @property
    def content_digest(self):return digest(asdict(self))

def clearance_subject(request,rights_policy,policy,binding):
    return digest({'request':request.content_digest,'rights_policy':rights_policy.content_digest,
        'inventory_policy':policy.content_digest,'binding':asdict(binding)})

def notice_subject(observation,binding):
    return digest({'observation':observation,'binding':asdict(binding)})

def verify_inventory(request,root,rights_policy,policy,binding,*,as_of,
                     legacy_reviews=(),legacy_verifier=None,session=None,clearance=None,
                     observations=(),capture_root=None):
    require(type(request) is RightsRequest and type(rights_policy) is RightsPolicy and
        type(policy) is InventoryPolicy and type(binding) is Binding,'H8_RIGHTS_CONFIG')
    require(policy.rights_policy_digest==rights_policy.content_digest and binding.policy_digest==policy.content_digest,'H8_RIGHTS_POLICY_BINDING')
    actual=check_files(root,policy.files)
    refs={r.artifact_id:r for r in request.snapshot.artifacts}
    require(set(refs)=={r['artifact_id'] for r in policy.provenance},'H8_RIGHTS_ARTIFACT_CENSUS')
    actual_by={r['path']:r for r in actual}
    for row in policy.provenance:
        a=refs[row['artifact_id']];f=actual_by[row['path']]
        require(a.path==f['path'] and a.sha256==f['sha256'] and a.size==f['bytes'],'H8_RIGHTS_ARTIFACT_BINDING')
    by_artifact={r['artifact_id']:r for r in policy.provenance}
    for m in rights_policy.materials:
        require(m.artifact_id in by_artifact and by_artifact[m.artifact_id]['material_id']==m.material_id,'H8_MATERIAL_PROVENANCE_BINDING')
    base=evaluate_rights(request,root,rights_policy,as_of=as_of,reviews=legacy_reviews,verifier=legacy_verifier)
    errors=[];reviews=[];capture_keys=[]
    if base.status=='BLOCKED':errors.append('H8_INHERITED_RIGHTS_BLOCKED')
    elif base.status!='CHECKS_PASSED':reviews.append('H8_INHERITED_RIGHTS_REVIEW_REQUIRED')
    require(type(observations) is tuple and len(observations)<=4096,'H8_OBSERVATIONS')
    expected={(n.notice_id,ch):n for n in policy.notices for ch in n.channels};seen=set();observed=[]
    for item in observations:
        fields(item,('observation','attestation'),'H8_NOTICE_OBSERVATION')
        obs=fields(item['observation'],('notice_id','channel','output_artifact_id','output_sha256','text',
            'capture','method','visible','location'),'H8_NOTICE_FIELDS')
        key=(obs['notice_id'],obs['channel']);require(key in expected and key not in seen,'H8_NOTICE_CENSUS');seen.add(key)
        n=expected[key];require(obs['output_artifact_id']==n.output_artifact_id and
            obs['output_sha256']==refs[n.output_artifact_id].sha256,'H8_NOTICE_OUTPUT_BINDING')
        require(type(obs['visible']) is bool,'H8_NOTICE_VISIBLE_TYPE');text(obs['location'],'notice.location',2048)
        text(obs['text'],'notice.observed',262144)
        if not obs['visible'] or n.required_text not in obs['text']:errors.append('H8_NOTICE_MISSING_OR_HIDDEN')
        methods={'VIDEO':'DECODED_FRAME','GAME':'NATIVE_HTTP_DOM','TEXT':'EXACT_FILE','SOURCE_OFFER':'HTTP_RESPONSE'}
        if obs['method']!=methods[obs['channel']]:errors.append('H8_NOTICE_NOT_ACTUALLY_RENDERED')
        ref=ArtifactRef(**obs['capture'])
        require(capture_root is not None,'H8_CAPTURE_ROOT_REQUIRED')
        data=regular_bytes(capture_root,ref.path)
        require(identity(data)==ref.sha256 and len(data)==ref.size,'H8_NOTICE_CAPTURE_CHANGED')
        if obs['channel']=='TEXT':require(data.decode('utf-8')==obs['text'],'H8_NOTICE_TEXT_CHANGED')
        if session is None or item['attestation'] is None:reviews.append('H8_CAPTURE_ATTESTATION_REQUIRED')
        else:
            require(type(session) is AuthoritySession and session.binding==binding,'H8_RIGHTS_SESSION')
            capture_keys.append(session.verify(item['attestation'],purpose='capture',subject_digest=notice_subject(obs,binding),
                expected_payload={'decision':'APPROVE','trust_digest':session.policy.content_digest}))
        observed.append({'notice_id':n.notice_id,'channel':obs['channel'],'capture_sha256':ref.sha256})
    if seen!=set(expected):errors.append('H8_MISSING_NOTICE_COVERAGE')
    authority=None
    if session is None or clearance is None:reviews.append('H8_QUALIFIED_CLEARANCE_REQUIRED')
    else:
        require(type(session) is AuthoritySession and session.binding==binding,'H8_RIGHTS_SESSION')
        # A caller-selected as_of cannot exceed or precede the verified interval.
        lo,hi=session.window();require(lo//1000<=as_of<=(hi+999)//1000,'H8_RIGHTS_TIME_MISMATCH')
        # All permissions must cover the entire verified clock interval.
        for boundary in set((lo//1000,(hi+999)//1000)):
            edge=evaluate_rights(request,root,rights_policy,as_of=boundary,reviews=legacy_reviews,verifier=legacy_verifier)
            if edge.status=='BLOCKED':errors.append('H8_RIGHTS_CLOCK_INTERVAL_BLOCKED')
            elif edge.status!='CHECKS_PASSED':reviews.append('H8_RIGHTS_CLOCK_INTERVAL_REVIEW')
        authority=session.verify(clearance,purpose='rights',subject_digest=clearance_subject(request,rights_policy,policy,binding),
            expected_payload={'decision':'APPROVE','trust_digest':session.policy.content_digest})
        require(all(a['principal_id']!=authority['principal_id'] and a['independence_group']!=authority['independence_group'] for a in capture_keys),'H8_RIGHTS_CAPTURE_NOT_INDEPENDENT')
    details={'inventory':actual,'provenance':list(policy.provenance),'notices':observed,
        'legacy_result':base.to_dict(),'clearance_identity':authority,
        'rights_scope_digest':clearance_subject(request,rights_policy,policy,binding),
        'legal_clearance_certified':False,'live_status_service_executed':False}
    return outcome('BIE-QA-HARD-037',binding,details,errors,reviews)
