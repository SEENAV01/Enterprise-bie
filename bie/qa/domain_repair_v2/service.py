"""Authenticated proposal generation over immutable, operator-owned artifact roots.

Generation never signs its own result. The inherited controller demands a NEW
proposal approval before staged execution, plus fresh downstream validation.
"""
from dataclasses import asdict
from pathlib import Path
import hashlib,os
from ..release_v2.contracts import ArtifactRef,ContractError,canonical_bytes,integer
from ..source_v2.io import SnapshotStore
from ..reasoning_v2.attestation import ReviewVerifier
from ..repair_v2 import Proposal,Replacement
from ..repair_v2.planner import classify,approved,check_closure,validate_proposal
from .contracts import Job,Limits,Generation,TASK_OWNERS
from .common import TYPES,read_request,source_of
from . import source,reasoning,pedagogy,director
WORKERS={'BIE-QA-REPAIR-004':source.repair,'BIE-QA-REPAIR-005':reasoning.repair,'BIE-QA-REPAIR-006':pedagogy.repair,'BIE-QA-REPAIR-007':director.repair}

def generate(job,batch,snapshot,artifact_root,repair_policy,domain_policy,*,as_of,limits=Limits(),
             inventory_reviews=(),generation_reviews=(),verifier=None):
    if type(job) is not Job or type(limits) is not Limits:raise ContractError('DOMAIN_REPAIR_INPUT_TYPE')
    integer(as_of,'as_of');verifier=ReviewVerifier() if verifier is None else verifier
    if type(domain_policy) is not TYPES[job.task_id][1]:raise ContractError('DOMAIN_REPAIR_POLICY_TYPE')
    expected=(snapshot.content_digest,batch.content_digest,repair_policy.content_digest,domain_policy.content_digest,limits.content_digest)
    actual=(job.snapshot_digest,job.batch_digest,job.repair_policy_digest,job.domain_policy_digest,job.limits_digest)
    if actual!=expected:raise ContractError('DOMAIN_REPAIR_JOB_BINDING')
    if job.target not in snapshot.artifacts:raise ContractError('DOMAIN_REPAIR_TARGET_NOT_IN_SNAPSHOT')
    plan=classify(batch,snapshot,artifact_root,repair_policy,as_of=as_of,reviews=inventory_reviews,verifier=verifier)
    if not plan.authenticated or plan.diagnostics:raise ContractError('DOMAIN_REPAIR_INVENTORY_APPROVAL_REQUIRED')
    owner=TASK_OWNERS[job.task_id]
    route=next((r for r in repair_policy.routes if r.owner==owner),None)
    if route is None or job.target.path not in route.mutable_paths:raise ContractError('DOMAIN_REPAIR_TARGET_NOT_OWNED')
    ok,why=approved(generation_reviews,verifier,subject=job.job_id,purpose='inference',request_digest=job.content_digest,
        policy=repair_policy,evidence_ids=(job.target.artifact_id,),now=as_of)
    if not ok:raise ContractError('DOMAIN_REPAIR_GENERATION_APPROVAL_REQUIRED',','.join(why))
    with SnapshotStore(artifact_root) as store:before=store.read(job.target)
    request=read_request(job.task_id,before);src=source_of(request)
    if (src.run_id,src.revision)!=(snapshot.run_id,snapshot.revision):raise ContractError('DOMAIN_REPAIR_REQUEST_RUN_BINDING')
    declared=[s.artifact for s in src.sources]+[o.artifact for o in src.outputs]
    if any(a not in snapshot.artifacts for a in declared):raise ContractError('DOMAIN_REPAIR_HIDDEN_ARTIFACT')
    matching_reports={b.artifact.sha256 for b in batch.reports if b.request_digest==request.content_digest and b.evaluator_policy_digest==domain_policy.content_digest}
    targets=tuple(f.failure_id for f in plan.failures if f.owner==owner and f.automatic and f.report_sha256 in matching_reports)
    if not targets:raise ContractError('DOMAIN_REPAIR_NO_AUTHORIZED_FAILURE')
    after,witness=WORKERS[job.task_id](request,artifact_root,domain_policy,limits)
    from .validation import evaluate_candidate,status_of
    post=evaluate_candidate(job.task_id,after,artifact_root,domain_policy,as_of=as_of)
    selected={'BIE-QA-REPAIR-004':('provenance',),'BIE-QA-REPAIR-005':('validity',),
              'BIE-QA-REPAIR-006':('sequence','assessment'),'BIE-QA-REPAIR-007':('pacing',)}[job.task_id]
    if any(getattr(post,area).status=='BLOCKED' for area in selected):raise ContractError('DOMAIN_REPAIR_POSTCHECK_BLOCKED')
    # Unsigned semantic/evidence checks may still block. Preserve them explicitly;
    # generating a proposed change does NOT authorize staged execution or release.
    def blockers(obj):
        found=[]
        if type(obj) is dict:
            if obj.get('severity')=='BLOCKER':found.append(obj)
            for v in obj.values():found.extend(blockers(v))
        elif type(obj) in (list,tuple):
            for v in obj:found.extend(blockers(v))
        return found
    witness.update(open_postcheck_blockers=blockers(post.to_dict()),checked_repair_areas=selected)
    witness.update(unsigned_postcheck_status=status_of(post),postcheck_fingerprint=__import__('hashlib').sha256(canonical_bytes(post.to_dict())).hexdigest())
    payload=canonical_bytes(asdict(after))
    if hashlib.sha256(payload).hexdigest()==job.target.sha256:raise ContractError('DOMAIN_REPAIR_NO_CHANGE')
    if len(payload)>min(limits.max_generated_bytes,repair_policy.max_replacement_bytes):raise ContractError('DOMAIN_REPAIR_OUTPUT_LIMIT')
    # Re-read all original inputs after generation; the function does not write them.
    with SnapshotStore(artifact_root) as store:
        for a in snapshot.artifacts:store.read(a)
    required,invalidated=check_closure(repair_policy,owner)
    witness.update(target_failure_ids=targets,domain_policy_digest=domain_policy.content_digest,limits_digest=limits.content_digest)
    return Generation(job.content_digest,plan.content_digest,job.target.sha256,payload,required,invalidated,canonical_bytes(witness))

