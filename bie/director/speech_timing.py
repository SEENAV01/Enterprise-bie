"""BIE-DIR-TIME-001: grounded speech estimates or reported audio alignment.

The alignment adapter validates a caller-supplied transcript/voice-bound timing
record. It does not open audio or certify alignment accuracy (AUDIO/QA owns that).
"""
from dataclasses import dataclass
import math
from .timing_contract import (TimingPolicy, SpokenWord, fingerprint, nonblank,
    ordered, identifiers, number, integer, digest_id, spoken_words, text_review_reasons)


@dataclass(frozen=True)
class SpeechUtterance:
    utterance_id: str
    segment_id: str
    scene_id: str
    voice_id: str
    text: str
    language: str
    evidence_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    script_fingerprint: str
    review_reasons: tuple[str, ...] = ()

    def fingerprint(self):
        return fingerprint(self)


@dataclass(frozen=True)
class WordTiming:
    word: SpokenWord
    start_ms: int
    end_ms: int


@dataclass(frozen=True)
class ReportedAlignment:
    utterance_fingerprint: str
    audio_sha256: str
    duration_ms: int
    word_intervals_ms: tuple[tuple[int, int], ...]
    aligner_version: str


@dataclass(frozen=True)
class UtteranceTiming:
    utterance: SpeechUtterance
    words: tuple[WordTiming, ...]
    duration_ms: int
    wpm: float | None
    alignment: ReportedAlignment | None


@dataclass(frozen=True)
class SpeechTimingPlan:
    utterances: tuple[UtteranceTiming, ...]
    policy: TimingPolicy
    basis: str
    review_reasons: tuple[str, ...]
    audio_verified: bool = False

    @property
    def requires_review(self):
        return bool(self.review_reasons)

    def fingerprint(self):
        return fingerprint(self)


def _validate_inputs(utterances):
    items = ordered(utterances, "utterances")
    if not items:
        raise ValueError("utterances must not be empty")
    seen_ids, closed_scenes = set(), set()
    previous_scene = None
    script_hashes = set()
    for u in items:
        if not isinstance(u, SpeechUtterance):
            raise ValueError("expected SpeechUtterance")
        for name in ("utterance_id", "segment_id", "scene_id", "voice_id", "text", "language"):
            nonblank(getattr(u, name), name)
        for name in ("evidence_ids", "objective_ids", "review_reasons"):
            values = getattr(u, name)
            if type(values) is not tuple:
                raise ValueError(f"{name} must be immutable tuple")
            identifiers(values, name, allow_empty=name == "review_reasons")
        digest_id(u.script_fingerprint, "script_fingerprint")
        script_hashes.add(u.script_fingerprint)
        if u.utterance_id in seen_ids:
            raise ValueError("duplicate utterance_id")
        seen_ids.add(u.utterance_id)
        if u.scene_id != previous_scene:
            if u.scene_id in closed_scenes:
                raise ValueError("scene utterances must be contiguous in supplied narrative order")
            if previous_scene is not None:
                closed_scenes.add(previous_scene)
            previous_scene = u.scene_id
        spoken_words(u.text)
    if len(script_hashes) != 1:
        raise ValueError("cannot mix different script revisions")
    return items


def utterances_from_script(script, drafts, segment_order, language="en"):
    """Join SCRIPT-001/002 without treating text_intent as spoken narration.

    Explicit segment_order prevents lexicographic script IDs from silently
    determining narrative sequence. Exactly one realized draft per segment.
    """
    nonblank(script.lesson_id, "lesson_id")
    nonblank(script.voice_profile, "voice_profile")
    nonblank(language, "language")
    segments = ordered(script.segments, "segments")
    order = identifiers(segment_order, "segment_order")
    by_segment = {}
    for s in segments:
        for name in ("segment_id", "scene_id", "purpose", "text_intent"):
            nonblank(getattr(s, name), name)
        identifiers(s.evidence_ids, "segment evidence")
        identifiers(s.objective_ids, "segment objectives")
        if s.segment_id in by_segment:
            raise ValueError("duplicate segment")
        by_segment[s.segment_id] = s
    by_draft = {}
    for d in ordered(drafts, "drafts"):
        nonblank(d.segment_id, "draft segment")
        nonblank(d.text, "draft text")
        identifiers(d.evidence_ids, "draft evidence")
        identifiers(d.unsupported_claims, "unsupported claims", allow_empty=True)
        if type(d.requires_review) is not bool or d.segment_id in by_draft:
            raise ValueError("invalid review flag or duplicate draft")
        by_draft[d.segment_id] = d
    if set(order) != set(by_segment) or set(order) != set(by_draft):
        raise ValueError("order, script and drafts must cover exactly the same segments")
    result = []
    for sid in order:
        s, d = by_segment[sid], by_draft[sid]
        if not set(d.evidence_ids) <= set(s.evidence_ids):
            raise ValueError("voiceover evidence outside script segment")
        reasons = tuple(x for x, condition in (
            ("UPSTREAM_REVIEW", d.requires_review),
            ("UNSUPPORTED_CLAIMS_WITHHELD", bool(d.unsupported_claims))) if condition)
        result.append(SpeechUtterance(sid, sid, s.scene_id, script.voice_profile,
            d.text, language, tuple(d.evidence_ids), tuple(s.objective_ids),
            script.fingerprint(), reasons))
    return _validate_inputs(result)


