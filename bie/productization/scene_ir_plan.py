"""Native single-scene composition from reopened current producer artifacts.

No code generation, rendering, provider call or upstream publication occurs here.
"""
from dataclasses import asdict
from copy import deepcopy

from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import DirectorRevisionStore
from bie.director.director_artifacts import reference
from bie.director.sync_contract import build_sync_context, SyncIndex
from bie.scene_ir.ani_dsl_adopter import adopt_ani_handoff
from bie.scene_ir.unified_scene_ir_contract import UnifiedElement, UnifiedTrack, UnifiedSceneIRDocument
from bie.scene_ir.unified_scene_ir_codec import encode_scene_ir, roundtrip_scene_ir
from bie.scene_ir.dsl_orchestrator import validate_scene_ir_document, require_dsl_gate
from bie.scene_ir.narration_cues import NarrationCue, validate_narration_cues
from bie.scene_ir.compiler_capability_resolution import resolve_compiler_capabilities
from bie.compiler.producer_motion_admission import current_motion_admission
from bie.compiler import governed_motion as gm
from bie.compiler.qa_scene_compile import CompilerQATarget, native_qa_capabilities
from bie.compiler.scene_ir_loader import load_scene_ir_payload
from bie.compiler.reduced_motion import resolve_reduced_motion
from bie.compiler.frame_layout import evaluate_frame_layout
from .director_storage import native_runtime
from .contracts import require, canonical, digest
from .scene_ir_catalog import build_catalog, verify_inventory
from .scene_ir_contract import POLICY, SCHEMA, strict_document, finite_tree

VALIDATORS = frozenset("DSL-VALID-" + n for n in
    ("SCHEMA", "SEMANTIC", "REFERENCE", "TEMPORAL", "SPATIAL", "ACCESSIBILITY", "TRACE"))


def consumer_policy(catalog, tracks, mappings):
    """Explicit source-bound non-geometric variants and only static decomposition overlaps.

    These are native outer declarations, not an alternative motion engine or a
    reduced-safe assertion. The native selector must validate every replacement
    against the live M1 admission, including complete original parameter meaning.
    """
    registry, overlaps = {}, []
    for element in catalog:
        own = [t for t in tracks if t["element_id"] == element["element_id"]]
        if own:
            ref = "scene-ir-m1:" + element["element_id"]
            element["accessibility"]["reduced_motion_variant"] = ref
            registry[ref] = dict(element_id=element["element_id"],
                track_replacements={t["track_id"]: dict(action=t["action"], parameters=deepcopy(t["parameters"])) for t in own},
                reason="Explicit reviewed M1 non-geometric item visibility or focus; technical equivalence only.",
                source_refs=element["source_refs"], reasoning_refs=element["reasoning_refs"])
    for mapping in mappings:
        if mapping["semantic_role"] == "supporting_axis":
            require(len(mapping["native_element_ids"]) == 2, "scene_ir_static_context_lost")
            overlaps.append(dict(elements=mapping["native_element_ids"],
                reason="Unanimated axis and its source-bound label are children of the same verified Visual primitive.",
                source_refs=mapping["source_refs"], reasoning_refs=mapping["reasoning_refs"]))
    return dict(reduced_motion_variants=registry, layout=dict(allow_overlap=overlaps))


