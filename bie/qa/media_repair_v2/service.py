"""Authenticated generation feeding the unchanged REPAIR003 staging controller.

An operator must separately approve each NEW proposal and register fresh compile,
render/replay and regression checks. This API cannot approve or publish releases.
"""
from dataclasses import asdict
from pathlib import Path
import hashlib,os
from ..release_v2.contracts import ArtifactRef,ContractError,canonical_bytes,integer
from ..source_v2.io import SnapshotStore
from ..source_v2.codec import loads
from ..repair_v2.codec import decode
from ..reasoning_v2.attestation import ReviewVerifier
from ..repair_v2 import Proposal,Replacement
from ..repair_v2.planner import classify,approved,check_closure,validate_proposal
from ..domain_repair_v2.contracts import Generation
from ..visual_v2.models import VisualRequest
from ..animation_v2.models import AnimationRequest
from .contracts import *
from . import visual,animation,code_game
TYPES={'BIE-QA-REPAIR-008':(VisualRequest,VisualRepairPolicy),'BIE-QA-REPAIR-009':(AnimationRequest,AnimationRepairPolicy),'BIE-QA-REPAIR-010':(CodeRequest,CodePolicy),'BIE-QA-REPAIR-011':(GameRepairRequest,GameRepairPolicy)}
WORKERS={'BIE-QA-REPAIR-008':visual.repair,'BIE-QA-REPAIR-009':animation.repair,'BIE-QA-REPAIR-010':code_game.code,'BIE-QA-REPAIR-011':code_game.game}

def read_request(task,b):return decode(loads(b),TYPES[task][0])
def read_policy(task,b):return decode(loads(b),TYPES[task][1])

def preview(task,request,root,domain_policy,*,limits=Limits(),as_of=0):
    if task not in TYPES or type(request) is not TYPES[task][0] or type(domain_policy) is not TYPES[task][1] or type(limits) is not Limits:raise ContractError('MEDIA_REPAIR_INPUT_TYPE')
    integer(as_of,'as_of')
    payload,witness=WORKERS[task](request,root,domain_policy,limits,as_of)
    if type(payload) is not bytes or len(payload)>limits.max_generated_bytes:raise ContractError('MEDIA_REPAIR_OUTPUT_LIMIT')
    witness.update(status='UNAUTHORIZED_PREVIEW_ONLY',product_accepted=False,previous_candidate_reviews_reusable=False)
    return payload,witness

