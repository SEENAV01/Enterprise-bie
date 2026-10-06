"""Current Visual composition over canonical REP, grammar and planning engines.

The input records are privately derived from verified current Director/source
ancestry by the Task034 intent producer. Historical DIR/REP codecs are not
admission paths for these records. Native algorithms and their evidence pins
remain unchanged. This module publishes the actual native VisualPlan contract.
"""
from dataclasses import asdict
from math import isfinite

from bie.visual_intelligence.visual_plan_contract import STAGES, VisualPlan
from bie.visual_intelligence.visual_orchestrator import VisualOrchestrator
from bie.visual_intelligence.director_handoff_adoption import DirectorContext
from bie.visual_intelligence.representation_core import SemanticIntent, TargetProfile
from bie.visual_intelligence.rep001_candidates import generate
from bie.visual_intelligence.rep002_fitness import score
from bie.visual_intelligence import rep003_diagram_sim, rep005_timeline, rep006_graph, rep008_dimension
from bie.visual_intelligence.representation_grammar_arbitration import RepDecision, Grammar, arbitrate
from bie.visual_intelligence.canonical_family_wiring import build_original_grammar_registry, execute_original_family_path
from bie.visual_intelligence.responsive_composition import Viewport, compose_responsive
from bie.visual_intelligence.layout_solver import solve_layout
from bie.visual_intelligence.safe_area import SafeArea
from bie.visual_intelligence.subtitle_safe_layout import SubtitleZone
from bie.visual_intelligence.asset_contracts import decision as asset_decision
from bie.visual_intelligence.asset_qa import AssetItem, evaluate_asset_qa
from bie.visual_intelligence.text_contracts import TextIntent
from bie.visual_intelligence.on_screen_text_selection import select_on_screen_text
from bie.visual_intelligence.typography_metrics import TypographyRequest, measure
from bie.visual_intelligence.access_contracts import VisualAccessIntent
from bie.visual_intelligence.contrast import evaluate_contrast
from bie.visual_intelligence.readable_size import evaluate_readable_size
from bie.visual_intelligence.alt_description_intent import build_alt_description_intent
from bie.visual_intelligence.color_independent_encoding import evaluate_color_independent_encoding
from bie.visual_intelligence.accessibility_integration import AccessibleVisualNode, integrate_accessibility, assert_accessible_for_handoff
from bie.visual_intelligence.semantic_constraint_engine import evaluate as semantic_policies
from bie.visual_intelligence.semantic_alignment_qa import SemanticSpec, evaluate_semantic_alignment
from bie.visual_intelligence.layout_qa import LayoutElement, Box as QABox, evaluate_layout_qa
from bie.visual_intelligence.clutter_qa import evaluate_clutter_qa
from bie.visual_intelligence.visual_benchmark import evaluate_visual_benchmark
from bie.visual_intelligence.capability_handoff import PrimitiveRequirement, TimingBinding, build_downstream_handoff, assert_handoff_consumable
from bie.visual_intelligence.qa_trace_matrix import TraceRow, audit_trace, require_trace_pass
from .contracts import ProducerError, require, digest, canonical, strict_json


SCHEMA = "1.0.0"
POLICY = "1.0.0"
COMPOSITION_POLICY = "current-source-grounded-native-visual-v1"
MAX_RECORDS = 8
MAX_ELEMENTS = 8
FAMILIES = {
    "sampled_chart": ("data_science", "graph", "data_chart"),
    "timeline": ("history", "timeline", "timeline"),
    "cellular": ("biology", "diagram", "cell_diagram"),
}


def _data(value):
    """Canonical JSON projection of actual native immutable results."""
    return strict_json(canonical(asdict(value)))