def scene_scope(execution, rows):
    """Admit the COMPLETE execution, not merely the scenes with animated rows."""
    architecture = execution.architecture
    scene_ids = [s.scene_id for s in architecture.scenes]
    timing = execution.timeline.scenes
    speech = execution.speech.utterances
    require(len(scene_ids) == 1 and len(timing) == 1 and speech and
            {s.scene_id for s in timing} == set(scene_ids) and
            {s.utterance.scene_id for s in speech} == set(scene_ids) and
            {s.scene_id for s in execution.snapshot.script.segments} == set(scene_ids) and
            {u.scene_id for u in execution.snapshot.utterances} == set(scene_ids),
            "scene_ir_multiple_scenes_unsupported")
    require(rows and {t.utterance.utterance_id for t in speech} ==
            {u.utterance_id for u in execution.snapshot.utterances} and
            {t.utterance.segment_id for t in speech} ==
            {s.segment_id for s in execution.snapshot.script.segments}, "scene_ir_incomplete_director")
    sid = scene_ids[0]
    scene = timing[0]
    require(not scene.requires_audio_replan, "scene_ir_audio_replan_required")
    require(type(scene.duration_ms) is int and scene.duration_ms > 0 and
            all(r["scene_id"] == sid and r["scene_start_ms"] == 0 and
                r["scene_end_ms"] == scene.duration_ms and
                r["timing_basis"] == execution.speech.basis for r in rows), "scene_ir_director_timing")
    require(type(architecture.title) is str and architecture.title.strip() == architecture.title,
            "scene_ir_director_title")
    context = build_sync_context(execution.speech, execution.pauses, execution.emphasis, execution.timeline)
    index = SyncIndex(context)
    utterances = {t.utterance.utterance_id: t for t in speech}
    require(len(utterances) == len(speech), "scene_ir_narration_identity")
    # All utterances survive as scene-local cue references. No final audio or
    # alignment is manufactured; these are native current planning events.
    cues, narration_map = [], []
    revision = rows[0]["narration_revision"]
    for uid, timed in utterances.items():
        events = [e for e in scene.events if e.utterance_id == uid and e.kind == "SPEECH"]
        require(events, "scene_ir_narration_missing")
        targets = tuple(sorted({p["primitive_id"] for r in rows if r["anchor"]["utterance_id"] == uid
                                for p in r["primitive_rows"]}))
        cues.append(NarrationCue("narration:" + uid, min(e.start_ms for e in events),
            max(e.end_ms for e in events), "utterance:" + timed.utterance.fingerprint(), revision, targets))
        narration_map.append(dict(cue_id=cues[-1].cue_id, text_ref=cues[-1].text_ref,
            utterance_id=uid, segment_id=timed.utterance.segment_id, scene_id=sid,
            utterance_fingerprint=timed.utterance.fingerprint(), narration_revision=revision))
    require(not validate_narration_cues(cues, scene.duration_ms, revision), "scene_ir_narration_invalid")
    for row in rows:
        anchor = row["anchor"]
        actual = index.anchor(anchor["utterance_id"], anchor["start_word"], anchor["end_word"])
        require(asdict(actual) == anchor, "scene_ir_narration_stale")
    return dict(scene_id=sid, title=architecture.title, duration_ms=scene.duration_ms,
                narration_cues=[asdict(c) for c in cues], timing_basis=execution.speech.basis,
                narration_map=narration_map,
                source_refs=list(architecture.scenes[0].evidence_ids),
                objective_ids=list(architecture.scenes[0].objective_ids),
                director_snapshot_sha256=execution.snapshot.fingerprint(),
                director_timeline_sha256=digest(asdict(execution.timeline)))


