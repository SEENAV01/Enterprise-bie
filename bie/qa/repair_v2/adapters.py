"""Reuse existing Report objects without trusting their mutable owner labels."""
from dataclasses import asdict
import hashlib
from ..source_v2.models import Report
from ..release_v2.contracts import ArtifactRef,ContractError,canonical_bytes
from .models import BoundReport

def bind_report(report,artifact_id,path):
    if type(report) is not Report:raise ContractError('REPAIR_NATIVE_REPORT_TYPE')
    data=canonical_bytes(report.to_dict())
    ref=ArtifactRef(artifact_id,path,hashlib.sha256(data).hexdigest(),len(data),'report')
    return BoundReport(ref,report.task_id,report.request_digest,report.policy_digest),data

def inspect_audio_invalidation(receipt):
    """Read the documented native H10 scope; never perform or certify dispatch."""
    if type(receipt) is not dict or receipt.get('schema_version')!='bie.audio.repair-invalidation/1' or receipt.get('product_accepted') is not False or receipt.get('repository_mutated') is not False:raise ContractError('REPAIR_NATIVE_AUDIO_SCOPE')
    rows=receipt.get('invalidations')
    if type(rows) is not list or not rows or len(rows)>128:raise ContractError('REPAIR_NATIVE_AUDIO_ROWS')
    ids=[]
    for r in rows:
        if type(r) is not dict or r.get('new_status')!='INVALIDATED' or type(r.get('task_id')) is not str:raise ContractError('REPAIR_NATIVE_AUDIO_STATUS')
        ids.append(r['task_id'])
    required={'AUDIO_TTS_CACHE','AUDIO_SYNC','AUDIO_MIX','CAPTIONS','ANIMATION_CLOCKS','AUDIO_QA','COMP_NARRATION_PLAN','COMP_GENERATED_SOURCE','RENDER'}
    if len(set(ids))!=len(ids) or set(ids)!=required:raise ContractError('REPAIR_NATIVE_AUDIO_COVERAGE')
    return dict(reported_invalidated_tasks=sorted(ids),dispatch_performed=False,artifact_bytes_verified=False,canonical_status_updated=False,requires_actual_downstream_rerun=True,product_accepted=False)
