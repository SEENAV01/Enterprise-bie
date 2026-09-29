"""Recompute repair receipt lineage, journal chain and generation identities.

Unsigned digests identify bytes, not who executed them. Authentication is checked
separately by the auditor; an operator-owned journal export is not a remote ledger.
"""
from dataclasses import asdict
from ..release_v2.contracts import ContractError,canonical_bytes,digest,integer,token,sha256,choice
from ..repair_v2.codec import decode
from ..repair_v2.models import Snapshot,CheckOutcome
from ..repair_v2.planner import check_closure
from .models import candidate_for
from .io import equal,fields,object_bytes

ATTEMPT_FIELDS = ('schema_version attempt proposal_id proposal_digest base_digest policy_digest plan_digest status diagnostics '
    'candidate candidate_digest staged_directory required_checks invalidated_previous_checks outcomes worker_error worker_elapsed_ms '
    'worker_executed original_files_written canonical_repository_modified product_accepted downstream_previous_evidence_reusable '
    'hostile_code_sandbox_verified remaining_failure_ids promotion_requires receipt_digest journal_head').split()
RESERVED_FIELDS='kind attempt proposal_id proposal_digest effect_digest reserved_at reserved_bytes reserved_seconds'.split()
FINISHED_FIELDS='kind attempt status receipt_digest'.split()

def inspect_journal(obj,snapshot,proposal,repair_policy,attempt,*,as_of,max_age):
    fields(obj,('binding','events','chain_head','product_accepted'),'AUDIT_JOURNAL_SCHEMA')
    equal(obj['product_accepted'],False,'AUDIT_JOURNAL_ACCEPTANCE')
    binding=dict(run_id=snapshot.run_id,revision=snapshot.revision,snapshot_digest=snapshot.content_digest,policy_digest=repair_policy.content_digest)
    equal(obj['binding'],binding,'AUDIT_JOURNAL_BINDING')
    events=obj['events']
    if type(events) is not list or not 2<=len(events)<=2*repair_policy.max_attempts:
        raise ContractError('AUDIT_JOURNAL_EVENT_LIMIT')
    head=digest(binding);pending=None;reserved=[];ids=set();effects=set();selected=None;staged=False;last_clock=-1
    for sequence,event in enumerate(events,1):
        if type(event) is not dict:raise ContractError('AUDIT_JOURNAL_EVENT_SCHEMA')
        if staged:raise ContractError('AUDIT_JOURNAL_AFTER_STAGED')
        if event.get('kind')=='RESERVED':
            fields(event,RESERVED_FIELDS,'AUDIT_RESERVATION_SCHEMA')
            if pending is not None:raise ContractError('AUDIT_JOURNAL_PENDING')
            integer(event['attempt'],'attempt',1,repair_policy.max_attempts)
            equal(event['attempt'],len(reserved)+1,'AUDIT_ATTEMPT_ORDER')
            token(event['proposal_id'],'proposal_id')
            for k in ('proposal_digest','effect_digest'):sha256(event[k],k)
            if event['proposal_id'] in ids or event['effect_digest'] in effects:raise ContractError('AUDIT_JOURNAL_REPLAY')
            integer(event['reserved_at'],'reserved_at')
            if not last_clock<=event['reserved_at']<=as_of:raise ContractError('AUDIT_JOURNAL_CLOCK')
            last_clock=event['reserved_at']
            integer(event['reserved_bytes'],'reserved_bytes',1,repair_policy.max_replacement_bytes)
            equal(event['reserved_seconds'],repair_policy.worker_timeout_seconds,'AUDIT_RESERVATION_TIME')
            ids.add(event['proposal_id']);effects.add(event['effect_digest']);reserved.append(event);pending=event
        elif event.get('kind')=='FINISHED':
            fields(event,FINISHED_FIELDS,'AUDIT_FINISH_SCHEMA')
            if pending is None:raise ContractError('AUDIT_ORPHAN_FINISH')
            equal(event['attempt'],pending['attempt'],'AUDIT_FINISH_ATTEMPT')
            choice(event['status'],('REJECTED','STAGED_FOR_REVIEW'),'status');sha256(event['receipt_digest'],'receipt_digest')
            if event['attempt']==attempt['attempt']:
                equal(pending['proposal_id'],proposal.proposal_id,'AUDIT_RESERVED_PROPOSAL')
                equal(pending['proposal_digest'],proposal.content_digest,'AUDIT_RESERVED_PROPOSAL')
                equal(pending['effect_digest'],proposal.effect_digest,'AUDIT_RESERVED_EFFECT')
                equal(pending['reserved_bytes'],sum(r.artifact.size for r in proposal.replacements),'AUDIT_RESERVED_SIZE')
                equal(event['receipt_digest'],attempt['receipt_digest'],'AUDIT_FINISH_RECEIPT')
                equal(event['status'],attempt['status'],'AUDIT_FINISH_STATUS')
                selected=pending
            staged=event['status']=='STAGED_FOR_REVIEW';pending=None
        else:raise ContractError('AUDIT_JOURNAL_EVENT_KIND')
        head=digest(dict(seq=sequence,body=event,previous=head))
        if event['kind']=='FINISHED' and event['attempt']==attempt['attempt']:
            equal(attempt['journal_head'],head,'AUDIT_ATTEMPT_JOURNAL_HEAD')
    if pending is not None:raise ContractError('AUDIT_JOURNAL_PENDING')
    equal(obj['chain_head'],head,'AUDIT_JOURNAL_HEAD')
    if selected is None:raise ContractError('AUDIT_ATTEMPT_NOT_JOURNALED')
    if as_of-selected['reserved_at']>max_age:raise ContractError('AUDIT_ATTEMPT_STALE')
    if sum(r['reserved_bytes'] for r in reserved)>repair_policy.max_total_replacement_bytes:
        raise ContractError('AUDIT_TOTAL_BYTE_BUDGET')
    if sum(r['reserved_seconds'] for r in reserved)>repair_policy.max_total_worker_seconds:
        raise ContractError('AUDIT_TOTAL_TIME_BUDGET')
    return selected

