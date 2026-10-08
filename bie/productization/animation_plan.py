"""Bounded native Animation composition for BIE-PROD-035.

The caller supplies independently rederived current Visual/Director rows.  This
module binds native tracks to exact child primitive and TimingBinding identities.
The Director sync remains the parent obligation; it is never relabelled as the
AnimationPlan.  Static axes remain static.  The only admitted actions are an
evidence-bound introduction of declared data, chronological revelation, and
attention-only emphasis of declared cellular structure.  No flow is inferred.
"""
from dataclasses import asdict, replace

from bie.animation_intelligence.ani_orchestrator import STAGES, OWNERS, StageReceipt, run_pipeline
from bie.animation_intelligence.vis_ani_adoption import adopt_visual_handoff
from bie.animation_intelligence.animation_plan_contract import AnimationPlan, AnimationTrack
from bie.animation_intelligence.contracts import AnimationContext, CueWindow, VisualElementState
from bie.animation_intelligence.semantic_animation_intent import build_semantic_animation_intent
from bie.animation_intelligence.reveal_selection import select_reveal
from bie.animation_intelligence.emphasize_selection import select_emphasis
from bie.animation_intelligence.attention_contracts import AttentionTarget
from bie.animation_intelligence.attention_model import build_attention_model
from bie.animation_intelligence.focal_timing import plan_focal_timing
from bie.animation_intelligence.narration_attention_sync import sync_narration_attention
from bie.animation_intelligence.competing_motion_prevention import prevent_competing_motion
from bie.animation_intelligence.domain_animation_registry import DomainAdapter, DomainAnimationRegistry
from bie.animation_intelligence.data_animation_grammar import plan_distribution_reveal
from bie.animation_intelligence.temporal_contracts import Context as TemporalContext, Event as TemporalEvent
from bie.animation_intelligence.timeline_animation import animate_timeline
from bie.animation_intelligence.chronology_reveal import animate_chronology
from bie.animation_intelligence.easing_contracts import MotionContext
from bie.animation_intelligence.duration_rules import resolve_duration
from bie.animation_intelligence.easing_semantics import select_easing_semantics
from bie.animation_intelligence.global_timeline_solver import TrackRequest, solve
from bie.animation_intelligence.continuity_ledger import ContinuityLedger, ContinuityRecord
from bie.animation_intelligence.qa_contracts import Event
from bie.animation_intelligence.animation_purpose_alignment_qa import evaluate as purpose_qa
from bie.animation_intelligence.animation_synchronization_qa import evaluate as synchronization_qa
from bie.animation_intelligence.temporal_conflict_qa import evaluate as temporal_qa
from bie.animation_intelligence.excessive_motion_qa import evaluate as motion_qa
from bie.animation_intelligence.ani_accessibility import AccessibilityPolicy, enforce_animation_accessibility
from bie.animation_intelligence.animation_performance_budget import (
    AnimationComplexity, AnimationBudget, evaluate_budget, assert_required_tracks_preserved)
from bie.animation_intelligence.ani_trace_matrix import TrackTrace, audit_trace, require_trace_pass
from bie.animation_intelligence.ani_sceneir_handoff import build_sceneir_handoff, require_sceneir_ready
from bie.animation_intelligence.ani_replay_currentness import (
    VersionVector, make_replay_record, assert_current)
from bie.visual_intelligence.capability_handoff import (
    PrimitiveRequirement, AssetBinding, TimingBinding, build_downstream_handoff)
from .contracts import ProducerError, require, canonical, digest


POLICY = "source-obligation-native-animation-composition-v1"
FAMILIES = {
    "sampled_chart": ("data_science", "declared_distribution", "reveal", "introduce"),
    "timeline": ("history", "declared_chronology", "reveal", "show_sequence"),
    "cellular": ("biology", "declared_structural_focus", "emphasize", "focus"),
}
MAX_TRACKS = 128


