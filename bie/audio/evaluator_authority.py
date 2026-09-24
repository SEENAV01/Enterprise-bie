"""H9-004: signed evaluator release authority bound to profile and calibration.

The trust root is supplied out-of-band. TEST_FIXTURE calibration or TEST_ONLY
issuers cannot authorize production pronunciation acceptance.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import base64, json, time
from .common import AudioError, fingerprint, integer, refs, text
from .evaluator_capability import EvaluatorProfile
from .acoustic_calibration import CalibrationResult


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()


@dataclass(frozen=True)
class AuthorityPayload:
    issuer_id: str
    issuer_role: str
    key_id: str
    key_custody: str
    evaluator_profile_fingerprint: str
    calibration_fingerprint: str
    deployment_environment: str
    issued_at: int
    expires_at: int
    evidence_refs: tuple[str,...]
    schema_version: str = "bie.audio.evaluator-authority/1"
    def __post_init__(self):
        if self.schema_version!="bie.audio.evaluator-authority/1": raise AudioError("EVALUATOR_AUTHORITY_VERSION")
        for k in ("issuer_id","key_id","deployment_environment"): text(getattr(self,k),k,256)
        if self.issuer_role not in ("TEST_ONLY","PRODUCTION_RELEASE_AUTHORITY"): raise AudioError("EVALUATOR_AUTHORITY_ROLE")
        if self.key_custody not in ("EPHEMERAL_TEST","LOCAL_FILE","EXTERNAL_KMS_HSM"): raise AudioError("EVALUATOR_AUTHORITY_CUSTODY")
        from .common import digest
        digest(self.evaluator_profile_fingerprint); digest(self.calibration_fingerprint)
        integer(self.issued_at,"issued at",0,4_000_000_000); integer(self.expires_at,"expires at",self.issued_at+1,4_000_000_000)
        refs(self.evidence_refs,"authority evidence")
    def fingerprint(self): return fingerprint(self)


@dataclass(frozen=True)
class SignedAuthority:
    payload: AuthorityPayload
    signature_b64: str
    def __post_init__(self):
        if type(self.payload) is not AuthorityPayload: raise AudioError("EVALUATOR_AUTHORITY_PAYLOAD")
        text(self.signature_b64,"authority signature",512)
        try:
            raw=base64.b64decode(self.signature_b64,validate=True)
        except Exception as exc: raise AudioError("EVALUATOR_AUTHORITY_SIGNATURE") from exc
        if len(raw)!=64: raise AudioError("EVALUATOR_AUTHORITY_SIGNATURE")


@dataclass(frozen=True)
class AuthorityTrust:
    key_id: str
    issuer_id: str
    public_key_b64: str
    allow_production: bool
    max_age_seconds: int = 30*24*3600
    max_future_skew_seconds: int = 300
    def __post_init__(self):
        text(self.key_id,"trust key",256); text(self.issuer_id,"trust issuer",256); text(self.public_key_b64,"public key",256)
        if type(self.allow_production) is not bool: raise AudioError("EVALUATOR_TRUST_BOOLEAN")
        integer(self.max_age_seconds,"max age",1,365*24*3600); integer(self.max_future_skew_seconds,"future skew",0,3600)
        try:
            raw=base64.b64decode(self.public_key_b64,validate=True)
        except Exception as exc: raise AudioError("EVALUATOR_TRUST_KEY") from exc
        if len(raw)!=32: raise AudioError("EVALUATOR_TRUST_KEY")


def sign_authority(payload:AuthorityPayload, private_key):
    if type(payload) is not AuthorityPayload: raise AudioError("EVALUATOR_AUTHORITY_PAYLOAD")
    sig=private_key.sign(b"BIE-AUDIO-EVALUATOR-AUTHORITY\0"+_canonical(asdict(payload)))
    return SignedAuthority(payload,base64.b64encode(sig).decode())


def verify_authority(signed:SignedAuthority, trust:AuthorityTrust, profile:EvaluatorProfile, calibration:CalibrationResult, *, now:int|None=None):
    if type(signed) is not SignedAuthority or type(trust) is not AuthorityTrust or type(profile) is not EvaluatorProfile or type(calibration) is not CalibrationResult:
        raise AudioError("EVALUATOR_AUTHORITY_INPUT")
    p=signed.payload; now=int(time.time()) if now is None else now; integer(now,"now",0,4_000_000_000)
    if p.key_id!=trust.key_id or p.issuer_id!=trust.issuer_id: raise AudioError("EVALUATOR_AUTHORITY_TRUST")
    if p.evaluator_profile_fingerprint!=profile.fingerprint() or p.calibration_fingerprint!=calibration.fingerprint(): raise AudioError("EVALUATOR_AUTHORITY_BINDING")
    if now+trust.max_future_skew_seconds<p.issued_at or now>p.expires_at or now-p.issued_at>trust.max_age_seconds: raise AudioError("EVALUATOR_AUTHORITY_FRESHNESS")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    try:
        pub=Ed25519PublicKey.from_public_bytes(base64.b64decode(trust.public_key_b64,validate=True))
        pub.verify(base64.b64decode(signed.signature_b64,validate=True),b"BIE-AUDIO-EVALUATOR-AUTHORITY\0"+_canonical(asdict(p)))
    except Exception as exc: raise AudioError("EVALUATOR_AUTHORITY_SIGNATURE") from exc
    production=(p.issuer_role=="PRODUCTION_RELEASE_AUTHORITY" and p.key_custody=="EXTERNAL_KMS_HSM" and trust.allow_production
        and calibration.status=="CALIBRATED" and calibration.calibration_scope=="HELD_OUT_INDEPENDENT")
    return {"verified":True,"production_authorized":production,"authority_fingerprint":p.fingerprint(),
            "scope":"PRODUCTION_AUTHORIZED" if production else "VERIFIED_NON_PRODUCTION"}