def validate_handoff(handoff, plan, rows, catalog, scope):
    finite_tree(handoff)
    require(set(handoff) == {"handoff_id", "animation_plan_fingerprint", "schema_version", "target_profile",
        "nodes", "unsupported_capabilities", "planned_fallbacks", "blockers", "review_required", "accepted"},
        "scene_ir_handoff_fields")
    require(handoff["schema_version"] == "0.1.0" and
            handoff["animation_plan_fingerprint"] == plan["plan_fingerprint"] and
            handoff["target_profile"] == plan["target_profile"] and
            handoff["review_required"] is True and handoff["accepted"] is False and
            not handoff["unsupported_capabilities"] and not handoff["planned_fallbacks"] and not handoff["blockers"],
            "scene_ir_handoff_contract")
    nodes = handoff["nodes"]
    require(type(nodes) is list and 0 < len(nodes) <= 128 and
            len({n["node_id"] for n in nodes}) == len(nodes) and
            len({n["track_id"] for n in nodes}) == len(nodes), "scene_ir_handoff_identity")
    tracks = {t["track_id"]: t for t in plan["tracks"]}
    require(len(tracks) == len(plan["tracks"]) and set(tracks) == {n["track_id"] for n in nodes},
            "scene_ir_track_coverage")
    targets = {e["element_id"] for e in catalog}
    row_by = {r["intent_id"]: r for r in rows}
    for n in nodes:
        require(set(n) == {"node_id", "track_id", "action", "target_ids", "start_ms", "end_ms",
            "source_refs", "reasoning_refs", "owner_stage", "parameters", "fallback_action"}, "scene_ir_node_fields")
        t = tracks[n["track_id"]]
        require(type(n["start_ms"]) is int and type(n["end_ms"]) is int and
            0 <= n["start_ms"] < n["end_ms"] <= scope["duration_ms"], "scene_ir_node_time")
        require(type(n["target_ids"]) is list and len(n["target_ids"]) == 1 and
            n["target_ids"][0] in targets and n["fallback_action"] is None and
            n["node_id"] == "ani:" + t["track_id"] and
            n["action"] == t["semantic_action"] and n["parameters"] == t["payload"] and
            all(n[k] == t[k] for k in ("target_ids", "start_ms", "end_ms", "source_refs", "reasoning_refs", "owner_stage")),
            "scene_ir_node_plan_mismatch")
        row = row_by.get(n["parameters"].get("director_animation_intent_id"))
        require(row is not None and row["scene_id"] == scope["scene_id"] and
                row["window"]["start_ms"] <= n["start_ms"] < n["end_ms"] <= row["window"]["end_ms"],
                "scene_ir_node_narration_window")
    return nodes


