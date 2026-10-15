"""Original BIE-DIR-QA-001 shared contracts; deterministic, scoped QA evidence.

These APIs are new implementation choices under the original roadmap titles.
Source extraction is an upstream BI artifact, not proof of PDF/OCR accuracy.
"""
from dataclasses import dataclass, fields, is_dataclass
import re
from .timing_contract import (fingerprint, nonblank, integer, number,
                              identifiers, digest_id, spoken_words)
from .speech_timing import SpeechUtterance, utterances_from_script
from .script_plan import ScriptPlan
from .voiceover_generation import VoiceoverDraft


def immutable(value):
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        number(value, "finite immutable number", low=-1e308)
    elif type(value) is tuple:
        for item in value:
            immutable(item)
    elif is_dataclass(value) and value.__dataclass_params__.frozen:
        for field in fields(value):
            immutable(getattr(value, field.name))
    else:
        raise ValueError("QA inputs must be frozen dataclasses and immutable tuples")


def rows(items, cls, name, key=None):
    if type(items) is not tuple or any(not isinstance(x, cls) for x in items):
        raise ValueError(f"{name} must be a tuple of {cls.__name__}")
    immutable(items)
    if key:
        identifiers(tuple(getattr(x, key) for x in items), name, allow_empty=True)
    return items


@dataclass(frozen=True)
class ScriptSnapshot:
    script: ScriptPlan
    drafts: tuple[VoiceoverDraft, ...]
    segment_order: tuple[str, ...]
    language: str
    utterances: tuple[SpeechUtterance, ...]

    def fingerprint(self):
        return fingerprint(self)


def snapshot_script(script, drafts, segment_order, language="en"):
    if not isinstance(script, ScriptPlan):
        raise ValueError("expected original ScriptPlan")
    immutable(script)
    rows(drafts, VoiceoverDraft, "drafts", "segment_id")
    if type(segment_order) is not tuple:
        raise ValueError("segment order must be an immutable tuple")
    utterances = utterances_from_script(script, drafts, segment_order, language)
    return ScriptSnapshot(script, drafts, segment_order, language, utterances)


def validate_snapshot(snapshot):
    if not isinstance(snapshot, ScriptSnapshot):
        raise ValueError("expected ScriptSnapshot")
    immutable(snapshot)
    expected = snapshot_script(snapshot.script, snapshot.drafts,
                               snapshot.segment_order, snapshot.language)
    if expected != snapshot:
        raise ValueError("stale or modified script snapshot")
    return {u.utterance_id: u for u in snapshot.utterances}


@dataclass(frozen=True)
class TextSpan:
    utterance_id: str
    start_char: int
    end_char: int
    utterance_fingerprint: str


def bind_span(snapshot, utterance_id, start_char=0, end_char=None):
    index = validate_snapshot(snapshot)
    if utterance_id not in index:
        raise ValueError("unknown utterance")
    u = index[utterance_id]
    span = TextSpan(utterance_id, start_char, len(u.text) if end_char is None else end_char,
                    u.fingerprint())
    span_text(index, span)
    return span


def span_text(index, span):
    if not isinstance(span, TextSpan) or span.utterance_id not in index:
        raise ValueError("unknown or invalid text span")
    integer(span.start_char, "span start")
    integer(span.end_char, "span end", 1)
    u = index[span.utterance_id]
    if span.utterance_fingerprint != u.fingerprint():
        raise ValueError("span is bound to another narration revision")
    if span.start_char >= span.end_char or span.end_char > len(u.text):
        raise ValueError("span outside narration")
    # Partial lexical tokens are not valid coverage of those tokens.
    for w in spoken_words(u.text):
        if w.start_char < span.start_char < w.end_char or w.start_char < span.end_char < w.end_char:
            raise ValueError("span splits a spoken word")
    return nonblank(u.text[span.start_char:span.end_char], "span text")


def sentence_spans(snapshot):
    """Conservative sentence spans; decimal points do not split sentences.

    Abbreviations and punctuation in other languages need downstream review.
    This helper never loses trailing text without sentence punctuation.
    """
    out = []
    for u in snapshot.utterances:
        start = 0
        for m in re.finditer(r"[.!?](?=\s|$)|\n+|$", u.text):
            end = m.end()
            a, b = start, end
            while a < b and u.text[a].isspace():
                a += 1
            while b > a and u.text[b-1].isspace():
                b -= 1
            if a < b:
                out.append(TextSpan(u.utterance_id, a, b, u.fingerprint()))
            start = end
    return tuple(out)


@dataclass(frozen=True)
class ScriptClaim:
    claim_id: str
    span: TextSpan
    kind: str  # FACT, QUESTION, INSTRUCTION, OTHER; labels never imply entailment
    evidence_ids: tuple[str, ...]


