"""Explicit out-of-band approval authority. HMAC is local shared-secret identity,
not remote attestation, non-repudiation or proof that a reviewer is competent."""
from __future__ import annotations
from dataclasses import replace
from types import MappingProxyType
import hmac,hashlib
from .contracts import AuthorityKey,Approval,PURPOSES,PublicationPolicy
from ..release_v2.contracts import ContractError,canonical_bytes,digest,integer

class AuthorityStore:
    def __init__(self,keys:tuple[AuthorityKey,...]=()):
        if type(keys)is not tuple or len(keys)>128 or any(type(k)is not AuthorityKey for k in keys):raise ContractError('AUTHORITY_KEYS')
        if len({k.key_id for k in keys})!=len(keys):raise ContractError('AUTHORITY_DUPLICATE_KEY')
        secrets={}
        for k in keys:
            if k.secret in secrets and secrets[k.secret]!=k.principal_id:raise ContractError('AUTHORITY_SHARED_PRINCIPAL_SECRET')
            secrets[k.secret]=k.principal_id
        self._keys=MappingProxyType({k.key_id:k for k in keys})
    def key(self,key_id,purpose,policy,as_of):
        k=self._keys.get(key_id)
        if k is None or not k.enabled:raise ContractError('AUTHORITY_UNKNOWN_OR_REVOKED')
        if purpose not in k.purposes:raise ContractError('AUTHORITY_PURPOSE')
        if not k.not_before<=as_of<k.not_after:raise ContractError('AUTHORITY_KEY_TIME')
        if policy.mode=='production' and k.assurance!='operator_managed':raise ContractError('AUTHORITY_TEST_ONLY')
        return k
    def check(self,approvals,assessment_digest,policy,*,as_of):
        integer(as_of,'as_of')
        if type(approvals)is not tuple or len(approvals)!=len(PURPOSES) or any(type(a)is not Approval for a in approvals):
            raise ContractError('APPROVAL_COVERAGE')
        if set(a.purpose for a in approvals)!=set(PURPOSES):raise ContractError('APPROVAL_PURPOSE_COVERAGE')
        if len({a.approval_id for a in approvals})!=len(approvals):raise ContractError('APPROVAL_DUPLICATE_ID')
        if len({a.principal_id for a in approvals})!=len(PURPOSES):raise ContractError('APPROVAL_INDEPENDENCE')
        for a in approvals:
            k=self.key(a.key_id,a.purpose,policy,as_of)
            if a.principal_id!=k.principal_id:raise ContractError('APPROVAL_PRINCIPAL')
            if a.assessment_digest!=assessment_digest:raise ContractError('APPROVAL_STALE_BINDING')
            if not a.created_at<=as_of<a.expires_at or a.expires_at-a.created_at>policy.max_review_lifetime_seconds:
                raise ContractError('APPROVAL_TIME')
            if a.expires_at>k.not_after:raise ContractError('APPROVAL_EXCEEDS_KEY_LIFETIME')
            signature=hmac.new(k.secret,a.signing_bytes(),hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature,a.signature):raise ContractError('APPROVAL_SIGNATURE')
            if a.decision!='APPROVE':raise ContractError('APPROVAL_REJECTED')
        return min(a.expires_at for a in approvals)

def approval_digest(approvals):
    return digest([a.to_dict() for a in sorted(approvals,key=lambda a:a.approval_id)])
