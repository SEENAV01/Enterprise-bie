"""H3-004/005: actual H2 evaluation, restart/reuse, current QA and publication.

No new speech synthesizer or orchestrator. Only local acoustic analysis is
recoverable here; paid neural synthesis and other AUDIO kernels are not claimed.
"""
from __future__ import annotations
from threading import Event, Lock, Thread
from pathlib import Path
import json
import time
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from .common import AudioError, strict_json
from .acoustic_contract import AcousticPolicy, build_job, canonical, plain
from .acoustic_evidence import validate_trust, issue_evaluation, verify_receipt
from .acoustic_runtime import verify_runtime
from .acoustic_io import publish_evaluation, verify_publication
from .qa_pipeline import audit_mix
from .durable_contract import DurablePolicy, build_request
from .durable_store import AudioArtifactStore, private_root
from .durable_jobs import AudioJobCoordinator


def authorize_signer(runtime, trust, signer, key_id, *, now=None):
    validate_trust(trust);verify_runtime(runtime)
    current = int(time.time()) if now is None else now
    from .common import integer
    integer(current,'verification time',0,2**53)
    public = signer.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()
    issuer = next((x for x in trust['issuers'] if x['key_id']==key_id),None)
    if (issuer is None or issuer['revoked'] or issuer['public_key_hex']!=public
        or runtime['fingerprint'] not in issuer['runtime_fingerprints']
        or not issuer['not_before'] <= current < issuer['not_after']):
        raise AudioError('DURABLE_SIGNER_NOT_TRUSTED')


class _Heartbeat:
    def __init__(self, coordinator, ticket, caller_cancel):
        self.coordinator,self.ticket = coordinator,ticket
        self.caller_cancel = caller_cancel
        self.cancel,self.stop = Event(),Event()
        self.lock,self.failure = Lock(),None
        self.thread = Thread(target=self.loop,daemon=True)
    def loop(self):
        next_beat = time.monotonic()+self.coordinator.policy.heartbeat_seconds
        while not self.stop.wait(.05):
            if self.caller_cancel is not None and self.caller_cancel.is_set():
                self.cancel.set();return
            if time.monotonic() >= next_beat:
                try:
                    with self.lock:self.ticket = self.coordinator.heartbeat(self.ticket)
                except Exception as exc:
                    self.failure = exc;self.cancel.set();return
                next_beat = time.monotonic()+self.coordinator.policy.heartbeat_seconds
    def __enter__(self):
        self.thread.start();return self
    def __exit__(self,*args):
        self.stop.set();self.thread.join(timeout=self.coordinator.policy.lock_timeout_seconds+1)
        if self.thread.is_alive():
            self.cancel.set();raise AudioError('DURABLE_HEARTBEAT_DID_NOT_STOP')


def evaluate_durable(mixed, sync, *, root, run_id, job_id, revision, runtime,
                     trust, signer, key_id, policy=AcousticPolicy(),
                     durable_policy=DurablePolicy(), cancellation=None):
    # Snapshot all externally mutable data before worker invocation.
    runtime,trust = plain(runtime),plain(trust)
    authorize_signer(runtime,trust,signer,key_id)
    if cancellation is not None and cancellation.is_set():
        raise AudioError('DURABLE_CANCELLED')
    job = build_job(mixed,sync,policy)
    request = build_request(job,run_id=run_id,job_id=job_id,revision=revision,
        runtime_fingerprint=runtime['fingerprint'],key_id=key_id,policy=durable_policy)
    root = private_root(root)
    store = AudioArtifactStore(Path(root)/'artifacts',policy=durable_policy)
    jobs = AudioJobCoordinator(Path(root)/'jobs',policy=durable_policy)
    ticket = jobs.acquire(request)
    if ticket.claimed_result_ref is not None:
        ref = strict_json(ticket.claimed_result_ref)
        loaded = jobs.complete(ticket,ticket.claimed_result_ref,store,request,trust)
        verify_runtime(runtime)
        return {**loaded,'request':request,'cache_hit':True,'native_evaluations':0,
                'execution':jobs.state(request),'native_worker_scope':'H2_BOUNDED_LOCAL_NOT_CANONICAL_KERNEL'}
    with _Heartbeat(jobs,ticket,cancellation) as heartbeat:
        try:
            receipt = issue_evaluation(job,mixed.wav_bytes,runtime,signer,key_id,cancellation=heartbeat.cancel)
        except Exception:
            if heartbeat.failure is not None:
                raise AudioError('DURABLE_LEASE_HEARTBEAT_FAILED') from heartbeat.failure
            raise
    if heartbeat.failure is not None:
        raise AudioError('DURABLE_LEASE_HEARTBEAT_FAILED') from heartbeat.failure
    if heartbeat.cancel.is_set() or (cancellation is not None and cancellation.is_set()):
        raise AudioError('DURABLE_CANCELLED')
    ref = store.put(request,mixed.wav_bytes,receipt,trust)
    # A stale owner might have created an immutable orphan, but cannot commit
    # a job result. Orphan garbage collection is explicitly not implemented.
    encoded = canonical(ref).decode()
    loaded = jobs.complete(heartbeat.ticket,encoded,store,request,trust)
    verify_runtime(runtime)
    return {**loaded,'request':request,'cache_hit':False,'native_evaluations':1,
            'execution':jobs.state(request),'native_worker_scope':'H2_BOUNDED_LOCAL_NOT_CANONICAL_KERNEL'}


def audit_durable_mix(mixed,sync,*,asset_wavs=(),caption_intent=None,output=None,**options):
    result = evaluate_durable(mixed,sync,**options)
    trust = options['trust'];policy = options.get('policy',AcousticPolicy())
    report,captions = audit_mix(mixed,sync,asset_wavs=asset_wavs,intent=caption_intent,
        acoustic_receipt=result['receipt'],evaluator_trust=trust,acoustic_policy=policy)
    if output is not None:
        publish_evaluation(mixed,sync,result['request']['job'],result['receipt'],trust,report,captions,output)
        verify_publication(output,mixed,sync,trust,policy)
    return result, report, captions
