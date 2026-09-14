"""BIE-DIR-QA-001: claim coverage, exact source fidelity and semantic receipts.

Exact quote equality does not prove contextual entailment or world truth.
Paraphrases require an explicit, revision-bound evaluator receipt; matching
keywords or merely possessing citation IDs cannot pass this gate.
"""
from dataclasses import dataclass
import re
from .qa_contract import (ScriptClaim, TextSpan, Finding, rows, validate_claims,
    validate_catalog, span_text, coverage, report, verify_report)
from .timing_contract import fingerprint, identifiers, number, nonblank


@dataclass(frozen=True)
class SemanticReceipt:
    claim_id: str
    claim_fingerprint: str
    passage_fingerprints: tuple[str, ...]
    verdict: str  # SUPPORTED, CONTRADICTED, UNCERTAIN
    evaluator: str
    evaluator_version: str
    confidence: float
    rationale: str


@dataclass(frozen=True)
class FactualPolicy:
    version: str = "bie-dir-factual/1.0.0"
    trusted_evaluators: tuple[str, ...] = ()  # exact evaluator@version
    minimum_confidence: float = 0.9


def normalized(text):
    return " ".join(text.casefold().split())


def factual_qa(snapshot, claims, catalog, receipts=(), policy=FactualPolicy()):
    index = validate_claims(snapshot, claims)
    _, passages = validate_catalog(catalog)
    rows(receipts, SemanticReceipt, "semantic receipts", "claim_id")
    if not isinstance(policy, FactualPolicy):
        raise ValueError("expected FactualPolicy")
    identifiers(policy.trusted_evaluators, "trusted evaluators", allow_empty=True)
    number(policy.minimum_confidence, "minimum confidence", 0, 1)
    by_claim = {c.claim_id: c for c in claims}
    by_receipt = {}
    for r in receipts:
        for name in ("evaluator", "evaluator_version", "rationale"):
            nonblank(getattr(r, name), name)
        number(r.confidence, "receipt confidence", 0, 1)
        if r.verdict not in ("SUPPORTED", "CONTRADICTED", "UNCERTAIN"):
            raise ValueError("invalid semantic verdict")
        c = by_claim.get(r.claim_id)
        if c is None or c.kind != "FACT" or r.claim_fingerprint != fingerprint(c):
            raise ValueError("stale or extraneous semantic receipt")
        expected = tuple(passages[e].fingerprint() for e in c.evidence_ids if e in passages)
        if len(expected) != len(c.evidence_ids) or r.passage_fingerprints != expected:
            raise ValueError("semantic receipt does not cover exact cited source revision/order")
        by_receipt[r.claim_id] = r
    findings, exact, supported = [], 0, 0
    for c in claims:
        def add(code, severity, detail):
            findings.append(Finding(code, severity, c.claim_id, detail, "SCRIPT_FACTUAL",
                                    c.span, c.evidence_ids))
        text = span_text(index, c.span)
        u = index[c.span.utterance_id]
        if not set(c.evidence_ids) <= set(u.evidence_ids):
            add("EVIDENCE_OUTSIDE_SCRIPT", "BLOCKER", "Claim citation is outside realized script lineage.")
        if c.kind != "FACT":
            add("NONFACT_LABEL_REQUIRES_REVIEW", "REVIEW",
                "An instruction/question label does not exclude implicit factual assertions.")
            continue
        if not c.evidence_ids or any(e not in passages for e in c.evidence_ids):
            add("MISSING_FACTUAL_EVIDENCE", "BLOCKER", "Every fact needs resolvable source passages.")
            continue
        quotes = [passages[e].quote for e in c.evidence_ids]
        is_exact = any(normalized(text) == normalized(q) for q in quotes)
        if is_exact:
            exact += 1
            add("EXACT_SOURCE_TEXT", "INFO", "Exact text fidelity observed; contextual truth is a separate check.")
        skeleton = lambda x: re.sub(r"\d+(?:[.,]\d+)*", "#", normalized(x))
        mismatches = [q for q in quotes if skeleton(text) == skeleton(q) and
                      re.findall(r"\d+(?:[.,]\d+)*", text) != re.findall(r"\d+(?:[.,]\d+)*", q)]
        if mismatches:
            add("SOURCE_NUMERIC_CONFLICT", "BLOCKER",
                "Otherwise identical source wording contains different numeric values; reconcile context/revisions.")
        r = by_receipt.get(c.claim_id)
        if r is None:
            add("SEMANTIC_SUPPORT_UNASSESSED", "REVIEW",
                "Contextual entailment is unassessed, including for exact quotations.")
        elif r.verdict == "CONTRADICTED":
            add("REPORTED_CONTRADICTION", "BLOCKER", "Supplied evaluator reports contradiction: " + r.rationale)
        elif (r.verdict != "SUPPORTED" or r.confidence < policy.minimum_confidence or
              r.evaluator + "@" + r.evaluator_version not in policy.trusted_evaluators):
            add("SEMANTIC_RECEIPT_REVIEW", "REVIEW", "Receipt is uncertain, below threshold or outside explicit evaluator policy.")
        else:
            supported += 1
            add("REPORTED_SUPPORT", "INFO", "Support reported by policy-listed evaluator: " + r.rationale)
    cov = coverage(snapshot, claims)
    for uid, covered, total in cov:
        if covered < total:
            findings.append(Finding("UNCLASSIFIED_NARRATION", "BLOCKER", uid,
                f"{total-covered} of {total} spoken words lack a claim span.", "SCRIPT_FACTUAL"))
    return report("BIE-DIR-QA-001", snapshot, (claims, catalog, receipts, policy), policy.version,
        findings, (("claims", len(claims)), ("exact_source_matches", exact),
                   ("reported_supported_facts", supported),
                   ("covered_words", sum(c[1] for c in cov)), ("total_words", sum(c[2] for c in cov))),
        "Declared claim coverage, source text fidelity and reported contextual support",
        ("Source bytes/extraction integrity belongs to QA-002 and upstream BI.",
         "Receipts are caller-supplied evidence, not authenticated signatures or independently rerun models.",
         "No independent world-truth, mathematical proof, real-book benchmark or product acceptance."))


def validate_factual_report(actual, *args, **kwargs):
    return verify_report(actual, factual_qa(*args, **kwargs))
