"""Content-bound factual, teaching-coverage and contradiction checks.

The deterministic kernel verifies scoped atoms. Arbitrary-language parsing,
reference correctness and teaching alignment require independently provisioned
assessments. No keyword/ID match or confidence field is treated as that evidence.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from itertools import combinations
from pathlib import Path
from ..release_v2.contracts import ContractError, digest, integer
from ..source_v2.models import Report, Finding
from ..source_v2.attestation import Assessment, AssessmentVerifier
from ..source_v2.evaluator import evaluate as evaluate_source, EvaluationPair
from .models import SemanticRequest, SemanticPolicy, Normalization, Proposition
from .attestation import SemanticAssessment, SemanticVerifier
from .logic import compare, conflict, validate_rule

LIMITATIONS = (
    'Factual checks are relative to a reviewed, version-bound reference inventory with exact declared context; they do not establish universal or current world truth.',
    'Only symbol polarity, governed single/multi-valued predicates and closed exact-decimal intervals are reasoned over. No language parser, unit conversion, causal inference or general theorem prover runs here.',
    'Normalization completeness, reference correctness, teaching depth and unmodeled semantic consistency depend on authenticated judgments. Authentication is not independent reproduction or calibration of those judgments.',
    'Declared text surfaces are not rendered frames, spoken audio or executed game states. Cinematic/learning quality, real-book E2E, full repository integration and product acceptance remain separate gates.',
)


@dataclass(frozen=True, slots=True)
class SemanticResult:
    source: EvaluationPair
    factual: Report
    coverage: Report
    contradiction: Report

    @property
    def status(self):
        statuses = [r.status for r in (self.source.provenance, self.source.grounding,
                                       self.factual, self.coverage, self.contradiction)]
        if 'BLOCKED' in statuses: return 'BLOCKED'
        if 'REVIEW_REQUIRED' in statuses: return 'REVIEW_REQUIRED'
        return 'CHECKS_PASSED'

    @property
    def product_accepted(self): return False

    def to_dict(self):
        return dict(source=self.source.to_dict(), factual=self.factual.to_dict(),
            coverage=self.coverage.to_dict(), contradiction=self.contradiction.to_dict(),
            status=self.status, product_accepted=False)

    @property
    def content_digest(self): return digest(self.to_dict())


def evaluate(request: SemanticRequest, artifact_root: str | Path, policy: SemanticPolicy, *,
             assessments: tuple[SemanticAssessment, ...] = (), verifier: SemanticVerifier | None = None,
             source_assessments: tuple[Assessment, ...] = (),
             source_verifier: AssessmentVerifier | None = None, as_of: int) -> SemanticResult:
    if type(request) is not SemanticRequest or type(policy) is not SemanticPolicy:
        raise ContractError('INVALID_SEMANTIC_INPUT')
    integer(as_of, 'as_of')
    if type(assessments) is not tuple or len(assessments) > 8192 or any(type(a) is not SemanticAssessment for a in assessments):
        raise ContractError('INVALID_SEMANTIC_ASSESSMENTS')
    if len({a.assessment_id for a in assessments}) != len(assessments):
        raise ContractError('DUPLICATE_SEMANTIC_ASSESSMENT')
    keys = [(a.purpose, a.subject_id, a.evaluator_id) for a in assessments]
    if len(set(keys)) != len(keys): raise ContractError('DUPLICATE_ASSESSOR_VOTE')
    verifier = SemanticVerifier() if verifier is None else verifier
    if type(verifier) is not SemanticVerifier: raise ContractError('INVALID_SEMANTIC_VERIFIER')
    source_result = evaluate_source(request.source, artifact_root, policy.source,
        assessments=source_assessments, verifier=source_verifier, as_of=as_of)
    # Recomputed from real bytes, never accepted as a caller-declared PASS object.
    common = list(source_result.grounding.findings)
    factual: list[Finding] = []
    coverage: list[Finding] = []
    contradictions: list[Finding] = []
    def add(target, code, subject, detail, severity='BLOCKER', owner='QA_SEMANTIC'):
        target.append(Finding(code, severity, subject, owner, detail))

    src = request.source
    claims = {c.claim_id: c for c in src.claims}
    citations = {c.citation_id: c for c in src.citations}
    blocks = {b.block_id: b for b in src.blocks}
    outputs = {o.output_id: o for o in src.outputs}
    norms = {n.claim_id: n for n in request.normalizations}
    rules = {r.predicate_id: r for r in policy.predicates}
    requirements = {r.requirement_id: r for r in policy.requirements}
    refs = {r.reference_id: r for r in request.references}
    if set(refs) != set(policy.expected_reference_ids):
        add(common, 'REFERENCE_INVENTORY_MISMATCH', 'reference-inventory', 'Submitted reference IDs differ from the independently provisioned inventory.')
    if not set(policy.reference_source_ids) <= {s.source_id for s in src.sources}:
        add(common, 'REFERENCE_SOURCE_INVENTORY_MISMATCH', 'reference-sources', 'An approved reference source is absent from the source request.')
    facts = [c for c in src.claims if c.kind == 'FACT']
    if not facts:
        add(common, 'NO_FACTUAL_SCOPE', 'semantic-scope', 'No factual claim inventory is present; semantic success cannot be inferred.', 'REVIEW')

    targets: dict[tuple[str, str], tuple[str, ...]] = {}
    for n in request.normalizations:
        if n.claim_id not in claims or claims[n.claim_id].kind != 'FACT':
            add(common, 'NORMALIZATION_CLAIM_MISMATCH', n.claim_id, 'Normalization must bind an existing FACT claim.')
        else: targets[('normalization', n.claim_id)] = claims[n.claim_id].citation_ids
    for r in request.references: targets[('reference', r.reference_id)] = r.citation_ids
    for l in request.coverage_links:
        targets[('coverage', l.link_id)] = tuple(sorted({e for cid in l.claim_ids if cid in claims for e in claims[cid].citation_ids}))
    targets[('consistency', 'semantic-scope')] = tuple(sorted(citations))
    request_digest, policy_digest = request.content_digest, policy.content_digest
    votes: dict[tuple[str, str], list] = {t: [] for t in targets}
    invalid_targets: set[tuple[str, str]] = set()
    for a in sorted(assessments, key=lambda a: a.assessment_id):
        t = (a.purpose, a.subject_id)
        if t not in targets:
            add(common, 'UNKNOWN_SEMANTIC_ASSESSMENT_SUBJECT', a.subject_id, 'Assessment purpose/subject has no corresponding submitted record.', owner='QA_TRUST')
            continue
        if set(a.evidence_ids) != set(targets[t]):
            add(common, 'SEMANTIC_EVIDENCE_SCOPE_MISMATCH', a.subject_id, 'Assessment must bind the exact citation set required by its subject.', owner='QA_TRUST')
            invalid_targets.add(t); continue
        auth = verifier._verify_bound(a, request_digest, policy_digest, policy.max_receipt_age_seconds, as_of)
        if not auth.authenticated:
            add(common, auth.code, a.subject_id, 'Assessment authentication, freshness, authority or input binding failed.', owner='QA_TRUST')
            invalid_targets.add(t); continue
        if a.verdict == 'REJECTED':
            add(common, 'SEMANTIC_ASSESSMENT_REJECTED', a.subject_id, 'An authenticated assessor reports a failed semantic obligation; a positive vote cannot override it.', owner='QA_TRUST')
            invalid_targets.add(t)
        if not auth.operational:
            add(common, 'TEST_ONLY_SEMANTIC_ASSESSMENT', a.subject_id, 'Test credentials cannot establish operational semantic evidence.', 'REVIEW', 'QA_TRUST')
            invalid_targets.add(t); continue
        if a.verdict != 'VERIFIED' or a.confidence_ppm < policy.minimum_confidence_ppm:
            add(common, 'SEMANTIC_ASSESSMENT_REVIEW', a.subject_id, 'The judgment is uncertain, rejected or below the operator floor.', 'REVIEW', 'QA_TRUST')
            invalid_targets.add(t); continue
        votes[t].append(auth.independence_group)
    ready = set()
    for t, groups in sorted(votes.items()):
        if t not in invalid_targets and len(set(groups)) >= policy.minimum_independent_assessors:
            ready.add(t)
        elif t not in invalid_targets:
            add(common, 'SEMANTIC_ASSESSMENT_QUORUM_MISSING', t[1], f'{t[0]} needs current independently provisioned assessment evidence.', 'REVIEW', 'QA_TRUST')

    reference_valid: set[str] = set()
    for r in request.references:
        rule = rules.get(r.proposition.predicate_id)
        try:
            if rule is None: raise ContractError('UNKNOWN_PREDICATE_RULE')
            validate_rule(r.proposition, rule)
        except ContractError as exc:
            add(common, exc.code, r.reference_id, 'Reference proposition is outside the governed relation/context/unit contract.'); continue
        valid_cites = True
        for cid in r.citation_ids:
            citation = citations.get(cid)
            block = blocks.get(citation.block_id) if citation else None
            if block is None or block.source_id not in policy.reference_source_ids:
                add(common, 'REFERENCE_SOURCE_NOT_APPROVED', r.reference_id, 'A reference citation is unresolved or outside the operator-approved source inventory.')
                valid_cites = False
        if valid_cites and ('reference', r.reference_id) in ready and source_result.provenance.status == 'CHECKS_PASSED':
            reference_valid.add(r.reference_id)

    normalized_valid: set[str] = set()
    atoms: list[tuple[str, Proposition]] = []
    for c in facts:
        n = norms.get(c.claim_id)
        if n is None:
            add(common, 'CLAIM_NORMALIZATION_MISSING', c.claim_id, 'Every factual claim requires complete, reviewed normalization; text labels cannot bypass it.', 'REVIEW')
            continue
        good = True
        for p in n.propositions:
            try:
                rule = rules.get(p.predicate_id)
                if rule is None: raise ContractError('UNKNOWN_PREDICATE_RULE')
                validate_rule(p, rule)
            except ContractError as exc:
                add(common, exc.code, c.claim_id, 'Claim context, unit or predicate cannot be silently normalized.')
                good = False
        if good:
            atoms.extend((c.claim_id, p) for p in n.propositions)
            if ('normalization', c.claim_id) in ready:
                normalized_valid.add(c.claim_id)
    n, m = len(atoms), len(request.references)
    comparisons_required = n*m + n*(n-1)//2 + m*(m-1)//2
    budget_ok = comparisons_required <= policy.max_comparisons
    comparisons_executed = 0
    if not budget_ok:
        add(common, 'SEMANTIC_COMPARISON_BUDGET_EXCEEDED', 'semantic-scope',
            'Complete declared comparison scope exceeds the policy bound; no truncated scan can pass.')

    conflicted_references = set()
    candidate_conflicts = 0
    supported_claims: set[str] = set()
    if budget_ok:
        for a, b in combinations(request.references, 2):
            comparisons_executed += 1
            if a.reference_id not in reference_valid or b.reference_id not in reference_valid: continue
            if a.proposition.predicate_id != b.proposition.predicate_id: continue
            if conflict(a.proposition, b.proposition, rules[a.proposition.predicate_id]):
                conflicted_references.update((a.reference_id, b.reference_id))
                add(common, 'CONFLICTING_REFERENCE_FACTS', a.reference_id,
                    f'Reviewed reference {b.reference_id} asserts an incompatible value in the same scope. No source is silently preferred.')
        usable_refs = reference_valid - conflicted_references
        for c in facts:
            norm = norms.get(c.claim_id)
            if norm is None: continue
            if c.claim_id not in normalized_valid:
                add(factual, 'FACTUAL_NORMALIZATION_UNVERIFIED', c.claim_id, 'Structured fields cannot establish what the output says without a complete authenticated normalization.', 'REVIEW')
                continue
            all_supported = True
            for p in norm.propositions:
                supported_by, contradicted_by = [], []
                for r in request.references:
                    comparisons_executed += 1
                    if r.reference_id not in usable_refs or p.predicate_id != r.proposition.predicate_id: continue
                    relation = compare(r.proposition, p, rules[p.predicate_id])
                    if relation == 'CONTRADICTS': contradicted_by.append(r.reference_id)
                    elif relation == 'ENTAILS' and set(r.citation_ids) <= set(c.citation_ids):
                        supported_by.append(r.reference_id)
                if contradicted_by:
                    all_supported = False
                    add(factual, 'FACT_CONTRADICTS_REFERENCE', c.claim_id,
                        'Incompatible with reviewed same-scope reference(s): ' + ','.join(sorted(contradicted_by)[:12]))
                elif not supported_by:
                    all_supported = False
                    add(factual, 'FACT_NOT_ESTABLISHED', c.claim_id,
                        'No cited reviewed reference entails this proposition. Overlap, missing scope and uncited references do not count.', 'REVIEW')
            if all_supported and source_result.grounding.status == 'CHECKS_PASSED':
                supported_claims.add(c.claim_id)
        for (cid_a, a), (cid_b, b) in combinations(atoms, 2):
            comparisons_executed += 1
            if a.predicate_id != b.predicate_id: continue
            if conflict(a, b, rules[a.predicate_id]):
                reviewed = cid_a in normalized_valid and cid_b in normalized_valid
                candidate_conflicts += 1
                add(contradictions, 'OUTPUT_CONTRADICTION' if reviewed else 'UNVERIFIED_CONFLICT_CANDIDATE', cid_a,
                    f'Incompatible with claim {cid_b} under the same governed scope. Output channels do not isolate contradictions.',
                    'BLOCKER' if reviewed else 'REVIEW')
    if ('consistency', 'semantic-scope') not in ready:
        add(contradictions, 'UNMODELED_SEMANTIC_CONSISTENCY_UNASSESSED', 'semantic-scope',
            'No complete authorized review of the declared text inventory; absence of typed conflicts is not proof of general consistency.', 'REVIEW')

    covered = set()
    proposed = set()
    for l in request.coverage_links:
        requirement = requirements.get(l.requirement_id)
        if requirement is None:
            add(coverage, 'UNKNOWN_COVERAGE_REQUIREMENT', l.link_id, 'Generated output cannot add or replace operator learning requirements.'); continue
        proposed.add(l.requirement_id)
        if any(cid not in claims for cid in l.claim_ids):
            add(coverage, 'COVERAGE_CLAIM_MISSING', l.link_id, 'Coverage must bind actual classified output claims.'); continue
        if any(outputs[claims[cid].output_id].channel not in requirement.allowed_channels
               for cid in l.claim_ids if claims[cid].output_id in outputs):
            add(coverage, 'COVERAGE_CHANNEL_MISMATCH', l.link_id, 'A required teaching facet is not provided through an allowed channel.'); continue
        if l.depth < requirement.minimum_depth:
            add(coverage, 'COVERAGE_DEPTH_INSUFFICIENT', l.link_id, 'Mentioning a concept is not the required explanation/application/derivation.', 'REVIEW'); continue
        linked_facts = [cid for cid in l.claim_ids if claims[cid].kind == 'FACT']
        if not linked_facts or any(cid not in supported_claims for cid in linked_facts):
            add(coverage, 'COVERAGE_FACTUAL_SUPPORT_MISSING', l.link_id, 'Teaching credit needs established factual content, not only a question/instruction label.', 'REVIEW'); continue
        if ('coverage', l.link_id) not in ready:
            add(coverage, 'COVERAGE_ALIGNMENT_UNASSESSED', l.link_id, 'A concept ID or asserted depth cannot establish that this surface actually teaches the facet.', 'REVIEW'); continue
        if source_result.grounding.status == 'CHECKS_PASSED': covered.add(l.requirement_id)
    total_weight = sum(r.weight for r in policy.requirements)
    covered_weight = sum(r.weight for r in policy.requirements if r.requirement_id in covered)
    weighted_ppm = covered_weight * 1000000 // total_weight
    for r in policy.requirements:
        if r.requirement_id not in covered:
            add(coverage, 'CRITICAL_CONCEPT_FACET_UNCOVERED' if r.critical else 'CONCEPT_FACET_UNCOVERED', r.requirement_id,
                'The required concept facet lacks verified teaching evidence; duplicate links never increase coverage.',
                'BLOCKER' if r.critical else 'REVIEW', 'PED_COVERAGE')
    if weighted_ppm < policy.minimum_weighted_coverage_ppm:
        add(coverage, 'WEIGHTED_COVERAGE_BELOW_FLOOR', 'concept-coverage', 'Verified unique requirement coverage is below the operator floor.', owner='PED_COVERAGE')
    # A contradiction invalidates apparent coverage credit, even when individual
    # sentences separately match different references or received positive votes.
    if any(f.severity == 'BLOCKER' for f in contradictions):
        add(coverage, 'COVERAGE_CONTRADICTION_BLOCKER', 'concept-coverage', 'Unresolved output contradiction prevents accepting the learning coverage.')
    evidence_digest = digest(dict(assessments=[asdict(a) for a in sorted(assessments, key=lambda a: a.assessment_id)],
        trust_configuration=verifier.configuration_digest, source_result=source_result.to_dict()))
    base_metrics = (('factual_claims', len(facts)), ('normalized_claims', len(normalized_valid)),
        ('reviewed_reference_facts', len(reference_valid)), ('comparisons_required', comparisons_required),
        ('comparisons_executed', comparisons_executed))
    def report(task, findings, metrics=()):
        ordered = tuple(sorted(set(common + findings), key=lambda f: (f.subject_id, f.code, f.severity, f.owner, f.detail)))
        return Report(task, request_digest, policy_digest, evidence_digest, as_of, ordered,
            tuple(sorted(base_metrics + metrics)), source_result.provenance.inspected_artifact_ids, LIMITATIONS)
    return SemanticResult(source_result,
        report('BIE-QA-SEM-001', factual, (('established_claims', len(supported_claims)),)),
        report('BIE-QA-SEM-002', factual + coverage, (('requirements', len(requirements)),
            ('requirements_covered', len(covered)), ('weighted_coverage_ppm', weighted_ppm),
            ('required_weight', total_weight), ('covered_weight', covered_weight))),
        report('BIE-QA-SEM-003', contradictions, (('typed_conflict_witnesses', candidate_conflicts),
            ('reference_conflicts', len(conflicted_references)))))


def evaluate_factual(*args, **kwargs): return evaluate(*args, **kwargs).factual

def evaluate_coverage(*args, **kwargs): return evaluate(*args, **kwargs).coverage

def evaluate_contradictions(*args, **kwargs): return evaluate(*args, **kwargs).contradiction


def verify_reports(actual: SemanticResult, *args, **kwargs) -> SemanticResult:
    expected = evaluate(*args, **kwargs)
    if type(actual) is not SemanticResult or actual != expected:
        raise ContractError('STALE_OR_EDITED_SEMANTIC_REPORT')
    return actual
