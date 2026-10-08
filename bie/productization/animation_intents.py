"""Source-grounded current Director/Visual animation intent admission.

Director synchronizes the original aggregate Visual target. Native Animation
tracks realize only that target's exact persisted grammar primitives. This
explicit parent/child binding preserves both native contracts; it never rewrites
Task034's visual sync candidate or pairs primitive/timing rows by position.

Only complete current source declarations already admitted by Task034 qualify:
descriptive chart introduction, chronology-preserving reveal, and attention to
flat cellular structure. Missing action is never interpreted as reveal. These
are technical planning policies, not measured instructional effectiveness.
"""
from dataclasses import asdict

from bie.bie_core.artifact_contracts import ArtifactEnvelope
from bie.director.director_benchmark import DirectorExecution
from bie.director.director_inputs import DirectorInputs
from bie.director.director_artifacts import fingerprint
from bie.director.narration_animation_sync import AnimationIntent, sync_animation_intents
from bie.director.narration_visual_sync import sync_visual_intents
from bie.director.sync_contract import IntentBinding, SyncIndex, build_sync_context
from bie.visual_intelligence.visual_plan_contract import VisualPlan, STAGES
from bie.visual_intelligence.capability_handoff import (
    PrimitiveRequirement, AssetBinding, TimingBinding, build_downstream_handoff,
)
from bie.animation_intelligence.vis_ani_adoption import adopt_visual_handoff
from .contracts import ProducerError, require, canonical, digest
from .visual_intents import derive_intents


SCHEMA = "bie.producer.current-animation-intent/1"
POLICY = "declared-source-current-narration-animation-v1"
ACTION_PURPOSE = {
    "sampled_chart": ("reveal", "introduce"),
    "timeline": ("reveal", "show_sequence"),
    "cellular": ("emphasize", "focus"),
}
ALLOWED_TEACHING_MOVES = frozenset({"EXPLAIN", "WORKED_EXAMPLE"})


def _index(rows, field, code):
    require(type(rows) in (tuple, list) and bool(rows), code)
    require(all(type(row) is dict and type(row.get(field)) is str and row[field]
                for row in rows), code)
    result = {row[field]: row for row in rows}
    require(len(result) == len(rows), code)
    return result


def _visual_validation(plan, records, validation):
    """Bind retained detailed receipts to exact native Visual stage payloads."""
    by_record = _index(records, "intent_id", "animation_visual_record_identity")
    by_detail = _index(validation, "intent_id", "animation_visual_validation_identity")
    require(set(by_record) == set(by_detail), "animation_visual_validation_identity")
    expected = {iid: dict(intent_id=iid, scene_id=r["scene_id"], record_sha256=digest(r))
                for iid, r in by_record.items()}
    for stage in plan.stages[1:]:
        payload = stage.payload
        require(payload.get("records_sha256") == digest(records) and
                payload.get("director_revision") == plan.dir_revision and
                payload.get("narration_revision") == plan.dir_revision and
                payload.get("source_id") == plan.source_id and
                payload.get("internal_stage") == stage.stage and
                payload.get("review_required") is True and payload.get("accepted") is False,
                "animation_visual_stage_identity")
        outputs = _index(payload.get("outputs"), "intent_id", "animation_visual_stage_identity")
        require(set(outputs) == set(by_record), "animation_visual_stage_identity")
        for iid, output in outputs.items():
            require(output.get("scene_id") == by_record[iid]["scene_id"],
                    "animation_visual_stage_identity")
            expected[iid].update({k: v for k, v in output.items() if k not in ("intent_id", "scene_id")})
    require(canonical(expected) == canonical(by_detail), "animation_visual_validation_identity")
    return by_detail