def generate(job,batch,snapshot,artifact_root,repair_policy,domain_policy,*,as_of,limits=Limits(),inventory_reviews=(),generation_reviews=(),verifier=None):
    if type(job) is not Job or type(limits) is not Limits:raise ContractError('MEDIA_REPAIR_INPUT_TYPE')
    integer(as_of,'as_of');verifier=ReviewVerifier() if verifier is None else verifier
    if type(domain_policy) is not TYPES[job.task_id][1]:raise ContractError('MEDIA_REPAIR_POLICY_TYPE')
    expected=(snapshot.content_digest,batch.content_digest,repair_policy.content_digest,domain_policy.content_digest,limits.content_digest)
    actual=(job.snapshot_digest,job.batch_digest,job.repair_policy_digest,job.domain_policy_digest,job.limits_digest)
    if actual!=expected:raise ContractError('MEDIA_REPAIR_JOB_BINDING')
    if job.target not in snapshot.artifacts or job.request not in snapshot.artifacts:raise ContractError('MEDIA_REPAIR_TARGET_NOT_IN_SNAPSHOT')
    plan=classify(batch,snapshot,artifact_root,repair_policy,as_of=as_of,reviews=inventory_reviews,verifier=verifier)
    if not plan.authenticated or plan.diagnostics:raise ContractError('MEDIA_REPAIR_INVENTORY_APPROVAL_REQUIRED')
    owner=TASK_OWNERS[job.task_id];route=next((r for r in repair_policy.routes if r.owner==owner),None)
    if route is None or job.target.path not in route.mutable_paths:raise ContractError('MEDIA_REPAIR_TARGET_NOT_OWNED')
    evidence=tuple(sorted({job.target.artifact_id,job.request.artifact_id}))
    ok,why=approved(generation_reviews,verifier,subject=job.job_id,purpose='inference',request_digest=job.content_digest,policy=repair_policy,evidence_ids=evidence,now=as_of)
    if not ok:raise ContractError('MEDIA_REPAIR_GENERATION_APPROVAL_REQUIRED',','.join(why))
    with SnapshotStore(artifact_root) as store:r=read_request(job.task_id,store.read(job.request));before=store.read(job.target)
    if (r.source.run_id,r.source.revision)!=(snapshot.run_id,snapshot.revision):raise ContractError('MEDIA_REPAIR_REQUEST_RUN_BINDING')
    refs=[s.artifact for s in r.source.sources]+[o.artifact for o in r.source.outputs]
    if any(a not in snapshot.artifacts for a in refs):raise ContractError('MEDIA_REPAIR_HIDDEN_ARTIFACT')
    if hasattr(r,'module') and r.module!=job.target:raise ContractError('MEDIA_REPAIR_MODULE_TARGET')
    qa=domain_policy.qa if hasattr(domain_policy,'qa') else domain_policy
    matching={b.artifact.sha256 for b in batch.reports if b.request_digest==r.content_digest and b.evaluator_policy_digest==qa.content_digest}
    targets=tuple(f.failure_id for f in plan.failures if f.owner==owner and f.automatic and f.report_sha256 in matching)
    if not targets:raise ContractError('MEDIA_REPAIR_NO_AUTHORIZED_FAILURE')
    payload,witness=preview(job.task_id,r,artifact_root,domain_policy,limits=limits,as_of=as_of)
    if payload==before:raise ContractError('MEDIA_REPAIR_NO_CHANGE')
    if len(payload)>repair_policy.max_replacement_bytes:raise ContractError('MEDIA_REPAIR_OUTPUT_LIMIT')
    with SnapshotStore(artifact_root) as store:
        for a in snapshot.artifacts:store.read(a)
    required,invalidated=check_closure(repair_policy,owner)
    witness.update(status='PROPOSAL_GENERATED_REVIEW_REQUIRED',target_failure_ids=targets,domain_policy_digest=domain_policy.content_digest,
        request_sha256=job.request.sha256,limits_digest=limits.content_digest,output_kind='declared_plan' if job.task_id.endswith(('008','009')) else 'generated_typescript',
        downstream_manifest_rebind_required=True,execution_evidence_reusable=False)
    return Generation(job.content_digest,plan.content_digest,job.target.sha256,payload,required,invalidated,canonical_bytes(witness))

def prepare(job,batch,snapshot,artifact_root,repair_policy,domain_policy,**kwargs):
    g=generate(job,batch,snapshot,artifact_root,repair_policy,domain_policy,**kwargs)
    directory=Path(artifact_root)/'proposals'
    if directory.is_symlink():raise ContractError('MEDIA_REPAIR_PROPOSAL_SYMLINK')
    directory.mkdir(mode=0o700,exist_ok=True)
    suffix='.json' if job.task_id.endswith(('008','009')) else '.ts'
    rel='proposals/media-'+g.content_digest+suffix;path=Path(artifact_root)/rel
    try:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:f.write(g.payload);f.flush();os.fsync(f.fileno())
    except OSError as exc:raise ContractError('MEDIA_REPAIR_PROPOSAL_EXISTS_OR_UNSAFE') from exc
    ref=ArtifactRef('media-replacement-'+g.content_digest[:32],rel,hashlib.sha256(g.payload).hexdigest(),len(g.payload),'support')
    targets=tuple(loads(g.witness)['target_failure_ids'])
    proposal=Proposal('media-proposal-'+g.content_digest[:32],snapshot.run_id,snapshot.revision,snapshot.content_digest,repair_policy.content_digest,
        g.plan_digest,TASK_OWNERS[job.task_id],targets,(Replacement(job.target.path,job.target.sha256,ref),))
    return proposal,g.receipt()
