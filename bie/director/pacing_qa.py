"""BIE-DIR-QA-006: inspect realized, revision-bound narration timing.

Policy values are engineering review thresholds, not measured comprehension
limits. Explicit response-time requirements are checked as contracts. All time
comes from the existing TIME producers; no text is shortened or audio edited.
"""
from dataclasses import dataclass
from .qa_contract import (TextSpan, Finding, validate_snapshot, span_text, rows,
                          immutable, report, verify_report)
from .timing_contract import nonblank, integer, number, identifiers, spoken_words
from .speech_timing import SpeechTimingPlan, validate_speech_plan
from .pause_timing import PauseTimingPlan, validate_pause_plan
from .emphasis_timing import EmphasisTimingPlan, validate_emphasis_plan
from .scene_duration_fit import SceneDurationPlan, fit_scene_durations


@dataclass(frozen=True)
class PacingBeat:
    beat_id: str
    span: TextSpan
    mode: str
    concept_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    minimum_reflection_ms: int = 0


@dataclass(frozen=True)
class PacingPolicy:
    version: str = "bie-dir-pacing-qa/1.0.0"
    minimum_wpm: float = 80.0
    maximum_wpm: float = 200.0
    reasoning_maximum_wpm: float = 150.0
    rolling_words: int = 12
    abrupt_rate_ratio: float = 1.6
    retrieval_reflection_ms: int = 2000
    reasoning_reflection_ms: int = 750
    break_ms: int = 500
    continuous_speech_review_ms: int = 60000
    unexplained_silence_review_ms: int = 8000
    concepts_per_minute_review: float = 12.0

    def validate(self):
        immutable(self)
        nonblank(self.version, "pacing policy version")
        number(self.minimum_wpm, "minimum wpm", 1, 1000)
        number(self.maximum_wpm, "maximum wpm", self.minimum_wpm, 1000)
        number(self.reasoning_maximum_wpm, "reasoning wpm", self.minimum_wpm, self.maximum_wpm)
        number(self.abrupt_rate_ratio, "rate ratio", 1.01)
        number(self.concepts_per_minute_review, "concept density", positive=True)
        integer(self.rolling_words, "rolling words", 2)
        for name in ("retrieval_reflection_ms", "reasoning_reflection_ms", "break_ms",
                     "continuous_speech_review_ms", "unexplained_silence_review_ms"):
            integer(getattr(self, name), name, 1)


def validate_timing(snapshot, speech, pauses, emphasis, timeline):
    """Recompose, rather than trust a timing fingerprint or edited duration."""
    validate_snapshot(snapshot)
    for value, cls in ((speech, SpeechTimingPlan), (pauses, PauseTimingPlan),
                       (emphasis, EmphasisTimingPlan), (timeline, SceneDurationPlan)):
        if not isinstance(value, cls):
            raise ValueError(f"expected {cls.__name__}")
        immutable(value)
    validate_speech_plan(speech)
    if tuple(t.utterance for t in speech.utterances) != snapshot.utterances:
        raise ValueError("timing does not describe the exact script in narrative order")
    validate_pause_plan(speech, pauses)
    validate_emphasis_plan(speech, emphasis)
    expected = fit_scene_durations(speech, pauses, emphasis, timeline.targets, timeline.policy)
    if expected != timeline:
        raise ValueError("stale, edited or inconsistent scene timeline")
    return tuple(event for scene in timeline.scenes for event in scene.events)


