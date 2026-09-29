"""HARD-004: out-of-band principal, independence group, and local key lifecycle.

HMAC proves possession of a shared secret, not truth, remote attestation, or
non-repudiation. Production key provisioning/revocation distribution is separate.
Never construct keys from a submitted evidence bundle. Legacy keys remain usable
at floor one but share an unclassified independence group until explicitly mapped.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import hmac
from types import MappingProxyType
from typing import Protocol
from .contracts import ContractError, GateEvidence, choice, token, tuple_tokens, integer, sha256


@dataclass(frozen=True, slots=True)
class TrustResult:
    accepted: bool
    diagnostic: str
    assurance: str
    principal_id: str = ''
    independence_group: str = ''
    credential_fingerprint: str = ''
    valid_until: int = 0

    def __post_init__(self):
        if type(self.accepted)is not bool:raise ContractError('INVALID_TRUST_RESULT')
        token(self.diagnostic,'trust.diagnostic')
        choice(self.assurance,('none','test_only','operator_managed'),'trust.assurance')
        if self.accepted == (self.assurance=='none'):raise ContractError('INCONSISTENT_TRUST_RESULT')
        for n in ('principal_id','independence_group'):
            if getattr(self,n):token(getattr(self,n),n)
            elif type(getattr(self,n))is not str:raise ContractError('INVALID_TRUST_IDENTITY')
        if self.credential_fingerprint:sha256(self.credential_fingerprint,'credential_fingerprint')
        elif type(self.credential_fingerprint)is not str:raise ContractError('INVALID_TRUST_IDENTITY')
        integer(self.valid_until,'trust.valid_until')


class EvidenceVerifier(Protocol):
    def verify_at(self, evidence: GateEvidence, *, as_of: int) -> TrustResult: ...


class DenyAllVerifier:
    def verify(self,evidence:GateEvidence)->TrustResult:
        return TrustResult(False,'NO_AUTHORIZED_EVIDENCE_VERIFIER','none')
    def verify_at(self,evidence:GateEvidence,*,as_of:int)->TrustResult:
        integer(as_of,'as_of');return self.verify(evidence)


@dataclass(frozen=True, slots=True)
class TrustedKey:
    key_id: str
    secret: bytes = field(repr=False)
    evaluator_id: str
    evaluator_version: str
    authorized_gate_ids: tuple[str,...]
    allowed_kinds: tuple[str,...]
    assurance: str = 'test_only'
    enabled: bool = True
    principal_id: str = ''
    independence_group: str = ''
    not_before: int = 0
    not_after: int = 2**53-1
    revoked_at: int | None = None

    def __post_init__(self):
        for n in ('key_id','evaluator_id','evaluator_version'):token(getattr(self,n),n)
        if type(self.secret)is not bytes or not 32<=len(self.secret)<=128:raise ContractError('INVALID_SECRET_LENGTH')
        tuple_tokens(self.authorized_gate_ids,'authorized_gate_ids',1,128)
        tuple_tokens(self.allowed_kinds,'allowed_kinds',1,2)
        for kind in self.allowed_kinds:choice(kind,('execution','review'),'allowed_kinds')
        choice(self.assurance,('test_only','operator_managed'),'assurance')
        if type(self.enabled)is not bool:raise ContractError('INVALID_KEY_ENABLED')
        for n in ('principal_id','independence_group'):
            if getattr(self,n):token(getattr(self,n),n)
            elif type(getattr(self,n))is not str:raise ContractError('INVALID_TRUST_IDENTITY')
        if bool(self.principal_id)!=bool(self.independence_group):raise ContractError('INCOMPLETE_TRUST_IDENTITY')
        integer(self.not_before,'key.not_before');integer(self.not_after,'key.not_after',self.not_before+1)
        if self.revoked_at is not None:integer(self.revoked_at,'key.revoked_at')


class HmacEvidenceVerifier:
    def __init__(self,keys:tuple[TrustedKey,...]):
        if type(keys)is not tuple or len(keys)>1024 or any(type(k)is not TrustedKey for k in keys):
            raise ContractError('INVALID_TRUST_KEYS')
        indexed={k.key_id:k for k in keys}
        if len(indexed)!=len(keys):raise ContractError('DUPLICATE_TRUST_KEY')
        secrets={};principals={}
        for key in keys:
            p,g=self._identity(key)
            # One secret cannot be provisioned as two supposedly independent people.
            previous=secrets.setdefault(key.secret,(p,g))
            if previous!=(p,g):raise ContractError('SHARED_SECRET_IDENTITY_CONFLICT')
            previous_group=principals.setdefault(p,g)
            if previous_group!=g:raise ContractError('PRINCIPAL_GROUP_CONFLICT')
        self._keys=MappingProxyType(indexed)

    @staticmethod
    def _identity(key):
        if key.principal_id:return key.principal_id,key.independence_group
        # Conservative compatibility: all unmapped old identities count as one
        # group, regardless of different names, versions, key IDs or secrets.
        return 'legacy-unclassified','legacy-unclassified'

    def verify(self,evidence:GateEvidence,*,as_of:int|None=None)->TrustResult:
        """Compatibility signature inspection; readiness always calls verify_at.

        The omitted clock uses the record's creation time only for this legacy
        inspection API. It must not be treated as proof of current validity.
        """
        if type(evidence)is not GateEvidence:raise ContractError('INVALID_EVIDENCE_TYPE')
        return self.verify_at(evidence,as_of=evidence.created_at if as_of is None else as_of)

    def verify_at(self,evidence:GateEvidence,*,as_of:int)->TrustResult:
        if type(evidence)is not GateEvidence:raise ContractError('INVALID_EVIDENCE_TYPE')
        integer(as_of,'as_of');key=self._keys.get(evidence.signer_key_id);code='AUTHENTICATED'
        if key is None:code='UNTRUSTED_SIGNER'
        elif not key.enabled or (key.revoked_at is not None and as_of>=key.revoked_at):code='REVOKED_SIGNER'
        elif not key.not_before<=as_of<key.not_after:code='SIGNER_NOT_CURRENT'
        elif evidence.created_at<key.not_before or evidence.created_at>=key.not_after:code='EVIDENCE_OUTSIDE_KEY_LIFETIME'
        elif evidence.expires_at>key.not_after:code='EVIDENCE_EXCEEDS_KEY_LIFETIME'
        elif evidence.evaluator_id!=key.evaluator_id or evidence.evaluator_version!=key.evaluator_version:code='UNAUTHORIZED_EVALUATOR'
        elif evidence.gate_id not in key.authorized_gate_ids:code='UNAUTHORIZED_GATE'
        elif evidence.kind not in key.allowed_kinds:code='UNAUTHORIZED_EVIDENCE_KIND'
        elif not hmac.compare_digest(hmac.new(key.secret,evidence.signing_bytes(),hashlib.sha256).hexdigest(),evidence.signature):code='BAD_SIGNATURE'
        if code!='AUTHENTICATED':return TrustResult(False,code,'none')
        principal,group=self._identity(key)
        valid_until=min(key.not_after,key.revoked_at if key.revoked_at is not None else key.not_after)
        return TrustResult(True,code,key.assurance,principal,group,hashlib.sha256(b'BIE-KEY-IDENTITY-1\x00'+key.secret).hexdigest(),valid_until)
