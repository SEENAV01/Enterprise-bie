"""M1 explicit producer-motion admission; no legacy-contract reinterpretation.

JSON is not authority. The producer boundary installs a read-verified, scoped
snapshot; this pure validator compares the complete envelope against it. No
rendering, publishing, provider calls or recursive reduced selection occur here.
"""
from contextvars import ContextVar
from copy import deepcopy
import json
import math
from .animation_compiler_common import normalize_track, AnimationCompilerError
from .qa_common import digest

SCHEMA = "bie.comp-producer-motion/1"
PROFILE = "producer-motion-v1"
POLICY = "whole-item-visibility-inward-focus/1"
METADATA = "producer_motion"
EXACT_LAYOUT = "verified-visual-layout-v1"
FIXTURE_LAYOUT = "native-compiler-fixture-v1"
PAIRS = {("chart", "reveal"), ("diagram", "reveal"), ("diagram", "emphasize")}
VARIANTS = {"reveal": "whole-item-visibility-v1", "emphasize": "inward-two-tone-focus-v1"}
COMMON = frozenset({"semantic_effect", "easing", "director_animation_intent_id",
    "parent_visual_target_id", "parent_visual_intent_id", "scene_id", "purpose",
    "objective_ids", "concept_ids", "uncertainty", "visual_primitive_id",
    "timing_binding", "source_item_ids", "ordering_basis", "source_state_id",
    "target_state_id", "flash_hz", "native_decision_fingerprint"})
EXECUTABLE = frozenset({"easing"})
SEMANTIC = frozenset({"index", "mode", "reason", "scale_allowed", "semantic_effect",
    "purpose", "uncertainty", "ordering_basis", "source_state_id", "target_state_id",
    "flash_hz", "timing_binding"})
_ACTIVE = ContextVar("bie_m1_current_motion", default=None)


def fail(code):
    # Never include private source values or paths in a public diagnostic.
    raise AnimationCompilerError("M1_" + code)


def require(condition, code):
    if not condition:
        fail(code)


def plain(value):
    """Bounded JSON-compatible thaw, with finite numbers and no unknown objects."""
    from collections.abc import Mapping
    def visit(v, depth):
        require(depth < 32, "JSON_DEPTH")
        if isinstance(v, Mapping):
            require(len(v) <= 512 and all(type(k) is str for k in v), "JSON_OBJECT")
            return {k: visit(x, depth + 1) for k, x in v.items()}
        if isinstance(v, (tuple, list)):
            require(len(v) <= 512, "JSON_ARRAY")
            return [visit(x, depth + 1) for x in v]
        require(v is None or type(v) in (str, bool, int, float), "JSON_VALUE")
        if type(v) in (int, float):
            require(math.isfinite(v), "NONFINITE")
        if type(v) is str:
            require(len(v) <= 16384, "TEXT_BUDGET")
        return v
    result = visit(value, 0)
    require(len(json.dumps(result, ensure_ascii=False).encode()) <= 512 * 1024, "JSON_BUDGET")
    return result


def is_governed(track):
    p = track.get("parameters", {}) if isinstance(track, dict) else track.parameters
    return p.get("schema_version") == SCHEMA


def fields(value, expected, code):
    require(type(value) is dict and set(value) == set(expected), code)


def ids(value):
    require(type(value) is list and value and all(type(v) is str and v.strip() == v
        and v and len(v) <= 2048 and not any(ord(c) < 32 for c in v) for v in value)
        and len(value) == len(set(value)), "IDENTIFIERS")


def mapping_for(parameters):
    return {k: {"class": "rendering" if k in EXECUTABLE else
                "semantic" if k in SEMANTIC else "provenance_currentness",
                "original_pointer": "/parameters/" + k,
                "value_sha256": digest(v)} for k, v in sorted(parameters.items())}