def _data(value):
    return asdict(value)


def _allowed(result, code):
    require(result.status in ("PASS", "REVIEW"), code)
    require(getattr(result, "accepted", False) is False, "animation_acceptance_promoted")
    require(not getattr(result, "blockers", ()), code)
    return result


def _verified_handoff(handoff, revision, fingerprint):
    require(type(handoff) is dict and handoff.get("accepted") is False and
            handoff.get("review_required") is True, "animation_acceptance_promoted")
    # Rebuild only the fingerprint of the exact supplied Visual handoff, never
    # synthesize a replacement input or infer target capability.
    primitives = tuple(PrimitiveRequirement(**p) for p in handoff["primitives"])
    assets = tuple(AssetBinding(**a) for a in handoff["assets"])
    timing = tuple(TimingBinding(**t) for t in handoff["timing"])
    caps = {cap for p in primitives for cap in p.capability_tags}
    require(not handoff["unsupported_capabilities"] and not handoff["planned_fallbacks"],
            "animation_visual_capability_unresolved")
    rebuilt = build_downstream_handoff(handoff_id=handoff["handoff_id"],
        plan_fingerprint=handoff["plan_fingerprint"], primitives=primitives, assets=assets,
        timing=timing, accessibility_ready=handoff["accessibility_ready"],
        target_capabilities=tuple(sorted(caps)), target_profile=handoff["target_profile"])
    require(canonical(_data(rebuilt)) == canonical(handoff), "animation_visual_handoff_mismatch")
    return adopt_visual_handoff(handoff, revision, expected_plan_fingerprint=fingerprint)