def _reviews(items, basis):
    reasons = {"UNCALIBRATED_WPM_ESTIMATE" if basis == "ESTIMATED_WPM"
               else "REPORTED_ALIGNMENT_REQUIRES_AUDIO_QA"}
    for u in items:
        reasons.update(u.review_reasons)
        reasons.update(text_review_reasons(u.text, u.language))
    return tuple(sorted(reasons))


def estimate_speech(utterances, policy=TimingPolicy(), wpm=None):
    policy.validate()
    items = _validate_inputs(utterances)
    rate = policy.default_wpm if wpm is None else wpm
    number(rate, "wpm", policy.min_wpm, policy.max_wpm)
    result = []
    for u in items:
        tokens = spoken_words(u.text)
        # Cumulative boundaries avoid N separate rounding errors.
        boundaries = [math.ceil(i * 60000 / rate) for i in range(len(tokens) + 1)]
        words = tuple(WordTiming(w, boundaries[i], boundaries[i+1]) for i, w in enumerate(tokens))
        result.append(UtteranceTiming(u, words, boundaries[-1], float(rate), None))
    return SpeechTimingPlan(tuple(result), policy, "ESTIMATED_WPM", _reviews(items, "ESTIMATED_WPM"))


def align_reported_speech(utterances, alignments, policy=TimingPolicy()):
    policy.validate()
    items = _validate_inputs(utterances)
    rows = ordered(alignments, "alignments")
    if len(items) != len(rows):
        raise ValueError("one reported alignment required per utterance")
    result = []
    for u, a in zip(items, rows):
        if not isinstance(a, ReportedAlignment):
            raise ValueError("expected ReportedAlignment")
        if a.utterance_fingerprint != u.fingerprint():
            raise ValueError("stale transcript, voice or source alignment")
        digest_id(a.audio_sha256, "audio_sha256")
        integer(a.duration_ms, "audio duration", 1)
        nonblank(a.aligner_version, "aligner_version")
        if type(a.word_intervals_ms) is not tuple:
            raise ValueError("alignment intervals must be immutable tuples")
        tokens = spoken_words(u.text)
        if len(tokens) != len(a.word_intervals_ms):
            raise ValueError("alignment does not cover the exact token sequence")
        words, end = [], 0
        for token, interval in zip(tokens, a.word_intervals_ms):
            if type(interval) is not tuple or len(interval) != 2:
                raise ValueError("invalid word interval")
            start, stop = interval
            integer(start, "word start")
            integer(stop, "word end", 1)
            if start < end or stop <= start or stop > a.duration_ms:
                raise ValueError("overlapping, inverted or out-of-audio interval")
            words.append(WordTiming(token, start, stop))
            end = stop
        result.append(UtteranceTiming(u, tuple(words), a.duration_ms, None, a))
    return SpeechTimingPlan(tuple(result), policy, "REPORTED_AUDIO_ALIGNMENT",
                            _reviews(items, "REPORTED_AUDIO_ALIGNMENT"))


def validate_speech_plan(plan):
    if not isinstance(plan, SpeechTimingPlan) or type(plan.utterances) is not tuple:
        raise ValueError("expected immutable SpeechTimingPlan")
    if not plan.utterances:
        raise ValueError("speech plan is empty")
    items = tuple(t.utterance for t in plan.utterances)
    if plan.basis == "ESTIMATED_WPM":
        rates = {t.wpm for t in plan.utterances}
        if len(rates) != 1 or None in rates:
            raise ValueError("estimated plan must have one validated speaking rate")
        expected = estimate_speech(items, plan.policy, plan.utterances[0].wpm)
    elif plan.basis == "REPORTED_AUDIO_ALIGNMENT":
        expected = align_reported_speech(items, tuple(t.alignment for t in plan.utterances), plan.policy)
    else:
        raise ValueError("unknown speech timing basis")
    if plan != expected or plan.fingerprint() != expected.fingerprint():
        raise ValueError("speech plan differs from its inputs/policy; rebuild instead of editing")
    return plan
