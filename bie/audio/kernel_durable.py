"""H4-R1-004: kernel-required evidence on unchanged H3 CAS/catalog/lease APIs.

A fourth canonical envelope binds signed kernel evidence to H3's original three
parents. The original H3 request and job methods remain unchanged. Completion
uses their same locked, fenced stores with current v2 verification added.
"""
from __future__ import annotations
from dataclasses import asdict, replace
from pathlib import Path
import time
from bie.bie_core.artifact_contracts import ProducerIdentity
from bie.director.director_artifacts import reference
from .common import AudioError, fingerprint, strict_json
from .acoustic_contract import AcousticPolicy, build_job, canonical, fields, plain
from .durable_contract import DurablePolicy, build_request, validate_request, request_key
from .durable_store import AudioArtifactStore, check_tree, private_root
from .durable_jobs import AudioJobCoordinator
from .durable_pipeline import _Heartbeat, authorize_signer
from .kernel_profile import KERNEL_SCOPE, validate_profile
from .kernel_evidence import (issue_kernel_evaluation, verify_kernel_receipt,
                              validate_kernel_trust)

PRODUCER=ProducerIdentity('bie.audio.kernel-recovery','1.0.0','deterministic')
METADATA={'requires_review':True,'product_accepted':False,'scope':KERNEL_SCOPE}


def kernel_policy(base_policy, profile):
    if type(base_policy) is not DurablePolicy:
        raise AudioError('KERNEL_DURABLE_POLICY_TYPE')
    return replace(base_policy,revision='audio-h4r1:'+fingerprint({
        'base_policy':asdict(base_policy),'profile_fingerprint':profile['fingerprint']}))


def build_kernel_request(job, *, profile, runtime, base_policy=DurablePolicy(), **identity):
    validate_profile(profile,runtime)
    return build_request(job,runtime_fingerprint=runtime['fingerprint'],
        policy=kernel_policy(base_policy,profile),**identity)


class KernelArtifactStore:
    def __init__(self, root, *, runtime, profile, base_policy=DurablePolicy()):
        self.runtime,self.profile=plain(runtime),plain(profile)
        validate_profile(self.profile,self.runtime)
        self.policy=kernel_policy(base_policy,self.profile)
        self.base=AudioArtifactStore(root,policy=self.policy)

    def _request(self, request, wav=None):
        if validate_request(request,wav)!=self.policy:
            raise AudioError('KERNEL_REQUEST_PROFILE_REQUIRED')
        if request['runtime_fingerprint']!=self.runtime['fingerprint']:
            raise AudioError('KERNEL_DURABLE_RUNTIME_BINDING')

    def put(self,request,wav,receipt,trust,*,now=None):
        request,receipt,trust=map(plain,(request,receipt,trust))
        self._request(request,wav)
        verify_kernel_receipt(receipt,request['job'],self.runtime,self.profile,trust,now=now,
            request_fingerprint=request['fingerprint'])
        if receipt['payload']['key_id']!=request['key_id']:
            raise AudioError('KERNEL_DURABLE_ISSUER_BINDING')
        inner_ref=self.base.put(request,wav,receipt['payload']['compatibility_receipt'],
                                trust['evaluator_trust'],now=now)
        payload={'request':request,'profile':self.profile,'kernel_receipt':receipt}
        self.base._budget(canonical(payload))
        with self.base.session() as io:
            count,total=check_tree(self.base.root,self.policy)
            if count+4>self.policy.max_files or total+4*len(canonical(payload))+100_000>self.policy.max_store_bytes:
                raise AudioError('KERNEL_STORE_BUDGET')
            result=io.derive('audio.acoustic.kernel-evaluation',request['run_id'],
                [reference(inner_ref)],payload,stage_id='AUDIO:ACOUSTIC:KERNEL:EVIDENCE',
                metadata=dict(METADATA),producer=PRODUCER,evidence=True)
            return plain(asdict(result))

    def load(self,ref,request,trust,*,now=None):
        request,trust=plain(request),plain(trust)
        self._request(request);validate_kernel_trust(trust)
        target=reference(plain(ref))
        with self.base.session() as io:
            outer=io.load(target)
            if (outer.artifact_type!='audio.acoustic.kernel-evaluation'
                or outer.run_id!=request['run_id'] or outer.metadata!=METADATA
                or outer.producer!=PRODUCER or len(outer.parent_refs)!=1):
                raise AudioError('KERNEL_DURABLE_ENVELOPE_REQUIRED')
            payload=plain(outer.payload)
            fields(payload,('request','profile','kernel_receipt'),'KERNEL_STORED_FIELDS')
            if payload['request']!=request or payload['profile']!=self.profile:
                raise AudioError('KERNEL_STORED_REQUEST_DRIFT')
            parent=io.load(outer.parent_refs[0])
            if outer.provenance_summary!=parent.provenance_summary:
                raise AudioError('KERNEL_STORED_PROVENANCE_DRIFT')
            parent_ref=asdict(outer.parent_refs[0])
        # Release catalog lock before the inherited store takes the same lock.
        loaded=self.base.load(parent_ref,request,trust['evaluator_trust'],now=now)
        receipt=payload['kernel_receipt']
        verify_kernel_receipt(receipt,request['job'],self.runtime,self.profile,trust,now=now,
            request_fingerprint=request['fingerprint'])
        if receipt['payload']['compatibility_receipt']!=loaded['receipt']:
            raise AudioError('KERNEL_STORED_RECEIPT_PARENT_MISMATCH')
        return {**loaded,'artifact_ref':plain(asdict(target)),'acoustic_artifact_ref':parent_ref,
            'kernel_receipt':receipt,'kernel_signature_reverified':True,
            'kernel_trust_fingerprint':fingerprint(trust),'scope':KERNEL_SCOPE,
            'native_worker_scope':KERNEL_SCOPE}