def _prepare(rows, settings, handoff):
    require(type(rows) in (list, tuple) and rows, "animation_intents_required")
    require(len({r["scene_id"] for r in rows}) == 1, "animation_multiscene_timing_contract_required")
    require(type(settings.get("reduced_motion_required")) is bool, "animation_reduced_motion_policy")
    first = rows[0]
    adopted = _verified_handoff(handoff, first["visual_revision"], first["visual_plan_fingerprint"])
    require(settings["budget"]["profile_id"] == adopted.target_profile, "animation_target_profile_mismatch")
    primitive_map = {p["primitive_id"]: p for p in handoff["primitives"]}
    timing_map = {t["visual_id"]: t for t in handoff["timing"]}
    require(len(primitive_map) == len(handoff["primitives"]), "animation_duplicate_primitive")
    require(len(timing_map) == len(handoff["timing"]), "animation_duplicate_timing")
    require(set(primitive_map) == set(timing_map), "animation_primitive_timing_mismatch")
    seen, entries, abstentions = set(), [], []
    for row in rows:
        require(row["semantic_kind"] in FAMILIES, "animation_unsupported_domain")
        domain, capability, action, purpose = FAMILIES[row["semantic_kind"]]
        require(row["action"] == action, "animation_unsupported_action")
        require(row["purpose"] == purpose, "animation_purpose_action_mismatch")
        require(row["visual_revision"] == first["visual_revision"] and
                row["narration_revision"] == first["narration_revision"] and
                row["visual_plan_fingerprint"] == adopted.plan_fingerprint and
                row["visual_handoff_id"] == adopted.handoff_id and
                row["target_profile"] == adopted.target_profile,
                "animation_visual_handoff_mismatch")
        start, end = row["window"]["start_ms"], row["window"]["end_ms"]
        require(row["scene_start_ms"] <= start < end <= row["scene_end_ms"],
                "animation_track_outside_scene")
        require(row["evidence_refs"] and row["reasoning_refs"] and row["objective_ids"] and
                row["concept_ids"], "animation_grounding_missing")
        require(row.get("accepted") is False and row.get("requires_review") is True and
                row.get("release_ready") is False and row.get("audio_complete") is False,
                "animation_acceptance_promoted")
        obligations = row["semantic_obligations"]
        require(obligations["kind"] == row["semantic_kind"] and obligations["source_items"],
                "animation_domain_obligations_missing")
        if row["semantic_kind"] == "cellular":
            require(not obligations["transports"] and not obligations["containments"],
                    "animation_cellular_motion_obligations_unavailable")
        if row["semantic_kind"] == "sampled_chart":
            require(obligations["sampled_data"] is True and obligations["exact_curve_claim"] is False,
                    "animation_sampled_data_claim_invalid")
        children = []
        for p in row["primitive_rows"]:
            pid = p["primitive_id"]
            require(pid not in seen, "animation_duplicate_primitive")
            seen.add(pid)
            require(pid in primitive_map and pid in timing_map, "animation_unknown_target")
            require(p["timing"]["visual_id"] == pid and canonical(p["timing"]) == canonical(timing_map[pid]),
                    "animation_primitive_timing_mismatch")
            require(p["primitive_type"] == primitive_map[pid]["primitive_type"] and
                    canonical(p["source_refs"]) == canonical(primitive_map[pid]["source_refs"]) and
                    canonical(p["reasoning_refs"]) == canonical(primitive_map[pid]["reasoning_refs"]),
                    "animation_primitive_lineage_mismatch")
            require(set(p["source_refs"]) <= set(row["evidence_refs"]) and
                    set(p["reasoning_refs"]) <= set(row["reasoning_refs"]),
                    "animation_grounding_mismatch")
            timing = p["timing"]
            require(timing["narration_revision"] == row["narration_revision"] and
                    timing["start_ms"] <= start < end <= timing["end_ms"],
                    "animation_primitive_timing_mismatch")
            element = p["element"]
            require(pid == row["visual_intent_id"] + ":" + element["id"] and
                    element["primitive"] == p["primitive_type"], "animation_unknown_target")
            if element["role"] in ("chart_frame", "timeline_axis"):
                abstentions.append(dict(primitive_id=pid, reason="static_context_axis_no_motion_obligation"))
                continue
            expected_role = {"sampled_chart": "data_series", "timeline": "historical_event"}.get(row["semantic_kind"])
            require(expected_role is None or element["role"] == expected_role, "animation_unsupported_target_role")
            children.append(p)
        require(children, "animation_semantic_targets_required")
        if row["semantic_kind"] == "timeline":
            order = row["semantic_obligations"]["chronological_order"]
            ranks = {source_id: i for i, source_id in enumerate(order)}
            require(len(ranks) == len(order), "animation_chronology_invalid")
            require({p["element"]["id"] for p in children} == {"event:" + k for k in ranks},
                    "animation_chronology_invalid")
            children.sort(key=lambda p: ranks[p["element"]["id"][len("event:"):]])
            ordering = "verified_declared_chronology"
        else:
            children.sort(key=lambda p: p["primitive_id"])
            ordering = "technical_case_sensitive_primitive_id_tiebreak_not_pedagogical_truth"
        for index, child in enumerate(children):
            entries.append(dict(row=row, primitive=child, domain=domain, capability=capability,
                action=action, purpose=purpose, technical_order=index, ordering=ordering,
                reduced_motion=settings["reduced_motion_required"],
                track_id="animation-track-" + digest(dict(intent=row["intent_id"], primitive=child["primitive_id"],
                    policy=POLICY))))
    require(seen == set(primitive_map), "animation_primitive_lineage_missing")
    require(0 < len(entries) <= MAX_TRACKS, "animation_track_budget")
    return adopted, entries, abstentions


def _ctx(entry, start=None, end=None):
    row = entry["row"]
    return AnimationContext(entry["track_id"], entry["purpose"], tuple(row["evidence_refs"]),
        tuple(row["reasoning_refs"]), row["visual_plan_fingerprint"],
        CueWindow(row["intent_id"], row["window"]["start_ms"] if start is None else start,
                  row["window"]["end_ms"] if end is None else end, row["narration_revision"]),
        row["visual_revision"], row["target_profile"], reduced_motion=entry["reduced_motion"],
        uncertainty=row["uncertainty"],
        payload=dict(parent_visual_intent_id=row["visual_intent_id"], policy=POLICY))


