"""BIE-DIR-QA-004: conservative duplicate candidates; retain purposeful practice.

No content is deleted. Similarity is an engineering heuristic, not a validated
semantic equivalence model. Numbers and polarity survive normalization.
"""
from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from .qa_contract import (TextSpan, Finding, rows, validate_snapshot, span_text,
                          report, verify_report, sentence_spans)
from .timing_contract import integer, number, nonblank, identifiers
from ..pedagogy.repetition_policy import RepetitionDecision


@dataclass(frozen=True)
class RepetitionPolicy:
    version: str = "bie-dir-repetition/1.0.0"
    minimum_words: int = 5
    near_duplicate_threshold: float = 0.85


@dataclass(frozen=True)
class RepeatPurpose:
    first: TextSpan
    repeated: TextSpan
    mode: str  # RECAP, RETRIEVAL, MISCONCEPTION_RECHECK, PRACTICE
    reason: str
    evidence_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    pedagogy_decision: RepetitionDecision | None = None


def tokens(text):
    return tuple(re.findall(r"\d+(?:[.,]\d+)*|[^\W_]+(?:['’][^\W_]+)*|[+\-−*/%=<>$€£₹¥]", text.casefold()))


def repetition_qa(snapshot, purposes=(), policy=RepetitionPolicy()):
    index = validate_snapshot(snapshot)
    rows(purposes, RepeatPurpose, "repeat purposes")
    if not isinstance(policy, RepetitionPolicy):
        raise ValueError("expected RepetitionPolicy")
    integer(policy.minimum_words, "minimum words", 2)
    number(policy.near_duplicate_threshold, "similarity threshold", 0.5, 1)
    sentences = sentence_spans(snapshot)
    positions = {s: i for i, s in enumerate(sentences)}
    annotations = {}
    for p in purposes:
        span_text(index, p.first)
        span_text(index, p.repeated)
        if p.first not in positions or p.repeated not in positions or positions[p.first] >= positions[p.repeated]:
            raise ValueError("repeat purpose must bind two ordered complete sentence spans")
        if (p.first, p.repeated) in annotations:
            raise ValueError("duplicate repeat purpose")
        if p.mode not in ("RECAP", "RETRIEVAL", "MISCONCEPTION_RECHECK", "PRACTICE"):
            raise ValueError("unknown repetition purpose")
        nonblank(p.reason, "repeat rationale")
        identifiers(p.evidence_ids, "repeat evidence")
        identifiers(p.objective_ids, "repeat objectives")
        a, b = index[p.first.utterance_id], index[p.repeated.utterance_id]
        if not set(p.evidence_ids) <= set(a.evidence_ids) & set(b.evidence_ids) or not set(p.objective_ids) <= set(a.objective_ids) & set(b.objective_ids):
            raise ValueError("repeat purpose is outside shared script lineage")
        if p.pedagogy_decision is not None:
            d = p.pedagogy_decision
            if not isinstance(d, RepetitionDecision) or type(d.repeat) is not bool:
                raise ValueError("expected original RepetitionDecision")
            integer(d.interval_units, "repetition interval", 1)
            nonblank(d.reason, "pedagogy rationale")
            if d.mode not in ("TARGETED", "SPACED", "RETRIEVAL_ONLY"):
                raise ValueError("unknown pedagogy repeat mode")
        annotations[p.first, p.repeated] = p
    findings, candidates, intentional, used = [], 0, 0, set()
    if snapshot.language.split("-")[0].lower() != "en":
        findings.append(Finding("LANGUAGE_SIMILARITY_UNCALIBRATED", "REVIEW", snapshot.script.lesson_id,
            "Token/sentence similarity is uncalibrated for this language.", "DIR_REPETITION"))
    sequences = [tokens(span_text(index, s)) for s in sentences]
    for j, second in enumerate(sentences):
        for i in range(j):
            first, a, b = sentences[i], sequences[i], sequences[j]
            if min(len(a), len(b)) < policy.minimum_words:
                continue
            similarity = SequenceMatcher(None, a, b, autojunk=False).ratio()
            if similarity < policy.near_duplicate_threshold:
                continue
            candidates += 1
            text = span_text(index, second)
            p = annotations.get((first, second))
            if p:
                used.add((first, second))
            def add(code, severity, detail):
                findings.append(Finding(code, severity, second.utterance_id, detail +
                    f" First span: {first.utterance_id}[{first.start_char}:{first.end_char}]; similarity={similarity:.4f}.",
                    "DIR_REPETITION", second, p.evidence_ids if p else ()))
            numbers = lambda seq: tuple(t for t in seq if any(c.isdigit() for c in t))
            polarity = lambda seq: tuple(t for t in seq if t in ("not", "never", "no", "cannot") or t.endswith(("n't", "n’t")))
            symbols = lambda seq: tuple(t for t in seq if t in ("+", "-", "−", "*", "/", "%", "=", "<", ">", "$", "€", "£", "₹", "¥"))
            if numbers(a) != numbers(b) or polarity(a) != polarity(b) or symbols(a) != symbols(b):
                add("REPEATED_TEXT_FACTUAL_DIFFERENCE", "REVIEW", "Near copy changes values, polarity or operators; check factual context before deduplication")
                continue
            if p is None:
                add("EXACT_REPETITION" if a == b else "NEAR_REPETITION", "REVIEW", "Candidate needs pedagogical purpose review; preserve content until resolved")
                continue
            d = p.pedagogy_decision
            if d and (not d.repeat or (d.mode == "RETRIEVAL_ONLY" and p.mode != "RETRIEVAL")):
                add("PEDAGOGY_REPEAT_CONFLICT", "REVIEW", "Repeat purpose conflicts with supplied pedagogy decision")
                continue
            retrieval = text.rstrip().endswith("?") or text.casefold().startswith(("recall ", "explain ", "state ", "solve ", "try "))
            if p.mode in ("RETRIEVAL", "MISCONCEPTION_RECHECK", "PRACTICE") and not retrieval:
                add("ACTIVE_PRACTICE_NOT_DEMONSTRATED", "REVIEW", "Declared practice needs an active prompt, not an identical repeated exposition")
                continue
            intentional += 1
            add("PURPOSEFUL_REPETITION_RETAINED", "INFO", p.mode + ": " + p.reason)
            if a != b:
                add("NEAR_REPEAT_SEMANTICS_REVIEW", "REVIEW", "Purpose is retained, but changed wording/units still need semantic review")
    for key, p in annotations.items():
        if key not in used:
            findings.append(Finding("REPEAT_PURPOSE_OUTSIDE_CANDIDATES", "INFO", p.repeated.utterance_id,
                "Purpose retained but this policy did not classify the pair as duplicate candidates.", "DIR_REPETITION", p.repeated))
    return report("BIE-DIR-QA-004", snapshot, (purposes, policy), policy.version, findings,
        (("sentences", len(sentences)), ("candidate_pairs", candidates), ("purposeful_pairs_retained", intentional)),
        "Exact and near sentence repetition candidates with revision-bound pedagogical exceptions",
        ("Thresholds and sentence/token boundaries are engineering heuristics, not empirical quality benchmarks.",
         "Semantic repetition and all factual differences cannot be exhaustively detected by lexical similarity.",
         "This module never deletes, rewrites or caps lesson content; no learner profile is required."))


def validate_repetition_report(actual, *args, **kwargs):
    return verify_report(actual, repetition_qa(*args, **kwargs))
