"""Provider-neutral authenticated grading receipt boundary for DIR/PED context.

Cryptographic verification remains the configured identity provider's job.  BIE
persists only the verified claim set and token/signature digests, and then binds
that receipt to exact source, learner, item, response, score and expiry fields.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib

from .contract_validation import finite, ids, nonblank
from .director_artifacts import canonical, fields, fingerprint


@dataclass(frozen=True)
class SignedGradeSubmission:
    grade_id: str
    issuer: str
    key_id: str
    learner_key: str
    concept_id: str
    item_id: str
    response_text: str
    score: float
    reliability: float
    issued_at_utc: str
    expires_at_utc: str
    signature: bytes

    def signed_payload(self, source_catalog_ref):
        return {
            "schema_version": "bie.ped.signed_grade/1.0.0",
            "source_catalog_ref": asdict(source_catalog_ref),
            **{key: value for key, value in asdict(self).items() if key != "signature"},
            "response_sha256": "sha256:" + hashlib.sha256(self.response_text.encode("utf-8")).hexdigest(),
        }


@dataclass(frozen=True)
class VerifiedGradeIdentity:
    issuer: str
    key_id: str
    subject: str
    grade_id: str
    verified_at_utc: str
    assurance: str


@dataclass(frozen=True)
class AuthenticatedAssessmentPolicy:
    version: str = "bie-dir-authenticated-assessment/1.0.0"
    allowed_issuers: tuple[str, ...] = ()
    maximum_clock_skew_seconds: int = 300
    minimum_assurance: str = "AUTHENTICATED_GRADER"

    def validate(self):
        nonblank(self.version, "authenticated assessment policy")
        ids(self.allowed_issuers, "allowed grading issuers", required=False)
        if type(self.maximum_clock_skew_seconds) is not int or not 0 <= self.maximum_clock_skew_seconds <= 3600:
            raise ValueError("bounded grading clock skew required")
        nonblank(self.minimum_assurance, "minimum grading assurance")


def _instant(value, name):
    nonblank(value, name)
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid " + name) from error
    if instant.tzinfo is None:
        raise ValueError(name + " must include timezone")
    return instant.astimezone(timezone.utc)


def validate_submission(submission, source_catalog_ref, policy, now_utc):
    if not isinstance(submission, SignedGradeSubmission) or not isinstance(policy, AuthenticatedAssessmentPolicy):
        raise ValueError("typed signed grade and policy required")
    policy.validate()
    for value in (submission.grade_id, submission.issuer, submission.key_id, submission.learner_key,
                  submission.concept_id, submission.item_id, submission.response_text):
        nonblank(value, "signed grade field")
    if policy.allowed_issuers and submission.issuer not in policy.allowed_issuers:
        raise ValueError("grading issuer is not allowed")
    finite(submission.score, "authenticated score", high=1)
    finite(submission.reliability, "authenticated reliability", high=1)
    if type(submission.signature) is not bytes or len(submission.signature) < 16 or len(submission.signature) > 8192:
        raise ValueError("bounded binary signature required")
    issued = _instant(submission.issued_at_utc, "grade issue time")
    expires = _instant(submission.expires_at_utc, "grade expiry time")
    now = _instant(now_utc, "verification time")
    skew = policy.maximum_clock_skew_seconds
    if expires <= issued or now.timestamp() + skew < issued.timestamp() or now.timestamp() - skew > expires.timestamp():
        raise ValueError("signed grade is not currently valid")
    return submission.signed_payload(source_catalog_ref)


def publish_authenticated_assessment(io, run_id, source_ref, submission, verifier, *,
                                     now_utc, policy=AuthenticatedAssessmentPolicy()):
    """Verify once through a configured provider and persist an auditable receipt."""
    payload = validate_submission(submission, source_ref, policy, now_utc)
    if not callable(getattr(verifier, "verify_grade", None)):
        raise ValueError("configured grade identity verifier required")
    signature_digest = "sha256:" + hashlib.sha256(submission.signature).hexdigest()
    payload_digest = fingerprint(payload)
    identity = verifier.verify_grade(canonical(payload).encode("utf-8"), submission.signature,
                                     submission.issuer, submission.key_id, now_utc)
    if not isinstance(identity, VerifiedGradeIdentity):
        raise ValueError("grade verifier must return a typed verified identity")
    for value in asdict(identity).values():
        nonblank(value, "verified grade identity")
    if ((identity.issuer, identity.key_id, identity.subject, identity.grade_id) !=
            (submission.issuer, submission.key_id, submission.learner_key, submission.grade_id)):
        raise ValueError("verified grade identity does not bind the submission")
    if identity.assurance != policy.minimum_assurance:
        raise ValueError("insufficient grading assurance")
    _instant(identity.verified_at_utc, "identity verification time")
    source = io.load(source_ref)
    if source.run_id != run_id or source.artifact_type != "document.source_catalog":
        raise ValueError("authenticated grade needs the exact source catalog")
    record = {
        "schema_version": "bie.ped.authenticated_assessment/1.0.0",
        "source_catalog_ref": asdict(source_ref),
        "learner_key": submission.learner_key,
        "concept_id": submission.concept_id,
        "item_id": submission.item_id,
        "response_text": submission.response_text,
        "response_sha256": payload["response_sha256"],
        "score": submission.score,
        "reliability": submission.reliability,
        "age_steps": 0,
        "score_origin": "AUTHENTICATED_GRADED_RESPONSE",
        "grade_id": submission.grade_id,
        "issued_at_utc": submission.issued_at_utc,
        "expires_at_utc": submission.expires_at_utc,
        "payload_fingerprint": payload_digest,
        "signature_sha256": signature_digest,
        "verification_identity": asdict(identity),
        "verification_policy": asdict(policy),
    }
    return io.derive("evidence.pedagogy_assessment.authenticated", run_id, (source_ref,), record,
        stage_id="PEDAGOGY", metadata={"requires_review": True, "accepted": False,
            "authenticated": True, "grade_id": submission.grade_id}, evidence=True)


def validate_authenticated_assessment(io, event, source_ref):
    if event.artifact_type != "evidence.pedagogy_assessment.authenticated" or event.schema_version != "1.0.0":
        raise ValueError("authenticated assessment artifact required")
    data = fields(event.payload, (
        "schema_version", "source_catalog_ref", "learner_key", "concept_id", "item_id",
        "response_text", "response_sha256", "score", "reliability", "age_steps", "score_origin",
        "grade_id", "issued_at_utc", "expires_at_utc", "payload_fingerprint", "signature_sha256",
        "verification_identity", "verification_policy"), "authenticated assessment")
    from .director_artifacts import reference
    if data["schema_version"] != "bie.ped.authenticated_assessment/1.0.0" or reference(data["source_catalog_ref"]) != source_ref:
        raise ValueError("stale authenticated assessment")
    if event.parent_refs != [source_ref] or event.run_id != io.load(source_ref).run_id:
        raise ValueError("authenticated assessment ancestry mismatch")
    if data["response_sha256"] != "sha256:" + hashlib.sha256(data["response_text"].encode("utf-8")).hexdigest():
        raise ValueError("authenticated response bytes changed")
    if data["score_origin"] != "AUTHENTICATED_GRADED_RESPONSE" or event.metadata.get("authenticated") is not True:
        raise ValueError("authenticated grade marker missing")
    policy = AuthenticatedAssessmentPolicy(**data["verification_policy"])
    policy.validate()
    identity = VerifiedGradeIdentity(**data["verification_identity"])
    if (identity.issuer, identity.key_id, identity.subject, identity.grade_id) != (
            data["verification_identity"]["issuer"], data["verification_identity"]["key_id"],
            data["learner_key"], data["grade_id"]):
        raise ValueError("persisted grading identity changed")
    for name in ("learner_key", "concept_id", "item_id", "response_text", "grade_id"):
        nonblank(data[name], name)
    finite(data["score"], "authenticated score", high=1)
    finite(data["reliability"], "authenticated reliability", high=1)
    for value in asdict(identity).values():
        nonblank(value, "verified grade identity")
    if policy.allowed_issuers and identity.issuer not in policy.allowed_issuers:
        raise ValueError("persisted grading issuer is not allowed")
    if identity.assurance != policy.minimum_assurance:
        raise ValueError("persisted grading assurance changed")
    _instant(data["issued_at_utc"], "grade issue time")
    _instant(data["expires_at_utc"], "grade expiry time")
    _instant(identity.verified_at_utc, "identity verification time")
    expected_payload = {
        "schema_version": "bie.ped.signed_grade/1.0.0",
        "source_catalog_ref": data["source_catalog_ref"],
        "grade_id": data["grade_id"], "issuer": identity.issuer, "key_id": identity.key_id,
        "learner_key": data["learner_key"], "concept_id": data["concept_id"],
        "item_id": data["item_id"], "response_text": data["response_text"],
        "score": data["score"], "reliability": data["reliability"],
        "issued_at_utc": data["issued_at_utc"], "expires_at_utc": data["expires_at_utc"],
        "response_sha256": data["response_sha256"],
    }
    if data["payload_fingerprint"] != fingerprint(expected_payload):
        raise ValueError("authenticated signed payload fields changed")
    if (type(data["signature_sha256"]) is not str or not data["signature_sha256"].startswith("sha256:")
            or len(data["signature_sha256"]) != 71):
        raise ValueError("authenticated signature digest changed")
    if data["age_steps"] != 0:
        raise ValueError("new authenticated observation cannot claim historical age")
    return data
