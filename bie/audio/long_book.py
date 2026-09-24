"""H7: deterministic bounded long-book AUDIO segment planning and resume decisions.

This module schedules prepared speech segments only. It does not create a second
execution queue, synthesize speech, or claim product/audio acceptance.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass

from .acoustic_contract import plain
from .common import AudioError, fingerprint, integer, text
from .pipeline_profile import validate_profile
from .pipeline_stems import canonicalize_stem_specs, stems_fingerprint
from .segment_cache import SegmentCachePolicy, _build_segment_identity_validated
from .speech_contract import SpeechPlan


@dataclass(frozen=True)
class LongBookPolicy:
    revision: str = "audio-h7-long-book-v1"
    max_segments_per_batch: int = 16
    max_spoken_chars_per_batch: int = 12000
    max_total_segments: int = 10000
    def __post_init__(self):
        text(self.revision, "long book policy", 160)
        integer(self.max_segments_per_batch, "segments per batch", 1, 64)
        integer(self.max_spoken_chars_per_batch, "spoken chars per batch", 64, 200000)
        integer(self.max_total_segments, "total segments", 1, 100000)


@dataclass(frozen=True)
class SegmentWorkItem:
    order: int
    segment_id: str
    identity_fingerprint: str
    spoken_chars: int
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class SegmentBatch:
    index: int
    item_fingerprints: tuple[str, ...]
    spoken_chars: int


@dataclass(frozen=True)
class LongBookPlan:
    policy: LongBookPolicy
    preparation_profile: str
    speech_plan_fingerprint: str
    profile_fingerprint: str
    mix_stems_fingerprint: str
    items: tuple[SegmentWorkItem, ...]
    batches: tuple[SegmentBatch, ...]
    fingerprint: str


def build_long_book_plan(plan: SpeechPlan, *, profile, preparation_profile=None, mix_stems=None,
                         policy=LongBookPolicy(), cache_policy=SegmentCachePolicy()):
    if type(plan) is not SpeechPlan: raise AudioError("LONG_BOOK_SPEECH_PLAN_REQUIRED")
    if type(policy) is not LongBookPolicy or type(cache_policy) is not SegmentCachePolicy:
        raise AudioError("LONG_BOOK_POLICY_TYPE")
    profile = plain(profile); validate_profile(profile)
    preparation_profile = plan.profile if preparation_profile is None else preparation_profile
    if preparation_profile != plan.profile:
        raise AudioError("LONG_BOOK_PREPARATION_PROFILE_MISMATCH")
    if len(plan.segments) > policy.max_total_segments:
        raise AudioError("LONG_BOOK_TOTAL_SEGMENTS")
    stems = canonicalize_stem_specs([] if mix_stems is None else mix_stems)
    items=[]
    for order, segment in enumerate(plan.segments):
        spoken = len(segment.spoken_text)
        if spoken <= 0 or spoken > policy.max_spoken_chars_per_batch:
            raise AudioError("LONG_BOOK_SINGLE_SEGMENT_BUDGET")
        identity = _build_segment_identity_validated(segment, profile=profile, preparation_profile=preparation_profile,
                                                     mix_stems_fingerprint=stems_fingerprint(stems), policy=cache_policy)
        refs=tuple(sorted({ref for span in segment.spans for ref in span.source_refs}))
        items.append(SegmentWorkItem(order, segment.segment_id, identity["fingerprint"], spoken, refs))
    batches=[]; current=[]; chars=0
    def flush():
        nonlocal current, chars
        if current:
            batches.append(SegmentBatch(len(batches), tuple(x.identity_fingerprint for x in current), chars))
            current=[]; chars=0
    for item in items:
        if current and (len(current) >= policy.max_segments_per_batch or chars + item.spoken_chars > policy.max_spoken_chars_per_batch):
            flush()
        current.append(item); chars += item.spoken_chars
    flush()
    if tuple(fp for b in batches for fp in b.item_fingerprints) != tuple(i.identity_fingerprint for i in items):
        raise AudioError("LONG_BOOK_TRUNCATION_OR_REORDER")
    body={"schema_version":"bie.audio.long-book-plan/1", "policy":asdict(policy),
          "preparation_profile":preparation_profile, "speech_plan_fingerprint":plan.fingerprint(),
          "profile_fingerprint":profile["fingerprint"], "mix_stems_fingerprint":stems_fingerprint(stems),
          "items":[asdict(i) for i in items], "batches":[asdict(b) for b in batches]}
    return LongBookPlan(policy,preparation_profile,plan.fingerprint(),profile["fingerprint"],
                        stems_fingerprint(stems),tuple(items),tuple(batches),fingerprint(body))


def resume_long_book(plan: LongBookPlan, completed_fingerprints):
    if type(plan) is not LongBookPlan or type(completed_fingerprints) not in (set, frozenset):
        raise AudioError("LONG_BOOK_RESUME_INPUT")
    known={i.identity_fingerprint for i in plan.items}
    if not completed_fingerprints <= known:
        raise AudioError("LONG_BOOK_UNKNOWN_COMPLETION")
    reused=tuple(i.identity_fingerprint for i in plan.items if i.identity_fingerprint in completed_fingerprints)
    pending=tuple(i.identity_fingerprint for i in plan.items if i.identity_fingerprint not in completed_fingerprints)
    return {"plan_fingerprint":plan.fingerprint,"reused":reused,"pending":pending,
            "complete":not pending,"product_accepted":False}


def compare_long_book_plans(previous: LongBookPlan, current: LongBookPlan):
    if type(previous) is not LongBookPlan or type(current) is not LongBookPlan:
        raise AudioError("LONG_BOOK_COMPARE_INPUT")
    old={x.segment_id:x.identity_fingerprint for x in previous.items}
    new={x.segment_id:x.identity_fingerprint for x in current.items}
    shared=sorted(set(old)&set(new))
    return {"reused":tuple(s for s in shared if old[s]==new[s]),
            "invalidated":tuple(s for s in shared if old[s]!=new[s]),
            "added":tuple(sorted(set(new)-set(old))),
            "removed":tuple(sorted(set(old)-set(new))),
            "scope":"SELECTIVE_SEGMENT_REUSE_DECISION_NOT_EXECUTION_ACCEPTANCE",
            "product_accepted":False}
