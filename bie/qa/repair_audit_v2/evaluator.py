"""Independent audit of inherited repair-attempt bytes and detailed case evidence."""
from dataclasses import dataclass,asdict,replace
from ..release_v2.contracts import ContractError,canonical_bytes,digest,integer
from ..source_v2.models import Report,Finding
from ..source_v2.io import SnapshotStore
from ..reasoning_v2.attestation import ReviewVerifier
from ..repair_v2.models import RepairPolicy
from ..repair_v2.planner import classify,approved,validate_proposal
from .models import AuditRequest,AuditPolicy,candidate_for
from .io import object_bytes,equal,verify_files
from .evidence import inspect_attempt,inspect_journal,inspect_generation
from .regression import inspect_regression,validate_obligations

LIMITS=(
    'Local repair evidence and explicitly enumerated regression cases only; not full canonical regression or release.',
    'Hash chains are not signatures; operator-managed assessment authenticates records, not evaluator correctness.',
    'Trusted validator process isolation is not a hostile-code sandbox or an independently measured learner outcome.',
    'All native media, browser, real-book, calibration and canonical integration obligations remain open.'
)
@dataclass(frozen=True,slots=True)
class AuditResult:
    evidence: Report
    regression: Report
    changes: tuple[str,...]
    @property
    def status(self):
        values=(self.evidence.status,self.regression.status)
        return 'BLOCKED' if 'BLOCKED' in values else 'REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in values else 'CHECKS_PASSED'
    def to_dict(self):
        return dict(schema_version='bie.qa.repair-audit/1',evidence=self.evidence.to_dict(),regression=self.regression.to_dict(),
            changed_artifact_ids=self.changes,status=self.status,scope='LOCAL_REPAIR_AUDIT_ONLY',
            full_repository_regression_run=False,product_accepted=False)

