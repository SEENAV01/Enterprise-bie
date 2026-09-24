"""Shared immutable AUDIO contracts, owned by BIE-AUDIO-VO-001.

Offsets are half-open Python Unicode code-point offsets in unchanged source text.
No pronunciation plan is a certificate of audio, factual or educational quality.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import json
import re
import unicodedata
from typing import Any

ENGINE_VERSION = "bie-audio-preparation/1.0.0"


class AudioError(ValueError):
    def __init__(self, code: str, path: str = "", detail: str = "") -> None:
        self.code, self.path, self.detail = code, path, detail
        super().__init__(f"{code}:{path}:{detail}")


def text(value: Any, path: str, *, blank: bool = False, maximum: int = 100_000) -> str:
    if type(value) is not str or len(value) > maximum or (not blank and not value.strip()):
        raise AudioError("INVALID_TEXT", path)
    for char in value:
        if 0xD800 <= ord(char) <= 0xDFFF or (unicodedata.category(char) == "Cc" and char not in "\n\r\t"):
            raise AudioError("INVALID_TEXT_CODEPOINT", path)
    return value


def integer(value: Any, path: str, low: int = 0, high: int = 1_000_000) -> int:
    if type(value) is not int or not low <= value <= high:
        raise AudioError("INVALID_INTEGER", path)
    return value


def digest(value: Any, path: str) -> str:
    if type(value) is not str or not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise AudioError("INVALID_DIGEST", path)
    return value


def locale(value: Any) -> str:
    # Deliberately bounded language-tag syntax, not a complete BCP47 validator.
    if type(value) is not str or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z]{2})?", value):
        raise AudioError("INVALID_LOCALE", "language")
    return value


def ids(values: Any, path: str, *, empty: bool = False) -> tuple[str, ...]:
    if type(values) is not tuple or (not values and not empty) or len(values) > 1000:
        raise AudioError("INVALID_IDENTIFIERS", path)
    for value in values:
        text(value, path, maximum=512)
    if len(values) != len(set(values)):
        raise AudioError("DUPLICATE_IDENTIFIER", path)
    return values


def canonical(value: Any) -> str:
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
                          default=lambda item: asdict(item) if hasattr(item, "__dataclass_fields__") else (_ for _ in ()).throw(TypeError(type(item).__name__)))
    except (TypeError, ValueError) as exc:
        raise AudioError("UNSERIALIZABLE") from exc


def fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def text_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def cluster_boundary(raw: str, index: int) -> bool:
    """Conservative protected-boundary check; not full UAX29 conformance."""
    if index <= 0 or index >= len(raw):
        return True
    a, b = raw[index - 1], raw[index]
    return not ((a == "\r" and b == "\n") or a in "\u200c\u200d" or b in "\u200c\u200d" or
        unicodedata.category(b).startswith("M") or 0xFE00 <= ord(b) <= 0xFE0F or
        0x1F3FB <= ord(b) <= 0x1F3FF or
        (0x1F1E6 <= ord(a) <= 0x1F1FF and 0x1F1E6 <= ord(b) <= 0x1F1FF))


@dataclass(frozen=True, slots=True)
class Annotation:
    """Explicit interpretation of one source span; no generated offsets accepted."""
    start: int
    end: int
    surface: str
    kind: str                    # math | symbol | acronym | term | verbatim
    role: str = ""               # symbol semantic role, math format='latex'
    rule_id: str = ""            # source-bound lexicon rule when explicitly selected
    source_refs: tuple[str, ...] = ()

    def validate(self, raw: str) -> None:
        integer(self.start, "annotation.start", high=len(raw))
        integer(self.end, "annotation.end", 1, len(raw))
        if self.end <= self.start or raw[self.start:self.end] != self.surface:
            raise AudioError("ANNOTATION_SOURCE_MISMATCH", str(self.start))
        if not cluster_boundary(raw, self.start) or not cluster_boundary(raw, self.end):
            raise AudioError("ANNOTATION_CLUSTER_SPLIT", str(self.start))
        if self.kind not in ("math", "symbol", "acronym", "term", "verbatim"):
            raise AudioError("ANNOTATION_KIND", self.kind)
        text(self.role, "annotation.role", blank=True, maximum=128)
        text(self.rule_id, "annotation.rule_id", blank=True, maximum=512)
        ids(self.source_refs, "annotation.source_refs")


@dataclass(frozen=True, slots=True)
class NarrationBlock:
    block_id: str
    scene_id: str
    segment_id: str
    voice_id: str
    language: str
    domain: str
    raw_text: str
    evidence_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    upstream_fingerprint: str
    annotations: tuple[Annotation, ...] = ()
    review_reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in ("block_id", "scene_id", "segment_id", "voice_id", "domain"):
            text(getattr(self, name), name, maximum=512)
        locale(self.language)
        text(self.raw_text, "raw_text")
        ids(self.evidence_ids, "evidence_ids")
        ids(self.objective_ids, "objective_ids")
        ids(self.review_reasons, "review_reasons", empty=True)
        digest(self.upstream_fingerprint, "upstream_fingerprint")
        if type(self.annotations) is not tuple or len(self.annotations) > 2000:
            raise AudioError("INVALID_ANNOTATIONS", self.block_id)
        previous = 0
        for annotation in self.annotations:
            if type(annotation) is not Annotation:
                raise AudioError("INVALID_ANNOTATION", self.block_id)
            annotation.validate(self.raw_text)
            if annotation.start < previous:
                raise AudioError("OVERLAPPING_ANNOTATIONS", self.block_id)
            previous = annotation.end


@dataclass(frozen=True, slots=True)
class NarrationDocument:
    document_id: str
    lesson_id: str
    script_fingerprint: str
    blocks: tuple[NarrationBlock, ...]
    revision: int = 1

    def validate(self) -> None:
        text(self.document_id, "document_id", maximum=512)
        text(self.lesson_id, "lesson_id", maximum=512)
        digest(self.script_fingerprint, "script_fingerprint")
        integer(self.revision, "revision", 1)
        if type(self.blocks) is not tuple or not self.blocks or len(self.blocks) > 1000:
            raise AudioError("INVALID_BLOCKS")
        seen, closed_scenes, previous_scene, total = set(), set(), None, 0
        for block in self.blocks:
            if type(block) is not NarrationBlock:
                raise AudioError("INVALID_BLOCK")
            block.validate()
            if block.block_id in seen:
                raise AudioError("DUPLICATE_BLOCK", block.block_id)
            seen.add(block.block_id)
            total += len(block.raw_text)
            if block.scene_id != previous_scene:
                if block.scene_id in closed_scenes:
                    raise AudioError("NONCONTIGUOUS_SCENE", block.scene_id)
                if previous_scene is not None:
                    closed_scenes.add(previous_scene)
                previous_scene = block.scene_id
        if total > 1_000_000:
            raise AudioError("DOCUMENT_LIMIT")

    @property
    def identity(self) -> str:
        self.validate()
        return fingerprint(self)


def document_from_dict(raw: dict) -> NarrationDocument:
    """Strict JSON ingress: reject unknown keys rather than silently drop them."""
    if type(raw) is not dict or set(raw) != {"document_id", "lesson_id", "script_fingerprint", "blocks", "revision"}:
        raise AudioError("DOCUMENT_KEYS")
    if type(raw["blocks"]) is not list:
        raise AudioError("INVALID_BLOCKS")
    blocks = []
    fields = set(NarrationBlock.__dataclass_fields__)
    afields = set(Annotation.__dataclass_fields__)
    for value in raw["blocks"]:
        if type(value) is not dict or set(value) != fields:
            raise AudioError("BLOCK_KEYS")
        value = dict(value)
        for key in ("evidence_ids", "objective_ids", "review_reasons", "annotations"):
            if type(value[key]) is not list:
                raise AudioError("BLOCK_COLLECTION_TYPE", key)
        annotations = []
        for annotation in value["annotations"]:
            if type(annotation) is not dict or set(annotation) != afields or type(annotation["source_refs"]) is not list:
                raise AudioError("ANNOTATION_KEYS")
            annotations.append(Annotation(**{**annotation, "source_refs": tuple(annotation["source_refs"])}))
        value["annotations"] = tuple(annotations)
        for key in ("evidence_ids", "objective_ids", "review_reasons"):
            value[key] = tuple(value[key])
        blocks.append(NarrationBlock(**value))
    doc = NarrationDocument(**{**raw, "blocks": tuple(blocks)})
    doc.validate()
    return doc


def from_director(utterances: tuple, *, document_id: str, lesson_id: str,
                  expected_script_fingerprint: str, domains: dict[str, str],
                  annotations: dict[str, tuple[Annotation, ...]] | None = None,
                  revision: int = 1) -> NarrationDocument:
    """Adopt actual canonical DIR SpeechUtterance, never script.text_intent.

    Acceptance and estimated durations are intentionally not synthesized here.
    Caller-supplied source references remain claims needing upstream source QA.
    """
    from bie.director.speech_timing import SpeechUtterance, _validate_inputs
    if type(utterances) is not tuple or not utterances:
        raise AudioError("DIRECTOR_UTTERANCES_REQUIRED")
    if any(type(u) is not SpeechUtterance for u in utterances):
        raise AudioError("DIRECTOR_CONTRACT_REQUIRED")
    _validate_inputs(utterances)
    digest(expected_script_fingerprint, "expected_script_fingerprint")
    if any(u.script_fingerprint != expected_script_fingerprint for u in utterances):
        raise AudioError("STALE_SCRIPT")
    if type(domains) is not dict or set(domains) != {u.utterance_id for u in utterances}:
        raise AudioError("DOMAIN_COVERAGE")
    annotations = {} if annotations is None else annotations
    if type(annotations) is not dict or not set(annotations) <= set(domains):
        raise AudioError("ANNOTATION_BLOCK_COVERAGE")
    blocks = tuple(NarrationBlock(u.utterance_id, u.scene_id, u.segment_id, u.voice_id,
        u.language, domains[u.utterance_id], u.text, u.evidence_ids, u.objective_ids,
        u.fingerprint(), annotations.get(u.utterance_id, ()), u.review_reasons) for u in utterances)
    doc = NarrationDocument(document_id, lesson_id, expected_script_fingerprint, blocks, revision)
    doc.validate()
    return doc


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    block_id: str
    start: int
    end: int
    detail: str
    owner_task: str
    severity: str = "REVIEW_REQUIRED"