def complete_kernel(jobs,ticket,result_ref,store,request,trust,*,now=None):
    """H3's completion fence, with outer-v2 authentication before either marker.

    This is an adapter over the existing lease/idempotency tables, not a new queue.
    It also recovers claim-complete / lease-incomplete crashes after revalidation.
    """
    if type(jobs) is not AudioJobCoordinator or type(store) is not KernelArtifactStore:
        raise AudioError('KERNEL_CANONICAL_DURABLE_ADAPTER_REQUIRED')
    if request_key(request)!=ticket.lease.key or request['fingerprint']!=ticket.lease.fingerprint:
        raise AudioError('KERNEL_TICKET_REQUEST_MISMATCH')
    if jobs.policy!=store.policy:
        raise AudioError('KERNEL_JOB_STORE_POLICY_MISMATCH')
    with jobs.session() as (leases,claims):
        current=leases.get(ticket.lease.key)
        def active():
            leases.assert_active(ticket.lease,now=now)
            if ticket.lease.expires_at <= (time.time() if now is None else now):
                raise AudioError('KERNEL_EXPIRED_FENCE')
        if current.state!='COMPLETED':
            active()
        elif current!=ticket.lease or current.result_ref!=result_ref:
            raise AudioError('KERNEL_FOREIGN_COMPLETION')
        loaded=store.load(strict_json(result_ref),request,trust,now=now)
        if current.state!='COMPLETED':
            active()
        claims.complete(ticket.lease.key,ticket.lease.owner,result_ref)
        leases.complete(ticket.lease,result_ref,now=now)
        return loaded


def evaluate_kernel_durable(mixed,sync,*,root,run_id,job_id,revision,runtime,profile,
    trust,signer,key_id,policy=AcousticPolicy(),durable_policy=DurablePolicy(),cancellation=None):
    runtime,profile,trust=map(plain,(runtime,profile,trust))
    validate_profile(profile,runtime);validate_kernel_trust(trust)
    if profile['fingerprint'] not in trust['profile_fingerprints']:
        raise AudioError('KERNEL_PROFILE_NOT_APPROVED')
    authorize_signer(runtime,trust['evaluator_trust'],signer,key_id)
    if cancellation is not None and cancellation.is_set():
        raise AudioError('KERNEL_CANCELLED')
    job=build_job(mixed,sync,policy)
    request=build_kernel_request(job,profile=profile,runtime=runtime,base_policy=durable_policy,
        run_id=run_id,job_id=job_id,revision=revision,key_id=key_id)
    root=private_root(root)
    store=KernelArtifactStore(root/'artifacts',runtime=runtime,profile=profile,base_policy=durable_policy)
    jobs=AudioJobCoordinator(root/'jobs',policy=store.policy)
    ticket=jobs.acquire(request)
    if ticket.claimed_result_ref is not None:
        loaded=complete_kernel(jobs,ticket,ticket.claimed_result_ref,store,request,trust)
        validate_profile(profile,runtime)
        return {**loaded,'request':request,'cache_hit':True,'native_evaluations':0,
                'execution':jobs.state(request)}
    with _Heartbeat(jobs,ticket,cancellation) as heartbeat:
        try:
            receipt=issue_kernel_evaluation(job,mixed.wav_bytes,runtime,profile,trust,signer,key_id,
                cancellation=heartbeat.cancel,lock_root=root/'worker-slots',
                request_fingerprint=request['fingerprint'])
        except Exception:
            if heartbeat.failure is not None:
                raise AudioError('KERNEL_LEASE_HEARTBEAT_FAILED') from heartbeat.failure
            raise
    if heartbeat.failure is not None:
        raise AudioError('KERNEL_LEASE_HEARTBEAT_FAILED') from heartbeat.failure
    if heartbeat.cancel.is_set() or (cancellation is not None and cancellation.is_set()):
        raise AudioError('KERNEL_CANCELLED')
    ref=store.put(request,mixed.wav_bytes,receipt,trust)
    if cancellation is not None and cancellation.is_set():
        raise AudioError('KERNEL_CANCELLED')
    loaded=complete_kernel(jobs,heartbeat.ticket,canonical(ref).decode(),store,request,trust)
    validate_profile(profile,runtime)
    return {**loaded,'request':request,'cache_hit':False,'native_evaluations':1,
            'execution':jobs.state(request)}