def validate_original(node, row):
    fields(node, {"node_id", "track_id", "action", "target_ids", "start_ms", "end_ms",
        "parameters", "source_refs", "reasoning_refs", "owner_stage", "fallback_action"}, "ORIGINAL_NODE_FIELDS")
    action = node["action"]
    require(action in VARIANTS and node["owner_stage"] == "DOMAIN" and
        node["fallback_action"] is None, "ORIGINAL_ACTION")
    p = node["parameters"]
    fields(p, COMMON | ({"index"} if action == "reveal" else {"mode", "reason", "scale_allowed"}),
        "PARAMETER_COVERAGE")
    for key in ("source_refs", "reasoning_refs", "target_ids"):
        ids(node[key])
    require(node["target_ids"] == [p["visual_primitive_id"]], "TARGET_IDENTITY")
    for key in ("objective_ids", "concept_ids", "source_item_ids"):
        ids(p[key])
    for key in ("start_ms", "end_ms"):
        require(type(node[key]) is int, "TIME_TYPE")
    require(0 <= node["start_ms"] < node["end_ms"] <= row["scene_end_ms"] <= 3600000, "TIME_BOUNDS")
    timing = p["timing_binding"]
    fields(timing, {"visual_id", "narration_revision", "start_ms", "end_ms", "focus", "reveal"}, "TIMING_FIELDS")
    require(type(timing["focus"]) is bool and type(timing["reveal"]) is bool, "TIMING_FLAGS")
    require(all(type(timing[k]) is int for k in ("start_ms", "end_ms", "narration_revision")), "TIME_TYPE")
    require(timing["visual_id"] == p["visual_primitive_id"] and
        timing["narration_revision"] == row["narration_revision"] and
        timing["start_ms"] <= node["start_ms"] < node["end_ms"] <= timing["end_ms"], "TIMING_BINDING")
    require(type(p["uncertainty"]) in (float, int) and 0 <= p["uncertainty"] <= 1 and
        type(p["flash_hz"]) is int and p["flash_hz"] == 0, "UNCERTAINTY_FLASH")
    require(p["scene_id"] == row["scene_id"] and p["director_animation_intent_id"] == row["intent_id"]
        and p["objective_ids"] == row["objective_ids"] and p["concept_ids"] == row["concept_ids"], "GROUNDING")
    if action == "reveal":
        require(type(p["index"]) is int and p["index"] == 0 and p["source_state_id"] is None and
            p["semantic_effect"] == "dependency_ordered_reveal" and p["easing"] == "ease_out" and
            p["purpose"] in {"introduce", "show_sequence"}, "REVEAL_SEMANTICS")
    else:
        require(p["scale_allowed"] is False and p["mode"] == "accent" and
            p["reason"] == "identify_source_declared_structure_in_current_narration" and
            p["source_state_id"] == p["target_state_id"] and
            p["semantic_effect"] == "increase_attention_without_changing_semantic_value" and
            p["easing"] == "ease_in_out" and p["purpose"] == "focus", "FOCUS_SEMANTICS")


def contract(track):
    from .animation_behavior import MotionContract
    tid, eid, action, start, end, parameters, src, rsn = normalize_track(track)
    if isinstance(track, dict):
        fields(track, {"track_id", "element_id", "action", "start_ms", "end_ms", "parameters",
            "source_refs", "reasoning_refs"}, "TRACK_FIELDS")
        require((tid, eid, action) == (track["track_id"], track["element_id"], track["action"]), "TRACK_IDENTITY")
    p = plain(parameters)
    fields(p, {"schema_version", "profile", "policy", "variant", "admission_id", "original",
        "original_sha256", "mapping", "binding"}, "ENVELOPE_FIELDS")
    require(p["schema_version"] == SCHEMA and p["profile"] == PROFILE and
        p["policy"] == POLICY and p["variant"] == VARIANTS.get(action), "VERSION_PROFILE")
    active = _ACTIVE.get()
    require(active is not None, "CURRENT_ADMISSION_REQUIRED")
    require(p["admission_id"] == active["identity"], "ADMISSION_IDENTITY")
    expected = active["tracks"].get(tid)
    require(expected is not None and p == expected["parameters"], "ORIGINAL_MAPPING_MISMATCH")
    require((eid, action, start, end, list(src), list(rsn)) ==
        (expected["element_id"], expected["action"], expected["start_ms"], expected["end_ms"],
         expected["source_refs"], expected["reasoning_refs"]), "TRACK_BINDING")
    original = p["original"]
    require(digest(original) == p["original_sha256"] and p["mapping"] == mapping_for(original["parameters"]),
        "LOSSLESS_MAPPING")
    require((p["binding"]["element_type"], action) in PAIRS, "CAPABILITY_PAIR")
    return MotionContract(tid, eid, action, start, end, original["parameters"]["easing"], p,
        (("native_bar_opacity",) if p["binding"]["element_type"] == "chart" else ("opacity",))
        if action == "reveal" else ("focus_indicator",))


def state(c, frame, fps):
    from .animation_behavior import frame_window
    a, b = frame_window(c, fps)
    u = min(1., max(0., (frame - a) / (b - a)))
    if c.action == "reveal":
        # One whole-item visibility transition at the governed curve midpoint.
        # Never display half-painted low-contrast labels or sweep over values.
        # This is a versioned presentation mapping, not a changed time interval.
        key = "series_opacity" if c.parameters["binding"]["element_type"] == "chart" else "opacity"
        return {key: 1. if 1 - (1 - u) ** 3 >= .5 else 0.}
    u = u * u * (3 - 2 * u)
    return {"focus_opacity": 1 - abs(2 * u - 1)}


