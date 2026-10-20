"""Read-only current Task035 -> compiler motion envelope (M1 prerequisite).

This is NOT a Scene IR catalog producer. Explicit native element bindings are
provided by a caller, checked for source conservation, then sealed for one scoped
compiler operation. Current service admission is repeated on entry and exit; JSON
hashes/receipts cannot grant authority. No upstream artifact is changed/published.
"""
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from .governed_motion import (SCHEMA, PROFILE, POLICY, METADATA, VARIANTS, PAIRS,
    _ACTIVE, plain, fields, require, ids, mapping_for, validate_original, EXACT_LAYOUT, FIXTURE_LAYOUT)
from .qa_common import digest


def _snapshot(service, run, tenant):
    from bie.productization.animation_slice import AnimationProducerService
    from bie.infrastructure.artifact_store import BlobRef
    require(isinstance(service, AnimationProducerService), "NATIVE_SERVICE_REQUIRED")
    plan, receipt = service.verified_animation(run, tenant)
    configuration = service.configuration(run, tenant)
    handoff = service.read(run, receipt["handoff_id"])
    current = service.read(run, receipt["current_inputs_id"])
    refs = {stage: service.stage_ref(run, stage)[0] for stage in ("VISUAL", "ANIMATION", "DIRECTOR")}
    refs.update({k: receipt[k] for k in ("handoff_id", "current_inputs_id", "validation_id")})
    artifacts = {}
    for label, aid in refs.items():
        record = service.record(run, aid)
        raw = service.cas.get_bytes(BlobRef(record.blob_algorithm, record.blob_digest, record.blob_size))
        require(sha256(raw).hexdigest() == record.blob_digest and len(raw) == record.blob_size, "ARTIFACT_BYTES")
        artifacts[label] = {"artifact_id": aid, "sha256": record.blob_digest, "bytes": len(raw),
            "parents": list(record.parent_artifact_ids)}
    # Original payload bytes remain private in the existing CAS. Exact originals
    # are included below; the service has independently rebuilt and compared them.
    return plain({"plan": plan, "handoff": handoff, "current": current, "artifacts": artifacts,
        "source_sha256": receipt["source_sha256"], "run_id": run, "tenant": tenant,
        "replay": receipt["replay"], "visual_target": configuration["config"]["visual"]["target"]})


def _element_semantics(element, row, primitive, action, presentation):
    """Bounded catalog admission, not layout or representation generation."""
    from .diagram_compiler import diagram_geometry
    from .chart_geometry import chart_geometry
    require(element["element_id"] == primitive["primitive_id"] and
        (element["element_type"], action) in PAIRS, "CATALOG_TARGET")
    require(element["source_refs"] == primitive["source_refs"] and
        element["reasoning_refs"] == primitive["reasoning_refs"] and
        type(element["accessibility"].get("alt")) is str and element["accessibility"]["alt"].strip(), "CATALOG_PROVENANCE")
    expected_box = primitive["layout"]["box"]
    if presentation == FIXTURE_LAYOUT and row["semantic_kind"] == "sampled_chart":
        expected_box = {"x": .05, "y": .05, "width": .9, "height": .9}
    require(element["normalized_box"] == expected_box, "CATALOG_LAYOUT_CHANGED")
    source = {i["id"]: i for i in row["semantic_obligations"]["source_items"]}
    selected = [source[i] for i in primitive["source_item_ids"]]
    props = element["props"]
    if row["semantic_kind"] == "sampled_chart":
        require(element["element_type"] == "chart" and action == "reveal", "CATALOG_FAMILY")
        g = chart_geometry(props)
        require(g["kind"] == "bar" and g["categories"] == [x["label"] for x in selected]
            and g["values"] == [x["value"] for x in selected], "CATALOG_DATA_CHANGED")
        # Scientific labels/units must be supplied by the source, not guessed.
        obligations = row["semantic_obligations"]
        for key in ("x_label", "y_label", "units"):
            expected = obligations["axis"][key] if key != "units" else ""
            require(props.get(key, "") == expected, "CATALOG_UNITS_CHANGED")
    else:
        require(element["element_type"] == "diagram" and len(selected) == 1, "CATALOG_FAMILY")
        g = diagram_geometry(props, element["source_refs"], element["reasoning_refs"])
        require(len(g["nodes"]) == 1 and not g["edges"], "CATALOG_RELATION_INVENTED")
        item = selected[0]
        # The one-node technical decomposition retains the entire declared item;
        # it is never a biological-flow or elapsed-time model.
        label = item["label"]
        if row["semantic_kind"] == "timeline":
            label += " | " + item["time_label"] + (" | uncertain" if item["uncertain"] else "")
        else:
            require(row["semantic_kind"] == "cellular" and not
                row["semantic_obligations"]["containments"] and not
                row["semantic_obligations"]["transports"], "CATALOG_UNSUPPORTED_STRUCTURE")
        require(g["nodes"][0]["label"] == label and g["nodes"][0]["node_id"] == item["id"], "CATALOG_CONTENT_CHANGED")


