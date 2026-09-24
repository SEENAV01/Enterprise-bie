"""BIE-AUDIO-VO-001: lossless, source-ordered and protected-span segmentation.

This is a conservative versioned engineering splitter, not universal linguistic
sentence segmentation or calibrated speech timing. Limits never drop text.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from bisect import bisect_right
import unicodedata
from .contracts import AudioError, NarrationDocument, fingerprint, integer, text_hash, cluster_boundary

ABBREVIATIONS = frozenset(("dr.", "mr.", "mrs.", "ms.", "prof.", "e.g.", "i.e.", "vs.", "fig.", "eq.", "no.", "sr.", "jr."))


@dataclass(frozen=True, slots=True)
class SegmentationPolicy:
    max_chars: int = 280
    max_utf8_bytes: int = 1200
    version: str = "bie-audio-segmentation/1"

    def validate(self) -> None:
        integer(self.max_chars, "max_chars", 16, 20_000)
        integer(self.max_utf8_bytes, "max_utf8_bytes", 32, 80_000)
        if self.version != "bie-audio-segmentation/1":
            raise AudioError("UNKNOWN_SEGMENTATION_POLICY")


@dataclass(frozen=True, slots=True)
class NarrationSegment:
    segment_id: str
    block_id: str
    scene_id: str
    voice_id: str
    language: str
    start_char: int
    end_char: int
    start_utf8: int
    end_utf8: int
    raw_text: str
    source_sha256: str
    evidence_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    review_reasons: tuple[str, ...]
    boundary_reason: str


@dataclass(frozen=True, slots=True)
class SegmentationPlan:
    document_fingerprint: str
    policy: SegmentationPolicy
    segments: tuple[NarrationSegment, ...]
    accepted: bool = False
    audio_generated: bool = False

    @property
    def identity(self) -> str:
        return fingerprint(self)


def delimited_math(text: str) -> tuple[tuple[int, int, str], ...]:
    """Discover explicit LaTeX delimiters; bare dollar currency is not inferred.

    $/$$ and backslash parentheses/brackets are supported. A solitary unescaped
    dollar is review-worthy and rejected rather than silently eaten as markup.
    """
    result, i = [], 0
    while i < len(text):
        if text.startswith(r"\$", i):
            i += 2
            continue
        opening = next((x for x in (r"\(", r"\[", "$$", "$") if text.startswith(x, i)), None)
        if opening is None:
            i += 1
            continue
        closing = {r"\(": r"\)", r"\[": r"\]", "$$": "$$", "$": "$"}[opening]
        j = i + len(opening)
        while j < len(text):
            if text.startswith(closing, j) and (j == 0 or text[j - 1] != "\\"):
                break
            j += 1
        if j >= len(text):
            raise AudioError("UNMATCHED_MATH_DELIMITER", str(i), "Use an explicit source annotation for currency/literal dollar.")
        end = j + len(closing)
        if not text[i + len(opening):j].strip():
            raise AudioError("EMPTY_MATH", str(i))
        result.append((i, end, text[i + len(opening):j]))
        i = end
    return tuple(result)


def safe_boundary(raw: str, index: int) -> bool:
    return cluster_boundary(raw, index)


def protected_ranges(block, extra=()):
    # Explicit annotations mask delimiter recognition (e.g. a literal $ price).
    ranges = [(a.start, a.end) for a in block.annotations]
    masked = list(block.raw_text)
    for a, b in ranges:
        masked[a:b] = " " * (b - a)
    ranges.extend((a, b) for a, b, _ in delimited_math("".join(masked)))
    for item in extra:
        if type(item) is not tuple or len(item) != 2:
            raise AudioError("PROTECTED_RANGE_SHAPE")
        a, b = item
        integer(a, "protected.start", 0, len(block.raw_text))
        integer(b, "protected.end", 1, len(block.raw_text))
        if a >= b or not safe_boundary(block.raw_text, a) or not safe_boundary(block.raw_text, b):
            raise AudioError("PROTECTED_RANGE_INVALID")
        ranges.append((a, b))
    merged = []
    for a, b in sorted(ranges):
        if merged and a < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    return tuple(merged)


def _candidates(raw: str, ranges):
    forbidden = set()
    for a, b in ranges:
        forbidden.update(range(a + 1, b))
    result = {len(raw): "BLOCK_END"}
    previous_space_end = 0
    for match in re.finditer(r"\s+", raw):
        end = match.end()
        prefix = raw[previous_space_end:match.start()]
        previous_space_end = end
        if end in forbidden or not safe_boundary(raw, end):
            continue
        last = re.search(r"\S+$", prefix)
        word = last.group().casefold() if last else ""
        reason = "WORD_BOUNDARY"
        trimmed = prefix.rstrip('\"\'”’)]}')
        if (trimmed.endswith(("!", "?", "।", "؟", "。", "！", "？")) or
                (trimmed.endswith(".") and word not in ABBREVIATIONS and
                 not re.fullmatch(r"(?:[a-z]\.)+", word))):
            reason = "SENTENCE_BOUNDARY"
        elif trimmed.endswith((",", ";", ":", "，", "；")):
            reason = "CLAUSE_BOUNDARY"
        elif "\n\n" in match.group() or "\r\n\r\n" in match.group():
            reason = "PARAGRAPH_BOUNDARY"
        result[end] = reason
    # Scripts with no spaces may break only after explicit sentence punctuation.
    for match in re.finditer(r"[。！？।؟]", raw):
        end = match.end()
        if end not in forbidden and safe_boundary(raw, end):
            result.setdefault(end, "SENTENCE_BOUNDARY")
    return sorted(result.items())


def segment_narration(document: NarrationDocument, policy=SegmentationPolicy(), *, protected=None) -> SegmentationPlan:
    document.validate()
    policy.validate()
    protected = {} if protected is None else protected
    if type(protected) is not dict or not set(protected) <= {b.block_id for b in document.blocks}:
        raise AudioError("PROTECTED_BLOCK_COVERAGE")
    doc_hash, out = document.identity, []
    for block in document.blocks:
        raw = block.raw_text
        ranges = protected_ranges(block, protected.get(block.block_id, ()))
        positions = _candidates(raw, ranges)
        byte_offsets = [0]
        for char in raw:
            byte_offsets.append(byte_offsets[-1] + len(char.encode("utf-8")))
        positions_only = [item[0] for item in positions]
        start = 0
        while start < len(raw):
            char_stop = min(len(raw), start + policy.max_chars,
                bisect_right(byte_offsets, byte_offsets[start] + policy.max_utf8_bytes) - 1)
            fitting = positions[bisect_right(positions_only, start):bisect_right(positions_only, char_stop)]
            if not fitting:
                raise AudioError("UNSPLITTABLE_NARRATION", block.block_id,
                    f"Protected expression/token at {start} exceeds configured per-segment budget; source retained, nothing published.")
            # Prefer a genuine sentence boundary; otherwise a clause, then word.
            natural = [p for p in fitting if p[1] in ("SENTENCE_BOUNDARY", "PARAGRAPH_BOUNDARY", "BLOCK_END")]
            clauses = [p for p in fitting if p[1] == "CLAUSE_BOUNDARY"]
            end, reason = (natural or clauses or fitting)[-1]
            fragment = raw[start:end]
            sid = "audseg:" + fingerprint((doc_hash, block.block_id, start, end, policy))[7:31]
            out.append(NarrationSegment(sid, block.block_id, block.scene_id, block.voice_id,
                block.language, start, end, byte_offsets[start], byte_offsets[end], fragment,
                text_hash(raw), block.evidence_ids, block.objective_ids, block.review_reasons, reason))
            start = end
    return SegmentationPlan(doc_hash, policy, tuple(out))


def verify_segments(plan: SegmentationPlan, document: NarrationDocument) -> None:
    document.validate()
    if type(plan) is not SegmentationPlan or plan.document_fingerprint != document.identity or plan.accepted is not False or plan.audio_generated is not False:
        raise AudioError("SEGMENT_PLAN_BINDING")
    plan.policy.validate()
    expected_order, actual_order = [b.block_id for b in document.blocks], []
    for block in document.blocks:
        rows = [s for s in plan.segments if s.block_id == block.block_id]
        if not rows or "".join(s.raw_text for s in rows) != block.raw_text:
            raise AudioError("SEGMENT_COVERAGE", block.block_id)
        cursor = 0
        for row in rows:
            if row.start_char != cursor or row.end_char <= cursor or row.raw_text != block.raw_text[cursor:row.end_char]:
                raise AudioError("SEGMENT_OFFSETS", block.block_id)
            if (row.source_sha256 != text_hash(block.raw_text) or row.scene_id != block.scene_id or
                row.voice_id != block.voice_id or row.language != block.language or
                row.evidence_ids != block.evidence_ids or row.objective_ids != block.objective_ids or
                row.review_reasons != block.review_reasons or
                row.start_utf8 != len(block.raw_text[:cursor].encode()) or
                row.end_utf8 != len(block.raw_text[:row.end_char].encode())):
                raise AudioError("SEGMENT_SOURCE_BINDING", block.block_id)
            if len(row.raw_text) > plan.policy.max_chars or len(row.raw_text.encode()) > plan.policy.max_utf8_bytes:
                raise AudioError("SEGMENT_BUDGET", block.block_id)
            if row.segment_id != "audseg:" + fingerprint((document.identity, block.block_id, cursor, row.end_char, plan.policy))[7:31]:
                raise AudioError("SEGMENT_IDENTITY", block.block_id)
            if not safe_boundary(block.raw_text, row.start_char) or not safe_boundary(block.raw_text, row.end_char):
                raise AudioError("SEGMENT_CLUSTER_SPLIT", block.block_id)
            if any(a.start < row.end_char < a.end for a in block.annotations):
                raise AudioError("SEGMENT_ANNOTATION_SPLIT", block.block_id)
            cursor = row.end_char
    for row in plan.segments:
        if not actual_order or row.block_id != actual_order[-1]:
            actual_order.append(row.block_id)
    if actual_order != expected_order:
        raise AudioError("SEGMENT_ORDER")