def prepare(job,batch,snapshot,artifact_root,repair_policy,domain_policy,**kwargs):
    """Recompute and publish only a NEW content-addressed proposal, never source edits.

    artifact_root is a private operator-owned directory. Parent directories must
    not be writable by untrusted users. This is not a hostile-code isolation claim.
    """
    g=generate(job,batch,snapshot,artifact_root,repair_policy,domain_policy,**kwargs)
    owner=TASK_OWNERS[job.task_id];sha=hashlib.sha256(g.payload).hexdigest()
    directory=Path(artifact_root)/'proposals'
    if directory.is_symlink():raise ContractError('DOMAIN_REPAIR_PROPOSAL_SYMLINK')
    directory.mkdir(mode=0o700,exist_ok=True)
    relative='proposals/domain-'+g.content_digest+'.json';path=Path(artifact_root)/relative
    try:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(g.payload);stream.flush();os.fsync(stream.fileno())
    except OSError as exc:raise ContractError('DOMAIN_REPAIR_PROPOSAL_EXISTS_OR_UNSAFE') from exc
    ref=ArtifactRef('domain-replacement-'+g.content_digest[:32],relative,sha,len(g.payload),'support')
    import json
    targets=tuple(json.loads(g.witness)['target_failure_ids'])
    proposal=Proposal('domain-proposal-'+g.content_digest[:32],snapshot.run_id,snapshot.revision,snapshot.content_digest,
        repair_policy.content_digest,g.plan_digest,owner,targets,(Replacement(job.target.path,job.target.sha256,ref),))
    return proposal,g.receipt()
