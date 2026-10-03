"""Finish only a proven canonical terminal result after a real process cut.

No pipeline rerun, invented transition, result synthesis, new queue or redrive.
Caller holds the same catalogue write lock as controlled worker execution and
has verified tenant, expected worker record, permission and unused audit credit.
Every required artifact/claim is checked before any canonical finalization.
"""
import time
from bie.infrastructure.artifact_store import BlobRef
from apps.api.job_service import STAGE_ID
from .contracts import require,strict_json

def finalize_verified_terminal(service,p,native,body,worker_id):
    snap,attempt,q=service._native_identity(native,body)
    changes=dict(queue_state_modified=False,native_run_state_modified=False,
                 idempotency_state_modified=False,native_attempt_state_modified=False)
    if attempt['state']=='FAILED' and q.state=='DELIVERED':
        return finalize_verified_failure(service,p,native,body,worker_id,snap,attempt,q,changes)
    if attempt['state']!='SUCCEEDED':
        service._snapshot(native,body)
        return changes
    service.administration._queue_item(body,q,None,time.time())
    job=body['native_job_id'];suffix=job[4:]
    source_id='source-'+suffix;result_id='result-'+suffix;evidence_id='evidence-'+suffix
    require(q.state in ('DELIVERED','ACKED') and q.consumer_id==worker_id,
            'terminal_recovery_delivery_mismatch')
    require(snap['run_state'] in ('ACTIVE','EXECUTION_COMPLETE') and
            attempt['input_artifact_refs']==[source_id] and attempt['output_artifact_refs']==[result_id] and
            attempt['evidence_refs']==[evidence_id] and attempt['diagnostics']==[],
            'terminal_recovery_result_invalid')
    require([(e['from_state'],e['to_state'],e['reason']) for e in snap['events']]==
            [('PENDING','READY','source_stored'),('READY','RUNNING','worker_started'),
             ('RUNNING','SUCCEEDED','inspection_complete')], 'terminal_recovery_history_invalid')
    def load(artifact_id,kind,parents,evidence,max_bytes):
        record=native.persistence.load_artifact(artifact_id)
        require(record.artifact_id==artifact_id and record.run_id==job and record.stage_id==STAGE_ID and
                record.artifact_type==kind and record.evidence is evidence and
                record.parent_artifact_ids==parents and 0<record.blob_size<=max_bytes,
                'terminal_recovery_artifact_invalid')
        raw=native.cas.get_bytes(BlobRef(record.blob_algorithm,record.blob_digest,record.blob_size))
        return record,raw
    source,raw_source=load(source_id,'document.source.pdf',[],False,service.limit)
    require(source.blob_digest==body['source_hash'] and source.metadata['source_hash']==body['source_hash'],
            'terminal_recovery_source_invalid')
    result,raw_result=load(result_id,'document.inspection.safe_json',[source_id],False,8*1024**2)
    value=strict_json(raw_result,8*1024**2)
    require(value['source_hash']==body['source_hash'] and value['byte_length']==len(raw_source) and
            result.metadata['source_hash']==body['source_hash'],'terminal_recovery_source_invalid')
    evidence,raw_evidence=load(evidence_id,'document.inspection.evidence',[result_id],True,16*1024)
    receipt=strict_json(raw_evidence)
    require(receipt==dict(job_id=job,source_hash=body['source_hash'],result_blob_hash=result.blob_digest,
            result_byte_length=result.blob_size,runtime_policy=value['toc_reconciliation_policy'],
            page_count=value['page_count'],total_blocks=value['total_blocks'],status='SUCCEEDED') and
            evidence.metadata=={'status':'SUCCEEDED'},'terminal_recovery_evidence_invalid')
    claim=native.idempotency.get(body['native_key'])
    require(claim.owner==job and claim.fingerprint==body['source_hash'] and
            ((claim.state=='CLAIMED' and claim.result_ref is None) or
             (claim.state=='COMPLETED' and claim.result_ref==result_id)),
            'terminal_recovery_idempotency_invalid')
    # All checks precede writes. A later crash can replay these same native APIs
    # from their durable intermediate state; it cannot grant a false success.
    if snap['run_state']!='EXECUTION_COMPLETE':
        service.authorize(p,'admin_recover');native.persistence.set_run_state(job,'EXECUTION_COMPLETE')
        changes['native_run_state_modified']=True
    if q.state=='DELIVERED':
        service.authorize(p,'admin_recover');native.queue.ack(q.task.task_id,worker_id)
        changes['queue_state_modified']=True
    if claim.state!='COMPLETED':
        service.authorize(p,'admin_recover');native.idempotency.complete(body['native_key'],job,result_id)
        changes['idempotency_state_modified']=True
    service._snapshot(native,body)
    return changes

