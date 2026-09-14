"""BIE-DIR-QA-005: optional curriculum target, scaffolding and declared advisories.

No learner questionnaire, grade prediction or scientific readability claim.
Target ages and level ranks are caller-declared curriculum policy, not laws.
"""
from dataclasses import dataclass
import re
from .qa_contract import (TextSpan, Finding, rows, immutable, validate_snapshot,
                          span_text, report, verify_report, sentence_spans)
from .timing_contract import nonblank, integer, identifiers, spoken_words
from .assessment_prompts import AssessmentPrompt

LEVELS = ("REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE")


@dataclass(frozen=True)
class AudienceTarget:
    minimum_age: int
    maximum_age: int
    level_rank: int
    allowed_assessment_levels: tuple[str, ...]
    curriculum_basis: str


@dataclass(frozen=True)
class TermRequirement:
    term: str
    minimum_level_rank: int
    evidence_ids: tuple[str, ...]
    definition: TextSpan | None = None


@dataclass(frozen=True)
class ContentAdvisory:
    advisory_id: str
    span: TextSpan
    category: str
    minimum_age: int
    rationale: str


@dataclass(frozen=True)
class AudiencePolicy:
    version: str = "bie-dir-audience/1.0.0"
    maximum_sentence_words: int = 30
    annotation_review_completed: bool = False