def _target(target):
    fields = {"profile_id", "capabilities", "max_complexity", "supports_interaction",
              "supports_3d", "supports_simulation", "viewport_width", "viewport_height",
              "font_px", "foreground", "background"}
    require(type(target) is dict and set(target) == fields, "visual_target_profile")
    require(all(type(target[k]) is bool for k in
                ("supports_interaction", "supports_3d", "supports_simulation")), "visual_target_profile")
    require(type(target["capabilities"]) in (list, tuple), "visual_target_profile")
    require(all(type(target[k]) is int and 240 <= target[k] <= 4096 for k in
                ("viewport_width", "viewport_height")), "visual_target_profile")
    require(type(target["font_px"]) in (int, float) and isfinite(target["font_px"])
            and 18 <= target["font_px"] <= 96, "visual_target_profile")
    native = TargetProfile(target["profile_id"], tuple(target["capabilities"]),
        target["max_complexity"], target["supports_interaction"], target["supports_3d"],
        target["supports_simulation"])
    require("2d" in native.capabilities, "visual_target_capability_required")
    return native


def _inputs(context, records, revision):
    require(isinstance(context, DirectorContext), "visual_current_director_context")
    require(type(revision) is int and revision == context.handoff_revision and revision > 0,
            "visual_revision_mismatch")
    require(type(records) in (list, tuple) and 0 < len(records) <= MAX_RECORDS,
            "visual_intent_budget")
    by_intent = {i.intent_id: i for i in context.intents}
    require(len(by_intent) == len(context.intents) == len(records), "visual_intent_identity")
    require(len({r.get("intent_id") for r in records}) == len(records), "visual_intent_identity")
    rows = []
    for r in records:
        require(type(r) is dict and r.get("requires_review") is True and r.get("accepted") is False,
                "visual_intent_contract")
        family = FAMILIES.get(r.get("semantic_kind"))
        require(family is not None and (r.get("domain"), r.get("representation"),
                r.get("grammar_representation")) == family, "visual_representation_unsupported")
        require(r.get("source_id") == context.source_id, "visual_foreign_source")
        intent = by_intent.get(r.get("intent_id"))
        require(intent is not None and tuple(r["evidence_refs"]) == intent.evidence_refs and
                tuple(r["reasoning_refs"]) == intent.reasoning_refs, "visual_intent_lineage")
        require(set(r["evidence_refs"]) <= set(context.evidence_refs) and
                set(r["reasoning_refs"]) <= set(context.reasoning_refs), "visual_intent_lineage")
        cues = [c for c in context.cues if c.intent_id == r["intent_id"]]
        require(len(cues) == 1 and cues[0].narration_revision == context.narration_revision,
                "visual_narration_revision_mismatch")
        require(type(r.get("grammar_inputs")) is dict and type(r.get("semantic_obligations")) is dict,
                "visual_semantic_contract")
        require(len(r.get("concept_ids", ())) > 0 and len(r.get("objective_ids", ())) > 0,
                "visual_intent_lineage")
        rows.append((r, cues[0]))
    return tuple(rows)


