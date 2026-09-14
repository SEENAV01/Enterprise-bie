"""Shared director synchronization contracts, owned by BIE-DIR-SYNC-001.

These are grounded intent schedules. They do not certify semantics, audio,
rendering or simulation correctness. Milliseconds are scene-local throughout.
"""
from dataclasses import dataclass, is_dataclass
from .timing_contract import (fingerprint, nonblank, identifiers, integer, number,
                              ordered, digest_id)
from .speech_timing import SpeechTimingPlan
from .pause_timing import PauseTimingPlan
from .emphasis_timing import EmphasisTimingPlan
from .scene_duration_fit import SceneDurationPlan, fit_scene_durations


def immutable_ids(values, name, empty=False):
    if type(values) is not tuple:
        raise ValueError(f"{name} must be an immutable tuple")
    return identifiers(values, name, allow_empty=empty)


@dataclass(frozen=True)
class SyncContext:
    speech: SpeechTimingPlan
    pauses: PauseTimingPlan
    emphasis: EmphasisTimingPlan
    timeline: SceneDurationPlan

    def fingerprint(self):
        return fingerprint(self)


def build_sync_context(speech, pauses, emphasis, timeline=None):
    if timeline is not None and not isinstance(timeline, SceneDurationPlan):
        raise ValueError("expected SceneDurationPlan")
    expected = (fit_scene_durations(speech, pauses, emphasis, timeline.targets, timeline.policy)
                if timeline is not None else fit_scene_durations(speech, pauses, emphasis))
    if timeline is not None and (timeline != expected or timeline.fingerprint() != expected.fingerprint()):
        raise ValueError("timeline is stale or edited; rebuild from its timing parents")
    return SyncContext(speech, pauses, emphasis, expected)


@dataclass(frozen=True)
class NarrationAnchor:
    scene_id: str
    utterance_id: str
    start_word: int
    end_word: int  # exclusive
    utterance_fingerprint: str


@dataclass(frozen=True)
class IntentBinding:
    intent_id: str
    target_id: str
    anchor: NarrationAnchor
    evidence_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    concept_ids: tuple[str, ...]
    purpose: str


@dataclass(frozen=True)
class SyncWindow:
    scene_id: str
    start_ms: int
    end_ms: int
    narration_start_ms: int
    narration_end_ms: int
    start_char: int
    end_char: int
    segment_id: str


@dataclass(frozen=True)
class SyncIssue:
    code: str
    intent_id: str
    detail: str
    repair_stage: str


@dataclass(frozen=True)
class SyncCue:
    binding: IntentBinding
    kind: str
    window: SyncWindow
    parameters: tuple


@dataclass(frozen=True)
class SyncPlan:
    task_id: str
    context_fingerprint: str
    upstream_fingerprint: str | None
    policy_version: str
    timing_basis: str
    inputs: tuple
    definitions: tuple
    cues: tuple[SyncCue, ...]
    issues: tuple[SyncIssue, ...]
    review_reasons: tuple[str, ...]

    @property
    def status(self):
        return "BLOCKED" if self.issues else "READY_FOR_DOWNSTREAM_REVIEW"

    @property
    def accepted(self):
        return False

    @property
    def requires_review(self):
        return True

    def fingerprint(self):
        return fingerprint(self)


def _immutable(value):
    if value is None or isinstance(value, (str, bool)):
        return
    if type(value) in (int, float):
        number(value, "parameter", low=-float("inf"))
    elif type(value) is tuple:
        for item in value:
            _immutable(item)
    elif is_dataclass(value) and value.__dataclass_params__.frozen:
        for name in value.__dataclass_fields__:
            _immutable(getattr(value, name))
    else:
        raise ValueError("sync data must contain only immutable finite values")


def parameters(**values):
    result = tuple(sorted(values.items()))
    _immutable(result)
    return result