def age_level_qa(snapshot, target=None, terms=(), advisories=(), assessments=(), policy=AudiencePolicy()):
    index = validate_snapshot(snapshot)
    rows(terms, TermRequirement, "terms", "term")
    rows(advisories, ContentAdvisory, "advisories", "advisory_id")
    rows(assessments, AssessmentPrompt, "assessments")
    if not isinstance(policy, AudiencePolicy):
        raise ValueError("expected AudiencePolicy")
    integer(policy.maximum_sentence_words, "sentence word threshold", 1)
    if type(policy.annotation_review_completed) is not bool:
        raise ValueError("annotation review flag must be bool")
    if target is not None:
        if not isinstance(target, AudienceTarget):
            raise ValueError("expected AudienceTarget")
        immutable(target)
        integer(target.minimum_age, "minimum age")
        integer(target.maximum_age, "maximum age", target.minimum_age)
        integer(target.level_rank, "curriculum level")
        identifiers(target.allowed_assessment_levels, "allowed cognitive levels")
        if not set(target.allowed_assessment_levels) <= set(LEVELS):
            raise ValueError("unknown cognitive level")
        nonblank(target.curriculum_basis, "curriculum basis")
    findings = []
    def add(code, severity, subject, detail, span=None):
        findings.append(Finding(code, severity, subject, detail, "PED_AUDIENCE", span))
    if target is None:
        add("AUDIENCE_TARGET_UNSPECIFIED", "REVIEW", snapshot.script.lesson_id,
            "Optional curriculum audience is unspecified; source-driven generation can continue.")
    if not policy.annotation_review_completed:
        add("AUDIENCE_ANNOTATIONS_UNREVIEWED", "REVIEW", snapshot.script.lesson_id,
            "Term and content advisory completeness has not been declared reviewed.")
    english = snapshot.language.split("-")[0].lower() == "en"
    if not english:
        add("AUDIENCE_LANGUAGE_UNCALIBRATED", "REVIEW", snapshot.script.lesson_id,
            "Sentence length and lexical matching need language-appropriate review.")
    long_sentences = 0
    for span in sentence_spans(snapshot):
        text = span_text(index, span)
        # Sentence length is a warning only; never an inferred grade/age.
        if re.search(r"\w", text) and len(spoken_words(text)) > policy.maximum_sentence_words:
            long_sentences += 1
            add("SENTENCE_LOAD_REVIEW", "REVIEW", span.utterance_id,
                "Sentence exceeds declared word threshold; consider splitting or adding a scaffold.", span)
    order = {u.utterance_id: i for i, u in enumerate(snapshot.utterances)}
    if len({t.term.casefold() for t in terms}) != len(terms):
        raise ValueError("duplicate case-insensitive term rule")
    for t in terms:
        integer(t.minimum_level_rank, "term level")
        identifiers(t.evidence_ids, "term evidence")
        matches = [(u, m) for u in snapshot.utterances for m in re.finditer(
            r"(?<!\w)" + re.escape(t.term) + r"(?!\w)", u.text, re.IGNORECASE)]
        if not matches:
            raise ValueError("term rule does not occur in narration")
        for u, _ in matches:
            if not set(t.evidence_ids) <= set(u.evidence_ids):
                raise ValueError("term rule is outside script evidence")
        definition_position = None
        if t.definition is not None:
            definition_text = span_text(index, t.definition)
            if not re.search(r"(?<!\w)" + re.escape(t.term) + r"(?!\w)", definition_text, re.IGNORECASE):
                raise ValueError("definition span must explicitly name the term")
            if not set(t.evidence_ids) <= set(index[t.definition.utterance_id].evidence_ids):
                raise ValueError("definition has different evidence lineage")
            definition_position = (order[t.definition.utterance_id], t.definition.start_char)
        u, m = matches[0]
        first_position = (order[u.utterance_id], m.start())
        if target is not None and t.minimum_level_rank > target.level_rank:
            if definition_position is None or definition_position > first_position:
                add("ADVANCED_TERM_WITHOUT_PRIOR_SCAFFOLD", "REVIEW", u.utterance_id,
                    "Define or scaffold advanced term at/before first use: " + t.term)
            else:
                add("DECLARED_TERM_SCAFFOLD", "INFO", u.utterance_id,
                    "A revision-bound definition is supplied; its semantic quality remains a pedagogy check: " + t.term)
    for a in advisories:
        span_text(index, a.span)
        if a.category not in ("MATURE_THEME", "GRAPHIC_DETAIL", "HAZARDOUS_ACTIVITY"):
            raise ValueError("unsupported content advisory category")
        integer(a.minimum_age, "advisory age")
        nonblank(a.rationale, "advisory rationale")
        if target is not None and target.minimum_age < a.minimum_age:
            add("CONTENT_OUTSIDE_DECLARED_AGE_POLICY", "BLOCKER", a.advisory_id,
                "Declared content policy does not cover the youngest intended audience: " + a.rationale, a.span)
    objectives = {o for u in snapshot.utterances for o in u.objective_ids}
    evidence = {e for u in snapshot.utterances for e in u.evidence_ids}
    for a in assessments:
        nonblank(a.objective_id, "assessment objective")
        nonblank(a.prompt, "assessment prompt")
        nonblank(a.success_criterion, "assessment criterion")
        identifiers(a.evidence_ids, "assessment evidence")
        if a.level not in LEVELS:
            raise ValueError("unknown assessment level")
        if a.objective_id not in objectives or not set(a.evidence_ids) <= evidence:
            add("ASSESSMENT_OUTSIDE_SCRIPT_LINEAGE", "BLOCKER", a.objective_id,
                "Assessment objective/evidence is outside the realized script.")
        if target is not None and a.level not in target.allowed_assessment_levels:
            add("ASSESSMENT_OUTSIDE_CURRICULUM_POLICY", "REVIEW", a.objective_id,
                "Assessment operation is outside the explicitly declared curriculum policy: " + a.level)
    return report("BIE-DIR-QA-005", snapshot, (target, terms, advisories, assessments, policy), policy.version,
        findings, (("long_sentence_candidates", long_sentences), ("declared_terms", len(terms)),
            ("declared_advisories", len(advisories)), ("assessment_prompts", len(assessments))),
        "Declared curriculum audience, term scaffolding, sentence load and annotated content policy",
        ("This is not empirical age suitability, validated grade prediction or exhaustive content moderation.",
         "No age automatically forbids higher-order thinking; cognitive operations follow explicit curriculum policy.",
         "Annotation review is caller-reported, not independently attested. Learner profiles are optional."))


def validate_age_level_report(actual, *args, **kwargs):
    return verify_report(actual, age_level_qa(*args, **kwargs))
