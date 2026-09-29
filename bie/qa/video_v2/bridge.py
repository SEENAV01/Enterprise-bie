"""Unsigned evidence only. Technical diagnostics cannot certify full BIE media."""
import hashlib
from ..release_v2.contracts import ArtifactRef,ReleaseCandidate,GateEvidence,ContractError,canonical_bytes
from ..release_v2.policy import ReleasePolicy,enterprise_policy
from ..source_v2.io import SnapshotStore
from ..source_v2.bridge import PreparedEvidence
from .models import VideoRequest,VideoPolicy,all_refs
from .codec import load_receipt
from .evaluator import evaluate

def prepare_release_evidence(request,candidate,artifact_root,policy,*,as_of,release_policy=None,**options):
    if type(request) is not VideoRequest or type(candidate) is not ReleaseCandidate or type(policy) is not VideoPolicy:raise ContractError('VIDEO_BRIDGE_TYPE')
    if (request.candidate_digest,request.run_id,request.revision)!=(candidate.content_digest,candidate.run_id,candidate.revision):raise ContractError('VIDEO_CANDIDATE_BINDING')
    idx={a.artifact_id:a for a in candidate.artifacts};required=list(all_refs(request))+[r.reference for r in policy.regions]
    with SnapshotStore(artifact_root) as store:
        for ref in (request.compile_receipt,request.render_receipt):
            try:r=load_receipt(store.read(ref));required.extend((r.stdout,r.stderr))
            except ContractError:pass # evaluator records broken bytes; never promote to PASS
    if any(idx.get(a.artifact_id)!=a for a in required):raise ContractError('VIDEO_CANDIDATE_ARTIFACT')
    rp=enterprise_policy() if release_policy is None else release_policy
    if type(rp) is not ReleasePolicy:raise ContractError('VIDEO_RELEASE_POLICY')
    result=evaluate(request,artifact_root,policy,as_of=as_of,**options)
    if not result.inspected_artifact_ids:raise ContractError('VIDEO_NO_INSPECTED_ARTIFACTS')
    if not set(result.inspected_artifact_ids)<=set(idx):raise ContractError('VIDEO_UNBOUND_INSPECTED_ARTIFACT')
    envelopes=[]
    for gate in ('code_compile','video_render','rendered_frame_inspection'):
        data=canonical_bytes(dict(gate=gate,video_report=result.to_dict(),native_pipeline_execution_verified=False,product_accepted=False))
        aid='qa16-'+gate.replace('_','-');path=f'qa_video_reports/{request.content_digest}/{gate}.json'
        if aid in idx or path in {a.path for a in candidate.artifacts}:raise ContractError('VIDEO_REPORT_COLLISION')
        ref=ArtifactRef(aid,path,hashlib.sha256(data).hexdigest(),len(data),'report')
        status='FAIL' if result.status=='BLOCKED' else 'NOT_RUN'
        codes=tuple(sorted({f.code for report in result.reports for f in report.findings if f.severity!='INFO'}))[:124]+('NATIVE_PIPELINE_AND_FULL_MEDIA_OPEN','UNSIGNED_VIDEO_EVIDENCE')
        envelope=GateEvidence('2.0.0',aid,gate,candidate.content_digest,rp.content_digest,candidate.run_id,candidate.revision,status,'bie-qa-video-v2','1.0.0','review',result.inspected_artifact_ids,ref,as_of,as_of+min(policy.max_receipt_age_seconds,rp.max_evidence_lifetime_seconds),codes,'UNSIGNED','')
        envelopes.append(PreparedEvidence(envelope,data))
    return tuple(envelopes)
