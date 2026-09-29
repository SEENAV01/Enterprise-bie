"""Authenticated contextual/extraction assessments, distinct from citation presence.

No embedded model, automatic online lookup or implicit trusted evaluator. Keys
and policy are out-of-band. HMAC is local shared-secret authentication only, not
proof that an evaluator's judgment is correct or calibrated.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from types import MappingProxyType
import hashlib, hmac
from ..release_v2.contracts import ContractError, token, sha256, integer, choice, tuple_tokens, canonical_bytes, digest
from .models import Request, Policy, text

@dataclass(frozen=True, slots=True)
class Assessment:
    assessment_id: str
    request_digest: str
    policy_digest: str
    subject_id: str
    purpose: str
    verdict: str
    confidence_ppm: int
    rationale: str
    evaluator_id: str
    evaluator_version: str
    issued_at: int
    expires_at: int
    key_id: str
    signature: str = ''

    def __post_init__(self):
        for k in ('assessment_id','subject_id','evaluator_id','evaluator_version','key_id'):
            token(getattr(self,k),k)
        sha256(self.request_digest,'request_digest');sha256(self.policy_digest,'policy_digest')
        choice(self.purpose,('semantic','extraction','nonfactual'),'purpose')
        choice(self.verdict,('SUPPORTED','CONTRADICTED','UNCERTAIN','VERIFIED','NO_FACTUAL_ASSERTION'),'verdict')
        allowed={'semantic':('SUPPORTED','CONTRADICTED','UNCERTAIN'),
                 'extraction':('VERIFIED','CONTRADICTED','UNCERTAIN'),
                 'nonfactual':('NO_FACTUAL_ASSERTION','CONTRADICTED','UNCERTAIN')}
        if self.verdict not in allowed[self.purpose]: raise ContractError('PURPOSE_VERDICT_MISMATCH')
        integer(self.confidence_ppm,'confidence_ppm',0,1_000_000)
        text(self.rationale,'rationale',8192)
        integer(self.issued_at,'issued_at');integer(self.expires_at,'expires_at',self.issued_at+1)
        if self.signature != '': sha256(self.signature,'signature')
        elif type(self.signature) is not str: raise ContractError('INVALID_SIGNATURE')

    def signing_bytes(self):
        d=asdict(self);del d['signature']
        return b'BIE-QA-SOURCE-ASSESSMENT-V1\x00'+canonical_bytes(d)

@dataclass(frozen=True, slots=True)
class AssessmentKey:
    key_id: str
    secret: bytes = field(repr=False)
    evaluator_id: str
    evaluator_version: str
    purposes: tuple[str,...]
    assurance: str = 'test_only'
    enabled: bool = True

    def __post_init__(self):
        for k in ('key_id','evaluator_id','evaluator_version'):token(getattr(self,k),k)
        if type(self.secret) is not bytes or not 32<=len(self.secret)<=128:raise ContractError('INVALID_SECRET_LENGTH')
        tuple_tokens(self.purposes,'purposes',1,3)
        for p in self.purposes:choice(p,('semantic','extraction','nonfactual'),'purpose')
        choice(self.assurance,('test_only','operator_managed'),'assurance')
        if type(self.enabled) is not bool:raise ContractError('INVALID_KEY_ENABLED')

@dataclass(frozen=True, slots=True)
class Verdict:
    code: str
    authenticated: bool
    operator_managed: bool

class AssessmentVerifier:
    def __init__(self, keys: tuple[AssessmentKey,...] = ()):
        if type(keys) is not tuple or len(keys)>1024 or any(type(k) is not AssessmentKey for k in keys):raise ContractError('INVALID_TRUST_KEYS')
        if len({k.key_id for k in keys})!=len(keys):raise ContractError('DUPLICATE_TRUST_KEY')
        self._keys=MappingProxyType({k.key_id:k for k in keys})

    @property
    def configuration_digest(self):
        # Secrets never appear in reports. Fingerprints identify provisioned key
        # material without making the public report a replacement for the key.
        return digest([{'key_id':k.key_id,'key_fingerprint':hashlib.sha256(k.secret).hexdigest(),
            'evaluator_id':k.evaluator_id,'evaluator_version':k.evaluator_version,
            'purposes':k.purposes,'assurance':k.assurance,'enabled':k.enabled}
            for k in sorted(self._keys.values(),key=lambda k:k.key_id)])

    def verify(self, a: Assessment, request: Request, policy: Policy, now: int) -> Verdict:
        if type(request) is not Request or type(policy) is not Policy:
            raise ContractError('INVALID_ASSESSMENT_CONTEXT')
        return self._verify_bound(a, request.content_digest, policy.content_digest,
                                  policy.max_receipt_age_seconds, now)

    def _verify_bound(self, a, request_digest, policy_digest, max_age, now):
        # Private fast path: digests computed by the evaluator from validated
        # immutable inputs, never accepted as replacement user inputs.
        if type(a) is not Assessment:raise ContractError('INVALID_ASSESSMENT')
        integer(now,'now')
        key=self._keys.get(a.key_id)
        code='AUTHENTICATED'
        if a.request_digest!=request_digest:code='STALE_ASSESSMENT'
        elif a.policy_digest!=policy_digest:code='ASSESSMENT_POLICY_MISMATCH'
        elif a.issued_at>now or a.expires_at<=now:code='ASSESSMENT_TIME_INVALID'
        elif now-a.issued_at>max_age or a.expires_at-a.issued_at>max_age:code='ASSESSMENT_LIFETIME_EXCEEDED'
        elif key is None:code='UNTRUSTED_ASSESSMENT_KEY'
        elif not key.enabled:code='REVOKED_ASSESSMENT_KEY'
        elif a.evaluator_id!=key.evaluator_id or a.evaluator_version!=key.evaluator_version:code='UNAUTHORIZED_ASSESSOR'
        elif a.purpose not in key.purposes:code='UNAUTHORIZED_ASSESSMENT_PURPOSE'
        elif not hmac.compare_digest(a.signature,hmac.new(key.secret,a.signing_bytes(),hashlib.sha256).hexdigest()):code='BAD_ASSESSMENT_SIGNATURE'
        return Verdict(code,code=='AUTHENTICATED',bool(code=='AUTHENTICATED' and key.assurance=='operator_managed'))
