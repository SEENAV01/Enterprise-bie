"""BIE-DIR-TIME-005: content-driven, bounded speaking-rate proposals.

No learner profile is required. This returns a versioned engineering proposal,
not empirically certified comprehension or a modified audio file.
"""
from dataclasses import dataclass
import math
from .timing_contract import fingerprint, nonblank, identifiers, number
from .speech_timing import estimate_speech, validate_speech_plan, SpeechTimingPlan
from .pause_timing import build_pause_timing, validate_pause_plan, PauseTimingPlan
from .emphasis_timing import build_emphasis_timing, validate_emphasis_plan, EmphasisTimingPlan
from .scene_duration_fit import fit_scene_durations, SceneFitPolicy, SceneDurationPlan


@dataclass(frozen=True)
class ContentLoad:
    conceptual: float
    prerequisite_novelty: float
    notation: float
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class WpmAdaptationPolicy:
    version: str = "bie-dir-wpm/1.0.0"
    conceptual_slowdown: float = 0.20
    novelty_slowdown: float = 0.10
    notation_slowdown: float = 0.15

    def validate(self):
        nonblank(self.version, "WPM policy version")
        for name in ("conceptual_slowdown", "novelty_slowdown", "notation_slowdown"):
            number(getattr(self, name), name, 0.0, 0.9)
        if self.conceptual_slowdown+self.novelty_slowdown+self.notation_slowdown > 0.9:
            raise ValueError("combined load slowdown must not exceed 0.9")


@dataclass(frozen=True)
class WpmAdaptation:
    input_speech_fingerprint: str
    input_pause_fingerprint: str
    input_emphasis_fingerprint: str
    load: ContentLoad
    policy: WpmAdaptationPolicy
    selected_wpm: float | None
    preferred_wpm: float | None
    content_rate_ceiling: float | None
    status: str
    candidate_speech: SpeechTimingPlan
    candidate_pauses: PauseTimingPlan
    candidate_emphasis: EmphasisTimingPlan
    candidate_scene_plan: SceneDurationPlan
    review_reasons: tuple[str, ...]

    def fingerprint(self):
        return fingerprint(self)


def adapt_wpm(speech, pauses, emphasis, load, targets=(),
              policy=WpmAdaptationPolicy(), fit_policy=SceneFitPolicy()):
    validate_speech_plan(speech)
    validate_pause_plan(speech, pauses)
    validate_emphasis_plan(speech, emphasis)
    policy.validate()
    if not isinstance(load, ContentLoad):
        raise ValueError("expected evidence-bound ContentLoad")
    for name in ("conceptual", "prerequisite_novelty", "notation"):
        number(getattr(load, name), name, 0.0, 1.0)
    if type(load.evidence_ids) is not tuple:
        raise ValueError("load evidence must be immutable")
    identifiers(load.evidence_ids, "content load evidence")
    known_evidence = {e for t in speech.utterances for e in t.utterance.evidence_ids}
    if not set(load.evidence_ids) <= known_evidence:
        raise ValueError("load evidence outside narration grounding")
    # Materialize/validate targets once, including generator callers.
    original_fit = fit_scene_durations(speech, pauses, emphasis, targets, fit_policy)
    targets = original_fit.targets
    lineage = (speech.fingerprint(), pauses.fingerprint(), emphasis.fingerprint())
    if speech.basis != "ESTIMATED_WPM":
        return WpmAdaptation(*lineage, load, policy, None, None, None, "AUDIO_REPLAN_REQUIRED",
            speech, pauses, emphasis, original_fit,
            tuple(sorted(set(original_fit.review_reasons) | {"REPORTED_AUDIO_CANNOT_BE_RETIMED_BY_WPM"})))
    factor = 1-(load.conceptual*policy.conceptual_slowdown +
                load.prerequisite_novelty*policy.novelty_slowdown + load.notation*policy.notation_slowdown)
    preferred = max(speech.policy.min_wpm, speech.policy.default_wpm*factor)
    ceiling = max(speech.policy.min_wpm, speech.policy.max_wpm*factor)
    inputs = tuple(t.utterance for t in speech.utterances)

    def evaluate(rate):
        candidate = estimate_speech(inputs, speech.policy, rate)
        cp = build_pause_timing(candidate, pauses.cues, pauses.policy_version)
        ce = build_emphasis_timing(candidate, emphasis.anchors, emphasis.policy)
        cf = fit_scene_durations(candidate, cp, ce, targets, fit_policy)
        return candidate, cp, ce, cf

    def fits(candidate):
        return all(s.target_ms is None or s.duration_ms <= s.target_ms+fit_policy.tolerance_ms
                   for s in candidate[-1].scenes)

    selected = preferred
    proposal = evaluate(selected)
    if fits(proposal):
        status = "CONTENT_RATE_SELECTED" if not targets else "TARGET_FIT_ESTIMATED"
    else:
        fastest = evaluate(ceiling)
        if not fits(fastest):
            # Keep content's preferred rate when the budget is impossible at the ceiling.
            status = "EXTEND_OR_SPLIT_REQUIRED"
        else:
            # Deterministic 0.1 WPM grid, with the exact content ceiling as an endpoint.
            lo, hi = math.ceil(preferred*10), math.floor(ceiling*10)
            best = None
            while lo <= hi:
                mid = (lo+hi)//2
                candidate = evaluate(mid/10)
                if fits(candidate):
                    best = (mid/10, candidate)
                    hi = mid-1
                else:
                    lo = mid+1
            selected, proposal = best if best is not None else (ceiling, fastest)
            status = "TARGET_FIT_ESTIMATED"
    reasons = set(proposal[-1].review_reasons) | {"CONTENT_LOAD_RATE_POLICY_UNCALIBRATED"}
    return WpmAdaptation(*lineage, load, policy, selected, preferred, ceiling, status,
        *proposal, tuple(sorted(reasons)))