def validate_element(track, element, target=None):
    c = contract(track)
    e = plain(element)
    expected = _ACTIVE.get()["elements"].get(c.element_id)
    require(e == expected, "ELEMENT_BINDING")
    require(e["element_type"] == c.parameters["binding"]["element_type"], "CAPABILITY_PAIR")
    if c.action == "emphasize":
        from .diagram_compiler import diagram_geometry
        geometry = diagram_geometry(e["props"], e["source_refs"], e["reasoning_refs"])
        # Indicator occupies a six-pixel inward gutter, never content/label area.
        # Bounded structure-only profile: no edge or label can cross this gutter.
        require(not geometry["edges"], "FOCUS_EDGE_SCOPE")
        if target is not None:
            box = e["normalized_box"]
            width, height = box["width"] * target.width, box["height"] * target.height
            x, y, w, h = geometry["view_box"]
            scale = min(width / w, height / h)
            require(width >= 48 and height >= 48, "FOCUS_BOUNDS")
            for n in geometry["nodes"]:
                margin = min(n["x"] - x - 1, n["y"] - y - 1,
                    x + w - n["x"] - n["width"] - 1, y + h - n["y"] - n["height"] - 1) * scale
                require(margin >= 8, "FOCUS_CONTENT_GUTTER")
    return c


def validate_document(raw, target):
    tracks = raw.get("tracks", [])
    selected = [t for t in tracks if is_governed(t)]
    metadata = raw.get("metadata", {}).get(METADATA)
    # Opaque metadata on an unversioned legacy document never selects new
    # behavior. A track's explicit schema is the dispatch authority; metadata
    # must additionally agree once that new contract is selected.
    declared = isinstance(metadata, dict) and metadata.get("schema_version") == SCHEMA
    if not selected and not declared and _ACTIVE.get() is None:
        return "web"
    fields(metadata, {"schema_version", "profile", "policy", "admission_id"}, "PROFILE_REQUIRED")
    require(metadata == {"schema_version": SCHEMA, "profile": PROFILE, "policy": POLICY,
        "admission_id": (_ACTIVE.get() or {}).get("identity")}, "PROFILE_IDENTITY")
    active = _ACTIVE.get()
    require(active is not None and selected and
        {t["track_id"] for t in selected} == set(active["tracks"]) and
        len({t["track_id"] for t in tracks}) == len(tracks), "TRACK_COVERAGE")
    elems = {e["element_id"]: e for e in raw["elements"]}
    require(len(elems) == len(raw["elements"]) and
        {k: elems.get(k) for k in active["elements"]} == active["elements"], "ELEMENT_COVERAGE")
    require(raw["scene_id"] == active["scene_id"] and raw["duration_ms"] == active["duration_ms"], "SCENE_BINDING")
    if active["presentation"] == FIXTURE_LAYOUT:
        require((target.width, target.height, target.fps) == (960, 640, 24), "FIXTURE_TARGET")
    else:
        declared_target = active["upstream"]["visual_target"]
        require((target.width, target.height, target.fps) == (declared_target["viewport_width"],
            declared_target["viewport_height"], 24), "CURRENT_TARGET")
    for t in selected:
        validate_element(t, elems[t["element_id"]], target)
        require(sum(x["element_id"] == t["element_id"] for x in tracks) == 1, "MIXED_TARGET_COMPOSITION")
    required = {(t["element_id"], "comp:m1:" + elems[t["element_id"]]["element_type"], t["action"]) for t in selected}
    requests = [r for r in raw["capability_requests"] if str(r.get("capability_id", "")).startswith("comp:m1:")]
    for r in requests:
        fields(r, {"element_id", "element_type", "capability_id", "requested_action", "required"}, "CAPABILITY_FIELDS")
        require(r["required"] is True and r["element_id"] in elems and
            r["element_type"] == elems[r["element_id"]]["element_type"], "CAPABILITY_REQUIRED")
    actual = [(r["element_id"], r["capability_id"], r["requested_action"]) for r in requests]
    require(set(actual) == required and len(actual) == len(required), "CAPABILITY_COVERAGE")
    return PROFILE


def validate_replacement(original, replacement, element, raw, target):
    # Explicit registry declaration is checked by the legacy outer resolver.
    # A same-action replacement is only safe after complete binding validation.
    validate_document(raw, target)
    before = validate_element(original, element, target)
    after = validate_element(replacement, element, target)
    require(plain(original) == plain(replacement) and before == after, "REDUCED_MAPPING_CHANGED")
    return {"schema_version": SCHEMA, "policy": POLICY, "profile": PROFILE,
        "track_id": before.track_id, "variant": before.parameters["variant"],
        "original_sha256": before.parameters["original_sha256"],
        "mapping_sha256": digest(before.parameters["mapping"]),
        "admission_id": before.parameters["admission_id"], "accepted": False}


def add_capabilities(registry, profile):
    require(profile in {"web", PROFILE}, "UNKNOWN_PROFILE")
    if profile == PROFILE:
        from bie.scene_ir.compiler_capability_declarations import CompilerCapability
        for kind in sorted({p[0] for p in PAIRS}):
            registry.register(CompilerCapability("comp:m1:" + kind, "1.0.0", (kind,),
                tuple(sorted(action for k, action in PAIRS if k == kind)), (PROFILE,), True))
    return registry