def build_current_scene(service, run, tenant, *, fault=lambda _: None):
    plan, receipt, bundle = service.verified_animation_with_inputs(run, tenant)
    rows = bundle["rows"]
    target = service.configuration(run, tenant)["config"]["visual"]["target"]
    with native_runtime(service, run, None) as assembly:
        director, execution = DirectorConsumers(assembly.io, DirectorRevisionStore(assembly.idempotency))._director(
            bundle["director"].to_ref())
        scope = scene_scope(execution, rows)
        scope["director_artifact_ref"] = asdict(director.to_ref())
    fault("after_SCENE_IR_inputs_verified")
    details = service.read(run, bundle["visual_receipt"]["validation_id"])
    catalog, mappings = build_catalog(rows, target, details)
    fault("after_SCENE_IR_catalog")
    handoff = service.read(run, receipt["handoff_id"])
    nodes = validate_handoff(handoff, plan, rows, catalog, scope)
    adopted, adoption = adopt_ani_handoff(handoff, scene_id=scope["scene_id"], title=scope["title"],
        duration_ms=scope["duration_ms"], element_catalog=catalog, ani_revision=plan["narration_revision"])
    adopted_by = {t["track_id"]: t for t in adopted.to_dict()["tracks"]}
    for node in nodes:
        expected = dict(track_id=node["track_id"], element_id=node["target_ids"][0], action=node["action"],
            start_ms=node["start_ms"], end_ms=node["end_ms"], parameters=node["parameters"],
            source_refs=node["source_refs"], reasoning_refs=node["reasoning_refs"])
        require(adopted_by.get(node["track_id"]) == expected, "scene_ir_adoption_field_loss")
    require(len(adopted_by) == len(nodes), "scene_ir_adoption_track_loss")
    fault("after_SCENE_IR_adoption")
    animated = {tid for n in nodes for tid in n["target_ids"]}
    # Accessibility declarations are part of the admitted element identity.
    # Bind them before M1 seals that identity, never mutate the bound catalog.
    for element in catalog:
        if element["element_id"] in animated:
            element["accessibility"]["reduced_motion_variant"] = "scene-ir-m1:" + element["element_id"]
    with current_motion_admission(service, run, tenant, [e for e in catalog if e["element_id"] in animated]) as bound:
        h3 = consumer_policy(catalog, list(bound["tracks"].values()), mappings)
        elements = tuple(UnifiedElement(e["element_id"], e["element_type"], e["props"], tuple(e["source_refs"]),
            tuple(e["reasoning_refs"]), e["accessibility"], e["normalized_box"]) for e in catalog)
        tracks = tuple(UnifiedTrack(t["track_id"], t["element_id"], t["action"], t["start_ms"], t["end_ms"],
            t["parameters"], tuple(t["source_refs"]), tuple(t["reasoning_refs"])) for t in bound["tracks"].values())
        capabilities = [dict(element_id=e.element_id, element_type=e.element_type, capability_id="comp:" + e.element_type,
            requested_action="render", required=True) for e in elements]
        capabilities += [dict(element_id=t.element_id, element_type=bound["elements"][t.element_id]["element_type"],
            capability_id="comp:m1:" + bound["elements"][t.element_id]["element_type"],
            requested_action=t.action, required=True) for t in tracks]
        doc = UnifiedSceneIRDocument(scope["scene_id"], SCHEMA, scope["title"], scope["duration_ms"], elements,
            tracks, tuple(sorted(set(scope["source_refs"]) | {r for e in elements for r in e.source_refs})),
            tuple(sorted({r for e in elements for r in e.reasoning_refs})),
            layout=dict(boxes=[dict(element_id=e.element_id, **gm.plain(e.normalized_box)) for e in elements],
                relative_constraints=[]), narration_cues=tuple(scope["narration_cues"]),
            capability_requests=tuple(capabilities), compiler_capabilities=tuple(sorted({r["capability_id"] for r in capabilities})),
            metadata={gm.METADATA: bound["metadata"], "compiler_h3": h3, "task036_policy": POLICY, "timing_basis": scope["timing_basis"],
                "audio_complete": False, "audio_reconciliation_open": True}, upstream_revision=plan["narration_revision"])
        compiler_target = CompilerQATarget(target["viewport_width"], target["viewport_height"], 24)
        gm.validate_document(doc.to_dict(), compiler_target)
        variants = {}
        layouts = {}
        for preference in ("standard", "reduced"):
            effective, selection = resolve_reduced_motion(doc.to_dict(), compiler_target, preference)
            require(effective["tracks"] == doc.to_dict()["tracks"] and
                effective["elements"] == doc.to_dict()["elements"] and selection["accepted"] is False and
                selection["learning_equivalence"] == "NOT_EVALUATED" and
                not selection["standard_unresolved_references"], "scene_ir_motion_selection_conservation")
            variants[preference] = selection
            layouts[preference] = evaluate_frame_layout(effective, compiler_target)
            require(layouts[preference]["passed"], "scene_ir_consumer_layout_blocked")
        cap = resolve_compiler_capabilities(doc, native_qa_capabilities(gm.PROFILE), gm.PROFILE)
        require(cap.passed and not cap.fallback_ids, "scene_ir_capability_blocked")
        gate = validate_scene_ir_document(doc)
        require(len(gate.validator_reports) == 7 and {r.validator_id for r in gate.validator_reports} == VALIDATORS
            and all(r.passed for r in gate.validator_reports), "scene_ir_native_validators_incomplete")
        require_dsl_gate(gate)
        encoded = encode_scene_ir(doc)
        require(strict_document(encoded.encode()).to_dict() == doc.to_dict() and
                roundtrip_scene_ir(doc).to_dict() == doc.to_dict(), "scene_ir_codec_conservation")
        inventory = verify_inventory(rows, doc.to_dict()["elements"], mappings, target)
        loaded = load_scene_ir_payload(encoded)
        require(loaded.scene_fingerprint == doc.fingerprint and loaded.canonical_json == encoded and
                loaded.document.to_dict() == doc.to_dict() and loaded.validation_passed, "scene_ir_loader_mismatch")
        fault("after_SCENE_IR_validation")
        private = dict(scope=scope, catalog_mapping=mappings, original_adoption=asdict(adoption),
            track_identity_map=[dict(node_id=n["node_id"], original_track_id=n["track_id"],
                document_track_ids=[n["track_id"]], original_target_ids=n["target_ids"],
                original_parameters=deepcopy(n["parameters"]), original_node_sha256=digest(n)) for n in nodes],
            motion_admission_id=bound["identity"], input_records_sha256=digest(rows),
            inventory=inventory, native_gate=asdict(gate), capability=asdict(cap),
            motion_selection=variants, consumer_layout=layouts)
    return doc, private, bundle, receipt