def _representation(record, target):
    kind = record["semantic_kind"]
    source_items = _verify_source_obligations(record)
    require(len(source_items) <= MAX_ELEMENTS, "visual_source_item_budget")
    # This bounded technical estimate is defined by source complexity, not a
    # fabricated render measurement or an arbitrary fixed favorable budget.
    complexity = len(source_items) / MAX_ELEMENTS
    require(complexity <= target.max_complexity, "visual_target_complexity_exceeded")
    semantic = SemanticIntent(record["intent_id"], record["domain"], tuple(record["concept_ids"]),
        tuple(record["evidence_refs"]), tuple(record["reasoning_refs"]), tuple(record["semantic_tags"]),
        quantitative=kind == "sampled_chart", temporal=kind == "timeline",
        uncertainty=record.get("uncertainty", 0.0),
        payload={"technical_source_derived": True, "semantic_kind": kind})
    candidates = generate(semantic)
    params = record["rep_parameters"]
    if kind == "sampled_chart":
        specific = rep006_graph.choose(semantic, **params)
    elif kind == "timeline":
        specific = rep005_timeline.choose(semantic, **params)
    else:
        specific = rep003_diagram_sim.choose(semantic, target, **params)
    require(specific.status == "PASS" and specific.selected == record["representation"],
            "visual_representation_blocked")
    # Native fitness inputs are technical contract checks, not empirical scores.
    # Unsupported semantic candidates cannot obtain the exact-contract fidelity.
    fitness = tuple(score(semantic, c, target,
        semantic_fidelity=1.0 if c.representation == specific.selected else 0.0,
        explanatory_power=c.base_confidence, cognitive_fit=1.0, timing_fit=1.0,
        evidence_confidence=specific.confidence) for c in candidates)
    dimensional = rep008_dimension.dimension(semantic, target, estimated_complexity=complexity)
    combined = rep008_dimension.compose(semantic,
        tuple((c.representation, f.total) for c, f in zip(candidates, fitness)),
        dimensional, max_secondary=0, complexity=complexity)
    require(combined.status == "PASS" and combined.primary == specific.selected and
            dimensional.status == "PASS", "visual_representation_blocked")
    registry = build_original_grammar_registry()
    views = tuple(Grammar(g.grammar_id, g.version, g.domains, g.representations,
        ("2d",), g.tags) for g in registry.list())
    # A sampled categorical graph is specifically a data_chart; this concrete
    # native family follows the source-declared encoding, not a guessed curve.
    rep = RepDecision(specific.decision_id, 1, record["domain"], record["grammar_representation"],
        specific.confidence, specific.evidence_refs, specific.reasoning_refs,
        ("2d",), tuple(record["semantic_tags"]), True)
    arbitration = arbitrate(rep, views)
    require(arbitration.status == "SELECTED", "visual_grammar_ambiguous_or_unsupported")
    resolved = registry.resolve(domain=rep.domain, representation=rep.representation, tags=rep.tags)
    require(resolved.grammar.grammar_id == arbitration.grammar_id,
            "visual_grammar_resolution_mismatch")
    return dict(semantic=_data(semantic), candidates=[_data(x) for x in candidates],
        fitness=[_data(x) for x in fitness], specific=_data(specific), dimension=_data(dimensional),
        composition=_data(combined), arbitration=_data(arbitration),
        complexity_estimate=dict(value=complexity, source_item_count=len(source_items),
            item_bound=MAX_ELEMENTS, policy="bounded-source-item-count-over-native-element-limit-v1",
            evidence_kind="TECHNICAL_CONTRACT_HEURISTIC", empirical_render_measurement=False),
        fitness_evidence_kind="TECHNICAL_CONTRACT_HEURISTIC", grammar=resolved.grammar)


def _family(record, target):
    values = record["grammar_inputs"]
    if record["semantic_kind"] == "cellular":
        # The existing family layout/QA cannot certify nested containment: its
        # generic grid is nonoverlapping. Preserve this as a real boundary.
        require(not any(c.get("parent_id") for c in values["components"]),
                "visual_containment_layout_required")
        require(not values["transports"], "visual_transport_teaching_contract_required")
    result = execute_original_family_path(domain=record["domain"],
        representation=record["grammar_representation"], tags=tuple(record["semantic_tags"]),
        grammar_inputs=values, evidence_refs=tuple(record["evidence_refs"]),
        reasoning_refs=tuple(record["reasoning_refs"]), viewport=target["viewport_width"])
    require(result.status == "PASS" and len(result.grammar_plan.elements) <= MAX_ELEMENTS,
            "visual_native_family_blocked")
    layout = compose_responsive(result.layout_plan,
        Viewport(target["viewport_width"], target["viewport_height"]))
    layout, solved = solve_layout(layout, safe_area=SafeArea(), subtitle_zone=SubtitleZone(),
                                  avoid_overlap=True)
    require(solved.solved, "visual_layout_unresolved")
    return result, layout, solved