class SyncIndex:
    """Validate timing once per builder, then resolve anchors with indexed lookups."""
    def __init__(self, context):
        if not isinstance(context, SyncContext):
            raise ValueError("expected SyncContext")
        expected = build_sync_context(context.speech, context.pauses, context.emphasis, context.timeline)
        if context != expected or context.fingerprint() != expected.fingerprint():
            raise ValueError("invalid synchronization context")
        self.context = context
        self.utterances = {t.utterance.utterance_id:t for t in context.speech.utterances}
        self.scenes = {s.scene_id:s for s in context.timeline.scenes}
        self.scene_order = {sid:i for i,sid in enumerate(self.scenes)}
        self.events = {(s.scene_id,e.utterance_id,e.word_index):e for s in context.timeline.scenes
                       for e in s.events if e.kind == "SPEECH"}

    def anchor(self, utterance_id, start_word, end_word):
        if utterance_id not in self.utterances:
            raise ValueError("unknown utterance")
        u = self.utterances[utterance_id].utterance
        result = NarrationAnchor(u.scene_id, utterance_id, start_word, end_word, u.fingerprint())
        self._anchor(result)
        return result

    def _anchor(self, anchor):
        if not isinstance(anchor, NarrationAnchor):
            raise ValueError("expected NarrationAnchor")
        nonblank(anchor.scene_id, "anchor scene")
        nonblank(anchor.utterance_id, "anchor utterance")
        digest_id(anchor.utterance_fingerprint, "anchor utterance fingerprint")
        t = self.utterances.get(anchor.utterance_id)
        if t is None or t.utterance.scene_id != anchor.scene_id:
            raise ValueError("unknown utterance or cross-scene anchor")
        if t.utterance.fingerprint() != anchor.utterance_fingerprint:
            raise ValueError("anchor belongs to a different text, voice or source revision")
        integer(anchor.start_word, "start_word")
        integer(anchor.end_word, "end_word", 1)
        if anchor.start_word >= anchor.end_word or anchor.end_word > len(t.words):
            raise ValueError("word anchor outside narration")
        return t

    def resolve(self, binding, lead_ms=0, tail_ms=0):
        if not isinstance(binding, IntentBinding):
            raise ValueError("expected IntentBinding")
        for name in ("intent_id", "target_id", "purpose"):
            nonblank(getattr(binding,name),name)
        for name in ("evidence_ids", "objective_ids", "concept_ids"):
            immutable_ids(getattr(binding,name),name)
        t = self._anchor(binding.anchor)
        if not set(binding.evidence_ids) <= set(t.utterance.evidence_ids):
            raise ValueError("intent evidence outside narration grounding")
        if not set(binding.objective_ids) <= set(t.utterance.objective_ids):
            raise ValueError("intent objectives outside narration objectives")
        integer(lead_ms, "lead_ms")
        integer(tail_ms, "tail_ms")
        a = binding.anchor
        first = self.events[(a.scene_id,a.utterance_id,a.start_word)]
        last = self.events[(a.scene_id,a.utterance_id,a.end_word-1)]
        window = SyncWindow(a.scene_id,first.start_ms-lead_ms,last.end_ms+tail_ms,
            first.start_ms,last.end_ms,t.words[a.start_word].word.start_char,
            t.words[a.end_word-1].word.end_char,t.utterance.segment_id)
        return window


def unique_inputs(values, cls):
    rows = ordered(values, "sync intents")
    seen = set()
    for row in rows:
        if not isinstance(row, cls) or not isinstance(row.binding, IntentBinding):
            raise ValueError(f"expected {cls.__name__}")
        _immutable(row)
        nonblank(row.binding.intent_id, "intent_id")
        if row.binding.intent_id in seen:
            raise ValueError("duplicate intent_id")
        seen.add(row.binding.intent_id)
    return rows


def window_issues(index, cue):
    issues = []
    w = cue.window
    if w.start_ms < 0:
        issues.append(SyncIssue("LEAD_BEFORE_SCENE",cue.binding.intent_id,
                               "Requested pre-roll precedes the scene; revise the upstream scene timing.","DIR_TIME"))
    if w.end_ms > index.scenes[w.scene_id].duration_ms:
        issues.append(SyncIssue("WINDOW_EXCEEDS_SCENE",cue.binding.intent_id,
                               "Requested hold needs a longer scene; no time was silently clamped.","DIR_TIME"))
    return issues


def finish_plan(index, task_id, version, inputs, definitions, cues, issues=(), upstream=None, reviews=()):
    nonblank(version, "sync policy version")
    for value in (inputs, definitions, cues):
        _immutable(value)
    all_issues = list(issues)
    for cue in cues:
        all_issues.extend(window_issues(index, cue))
    for scene in index.scenes.values():
        if scene.requires_audio_replan:
            all_issues.append(SyncIssue("AUDIO_REPLAN_REQUIRED",scene.scene_id,
                "Timing carries an unresolved recorded-audio pause shortfall.","AUDIO"))
    if not inputs:
        all_issues.append(SyncIssue("NO_INTENTS",task_id,"No intents supplied for this scoped plan.","DIR_SCRIPT"))
    all_issues = tuple(sorted(set(all_issues),key=lambda i:(i.intent_id,i.code,i.detail)))
    cue_order = lambda c:(index.scene_order[c.window.scene_id],c.window.start_ms,c.binding.intent_id)
    return SyncPlan(task_id,index.context.fingerprint(),upstream,version,index.context.speech.basis,
        tuple(sorted(inputs,key=lambda x:x.binding.intent_id)),definitions,tuple(sorted(cues,key=cue_order)),all_issues,
        tuple(sorted(set(index.context.timeline.review_reasons) | set(reviews) |
                     {"SEMANTIC_BINDINGS_REQUIRE_DOWNSTREAM_QA","INTENT_SCHEDULE_NOT_RENDER_VERIFICATION"})))


def same_plan(plan, expected):
    if not isinstance(plan, SyncPlan) or plan != expected or plan.fingerprint() != expected.fingerprint():
        raise ValueError("sync plan is stale or edited; rebuild from exact parents")
    return plan


def require_target(cue, visual_cue, kind=None):
    """Require same grounded target; return timing conflicts as explicit blockers."""
    if cue.binding.target_id != visual_cue.binding.target_id or cue.window.scene_id != visual_cue.window.scene_id:
        raise ValueError("sync intent refers to a different visual target or scene")
    for field in ("concept_ids","evidence_ids","objective_ids"):
        if not set(getattr(cue.binding,field)) <= set(getattr(visual_cue.binding,field)):
            raise ValueError(f"sync {field} outside visual intent grounding")
    if kind is not None and visual_cue.kind != kind:
        raise ValueError("wrong visual kind for specialized sync")
    if cue.window.start_ms < visual_cue.window.start_ms or cue.window.end_ms > visual_cue.window.end_ms:
        return [SyncIssue("OUTSIDE_VISUAL_LIFETIME",cue.binding.intent_id,
                         "Narration sync falls outside its visual visibility window.","DIR_SYNC_VISUAL")]
    return []
