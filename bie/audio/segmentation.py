"""AUDIO-VO-001: lossless segmentation of actual canonical DIR utterances.

Provider-sized units are not lesson limits. All characters, source references,
explicit ordering and pause ownership survive. No word-time measurements exist here.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from bisect import bisect_right
from bie.director.speech_timing import SpeechUtterance, _validate_inputs, utterances_from_script
from bie.director.script_plan import validate_script_plan
from .common import AudioError, boundary, digest, fingerprint, integer, locale, refs, text


@dataclass(frozen=True)
class SegmentPolicy:
    version: str = "bie-audio-segmentation/1"
    max_chars: int = 800
    max_utf8_bytes: int = 3200
    max_segments: int = 10000
    abbreviations: tuple[str, ...] = ("Dr.", "Mr.", "Mrs.", "Ms.", "Prof.", "e.g.", "i.e.", "vs.", "Fig.")

    def __post_init__(self):
        if self.version != "bie-audio-segmentation/1":
            raise AudioError("UNSUPPORTED_SEGMENT_POLICY")
        integer(self.max_chars, "max_chars", 8, 20000)
        integer(self.max_utf8_bytes, "max_utf8_bytes", 16, 80000)
        integer(self.max_segments, "max_segments", 1, 100000)
        refs(self.abbreviations, "abbreviations", False)


@dataclass(frozen=True)
class ProtectedSpan:
    utterance_id: str
    start: int
    end: int
    surface: str
    utterance_fingerprint: str
    kind: str = "verbatim"

    def __post_init__(self):
        text(self.utterance_id, "utterance_id", 2048)
        integer(self.start, "span start")
        integer(self.end, "span end", 1)
        text(self.surface, "protected text", 20000)
        digest(self.utterance_fingerprint)
        if self.kind not in ("verbatim", "math", "term", "symbol", "acronym") or self.end <= self.start:
            raise AudioError("INVALID_PROTECTED_SPAN")


@dataclass(frozen=True)
class Pause:
    utterance_id: str
    offset: int
    milliseconds: int
    source_refs: tuple[str, ...]

    def __post_init__(self):
        text(self.utterance_id, "pause utterance", 2048)
        integer(self.offset, "pause offset", 1)
        integer(self.milliseconds, "pause ms", 0, 3600000)
        refs(self.source_refs, "pause evidence")


@dataclass(frozen=True)
class NarrationSegment:
    segment_id: str
    utterance_id: str
    utterance_fingerprint: str
    script_fingerprint: str
    scene_id: str
    voice_id: str
    language: str
    start_char: int
    end_char: int
    display_text: str
    evidence_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    review_reasons: tuple[str, ...]
    pause_after_ms: int
    pause_refs: tuple[str, ...]


@dataclass(frozen=True)
class SegmentationPlan:
    input_fingerprint: str
    policy: SegmentPolicy
    protected: tuple[ProtectedSpan, ...]
    pauses: tuple[Pause, ...]
    segments: tuple[NarrationSegment, ...]
    accepted: bool = False
    audio_generated: bool = False

    def fingerprint(self) -> str:
        return fingerprint(self)


def _sentences(s: str, policy: SegmentPolicy) -> set[int]:
    cuts = {len(s)}
    for m in re.finditer(r"[.!?।؟](?:[\"'”’)\]]*)(?:\s+|$)|\n\s*\n", s):
        point = m.start()
        prefix = s[max(0,point-max((len(a) for a in policy.abbreviations),default=64)-64):point+1]
        if s[point] == "." and (any(prefix.endswith(x) for x in policy.abbreviations)
                or re.search(r"(?:\b[A-Za-z]\.){1,}$", prefix)):
            continue
        cuts.add(m.end())
    return cuts


def split_narration(utterances: tuple[SpeechUtterance, ...], *, policy: SegmentPolicy = SegmentPolicy(),
                    protected: tuple[ProtectedSpan, ...] = (), pauses: tuple[Pause, ...] = ()) -> SegmentationPlan:
    if type(utterances) is not tuple or not 1 <= len(utterances) <= 10000 or type(policy) is not SegmentPolicy:
        raise AudioError("INVALID_SEGMENTATION_INPUT")
    if type(protected) is not tuple or type(pauses) is not tuple or len(protected) + len(pauses) > 100000:
        raise AudioError("INVALID_SPAN_COLLECTION")
    for u in utterances:
        if type(u) is not SpeechUtterance:
            raise AudioError("CANONICAL_UTTERANCE_REQUIRED")
        text(u.text, "narration", 1000000)
        locale(u.language)
    if sum(len(u.text) for u in utterances) > 5000000:
        raise AudioError("NARRATION_RESOURCE_BUDGET")
    _validate_inputs(utterances)
    by_id = {u.utterance_id: u for u in utterances}
    grouped: dict[str, list[ProtectedSpan]] = {k: [] for k in by_id}
    for span in protected:
        if type(span) is not ProtectedSpan or span.utterance_id not in by_id:
            raise AudioError("UNKNOWN_PROTECTED_UTTERANCE")
        u = by_id[span.utterance_id]
        if span.utterance_fingerprint != u.fingerprint():
            raise AudioError("STALE_PROTECTED_SPAN")
        if span.end > len(u.text) or u.text[span.start:span.end] != span.surface:
            raise AudioError("PROTECTED_TEXT_MISMATCH")
        if not boundary(u.text, span.start) or not boundary(u.text, span.end):
            raise AudioError("GRAPHEME_BOUNDARY")
        grouped[span.utterance_id].append(span)
    for spans in grouped.values():
        spans.sort(key=lambda x: (x.start, x.end))
        if any(b.start < a.end for a,b in zip(spans,spans[1:])):
            raise AudioError("OVERLAPPING_PROTECTED_SPANS")
    pause_index = {}
    for p in pauses:
        if type(p) is not Pause or p.utterance_id not in by_id:
            raise AudioError("UNKNOWN_PAUSE_UTTERANCE")
        u = by_id[p.utterance_id]
        if p.offset > len(u.text) or not boundary(u.text, p.offset):
            raise AudioError("PAUSE_BOUNDARY")
        if p.offset < len(u.text) and not (u.text[p.offset-1].isspace() or u.text[p.offset-1] in ".!?।؟;:"):
            raise AudioError("PAUSE_SPLITS_TOKEN")
        if any(s.start < p.offset < s.end for s in grouped[u.utterance_id]):
            raise AudioError("PAUSE_SPLITS_PROTECTED")
        key = (p.utterance_id,p.offset)
        if key in pause_index:
            raise AudioError("DUPLICATE_PAUSE")
        pause_index[key] = p
    output = []
    for u in utterances:
        s = u.text
        spans = grouped[u.utterance_id]
        span_starts = [x.start for x in spans]
        def safe(i):
            j = bisect_right(span_starts,i)-1
            return boundary(s,i) and not (j>=0 and spans[j].start<i<spans[j].end)
        sentence = sorted(i for i in _sentences(s,policy) if safe(i))
        whitespace = sorted(m.end() for m in re.finditer(r"\s+",s) if safe(m.end()))
        pauses_here = sorted(p.offset for p in pauses if p.utterance_id == u.utterance_id)
        start = 0
        while start < len(s):
            pause_position = bisect_right(pauses_here,start)
            forced = pauses_here[pause_position] if pause_position<len(pauses_here) else len(s)
            cap = min(forced,start+policy.max_chars)
            # Byte prefix accounting avoids quadratic repeated encoding.
            size = 0
            end = start
            while end < cap:
                width = len(s[end].encode("utf-8"))
                if size+width > policy.max_utf8_bytes:
                    break
                size += width
                end += 1
            candidate_index = bisect_right(sentence,end)-1
            best_sentence = sentence[candidate_index] if candidate_index>=0 and sentence[candidate_index]>start else None
            if forced <= end and safe(forced):
                stop = forced
            elif best_sentence is not None:
                stop = best_sentence
            else:
                candidate_index = bisect_right(whitespace,end)-1
                best_space = whitespace[candidate_index] if candidate_index>=0 and whitespace[candidate_index]>start else None
                if best_space is None:
                    raise AudioError("INDIVISIBLE_SPAN_EXCEEDS_PROVIDER_LIMIT", f"{u.utterance_id}:{start}")
                stop = best_space
            piece = s[start:stop]
            if not piece.strip():
                raise AudioError("WHITESPACE_ONLY_SEGMENT", f"{u.utterance_id}:{start}")
            pause = pause_index.get((u.utterance_id,stop))
            sid = "audio-segment:" + fingerprint((u.fingerprint(),start,stop,policy))[7:]
            output.append(NarrationSegment(sid,u.utterance_id,u.fingerprint(),u.script_fingerprint,
                u.scene_id,u.voice_id,u.language,start,stop,piece,u.evidence_ids,u.objective_ids,u.review_reasons,
                pause.milliseconds if pause else 0,pause.source_refs if pause else ()))
            if len(output) > policy.max_segments:
                raise AudioError("SEGMENT_RESOURCE_BUDGET")
            start = stop
    return SegmentationPlan(fingerprint(utterances),policy,
        tuple(sorted(protected,key=lambda x:(x.utterance_id,x.start))),
        tuple(sorted(pauses,key=lambda x:(x.utterance_id,x.offset))),tuple(output))


def from_director_script(script, drafts, segment_order, *, language="en", **options):
    """Use the same realized utterance producer as canonical DIR; never narrate intent."""
    validate_script_plan(script)
    if type(drafts) is not tuple or type(segment_order) is not tuple:
        raise AudioError("IMMUTABLE_DIRECTOR_INPUT_REQUIRED")
    utterances = tuple(utterances_from_script(script,drafts,segment_order,language))
    return utterances, split_narration(utterances,**options)


def validate_plan(plan: SegmentationPlan, utterances: tuple[SpeechUtterance, ...]) -> SegmentationPlan:
    if type(plan) is not SegmentationPlan:
        raise AudioError("SEGMENTATION_PLAN_REQUIRED")
    expected = split_narration(utterances,policy=plan.policy,protected=plan.protected,pauses=plan.pauses)
    if plan != expected:
        raise AudioError("STALE_OR_EDITED_SEGMENTATION")
    return plan
