"""Dataset-bound review verification (BIE-EVAL-REG-003).

HMAC keys belong to a trusted supervisor, not the candidate being evaluated.
This verifies operator-provisioned signatures; it does not verify real-world
identities or establish that the scientific review actually happened. HMAC
is shared-secret authentication, NOT independent digital non-repudiation.
Production identity integration and actual expert review remain required.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import hashlib
import hmac
from .models import (BenchmarkError, canonical_json, digest_string, exact_fields,
                     ident, number, text)
from .versioning import Snapshot

ROLES = frozenset({"SCIENCE_REVIEWER", "DATASET_GOVERNOR"})

@dataclass(frozen=True)
class Authority:
    principal_id: str
    role: str
    key_id: str
    key: bytes = field(repr=False)
    revoked: bool = False

    def __post_init__(self) -> None:
        ident(self.principal_id)
        ident(self.key_id)
        if self.role not in ROLES or type(self.key) is not bytes or len(self.key) < 32:
            raise BenchmarkError("INVALID_AUTHORITY")
        if type(self.revoked) is not bool:
            raise BenchmarkError("INVALID_REVOCATION")

@dataclass(frozen=True)
class Approval:
    dataset_sha256: str
    principal_id: str
    role: str
    key_id: str
    decision: str
    issued_at: float
    expires_at: float
    review_evidence_sha256: str
    nonce: str
    signature: str

    def payload(self) -> dict:
        body = asdict(self)
        del body["signature"]
        return body

    def __post_init__(self) -> None:
        for d in (self.dataset_sha256, self.review_evidence_sha256, self.signature):
            digest_string(d)
        for i in (self.principal_id, self.key_id, self.nonce):
            ident(i)
        if self.role not in ROLES or self.decision not in {"APPROVE", "REJECT"}:
            raise BenchmarkError("INVALID_APPROVAL")
        issued, expiry = number(self.issued_at), number(self.expires_at)
        if issued < 0 or not issued < expiry or expiry - issued > 90 * 86400:
            raise BenchmarkError("INVALID_APPROVAL_TIME")

    @classmethod
    def from_dict(cls, body: dict) -> Approval:
        exact_fields(body, set(cls.__dataclass_fields__))
        return cls(**body)


class AuthorityStore:
    def __init__(self, authorities: tuple[Authority, ...]):
        if type(authorities) is not tuple or not authorities:
            raise BenchmarkError("AUTHORITIES_REQUIRED")
        if any(type(a) is not Authority for a in authorities):
            raise BenchmarkError("INVALID_AUTHORITY")
        if len({a.key_id for a in authorities}) != len(authorities):
            raise BenchmarkError("DUPLICATE_AUTHORITY_KEY")
        self._authorities = {a.key_id: a for a in authorities}

    def sign(self, key_id: str, snapshot: Snapshot, *, decision: str, issued_at: float,
             expires_at: float, review_evidence: bytes, nonce: str) -> Approval:
        """Trusted-side helper; never expose this method/key store to candidates."""
        if type(review_evidence) is not bytes or not review_evidence or len(review_evidence) > 2_000_000:
            raise BenchmarkError("REVIEW_EVIDENCE_REQUIRED")
        a = self._authorities.get(key_id)
        if a is None or a.revoked:
            raise BenchmarkError("AUTHORITY_NOT_ACTIVE")
        args = dict(dataset_sha256=snapshot.sha256, principal_id=a.principal_id,
            role=a.role, key_id=a.key_id, decision=decision, issued_at=issued_at,
            expires_at=expires_at, review_evidence_sha256=hashlib.sha256(review_evidence).hexdigest(),
            nonce=nonce, signature="0" * 64)
        unsigned = Approval(**args)
        args["signature"] = hmac.new(a.key, canonical_json(unsigned.payload()).encode(), hashlib.sha256).hexdigest()
        return Approval(**args)

    def verify(self, approval: Approval, snapshot: Snapshot, *, now: float,
               review_evidence: bytes) -> None:
        clock = number(now)
        a = self._authorities.get(approval.key_id)
        if a is None or a.revoked:
            raise BenchmarkError("AUTHORITY_NOT_ACTIVE")
        if a.principal_id != approval.principal_id or a.role != approval.role:
            raise BenchmarkError("AUTHORITY_BINDING_MISMATCH")
        if approval.dataset_sha256 != snapshot.sha256:
            raise BenchmarkError("APPROVAL_DATASET_MISMATCH")
        if not approval.issued_at <= clock < approval.expires_at:
            raise BenchmarkError("APPROVAL_NOT_CURRENT")
        if type(review_evidence) is not bytes or not review_evidence or hashlib.sha256(review_evidence).hexdigest() != approval.review_evidence_sha256:
            raise BenchmarkError("REVIEW_EVIDENCE_MISMATCH")
        expected = hmac.new(a.key, canonical_json(approval.payload()).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, approval.signature):
            raise BenchmarkError("INVALID_APPROVAL_SIGNATURE")

    def authorize_holdout(self, snapshot: Snapshot, approvals: tuple[Approval, ...], *,
                          now: float, evidence: dict[str, bytes]) -> dict:
        """Authorize protected evaluation, NOT release. Any reject vetoes quorum."""
        if any(c.evidence_grade != "REFERENCE_CANDIDATE" for c in snapshot.cases):
            raise BenchmarkError("DIAGNOSTIC_NOT_GOLDEN")
        authors = {c.author_id for c in snapshot.cases}
        principals: set[str] = set()
        roles: set[str] = set()
        if type(approvals) is not tuple or len(approvals) < 2:
            raise BenchmarkError("INSUFFICIENT_INDEPENDENT_REVIEWS")
        for approval in approvals:
            self.verify(approval, snapshot, now=now,
                        review_evidence=evidence.get(approval.review_evidence_sha256, b""))
            if approval.principal_id in principals:
                raise BenchmarkError("DUPLICATE_REVIEWER")
            if approval.principal_id in authors:
                raise BenchmarkError("SELF_REVIEW")
            if approval.decision != "APPROVE":
                raise BenchmarkError("REVIEW_REJECTED")
            principals.add(approval.principal_id)
            roles.add(approval.role)
        if roles != ROLES:
            raise BenchmarkError("MISSING_REVIEW_ROLE")
        return {"dataset_sha256": snapshot.sha256, "evaluation_authorized": True,
                "reviewers": sorted(principals), "release_authorized": False,
                "product_accepted": False, "identity_scope": "OPERATOR_PROVISIONED_HMAC"}