def finalize_verified_failure(service,p,native,body,worker_id,snap,attempt,q,changes):
    """Finish proven FAILED bookkeeping, never create a result or a new attempt."""
    job=body['native_job_id'];suffix=job[4:];source_id='source-'+suffix;evidence_id='evidence-'+suffix
    service.administration._queue_item(body,q,None,time.time())
    require(q.state=='DELIVERED' and q.consumer_id==worker_id,'terminal_recovery_delivery_mismatch')
    codes=attempt['diagnostics']
    quota_failure=(type(codes) is list and len(codes)==1 and
                   codes[0] in ('cas_capacity_reached','cas_blob_too_large'))
    require(snap['run_state'] in ('ACTIVE','BLOCKED') and attempt['input_artifact_refs']==[source_id] and
            attempt['output_artifact_refs']==[] and
            ((quota_failure and attempt['evidence_refs']==[]) or
             (type(codes) is list and len(codes)==1 and codes[0] in ('pdf_inspection_failed','internal_worker_error')
              and attempt['evidence_refs']==[evidence_id])),
            'terminal_recovery_failure_invalid')
    code=codes[0]
    require([(e['from_state'],e['to_state'],e['reason']) for e in snap['events']]==
        [('PENDING','READY','source_stored'),('READY','RUNNING','worker_started'),('RUNNING','FAILED',code)],
        'terminal_recovery_history_invalid')
    source=native.persistence.load_artifact(source_id)
    require(source.artifact_id==source_id and source.run_id==job and source.stage_id==STAGE_ID and
            source.artifact_type=='document.source.pdf' and source.evidence is False and
            source.parent_artifact_ids==[] and 0<source.blob_size<=service.limit and
            source.blob_digest==body['source_hash'] and source.metadata['source_hash']==body['source_hash'],
            'terminal_recovery_source_invalid')
    raw_source=native.cas.get_bytes(BlobRef(source.blob_algorithm,source.blob_digest,source.blob_size))
    require(len(raw_source)==source.blob_size,'terminal_recovery_source_invalid')
    if quota_failure:
        # The existing governed quota fallback records FAILED in the native
        # transition journal precisely because even its failure evidence cannot
        # be stored. Do not demand or synthesize a CAS receipt. Require the exact
        # source/config/worker/claim/history binding above, unchanged budget
        # policy and absence of result/evidence registration before finalizing.
        service.cas_budget.verify_policy()
        records=native.persistence.artifacts_for_run(job)
        require(evidence_id not in records and 'result-'+suffix not in records,
                'terminal_recovery_evidence_invalid')
    else:
        evidence=native.persistence.load_artifact(evidence_id)
        require(evidence.artifact_id==evidence_id and evidence.run_id==job and evidence.stage_id==STAGE_ID and
                evidence.artifact_type=='document.inspection.evidence' and evidence.evidence is True and
                evidence.parent_artifact_ids==[source_id] and evidence.metadata=={'status':'FAILED'} and
                0<evidence.blob_size<=16*1024,'terminal_recovery_evidence_invalid')
        raw=native.cas.get_bytes(BlobRef(evidence.blob_algorithm,evidence.blob_digest,evidence.blob_size))
        require(strict_json(raw)==dict(job_id=job,source_hash=body['source_hash'],status='FAILED',diagnostic_code=code),
                'terminal_recovery_evidence_invalid')
    claim=native.idempotency.get(body['native_key'])
    require(claim.owner==job and claim.fingerprint==body['source_hash'] and claim.state=='CLAIMED' and
            claim.result_ref is None,'terminal_recovery_idempotency_invalid')
    # The canonical failed job intentionally has no completed result claim.
    # Preserve it. No extraction, failure reclassification, retry or fake CAS
    # evidence. A later crash replays from the existing durable terminal state.
    if snap['run_state']!='BLOCKED':
        service.authorize(p,'admin_recover');native.persistence.set_run_state(job,'BLOCKED')
        changes['native_run_state_modified']=True
    service.authorize(p,'admin_recover');native.queue.dead_letter(q.task.task_id,code)
    changes['queue_state_modified']=True
    service._snapshot(native,body)
    return changes