def _element(entry):
    child = entry["primitive"]
    return VisualElementState(child["primitive_id"], child["element"]["role"],
        "verified-visual-state-" + digest(child["element"]), tuple(child["source_refs"]),
        identity_id=child["primitive_id"], geometry_kind=child["primitive_type"], payload=child["element"]["payload"])


def _domain(row, registry, entries):
    domain, capability, _, _ = FAMILIES[row["semantic_kind"]]
    adapter = registry.resolve(domain, capability)
    source = row["semantic_obligations"]["source_items"]
    if row["semantic_kind"] == "sampled_chart":
        result = _allowed(plan_distribution_reveal(row["intent_id"] + ":domain",
            [dict(bin_id=x["id"], value=x["value"], label=x["label"]) for x in source],
            source_refs=tuple(row["evidence_refs"]), normalized=False), "animation_domain_blocked")
        return dict(adapter=_data(adapter), native=_data(result), claim="descriptive_declared_samples")
    if row["semantic_kind"] == "timeline":
        ranks = {name: i for i, name in enumerate(row["semantic_obligations"]["chronological_order"])}
        ctx = TemporalContext(row["intent_id"], tuple(row["evidence_refs"]), tuple(row["reasoning_refs"]),
            row["visual_plan_fingerprint"], row["visual_revision"], row["uncertainty"])
        events = tuple(TemporalEvent(x["id"], x["label"], row["evidence_refs"][0], ranks[x["id"]],
            x["order_key"], x["uncertain"]) for x in source)
        timeline = _allowed(animate_timeline(ctx, row["intent_id"], events,
            scale_mode="ordinal", preserve_uncertainty=True), "animation_domain_blocked")
        chronology = _allowed(animate_chronology(ctx, row["intent_id"], events,
            exact_date_claims=False), "animation_domain_blocked")
        return dict(adapter=_data(adapter), timeline=_data(timeline), chronology=_data(chronology),
            claim="declared_event_order_not_elapsed_time", source_uncertainty_retained=True)
    # There is no native biological flow justification in Task034 static source.
    # Execute native attention-only selection here, within DOMAIN. TIMELINE
    # later realizes these decisions in the scheduler's bounded subwindows.
    selected = []
    for entry in entries:
        if entry["row"]["intent_id"] == row["intent_id"]:
            selected.append(_data(_allowed(select_emphasis(_ctx(entry), element=_element(entry),
                reason="identify_source_declared_structure_in_current_narration", quantitative_semantics=True,
                allow_scale_emphasis=False), "animation_domain_blocked")))
    require(selected, "animation_domain_obligations_missing")
    return dict(adapter=_data(adapter), native_engine="select_emphasis", claim="attention_to_declared_static_structure",
        native=selected, transport_executed=False, physical_motion_claim=False,
        source_item_ids=[x["id"] for x in source])


