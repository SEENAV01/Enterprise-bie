"""H5-004 CAS/catalog and fenced lease adapter for the fixed local pipeline.

Uses existing canonical stores, locks and heartbeat; no new queue/orchestrator.
Cache unit is a bounded whole run. External paid-call retry is not implemented.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import time
import uuid
from bie.bie_core.artifact_contracts import ArtifactEnvelope,ProducerIdentity,ProvenanceSource,ProvenanceSummary
from bie.infrastructure.artifact_store import BlobRef
from bie.director.director_artifacts import reference
from bie.director.director_durable_recovery import RecoveryError
from .common import AudioError,fingerprint,strict_json
from .acoustic_contract import canonical,fields,plain
from .durable_contract import DurablePolicy
from .durable_store import AudioArtifactStore,check_tree,private_root
from .durable_jobs import AudioJobCoordinator,Ticket
from .durable_pipeline import _Heartbeat
from .pipeline_contract import SCOPE,BOUNDARIES,validate_request,request_key,PipelineLimits
from .pipeline_profile import validate_profile
from .pipeline_bundle import index_files,NAMES
from .pipeline_evidence import verify_receipt,issue_execution,authorize

PRODUCER=ProducerIdentity('bie.audio.local-pipeline','1.0.0','deterministic')
METADATA={'requires_review':True,'scope':SCOPE,**BOUNDARIES}


def provenance(request):
    return ProvenanceSummary([ProvenanceSource(ref,{'kind':'declared-prepared-narration-reference',
        'plan_fingerprint':request['plan_fingerprint']}) for ref in request['source_refs']])


class PipelineArtifactStore:
    def __init__(self,root,*,profile,policy=DurablePolicy()):
        self.profile=plain(profile);self.policy=policy
        validate_profile(self.profile)
        self.base=AudioArtifactStore(root,policy=policy)

    def _request(self,request):
        validate_request(request)
        if request['profile_fingerprint']!=self.profile['fingerprint'] or request['durable_policy']!=asdict(self.policy):
            raise AudioError('PIPELINE_STORE_POLICY_BINDING')

    def put(self,request,files,receipt,trust,*,now=None):
        request,receipt,trust=map(plain,(request,receipt,trust));files=dict(files)
        self._request(request)
        verify_receipt(receipt,files,request,self.profile,trust,now=now)
        index=index_files(files,PipelineLimits(**request['limits']))
        self.base._budget(canonical(request),canonical(receipt),*files.values())
        with self.base.session() as io:
            count,total=check_tree(self.base.root,self.policy)
            reserve=sum(len(v) for v in files.values())+8*(len(canonical(request))+len(canonical(receipt)))+500_000
            if total+reserve>self.policy.max_store_bytes or count+40>self.policy.max_files:
                raise AudioError('PIPELINE_STORE_BUDGET')
            blobs={n:asdict(io.catalog.cas.put_bytes(b)) for n,b in sorted(files.items())}
            source=ArtifactEnvelope.create('source.asset','1.0.0',request['run_id'],PRODUCER,[],provenance(request),dict(METADATA),
                {'kind':'prepared-narration-import','authority':'DECLARED_SOURCE_NOT_CANONICAL_DIR_ACCEPTANCE',
                 'source':request['source'],'plan':request['plan']})
            sr=io.put(source,'AUDIO:PIPELINE:SOURCE')
            rr=io.derive('audio.pipeline.request',request['run_id'],[sr],request,
                stage_id='AUDIO:PIPELINE:REQUEST',metadata=dict(METADATA),producer=PRODUCER)
            payload={'request_fingerprint':request['fingerprint'],'blobs':blobs,'index':index,'receipt':receipt}
            self.base._budget(canonical(payload))
            result=io.derive('audio.pipeline.execution',request['run_id'],[rr],payload,
                stage_id='AUDIO:PIPELINE:EXECUTION',metadata=dict(METADATA),producer=PRODUCER,evidence=True)
            return plain(asdict(result))

    def load(self,ref,request,trust,*,now=None):
        request,trust=plain(request),plain(trust);self._request(request);target=reference(plain(ref))
        with self.base.session() as io:
            result=io.load(target)
            if len(result.parent_refs)!=1:raise AudioError('PIPELINE_PARENT_CHAIN')
            req=io.load(result.parent_refs[0])
            if len(req.parent_refs)!=1:raise AudioError('PIPELINE_PARENT_CHAIN')
            src=io.load(req.parent_refs[0])
            for envelope,kind in ((result,'audio.pipeline.execution'),(req,'audio.pipeline.request'),(src,'source.asset')):
                if (envelope.artifact_type!=kind or envelope.run_id!=request['run_id'] or envelope.producer!=PRODUCER
                    or envelope.metadata!=METADATA or envelope.provenance_summary!=provenance(request)):
                    raise AudioError('PIPELINE_ENVELOPE_BINDING')
            if src.parent_refs or src.payload!={'kind':'prepared-narration-import',
                'authority':'DECLARED_SOURCE_NOT_CANONICAL_DIR_ACCEPTANCE','source':request['source'],'plan':request['plan']}:
                raise AudioError('PIPELINE_SOURCE_PARENT')
            if req.payload!=request:raise AudioError('PIPELINE_STORED_REQUEST')
            p=plain(result.payload);fields(p,('request_fingerprint','blobs','index','receipt'))
            if p['request_fingerprint']!=request['fingerprint'] or type(p['blobs'])is not dict or set(p['blobs'])!=NAMES:
                raise AudioError('PIPELINE_STORED_BUNDLE')
            files={};total=0;limits=PipelineLimits(**request['limits'])
            for name,row in sorted(p['blobs'].items()):
                fields(row,tuple(BlobRef.__dataclass_fields__))
                blob=BlobRef(**row)
                if type(blob.size)is not int or not 0<blob.size<=limits.max_file_bytes:
                    raise AudioError('PIPELINE_STORED_BLOB_BUDGET')
                total+=blob.size
                if total>limits.max_bundle_bytes:raise AudioError('PIPELINE_STORED_TOTAL_BUDGET')
                files[name]=io.catalog.cas.get_bytes(blob)
            if index_files(files,limits)!=p['index']:raise AudioError('PIPELINE_STORED_INDEX')
        verified=verify_receipt(p['receipt'],files,request,self.profile,trust,now=now)
        return {'artifact_ref':plain(asdict(target)),'files':files,'receipt':p['receipt'],
            'verification':verified,'current_trust_fingerprint':fingerprint(trust)}


class PipelineCoordinator(AudioJobCoordinator):
    """Only request namespace/validation differs; lease, claim and lock APIs stay canonical."""
    def acquire(self,request,*,now=None):
        validate_request(request)
        if request['durable_policy']!=asdict(self.policy):raise AudioError('PIPELINE_JOB_POLICY')
        key=request_key(request);current=time.time() if now is None else now
        with self.session() as (leases,claims):
            try:prior=leases.get(key)
            except RecoveryError:prior=None
            if prior and prior.state!='COMPLETED' and prior.expires_at<=current and prior.epoch>=self.policy.max_attempts:
                raise AudioError('PIPELINE_ATTEMPTS_EXHAUSTED')
            lease=leases.acquire(key,request['fingerprint'],'audio-pipeline:'+uuid.uuid4().hex,
                now=now,ttl_seconds=self.policy.lease_ttl_seconds)
            claim=claims.claim(key,request['fingerprint'],lease.owner)
            if claim.state=='COMPLETED':
                if lease.state=='COMPLETED' and lease.result_ref!=claim.result_ref:raise AudioError('PIPELINE_COMPLETION_CONFLICT')
                return Ticket(lease,claim.result_ref)
            if lease.state=='COMPLETED':raise AudioError('PIPELINE_COMPLETION_CONFLICT')
            if claim.owner!=lease.owner:
                leases.reclaim_idempotency(claims,lease,lease.owner,now=now)
            return Ticket(lease,None)

    def complete(self,ticket,result_ref,store,request,trust,*,now=None):
        if type(store)is not PipelineArtifactStore or store.policy!=self.policy:
            raise AudioError('PIPELINE_CANONICAL_STORE_REQUIRED')
        if ticket.lease.key!=request_key(request) or ticket.lease.fingerprint!=request['fingerprint']:
            raise AudioError('PIPELINE_TICKET_BINDING')
        with self.session() as (leases,claims):
            current=leases.get(ticket.lease.key)
            def active():
                leases.assert_active(ticket.lease,now=now)
                if ticket.lease.expires_at <= (time.time() if now is None else now):raise AudioError('PIPELINE_EXPIRED_FENCE')
            if current.state=='COMPLETED':
                if current!=ticket.lease or current.result_ref!=result_ref:raise AudioError('PIPELINE_FOREIGN_COMPLETION')
            else:active()
            loaded=store.load(strict_json(result_ref),request,trust,now=now)
            if current.state!='COMPLETED':active()
            claims.complete(ticket.lease.key,ticket.lease.owner,result_ref)
            leases.complete(ticket.lease,result_ref,now=now)
            return loaded

    def state(self,request):
        with self.session() as (leases,claims):
            key=request_key(request);lease=leases.get(key);claim=claims.get(key)
            if lease.fingerprint!=request['fingerprint'] or claim.fingerprint!=request['fingerprint']:
                raise AudioError('PIPELINE_STATE_IDENTITY')
            return {'lease_state':lease.state,'claim_state':claim.state,'epoch':lease.epoch,
                'scope':'JOB_STATUS_NOT_ACCEPTANCE','product_accepted':False}


def execute_durable(request,profile,trust,signer,*,root,cancellation=None):
    request,profile,trust=map(plain,(request,profile,trust))
    if signer is None:raise AudioError('PIPELINE_SIGNER_REQUIRED')
    validate_request(request);validate_profile(profile);authorize(profile,trust,request['key_id'],signer=signer)
    if cancellation is not None and cancellation.is_set():raise AudioError('PIPELINE_CANCELLED')
    root=private_root(root);policy=DurablePolicy(**request['durable_policy'])
    store=PipelineArtifactStore(root/'artifacts',profile=profile,policy=policy)
    jobs=PipelineCoordinator(root/'jobs',policy=policy);ticket=jobs.acquire(request)
    if ticket.claimed_result_ref is not None:
        result=jobs.complete(ticket,ticket.claimed_result_ref,store,request,trust)
        if cancellation is not None and cancellation.is_set():raise AudioError('PIPELINE_CANCELLED')
        return {**result,'cache_hit':True,'native_pipeline_runs':0,'state':jobs.state(request)}
    with _Heartbeat(jobs,ticket,cancellation) as heartbeat:
        files,receipt=issue_execution(request,profile,trust,signer,cancellation=heartbeat.cancel,lock_root=root/'worker-slots')
        if heartbeat.failure is not None:raise AudioError('PIPELINE_HEARTBEAT_FAILED') from heartbeat.failure
        if heartbeat.cancel.is_set() or (cancellation is not None and cancellation.is_set()):raise AudioError('PIPELINE_CANCELLED')
        # Keep the original heartbeat alive through CAS/catalog publication too.
        ref=store.put(request,files,receipt,trust)
        with heartbeat.lock:
            if heartbeat.failure is not None:raise AudioError('PIPELINE_HEARTBEAT_FAILED') from heartbeat.failure
            if heartbeat.cancel.is_set() or (cancellation is not None and cancellation.is_set()):raise AudioError('PIPELINE_CANCELLED')
            heartbeat.ticket=jobs.heartbeat(heartbeat.ticket)
            loaded=jobs.complete(heartbeat.ticket,canonical(ref).decode(),store,request,trust)
            heartbeat.stop.set()
    return {**loaded,'cache_hit':False,'native_pipeline_runs':1,'state':jobs.state(request)}
