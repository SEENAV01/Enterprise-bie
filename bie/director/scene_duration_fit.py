"""BIE-DIR-TIME-004: compose word, pause and emphasis time without truncation."""
from dataclasses import dataclass
import math
from .timing_contract import fingerprint, nonblank, ordered, number, integer
from .speech_timing import validate_speech_plan
from .pause_timing import validate_pause_plan
from .emphasis_timing import validate_emphasis_plan
from .pacing_plan import ScenePacing


@dataclass(frozen=True)
class SceneFitPolicy:
    version: str = "bie-dir-scene-fit/1.0.0"
    tolerance_ms: int = 0
    split_suggestion_ratio: float = 1.5

    def validate(self):
        nonblank(self.version, "scene fit policy version")
        integer(self.tolerance_ms, "tolerance_ms")
        number(self.split_suggestion_ratio, "split suggestion ratio", 1.0)


@dataclass(frozen=True)
class TimelineEvent:
    kind: str
    utterance_id: str
    word_index: int | None
    boundary: int | None
    start_ms: int
    end_ms: int
    evidence_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    concept_ids: tuple[str, ...] = ()
    cue_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SceneDurationFit:
    scene_id: str
    target_ms: int | None
    speech_and_recorded_gaps_ms: int
    additional_pause_ms: int
    additional_emphasis_ms: int
    duration_ms: int
    planning_upper_ms: int
    status: str
    requires_audio_replan: bool
    review_reasons: tuple[str, ...]
    events: tuple[TimelineEvent, ...]


@dataclass(frozen=True)
class SceneDurationPlan:
    speech_fingerprint: str
    pause_fingerprint: str
    emphasis_fingerprint: str
    policy: SceneFitPolicy
    targets: tuple[ScenePacing, ...]
    basis: str
    scenes: tuple[SceneDurationFit, ...]
    review_reasons: tuple[str, ...]

    @property
    def duration_ms(self):
        return sum(s.duration_ms for s in self.scenes)

    @property
    def requires_review(self):
        return bool(self.review_reasons)

    def fingerprint(self):
        return fingerprint(self)


def fit_scene_durations(speech, pauses, emphasis, targets=(), policy=SceneFitPolicy()):
    validate_speech_plan(speech)
    validate_pause_plan(speech, pauses)
    validate_emphasis_plan(speech, emphasis)
    policy.validate()
    rows = ordered(targets, "scene pacing targets")
    scene_ids = tuple(dict.fromkeys(t.utterance.scene_id for t in speech.utterances))
    target_by_scene = {}
    for target in rows:
        if not isinstance(target, ScenePacing):
            raise ValueError("expected existing ScenePacing contract")
        nonblank(target.scene_id, "target scene_id")
        nonblank(target.reason, "pacing reason")
        if target.pace_band not in ("FAST", "NORMAL", "SLOW"):
            raise ValueError("unknown pacing band")
        number(target.target_seconds, "target seconds", positive=True)
        number(target.target_seconds * 1000, "target milliseconds", positive=True)
        if target.scene_id not in scene_ids or target.scene_id in target_by_scene:
            raise ValueError("unknown or duplicate scene pacing target")
        target_by_scene[target.scene_id] = target
    slots = {(s.utterance_id, s.boundary): s for s in pauses.slots}
    covered_slots = {boundary: s for s in pauses.slots for boundary in s.covered_boundaries}
    stretches = {(w.utterance_id, w.word_index): w for w in emphasis.words}
    result, all_reasons = [], set(speech.review_reasons) | set(emphasis.review_reasons)
    for scene_id in scene_ids:
        events, cursor, baseline, added_pause, added_emphasis = [], 0, 0, 0, 0
        audio_replan = False
        reasons = set(speech.review_reasons) | set(emphasis.review_reasons)
        for t in (t for t in speech.utterances if t.utterance.scene_id == scene_id):
            u, previous_end = t.utterance, 0
            baseline += t.duration_ms
            for boundary in range(len(t.words) + 1):
                slot = slots.get((u.utterance_id, boundary))
                right = t.words[boundary].start_ms if boundary < len(t.words) else t.duration_ms
                gap = right - previous_end
                gap_slot = covered_slots.get((u.utterance_id, boundary))
                cue_ids = gap_slot.cue_ids if gap_slot else ()
                if gap:
                    events.append(TimelineEvent("RECORDED_GAP", u.utterance_id, None, boundary,
                        cursor, cursor+gap, u.evidence_ids, u.objective_ids, (), cue_ids))
                    cursor += gap
                if slot:
                    audio_replan |= slot.shortfall_ms > 0
                    if slot.additional_ms:
                        events.append(TimelineEvent("PLANNED_PAUSE", u.utterance_id, None, boundary,
                            cursor, cursor+slot.additional_ms, slot.evidence_ids, slot.objective_ids, (), cue_ids))
                        cursor += slot.additional_ms
                        added_pause += slot.additional_ms
                if boundary == len(t.words):
                    break
                word = t.words[boundary]
                stretch = stretches.get((u.utterance_id, boundary))
                extra = stretch.additional_ms if stretch else 0
                duration = word.end_ms-word.start_ms+extra
                events.append(TimelineEvent("SPEECH", u.utterance_id, boundary, None,
                    cursor, cursor+duration, u.evidence_ids, u.objective_ids,
                    (stretch.concept_id,) if stretch else ()))
                cursor += duration
                added_emphasis += extra
                previous_end = word.end_ms
        target = target_by_scene.get(scene_id)
        target_ms = math.ceil(target.target_seconds*1000) if target else None
        upper = (math.ceil((baseline+added_emphasis)*(1+speech.policy.estimate_margin)) + added_pause
                 if speech.basis == "ESTIMATED_WPM" else cursor)
        if target_ms is None:
            status = "NO_TARGET"
        elif cursor <= target_ms + policy.tolerance_ms:
            status = "WITHIN_TARGET"
            if upper > target_ms + policy.tolerance_ms:
                reasons.add("TARGET_WITHIN_ESTIMATE_UNCERTAINTY")
        else:
            status = "SPLIT_OR_EXTEND" if cursor > target_ms*policy.split_suggestion_ratio else "EXTEND"
        if audio_replan:
            reasons.add("PAUSE_SHORTFALL_REQUIRES_AUDIO_REPLAN")
        # Internal conservation check: every millisecond belongs to exactly one event.
        if cursor != baseline + added_pause + added_emphasis:
            raise RuntimeError("timing conservation failure")
        all_reasons.update(reasons)
        result.append(SceneDurationFit(scene_id, target_ms, baseline, added_pause,
            added_emphasis, cursor, upper, status, audio_replan, tuple(sorted(reasons)), tuple(events)))
    return SceneDurationPlan(speech.fingerprint(), pauses.fingerprint(), emphasis.fingerprint(),
        policy, tuple(target_by_scene[s] for s in scene_ids if s in target_by_scene),
        speech.basis, tuple(result), tuple(sorted(all_reasons)))
