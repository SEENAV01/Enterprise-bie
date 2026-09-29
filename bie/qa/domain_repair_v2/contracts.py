"""REPAIR004..007: data-only deterministic transformations of existing QA requests.

Policies, secrets, source bytes and executable callbacks never come from a model.
A generated proposal is not approval, a successful repair, or product acceptance.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from ..release_v2.contracts import ArtifactRef, ContractError, token, integer, choice, sha256, digest
from ..repair_v2.models import mutable_path
TASK_OWNERS={'BIE-QA-REPAIR-004':'BI','BIE-QA-REPAIR-005':'RE','BIE-QA-REPAIR-006':'PED','BIE-QA-REPAIR-007':'DIR'}

@dataclass(frozen=True, slots=True)
class Limits:
    max_proof_calls: int = 128
    max_total_logic_visits: int = 2000000
    max_added_ms: int = 120000
    max_generated_bytes: int = 2*1024*1024
    def __post_init__(self):
        integer(self.max_proof_calls,'max_proof_calls',1,512)
        integer(self.max_total_logic_visits,'max_total_logic_visits',1,20000000)
        integer(self.max_added_ms,'max_added_ms',0,3600000)
        integer(self.max_generated_bytes,'max_generated_bytes',1,16*1024*1024)
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True, slots=True)
class Job:
    job_id: str
    task_id: str
    target: ArtifactRef
    snapshot_digest: str
    batch_digest: str
    repair_policy_digest: str
    domain_policy_digest: str
    limits_digest: str
    def __post_init__(self):
        token(self.job_id,'job_id');choice(self.task_id,tuple(TASK_OWNERS),'task_id')
        if type(self.target) is not ArtifactRef or self.target.role!='support':raise ContractError('DOMAIN_REPAIR_TARGET_TYPE')
        mutable_path(self.target.path)
        for name in ('snapshot_digest','batch_digest','repair_policy_digest','domain_policy_digest','limits_digest'):sha256(getattr(self,name),name)
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True, slots=True)
class Generation:
    job_digest: str
    plan_digest: str
    before_sha256: str
    payload: bytes
    required_checks: tuple[str,...]
    invalidated_checks: tuple[str,...]
    witness: bytes
    @property
    def content_digest(self):
        import hashlib
        return digest(dict(job=self.job_digest,plan=self.plan_digest,before=self.before_sha256,
            after=hashlib.sha256(self.payload).hexdigest(),required=self.required_checks,
            invalidated=self.invalidated_checks,witness_sha256=hashlib.sha256(self.witness).hexdigest()))
    def receipt(self):
        import hashlib,json
        return dict(schema_version='bie.qa.domain-repair-generation/1',generation_digest=self.content_digest,
            job_digest=self.job_digest,plan_digest=self.plan_digest,before_sha256=self.before_sha256,
            after_sha256=hashlib.sha256(self.payload).hexdigest(),generated_bytes=len(self.payload),
            required_checks=self.required_checks,invalidated_previous_checks=self.invalidated_checks,
            witness=json.loads(self.witness),status='PROPOSAL_GENERATED_REVIEW_REQUIRED',
            original_files_written=False,previous_candidate_reviews_reusable=False,
            live_model_invoked=False,canonical_repository_modified=False,product_accepted=False)
