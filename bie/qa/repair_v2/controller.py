"""Stage bounded proposals without ever changing original artifact files.

Verified results are retained for review, never merged, deployed or accepted.
Failure reports are re-read/reclassified; caller-supplied plan booleans are not trusted.
"""
from __future__ import annotations
from dataclasses import asdict,replace
from pathlib import Path
import hashlib,os,shutil,tempfile,stat
from ..release_v2.contracts import ContractError,canonical_bytes,digest,integer
from ..source_v2.io import SnapshotStore
from ..reasoning_v2.attestation import ReviewVerifier
from .models import Snapshot,RepairPolicy,Proposal
from .planner import classify,validate_proposal,approved
from .journal import Journal
from .worker import run_checks,validate_registry

def verify_snapshot(root,snapshot):
    root=Path(root);expected={a.path for a in snapshot.artifacts};actual=set()
    for p in root.rglob('*'):
        st=p.lstat()
        if stat.S_ISDIR(st.st_mode):continue
        if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1:raise ContractError('REPAIR_STAGE_UNSAFE_ENTRY')
        actual.add(p.relative_to(root).as_posix())
    if actual!=expected:raise ContractError('REPAIR_STAGE_FILE_SET')
    with SnapshotStore(root) as store:
        for a in snapshot.artifacts:store.read(a)
    return snapshot.content_digest

def execute(batch,snapshot,artifact_root,policy,proposal,*,as_of,output_root,journal,
            checks,inventory_reviews=(),proposal_reviews=(),verifier=None):
    integer(as_of,'as_of')
    if type(journal) is not Journal or type(policy) is not RepairPolicy or type(snapshot) is not Snapshot or type(proposal) is not Proposal:raise ContractError('REPAIR_EXECUTION_TYPE')
    if journal.snapshot!=snapshot or journal.policy!=policy:raise ContractError('REPAIR_JOURNAL_CONTEXT')
    verifier=ReviewVerifier() if verifier is None else verifier
    plan=classify(batch,snapshot,artifact_root,policy,as_of=as_of,reviews=inventory_reviews,verifier=verifier)
    required,invalidated=validate_proposal(proposal,plan,snapshot,policy)
    valid,reasons=approved(proposal_reviews,verifier,subject=proposal.proposal_id,purpose='inference',request_digest=proposal.content_digest,policy=policy,evidence_ids=tuple(r.artifact.artifact_id for r in proposal.replacements),now=as_of)
    if not valid:raise ContractError('REPAIR_PROPOSAL_APPROVAL_REQUIRED',','.join(reasons))
    if type(checks) is not dict or not set(required)<=set(checks) or any(not callable(checks[k]) for k in required):raise ContractError('REPAIR_REQUIRED_CHECK_UNAVAILABLE')
    validate_registry(policy,required,checks)
    base=Path(artifact_root).resolve();out=Path(output_root)
    if not out.is_dir() or out.is_symlink():raise ContractError('REPAIR_OUTPUT_ROOT')
    out=out.resolve()
    if out==base or out.is_relative_to(base) or base.is_relative_to(out):raise ContractError('REPAIR_OUTPUT_OVERLAPS_ORIGINAL')
    attempt=journal.reserve(proposal,as_of);stage=None;result=None;errors=[];candidate=None;worker=None
    try:
        # Read original/new bytes once via the inherited confined, hash-checked reader.
        with SnapshotStore(base) as store:original={a.path:store.read(a) for a in snapshot.artifacts}
        with SnapshotStore(base) as store:new={r.path:store.read(r.artifact) for r in proposal.replacements}
        repl={r.path:r for r in proposal.replacements}
        candidate=Snapshot(snapshot.run_id,snapshot.revision,tuple(replace(a,sha256=repl[a.path].artifact.sha256,size=repl[a.path].artifact.size) if a.path in repl else a for a in snapshot.artifacts))
        stage=Path(tempfile.mkdtemp(prefix='repair-private-',dir=out));os.chmod(stage,0o700)
        for path,data in {**original,**new}.items():
            p=stage/path;p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        verify_snapshot(stage,candidate)
        worker=run_checks(stage,candidate,policy,required,checks)
        if worker['error']:errors.append(worker['error'])
        if any(r.status!='PASS' for r in worker['outcomes']):errors.append('REPAIR_REVALIDATION_NOT_PASS')
        if len(worker['outcomes'])!=len(required):errors.append('REPAIR_REVALIDATION_INCOMPLETE')
        verify_snapshot(stage,candidate)
        # Original immutability is checked again after validators exit.
        with SnapshotStore(base) as store:
            for a in snapshot.artifacts:store.read(a)
        if not errors:
            target=out/('candidate-'+proposal.content_digest)
            if target.exists() or target.is_symlink():raise ContractError('REPAIR_OUTPUT_ALREADY_EXISTS')
            # Private parent/no untrusted writers is the documented POSIX precondition.
            os.rename(stage,target);stage=None;result=str(target)
    except (ContractError,OSError,ValueError) as exc:
        errors.append(exc.code if isinstance(exc,ContractError) else 'REPAIR_FILESYSTEM_OR_WORKER_ERROR')
    finally:
        if stage is not None:shutil.rmtree(stage,ignore_errors=True)
    status='STAGED_FOR_REVIEW' if result else 'REJECTED'
    receipt=dict(schema_version='bie.qa.repair-attempt/1',attempt=attempt,proposal_id=proposal.proposal_id,
        proposal_digest=proposal.content_digest,base_digest=snapshot.content_digest,policy_digest=policy.content_digest,
        plan_digest=plan.content_digest,status=status,diagnostics=tuple(sorted(set(errors))),
        candidate=asdict(candidate) if candidate else None,candidate_digest=candidate.content_digest if candidate else '',
        staged_directory=result,required_checks=required,invalidated_previous_checks=invalidated,
        outcomes=[asdict(x) for x in worker['outcomes']] if worker else [],worker_error=worker['error'] if worker else '',
        worker_elapsed_ms=worker['elapsed_ms'] if worker else 0,worker_executed=bool(worker),
        original_files_written=False,canonical_repository_modified=False,product_accepted=False,
        downstream_previous_evidence_reusable=False,hostile_code_sandbox_verified=False,
        remaining_failure_ids=tuple(f.failure_id for f in plan.failures if f.failure_id not in proposal.target_failure_ids),
        promotion_requires='fresh canonical downstream execution and review; never automatic release')
    receipt['receipt_digest']=digest(receipt)
    receipt['journal_head']=journal.finish(attempt,status,receipt['receipt_digest'])
    return receipt