def _verify_source_obligations(record):
    """Source parser output is a separate obligation from grammar input rows."""
    obligations = record["semantic_obligations"]
    require(obligations.get("kind") == record["semantic_kind"] and
            type(obligations.get("source_items")) is list and obligations["source_items"],
            "visual_source_obligations_missing")
    source = obligations["source_items"]
    require(len({x["id"] for x in source}) == len(source), "visual_source_obligations_invalid")
    values = record["grammar_inputs"]
    if record["semantic_kind"] == "sampled_chart":
        require(values["x_label"] == obligations["axis"]["x_label"] and
                values["y_label"] == obligations["axis"]["y_label"] and
                values["y_baseline"] == obligations["y_baseline"] and
                obligations["sampled_data"] is True and obligations["exact_curve_claim"] is False,
                "visual_source_semantics_changed")
        rows = [x for series in values["series"] for x in series["values"]]
        require(canonical([(x["x"], x["y"]) for x in rows]) ==
                canonical([(x["label"], x["value"]) for x in source]),
                "visual_source_semantics_changed")
    elif record["semantic_kind"] == "timeline":
        fields = ("id", "label", "time_label", "order_key", "lower_bound", "upper_bound", "uncertain")
        require(canonical([{k: x.get(k) for k in fields} for x in values["events"]]) ==
                canonical([{k: x.get(k) for k in fields} for x in source]),
                "visual_source_semantics_changed")
        expected = sorted(source, key=lambda x: (x["order_key"], x["id"]))
        require(obligations["source_order"] == [x["id"] for x in source] and
                obligations["chronological_order"] == [x["id"] for x in expected] and
                obligations["duration_claim"] is False, "visual_chronology_changed")
    else:
        fields = ("id", "label", "kind", "parent_id")
        require(canonical([{k: x.get(k) for k in fields} for x in values["components"]]) ==
                canonical([{k: x.get(k) for k in fields} for x in source]),
                "visual_source_semantics_changed")
        require(canonical(obligations["transports"]) == canonical(values["transports"]) and
                obligations["physical_scale_claim"] is False,
                "visual_source_semantics_changed")
    return source


def _source_semantics(record, gp):
    """Check native realization against source facts, independent of role QA."""
    source_items = _verify_source_obligations(record)
    raw = record["grammar_inputs"]
    kind = record["semantic_kind"]
    elements = {e["id"]: e for e in gp.elements}
    realized = []
    view = gp.to_dict()
    view["metadata"] = {}
    if kind == "sampled_chart":
        frame = elements["chart:frame"]["payload"]
        require(frame["x_label"] == raw["x_label"] and frame["y_label"] == raw["y_label"] and
                frame["y_baseline"] == raw["y_baseline"] and frame["chart_type"] == raw["chart_type"],
                "visual_source_semantics_changed")
        for series in raw["series"]:
            e = elements["series:" + series["id"]]
            # The native grammar canonically normalizes finite source numbers
            # to floats. Compare their values, not int/float JSON spellings;
            # source value_text remains retained by the independent record.
            normalized = [dict(v, y=float(v["y"])) for v in series["values"]]
            require(e["label"] == series.get("label", series["id"]) and
                    canonical(e["payload"]["values"]) == canonical(normalized),
                    "visual_source_semantics_changed")
            require(not any("error" in v for v in series["values"]),
                    "visual_uncertainty_display_required")
            realized.extend(x["id"] for x in source_items)
        for e in view["elements"]:
            if e["role"] == "data_series":
                e["role"] = "series"
                e["payload"]["encoding_channel"] = e["payload"]["encoding"]
        view["metadata"] = {"baseline_truncated": raw["y_baseline"] not in (0, None),
                            "baseline_disclosure": False, "aggregation": False}
        require(not view["metadata"]["baseline_truncated"], "visual_baseline_disclosure_required")
    elif kind == "timeline":
        expected = sorted(raw["events"], key=lambda e: (e.get("order_key", e.get("lower_bound",
                          e.get("upper_bound"))), e["id"]))
        actual = [e for e in gp.elements if e["role"] == "historical_event"]
        require(len(actual) == len(expected), "visual_source_semantics_changed")
        for position, (e, source) in enumerate(zip(actual, expected)):
            require(e["id"] == "event:" + source["id"] and
                    e["label"] == source.get("label", source["id"]) and
                    e["payload"]["time_label"] == source["time_label"] and
                    e["payload"]["ordinal_position"] == position,
                    "visual_chronology_changed")
            realized.append(source["id"])
        sources = {e["id"]: e for e in raw["events"]}
        for e in view["elements"]:
            if e["role"] != "historical_event":
                continue
            source = sources[e["id"][6:]]
            p = e["payload"]
            p.update(chronology_index=p["ordinal_position"], source_date_uncertain=bool(source.get("uncertain")),
                visual_date_uncertain=p["uncertain"], source_interval=[source.get("lower_bound"), source.get("upper_bound")],
                visual_interval=[p["lower_bound"], p["upper_bound"]])
    else:
        for source in raw["components"]:
            e = elements["bio:" + source["id"]]
            require(e["label"] == source.get("label", source["id"]) and
                    e["payload"]["kind"] == source["kind"] and
                    e["payload"]["parent_id"] == source.get("parent_id"),
                    "visual_source_semantics_changed")
            realized.append(source["id"])
    require(realized and source_items, "visual_semantics_empty")
    # Source decoded item IDs are the independent required set. Native output
    # must realize every one before its verified concept bindings can count.
    # The native grammar has no knowledge-concept field. Do not assert concept
    # realization by comparing the same supplied concept tuple with itself.
    # Here source-item IDs form the independent semantic obligation and actual
    # output facts above establish their realization. Concept/objective binding
    # remains independently validated by the authoritative intent producer.
    spec = SemanticSpec(tuple(x["id"] for x in source_items), (), tuple(record["evidence_refs"]),
                        tuple(record["reasoning_refs"]))
    aligned = evaluate_semantic_alignment(spec, tuple(realized), (), (),
                                         tuple(gp.evidence_refs))
    policy = semantic_policies(view, gp.constraints)
    require(aligned.passed and policy.passed, "visual_semantic_qa_blocked")
    return aligned, policy, realized


