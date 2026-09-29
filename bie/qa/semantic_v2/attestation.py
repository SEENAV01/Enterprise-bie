"""Purpose-scoped authentication; no trusted evaluator is shipped or implied.

HMAC is a local shared-secret adapter, not remote attestation or a correctness
proof. Production provisioning/calibration remain separate integration gates.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from types import MappingProxyType
import hashlib, hmac
from ..release_v2.contracts import ContractError, canonical_bytes, digest, token, sha256, integer, choice, tuple_tokens
from ..source_v2.models import text
from .models import SemanticRequest, SemanticPolicy

PURPOSES = ('normalization', 'reference', 'coverage', 'consistency')


@dataclass(frozen=True, slots=True)
class SemanticAssessment:
    assessment_id: str
    request_digest: str
    policy_digest: str
    subject_id: str
    purpose: str
    verdict: str
    evidence_ids: tuple[str, ...]
    confidence_ppm: int
    rationale: str
    evaluator_id: str
    evaluator_version: str
    issued_at: int
    expires_at: int
    key_id: str
    signature: str = ''

    def __post_init__(self):
        for f in ('assessment_id', 'subject_id', 'evaluator_id', 'evaluator_version', 'key_id'):
            token(getattr(self, f), f)
        sha256(self.request_digest, 'request_digest'); sha256(self.policy_digest, 'policy_digest')
        choice(self.purpose, PURPOSES, 'purpose')
        choice(self.verdict, ('VERIFIED', 'REJECTED', 'UNCERTAIN'), 'verdict')
        tuple_tokens(self.evidence_ids, 'evidence_ids', 1, 4096)
        integer(self.confidence_ppm, 'confidence_ppm', 0, 1000000)
        text(self.rationale, 'rationale', 8192)
        integer(self.issued_at, 'issued_at'); integer(self.expires_at, 'expires_at', self.issued_at + 1)
        if type(self.signature) is not str: raise ContractError('INVALID_SIGNATURE')
        if self.signature: sha256(self.signature, 'signature')

    def signing_bytes(self):
        data = asdict(self); del data['signature']
        return b'BIE-QA-SEM-ASSESSMENT-V1\x00' + canonical_bytes(data)


@dataclass(frozen=True, slots=True)
class SemanticKey:
    key_id: str
    secret: bytes = field(repr=False)
    evaluator_id: str
    evaluator_version: str
    independence_group: str
    purposes: tuple[str, ...]
    assurance: str = 'test_only'
    enabled: bool = True

    def __post_init__(self):
        for f in ('key_id', 'evaluator_id', 'evaluator_version', 'independence_group'):
            token(getattr(self, f), f)
        if type(self.secret) is not bytes or not 32 <= len(self.secret) <= 128:
            raise ContractError('INVALID_SEMANTIC_SECRET')
        tuple_tokens(self.purposes, 'purposes', 1, len(PURPOSES))
        for p in self.purposes: choice(p, PURPOSES, 'purpose')
        choice(self.assurance, ('test_only', 'operator_managed'), 'assurance')
        if type(self.enabled) is not bool: raise ContractError('INVALID_KEY_ENABLED')


@dataclass(frozen=True, slots=True)
class Authentication:
    code: str
    authenticated: bool
    operational: bool
    independence_group: str


class SemanticVerifier:
    def __init__(self, keys: tuple[SemanticKey, ...] = ()):
        if type(keys) is not tuple or len(keys) > 1024 or any(type(k) is not SemanticKey for k in keys):
            raise ContractError('INVALID_SEMANTIC_KEYS')
        if len({k.key_id for k in keys}) != len(keys): raise ContractError('DUPLICATE_SEMANTIC_KEY')
        # A single evaluator principal cannot be relabeled as independent groups.
        groups = {}
        for k in keys:
            if k.evaluator_id in groups and groups[k.evaluator_id] != k.independence_group:
                raise ContractError('INCONSISTENT_ASSESSOR_INDEPENDENCE')
            groups[k.evaluator_id] = k.independence_group
        self._keys = MappingProxyType({k.key_id: k for k in keys})

    @property
    def configuration_digest(self):
        return digest([dict(key_id=k.key_id, fingerprint=hashlib.sha256(k.secret).hexdigest(),
            evaluator_id=k.evaluator_id, evaluator_version=k.evaluator_version,
            independence_group=k.independence_group, purposes=k.purposes,
            assurance=k.assurance, enabled=k.enabled)
            for k in sorted(self._keys.values(), key=lambda k: k.key_id)])

    def verify(self, assessment: SemanticAssessment, request: SemanticRequest,
               policy: SemanticPolicy, now: int) -> Authentication:
        if type(request) is not SemanticRequest or type(policy) is not SemanticPolicy:
            raise ContractError('INVALID_SEMANTIC_ASSESSMENT_CONTEXT')
        return self._verify_bound(assessment, request.content_digest, policy.content_digest,
                                  policy.max_receipt_age_seconds, now)

    def _verify_bound(self, a, request_digest, policy_digest, max_age, now):
        if type(a) is not SemanticAssessment: raise ContractError('INVALID_SEMANTIC_ASSESSMENT')
        integer(now, 'now')
        k = self._keys.get(a.key_id)
        code = 'AUTHENTICATED'
        if a.request_digest != request_digest: code = 'STALE_SEMANTIC_ASSESSMENT'
        elif a.policy_digest != policy_digest: code = 'SEMANTIC_POLICY_MISMATCH'
        elif a.issued_at > now or a.expires_at <= now: code = 'SEMANTIC_ASSESSMENT_TIME'
        elif now - a.issued_at > max_age or a.expires_at - a.issued_at > max_age: code = 'SEMANTIC_ASSESSMENT_LIFETIME'
        elif k is None: code = 'UNTRUSTED_SEMANTIC_KEY'
        elif not k.enabled: code = 'REVOKED_SEMANTIC_KEY'
        elif (a.evaluator_id, a.evaluator_version) != (k.evaluator_id, k.evaluator_version): code = 'UNAUTHORIZED_SEMANTIC_ASSESSOR'
        elif a.purpose not in k.purposes: code = 'UNAUTHORIZED_SEMANTIC_PURPOSE'
        elif not hmac.compare_digest(a.signature, hmac.new(k.secret, a.signing_bytes(), hashlib.sha256).hexdigest()): code = 'BAD_SEMANTIC_SIGNATURE'
        ok = code == 'AUTHENTICATED'
        return Authentication(code, ok, bool(ok and k.assurance == 'operator_managed'), k.independence_group if ok else '')
