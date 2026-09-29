"""RIGHTS001/002: enforce explicit rights evidence, never infer permission from labels.

All data files are inspected, including originals, terms, status and obligations.
An operator-owned scope and separately provisioned authority remain prerequisites.
This is compliance evidence QA, not legal advice or an ownership determination.
"""
from __future__ import annotations
from dataclasses import dataclass
from ..release_v2.contracts import ContractError,canonical_bytes,digest,integer
from ..source_v2.codec import loads
from ..source_v2.io import SnapshotStore
from ..source_v2.models import Report,Finding
from ..repair_audit_v2.io import fields,verify_files
from ..repair_v2.planner import approved
from ..reasoning_v2.attestation import Review,ReviewVerifier
from .models import RightsPolicy,RightsRequest
from .expressions import single_atom,selected_branch

LIMITATIONS=(
 'No default permission from a license name, educational purpose, purchase, generated origin or public-domain claim.',
 'Policy scope, exclusions, ownership, license meaning, legal exceptions and grantee authority need independent review.',
 'AND/OR/WITH selection is bounded syntax, not full SPDX catalog validation or automatic compatibility analysis.',
 'Notice bytes are checked in declared files; no native rendered credits, browser availability or source-offer endpoint was verified.',
 'Status is a freshness-checked supplied snapshot, not live revocation discovery or legal termination adjudication.',
 'No full-book/asset inventory discovery, native media/game clearance, canonical integration or product acceptance.'
)

@dataclass(frozen=True,slots=True)
class Result:
    reports:tuple[Report,...]
    details_json:str
    @property
    def status(self):
        states={r.status for r in self.reports}
        return 'BLOCKED' if 'BLOCKED' in states else 'REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in states else 'CHECKS_PASSED'
    def to_dict(self):
        return dict(schema_version='bie.qa.rights-result/1',reports=[r.to_dict() for r in self.reports],details=loads(self.details_json.encode()),status=self.status,
            product_accepted=False,legal_clearance_certified=False,actual_media_credits_verified=False)


def review_targets(request,policy):
    """Exact scope of separate reviews; policies and keys are not read from candidate text."""
    refs={a.artifact_id for a in request.snapshot.artifacts};gs={g.grant_id:g for g in policy.grants}
    ms={m.material_id:m for m in policy.materials};us={u.use_id:u for u in policy.requirements}
    targets={('inventory','rights-inventory'):tuple(sorted(refs)),('support','rights-status'):(request.status_artifact_id,)}
    for s in request.selections:
        if s.use_id not in us:continue
        u=us[s.use_id];m=ms[u.material_id]
        for gid in s.grant_ids:
            if gid in gs:
                g=gs[gid];targets[('support','rights-grant:'+gid)]=tuple(sorted(set(g.evidence_ids+(m.artifact_id,))))
                if g.basis=='EXCEPTION':
                    k=('inference','rights-exception:'+gid)
                    targets[k]=tuple(sorted(set(targets.get(k,())+g.evidence_ids+(m.artifact_id,u.output_artifact_id))))
        targets[('mapping','rights-use:'+u.use_id)]=tuple(sorted({m.artifact_id,u.output_artifact_id}))
        if s.notices:targets[('disclosure','rights-notices:'+u.use_id)]=tuple(sorted({n.artifact_id for n in s.notices}))
    return targets