def _text(record, gp, layout, target):
    by_node = {n.node_id: n for n in layout.nodes}
    texts, metrics = [], []
    for e in gp.elements:
        require(bool(e.get("label")), "visual_source_label_required")
        node = by_node[e["id"]]
        text = select_on_screen_text(TextIntent(e["id"], e["label"], "label",
            tuple(record["evidence_refs"]), tuple(record["reasoning_refs"]), max_chars=90),
            available_char_budget=90, allow_condense=False)
        require(text.action == "show_text" and text.display_text == " ".join(e["label"].split()),
                "visual_text_overflow")
        metric = measure(TypographyRequest(text.display_text, target["font_px"],
            node.box.width * target["viewport_width"], node.box.height * target["viewport_height"],
            mode="label"))
        require(not metric.overflow, "visual_text_overflow")
        texts.append(text)
        metrics.append(metric)
    return texts, metrics


def _access(record, gp, target):
    decisions, alts, nodes, contrast_results = [], [], [], {}
    for e in gp.elements:
        access = VisualAccessIntent(e["id"], "label", tuple(record["evidence_refs"]),
                                    tuple(record["reasoning_refs"]))
        contrast = evaluate_contrast(access, foreground=target["foreground"], background=target["background"])
        readable = evaluate_readable_size(access, font_px=target["font_px"],
                                          viewport_width_px=target["viewport_width"])
        encoding = evaluate_color_independent_encoding(access, categories=(e["id"],),
            color_map={e["id"]: target["foreground"]}, secondary_encodings={e["id"]: ("label",)})
        alt = build_alt_description_intent(VisualAccessIntent(e["id"],
            "chart" if record["semantic_kind"] == "sampled_chart" else
            "timeline" if record["semantic_kind"] == "timeline" else "diagram",
            tuple(record["evidence_refs"]), tuple(record["reasoning_refs"])),
            purpose="Explain the explicitly supplied source structure", key_elements=(e["label"],))
        require(contrast.payload["passes"] and readable.payload["passes"] and encoding.payload["passes"],
                "visual_accessibility_blocked")
        contrast_results[e["id"]] = contrast.payload["passes"]
        nodes.append(AccessibleVisualNode(e["id"], "label", target["font_px"],
            target["foreground"], target["background"], e["id"], "label", alt.mode, True))
        alts.append(alt)
        decisions.extend((contrast, readable, encoding))
    accessibility = integrate_accessibility(nodes, contrast_results=contrast_results, allow_auto_repair=False)
    assert_accessible_for_handoff(accessibility)
    return decisions, alts, accessibility


