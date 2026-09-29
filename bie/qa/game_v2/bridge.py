"""Unsigned FAIL/NOT_RUN only; no game acceptance from diagnostic evidence."""
import hashlib
from ..release_v2.contracts import ArtifactRef,ReleaseCandidate,GateEvidence,ContractError,canonical_bytes
from ..release_v2.policy import ReleasePolicy,enterprise_policy
from ..source_v2.io import SnapshotStore
from ..source_v2.bridge import PreparedEvidence
from .models import GameRequest,GamePolicy,all_refs
from .codec import load_build,load_runtime
from .evaluator import evaluate

def prepare_release_evidence(request,candidate,artifact_root,policy,*,as_of,release_policy=None,**options):
    if type(request) is not GameRequest or type(candidate) is not ReleaseCandidate or type(policy) is not GamePolicy:raise ContractError('GAME_BRIDGE_TYPE')
    if (request.candidate_digest,request.run_id,request.revision)!=(candidate.content_digest,candidate.run_id,candidate.revision):raise ContractError('GAME_CANDIDATE_BINDING')
    idx={x.artifact_id:x for x in candidate.artifacts};required=list(all_refs(request))
    with SnapshotStore(artifact_root) as store:
        try:
            b=load_build(store.read(request.build_receipt));required.extend((b.stdout,b.stderr))
        except ContractError:pass
        try:
            r=load_runtime(store.read(request.runtime_receipt));required.extend(s.screenshot for t in r.traces for s in t.steps)
        except ContractError:pass
    if any(idx.get(a.artifact_id)!=a for a in required):raise ContractError('GAME_CANDIDATE_ARTIFACT')
    rp=enterprise_policy() if release_policy is None else release_policy
    if type(rp) is not ReleasePolicy:raise ContractError('GAME_RELEASE_POLICY')
    result=evaluate(request,artifact_root,policy,as_of=as_of,**options)
    if not result.inspected_artifact_ids or not set(result.inspected_artifact_ids)<=set(idx):raise ContractError('GAME_UNBOUND_INSPECTED_ARTIFACT')
    out=[]
    for gate in ('game_build','game_runtime','game_interactions','game_learning_alignment'):
        data=canonical_bytes(dict(gate=gate,game_report=result.to_dict(),native_game_acceptance=False,product_accepted=False))
        aid='qa16-'+gate.replace('_','-');path=f'qa_game_reports/{request.content_digest}/{gate}.json'
        if aid in idx or path in {a.path for a in candidate.artifacts}:raise ContractError('GAME_REPORT_COLLISION')
        ref=ArtifactRef(aid,path,hashlib.sha256(data).hexdigest(),len(data),'report')
        codes=tuple(sorted({f.code for r in result.reports for f in r.findings if f.severity!='INFO'}))[:124]+('NATIVE_GAME_AND_LEARNING_VALIDATION_OPEN','UNSIGNED_GAME_EVIDENCE')
        e=GateEvidence('2.0.0',aid,gate,candidate.content_digest,rp.content_digest,candidate.run_id,candidate.revision,'FAIL' if result.status=='BLOCKED' else 'NOT_RUN','bie-qa-game-v2','1.0.0','review',result.inspected_artifact_ids,ref,as_of,as_of+min(policy.max_receipt_age_seconds,rp.max_evidence_lifetime_seconds),codes,'UNSIGNED','')
        out.append(PreparedEvidence(e,data))
    return tuple(out)