def evaluate(request,root,policy,*,as_of,reviews=(),verifier=None):
    if type(request) is not RightsRequest or type(policy) is not RightsPolicy:raise ContractError('RIGHTS_INPUT_TYPE')
    integer(as_of,'as_of');verifier=ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier:raise ContractError('RIGHTS_VERIFIER_TYPE')
    if type(reviews) is not tuple or len(reviews)>1024 or any(type(r) is not Review for r in reviews) or len({r.review_id for r in reviews})!=len(reviews):raise ContractError('RIGHTS_REVIEWS_TYPE')
    fs=[[],[]];inspected=set();details=[];auth_results={}
    def add(indices,code,subject='rights',severity='BLOCKER'):
        for i in indices:
            f=Finding(code,severity,subject,'RIGHTS','Rights evidence requirement: '+code)
            if f not in fs[i]:fs[i].append(f)
    def auth(subject,purpose,ids,indices):
        relevant=tuple(r for r in reviews if (r.subject_id,r.purpose)==(subject,purpose))
        ok,codes=approved(relevant,verifier,subject=subject,purpose=purpose,request_digest=request.content_digest,policy=policy,evidence_ids=ids,now=as_of)
        auth_results[purpose+':'+subject]=dict(verified=ok,codes=codes)
        if not ok:
            add(indices,'RIGHTS_AUTHORIZATION_REQUIRED',subject,'REVIEW')
            for r in relevant:
                a=verifier.verify_bound(r,request.content_digest,policy.content_digest,policy.max_receipt_age_seconds,as_of)
                if a.operational and r.verdict=='REJECTED':add(indices,'RIGHTS_REVIEW_REJECTED',subject)
    try:
        if request.snapshot.content_digest!=policy.snapshot_digest:raise ContractError('RIGHTS_SNAPSHOT_BINDING')
        if as_of>=policy.planned_until:raise ContractError('RIGHTS_USE_WINDOW_ENDED')
        verify_files(root,request.snapshot,exact=True)
        refs={a.artifact_id:a for a in request.snapshot.artifacts}
        blobs={}
        with SnapshotStore(root) as store:
            for a in request.snapshot.artifacts:blobs[a.artifact_id]=store.read(a);inspected.add(a.artifact_id)
        materials={m.material_id:m for m in policy.materials};grants={g.grant_id:g for g in policy.grants}
        required={u.use_id:u for u in policy.requirements};selected={s.use_id:s for s in request.selections}
        if set(required)!=set(selected):add(range(2),'RIGHTS_USE_INVENTORY_MISMATCH')
        material_refs={m.artifact_id for m in policy.materials if m.category=='SOURCE'}
        if {a.artifact_id for a in request.snapshot.artifacts if a.role=='source'}-material_refs:add((1,),'RIGHTS_SOURCE_INVENTORY_INCOMPLETE')
        for m in policy.materials:
            if m.artifact_id not in refs:raise ContractError('RIGHTS_MATERIAL_BYTES_MISSING')
            if m.category=='SOURCE' and refs[m.artifact_id].role!='source':raise ContractError('RIGHTS_SOURCE_ROLE_MISMATCH')
            if m.artifact_id==request.status_artifact_id:raise ContractError('RIGHTS_STATUS_MATERIAL_ALIAS')
        for u in policy.requirements:
            if u.output_artifact_id not in refs or any(n not in refs for n in u.notice_artifact_ids):raise ContractError('RIGHTS_OUTPUT_BYTES_MISSING')
            if refs[u.output_artifact_id].role not in ('video','game','support'):raise ContractError('RIGHTS_OUTPUT_ROLE')
            if any(refs[n].role not in ('video','game','support') for n in u.notice_artifact_ids):raise ContractError('RIGHTS_NOTICE_ROLE')
        for g in policy.grants:
            if any(x not in refs for x in g.evidence_ids):raise ContractError('RIGHTS_GRANT_DOCUMENT_MISSING')
            if request.status_artifact_id in g.evidence_ids:raise ContractError('RIGHTS_STATUS_NOT_GRANT')
        targets=review_targets(request,policy)
        if any((r.purpose,r.subject_id) not in targets for r in reviews):raise ContractError('RIGHTS_UNEXPECTED_REVIEW')
        auth('rights-inventory','inventory',targets['inventory','rights-inventory'],range(2))
        auth('rights-status','support',targets['support','rights-status'],range(2))
        status=loads(blobs[request.status_artifact_id]);fields(status,{'schema_version','observed_at','grants'},'RIGHTS_STATUS_FIELDS')
        if status['schema_version']!='bie.qa.rights-status/1':raise ContractError('RIGHTS_STATUS_SCHEMA')
        integer(status['observed_at'],'observed_at')
        if not 0<=as_of-status['observed_at']<=policy.max_status_age_seconds:raise ContractError('RIGHTS_STATUS_STALE')
        if type(status['grants']) is not list or len(status['grants'])!=len(grants):raise ContractError('RIGHTS_STATUS_COVERAGE')
        states={}
        for row in status['grants']:
            fields(row,{'grant_id','state'},'RIGHTS_STATUS_ENTRY')
            if type(row['grant_id']) is not str or row['grant_id'] not in grants or row['grant_id'] in states:raise ContractError('RIGHTS_STATUS_DUPLICATE_OR_UNKNOWN')
            if row['state'] not in ('ACTIVE','REVOKED','SUSPENDED','UNKNOWN'):raise ContractError('RIGHTS_STATUS_VALUE')
            states[row['grant_id']]=row['state']
        if set(states)!=set(grants):raise ContractError('RIGHTS_STATUS_COVERAGE')
        ancestry={}
        def parents(mid):
            if mid not in ancestry:
                p=set(materials[mid].parent_ids)
                for x in materials[mid].parent_ids:p|=parents(x)
                ancestry[mid]=p
            return ancestry[mid]
        for u in policy.requirements:
            m=materials[u.material_id];idx=0 if m.category=='ASSET' else 1;ii=(idx,)
            if m.origin=='UNKNOWN':add(ii,'RIGHTS_ORIGIN_UNKNOWN',u.use_id,'REVIEW')
            for parent in parents(m.material_id):
                puses=[pu for pu in policy.requirements if pu.material_id==parent and pu.output_artifact_id==u.output_artifact_id and set(u.operations)<=set(pu.operations)]
                if not puses:add(ii,'RIGHTS_DERIVED_PERMISSION_GAP',u.use_id)
            s=selected.get(u.use_id)
            if s is None:continue
            if not s.grant_ids:add(ii,'RIGHTS_GRANT_REQUIRED',u.use_id);continue
            if any(g not in grants for g in s.grant_ids):add(ii,'RIGHTS_UNKNOWN_GRANT',u.use_id);continue
            gs=[grants[g] for g in s.grant_ids]
            if any(g.material_id!=u.material_id for g in gs):add(ii,'RIGHTS_WRONG_MATERIAL_GRANT',u.use_id);continue
            try:branch=selected_branch(m.license_expression,tuple(g.license_atom for g in gs))
            except ContractError as exc:
                severity='REVIEW' if exc.code.startswith('RIGHTS_EXPRESSION_') else 'BLOCKER'
                add(ii,exc.code,u.use_id,severity);branch=()
            auth('rights-use:'+u.use_id,'mapping',targets['mapping','rights-use:'+u.use_id],ii)
            expected_notices={(g.grant_id,o.obligation_id):o for g in gs for o in g.obligations}
            proofs={(n.grant_id,n.obligation_id):n for n in s.notices}
            if set(proofs)!=set(expected_notices):add(ii,'RIGHTS_OBLIGATION_COVERAGE',u.use_id)
            for key,o in expected_notices.items():
                n=proofs.get(key)
                if n is None:continue
                if n.artifact_id not in u.notice_artifact_ids:add(ii,'RIGHTS_NOTICE_LOCATION',u.use_id);continue
                b=blobs[n.artifact_id]
                if n.end>len(b) or b[n.start:n.end]!=o.required_text.encode('utf-8'):add(ii,'RIGHTS_NOTICE_TEXT_MISMATCH',u.use_id)
            if s.notices:auth('rights-notices:'+u.use_id,'disclosure',targets['disclosure','rights-notices:'+u.use_id],ii)
            for g in gs:
                auth('rights-grant:'+g.grant_id,'support',targets['support','rights-grant:'+g.grant_id],ii)
                if g.basis=='EXCEPTION':auth('rights-exception:'+g.grant_id,'inference',targets['inference','rights-exception:'+g.grant_id],ii)
                if states[g.grant_id] in ('REVOKED','SUSPENDED'):add(ii,'RIGHTS_GRANT_INACTIVE',g.grant_id)
                elif states[g.grant_id]=='UNKNOWN':add(ii,'RIGHTS_GRANT_STATUS_UNKNOWN',g.grant_id,'REVIEW')
                if not set(u.operations)<=set(g.operations):add(ii,'RIGHTS_OPERATION_NOT_GRANTED',u.use_id)
                if not set(m.dimensions)<=set(g.dimensions):add(ii,'RIGHTS_DIMENSION_NOT_GRANTED',u.use_id)
                if policy.grantee_id not in g.grantees and 'ALL' not in g.grantees:add(ii,'RIGHTS_GRANTEE_MISMATCH',u.use_id)
                if not set(policy.territories)<=set(g.territories) and 'WORLDWIDE' not in g.territories:add(ii,'RIGHTS_TERRITORY_MISMATCH',u.use_id)
                if not set(policy.channels)<=set(g.channels) and 'ALL' not in g.channels:add(ii,'RIGHTS_CHANNEL_MISMATCH',u.use_id)
                if policy.commercial and not g.commercial_allowed:add(ii,'RIGHTS_COMMERCIAL_USE_NOT_GRANTED',u.use_id)
                if g.valid_from>policy.planned_from or g.valid_until<policy.planned_until or not g.valid_from<=as_of<g.valid_until:add(ii,'RIGHTS_GRANT_TIME_WINDOW',u.use_id)
                if g.allowed_output_licenses and u.output_license not in g.allowed_output_licenses:add(ii,'RIGHTS_OUTPUT_LICENSE_NOT_APPROVED',u.use_id)
            details.append(dict(use_id=u.use_id,category=m.category,selected_license_branch=branch,grant_ids=s.grant_ids,obligation_count=len(expected_notices),ancestors=sorted(parents(m.material_id))))
        # A dependent cannot be cleared when its upstream/source check is unresolved.
        affected={f.subject_id for family in fs for f in family}
        for u in policy.requirements:
            if parents(u.material_id):
                blockers=[pu.use_id for pu in policy.requirements if pu.material_id in parents(u.material_id) and pu.output_artifact_id==u.output_artifact_id and (pu.use_id in affected or any(g in affected for g in (selected[pu.use_id].grant_ids if pu.use_id in selected else ())))]
                if blockers:add((0 if materials[u.material_id].category=='ASSET' else 1,),'RIGHTS_UPSTREAM_CLEARANCE_PENDING',u.use_id,'REVIEW')
        verify_files(root,request.snapshot,exact=True)
    except (ContractError,OSError,UnicodeError) as exc:
        add(range(2),exc.code if isinstance(exc,ContractError) else 'RIGHTS_INPUT_IO')
    eid=digest(dict(request=request.content_digest,policy=policy.content_digest,verifier=verifier.configuration_digest,auth=auth_results))
    reports=tuple(Report(f'BIE-QA-RIGHTS-{i+1:03}',request.content_digest,policy.content_digest,eid,as_of,
        tuple(sorted(fs[i],key=lambda f:(f.severity,f.code,f.subject_id))),
        (('required_uses',sum((m.category=='ASSET')==(i==0) for u in policy.requirements for m in policy.materials if u.material_id==m.material_id)),),tuple(sorted(inspected)),LIMITATIONS) for i in range(2))
    return Result(reports,canonical_bytes(dict(uses=details,authorization=auth_results)).decode())
