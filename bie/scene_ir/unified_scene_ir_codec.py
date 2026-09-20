from __future__ import annotations
import json
from .unified_scene_ir_contract import UnifiedElement, UnifiedTrack, UnifiedSceneIRDocument, UnifiedSceneIRError

class SceneIRCodecError(ValueError): pass

ROOT_FIELDS = {
    "scene_id","schema_version","title","duration_ms","elements","tracks",
    "source_refs","reasoning_refs","layout","events","narration_cues","interaction_cues",
    "interaction_bindings","state_bindings","simulation_controls","accessibility_metadata",
    "capability_requests","planned_fallbacks","compiler_capabilities","metadata",
    "upstream_revision","fingerprint","review_required","accepted"
}
ELEMENT_FIELDS = {"element_id","element_type","props","source_refs","reasoning_refs","accessibility","normalized_box"}
TRACK_FIELDS = {"track_id","element_id","action","start_ms","end_ms","parameters","source_refs","reasoning_refs"}

def _unknown(obj, allowed, path):
    extra = set(obj) - set(allowed)
    if extra:
        raise SceneIRCodecError(f"unknown field(s) at {path}: {sorted(extra)}")

def decode_scene_ir(payload):
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception as e:
            raise SceneIRCodecError("invalid JSON") from e
    if not isinstance(payload, dict):
        raise SceneIRCodecError("SceneIR payload must be object")
    _unknown(payload, ROOT_FIELDS, "$")
    if payload.get("accepted") not in (None, False):
        raise SceneIRCodecError("accepted=true cannot be decoded")
    if payload.get("review_required") not in (None, True):
        raise SceneIRCodecError("review_required must remain true")

    elems=[]
    for i,e in enumerate(payload.get("elements",())):
        if not isinstance(e, dict):
            raise SceneIRCodecError(f"element {i} must be object")
        _unknown(e, ELEMENT_FIELDS, f"$.elements[{i}]")
        elems.append(UnifiedElement(
            e["element_id"],e["element_type"],e.get("props",{}),
            tuple(e.get("source_refs",())),tuple(e.get("reasoning_refs",())),
            e.get("accessibility",{}),e.get("normalized_box")
        ))

    tracks=[]
    for i,t in enumerate(payload.get("tracks",())):
        if not isinstance(t, dict):
            raise SceneIRCodecError(f"track {i} must be object")
        _unknown(t, TRACK_FIELDS, f"$.tracks[{i}]")
        tracks.append(UnifiedTrack(
            t["track_id"],t["element_id"],t["action"],t["start_ms"],t["end_ms"],
            t.get("parameters",{}),tuple(t.get("source_refs",())),tuple(t.get("reasoning_refs",()))
        ))

    try:
        return UnifiedSceneIRDocument(
            scene_id=payload["scene_id"],schema_version=payload["schema_version"],
            title=payload["title"],duration_ms=payload["duration_ms"],
            elements=tuple(elems),tracks=tuple(tracks),
            source_refs=tuple(payload.get("source_refs",())),
            reasoning_refs=tuple(payload.get("reasoning_refs",())),
            layout=payload.get("layout",{}),events=tuple(payload.get("events",())),
            narration_cues=tuple(payload.get("narration_cues",())),
            interaction_cues=tuple(payload.get("interaction_cues",())),
            interaction_bindings=tuple(payload.get("interaction_bindings",())),
            state_bindings=tuple(payload.get("state_bindings",())),
            simulation_controls=tuple(payload.get("simulation_controls",())),
            accessibility_metadata=tuple(payload.get("accessibility_metadata",())),
            capability_requests=tuple(payload.get("capability_requests",())),
            planned_fallbacks=tuple(payload.get("planned_fallbacks",())),
            compiler_capabilities=tuple(payload.get("compiler_capabilities",())),
            metadata=payload.get("metadata",{}),
            upstream_revision=payload.get("upstream_revision",1),
            fingerprint=payload.get("fingerprint",""),
        )
    except KeyError as e:
        raise SceneIRCodecError(f"missing required field: {e.args[0]}") from e
    except UnifiedSceneIRError as e:
        raise SceneIRCodecError(str(e)) from e

def encode_scene_ir(document):
    return json.dumps(document.to_dict(),sort_keys=True,separators=(",",":"),ensure_ascii=False)

def roundtrip_scene_ir(document):
    encoded=encode_scene_ir(document)
    decoded=decode_scene_ir(encoded)
    if decoded.fingerprint != document.fingerprint:
        raise SceneIRCodecError("round-trip fingerprint mismatch")
    return decoded
