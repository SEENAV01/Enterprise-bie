"""BIE-DIR-QA-002: real byte hashes, extracted page/quote and citation coverage.

The UTF-8 text adapter proves extraction equality. PDF extraction accuracy needs
upstream BI evidence; hashing supplied PDF bytes is not an OCR verification.
"""
from dataclasses import dataclass
import hashlib
from .qa_contract import (Finding, validate_claims, validate_catalog, coverage,
                          report, verify_report)
from .timing_contract import nonblank, identifiers


@dataclass(frozen=True)
class SourceBytes:
    source_id: str
    data: bytes
    media_type: str


def source_grounding_qa(snapshot, claims, catalog, artifacts=(), policy_version="bie-dir-grounding/1.0.0"):
    index = validate_claims(snapshot, claims)
    pages, passages = validate_catalog(catalog)
    if type(artifacts) is not tuple or any(not isinstance(a, SourceBytes) for a in artifacts):
        raise ValueError("artifacts must be a tuple of SourceBytes")
    identifiers(tuple(a.source_id for a in artifacts), "artifacts", allow_empty=True)
    available, receipts, findings = {}, [], []
    for a in artifacts:
        if type(a.data) is not bytes or not a.data:
            raise ValueError("source artifact must contain nonempty actual bytes")
        nonblank(a.media_type, "media type")
        sha = "sha256:" + hashlib.sha256(a.data).hexdigest()
        available[a.source_id] = (a, sha)
        receipts.append((a.source_id, a.media_type, sha, len(a.data)))
    checked_sources = set()
    for p in catalog.pages:
        if p.source_id not in available:
            findings.append(Finding("SOURCE_BYTES_MISSING", "BLOCKER", p.page_id,
                "Actual source bytes are unavailable for hash verification.", "BI_SOURCE"))
            continue
        a, sha = available[p.source_id]
        checked_sources.add(p.source_id)
        if sha != p.source_sha256:
            findings.append(Finding("SOURCE_HASH_MISMATCH", "BLOCKER", p.page_id,
                "Supplied source bytes differ from extraction lineage.", "BI_SOURCE"))
            continue
        if a.media_type == "text/plain; charset=utf-8":
            try:
                text = a.data.decode("utf-8")
            except UnicodeDecodeError:
                text = None
            if p.page_number != 1 or text != p.text:
                findings.append(Finding("TEXT_EXTRACTION_MISMATCH", "BLOCKER", p.page_id,
                    "UTF-8 adapter requires one page equal to the complete source text.", "BI_EXTRACTION"))
        else:
            findings.append(Finding("EXTRACTION_ACCURACY_UNVERIFIED", "REVIEW", p.page_id,
                "Byte hash checked; page text/region semantics still require upstream extraction QA.", "BI_EXTRACTION"))
    for c in claims:
        u = index[c.span.utterance_id]
        missing = tuple(e for e in c.evidence_ids if e not in passages)
        if not c.evidence_ids or missing:
            findings.append(Finding("CITATION_UNRESOLVED", "BLOCKER", c.claim_id,
                "Every classified span needs source context; one valid citation cannot hide another missing citation.",
                "SCRIPT_GROUNDING", c.span, missing))
        if not set(c.evidence_ids) <= set(u.evidence_ids):
            findings.append(Finding("EVIDENCE_OUTSIDE_SCRIPT", "BLOCKER", c.claim_id,
                "Claim citations do not belong to this realized script segment.", "SCRIPT_GROUNDING", c.span, c.evidence_ids))
    used = {e for c in claims for e in c.evidence_ids}
    for u in snapshot.utterances:
        unresolved = tuple(e for e in u.evidence_ids if e not in passages)
        if unresolved:
            findings.append(Finding("DRAFT_CITATION_UNRESOLVED", "BLOCKER", u.utterance_id,
                "Realized draft includes unresolved source references.", "SCRIPT_GROUNDING", evidence_ids=unresolved))
        unused = tuple(e for e in u.evidence_ids if not any(c.span.utterance_id == u.utterance_id and e in c.evidence_ids for c in claims))
        if unused:
            findings.append(Finding("UNASSIGNED_DRAFT_CITATION", "REVIEW", u.utterance_id,
                "Draft reference has no declared claim span.", "SCRIPT_GROUNDING", evidence_ids=unused))
    cov = coverage(snapshot, claims)
    for uid, covered, total in cov:
        if covered != total:
            findings.append(Finding("GROUNDING_COVERAGE_GAP", "BLOCKER", uid,
                f"{total-covered} spoken words lack declared grounding spans.", "SCRIPT_GROUNDING"))
    for source_id in sorted(set(available) - {p.source_id for p in pages.values()}):
        findings.append(Finding("UNUSED_SOURCE_ARTIFACT", "INFO", source_id,
            "Supplied artifact is outside this extraction catalog.", "BI_SOURCE"))
    return report("BIE-DIR-QA-002", snapshot, (claims, catalog, tuple(receipts), policy_version),
        policy_version, findings, (("source_artifacts_checked", len(checked_sources)),
            ("cited_passages", len(used)), ("covered_words", sum(c[1] for c in cov)),
            ("total_words", sum(c[2] for c in cov))),
        "Source-byte lineage, exact extracted spans and declared narration citation coverage",
        ("Grounding does not prove that a citation entails the claim; QA-001 remains separate.",
         "Non-text extraction, page numbering and region semantics require upstream BI verification.",
         "No real-book or product acceptance is implied."))


def validate_grounding_report(actual, *args, **kwargs):
    return verify_report(actual, source_grounding_qa(*args, **kwargs))
