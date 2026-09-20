"""H2-005 source-level cross-element/track ownership and time coverage gates."""
from __future__ import annotations
from dataclasses import asdict
from itertools import combinations
from .qa_common import diagnostic_message, QAFinding, ordered_findings
from .animation_behavior import motion_contract, frame_window
from .simulation_models import simulation_contract


def validate_scene_behaviors(document, target):
    raw = document.to_dict()
    findings, contracts = [], {"schema_version": "bie.scene-behavior.v1", "motion": [], "simulations": [], "accepted": False}
    def error(code, message, path): findings.append(QAFinding(code, "ERROR", message, path))
    tracks = []
    frames = (document.duration_ms*target.fps+999)//1000
    for i, t in enumerate(raw["tracks"]):
        path = f"$.tracks[{i}]"
        try:
            c = motion_contract(t); a,b = frame_window(c, target.fps)
            if b >= frames:
                error("ANIMATION_EXCEEDS_SCENE", "a required animation sample lies outside the rendered scene", path)
            contracts["motion"].append({**asdict(c), "sample_start_frame": a, "sample_end_frame": b, "interval_policy": "start-inclusive/end-exclusive; endpoint at final included frame"})
            tracks.append(c)
        except ValueError as exc:
            code = str(exc).split(":",1)[0]
            error(code if code.isupper() else "ANIMATION_CONTRACT_INVALID", diagnostic_message(exc), path)
    for a,b in combinations(tracks, 2):
        if a.element_id != b.element_id or not set(a.owned_properties)&set(b.owned_properties): continue
        first,last = sorted((a,b), key=lambda t:t.start_ms)
        valid_fade_pair = (first.action == "enter" and last.action == "exit" and first.end_ms <= last.start_ms and
                          first.parameters == {"from_opacity":0., "to_opacity":1.} and last.parameters == {"from_opacity":1., "to_opacity":0.})
        if not valid_fade_pair:
            error("ANIMATION_PROPERTY_OWNERSHIP_CONFLICT", "nested tracks would implicitly combine the same persistent visual property: " + a.track_id + ", " + b.track_id, "$.tracks")
    for i,e in enumerate(raw["elements"]):
        path = f"$.elements[{i}]"
        if e["element_type"] == "simulation":
            try:
                c = simulation_contract(e["props"])
                end_seconds = (c.start_ms+c.duration_ms)/1000
                if end_seconds > (frames-1)/target.fps + 1e-12:
                    error("SIMULATION_FINAL_STATE_NOT_VISIBLE", "scene must include at least one sample at/after the simulation endpoint", path)
                omega = dict(c.parameters).get("omega",0.)
                if omega/(2*3.141592653589793)*8 > target.fps:
                    error("SIMULATION_FRAME_ALIASING", "oscillator needs at least eight rendered frames per cycle", path)
                contracts["simulations"].append({"element_id":e["element_id"], **c.to_dict(), "source_refs":e["source_refs"], "reasoning_refs":e["reasoning_refs"]})
            except ValueError as exc:
                code = str(exc).split(":",1)[0]
                error(code if code.isupper() else "SIMULATION_CONTRACT_INVALID", diagnostic_message(exc), path)
        if e["element_type"] == "map":
            for layer in e["props"].get("layers",[]):
                if isinstance(layer,dict) and layer.get("source_ref") is not None and layer["source_ref"] not in e["source_refs"]:
                    error("MAP_LAYER_SOURCE_UNBOUND", "layer source_ref must be bound by element provenance", path)
    from .specialized_motion import validate_specialized_bindings, is_specialized
    if any(is_specialized(t) for t in raw["tracks"]):
        try:
            contracts["specialized"] = validate_specialized_bindings(raw, target)
        except ValueError as exc:
            code = str(exc).split(":", 1)[0]
            error(code if code.isupper() else "SPECIALIZED_BINDING_INVALID", diagnostic_message(exc), "$.tracks")
    return ordered_findings(findings), contracts