def _compose(rows, settings, run_id, handoff, fault):
    state = dict(rows=rows, settings=settings, outputs={}, tracks=[], events=[], native_steps={})
    registry = DomainAnimationRegistry()
    for family, (domain, capability, _, _) in FAMILIES.items():
        registry.register(DomainAdapter("task035:" + family, domain, settings["domain_registry_version"],
            (capability,), 1))

    def hook(name):
        if fault is not None:
            fault(name)

    def execute(stage):
        if stage == "VIS_ADOPT":
            adopted, entries, abstentions = _prepare(rows, settings, handoff)
            state.update(adopted=adopted, entries=entries)
            output = dict(adoption=_data(adopted), abstentions=abstentions)
        elif stage == "SEM":
            decisions = []
            for entry in state["entries"]:
                decision = _allowed(build_semantic_animation_intent(_ctx(entry),
                    target_ids=(entry["primitive"]["primitive_id"],),
                    semantic_change=entry["purpose"], preferred_actions=(entry["action"],)),
                    "animation_semantics_blocked")
                decisions.append(_data(decision))
            output = dict(decisions=decisions, default_reveal_used=False, positional_timing_used=False)
        elif stage == "ATTN":
            targets = tuple(AttentionTarget(e["primitive"]["primitive_id"], e["primitive"]["element"]["role"],
                .5, tuple(e["row"]["evidence_refs"]), tuple(e["row"]["reasoning_refs"]), .1, .5)
                for e in state["entries"])
            result = _allowed(build_attention_model(targets), "animation_attention_blocked")
            state["attention_targets"] = {t.target_id: t for t in targets}
            output = dict(model=_data(result), policy="bounded_technical_equal_importance_nonempirical",
                          concurrency_limit=1, motion_salience=.1)
        elif stage == "DOMAIN":
            output = dict(registry=registry.snapshot(), plans=[_domain(r, registry, state["entries"]) for r in rows])
            hook("after_ANIMATION_semantic_domain")
        elif stage == "EASE":
            policies = []
            for entry in state["entries"]:
                row = entry["row"]
                complexity = min(1., len(row["semantic_obligations"]["source_items"]) / 8)
                motion = MotionContext(entry["track_id"], entry["action"], tuple(row["evidence_refs"]),
                    tuple(row["reasoning_refs"]), row["visual_plan_fingerprint"], row["narration_revision"],
                    settings["reduced_motion_required"], .5, complexity)
                duration = _allowed(resolve_duration(motion,
                    narration_window_ms=row["window"]["end_ms"] - row["window"]["start_ms"],
                    semantic_steps=1, allow_scene_extension=False), "animation_duration_blocked")
                easing = _allowed(select_easing_semantics(motion), "animation_easing_blocked")
                entry.update(duration=duration.duration_ms, easing=easing.easing)
                policies.append(dict(track_id=entry["track_id"], duration=_data(duration), easing=_data(easing),
                    complexity_basis="bounded_source_item_count_over_eight_technical_heuristic"))
            output = dict(policies=policies, scene_extension_allowed=False)
        elif stage == "TIMELINE":
            requests = []
            # Explicit chronology determines source teaching sequence. Other
            # ties use the documented technical ID order, never source-page order.
            for entry in state["entries"]:
                row = entry["row"]
                requests.append(TrackRequest(entry["track_id"], row["window"]["start_ms"], entry["duration"],
                    row["window"]["start_ms"], row["window"]["end_ms"],
                    1. - entry["technical_order"] / (MAX_TRACKS + 1),
                    "task035-essential-attention", True))
            timeline = solve(requests)
            require(timeline.solved and not timeline.unsat_core, "animation_timeline_unsat")
            scheduled = {t.track_id: t for t in timeline.scheduled}
            require(set(scheduled) == {e["track_id"] for e in state["entries"]}, "animation_timeline_track_loss")
            windows, decisions = [], []
            for entry in state["entries"]:
                row, child, slot = entry["row"], entry["primitive"], scheduled[entry["track_id"]]
                require(child["timing"]["start_ms"] <= slot.start_ms < slot.end_ms <= child["timing"]["end_ms"] and
                    row["scene_start_ms"] <= slot.start_ms < slot.end_ms <= row["scene_end_ms"],
                    "animation_track_outside_scene")
                ctx, element = _ctx(entry, slot.start_ms, slot.end_ms), _element(entry)
                if entry["action"] == "reveal":
                    decision = select_reveal(ctx, elements=(element,), dependency_order=(element.element_id,), progressive=True)
                else:
                    decision = select_emphasis(ctx, element=element,
                        reason="identify_source_declared_structure_in_current_narration", quantitative_semantics=True,
                        allow_scale_emphasis=False)
                _allowed(decision, "animation_semantics_blocked")
                decisions.append(_data(decision))
                step = decision.steps[0]
                require(len(decision.steps) == 1 and decision.action == entry["action"] and step.action == entry["action"] and
                        step.target_ids == (child["primitive_id"],) and
                        (step.start_ms, step.end_ms) == (slot.start_ms, slot.end_ms), "animation_native_motion_mismatch")
                expected_source = None if entry["action"] == "reveal" else element.state_id
                expected_effect = ("dependency_ordered_reveal" if entry["action"] == "reveal" else
                                   "increase_attention_without_changing_semantic_value")
                expected_payload = ({"index": 0} if entry["action"] == "reveal" else
                    {"mode": "highlight" if element.semantic_role in {"text", "label", "equation"} else "accent",
                     "reason": "identify_source_declared_structure_in_current_narration", "scale_allowed": False})
                require(step.source_state_id == expected_source and step.target_state_id == element.state_id and
                        step.semantic_effect == expected_effect and canonical(step.payload) == canonical(expected_payload),
                        "animation_native_state_mismatch")
                state["native_steps"][entry["track_id"]] = step
                payload = dict(step.payload, semantic_effect=step.semantic_effect, easing=entry["easing"],
                    director_animation_intent_id=row["intent_id"], parent_visual_target_id=row["target_id"],
                    parent_visual_intent_id=row["visual_intent_id"], scene_id=row["scene_id"],
                    purpose=entry["purpose"], objective_ids=row["objective_ids"], concept_ids=row["concept_ids"],
                    uncertainty=row["uncertainty"], visual_primitive_id=child["primitive_id"],
                    timing_binding=child["timing"], source_item_ids=child.get("source_item_ids", []),
                    ordering_basis=entry["ordering"], source_state_id=step.source_state_id,
                    target_state_id=step.target_state_id, flash_hz=0, native_decision_fingerprint=decision.fingerprint)
                state["tracks"].append(AnimationTrack(entry["track_id"], step.action, step.target_ids,
                    slot.start_ms, slot.end_ms, tuple(child["source_refs"]), tuple(child["reasoning_refs"]),
                    "DOMAIN", None, payload))
                state["events"].append(Event(entry["track_id"], step.action, step.target_ids,
                    slot.start_ms, slot.end_ms, entry["purpose"], tuple(child["source_refs"]),
                    tuple(child["reasoning_refs"]), row["narration_revision"], .5, .1, True, payload))
                target = state["attention_targets"][child["primitive_id"]]
                focus = _allowed(plan_focal_timing(decision_id=entry["track_id"] + ":focus", target=target,
                    cue_start_ms=slot.start_ms, cue_end_ms=slot.end_ms, narration_revision=row["narration_revision"],
                    lead_ms=0, tail_ms=0, min_focus_ms=1), "animation_attention_blocked")
                windows.extend(replace(w, payload=dict(w.payload, evidence_refs=row["evidence_refs"],
                    reasoning_refs=row["reasoning_refs"])) for w in focus.windows)
            attention = _allowed(sync_narration_attention(decision_id="task035:narration-attention",
                narration_revision=rows[0]["narration_revision"], cue_windows=tuple(_ctx(e).cue for e in state["entries"]),
                attention_windows=windows, allow_overlap_same_target=False), "animation_attention_blocked")
            competing = _allowed(prevent_competing_motion(decision_id="task035:competing-motion", windows=windows,
                motion_targets={w.window_id: w.target_ids for w in windows}, max_simultaneous_motion=1),
                "animation_attention_blocked")
            output = dict(timeline=_data(timeline), native_actions=decisions, attention_sync=_data(attention),
                competing_motion=_data(competing), attention_windows=[_data(w) for w in windows])
            hook("after_ANIMATION_timeline")
        elif stage == "CONTINUITY":
            ledger, retained = ContinuityLedger(), []
            for entry in state["entries"]:
                child, row = entry["primitive"], entry["row"]
                source_element = _element(entry)
                step = state["native_steps"][entry["track_id"]]
                # The bounded actions introduce or focus the exact current
                # semantic state. Resolve the native realization's target ID
                # through the verified Visual state catalog. No alternate state,
                # role, notation, representation, or position is synthesized.
                catalog = {source_element.state_id: (source_element, child["layout"])}
                require(step.target_state_id in catalog and
                        (step.source_state_id is None if entry["action"] == "reveal" else
                         step.source_state_id == source_element.state_id), "animation_continuity_state_mismatch")
                target_element, target_layout = catalog[step.target_state_id]
                source_box, target_box = child["layout"]["box"], target_layout["box"]
                source_position = (source_box["x"], source_box["y"])
                target_position = (target_box["x"], target_box["y"])
                before = ContinuityRecord(row["scene_id"], source_element.identity_id, source_element.element_id,
                    source_element.semantic_role, None, None, source_element.geometry_kind,
                    source_position, source_position)
                after = ContinuityRecord(row["scene_id"], target_element.identity_id, target_element.element_id,
                    target_element.semantic_role, None, None, target_element.geometry_kind,
                    target_position, target_position)
                ledger.add(before)
                ledger.add(after)
                retained.append(dict(track_id=entry["track_id"], before=_data(before), after=_data(after),
                    source_state_id=step.source_state_id, target_state_id=step.target_state_id,
                    target_state_fingerprint=digest(child["element"]), native_semantic_effect=step.semantic_effect))
            output = dict(records=retained, authorized_changes=[], passed=True)
        elif stage == "QA":
            events, tracks = state["events"], state["tracks"]
            cues = [dict(cue_id=r["intent_id"], **r["window"]) for r in rows]
            purpose = _allowed(purpose_qa(events), "animation_purpose_qa_blocked")
            sync = _allowed(synchronization_qa(events, rows[0]["narration_revision"], cues),
                            "animation_sync_qa_blocked")
            temporal = _allowed(temporal_qa(events, max_parallel_essential=1), "animation_temporal_qa_blocked")
            motion = _allowed(motion_qa(events, reduced_motion_requested=settings["reduced_motion_required"]),
                              "animation_motion_qa_blocked")
            accessibility = _allowed(enforce_animation_accessibility(tracks,
                AccessibilityPolicy(settings["reduced_motion_required"])), "animation_accessibility_blocked")
            require(not accessibility.replacements, "animation_reduced_motion_realization_required")
            points = {x for t in tracks for x in (t.start_ms, t.end_ms)}
            concurrency = max(sum(t.start_ms <= x < t.end_ms for t in tracks) for x in points)
            complexity = AnimationComplexity(tuple(t.track_id for t in tracks), len(tracks), concurrency, 0, 0, 0, 0, 0)
            budget = evaluate_budget(complexity, AnimationBudget(**settings["budget"]))
            require(budget.action == "PASS", "animation_performance_blocked")
            assert_required_tracks_preserved(budget, [t.track_id for t in tracks])
            qa_ids = (purpose.qa_id, sync.qa_id, temporal.qa_id, motion.qa_id, "animation:accessibility", "animation:performance")
            trace = audit_trace(tuple(TrackTrace(t.track_id, t.source_refs, t.reasoning_refs, t.target_ids,
                t.owner_stage, qa_ids, ("ani:" + t.track_id,), True) for t in tracks))
            require_trace_pass(trace)
            output = dict(purpose=_data(purpose), synchronization=_data(sync), temporal=_data(temporal),
                motion=_data(motion), accessibility=_data(accessibility), performance=_data(budget),
                complexity=_data(complexity), trace=_data(trace))
            hook("after_ANIMATION_qa")
        else:
            first, adopted, tracks = rows[0], state["adopted"], tuple(state["tracks"])
            plan_id = "animation:" + digest(dict(run_id=run_id, rows=rows, settings=settings,
                                                handoff_fingerprint=handoff["handoff_fingerprint"]))
            plan = AnimationPlan(plan_id, "1.0.0", adopted.handoff_id, adopted.plan_fingerprint,
                first["visual_revision"], first["narration_revision"], adopted.target_profile, tracks,
                min(r["scene_start_ms"] for r in rows), max(r["scene_end_ms"] for r in rows),
                tuple(sorted({s for t in tracks for s in t.source_refs})),
                tuple(sorted({r for t in tracks for r in t.reasoning_refs})), settings["reduced_motion_required"])
            require(plan.accepted is False, "animation_acceptance_promoted")
            hook("after_ANIMATION_plan")
            downstream = build_sceneir_handoff(plan)
            require_sceneir_ready(downstream)
            require(downstream.accepted is False and downstream.review_required is True,
                    "animation_acceptance_promoted")
            vector = VersionVector(first["visual_revision"], first["narration_revision"],
                settings["policy_revision"], settings["domain_registry_version"], adopted.target_profile)
            input_fingerprint = digest(dict(rows=rows, settings=settings, handoff=handoff))
            dependencies = (adopted.handoff_id, adopted.plan_fingerprint,
                            *(r["intent_id"] for r in rows))
            replay = make_replay_record(run_id, vector, input_fingerprint, plan.plan_fingerprint, dependencies)
            assert_current(replay, vector, input_fingerprint, dependencies)
            state.update(plan=plan, handoff=downstream)
            output = dict(plan_fingerprint=plan.plan_fingerprint, handoff=_data(downstream),
                replay=_data(replay), version_vector=_data(vector), sceneir_handoff_ready=True,
                global_scene_ir_executed=False)
            hook("after_ANIMATION_handoff")
        state["outputs"][stage] = output
        return state, StageReceipt(stage, OWNERS[stage], "PASS",
            "animation-stage:" + digest(dict(stage=stage, output=output)), (), False)

    handlers = {stage: (lambda current, s=stage: execute(s)) for stage in STAGES}
    final, report = run_pipeline(handlers, state)
    require(report.passed and not report.blockers and tuple(r.stage for r in report.receipts) == STAGES,
            "animation_native_prefix_incomplete")
    details = dict(policy=POLICY, stages=[_data(r) for r in report.receipts], outputs=state["outputs"],
        qa=state["outputs"]["QA"], rows_fingerprint=digest(rows), settings_fingerprint=digest(settings),
        requires_review=True, accepted=False, release_ready=False, product_accepted=False,
        audio_complete=False, audio_reconciliation_open=True, global_scene_ir_executed=False,
        source_order_preserved=True, evidence_kind="TECHNICAL_SOURCE_DERIVED")
    return final["plan"], final["handoff"], details


def build_current_animation(rows, settings, *, run_id, handoff, fault=None):
    """Compose all nine native stages; callers persist the exact native output."""
    return _compose(rows, settings, run_id, handoff, fault)


def validate_current_animation(rows, settings, *, run_id, handoff, plan_dict, handoff_dict, details=None):
    """Recompute identities from independently verified current upstream rows."""
    require(plan_dict.get("accepted") is False and handoff_dict.get("accepted") is False and
            handoff_dict.get("review_required") is True, "animation_acceptance_promoted")
    plan, downstream, actual = build_current_animation(rows, settings, run_id=run_id, handoff=handoff)
    require(plan_dict.get("plan_fingerprint") == plan.plan_fingerprint and
            canonical(plan_dict) == canonical(_data(plan)), "animation_plan_identity_mismatch")
    require(canonical(handoff_dict) == canonical(_data(downstream)), "animation_handoff_identity_mismatch")
    if details is not None:
        require(canonical(details) == canonical(actual), "animation_details_identity_mismatch")
    return plan, downstream, actual
