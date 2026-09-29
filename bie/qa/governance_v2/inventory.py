"""HARD006 release census and independently authenticated closure validation.

The caller supplies an InventoryAuthority out-of-band, never from submitted JSON.
Actual reads are injected by the publication snapshot reader to preserve aliases,
hashes and graph edges. No source, metadata, journal or repository is modified.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,hmac
from .contracts import InventoryAuthority,INVENTORY_SCHEMA,CLOSURE_SCHEMA,OPEN_STATUSES,closure_signing_bytes
from ..release_v2.contracts import ContractError,token,integer,canonical_bytes
from ..release_v2.codec import artifact_from_dict
from ..publication_v2.report_policy import TerminalRequirement

@dataclass(frozen=True)
class InventoryResult:
    blockers: tuple[str,...]
    expires_at: int|None
    checked_obligations: tuple[str,...]
    authority_digest: str|None


def _ids(raw,name,limit=4096):
    from ..publication_v2.contracts import seq
    arr=seq(raw,name,limit)
    for ident in arr:token(ident,name)
    if len(arr)!=len(set(arr)):raise ContractError('INVENTORY_DUPLICATE',name)
    return set(arr)


def _lifetime(raw,authority,as_of,codes,prefix):
    created=integer(raw['created_at'],'created_at');expires=integer(raw['expires_at'],'expires_at',created+1)
    if not created<=as_of<expires:codes.add(prefix+'_TIME')
    if expires-created>authority.max_lifetime_seconds or as_of-created>authority.max_lifetime_seconds:codes.add(prefix+'_LIFETIME')
    return created,expires


def evaluate_inventory(request,authority,publication_policy,*,as_of,read,register):
    """Return blockers; raise only contract errors (caller must retain them)."""
    from ..publication_v2.contracts import shape,seq,strict_json,STAGES
    from ..publication_v2.terminal import TerminalContext,validate_terminal
    if authority is None:
        return InventoryResult(('AUTHORITATIVE_INVENTORY_UNCONFIGURED',),None,(),None)
    if type(authority) is not InventoryAuthority:raise ContractError('INVENTORY_AUTHORITY_TYPE')
    codes=set();expiry=[];checked=[]
    c=request.bundle.candidate
    if publication_policy.mode=='production' and authority.profile!='SECTION16':codes.add('DIAGNOSTIC_INVENTORY_NOT_PRODUCTION')
    requirements={(r.subject_type,r.subject_id):r for r in authority.check_requirements}
    actual_requirements={(r.subject_type,r.subject_id):r for r in publication_policy.terminal_requirements}
    needed={('gate',g.gate_id) for g in publication_policy.release_policy.gates}|{('section_exit',s) for s in STAGES}
    if set(requirements)!=needed or requirements!=actual_requirements:codes.add('AUTHORITATIVE_CHECK_POLICY_MISMATCH')
    if set(c.artifacts)!=set(authority.artifacts):codes.add('AUTHORITATIVE_ARTIFACT_MISMATCH')
    if request.inventory is None:
        return InventoryResult(tuple(sorted(codes|{'AUTHORITATIVE_INVENTORY_MISSING'})),None,(),authority.content_digest)
    register(request.inventory,'inventory')
    raw=strict_json(read(request.inventory))
    shape(raw,('schema_version','authority_digest','candidate_digest','run_id','revision','created_at','expires_at','artifacts','task_ids','checks','obligations'))
    if raw['schema_version']!=INVENTORY_SCHEMA:raise ContractError('INVENTORY_SCHEMA')
    expected=dict(authority_digest=authority.content_digest,candidate_digest=c.content_digest,run_id=c.run_id,revision=c.revision)
    if any(type(raw[k])is not type(v) or raw[k]!=v for k,v in expected.items()):codes.add('INVENTORY_BINDING_MISMATCH')
    _,expires=_lifetime(raw,authority,as_of,codes,'INVENTORY');expiry.append(expires)
    refs=tuple(artifact_from_dict(x) for x in seq(raw['artifacts'],'artifacts',2048))
    if len({r.artifact_id for r in refs})!=len(refs) or len({r.path for r in refs})!=len(refs):raise ContractError('INVENTORY_DUPLICATE_ARTIFACT')
    if set(refs)!=set(authority.artifacts):codes.add('INVENTORY_ARTIFACT_CENSUS')
    for ref in authority.artifacts:register(ref,'required_artifact');read(ref)
    if _ids(raw['task_ids'],'task_ids',512)!=set(authority.task_ids):codes.add('INVENTORY_TASK_CENSUS')
    declared={}
    for value in seq(raw['checks'],'checks',256):
        shape(value,('subject_type','subject_id','check_ids'))
        token(value['subject_type'],'subject_type');token(value['subject_id'],'subject_id')
        key=(value['subject_type'],value['subject_id'])
        if key in declared:raise ContractError('INVENTORY_DUPLICATE_CHECK_SUBJECT')
        declared[key]=_ids(value['check_ids'],'check_ids')
    if declared!={key:set(r.required_check_ids) for key,r in requirements.items()}:codes.add('INVENTORY_CHECK_CENSUS')
    # The independent check inventory constrains outer proof checks as well as H1's
    # typed terminal checks. Removing one layer cannot shrink another layer's floor.
    for ev in request.bundle.evidence:
        req=requirements.get(('gate',ev.gate_id))
        if req is None:continue
        proof=strict_json(read(ev.report));checks=proof.get('checks',[])
        observed=_ids([x.get('check_id') for x in checks if type(x)is dict],'proof.check_ids') if type(checks)is list else set()
        if not set(req.required_check_ids)<=observed:codes.add('MISSING_AUTHORITATIVE_PROOF_CHECK')
    obligations={o.obligation_id:o for o in authority.obligations};rows={}
    for value in seq(raw['obligations'],'obligations',2048):
        shape(value,('obligation_id','owner','scope','definition_digest','status','closure_ref'))
        token(value['obligation_id'],'obligation_id')
        if value['obligation_id'] in rows:raise ContractError('INVENTORY_DUPLICATE_OBLIGATION')
        rows[value['obligation_id']]=value
    if set(rows)!=set(obligations):codes.add('INVENTORY_OBLIGATION_CENSUS')
    closure_ids=set();evidence_ids=set()
    for oid,o in obligations.items():
        row=rows.get(oid)
        if row is None:continue
        checked.append(oid)
        if (row['owner'],row['scope'],row['definition_digest'])!=(o.owner,o.scope,o.definition_digest):codes.add('OBLIGATION_DEFINITION_MISMATCH')
        if row['status'] in OPEN_STATUSES:
            codes.add('AUTHORITATIVE_OBLIGATION_OPEN')
            if row['closure_ref']is not None:codes.add('OPEN_OBLIGATION_HAS_CLOSURE')
            continue
        if row['status']!='CLOSED':raise ContractError('OBLIGATION_STATUS')
        if row['closure_ref']is None:codes.add('OBLIGATION_CLOSURE_MISSING');continue
        cr=artifact_from_dict(row['closure_ref'])
        if cr.role!='report':raise ContractError('CLOSURE_ROLE')
        if cr.artifact_id in closure_ids:raise ContractError('CLOSURE_REUSED')
        closure_ids.add(cr.artifact_id);register(cr,'closure')
        closed=strict_json(read(cr))
        shape(closed,('schema_version','closure_id','obligation_id','owner','scope','definition_digest','authority_digest','candidate_digest','run_id','revision',
            'evidence_scope','status','created_at','expires_at','evidence','approvals'))
        if closed['schema_version']!=CLOSURE_SCHEMA:raise ContractError('CLOSURE_SCHEMA')
        bind=dict(closure_id=cr.artifact_id,obligation_id=oid,owner=o.owner,scope=o.scope,definition_digest=o.definition_digest,
            authority_digest=authority.content_digest,candidate_digest=c.content_digest,run_id=c.run_id,revision=c.revision,status='CLOSED',evidence_scope=o.evidence_scope)
        if any(type(closed[k]) is not type(v) or closed[k]!=v for k,v in bind.items()):codes.add('CLOSURE_BINDING_MISMATCH')
        if publication_policy.mode=='production' and closed['evidence_scope']!='NATIVE_PRODUCT':codes.add('DIAGNOSTIC_CLOSURE_NOT_PRODUCTION')
        created,expires=_lifetime(closed,authority,as_of,codes,'CLOSURE');expiry.append(expires)
        _authenticate(closed,o,authority,publication_policy.mode,as_of,codes)
        evidence=seq(closed['evidence'],'evidence',128)
        if not evidence:codes.add('CLOSURE_EVIDENCE_MISSING')
        check=TerminalRequirement('obligation',oid,o.evaluator_policy_digest,o.required_check_ids)
        artifacts=tuple(a for a in authority.artifacts if a.artifact_id in o.affected_artifact_ids)
        context=TerminalContext(c,publication_policy.release_policy.content_digest,None,'obligation',oid,cr.artifact_id,artifacts,
            as_of,created,expires,authority.max_lifetime_seconds,publication_policy.mode)
        for value in evidence:
            er=artifact_from_dict(value)
            if er.role!='report' or er.artifact_id in evidence_ids or er.artifact_id in closure_ids:raise ContractError('CLOSURE_EVIDENCE_ALIAS')
            evidence_ids.add(er.artifact_id);register(er,'closure_evidence')
            data=strict_json(read(er))
            if data.get('report_id')!=er.artifact_id:codes.add('CLOSURE_REPORT_ID_MISMATCH')
            if data.get('scope')!=o.evidence_scope:codes.add('CLOSURE_EVIDENCE_SCOPE_MISMATCH')
            def inspect(ref):
                if ref.artifact_id in closure_ids|evidence_ids:raise ContractError('CLOSURE_DEPENDENCY_CYCLE')
                register(ref,'closure_dependency');return read(ref)
            outcome=validate_terminal(data,context,check,inspect)
            codes.update(outcome.blockers)
            if outcome.expires_at is not None:expiry.append(outcome.expires_at)
    return InventoryResult(tuple(sorted(codes)),min(expiry) if expiry else None,tuple(sorted(checked)),authority.content_digest)


def _authenticate(raw,obligation,authority,mode,now,codes):
    from ..publication_v2.contracts import shape,seq
    keys={k.key_id:k for k in authority.closure_keys};seen=set();principals=set();groups=set();fingerprints=set()
    message=closure_signing_bytes(raw)
    for a in seq(raw['approvals'],'approvals',16):
        shape(a,('key_id','principal_id','purpose','signature'))
        for field in ('key_id','principal_id','purpose'):token(a[field],field)
        if a['key_id'] in seen:raise ContractError('DUPLICATE_CLOSURE_APPROVAL')
        seen.add(a['key_id']);k=keys.get(a['key_id'])
        if k is None:codes.add('UNKNOWN_CLOSURE_KEY');continue
        if not k.enabled:codes.add('REVOKED_CLOSURE_KEY');continue
        if not k.not_before<=raw['created_at']<=now<raw['expires_at']<=k.not_after:codes.add('CLOSURE_KEY_TIME');continue
        if mode=='production' and k.assurance!='operator_managed':codes.add('TEST_ONLY_CLOSURE_KEY');continue
        if a['principal_id']!=k.principal_id or a['purpose']!='gap_closure' or obligation.obligation_id not in k.obligation_ids:
            codes.add('UNAUTHORIZED_CLOSURE_PRINCIPAL');continue
        signature=hmac.new(k.secret,message,hashlib.sha256).hexdigest()
        if type(a['signature'])is not str or len(a['signature'])!=64 or any(x not in '0123456789abcdef' for x in a['signature']) or not hmac.compare_digest(signature,a['signature']):codes.add('BAD_CLOSURE_SIGNATURE');continue
        principals.add(k.principal_id);groups.add(k.independence_group);fingerprints.add(hashlib.sha256(k.secret).hexdigest())
    if min(len(principals),len(groups),len(fingerprints))<authority.minimum_independent_closers:codes.add('CLOSURE_INDEPENDENCE_FLOOR')
