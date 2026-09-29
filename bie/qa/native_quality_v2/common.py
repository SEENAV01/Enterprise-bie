"""H3 shared byte-bound contracts; no verdict in this module authorizes release."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from ..release_v2.contracts import ContractError, ArtifactRef, canonical_bytes, digest, token, integer, sha256, revision
from ..publication_v2.contracts import strict_json
from ..source_v2.io import SnapshotStore
from ..reasoning_v2.attestation import ReviewVerifier, Review

SCHEMA = 'bie.qa.native-quality/1'
MAX_ITEMS = 4096

def require(ok: bool, code: str) -> None:
    if not ok: raise ContractError(code)

def fields(obj: Any, names: tuple[str,...] | set[str], code='NATIVE_FIELDS') -> dict:
    require(type(obj) is dict and set(obj)==set(names),code)
    return obj

def items(value: Any, name: str, minimum=0, maximum=MAX_ITEMS) -> list:
    require(type(value) is list and minimum<=len(value)<=maximum, name+'_INVENTORY')
    return value

def text(value: Any, name: str, maximum=262144) -> str:
    require(type(value) is str and bool(value.strip()) and len(value)<=maximum and '\x00' not in value, name+'_TEXT')
    try: value.encode('utf-8')
    except UnicodeError as exc: raise ContractError(name+'_UNICODE') from exc
    return value

def unique(rows: list, key: str, code: str) -> dict:
    require(all(type(r) is dict and key in r and type(r[key]) is str for r in rows),code)
    require(len({r[key] for r in rows})==len(rows),code)
    return {r[key]:r for r in rows}

def read_json(store: SnapshotStore, ref: ArtifactRef) -> dict:
    data=strict_json(store.read(ref))
    require(type(data) is dict,'NATIVE_JSON_OBJECT')
    return data

@dataclass(frozen=True,slots=True)
class Binding:
    run_id: str
    revision: str
    candidate_digest: str
    policy_digest: str
    def __post_init__(self):
        token(self.run_id,'run_id');revision(self.revision)
        sha256(self.candidate_digest,'candidate');sha256(self.policy_digest,'policy')
    @property
    def content_digest(self): return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class Finding:
    code: str
    subject: str
    severity: str = 'REVIEW'
    def __post_init__(self):
        token(self.code,'code');text(self.subject,'subject',256)
        require(self.severity in ('BLOCKER','REVIEW','ADVISORY'),'NATIVE_SEVERITY')

@dataclass(frozen=True,slots=True)
class Report:
    task_id: str
    binding: Binding
    findings: tuple[Finding,...]
    inspected: tuple[ArtifactRef,...]
    details_digest: str
    def __post_init__(self):
        token(self.task_id,'task_id');require(type(self.binding) is Binding,'REPORT_BINDING')
        require(type(self.findings) is tuple and all(type(f) is Finding for f in self.findings),'REPORT_FINDINGS')
        require(type(self.inspected) is tuple and all(type(a) is ArtifactRef for a in self.inspected),'REPORT_ARTIFACTS')
        sha256(self.details_digest,'details_digest')
    @property
    def status(self):
        return 'BLOCKED' if any(f.severity=='BLOCKER' for f in self.findings) else 'REVIEW_REQUIRED' if any(f.severity=='REVIEW' for f in self.findings) else 'LOCAL_CHECKS_CLEAR'
    def to_dict(self):
        return dict(schema_version=SCHEMA,**asdict(self),status=self.status,product_accepted=False,release_authorized=False)


def report(task: str,binding: Binding,findings: list[Finding],inspected=(),details=None) -> Report:
    require(type(binding) is Binding,'NATIVE_BINDING')
    return Report(task,binding,tuple(sorted(set(findings),key=lambda f:(f.code,f.subject,f.severity))),tuple(inspected),digest(details or {}))


def approved(review: Review | None, verifier: ReviewVerifier, *, subject: str, purpose: str,
             request_digest: str, policy_digest: str, now: int, evidence_ids: tuple[str,...], max_age=86400) -> str:
    """Reuse existing scoped authentication. Credentials never come from source data."""
    require(type(verifier) is ReviewVerifier,'NATIVE_TRUST_CONFIGURATION')
    if review is None: return 'REVIEW_REQUIRED'
    a=verifier.verify_bound(review,request_digest,policy_digest,max_age,now)
    if not a.authenticated: return 'BLOCKED'
    if review.subject_id!=subject or review.purpose!=purpose or set(review.evidence_ids)!=set(evidence_ids):return 'BLOCKED'
    if review.verdict=='REJECTED':return 'BLOCKED'
    if not a.operational or review.verdict!='VERIFIED':return 'REVIEW_REQUIRED'
    return 'VERIFIED'


def binding_matches(payload: dict, binding: Binding):
    require(payload==asdict(binding),'NATIVE_BINDING_MISMATCH')