def pacing_qa(snapshot, speech, pauses, emphasis, timeline, beats=(), policy=PacingPolicy()):
    policy.validate()
    events = validate_timing(snapshot, speech, pauses, emphasis, timeline)
    index = validate_snapshot(snapshot)
    rows(beats, PacingBeat, "pacing beats", "beat_id")
    word_events = {(e.utterance_id, e.word_index): (i, e)
                   for i, e in enumerate(events) if e.kind == "SPEECH"}
    findings, measurements, occupied, reflection_ends = [], [], set(), set()

    def add(code, severity, subject, detail, stage="DIR", span=None, evidence=()):
        findings.append(Finding(code, severity, subject, detail, stage, span, evidence))

    # The original timing producers bind every word, recorded silence and planned
    # addition. Flattening preserves cross-utterance AND cross-scene adjacency;
    # a scene cut is not automatically a comprehension break.
    def following_silence(position):
        duration = 0
        for event in events[position+1:]:
            if event.kind == "SPEECH":
                break
            duration += event.end_ms - event.start_ms
        return duration

    for beat in beats:
        span_text(index, beat.span)
        if beat.mode not in ("INTRODUCE", "EXPLAIN", "DERIVE", "DEMONSTRATE", "RETRIEVE", "RECAP"):
            raise ValueError("unknown pacing mode")
        integer(beat.minimum_reflection_ms, "reflection time")
        for name in ("concept_ids", "evidence_ids", "objective_ids"):
            identifiers(getattr(beat, name), name, allow_empty=name == "concept_ids")
        u = index[beat.span.utterance_id]
        if not set(beat.evidence_ids) <= set(u.evidence_ids) or not set(beat.objective_ids) <= set(u.objective_ids):
            raise ValueError("pacing beat outside narration grounding/objectives")
        keys = [(u.utterance_id, w.index) for w in spoken_words(u.text)
                if beat.span.start_char <= w.start_char and w.end_char <= beat.span.end_char]
        if not keys or occupied.intersection(keys):
            raise ValueError("empty or overlapping pacing beats")
        occupied.update(keys)
        selected = [word_events[key] for key in keys]
        active_ms = sum(e.end_ms-e.start_ms for _, e in selected)
        rate = 60000 * len(keys) / active_ms
        measurements.append((f"beat:{beat.beat_id}:active_wpm", round(rate, 3)))
        if beat.mode in ("DERIVE", "DEMONSTRATE") and rate > policy.reasoning_maximum_wpm:
            add("REASONING_PACE_REVIEW", "REVIEW", beat.beat_id,
                "Reasoning narration exceeds the configured review rate.", span=beat.span, evidence=beat.evidence_ids)
        observed = following_silence(selected[-1][0])
        heuristic = (policy.retrieval_reflection_ms if beat.mode == "RETRIEVE" else
                     policy.reasoning_reflection_ms if beat.mode in ("DERIVE", "DEMONSTRATE") else 0)
        required = max(beat.minimum_reflection_ms, heuristic)
        measurements.append((f"beat:{beat.beat_id}:following_silence_ms", observed))
        if required:
            reflection_ends.add(selected[-1][0])
        if observed < beat.minimum_reflection_ms:
            add("REQUIRED_REFLECTION_SHORTFALL", "BLOCKER", beat.beat_id,
                f"Required {beat.minimum_reflection_ms} ms immediately after this beat; available {observed} ms.",
                "AUDIO" if speech.basis == "REPORTED_AUDIO_ALIGNMENT" else "TIME",
                beat.span, beat.evidence_ids)
        elif observed < heuristic:
            add("REFLECTION_OPPORTUNITY_REVIEW", "REVIEW", beat.beat_id,
                f"Configured {beat.mode} review target is {heuristic} ms; available {observed} ms.",
                "TIME", beat.span, beat.evidence_ids)
        # Count concepts once per annotated beat. This is declared density, not
        # automatic concept discovery or measured cognitive load.
        elapsed = sum(events[i].end_ms-events[i].start_ms for i in range(selected[0][0], selected[-1][0]+1))
        density = 60000 * len(beat.concept_ids) / elapsed
        measurements.append((f"beat:{beat.beat_id}:declared_concepts_per_minute", round(density, 3)))
        if density > policy.concepts_per_minute_review:
            add("DECLARED_CONCEPT_DENSITY_REVIEW", "REVIEW", beat.beat_id,
                "Declared concept density exceeds the review threshold; inspect scaffolding and chunking.",
                "PED", beat.span, beat.evidence_ids)

    rates = []
    for u in snapshot.utterances:
        words = spoken_words(u.text)
        selected = [word_events[(u.utterance_id, w.index)][1] for w in words]
        duration = sum(e.end_ms-e.start_ms for e in selected)
        rate = 60000*len(words)/duration
        rates.append((u.utterance_id, rate, len(words)))
        measurements.append((f"utterance:{u.utterance_id}:active_wpm", round(rate, 3)))
        if rate > policy.maximum_wpm or rate < policy.minimum_wpm:
            add("SPEECH_RATE_OUTSIDE_POLICY", "REVIEW", u.utterance_id,
                f"Active speech rate {rate:.3f} WPM is outside the configured review interval.", "TIME")
        n = min(policy.rolling_words, len(selected))
        peak = max(60000*n/sum(e.end_ms-e.start_ms for e in selected[i:i+n])
                   for i in range(len(selected)-n+1))
        measurements.append((f"utterance:{u.utterance_id}:peak_window_wpm", round(peak, 3)))
        if peak > policy.maximum_wpm:
            add("RUSHED_SPEECH_WINDOW", "REVIEW", u.utterance_id,
                f"A {n}-word active-speech window reaches {peak:.3f} WPM; silence cannot hide rushed speech.", "TIME")
        missing = sum((u.utterance_id, w.index) not in occupied for w in words)
        if missing:
            add("PACING_ANNOTATION_INCOMPLETE", "REVIEW", u.utterance_id,
                f"{missing} spoken words have no source-bound pacing beat; teaching-mode checks remain incomplete.")
    for (left, a, na), (right, b, nb) in zip(rates, rates[1:]):
        if min(na, nb) >= policy.rolling_words and max(a, b)/min(a, b) > policy.abrupt_rate_ratio:
            add("ABRUPT_RATE_CHANGE", "REVIEW", right, f"Adjacent narration changes rate abruptly after {left}.", "TIME")

    burst, longest, cursor = 0, 0, 0
    while cursor < len(events):
        e = events[cursor]
        if e.kind == "SPEECH":
            burst += e.end_ms-e.start_ms
            longest = max(longest, burst)
            cursor += 1
            continue
        first, silence, cues = cursor, 0, set()
        while cursor < len(events) and events[cursor].kind != "SPEECH":
            gap = events[cursor]
            silence += gap.end_ms-gap.start_ms
            cues.update(gap.cue_ids)
            cursor += 1
        if silence >= policy.break_ms:
            burst = 0
        elif burst:
            burst += silence
        if silence >= policy.unexplained_silence_review_ms and not cues and first-1 not in reflection_ends:
            add("UNEXPLAINED_SILENCE_REVIEW", "REVIEW", e.utterance_id,
                f"{silence} ms of silence has no declared pause or reflection purpose.", "TIME")
    if longest > policy.continuous_speech_review_ms:
        add("CONTINUOUS_SPEECH_REVIEW", "REVIEW", snapshot.script.lesson_id,
            f"Continuous narration reaches {longest} ms; review opportunities to process the material.", "PED")
    for slot in pauses.slots:
        if slot.shortfall_ms:
            add("PAUSE_SHORTFALL_REQUIRES_AUDIO_REPLAN", "BLOCKER", slot.utterance_id,
                f"Recorded audio lacks {slot.shortfall_ms} ms of its declared pause.", "AUDIO")
    for scene in timeline.scenes:
        if scene.status in ("EXTEND", "SPLIT_OR_EXTEND"):
            add("SCENE_TARGET_REQUIRES_REPLAN", "REVIEW", scene.scene_id,
                "Source-preserving duration exceeds the soft target; extend or split the scene.", "DIR")
    for reason in timeline.review_reasons:
        add(reason, "REVIEW", snapshot.script.lesson_id,
            "Timing producer review remains unresolved; estimated/reported timing is not verified audio.", "AUDIO")
    measurements.extend((("total_duration_ms", timeline.duration_ms), ("longest_continuous_speech_ms", longest),
                         ("spoken_words", len(word_events)), ("annotated_words", len(occupied))))
    return report("BIE-DIR-QA-006", snapshot, (speech, pauses, emphasis, timeline, beats, policy), policy.version,
                  findings, measurements, "Realized narration timing, explicit reflection contracts and pacing review heuristics",
                  ("Estimated timing and reported alignment require actual audio QA.",
                   "Mode/concept annotations require upstream semantic production and review.",
                   "Policy thresholds are not empirical comprehension limits or duration caps."))


def validate_pacing_report(actual, snapshot, speech, pauses, emphasis, timeline, beats=(), policy=PacingPolicy()):
    return verify_report(actual, pacing_qa(snapshot, speech, pauses, emphasis, timeline, beats, policy))
