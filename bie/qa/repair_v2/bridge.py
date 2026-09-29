"""Repaired candidates invalidate prior success; emit unsigned NOT_RUN only."""
import hashlib
from ..release_v2.contracts import ContractError,ReleaseCandidate,ArtifactRef,GateEvidence,canonical_bytes,digest
from ..release_v2.policy import enterprise_policy
from ..source_v2.bridge import PreparedEvidence
from .models import Snapshot
from .codec import decode
from ..source_v2.codec import loads
from .controller import verify_snapshot

def prepare_release_evidence(receipt,candidate,artifact_root,*,as_of):
    if type(receipt) is not dict or type(candidate) is not ReleaseCandidate:raise ContractError('REPAIR_BRIDGE_TYPE')
    body={k:v for k,v in receipt.items() if k not in ('receipt_digest','journal_head')}
    if digest(body)!=receipt.get('receipt_digest'):raise ContractError('REPAIR_RECEIPT_INTEGRITY')
    if receipt.get('status')!='STAGED_FOR_REVIEW' or receipt.get('product_accepted') is not False or receipt.get('downstream_previous_evidence_reusable') is not False:raise ContractError('REPAIR_BRIDGE_SCOPE')
    snapshot=decode(loads(canonical_bytes(receipt['candidate'])),Snapshot)
    if (candidate.run_id,candidate.revision)!=(snapshot.run_id,snapshot.revision) or set(candidate.artifacts)!=set(snapshot.artifacts) or receipt['candidate_digest']!=snapshot.content_digest:raise ContractError('REPAIR_RELEASE_CANDIDATE_BINDING')
    verify_snapshot(artifact_root,snapshot)
    data=canonical_bytes(dict(attempt=receipt,full_repository_regression_run=False,product_accepted=False))
    aid='qa16-repair-regression';ref=ArtifactRef(aid,f'qa_repair_reports/{candidate.content_digest}/regression.json',hashlib.sha256(data).hexdigest(),len(data),'report')
    if aid in {a.artifact_id for a in candidate.artifacts} or ref.path in {a.path for a in candidate.artifacts}:raise ContractError('REPAIR_REPORT_COLLISION')
    rp=enterprise_policy()
    e=GateEvidence('2.0.0',aid,'regression',candidate.content_digest,rp.content_digest,candidate.run_id,candidate.revision,'NOT_RUN','bie-qa-repair-v2','1.0.0','review',tuple(sorted(a.artifact_id for a in snapshot.artifacts)),ref,as_of,as_of+3600,('CANONICAL_REPAIR_REGRESSION_PENDING','UNSIGNED_REPAIR_EVIDENCE'),'UNSIGNED','')
    return PreparedEvidence(e,data)
