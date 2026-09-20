"""Source-authorized H10 state/motion composition, not an implicit fallback.

An explicit state policy wraps content replacement, inside geometry transforms,
applying frame visibility and nonconflicting opacity to the resulting subtree. Original
unconfigured H6 scenes retain their conflict behavior. Educational equivalence
and real-browser execution are separate gates.
"""
from __future__ import annotations

from copy import deepcopy
from .qa_common import CompilerQAError, digest

SCHEMA = "bie.comp-state-motion-composition.v1"
POLICY = "outer-state-controls"
MAX_COMPOSITIONS = 128


def _fail(code: str, message: str) -> None:
    raise CompilerQAError(code + ": " + message)


def _strings(value, label: str) -> list[str]:
    if (not isinstance(value, list) or not value or len(value) > 256
            or any(not isinstance(v, str) or not v.strip() for v in value)
            or len(set(value)) != len(value)):
        _fail("STATE_MOTION_LIST_INVALID", label + " requires unique nonblank strings")
    return value


def validate_state_composition(raw: dict, bindings: list[dict]) -> list[dict]:
    """Bind every opt-in to the exact target, all its tracks, and state controls.

    Opacity writers on both sides still fail closed: there is no inferred blend.
    Visibility can mask an animated subtree, while motion continues advancing
    against absolute scene frames, so reverse/random seeking remains pure.
    """
    cfg = raw.get("metadata", {}).get("compiler_h10")
    tracks = raw.get("tracks", [])
    elements = {e["element_id"]: e for e in raw["elements"]}
    needed = {}
    for binding in bindings:
        if binding["property_name"] not in {"visible", "opacity"}:
            continue
        target = binding["target_id"]
        if any(t["element_id"] == target for t in tracks):
            needed.setdefault(target, set()).add(binding["property_name"])
    if cfg is None:
        if needed:
            _fail("FRAME_RUNTIME_PROPERTY_CONFLICT", "state visibility/opacity plus animation requires explicit composition")
        return []
    if not isinstance(cfg, dict) or set(cfg) != {"schema_version", "compositions"}:
        _fail("STATE_MOTION_FIELDS", "exact versioned composition fields required")
    if cfg["schema_version"] != SCHEMA:
        _fail("STATE_MOTION_VERSION", "unsupported composition version")
    rows = cfg["compositions"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_COMPOSITIONS:
        _fail("STATE_MOTION_BUDGET", "one to 128 composition rows required")
    expected_keys = {"target_id", "track_ids", "state_properties", "policy", "source_refs", "reasoning_refs"}
    result, seen = [], set()
    from .animation_behavior import motion_contract
    for row in rows:
        if not isinstance(row, dict) or set(row) != expected_keys:
            _fail("STATE_MOTION_FIELDS", "composition fields are missing or unconsumed")
        eid = row["target_id"]
        if not isinstance(eid, str) or eid not in elements or eid in seen:
            _fail("STATE_MOTION_TARGET", "unknown or duplicate target")
        seen.add(eid)
        if row["policy"] != POLICY:
            _fail("STATE_MOTION_POLICY", "no implicit blend or override is supported")
        tids = _strings(row["track_ids"], "track_ids")
        props = _strings(row["state_properties"], "state_properties")
        own_tracks = [t for t in tracks if t["element_id"] == eid]
        if set(tids) != {t["track_id"] for t in own_tracks} or not own_tracks:
            _fail("STATE_MOTION_TRACK_COVERAGE", "all and only the actual target tracks must be bound")
        if eid not in needed or set(props) != needed[eid]:
            _fail("STATE_MOTION_PROPERTY_COVERAGE", "all and only combined visible/opacity controls must be bound")
        contracts = [motion_contract(t) for t in own_tracks]
        if "opacity" in props and any("opacity" in c.owned_properties for c in contracts):
            _fail("STATE_MOTION_OPACITY_CONFLICT", "two opacity writers require an unsupported blend policy")
        for key in ("source_refs", "reasoning_refs"):
            declared = set(_strings(row[key], key))
            required = set(elements[eid].get(key, []))
            for track in own_tracks:
                required.update(track.get(key, []))
            if not required <= declared or not declared <= set(raw.get(key, [])):
                _fail("STATE_MOTION_PROVENANCE", key + " must cover the element/tracks and be scene-bound")
        from .registered_actions import is_registered, CONTENT_ACTIONS
        from .specialized_motion import is_specialized
        inner = {t['track_id'] for t in own_tracks if
                 (is_registered(t) and t['action'] in CONTENT_ACTIONS) or
                 (is_specialized(t) and t['action'] in {'morph','trace'})}
        result.append({"target_id": eid, "track_ids": sorted(tids), "state_properties": sorted(props),
                       "content_track_ids": sorted(inner), "outer_geometry_track_ids": sorted(set(tids)-inner),
                       "policy": POLICY, "source_refs": sorted(row["source_refs"]),
                       "reasoning_refs": sorted(row["reasoning_refs"]),
                       "definition_sha256": digest(row), "accepted": False})
    if seen != set(needed):
        _fail("STATE_MOTION_TARGET_COVERAGE", "every combined target needs an explicit row")
    return sorted(result, key=lambda r: r["target_id"])


def composed_targets(plan: dict | None) -> frozenset[str]:
    return frozenset(row["target_id"] for row in (plan or {}).get("state_motion_compositions", []))