def _handoff(plan, raw, visual_revision, target_profile):
    require(type(raw) is dict and raw.get("review_required") is True and
            raw.get("accepted") is False and raw.get("accessibility_ready") is True,
            "animation_visual_handoff_review_boundary")
    require(raw.get("plan_fingerprint") == plan.fingerprint and
            raw.get("handoff_id") == "visual-handoff:" + plan.fingerprint and
            raw.get("target_profile") == target_profile and
            raw.get("required_2d") is True and raw.get("required_3d") is False and
            not raw.get("unsupported_capabilities") and not raw.get("planned_fallbacks"),
            "animation_visual_handoff_identity")
    primitives = _index(raw.get("primitives"), "primitive_id", "animation_primitive_identity")
    timings = _index(raw.get("timing"), "visual_id", "animation_timing_identity")
    require(set(primitives) == set(timings), "animation_primitive_timing_mismatch")
    require(all(tuple(p.get("capability_tags", ())) == ("2d",) and
                p.get("required") is True and p.get("fallback_type") is None
                for p in primitives.values()), "animation_target_capability_unsupported")
    try:
        rebuilt = build_downstream_handoff(handoff_id=raw["handoff_id"],
            plan_fingerprint=plan.fingerprint,
            primitives=tuple(PrimitiveRequirement(**p) for p in raw["primitives"]),
            assets=tuple(AssetBinding(**a) for a in raw["assets"]),
            timing=tuple(TimingBinding(**t) for t in raw["timing"]),
            accessibility_ready=True, target_capabilities=("2d",), target_profile=target_profile)
        require(canonical(asdict(rebuilt)) == canonical(raw), "animation_visual_handoff_fingerprint")
        adopt_visual_handoff(raw, visual_revision, plan.fingerprint)
    except ProducerError:
        raise
    except Exception:
        raise ProducerError("animation_visual_handoff_invalid") from None
    require(not raw["assets"], "animation_external_asset_obligation")
    return primitives, timings


def _source_items(record, elements):
    obligations = record["semantic_obligations"]
    items = _index(obligations.get("source_items"), "id", "animation_source_obligation")
    kind = record["semantic_kind"]
    require(obligations.get("kind") == kind, "animation_source_obligation")
    associations = {}
    if kind == "sampled_chart":
        require(obligations.get("sampled_data") is True and
                obligations.get("exact_curve_claim") is False and
                set(elements) == {"chart:frame", "series:declared-samples"},
                "animation_chart_semantics_unsupported")
        values = elements["series:declared-samples"]["payload"]["values"]
        require(canonical([(v["x"], float(v["y"])) for v in values]) ==
                canonical([(i["label"], float(i["value"])) for i in items.values()]),
                "animation_source_item_mismatch")
        associations = {"chart:frame": ([], "supporting_axis"),
                        "series:declared-samples": (list(items), "declared_samples")}
    elif kind == "timeline":
        require(obligations.get("duration_claim") is False,
                "animation_chronology_duration_claim")
        for key, element in elements.items():
            if key.startswith("event:"):
                sid = key[len("event:"):]
                require(sid in items, "animation_source_item_mismatch")
                source, payload = items[sid], element["payload"]
                require(payload.get("time_label") == source["time_label"] and
                        payload.get("uncertain") is source["uncertain"] and
                        payload.get("lower_bound") == source["lower_bound"] and
                        payload.get("upper_bound") == source["upper_bound"],
                        "animation_chronology_uncertainty_changed")
                associations[key] = ([sid], "declared_event")
            else:
                require(element.get("role") in ("timeline_axis", "time_axis"),
                        "animation_unknown_visual_primitive")
                associations[key] = ([], "supporting_axis")
        require({s for ids, _ in associations.values() for s in ids} == set(items),
                "animation_source_item_mismatch")
    elif kind == "cellular":
        require(not obligations.get("containments") and not obligations.get("transports") and
                obligations.get("physical_scale_claim") is False,
                "animation_cellular_motion_contract_required")
        require(set(elements) == {"bio:" + sid for sid in items}, "animation_source_item_mismatch")
        for sid, source in items.items():
            element = elements["bio:" + sid]
            require(element.get("label") == source["label"] and
                    element["payload"].get("kind") == source["kind"] and
                    element["payload"].get("parent_id") is None and source["parent_id"] is None,
                    "animation_source_item_mismatch")
            associations["bio:" + sid] = ([sid], "declared_static_structure")
    else:
        raise ProducerError("animation_semantics_not_admitted")
    return associations


