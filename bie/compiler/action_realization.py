"""Connect native capability requests to actually emitted scene tracks.

A capability registry is availability, not execution evidence. Render requests
are discharged by the element emitter; native non-render requests need at least
one matching, connected compiled track. Unsupported/fallback checks remain owned
by capability_fallback_qa rather than being silently reinterpreted here.
"""
from __future__ import annotations

from hashlib import sha256
from .qa_common import QAFinding, ordered_findings


def inspect_action_realization(document, registry, animation_results, *, profile="web"):
    raw = document.to_dict()
    elems = {e["element_id"]: e for e in raw["elements"]}
    compiled = {r.track_id: r for r in animation_results}
    findings, rows = [], []
    for index, req in enumerate(raw["capability_requests"]):
        eid, cid, action = req.get("element_id"), req.get("capability_id"), req.get("requested_action")
        if eid not in elems or not isinstance(action, str) or action == "render":
            continue
        kind = elems[eid]["element_type"]
        if not registry.supports(cid, kind, action, profile):
            continue
        matches = [t for t in raw["tracks"] if t["element_id"] == eid and t["action"] == action]
        realized = []
        for track in matches:
            emitted = compiled.get(track["track_id"])
            if emitted is not None and emitted.action == action and "BlockedTrack" not in emitted.source_path:
                realized.append({"track_id": track["track_id"], "path": emitted.source_path,
                                 "source_sha256": sha256(emitted.source_text.encode("utf-8")).hexdigest(),
                                 "source_refs": list(track["source_refs"]),
                                 "reasoning_refs": list(track["reasoning_refs"])})
        rows.append({"request_index": index, "capability_id": cid, "element_id": eid,
                     "requested_action": action, "realized_tracks": realized,
                     "status": "EMITTED" if realized else "NOT_REALIZED"})
        if not realized:
            findings.append(QAFinding("REQUIRED_ACTION_NOT_REALIZED" if req.get("required", True) is not False
                                      else "OPTIONAL_ACTION_NOT_REALIZED",
                                      "ERROR" if req.get("required", True) is not False else "WARNING",
                                      "Registry availability has no matching emitted track for " + action,
                                      f"$.capability_requests[{index}]"))
    receipt = {"schema_version": "bie.comp-action-realization.v1", "scene_fingerprint": document.fingerprint,
               "requests": rows, "scope": "GENERATED_TRACK_SOURCE_NOT_RENDERED_BEHAVIOR",
               "passed": not any(f.severity == "ERROR" for f in findings),
               "actual_render_verified": False, "accepted": False}
    return ordered_findings(findings), receipt
