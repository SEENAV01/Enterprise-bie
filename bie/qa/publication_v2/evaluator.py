"""Read actual bytes, re-run every inherited gate, construct manifest/graph/blockers.

Reports are evidence claims, not truth. Native scope and complete inventory require
separate operator-provisioned assessors; metadata alone cannot grant certification.
"""
from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
from collections import deque
from .contracts import (SCHEMA,PROOF_SCHEMA,EXIT_SCHEMA,STAGES,PublicationRequest,
    PublicationPolicy,strict_json,shape,seq)
from ..release_v2.contracts import ContractError,ArtifactRef,canonical_bytes,digest,integer,token
from ..release_v2.codec import artifact_from_dict
from ..release_v2.evaluator import ReleaseEvaluator
from ..source_v2.io import SnapshotStore
from .terminal import TerminalContext, validate_terminal
from ..governance_v2.inventory import evaluate_inventory

@dataclass(frozen=True)
class Assessment:
    request_digest:str
    policy_digest:str
    as_of:int
    status:str
    manifest:dict
    graph:dict
    blockers:tuple[dict,...]
    inherited_gate_report:dict
    ready_for_signing:bool
    product_accepted:bool=False
    def to_dict(self):return asdict(self)
    @property
    def content_digest(self):return digest(self.to_dict())
    def to_bytes(self):return canonical_bytes(self.to_dict())


