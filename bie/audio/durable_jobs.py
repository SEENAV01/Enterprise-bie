"""H3-003: fenced AUDIO acoustic jobs using the existing BIE lease/claim stores.

The original classes keep their DIR names for byte identity. AUDIO keys are
namespaced. Cooperating processes serialize short cross-table transitions;
crashed native evaluation is at-least-once, not exactly-once external synthesis.
"""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
import time
import uuid
from bie.director.director_durable_recovery import DirectorLeaseStore, FencedLease, RecoveryError
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore, IdempotencyError
from .common import AudioError, strict_json
from .tts_cache import key_lock
from .durable_contract import DurablePolicy, validate_request, request_key
from .durable_store import private_root, check_tree

@dataclass(frozen=True)
class Ticket:
    lease: FencedLease
    claimed_result_ref: str | None


class AudioJobCoordinator:
    def __init__(self, root, *, policy=DurablePolicy()):
        if type(policy) is not DurablePolicy:
            raise AudioError('DURABLE_POLICY_TYPE')
        self.root, self.policy = private_root(root), policy

    @contextmanager
    def session(self):
        private_root(self.root)
        with key_lock(self.root/'jobs.lock',timeout=self.policy.lock_timeout_seconds):
            check_tree(self.root,self.policy)
            leases = DirectorLeaseStore(self.root/'jobs.sqlite')
            claims = SQLiteIdempotencyStore(self.root/'jobs.sqlite')
            try:
                yield leases, claims
            finally:
                claims.close();leases.close()

    def acquire(self, request, *, now=None):
        if validate_request(request) != self.policy:
            raise AudioError('DURABLE_POLICY_MISMATCH')
        key = request_key(request)
        with self.session() as (leases, claims):
            try:
                prior = leases.get(key)
            except RecoveryError:
                prior = None
            current = time.time() if now is None else now
            if prior and prior.state != 'COMPLETED' and prior.expires_at <= current and prior.epoch >= self.policy.max_attempts:
                raise AudioError('DURABLE_ATTEMPTS_EXHAUSTED')
            # Never reuse a caller-controlled owner string: simultaneous calls
            # must not masquerade as the same live worker.
            lease = leases.acquire(key,request['fingerprint'],'audio:'+uuid.uuid4().hex,
                now=now,ttl_seconds=self.policy.lease_ttl_seconds)
            claim = claims.claim(key,request['fingerprint'],lease.owner)
            if claim.state == 'COMPLETED':
                if lease.state == 'COMPLETED' and lease.result_ref != claim.result_ref:
                    raise AudioError('DURABLE_COMPLETION_DISAGREEMENT')
                return Ticket(lease,claim.result_ref)
            if lease.state == 'COMPLETED':
                raise AudioError('DURABLE_COMPLETION_DISAGREEMENT')
            if claim.owner != lease.owner:
                claims_recovered = leases.reclaim_idempotency(claims,lease,lease.owner,now=now)
                if claims_recovered.owner != lease.owner:
                    raise AudioError('DURABLE_CLAIM_RECOVERY_FAILED')
            return Ticket(lease,None)

    def heartbeat(self, ticket, *, now=None):
        with self.session() as (leases, _):
            leases.assert_active(ticket.lease,now=now)
            if ticket.lease.expires_at <= (time.time() if now is None else now):
                raise AudioError('DURABLE_EXPIRED_FENCE')
            updated = leases.heartbeat(ticket.lease,now=now,ttl_seconds=self.policy.lease_ttl_seconds)
            return Ticket(updated,ticket.claimed_result_ref)

    def complete(self, ticket, result_ref, store, request, trust, *, now=None):
        """Reauthenticate before changing either completion marker.

        A crash after claims.complete but before leases.complete is recovered by
        the next acquired fence, only after current-source signature verification succeeds again.
        """
        if request_key(request) != ticket.lease.key or request['fingerprint'] != ticket.lease.fingerprint:
            raise AudioError('DURABLE_TICKET_REQUEST_MISMATCH')
        from .durable_store import AudioArtifactStore
        if type(store) is not AudioArtifactStore:
            raise AudioError('DURABLE_CANONICAL_STORE_REQUIRED')
        with self.session() as (leases, claims):
            current = leases.get(ticket.lease.key)
            if current.state != 'COMPLETED':
                leases.assert_active(ticket.lease,now=now)
                if ticket.lease.expires_at <= (time.time() if now is None else now):
                    raise AudioError('DURABLE_EXPIRED_FENCE')
            elif current != ticket.lease or current.result_ref != result_ref:
                raise AudioError('DURABLE_FOREIGN_COMPLETION')
            value = store.load(strict_json(result_ref),request,trust,now=now)
            if current.state != 'COMPLETED':
                leases.assert_active(ticket.lease,now=now)
                if ticket.lease.expires_at <= (time.time() if now is None else now):
                    raise AudioError('DURABLE_EXPIRED_FENCE')
            claims.complete(ticket.lease.key,ticket.lease.owner,result_ref)
            leases.complete(ticket.lease,result_ref,now=now)
            return value

    def state(self, request):
        with self.session() as (leases, claims):
            key = request_key(request)
            lease = leases.get(key);claim = claims.get(key)
            if lease.fingerprint != request['fingerprint'] or claim.fingerprint != request['fingerprint']:
                raise AudioError('DURABLE_JOB_FINGERPRINT_CONFLICT')
            return {'lease_state':lease.state,'claim_state':claim.state,'epoch':lease.epoch,
                'result_ref':lease.result_ref,'expires_at':lease.expires_at,
                'authority':'EXECUTION_STATUS_ONLY_NOT_ACOUSTIC_ACCEPTANCE','product_accepted':False}