def inspect_attempt(obj,snapshot,proposal,repair_policy,plan):
    fields(obj,ATTEMPT_FIELDS,'AUDIT_ATTEMPT_SCHEMA')
    equal(obj['schema_version'],'bie.qa.repair-attempt/1','AUDIT_ATTEMPT_VERSION')
    sha256(obj['receipt_digest'],'receipt_digest');sha256(obj['journal_head'],'journal_head')
    body={k:v for k,v in obj.items() if k not in ('receipt_digest','journal_head')}
    equal(obj['receipt_digest'],digest(body),'AUDIT_ATTEMPT_HASH')
    for k,expected in dict(proposal_id=proposal.proposal_id,proposal_digest=proposal.content_digest,
        base_digest=snapshot.content_digest,policy_digest=repair_policy.content_digest,plan_digest=plan.content_digest).items():
        equal(obj[k],expected,'AUDIT_ATTEMPT_BINDING')
    for k in ('original_files_written','canonical_repository_modified','product_accepted',
              'downstream_previous_evidence_reusable','hostile_code_sandbox_verified'):
        equal(obj[k],False,'AUDIT_ATTEMPT_SCOPE')
    integer(obj['attempt'],'attempt',1,repair_policy.max_attempts)
    choice(obj['status'],('STAGED_FOR_REVIEW','REJECTED'),'status')
    if obj['status']!='STAGED_FOR_REVIEW':raise ContractError('AUDIT_REPAIR_NOT_STAGED')
    equal(obj['diagnostics'],[],'AUDIT_ATTEMPT_DIAGNOSTICS')
    equal(obj['worker_error'],'','AUDIT_ATTEMPT_WORKER_ERROR')
    equal(obj['worker_executed'],True,'AUDIT_WORKER_NOT_EXECUTED')
    integer(obj['worker_elapsed_ms'],'worker_elapsed_ms',0,(repair_policy.worker_timeout_seconds+5)*1000)
    if type(obj['staged_directory']) is not str or not obj['staged_directory']:
        raise ContractError('AUDIT_STAGED_DIRECTORY_MISSING')
    # staged_directory is only historical metadata, NEVER followed as a path.
    equal(obj['promotion_requires'],'fresh canonical downstream execution and review; never automatic release','AUDIT_PROMOTION_SCOPE')
    expected=candidate_for(snapshot,proposal)
    actual=decode(obj['candidate'],Snapshot)
    equal(asdict(actual),asdict(expected),'AUDIT_CANDIDATE_INVENTORY')
    equal(obj['candidate_digest'],expected.content_digest,'AUDIT_CANDIDATE_DIGEST')
    required,invalidated=check_closure(repair_policy,proposal.owner)
    equal(obj['required_checks'],required,'AUDIT_CHECK_CLOSURE')
    equal(obj['invalidated_previous_checks'],invalidated,'AUDIT_INVALIDATION_CLOSURE')
    outcomes=decode(obj['outcomes'],tuple[CheckOutcome,...])
    equal(tuple(o.check_id for o in outcomes),required,'AUDIT_OUTCOME_COVERAGE')
    for o in outcomes:
        equal((o.candidate_digest,o.policy_digest),(expected.content_digest,repair_policy.content_digest),'AUDIT_OUTCOME_BINDING')
        if o.status!='PASS' or o.diagnostics:raise ContractError('AUDIT_STAGED_OUTCOME_NOT_PASS')
    remaining=tuple(f.failure_id for f in plan.failures if f.failure_id not in proposal.target_failure_ids)
    equal(obj['remaining_failure_ids'],remaining,'AUDIT_HIDDEN_UNRESOLVED_FAILURE')
    return expected,required,invalidated