def derive_animation_intents(inputs, execution, visual_sync, records, plan_dict,
                             handoff_dict, validation, *, visual_revision, target_profile):
    """Derive native aggregate intents and private, identity-bound child rows.

    The durable service must first run Task034 verified_visual and native current
    Director validation. This pure boundary independently checks the retained
    semantics; it cannot confer currentness on a raw envelope or replace CAS.
    """
    require(isinstance(inputs, DirectorInputs) and isinstance(execution, DirectorExecution),
            "animation_native_inputs_required")
    require(isinstance(visual_sync, ArtifactEnvelope) and
            visual_sync.artifact_type == "director.visual_sync_candidate",
            "animation_visual_sync_required")
    try:
        visual_sync.validate()
    except Exception:
        raise ProducerError("animation_visual_sync_identity") from None
    require(type(visual_revision) is int and visual_revision > 0 and
            type(target_profile) is str and target_profile, "animation_configuration_invalid")
    original, expected_records, abstentions = derive_intents(inputs, execution)
    require(original and canonical(records) == canonical(expected_records) and
            not any(a["status"] in ("BLOCKED", "REVIEW_REQUIRED") for a in abstentions),
            "animation_visual_intent_grounding")
    context = build_sync_context(execution.speech, execution.pauses, execution.emphasis, execution.timeline)
    visuals = sync_visual_intents(context, original)
    require(not any(i.code == "AUDIO_REPLAN_REQUIRED" for i in visuals.issues),
            "animation_audio_replan_required")
    require(not visuals.issues, "animation_visual_sync_blocked")
    payload = visual_sync.payload
    require(payload.get("director_ref") in [asdict(r) for r in visual_sync.parent_refs] and
            payload.get("director_ref", {}).get("artifact_type") == "director.plan",
            "animation_visual_sync_parent")
    require(payload.get("schema_version") == "bie.dir.consumer_candidate/1.0.0" and
            payload.get("consumer_kind") == "director.visual_sync_candidate" and
            payload.get("review_boundary") == "PLANNING_PREVIEW_ONLY" and
            visual_sync.metadata.get("requires_review") is True and
            visual_sync.metadata.get("accepted") is False and
            visual_sync.metadata.get("release_ready") is False and
            visual_sync.metadata.get("status") == "REVIEW_REQUIRED",
            "animation_visual_sync_review_boundary")
    require(canonical(payload.get("parameters", {}).get("intents")) ==
            canonical([asdict(i) for i in original]) and
            canonical(payload.get("result")) == canonical(asdict(visuals)) and
            payload.get("result_fingerprint") == fingerprint(asdict(visuals)),
            "animation_visual_sync_mismatch")
    try:
        plan = VisualPlan.from_dict(plan_dict)
    except Exception:
        raise ProducerError("animation_visual_plan_fingerprint") from None
    require(plan.plan_id == "visual:" + visual_sync.run_id and
            plan.dir_id == visual_sync.artifact_id and plan.dir_revision == visual_revision and
            plan.target_profile == target_profile and plan.current is True and
            plan.review_required is True and plan.accepted is False and
            tuple(s.stage for s in plan.stages) == STAGES and
            all(s.current and s.status == "PASS" for s in plan.stages),
            "animation_visual_plan_identity")
    details = _visual_validation(plan, records, validation)
    primitives, timings = _handoff(plan, handoff_dict, visual_revision, target_profile)
    index = SyncIndex(context)
    by_visual = {i.binding.intent_id: i for i in original}
    by_segment = {s.segment_id: s for s in execution.snapshot.script.segments}
    by_objective = {o.objective_id: o for o in inputs.objectives}
    intents, rows, consumed = [], [], set()
    for record in records:
        visual = by_visual[record["intent_id"]]
        binding = visual.binding
        utterance = index.utterances[binding.anchor.utterance_id].utterance
        segment = by_segment[utterance.segment_id]
        require(segment.purpose in ALLOWED_TEACHING_MOVES, "animation_teaching_purpose_not_admitted")
        require(set(binding.objective_ids) <= by_objective.keys() and
                set(binding.concept_ids) == {by_objective[o].concept_id for o in binding.objective_ids},
                "animation_foreign_concept")
        kind = record["semantic_kind"]
        require(kind in ACTION_PURPOSE, "animation_semantics_not_admitted")
        action, purpose = ACTION_PURPOSE[kind]
        window = index.resolve(binding)
        detail = details[record["intent_id"]]
        elements = _index(detail["grammar"]["elements"], "id", "animation_grammar_identity")
        layouts = _index(detail["layout"]["nodes"], "node_id", "animation_layout_identity")
        require(set(elements) == set(layouts), "animation_layout_identity")
        associations = _source_items(record, elements)
        children = []
        for eid in sorted(elements):
            pid = record["intent_id"] + ":" + eid
            require(pid in primitives and pid not in consumed, "animation_primitive_identity")
            primitive, timing, element = primitives[pid], timings[pid], elements[eid]
            require(primitive["primitive_type"] == element["primitive"] and
                    canonical(primitive["source_refs"]) == canonical(element["source_ids"]) and
                    canonical(primitive["reasoning_refs"]) == canonical(record["reasoning_refs"]) and
                    set(primitive["source_refs"]) <= set(binding.evidence_ids) and
                    set(layouts[eid]["source_ids"]) <= set(binding.evidence_ids),
                    "animation_primitive_lineage_mismatch")
            require(type(timing["narration_revision"]) is int and
                    timing["narration_revision"] == visual_revision and
                    timing["start_ms"] == window.start_ms and timing["end_ms"] == window.end_ms,
                    "animation_primitive_timing_mismatch")
            source_ids, role = associations[eid]
            children.append(dict(primitive_id=pid, primitive_type=primitive["primitive_type"],
                source_refs=list(primitive["source_refs"]), reasoning_refs=list(primitive["reasoning_refs"]),
                timing=dict(timing), element=element, layout=layouts[eid],
                source_item_ids=source_ids, semantic_role=role))
            consumed.add(pid)
        identity = dict(policy=POLICY, visual_ref=asdict(visual_sync.to_ref()),
            visual_plan_fingerprint=plan.fingerprint, handoff_fingerprint=handoff_dict["handoff_fingerprint"],
            visual_intent_id=binding.intent_id, record_sha256=digest(record),
            action=action, purpose=purpose, primitive_ids=[c["primitive_id"] for c in children])
        iid = "animation-intent-" + digest(identity)
        current_binding = IntentBinding(iid, binding.target_id, binding.anchor,
            binding.evidence_ids, binding.objective_ids, binding.concept_ids, purpose)
        intents.append(AnimationIntent(current_binding, binding.intent_id, action))
        obligations = record["semantic_obligations"]
        source_order = [item["id"] for item in obligations["source_items"]]
        rows.append(dict(schema=SCHEMA, policy=POLICY, intent_id=iid,
            target_id=binding.target_id, visual_intent_id=binding.intent_id,
            action=action, purpose=purpose, semantic_kind=kind, teaching_move=segment.purpose,
            scene_id=window.scene_id, scene_start_ms=0,
            scene_end_ms=index.scenes[window.scene_id].duration_ms,
            window=dict(start_ms=window.start_ms, end_ms=window.end_ms), anchor=asdict(binding.anchor),
            narration_revision=visual_revision, visual_revision=visual_revision,
            visual_plan_fingerprint=plan.fingerprint, visual_handoff_id=handoff_dict["handoff_id"],
            visual_handoff_fingerprint=handoff_dict["handoff_fingerprint"],
            visual_sync_ref=asdict(visual_sync.to_ref()), director_ref=payload["director_ref"],
            target_profile=target_profile, source_id=record["source_id"],
            source_sha256=record["source_sha256"], record_sha256=digest(record),
            evidence_refs=list(binding.evidence_ids), reasoning_refs=list(record["reasoning_refs"]),
            objective_ids=list(binding.objective_ids), concept_ids=list(binding.concept_ids),
            uncertainty=record["uncertainty"], semantic_obligations=obligations,
            source_order=source_order, semantic_order=obligations.get("chronological_order", []),
            primitive_order_policy="RAW_ID_TECHNICAL_TIE_BREAK_NOT_PEDAGOGICAL_ORDER",
            primitive_rows=children, timing_basis=context.speech.basis,
            private=True, evidence_kind="TECHNICAL_SOURCE_DERIVED", requires_review=True,
            accepted=False, release_ready=False, product_accepted=False,
            audio_complete=False, audio_reconciliation_open=True))
    require(consumed == set(primitives), "animation_unbound_visual_primitive")
    synchronized = sync_animation_intents(context, visuals, tuple(intents))
    require(not synchronized.issues, "animation_director_sync_blocked")
    return tuple(intents), rows


def validate_derived_animation(inputs, execution, visual_sync, records, plan_dict,
                               handoff_dict, validation, typed_intents, rows, **settings):
    expected, expected_rows = derive_animation_intents(inputs, execution, visual_sync,
        records, plan_dict, handoff_dict, validation, **settings)
    require(type(typed_intents) is tuple and all(isinstance(i, AnimationIntent) for i in typed_intents)
            and canonical([asdict(i) for i in typed_intents]) == canonical([asdict(i) for i in expected])
            and canonical(rows) == canonical(expected_rows), "animation_intent_derivation_mismatch")
    return typed_intents, rows
