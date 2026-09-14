"""BIE-DIR-TIME-003: explicit concept-to-word timing, without keyword guessing."""
from dataclasses import dataclass
import math
from .timing_contract import fingerprint, nonblank, ordered, identifiers, number, integer
from .speech_timing import validate_speech_plan
from .emphasis_plan import EmphasisDecision


@dataclass(frozen=True)
class EmphasisPolicy:
    version: str = "bie-dir-emphasis/1.0.0"
    maximum_slowdown: float = 0.25

    def validate(self):
        nonblank(self.version, "emphasis policy version")
        number(self.maximum_slowdown, "maximum_slowdown", 0.0, 0.75)


@dataclass(frozen=True)
class EmphasisAnchor:
    anchor_id: str
    utterance_id: str
    start_word: int
    end_word: int  # exclusive
    decision: EmphasisDecision
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class EmphasisWord:
    utterance_id: str
    word_index: int
    anchor_id: str
    concept_id: str
    requested_rate_factor: float
    effective_wpm: float | None
    additional_ms: int
    floor_limited: bool


@dataclass(frozen=True)
class EmphasisTimingPlan:
    speech_fingerprint: str
    policy: EmphasisPolicy
    anchors: tuple[EmphasisAnchor, ...]
    words: tuple[EmphasisWord, ...]
    review_reasons: tuple[str, ...]

    def fingerprint(self):
        return fingerprint(self)


def build_emphasis_timing(speech, anchors=(), policy=EmphasisPolicy()):
    validate_speech_plan(speech)
    policy.validate()
    rows = ordered(anchors, "emphasis anchors")
    by_id = {t.utterance.utterance_id: t for t in speech.utterances}
    positions = {key: i for i, key in enumerate(by_id)}
    seen_ids, occupied, words, reasons = set(), set(), [], set()
    for a in rows:
        if not isinstance(a, EmphasisAnchor) or not isinstance(a.decision, EmphasisDecision):
            raise ValueError("expected emphasis anchor and existing EmphasisDecision")
        nonblank(a.anchor_id, "anchor_id")
        nonblank(a.utterance_id, "utterance_id")
        nonblank(a.decision.concept_id, "concept_id")
        number(a.decision.emphasis, "emphasis strength", 0.0, 1.0)
        if type(a.decision.reasons) is not tuple:
            raise ValueError("decision reasons must be immutable")
        identifiers(a.decision.reasons, "emphasis reasons", allow_empty=True)
        if a.anchor_id in seen_ids or a.utterance_id not in by_id:
            raise ValueError("duplicate anchor or unknown utterance")
        seen_ids.add(a.anchor_id)
        t = by_id[a.utterance_id]
        integer(a.start_word, "start_word")
        integer(a.end_word, "end_word", 1)
        if a.end_word <= a.start_word or a.end_word > len(t.words):
            raise ValueError("emphasis span outside utterance")
        if type(a.evidence_ids) is not tuple:
            raise ValueError("emphasis evidence must be immutable")
        identifiers(a.evidence_ids, "emphasis evidence")
        if not set(a.evidence_ids) <= set(t.utterance.evidence_ids):
            raise ValueError("emphasis evidence outside utterance grounding")
        factor = 1.0 - policy.maximum_slowdown * a.decision.emphasis
        for index in range(a.start_word, a.end_word):
            key = (a.utterance_id, index)
            if key in occupied:
                raise ValueError("overlapping emphasis anchors require explicit upstream resolution")
            occupied.add(key)
            effective, extra, floor_limited = None, 0, False
            if t.wpm is not None:
                requested = t.wpm * factor
                effective = max(speech.policy.min_wpm, requested)
                floor_limited = effective > requested
                old_duration = t.words[index].end_ms - t.words[index].start_ms
                extra = max(0, math.ceil(60000 / effective) - old_duration) if effective < t.wpm else 0
                if floor_limited:
                    reasons.add("EMPHASIS_SLOWDOWN_LIMITED_BY_RATE_FLOOR")
            elif factor < 1:
                reasons.add("REPORTED_EMPHASIS_REQUIRES_AUDIO_QA")
            words.append(EmphasisWord(a.utterance_id, index, a.anchor_id,
                a.decision.concept_id, factor, effective, extra, floor_limited))
    return EmphasisTimingPlan(speech.fingerprint(), policy,
        tuple(sorted(rows, key=lambda a: (positions[a.utterance_id], a.start_word, a.anchor_id))),
        tuple(sorted(words, key=lambda w: (positions[w.utterance_id], w.word_index))), tuple(sorted(reasons)))


def validate_emphasis_plan(speech, plan):
    if not isinstance(plan, EmphasisTimingPlan) or plan.speech_fingerprint != speech.fingerprint():
        raise ValueError("emphasis plan belongs to a different speech revision")
    expected = build_emphasis_timing(speech, plan.anchors, plan.policy)
    if plan != expected or plan.fingerprint() != expected.fingerprint():
        raise ValueError("emphasis plan was edited or is inconsistent")
    return plan