GEN_FIELDS=('schema_version generation_digest job_digest plan_digest before_sha256 after_sha256 generated_bytes required_checks '
    'invalidated_previous_checks witness status original_files_written previous_candidate_reviews_reusable live_model_invoked '
    'canonical_repository_modified product_accepted').split()

def inspect_generation(link,store,request,repair_policy,audit_policy,required,invalidated):
    from ..domain_repair_v2.contracts import Job as DomainJob,TASK_OWNERS as DOM
    from ..media_repair_v2.contracts import Job as MediaJob,TASK_OWNERS as MED
    raw=object_bytes(store,link.job,audit_policy.max_evidence_bytes)
    task=raw.get('task_id')
    cls=DomainJob if task in DOM else MediaJob if task in MED else None
    if cls is None:raise ContractError('AUDIT_GENERATION_JOB_KIND')
    job=decode(raw,cls)
    equal(job.snapshot_digest,request.snapshot.content_digest,'AUDIT_GENERATION_BASE')
    equal(job.batch_digest,request.batch.content_digest,'AUDIT_GENERATION_BATCH')
    equal(job.repair_policy_digest,repair_policy.content_digest,'AUDIT_GENERATION_POLICY')
    policy_obj=object_bytes(store,link.domain_policy,audit_policy.max_evidence_bytes)
    limits_obj=object_bytes(store,link.limits,audit_policy.max_evidence_bytes)
    equal(job.domain_policy_digest,digest(policy_obj),'AUDIT_DOMAIN_POLICY_BYTES')
    equal(job.limits_digest,digest(limits_obj),'AUDIT_GENERATION_LIMITS_BYTES')
    if job.target not in request.snapshot.artifacts:raise ContractError('AUDIT_GENERATION_TARGET')
    if cls is MediaJob and job.request not in request.snapshot.artifacts:raise ContractError('AUDIT_GENERATION_REQUEST')
    equal((DOM|MED)[task],request.proposal.owner,'AUDIT_GENERATION_OWNER')
    replacements=request.proposal.replacements
    if len(replacements)!=1 or replacements[0].path!=job.target.path:raise ContractError('AUDIT_GENERATION_REPLACEMENTS')
    r=replacements[0];obj=object_bytes(store,link.receipt,audit_policy.max_evidence_bytes)
    fields(obj,GEN_FIELDS,'AUDIT_GENERATION_SCHEMA')
    equal(obj['schema_version'],'bie.qa.domain-repair-generation/1','AUDIT_GENERATION_VERSION')
    for k in ('original_files_written','previous_candidate_reviews_reusable','live_model_invoked','canonical_repository_modified','product_accepted'):
        equal(obj[k],False,'AUDIT_GENERATION_SCOPE')
    equal(obj['status'],'PROPOSAL_GENERATED_REVIEW_REQUIRED','AUDIT_GENERATION_STATUS')
    equal(obj['job_digest'],job.content_digest,'AUDIT_GENERATION_JOB_DIGEST')
    equal(obj['plan_digest'],request.proposal.plan_digest,'AUDIT_GENERATION_PLAN')
    equal(obj['before_sha256'],r.before_sha256,'AUDIT_GENERATION_BEFORE')
    equal(obj['after_sha256'],r.artifact.sha256,'AUDIT_GENERATION_AFTER')
    equal(obj['generated_bytes'],r.artifact.size,'AUDIT_GENERATION_SIZE')
    equal(obj['required_checks'],required,'AUDIT_GENERATION_CHECKS')
    equal(obj['invalidated_previous_checks'],invalidated,'AUDIT_GENERATION_INVALIDATION')
    witness=obj['witness']
    if type(witness) is not dict:raise ContractError('AUDIT_GENERATION_WITNESS')
    equal(witness.get('target_failure_ids'),request.proposal.target_failure_ids,'AUDIT_GENERATION_TARGETS')
    equal(witness.get('domain_policy_digest'),job.domain_policy_digest,'AUDIT_GENERATION_WITNESS_POLICY')
    equal(witness.get('limits_digest'),job.limits_digest,'AUDIT_GENERATION_WITNESS_LIMITS')
    expected=digest(dict(job=obj['job_digest'],plan=obj['plan_digest'],before=obj['before_sha256'],
        after=obj['after_sha256'],required=required,invalidated=invalidated,witness_sha256=digest(witness)))
    equal(obj['generation_digest'],expected,'AUDIT_GENERATION_DIGEST')
    return task
