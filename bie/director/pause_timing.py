"""BIE-DIR-TIME-002: evidence-bound, explicit word-boundary pauses."""
from dataclasses import dataclass
from .timing_contract import fingerprint, nonblank, ordered, identifiers, integer
from .speech_timing import validate_speech_plan


@dataclass(frozen=True)
class PauseCue:
    cue_id: str
    utterance_id: str
    boundary: int  # 0 before first word; N after last word
    duration_ms: int
    reason: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class PauseSlot:
    utterance_id: str
    boundary: int
    required_ms: int
    existing_ms: int
    additional_ms: int
    shortfall_ms: int
    cue_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    covered_boundaries: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class PauseTimingPlan:
    speech_fingerprint: str
    policy_version: str
    cues: tuple[PauseCue, ...]
    slots: tuple[PauseSlot, ...]

    @property
    def requires_rerender(self):
        return any(s.shortfall_ms for s in self.slots)

    def fingerprint(self):
        return fingerprint(self)


def build_pause_timing(speech, cues=(), policy_version="bie-dir-pause/1.0.0"):
    """Coincident cues share a single pause of max(requested durations).

    Reported audio remains immutable: existing silence is checked and shortfall
    is returned for audio regeneration/re-alignment, never inserted invisibly.
    """
    validate_speech_plan(speech)
    nonblank(policy_version, "pause policy version")
    rows = ordered(cues, "pause cues")
    by_id = {t.utterance.utterance_id: t for t in speech.utterances}
    positions = {key: i for i, key in enumerate(by_id)}
    # Tail/head cues at a shared within-scene utterance boundary request one
    # silence interval. Adjacent recorded clips may both contribute silence.
    aliases, coverage = {}, {}
    for left, right in zip(speech.utterances, speech.utterances[1:]):
        if left.utterance.scene_id == right.utterance.scene_id:
            tail = (left.utterance.utterance_id, len(left.words))
            head = (right.utterance.utterance_id, 0)
            aliases[head] = tail
            coverage[tail] = (tail, head)
    grouped, seen = {}, set()
    for c in rows:
        if not isinstance(c, PauseCue):
            raise ValueError("expected PauseCue")
        nonblank(c.cue_id, "cue_id")
        nonblank(c.utterance_id, "utterance_id")
        nonblank(c.reason, "pause reason")
        if c.cue_id in seen or c.utterance_id not in by_id:
            raise ValueError("duplicate cue or unknown utterance")
        seen.add(c.cue_id)
        t = by_id[c.utterance_id]
        integer(c.boundary, "pause boundary")
        integer(c.duration_ms, "pause duration", 1)
        if c.boundary > len(t.words):
            raise ValueError("pause boundary outside utterance")
        if type(c.evidence_ids) is not tuple:
            raise ValueError("pause evidence must be immutable")
        identifiers(c.evidence_ids, "pause evidence")
        if not set(c.evidence_ids) <= set(t.utterance.evidence_ids):
            raise ValueError("pause evidence outside utterance grounding")
        original_key = (c.utterance_id, c.boundary)
        grouped.setdefault(aliases.get(original_key, original_key), []).append(c)
    slots = []
    for (uid, boundary), group in sorted(grouped.items(), key=lambda x: (positions[x[0][0]], x[0][1])):
        covered = coverage.get((uid, boundary), ((uid, boundary),))
        existing = 0
        for clip_id, edge in covered:
            t = by_id[clip_id]
            left = t.words[edge-1].end_ms if edge else 0
            right = t.words[edge].start_ms if edge < len(t.words) else t.duration_ms
            existing += right - left
        required = max(c.duration_ms for c in group)
        deficit = max(0, required-existing)
        estimated = speech.basis == "ESTIMATED_WPM"
        slots.append(PauseSlot(uid, boundary, required, existing,
            deficit if estimated else 0, 0 if estimated else deficit,
            tuple(sorted(c.cue_id for c in group)),
            tuple(sorted({e for c in group for e in c.evidence_ids})),
            tuple(sorted({o for c in group for o in by_id[c.utterance_id].utterance.objective_ids})), covered))
    canonical_cues = tuple(sorted(rows, key=lambda c: (positions[c.utterance_id], c.boundary, c.cue_id)))
    return PauseTimingPlan(speech.fingerprint(), policy_version, canonical_cues, tuple(slots))


def validate_pause_plan(speech, plan):
    if not isinstance(plan, PauseTimingPlan) or plan.speech_fingerprint != speech.fingerprint():
        raise ValueError("pause plan belongs to a different speech revision")
    expected = build_pause_timing(speech, plan.cues, plan.policy_version)
    if plan != expected or plan.fingerprint() != expected.fingerprint():
        raise ValueError("pause plan was edited or is inconsistent")
    return plan
