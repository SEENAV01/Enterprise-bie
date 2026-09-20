from __future__ import annotations
from dataclasses import dataclass, field, asdict
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping, Iterable
import json

class UnifiedSceneIRError(ValueError):
    pass

def _tok(v, name):
    if not isinstance(v, str) or not v.strip():
        raise UnifiedSceneIRError(f"{name} must be nonblank")
    return v.strip()

def _freeze(v):
    if isinstance(v, Mapping):
        return MappingProxyType({str(k): _freeze(v[k]) for k in sorted(v, key=str)})
    if isinstance(v, list):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, tuple):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, set):
        return tuple(sorted(_freeze(x) for x in v))
    return v

def _thaw(v):
    if isinstance(v, Mapping):
        return {str(k): _thaw(v[k]) for k in sorted(v, key=str)}
    if isinstance(v, tuple):
        return [_thaw(x) for x in v]
    return v

def _fp(v):
    raw = json.dumps(_thaw(v), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class UnifiedElement:
    element_id: str
    element_type: str
    props: Mapping[str, Any]
    source_refs: tuple[str, ...]
    reasoning_refs: tuple[str, ...]
    accessibility: Mapping[str, Any] = field(default_factory=dict)
    normalized_box: Mapping[str, Any] | None = None

    def __post_init__(self):
        object.__setattr__(self, "element_id", _tok(self.element_id, "element_id"))
        object.__setattr__(self, "element_type", _tok(self.element_type, "element_type"))
        if not self.source_refs or not self.reasoning_refs:
            raise UnifiedSceneIRError("element source/reasoning lineage required")
        object.__setattr__(self, "source_refs", tuple(_tok(x, "source_ref") for x in self.source_refs))
        object.__setattr__(self, "reasoning_refs", tuple(_tok(x, "reasoning_ref") for x in self.reasoning_refs))
        object.__setattr__(self, "props", _freeze(dict(self.props)))
        object.__setattr__(self, "accessibility", _freeze(dict(self.accessibility)))
        if self.normalized_box is not None:
            box = dict(self.normalized_box)
            for k in ("x","y","width","height"):
                if k not in box:
                    raise UnifiedSceneIRError("normalized_box requires x,y,width,height")
                v = box[k]
                if isinstance(v, bool) or not isinstance(v, (int,float)):
                    raise UnifiedSceneIRError("normalized_box numeric values required")
            x,y,w,h = map(float, (box["x"],box["y"],box["width"],box["height"]))
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > 1.0+1e-9 or y+h > 1.0+1e-9:
                raise UnifiedSceneIRError("normalized_box outside canvas")
            object.__setattr__(self, "normalized_box", _freeze(box))

@dataclass(frozen=True)
class UnifiedTrack:
    track_id: str
    element_id: str
    action: str
    start_ms: int
    end_ms: int
    parameters: Mapping[str, Any]
    source_refs: tuple[str, ...]
    reasoning_refs: tuple[str, ...]

    def __post_init__(self):
        for f in ("track_id","element_id","action"):
            object.__setattr__(self, f, _tok(getattr(self,f), f))
        if isinstance(self.start_ms,bool) or not isinstance(self.start_ms,int) or self.start_ms < 0:
            raise UnifiedSceneIRError("start_ms invalid")
        if isinstance(self.end_ms,bool) or not isinstance(self.end_ms,int) or self.end_ms <= self.start_ms:
            raise UnifiedSceneIRError("end_ms invalid")
        if not self.source_refs or not self.reasoning_refs:
            raise UnifiedSceneIRError("track source/reasoning lineage required")
        object.__setattr__(self, "parameters", _freeze(dict(self.parameters)))
        object.__setattr__(self, "source_refs", tuple(_tok(x, "source_ref") for x in self.source_refs))
        object.__setattr__(self, "reasoning_refs", tuple(_tok(x, "reasoning_ref") for x in self.reasoning_refs))

@dataclass(frozen=True)
class UnifiedSceneIRDocument:
    scene_id: str
    schema_version: str
    title: str
    duration_ms: int
    elements: tuple[UnifiedElement, ...]
    tracks: tuple[UnifiedTrack, ...]
    source_refs: tuple[str, ...]
    reasoning_refs: tuple[str, ...]
    layout: Mapping[str, Any] = field(default_factory=dict)
    events: tuple[Mapping[str, Any], ...] = ()
    narration_cues: tuple[Mapping[str, Any], ...] = ()
    interaction_cues: tuple[Mapping[str, Any], ...] = ()
    interaction_bindings: tuple[Mapping[str, Any], ...] = ()
    state_bindings: tuple[Mapping[str, Any], ...] = ()
    simulation_controls: tuple[Mapping[str, Any], ...] = ()
    accessibility_metadata: tuple[Mapping[str, Any], ...] = ()
    capability_requests: tuple[Mapping[str, Any], ...] = ()
    planned_fallbacks: tuple[Mapping[str, Any], ...] = ()
    compiler_capabilities: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    upstream_revision: int = 1
    fingerprint: str = ""
    review_required: bool = True
    accepted: bool = False

    def __post_init__(self):
        object.__setattr__(self, "scene_id", _tok(self.scene_id, "scene_id"))
        object.__setattr__(self, "title", _tok(self.title, "title"))
        if self.schema_version != "1.0.0":
            raise UnifiedSceneIRError("unsupported schema_version")
        if isinstance(self.duration_ms,bool) or not isinstance(self.duration_ms,int) or self.duration_ms < 1:
            raise UnifiedSceneIRError("duration_ms invalid")
        if isinstance(self.upstream_revision,bool) or not isinstance(self.upstream_revision,int) or self.upstream_revision < 1:
            raise UnifiedSceneIRError("upstream_revision invalid")
        if not self.source_refs or not self.reasoning_refs:
            raise UnifiedSceneIRError("scene lineage required")

        elements = tuple(self.elements)
        tracks = tuple(self.tracks)
        if not elements:
            raise UnifiedSceneIRError("at least one element required")
        if len({e.element_id for e in elements}) != len(elements):
            raise UnifiedSceneIRError("duplicate element id")
        valid = {e.element_id for e in elements}
        if len({t.track_id for t in tracks}) != len(tracks):
            raise UnifiedSceneIRError("duplicate track id")
        for t in tracks:
            if t.element_id not in valid:
                raise UnifiedSceneIRError("track references unknown element")
            if t.end_ms > self.duration_ms:
                raise UnifiedSceneIRError("track exceeds scene duration")

        object.__setattr__(self, "elements", elements)
        object.__setattr__(self, "tracks", tracks)
        object.__setattr__(self, "source_refs", tuple(_tok(x,"source_ref") for x in self.source_refs))
        object.__setattr__(self, "reasoning_refs", tuple(_tok(x,"reasoning_ref") for x in self.reasoning_refs))
        object.__setattr__(self, "layout", _freeze(dict(self.layout)))
        for name in (
            "events","narration_cues","interaction_cues","interaction_bindings",
            "state_bindings","simulation_controls","accessibility_metadata",
            "capability_requests","planned_fallbacks"
        ):
            object.__setattr__(self, name, tuple(_freeze(dict(x)) for x in getattr(self,name)))
        object.__setattr__(self, "compiler_capabilities", tuple(_tok(x,"compiler_capability") for x in self.compiler_capabilities))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata)))

        calc = _fp(self.to_dict(include_fingerprint=False))
        if self.fingerprint and self.fingerprint != calc:
            raise UnifiedSceneIRError("fingerprint mismatch")
        object.__setattr__(self, "fingerprint", calc)
        object.__setattr__(self, "review_required", True)
        object.__setattr__(self, "accepted", False)

    def to_dict(self, include_fingerprint=True):
        d = {
            "scene_id": self.scene_id,
            "schema_version": self.schema_version,
            "title": self.title,
            "duration_ms": self.duration_ms,
            "elements": [
                {
                    "element_id": e.element_id,
                    "element_type": e.element_type,
                    "props": _thaw(e.props),
                    "source_refs": list(e.source_refs),
                    "reasoning_refs": list(e.reasoning_refs),
                    "accessibility": _thaw(e.accessibility),
                    "normalized_box": None if e.normalized_box is None else _thaw(e.normalized_box),
                } for e in self.elements
            ],
            "tracks": [
                {
                    "track_id": t.track_id,
                    "element_id": t.element_id,
                    "action": t.action,
                    "start_ms": t.start_ms,
                    "end_ms": t.end_ms,
                    "parameters": _thaw(t.parameters),
                    "source_refs": list(t.source_refs),
                    "reasoning_refs": list(t.reasoning_refs),
                } for t in self.tracks
            ],
            "source_refs": list(self.source_refs),
            "reasoning_refs": list(self.reasoning_refs),
            "layout": _thaw(self.layout),
            "events": [_thaw(x) for x in self.events],
            "narration_cues": [_thaw(x) for x in self.narration_cues],
            "interaction_cues": [_thaw(x) for x in self.interaction_cues],
            "interaction_bindings": [_thaw(x) for x in self.interaction_bindings],
            "state_bindings": [_thaw(x) for x in self.state_bindings],
            "simulation_controls": [_thaw(x) for x in self.simulation_controls],
            "accessibility_metadata": [_thaw(x) for x in self.accessibility_metadata],
            "capability_requests": [_thaw(x) for x in self.capability_requests],
            "planned_fallbacks": [_thaw(x) for x in self.planned_fallbacks],
            "compiler_capabilities": list(self.compiler_capabilities),
            "metadata": _thaw(self.metadata),
            "upstream_revision": self.upstream_revision,
            "review_required": True,
            "accepted": False,
        }
        if include_fingerprint:
            d["fingerprint"] = self.fingerprint
        return d
