"""Content-bound provenance and conservative contextual-grounding evaluators.

The provenance result concerns the declared text surface, not whether an entire
video/game faithfully renders it. Contextual support requires an independently
provisioned assessor. No keyword/exact-quote shortcut grants semantic support.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import unicodedata

from ..release_v2.contracts import ContractError, digest, integer
from .models import (Request, Policy, Report, Finding, MAX_TEXT, MAX_ITEMS, text)
from .attestation import Assessment, AssessmentVerifier
from .io import SnapshotStore

LIMITATIONS = (
    'Only declared, operator-scoped UTF-8 output surfaces are checked; actual rendered video and playable game fidelity are separate gates.',
    'UTF-8 sources are compared directly. Other formats require authenticated extraction assessments; this evaluator does not execute PDF extraction or OCR.',
    'Authenticated assessment means a policy-authorized party reported a judgment, not independent proof of factual truth or assessor calibration.',
    'Exact quotation and citation presence do not prove contextual entailment. No model, real-book benchmark, production deployment or product acceptance is implied.',
)


def _word_char(c: str) -> bool:
    return c == '_' or unicodedata.category(c)[:1] in ('L', 'M', 'N')


def _whole_boundaries(s: str, start: int, end: int) -> bool:
    # Combining marks remain part of their lexical token; do not count half a
    # word (including non-Latin letters) as covered evidence.
    return not ((0 < start < len(s) and _word_char(s[start-1]) and _word_char(s[start])) or
                (0 < end < len(s) and _word_char(s[end-1]) and _word_char(s[end])))


def _covered_nonspace(s: str, spans: list[tuple[int, int]]) -> int:
    """Interval union, not additive span lengths; bounded memory and no inflation."""
    merged: list[list[int]] = []
    for a, b in sorted(spans):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return sum(sum(not c.isspace() for c in s[a:b]) for a, b in merged)


@dataclass(frozen=True, slots=True)
class EvaluationPair:
    provenance: Report
    grounding: Report

    def to_dict(self) -> dict:
        return {'provenance': self.provenance.to_dict(), 'grounding': self.grounding.to_dict()}


def evaluate(request: Request, artifact_root: str | Path, policy: Policy, *,
             assessments: tuple[Assessment, ...] = (),
             verifier: AssessmentVerifier | None = None, as_of: int) -> EvaluationPair:
    """Read immutable artifact snapshots once; never modify inputs or the root.

    Trust configuration and expected output IDs must come from the operator,
    never from the untrusted generated request or a submitted assessment.
    Invalid contract shapes raise ContractError; absent/bad evidence is reported
    fail-closed as BLOCKED or REVIEW_REQUIRED, never an optimistic pass.
    """
    if type(request) is not Request or type(policy) is not Policy:
        raise ContractError('INVALID_EVALUATOR_INPUT')
    integer(as_of, 'as_of')
    if type(assessments) is not tuple or len(assessments) > MAX_ITEMS or any(type(a) is not Assessment for a in assessments):
        raise ContractError('INVALID_ASSESSMENT_COLLECTION')
    if len({a.assessment_id for a in assessments}) != len(assessments):
        raise ContractError('DUPLICATE_ASSESSMENT_ID')
    if len({(a.purpose, a.subject_id) for a in assessments}) != len(assessments):
        raise ContractError('DUPLICATE_ASSESSMENT_SUBJECT')
    if verifier is None:
        verifier = AssessmentVerifier()
    if type(verifier) is not AssessmentVerifier:
        raise ContractError('INVALID_ASSESSMENT_VERIFIER')

    prov: list[Finding] = []
    semantic: list[Finding] = []
    def add(code, subject, detail, severity='BLOCKER', owner='BI_SOURCE'):
        prov.append(Finding(code, severity, subject, owner, detail))
    def sem(code, subject, detail, severity='REVIEW'):
        semantic.append(Finding(code, severity, subject, 'KI_SEMANTIC', detail))

    sources = {s.source_id: s for s in request.sources}
    blocks = {b.block_id: b for b in request.blocks}
    outputs = {o.output_id: o for o in request.outputs}
    citations = {c.citation_id: c for c in request.citations}
    claims = {c.claim_id: c for c in request.claims}
    if set(outputs) != set(policy.expected_output_ids):
        add('OUTPUT_SCOPE_MISMATCH', 'scope', 'Submitted output IDs differ from the operator-owned expected scope.', owner='QA_SCOPE')

    raw: dict[str, bytes] = {}
    refs = [s.artifact for s in request.sources] + [o.artifact for o in request.outputs]
    try:
        with SnapshotStore(artifact_root) as store:
            for ref in sorted(refs, key=lambda a: a.artifact_id):
                try:
                    raw[ref.artifact_id] = store.read(ref)
                except ContractError as exc:
                    add(exc.code, ref.artifact_id, 'Actual artifact snapshot could not be verified.')
    except ContractError as exc:
        add(exc.code, 'artifact_root', 'Artifact root is unavailable or unsafe.')

    # Receipt validation is purpose-scoped: a semantic contradiction must not
    # falsely assert that a perfectly resolvable citation is broken.
    request_digest, policy_digest = request.content_digest, policy.content_digest
    assessed: dict[tuple[str, str], Assessment] = {}
    for a in sorted(assessments, key=lambda a: a.assessment_id):
        target = prov if a.purpose == 'extraction' else semantic
        subject_exists = (a.subject_id in sources if a.purpose == 'extraction' else
                          a.subject_id in claims and
                          ((a.purpose == 'semantic') == (claims[a.subject_id].kind == 'FACT')))
        if not subject_exists:
            target.append(Finding('ASSESSMENT_SUBJECT_MISMATCH', 'BLOCKER', a.subject_id,
                                  'QA_TRUST', 'Assessment has no matching subject or purpose in this request.'))
            continue
        trust = verifier._verify_bound(a, request_digest, policy_digest, policy.max_receipt_age_seconds, as_of)
        if not trust.authenticated:
            target.append(Finding(trust.code, 'BLOCKER', a.subject_id, 'QA_TRUST',
                                  'Assessment authentication, authority, freshness or input binding failed.'))
            continue
        if not trust.operator_managed:
            target.append(Finding('TEST_ONLY_ASSESSMENT', 'REVIEW', a.subject_id, 'QA_TRUST',
                                  'Test-only credentials cannot establish operational evidence.'))
            # A declared contradiction stays conservative even in a fixture.
            if a.verdict == 'CONTRADICTED':
                target.append(Finding('ASSESSOR_REPORTED_CONTRADICTION', 'BLOCKER', a.subject_id,
                                      'QA_TRUST', 'The supplied authenticated test assessment reports contradiction.'))
            continue
        assessed[(a.purpose, a.subject_id)] = a

    valid_sources: set[str] = set()
    for source in request.sources:
        members = [b for b in request.blocks if b.source_id == source.source_id]
        payload = raw.get(source.artifact.artifact_id)
        if not members:
            add('SOURCE_WITHOUT_BLOCKS', source.source_id, 'Source has no extracted evidence blocks.')
            continue
        if payload is None:
            continue
        if source.media_type == 'utf8':
            try:
                decoded = payload.decode('utf-8', errors='strict')
                text(decoded, 'source.text')
            except (UnicodeError, ContractError):
                add('INVALID_SOURCE_UTF8', source.source_id, 'UTF-8 source must be nonempty valid bounded text.')
                continue
            if len(members) != 1 or members[0].page != 1 or members[0].text != decoded or members[0].box_ppm != (0, 0, 1_000_000, 1_000_000):
                add('UTF8_EXTRACTION_MISMATCH', source.source_id, 'The UTF-8 adapter requires exactly one complete source block without silent normalization.')
                continue
            valid_sources.add(source.source_id)
        else:
            # A caller declaring "pdf" with arbitrary bytes cannot bypass even
            # the basic format signature. This is NOT a complete format parser.
            valid_magic = (payload.startswith(b'%PDF-') if source.media_type == 'pdf' else
                           payload.startswith(b'PK') if source.media_type in ('epub', 'docx') else True)
            if not valid_magic:
                add('SOURCE_FORMAT_SIGNATURE_MISMATCH', source.source_id, 'Declared source format disagrees with its basic byte signature.')
                continue
            a = assessed.get(('extraction', source.source_id))
            if a is None:
                add('EXTRACTION_UNASSESSED', source.source_id, 'Non-text page/region extraction needs a current operator-authorized assessment.', 'REVIEW', 'BI_EXTRACTION')
            elif a.verdict == 'CONTRADICTED':
                add('EXTRACTION_CONTRADICTED', source.source_id, 'Authorized extraction assessor reports a mismatch.', owner='BI_EXTRACTION')
            elif a.verdict != 'VERIFIED' or a.confidence_ppm < policy.minimum_extraction_confidence_ppm:
                add('EXTRACTION_REVIEW_REQUIRED', source.source_id, 'Extraction is uncertain or below the operator confidence floor.', 'REVIEW', 'BI_EXTRACTION')
            else:
                valid_sources.add(source.source_id)
        # Never ignore a contradictory/uncertain extraction assessment for text
        # merely because the direct byte comparison succeeded.
        a = assessed.get(('extraction', source.source_id))
        if source.media_type == 'utf8' and a is not None:
            if a.verdict == 'CONTRADICTED':
                add('EXTRACTION_CONTRADICTED', source.source_id, 'Direct equality does not suppress a reported extraction contradiction.')
                valid_sources.discard(source.source_id)
            elif a.verdict != 'VERIFIED' or a.confidence_ppm < policy.minimum_extraction_confidence_ppm:
                add('EXTRACTION_REVIEW_REQUIRED', source.source_id, 'A supplied extraction assessment remains unresolved.', 'REVIEW', 'BI_EXTRACTION')
                valid_sources.discard(source.source_id)

    valid_blocks: set[str] = set()
    seen_regions: set[tuple[str, int, str]] = set()
    for b in request.blocks:
        source = sources.get(b.source_id)
        if source is None or b.source_sha256 != source.artifact.sha256:
            add('BLOCK_SOURCE_MISMATCH', b.block_id, 'Block source ID or hash does not match the declared source.')
            continue
        if b.page > source.page_count:
            add('BLOCK_PAGE_OUT_OF_RANGE', b.block_id, 'Block page is outside the source page inventory.')
            continue
        key = (b.source_id, b.page, b.region_id)
        if key in seen_regions:
            add('DUPLICATE_SOURCE_REGION', b.block_id, 'A source region cannot have competing block identities.')
            continue
        seen_regions.add(key)
        if b.confidence_ppm < policy.minimum_extraction_confidence_ppm:
            add('LOW_EXTRACTION_CONFIDENCE', b.block_id, 'Block extraction confidence is below the operator floor.', 'REVIEW', 'BI_EXTRACTION')
        if b.source_id in valid_sources:
            valid_blocks.add(b.block_id)

    # Valid structural references are tracked separately from extraction trust.
    # This lets the report locate the exact gap without making up missing text.
    resolved_citations: set[str] = set()
    for c in request.citations:
        b = blocks.get(c.block_id)
        if b is None or c.block_digest != b.content_digest:
            add('CITATION_BLOCK_MISMATCH', c.citation_id, 'Citation points to a missing or differently versioned block.', owner='BI_PROVENANCE')
            continue
        if c.end > len(b.text) or b.text[c.start:c.end] != c.quote:
            add('CITATION_QUOTE_MISMATCH', c.citation_id, 'Citation quotation is not the exact declared source span.', owner='BI_PROVENANCE')
            continue
        if not _whole_boundaries(b.text, c.start, c.end):
            add('CITATION_SPLITS_TOKEN', c.citation_id, 'Citation boundaries split a lexical token.', owner='BI_PROVENANCE')
            continue
        resolved_citations.add(c.citation_id)

    decoded_outputs: dict[str, str] = {}
    for o in request.outputs:
        payload = raw.get(o.artifact.artifact_id)
        if payload is None:
            continue
        try:
            value = payload.decode('utf-8', errors='strict')
            text(value, 'output.text')
        except (UnicodeError, ContractError):
            add('INVALID_OUTPUT_UTF8', o.output_id, 'Output must be nonempty valid bounded UTF-8 text.', owner='QA_OUTPUT')
            continue
        decoded_outputs[o.output_id] = value

    valid_claims: set[str] = set()
    cited_claims: set[str] = set()
    spans: dict[str, list] = {o: [] for o in outputs}
    cited_spans: dict[str, list] = {o: [] for o in outputs}
    used: set[str] = set()
    for c in request.claims:
        o = outputs.get(c.output_id)
        value = decoded_outputs.get(c.output_id)
        if o is None or c.output_sha256 != o.artifact.sha256:
            add('CLAIM_OUTPUT_MISMATCH', c.claim_id, 'Claim does not bind the exact output artifact revision.', owner='KI_CLAIMS')
            continue
        if value is None:
            continue
        if c.end > len(value) or value[c.start:c.end] != c.text:
            add('CLAIM_TEXT_MISMATCH', c.claim_id, 'Claim text is not the exact declared output span.', owner='KI_CLAIMS')
            continue
        if not _whole_boundaries(value, c.start, c.end):
            add('CLAIM_SPLITS_TOKEN', c.claim_id, 'Claim boundaries split a lexical token.', owner='KI_CLAIMS')
            continue
        valid_claims.add(c.claim_id)
        spans[c.output_id].append((c.start, c.end))
        used.update(c.citation_ids)
        if not c.citation_ids or any(e not in resolved_citations for e in c.citation_ids):
            add('CLAIM_CITATION_UNRESOLVED', c.claim_id, 'Every declared citation must resolve; a valid citation does not hide a broken or missing one.', owner='KI_CLAIMS')
        else:
            cited_claims.add(c.claim_id)
            cited_spans[c.output_id].append((c.start, c.end))

    for eid in sorted(set(citations) - used):
        add('UNASSIGNED_CITATION', eid, 'Citation is not assigned to a valid output claim.', 'REVIEW', 'BI_PROVENANCE')
    used_blocks = {citations[e].block_id for e in used if e in citations}
    for b in request.blocks:
        if b.block_id not in used_blocks:
            add('UNUSED_SOURCE_BLOCK', b.block_id, 'Source block is retained as context but not cited.', 'INFO', 'BI_PROVENANCE')

    total = covered = cited = 0
    for oid, value in decoded_outputs.items():
        n = sum(not c.isspace() for c in value)
        ncovered = _covered_nonspace(value, spans[oid])
        ncited = _covered_nonspace(value, cited_spans[oid])
        total += n; covered += ncovered; cited += ncited
        if ncovered != n:
            add('UNCLASSIFIED_OUTPUT_CONTENT', oid, f'{n-ncovered} non-whitespace code points have no valid claim span.', owner='KI_CLAIMS')
        if ncited != n:
            add('UNCITED_OUTPUT_CONTENT', oid, f'{n-ncited} non-whitespace code points lack resolved citation coverage.', owner='KI_CLAIMS')

    exact = supported = nonfactual = 0
    for c in request.claims:
        if c.claim_id not in valid_claims or c.claim_id not in cited_claims:
            sem('GROUNDING_INPUT_INVALID', c.claim_id, 'Contextual support cannot be credited for invalid output or citation spans.', 'BLOCKER')
            continue
        if any(c.text == citations[e].quote for e in c.citation_ids):
            exact += 1
            sem('EXACT_SOURCE_TEXT_OBSERVED', c.claim_id, 'Exact text fidelity observed; contextual support remains a separate assessment.', 'INFO')
        purpose = 'semantic' if c.kind == 'FACT' else 'nonfactual'
        a = assessed.get((purpose, c.claim_id))
        if a is None:
            sem('SEMANTIC_SUPPORT_UNASSESSED' if purpose == 'semantic' else 'NONFACT_LABEL_UNASSESSED', c.claim_id,
                'Current operator-authorized contextual assessment is absent. A kind label or quotation cannot bypass this check.')
        elif a.verdict == 'CONTRADICTED':
            sem('ASSESSOR_REPORTED_CONTRADICTION', c.claim_id, 'Authorized assessor reports contradiction or hidden factual content.', 'BLOCKER')
        elif a.verdict not in ('SUPPORTED', 'NO_FACTUAL_ASSERTION') or a.confidence_ppm < policy.minimum_confidence_ppm:
            sem('CONTEXTUAL_ASSESSMENT_REVIEW', c.claim_id, 'Contextual assessment is uncertain or below the operator confidence floor.')
        elif any(citations[e].block_id not in valid_blocks for e in c.citation_ids):
            sem('SUPPORT_SOURCE_UNVERIFIED', c.claim_id, 'A contextual assessment cannot replace unresolved source extraction evidence.')
        else:
            if purpose == 'semantic': supported += 1
            else: nonfactual += 1
            sem('AUTHORIZED_ASSESSMENT_RECORDED', c.claim_id, 'A current, bound operator-authorized assessment reports support; evaluator calibration is a separate obligation.', 'INFO')

    metrics = (('source_artifacts', len(request.sources)), ('source_artifacts_verified', len(valid_sources)),
               ('outputs_expected', len(policy.expected_output_ids)), ('outputs_read', len(decoded_outputs)),
               ('claims', len(request.claims)), ('claims_with_resolved_citations', len(cited_claims)),
               ('citations', len(request.citations)), ('citations_resolved', len(resolved_citations)),
               ('nonspace_codepoints', total), ('classified_codepoints', covered), ('cited_codepoints', cited))
    evidence_digest = digest({'assessments': [asdict(a) for a in sorted(assessments, key=lambda a: a.assessment_id)],
                              'trust_configuration': verifier.configuration_digest})
    def report(task, findings, measurements):
        ordered = tuple(sorted(set(findings), key=lambda f: (f.subject_id, f.code, f.severity, f.owner, f.detail)))
        return Report(task, request_digest, policy_digest, evidence_digest, as_of,
                      ordered, tuple(sorted(measurements)), tuple(sorted(raw)), LIMITATIONS)
    return EvaluationPair(
        report('BIE-QA-SOURCE-002', prov, metrics),
        report('BIE-QA-SOURCE-001', prov + semantic, metrics +
               (('exact_source_text_matches', exact), ('authorized_supported_claims', supported),
                ('authorized_nonfactual_claims', nonfactual))))


def evaluate_provenance(*args, **kwargs) -> Report:
    return evaluate(*args, **kwargs).provenance


def evaluate_grounding(*args, **kwargs) -> Report:
    return evaluate(*args, **kwargs).grounding


def verify_reports(actual: EvaluationPair, *args, **kwargs) -> EvaluationPair:
    """Recompute from actual bytes and policy, rejecting edited or stale reports."""
    expected = evaluate(*args, **kwargs)
    if type(actual) is not EvaluationPair or actual != expected:
        raise ContractError('STALE_OR_EDITED_SOURCE_REPORT')
    return actual