def evaluate(request,original_root,candidate_root,repair_policy,audit_policy,*,as_of,
             inventory_reviews=(),proposal_reviews=(),audit_reviews=(),verifier=None):
    integer(as_of,'as_of')
    if type(request) is not AuditRequest or type(audit_policy) is not AuditPolicy or type(repair_policy) is not RepairPolicy:
        raise ContractError('AUDIT_INPUT_TYPE')
    verifier=ReviewVerifier() if verifier is None else verifier
    ef=[];rf=[];inspected=[];counts=[];changes=();reserved=None
    def add(target,code,severity='BLOCKER',detail='Repair evidence requirement not satisfied.'):
        target.append(Finding(code,severity,'repair-audit','QA',detail))
    try:
        validate_obligations(request.snapshot,request.proposal,repair_policy,audit_policy)
        equal(request.batch.snapshot_digest,request.snapshot.content_digest,'AUDIT_FAILURE_BASE')
        if original_root is None or candidate_root is None:raise ContractError('AUDIT_ROOT_REQUIRED')
        from pathlib import Path
        a=Path(original_root).resolve();b=Path(candidate_root).resolve()
        if a==b or a.is_relative_to(b) or b.is_relative_to(a):raise ContractError('AUDIT_ROOT_OVERLAP')
        verify_files(original_root,request.snapshot)
        expected=candidate_for(request.snapshot,request.proposal)
        verify_files(candidate_root,expected,exact=True)
        with SnapshotStore(original_root) as store:
            attempt=object_bytes(store,request.attempt,audit_policy.max_evidence_bytes)
            journal=object_bytes(store,request.journal,audit_policy.max_evidence_bytes)
            # Hash validation must precede accepting any journal fields as context.
            from .evidence import ATTEMPT_FIELDS
            from .io import fields
            fields(attempt,ATTEMPT_FIELDS,'AUDIT_ATTEMPT_SCHEMA')
            body={k:v for k,v in attempt.items() if k not in ('receipt_digest','journal_head')}
            equal(attempt['receipt_digest'],digest(body),'AUDIT_ATTEMPT_HASH')
            reserved=inspect_journal(journal,request.snapshot,request.proposal,repair_policy,attempt,
                as_of=as_of,max_age=audit_policy.max_receipt_age_seconds)
            inspected.extend((request.attempt.artifact_id,request.journal.artifact_id))
        # Replay classification at the actual reservation's operator clock. Missing
        # approvals remain review blockers; a reconstructed plan is NOT authorization.
        plan=classify(request.batch,request.snapshot,original_root,repair_policy,as_of=reserved['reserved_at'],
            reviews=inventory_reviews,verifier=verifier)
        inspected.extend(b.artifact.artifact_id for b in request.batch.reports)
        if not plan.authenticated or plan.diagnostics:
            add(ef,'AUDIT_INVENTORY_AUTH_REQUIRED','REVIEW','Original failure-inventory authorization is missing or invalid.')
        reconstructed=replace(plan,authenticated=True,diagnostics=())
        validate_proposal(request.proposal,reconstructed,request.snapshot,repair_policy)
        expected,required,invalidated=inspect_attempt(attempt,request.snapshot,request.proposal,repair_policy,reconstructed)
        ok,reasons=approved(proposal_reviews,verifier,subject=request.proposal.proposal_id,purpose='inference',
            request_digest=request.proposal.content_digest,policy=repair_policy,
            evidence_ids=tuple(r.artifact.artifact_id for r in request.proposal.replacements),now=reserved['reserved_at'])
        if not ok:add(ef,'AUDIT_PROPOSAL_AUTH_REQUIRED','REVIEW','Proposal approval must have been valid at reservation time.')
        ok,reasons=approved(audit_reviews,verifier,subject='repair-audit-execution',purpose='support',
            request_digest=request.content_digest,policy=audit_policy,evidence_ids=tuple(a.artifact_id for a in request.evidence_refs),now=as_of)
        if not ok:add(ef,'AUDIT_EXECUTION_AUTH_REQUIRED','REVIEW','Execution/generation record authenticity requires a fresh, separately provisioned review.')
        if attempt['remaining_failure_ids']:
            add(ef,'AUDIT_REMAINING_FAILURES','REVIEW','Non-target failures remain open; this repair cannot certify the product.')
        if audit_policy.require_generation and not request.generation:raise ContractError('AUDIT_GENERATION_REQUIRED')
        with SnapshotStore(original_root) as store:
            # Replacements are inspected independently of their candidate copy.
            for r in request.proposal.replacements:store.read(r.artifact);inspected.append(r.artifact.artifact_id)
            for link in request.generation:
                inspect_generation(link,store,request,repair_policy,audit_policy,required,invalidated)
                inspected.extend(a.artifact_id for a in (link.job,link.receipt,link.domain_policy,link.limits))
        changed_paths={r.path for r in request.proposal.replacements}
        changes=tuple(sorted(a.artifact_id for a in expected.artifacts if a.path in changed_paths))
        inspected.extend(a.artifact_id for a in request.snapshot.artifacts)
        counts.extend((('verified_snapshot_files',len(expected.artifacts)),('changed_files',len(changes)),('required_checks',len(required)),('generation_receipts',len(request.generation))))
    except (ContractError,OSError,KeyError,TypeError,ValueError) as exc:
        code=exc.code if isinstance(exc,ContractError) else 'AUDIT_EVIDENCE_INVALID'
        add(ef,code);add(rf,'AUDIT_EVIDENCE_PREREQUISITE_FAILED')
    if not any(f.severity=='BLOCKER' for f in ef):
        try:
            with SnapshotStore(original_root) as store:
                regression=object_bytes(store,request.regression,audit_policy.max_evidence_bytes)
            data=inspect_regression(regression,request.snapshot,request.proposal,repair_policy,audit_policy,as_of=as_of)
            if reserved is not None and regression['evaluated_at']<reserved['reserved_at']:
                raise ContractError('AUDIT_REGRESSION_PREDATES_REPAIR')
            inspected.append(request.regression.artifact_id)
            counts.extend((('case_pairs',data['case_count']),('target_cases',data['target_count'])))
            for code,key in data['problems']:
                add(rf,code,detail='Case failed: '+key[0]+':'+key[1])
            if any(f.severity=='REVIEW' for f in ef):add(rf,'AUDIT_EVIDENCE_AUTH_OR_SCOPE_PENDING','REVIEW','Unsigned or unresolved evidence cannot authorize regression acceptance.')
        except (ContractError,OSError,KeyError,TypeError,ValueError) as exc:
            add(rf,exc.code if isinstance(exc,ContractError) else 'AUDIT_REGRESSION_INVALID')
    # Re-read originals/candidate after every successful verification path.
    if not any(f.severity=='BLOCKER' for f in ef+rf):
        try:
            verify_files(original_root,request.snapshot);verify_files(candidate_root,candidate_for(request.snapshot,request.proposal),exact=True)
        except (ContractError,OSError) as exc:
            add(ef,exc.code if isinstance(exc,ContractError) else 'AUDIT_POSTCHECK_IO');add(rf,'AUDIT_POSTCHECK_IO')
    evidence_digest=digest(dict(request=request.content_digest,repair_policy=repair_policy.content_digest,audit_policy=audit_policy.content_digest))
    def report(task,findings):
        return Report(task,request.content_digest,audit_policy.content_digest,evidence_digest,as_of,
            tuple(sorted(findings,key=lambda f:(f.severity,f.code,f.detail))),tuple(sorted(counts)),tuple(sorted(set(inspected))),LIMITS)
    return AuditResult(report('BIE-QA-REPAIR-012',ef),report('BIE-QA-REPAIR-013',rf),changes)