def _lower(snapshot, elements, presentation):
    require(presentation in {EXACT_LAYOUT, FIXTURE_LAYOUT}, "PRESENTATION_POLICY")
    plan, current, handoff = snapshot["plan"], snapshot["current"], snapshot["handoff"]
    require(handoff["schema_version"] == "0.1.0" and handoff["animation_plan_fingerprint"] == plan["plan_fingerprint"]
        and not handoff["blockers"] and not handoff["unsupported_capabilities"] and not handoff["planned_fallbacks"]
        and handoff["accepted"] is False and handoff["review_required"] is True, "HANDOFF_CONTRACT")
    nodes = handoff["nodes"]
    require(0 < len(nodes) <= 128 and len({n["track_id"] for n in nodes}) == len(nodes)
        and len({n["node_id"] for n in nodes}) == len(nodes), "NODE_IDENTITIES")
    elements = plain(elements)
    require(type(elements) is list and len({e["element_id"] for e in elements}) == len(elements), "CATALOG_IDENTITIES")
    catalog = {e["element_id"]: e for e in elements}
    require(set(catalog) == {p for n in nodes for p in n["target_ids"]}, "CATALOG_COVERAGE")
    rows = current["rows"]
    require(len({r["scene_id"] for r in rows}) == 1, "SCENE_SCOPE")
    by_intent = {r["intent_id"]: r for r in rows}
    bindings = {}
    for node in nodes:
        row = by_intent.get(node["parameters"]["director_animation_intent_id"])
        require(row is not None, "INTENT_IDENTITY")
        validate_original(node, row)
        pid = node["target_ids"][0]
        primitive = next((p for p in row["primitive_rows"] if p["primitive_id"] == pid), None)
        require(primitive is not None, "PRIMITIVE_IDENTITY")
        _element_semantics(catalog[pid], row, primitive, node["action"], presentation)
        bindings[node["track_id"]] = {"element_id": pid, "element_type": catalog[pid]["element_type"],
            "element_sha256": digest(catalog[pid]), "row_sha256": digest(row),
            "primitive_sha256": digest(primitive), "narration_revision": row["narration_revision"],
            "visual_revision": row["visual_revision"], "target_profile": row["target_profile"],
            "visual_target": snapshot["visual_target"],
            "presentation_policy": presentation, "original_visual_layout": primitive["layout"],
            "compiler_test_layout": catalog[pid]["normalized_box"] if presentation == FIXTURE_LAYOUT else None,
            "original_scene_duration_ms": row["scene_end_ms"],
            "compiler_test_duration_ms": 2000 if presentation == FIXTURE_LAYOUT else None,
            "production_catalog_claimed": False}
    if presentation == FIXTURE_LAYOUT:
        # An explicit bounded compiler-contract fixture, not a shortened lesson.
        # All original motion windows and original narration associations remain
        # present and unchanged. Longer tracks are unsupported, never clipped.
        require(all(n["end_ms"] < 2000 for n in nodes), "COMPILER_FIXTURE_WINDOW")
    # Snapshot includes full source/parent identities and native currentness,
    # not just an aggregate caller-supplied digest.
    identity = digest({"schema": SCHEMA, "profile": PROFILE, "policy": POLICY,
        "snapshot": snapshot, "bindings": bindings})
    tracks = {}
    for node in nodes:
        tid = node["track_id"]
        p = {"schema_version": SCHEMA, "profile": PROFILE, "policy": POLICY,
            "variant": VARIANTS[node["action"]], "admission_id": identity,
            "original": deepcopy(node), "original_sha256": digest(node),
            "mapping": mapping_for(node["parameters"]), "binding": bindings[tid]}
        tracks[tid] = {"track_id": tid, "element_id": node["target_ids"][0], "action": node["action"],
            "start_ms": node["start_ms"], "end_ms": node["end_ms"], "parameters": p,
            "source_refs": node["source_refs"], "reasoning_refs": node["reasoning_refs"]}
    return {"identity": identity, "elements": catalog, "tracks": tracks, "presentation": presentation,
        "scene_id": rows[0]["scene_id"],
        "duration_ms": 2000 if presentation == FIXTURE_LAYOUT else rows[0]["scene_end_ms"],
        "metadata": {"schema_version": SCHEMA, "profile": PROFILE, "policy": POLICY, "admission_id": identity},
        "upstream": snapshot}


@contextmanager
def current_motion_admission(service, run, tenant, elements, *, presentation=EXACT_LAYOUT):
    """Use inside the existing authorized service context; no new control plane.

Every new scope/replay reopens verified_animation; changes/revocation on exit
invalidate the operation. No persistence, publication or accepted receipt here.
"""
    snapshot = _snapshot(service, run, tenant)
    bound = _lower(snapshot, elements, presentation)
    marker = _ACTIVE.set(bound)
    try:
        yield deepcopy(bound)
        require(_snapshot(service, run, tenant) == snapshot, "CURRENTNESS_CHANGED")
    finally:
        _ACTIVE.reset(marker)