def assess(request:PublicationRequest,root:str|Path,policy:PublicationPolicy,*,as_of:int,verifier=None)->Assessment:
    if type(request)is not PublicationRequest or type(policy)is not PublicationPolicy:raise ContractError('PUBLICATION_INPUT_TYPE')
    integer(as_of,'as_of')
    bundle=request.bundle;c=bundle.candidate
    original=ReleaseEvaluator(policy.release_policy,verifier).evaluate(bundle,root,as_of=as_of)
    subjects={a.artifact_id:a for a in c.artifacts}
    refs={a.artifact_id:a for a in c.artifacts};paths={a.path:a for a in c.artifacts}
    nodes={};edges=set();blockers=[];lineage={}
    rules={r.gate_id:r for r in policy.release_policy.gates}
    reserved_reports=set(subjects)|{e.report.artifact_id for e in bundle.evidence}|{r.artifact_id for r in request.governance}
    def block(code,subject='release',owner='QA.RELEASE',artifacts=()):
        token(code,'blocker.code')
        blockers.append(dict(code=code,subject=subject,owner=owner,artifact_ids=sorted(set(artifacts))))
    def node(key,kind,**data):
        val=dict(node_id=key,kind=kind,**data)
        if key in nodes and nodes[key]!=val:block('GRAPH_NODE_ALIAS',key)
        else:nodes[key]=val
    def edge(a,b,relation):edges.add((a,b,relation))
    def reference(ref):
        if (ref.artifact_id in refs and refs[ref.artifact_id]!=ref) or (ref.path in paths and paths[ref.path]!=ref):
            raise ContractError('PUBLICATION_ARTIFACT_ALIAS')
        refs[ref.artifact_id]=ref;paths[ref.path]=ref
        node('artifact:'+ref.artifact_id,'artifact',**ref.to_dict())
    def scoped(value,where):
        if value not in ('NATIVE_PRODUCT','DIAGNOSTIC'):raise ContractError('PUBLICATION_PROOF_SCOPE')
        if value!='NATIVE_PRODUCT' and policy.mode=='production':block('NON_NATIVE_PROOF',where)
    terminal_requirements={(r.subject_type,r.subject_id):r for r in policy.terminal_requirements}
    def report_refs(value,where,store,read,context):
        arr=seq(value,'source_reports',128)
        if not arr:raise ContractError('MISSING_SOURCE_REPORTS')
        seen=set()
        for item in arr:
            ref=artifact_from_dict(item)
            if ref.role!='report' or ref.artifact_id in seen:raise ContractError('SOURCE_REPORT_ROLE_OR_DUPLICATE')
            if ref.artifact_id in reserved_reports:raise ContractError('SOURCE_REPORT_NOT_TERMINAL')
            seen.add(ref.artifact_id);reference(ref);payload=read(ref)
            edge(where,'artifact:'+ref.artifact_id,'supported_by')
            def inspect(dependency):
                if dependency.artifact_id==ref.artifact_id or dependency.artifact_id in reserved_reports-set(subjects):
                    raise ContractError('TERMINAL_DEPENDENCY_CYCLE')
                reference(dependency)
                edge('artifact:'+ref.artifact_id,'artifact:'+dependency.artifact_id,'inspected_bytes')
                return read(dependency)
            raw=strict_json(payload)
            if raw.get('schema_version')=='bie.qa.terminal-report/1' and raw.get('report_id')!=ref.artifact_id:
                block('TERMINAL_REPORT_ID_MISMATCH',ref.artifact_id)
            result=validate_terminal(raw,context,terminal_requirements.get((context.subject_type,context.subject_id)),inspect)
            for code in result.blockers:block(code,ref.artifact_id)
            if result.expires_at is not None:expires.append(result.expires_at)
            if result.advisories:
                nodes['artifact:'+ref.artifact_id]['advisories']=list(result.advisories)
    for a in c.artifacts:reference(a)
    for item in request.open_items:
        if not set(item.artifact_ids)<=set(subjects):block('OPEN_ITEM_UNKNOWN_ARTIFACT',item.item_id,item.owner)
        block(item.code,item.item_id,item.owner,item.artifact_ids)
    # Original errors are never filtered down to only failed gates.
    for code in original.global_diagnostics:block(code)
    if not original.ready_for_review:block('INHERITED_RELEASE_NOT_READY')
    for gate in original.gate_results:
        node('gate:'+gate.gate_id,'gate',gate_id=gate.gate_id,owner=gate.owner,status=gate.status)
        for code in gate.diagnostics:block(code,gate.gate_id,gate.owner)
        for ev in gate.evidence:
            for code in ev.diagnostics:block(code,ev.evidence_id,gate.owner)
    # Submitted lineage may describe only real candidate objects. No missing-parent
    # placeholder nodes and no opaque wildcard coverage are permitted.
    for item in request.lineage:
        if item.artifact_id not in subjects or not set(item.parent_ids)<=set(subjects):
            block('LINEAGE_UNKNOWN_ARTIFACT',item.artifact_id);continue
        if subjects[item.artifact_id].role=='source':block('SOURCE_CANNOT_BE_DERIVED',item.artifact_id)
        lineage[item.artifact_id]=item.parent_ids
        for parent in item.parent_ids:edge('artifact:'+item.artifact_id,'artifact:'+parent,'derived_from')
    for aid,a in subjects.items():
        if a.role!='source' and aid not in lineage:block('MISSING_ARTIFACT_LINEAGE',aid,artifacts=(aid,))
        if a.role!='source':
            pending=[aid];seen=set();grounded=False
            while pending:
                x=pending.pop()
                if x in seen:continue
                seen.add(x)
                if subjects[x].role=='source':grounded=True
                pending.extend(lineage.get(x,()))
            if not grounded:block('NO_SOURCE_PATH',aid,artifacts=(aid,))
    # Full proof and exit evidence are read through the inherited bounded snapshot
    # reader. Report caching saves IO only when the complete ArtifactRef is identical.
    inventory_result=None
    cache={};expires=[ev.expires_at for ev in bundle.evidence]
    expires.extend(r.trust_expires_at for g in original.gate_results for r in g.evidence if r.trust_expires_at>0)
    try:
        with SnapshotStore(root) as store:
            def read(ref):
                if ref not in cache:cache[ref]=store.read(ref)
                return cache[ref]
            # HARD006: candidate evidence never supplies its own required census.
            # Missing authority or a missing declaration is a blocker, not a bypass.
            try:
                inventory_reserved=set(reserved_reports)
                def inventory_ref(ref,relation):
                    if relation in ('inventory','closure','closure_evidence') and ref.artifact_id in inventory_reserved:
                        raise ContractError('INVENTORY_REPORT_ALIAS')
                    reference(ref)
                    edge('release:'+request.release_id,'artifact:'+ref.artifact_id,relation)
                inventory_result=evaluate_inventory(request,policy.inventory_authority,policy,as_of=as_of,read=read,register=inventory_ref)
                for code in inventory_result.blockers:block(code,'authoritative-inventory')
                if inventory_result.expires_at is not None:expires.append(inventory_result.expires_at)
            except ContractError as exc:block(exc.code,'authoritative-inventory')
            for ev in sorted(bundle.evidence,key=lambda e:e.evidence_id):
                eid='evidence:'+ev.evidence_id
                node(eid,'evidence',evidence_id=ev.evidence_id,gate_id=ev.gate_id,evidence_digest=digest(ev.to_dict()))
                edge('gate:'+ev.gate_id,eid,'evaluated_by')
                try:
                    reference(ev.report);edge(eid,'artifact:'+ev.report.artifact_id,'reported_in')
                    for aid in ev.inspected_artifact_ids:edge(eid,'artifact:'+aid,'inspected')
                    raw=strict_json(read(ev.report))
                    shape(raw,('schema_version','evidence_id','gate_id','candidate_digest','policy_digest','run_id','revision','status','scope','checks','source_reports'))
                    expected=(PROOF_SCHEMA,ev.evidence_id,ev.gate_id,c.content_digest,policy.release_policy.content_digest,c.run_id,c.revision,ev.status)
                    actual=tuple(raw[k] for k in ('schema_version','evidence_id','gate_id','candidate_digest','policy_digest','run_id','revision','status'))
                    if actual!=expected:raise ContractError('PROOF_BINDING_MISMATCH')
                    scoped(raw['scope'],ev.evidence_id)
                    if ev.diagnostics:block('UNCLEARED_EVIDENCE_DIAGNOSTICS',ev.evidence_id)
                    checks=seq(raw['checks'],'checks',4096)
                    if not checks:raise ContractError('EMPTY_PROOF_CHECKS')
                    seen=set()
                    for check in checks:
                        shape(check,('check_id','status','diagnostics'));token(check['check_id'],'check_id')
                        if check['check_id']in seen:raise ContractError('DUPLICATE_PROOF_CHECK')
                        seen.add(check['check_id'])
                        if check['status'] not in ('PASS','FAIL','ERROR','SKIPPED','NOT_RUN','REVIEW_REQUIRED'):raise ContractError('INVALID_PROOF_STATUS')
                        codes=seq(check['diagnostics'],'diagnostics',128)
                        for code in codes:token(code,'proof.diagnostic')
                        if check['status']!='PASS' or codes:block('PROOF_CHECK_NOT_CLEAR',ev.evidence_id,rules.get(ev.gate_id).owner if ev.gate_id in rules else 'QA.RELEASE')
                    context=TerminalContext(c,policy.release_policy.content_digest,None,'gate',ev.gate_id,ev.evidence_id,
                        tuple(subjects[x] for x in ev.inspected_artifact_ids if x in subjects),as_of,ev.created_at,ev.expires_at,
                        policy.release_policy.max_evidence_lifetime_seconds,policy.mode)
                    report_refs(raw['source_reports'],'artifact:'+ev.report.artifact_id,store,read,context)
                except ContractError as exc:block(exc.code,ev.evidence_id)
            stages=set()
            for ref in sorted(request.governance,key=lambda r:r.artifact_id):
                try:
                    reference(ref);raw=strict_json(read(ref))
                    shape(raw,('schema_version','stage','status','revision','candidate_digest','bundle_digest','open_must_have_ids','scope','source_reports'))
                    if (raw['schema_version'],raw['revision'],raw['candidate_digest'],raw['bundle_digest'])!=(EXIT_SCHEMA,c.revision,c.content_digest,bundle.content_digest):
                        raise ContractError('SECTION_EXIT_BINDING')
                    if raw['stage'] not in STAGES or raw['stage'] in stages:raise ContractError('SECTION_EXIT_STAGE')
                    stages.add(raw['stage']);scoped(raw['scope'],ref.artifact_id)
                    if raw['status']!='PASS' or seq(raw['open_must_have_ids'],'must_have_ids'):block('SECTION_EXIT_NOT_CLEAR',ref.artifact_id)
                    context=TerminalContext(c,policy.release_policy.content_digest,bundle.content_digest,'section_exit',raw['stage'],ref.artifact_id,
                        tuple(c.artifacts),as_of,as_of,as_of+policy.max_review_lifetime_seconds,policy.max_review_lifetime_seconds,policy.mode)
                    report_refs(raw['source_reports'],'artifact:'+ref.artifact_id,store,read,context)
                except ContractError as exc:block(exc.code,ref.artifact_id)
            for stage in sorted(set(STAGES)-stages):block('MISSING_SECTION_EXIT_EVIDENCE',stage)
    except ContractError as exc:block(exc.code)
    # Bound graph size, detect any cycle including report-to-itself aliases.
    rid='release:'+request.release_id
    node(rid,'release',release_id=request.release_id,release_version=request.release_version)
    for r in rules:edge(rid,'gate:'+r,'requires')
    for aid in subjects:edge(rid,'artifact:'+aid,'delivers')
    for ref in request.governance:edge(rid,'artifact:'+ref.artifact_id,'section_exit')
    if len(nodes)>16384 or len(edges)>65536:raise ContractError('PUBLICATION_GRAPH_LIMIT')
    degree={n:0 for n in nodes};adj={n:[] for n in nodes}
    for a,b,_ in sorted(edges):
        if a not in nodes or b not in nodes:block('GRAPH_DANGLING_EDGE',a);continue
        degree[b]+=1;adj[a].append(b)
    q=deque(sorted(n for n,d in degree.items() if d==0));order=[]
    while q:
        n=q.popleft();order.append(n)
        for x in sorted(adj[n]):
            degree[x]-=1
            if degree[x]==0:q.append(x)
    if len(order)!=len(nodes):block('EVIDENCE_GRAPH_CYCLE')
    uniq={canonical_bytes(b):b for b in blockers}
    ordered=tuple(uniq[k] for k in sorted(uniq))
    graph=dict(schema_version=SCHEMA,nodes=[nodes[k] for k in sorted(nodes)],
        edges=[dict(source=a,target=b,relation=r) for a,b,r in sorted(edges)],topological_order=order)
    manifest=dict(schema_version=SCHEMA,release_id=request.release_id,release_version=request.release_version,
        environment_id=policy.environment_id,mode=policy.mode,run_id=c.run_id,revision=c.revision,
        request_digest=request.content_digest,candidate_digest=c.content_digest,bundle_digest=bundle.content_digest,
        release_policy_digest=policy.release_policy.content_digest,publication_policy_digest=policy.content_digest,
        candidate_artifact_ids=sorted(subjects),artifacts=[refs[k].to_dict() for k in sorted(refs)],
        evidence_expiry=min(expires) if expires else as_of,graph_digest=digest(graph),
        gate_report_digest=digest(original.to_dict()),inventory_authority_digest=policy.inventory_authority.content_digest if policy.inventory_authority else None,
        inventory_obligations_checked=list(inventory_result.checked_obligations) if inventory_result else [],product_accepted=False)
    clear=not ordered and original.ready_for_review
    return Assessment(request.content_digest,policy.content_digest,as_of,'READY_FOR_AUTHORIZATION' if clear else 'BLOCKED',
        manifest,graph,ordered,original.to_dict(),clear)