def _compose(context, records, target_dict, run_id, revision):
    target = _target(target_dict)
    rows = _inputs(context, records, revision)
    registry = build_original_grammar_registry()
    receipts = [dict(intent_id=r["intent_id"], scene_id=r["scene_id"], record_sha256=digest(r))
                for r, _ in rows]
    working = [{} for _ in rows]
    primitives, timings = [], []

    def execute(stage):
        # Actual engines execute in their declared VisualOrchestrator callbacks.
        # The canonical family helper performs a composite preflight at GRAM;
        # final layout/text/access/QA below execute over the governed target.
        outputs = []
        for (record, cue), state, receipt in zip(rows, working, receipts):
            if stage == "REP":
                rep = _representation(record, target)
                rep.pop("grammar")
                state["representation"] = rep
                output = dict(representation=rep)
            elif stage == "GRAM":
                family, _, _ = _family(record, target_dict)
                state["family"] = family
                gp = family.grammar_plan
                require(gp.grammar_id == state["representation"]["arbitration"]["grammar_id"],
                        "visual_grammar_resolution_mismatch")
                # This is canonical engine composition, not an assertion that
                # current records came from a historical archive invocation.
                output = dict(grammar=gp.to_dict(), family_preflight=dict(
                    status=family.status, qa=[_data(x) for x in family.qa_results],
                    provenance="CURRENT_CANONICAL_IMPLEMENTATION_EXECUTION"))
            elif stage == "LAYOUT":
                family = state["family"]
                layout = compose_responsive(family.layout_plan,
                    Viewport(target_dict["viewport_width"], target_dict["viewport_height"]))
                layout, solved = solve_layout(layout, safe_area=SafeArea(),
                    subtitle_zone=SubtitleZone(), avoid_overlap=True)
                require(solved.solved, "visual_layout_unresolved")
                state["layout"] = layout
                output = dict(layout=layout.to_dict(), solver=_data(solved))
            elif stage == "ASSET":
                family = state["family"]
                gp = family.grammar_plan
                # No rendered asset is asserted here. This native AssetItem
                # describes bounded procedural plan definitions: binary source
                # preservation/schema-completeness checks, not visual quality.
                _source_semantics(record, gp)
                require(all(e["source_ids"] and e["primitive"] for e in gp.elements),
                        "visual_procedural_asset_contract")
                asset = asset_decision(family.asset_need, "use_native_procedural_primitives",
                    request={"external_assets_required": False, "grammar_id": gp.grammar_id,
                             "primitive_ids": [e["id"] for e in gp.elements]},
                    rationale=("source_grounded_native_procedural_plan", "no_external_asset_acquisition"))
                aq = evaluate_asset_qa((AssetItem(record["intent_id"], True,
                    tuple(record["evidence_refs"]), 1.0, 1.0, True, False, False, True),),
                    tuple(record["evidence_refs"]), tuple(record["reasoning_refs"]))
                require(aq.passed, "visual_asset_qa_blocked")
                state["asset_qa"] = aq
                output = dict(asset=_data(asset), asset_qa=_data(aq), asset_evidence=dict(
                    semantic_score_meaning="BINARY_EXACT_SOURCE_PRESERVATION_CHECK",
                    quality_score_meaning="BINARY_PROCEDURAL_DEFINITION_COMPLETENESS",
                    rights_scope="NATIVE_PROCEDURAL_PLAN_NO_EXTERNAL_MATERIAL",
                    rendered_asset_quality_measured=False))
            elif stage == "TEXT":
                texts, metrics = _text(record, state["family"].grammar_plan,
                                       state["layout"], target_dict)
                state["texts"] = texts
                output = dict(text=[_data(x) for x in texts], typography=[_data(x) for x in metrics])
            elif stage == "ACCESS":
                access, alts, accessibility = _access(record, state["family"].grammar_plan, target_dict)
                output = dict(access=[_data(x) for x in access], alt_intents=[_data(x) for x in alts],
                              accessibility=_data(accessibility))
            else:
                gp, layout, aq = state["family"].grammar_plan, state["layout"], state["asset_qa"]
                semantic, policies, realized = _source_semantics(record, gp)
                lq = evaluate_layout_qa(tuple(LayoutElement(n.node_id, n.role,
                    QABox(n.box.x, n.box.y, n.box.width, n.box.height), n.required) for n in layout.nodes),
                    tuple(record["evidence_refs"]), tuple(record["reasoning_refs"]),
                    subtitle_zone=QABox(0, .81, 1, .16))
                cq = evaluate_clutter_qa(len(gp.elements), sum(len(t.display_text) for t in state["texts"]),
                    0, len(gp.relations), 0, 1, tuple(record["evidence_refs"]), tuple(record["reasoning_refs"]))
                benchmark = evaluate_visual_benchmark((semantic, lq, cq, aq))
                require(lq.passed and cq.passed and benchmark.passed, "visual_qa_blocked")
                trace = audit_trace(tuple(TraceRow(record["intent_id"] + ":" + e["id"], True,
                    tuple(e["source_ids"]), tuple(record["reasoning_refs"]),
                    state["representation"]["composition"]["plan_id"], e["id"], e["id"], e["id"], None,
                    (semantic.qa_id, lq.qa_id, cq.qa_id, aq.qa_id), True) for e in gp.elements))
                require_trace_pass(trace)
                output = dict(semantic_qa=_data(semantic), semantic_policies=_data(policies),
                    layout_qa=_data(lq), clutter_qa=_data(cq), benchmark=_data(benchmark), trace=_data(trace),
                    realized_source_items=realized)
                for e in gp.elements:
                    pid = record["intent_id"] + ":" + e["id"]
                    primitives.append(PrimitiveRequirement(pid, e["primitive"], True, ("2d",), None,
                        tuple(e["source_ids"]), tuple(record["reasoning_refs"])))
                    timings.append(TimingBinding(pid, cue.start_ms, cue.end_ms, False, True,
                                                  context.narration_revision))
            receipt.update(output)
            outputs.append(dict(intent_id=record["intent_id"], scene_id=record["scene_id"], **output))
        payload = dict(policy=COMPOSITION_POLICY, target=target_dict,
            source_id=context.source_id, director_handoff_id=context.handoff_id,
            director_revision=context.handoff_revision, narration_revision=context.narration_revision,
            context_fingerprint=context.fingerprint, records_sha256=digest(records),
            implementation_registry=registry.snapshot()["fingerprint"], evidence_kind="TECHNICAL_SOURCE_DERIVED",
            outputs=outputs, internal_stage=stage, review_required=True, accepted=False)
        return dict(artifact_id="vis:" + digest(dict(stage=stage, payload=payload)), revision=revision,
            fingerprint=digest(payload), payload=payload, current=True, status="PASS")
    orchestrator = VisualOrchestrator(SCHEMA, POLICY)
    for name in STAGES[1:]:
        orchestrator.register(name, lambda _, n=name: execute(n))
    plan, report = orchestrator.run("visual:" + run_id, context, target.profile_id)
    require(report.blocked_stage is None and tuple(s.stage for s in plan.stages) == STAGES and
            all(s.current and s.status == "PASS" for s in plan.stages) and
            plan.review_required is True and plan.accepted is False, "visual_plan_incomplete")
    handoff = build_downstream_handoff(handoff_id="visual-handoff:" + plan.fingerprint,
        plan_fingerprint=plan.fingerprint, primitives=primitives, assets=(), timing=timings,
        accessibility_ready=True, target_capabilities=target.capabilities, target_profile=target.profile_id)
    assert_handoff_consumable(handoff)
    return plan, handoff, receipts


def build_current_plan(context, records, target_dict, *, run_id, revision):
    try:
        return _compose(context, records, target_dict, run_id, revision)
    except ProducerError:
        raise
    except Exception:
        raise ProducerError("visual_native_contract_failed") from None


def validate_current_plan(context, records, target_dict, *, run_id, revision,
                          plan_dict, handoff_dict, receipts=None):
    """Fresh verified inputs must recompose exact native plan/handoff identity."""
    plan, handoff, actual = build_current_plan(context, records, target_dict,
                                              run_id=run_id, revision=revision)
    require(type(plan_dict) is dict and plan_dict.get("review_required") is True and
            plan_dict.get("accepted") is False, "visual_review_boundary")
    try:
        loaded = VisualPlan.from_dict(plan_dict)
    except Exception:
        raise ProducerError("visual_plan_fingerprint_mismatch") from None
    require(canonical(loaded.to_dict()) == canonical(plan.to_dict()), "visual_plan_identity_mismatch")
    require(canonical(handoff_dict) == canonical(_data(handoff)), "visual_handoff_identity_mismatch")
    if receipts is not None:
        require(canonical(receipts) == canonical(actual), "visual_receipt_mismatch")
    return plan, handoff, actual