def validate_claims(snapshot, claims):
    index = validate_snapshot(snapshot)
    rows(claims, ScriptClaim, "claims", "claim_id")
    for c in claims:
        span_text(index, c.span)
        if c.kind not in ("FACT", "QUESTION", "INSTRUCTION", "OTHER"):
            raise ValueError("unsupported claim kind")
        identifiers(c.evidence_ids, "claim evidence", allow_empty=True)
    return index


@dataclass(frozen=True)
class SourcePage:
    page_id: str
    source_id: str
    source_sha256: str
    page_number: int
    text: str
    extractor_version: str

    def fingerprint(self):
        return fingerprint(self)


@dataclass(frozen=True)
class SourcePassage:
    evidence_id: str
    page_id: str
    page_fingerprint: str
    region_id: str
    start_char: int
    end_char: int
    quote: str

    def fingerprint(self):
        return fingerprint(self)


@dataclass(frozen=True)
class SourceCatalog:
    pages: tuple[SourcePage, ...]
    passages: tuple[SourcePassage, ...]

    def fingerprint(self):
        return fingerprint(self)


def validate_catalog(catalog):
    if not isinstance(catalog, SourceCatalog):
        raise ValueError("expected SourceCatalog")
    rows(catalog.pages, SourcePage, "pages", "page_id")
    rows(catalog.passages, SourcePassage, "passages", "evidence_id")
    pages, source_hashes, locations = {}, {}, set()
    for p in catalog.pages:
        for name in ("source_id", "text", "extractor_version"):
            nonblank(getattr(p, name), name)
        digest_id(p.source_sha256, "source hash")
        integer(p.page_number, "page number", 1)
        if (p.source_id, p.page_number) in locations:
            raise ValueError("duplicate source page")
        locations.add((p.source_id, p.page_number))
        if p.source_id in source_hashes and source_hashes[p.source_id] != p.source_sha256:
            raise ValueError("mixed source revisions")
        source_hashes[p.source_id] = p.source_sha256
        pages[p.page_id] = p
    for e in catalog.passages:
        nonblank(e.region_id, "region id")
        nonblank(e.quote, "source quote")
        integer(e.start_char, "source start")
        integer(e.end_char, "source end", 1)
        p = pages.get(e.page_id)
        if p is None or e.page_fingerprint != p.fingerprint():
            raise ValueError("missing or stale source page")
        if not 0 <= e.start_char < e.end_char <= len(p.text) or p.text[e.start_char:e.end_char] != e.quote:
            raise ValueError("source quote does not match exact page span")
    return pages, {p.evidence_id: p for p in catalog.passages}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    subject_id: str
    detail: str
    repair_stage: str
    span: TextSpan | None = None
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class QAReport:
    task_id: str
    snapshot_fingerprint: str
    inputs_fingerprint: str
    policy_version: str
    findings: tuple[Finding, ...]
    measurements: tuple[tuple[str, int | float | str], ...]
    scope: str
    limitations: tuple[str, ...]

    @property
    def status(self):
        if any(f.severity == "BLOCKER" for f in self.findings):
            return "BLOCKED"
        if any(f.severity == "REVIEW" for f in self.findings):
            return "REVIEW_REQUIRED"
        return "CHECKS_PASSED"

    @property
    def accepted(self):
        return False

    @property
    def requires_review(self):
        return self.status != "CHECKS_PASSED"

    def fingerprint(self):
        return fingerprint(self)


@dataclass(frozen=True)
class _QAInputs:
    values: tuple


def report(task_id, snapshot, inputs, policy_version, findings, measurements, scope, limitations):
    validate_snapshot(snapshot)
    immutable(inputs)
    nonblank(policy_version, "policy version")
    out = list(findings)
    for u in snapshot.utterances:
        for reason in u.review_reasons:
            out.append(Finding(reason, "REVIEW", u.utterance_id,
                               "Upstream script review remains unresolved.", "SCRIPT"))
    for f in out:
        if f.severity not in ("BLOCKER", "REVIEW", "INFO"):
            raise ValueError("unknown finding severity")
        for value in (f.code, f.subject_id, f.detail, f.repair_stage):
            nonblank(value, "finding field")
    return QAReport(task_id, snapshot.fingerprint(), fingerprint(_QAInputs(inputs)), policy_version,
                    tuple(out), tuple(measurements), scope, tuple(limitations))


def coverage(snapshot, claims):
    """Union of whole spoken-word spans. Overlap cannot inflate coverage."""
    counts = []
    for u in snapshot.utterances:
        words = spoken_words(u.text)
        spans = [c.span for c in claims if c.span.utterance_id == u.utterance_id]
        covered = sum(any(s.start_char <= w.start_char and s.end_char >= w.end_char
                          for s in spans) for w in words)
        counts.append((u.utterance_id, covered, len(words)))
    return tuple(counts)


def verify_report(actual, expected):
    if not isinstance(actual, QAReport) or actual != expected:
        raise ValueError("stale, edited or differently scoped QA report")
    return actual
