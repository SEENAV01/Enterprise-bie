"""Current, source-admitted visual intents for BIE-PROD-034.

This bridge accepts three *complete* bounded declarations in a verified native
source passage and finds that exact declaration in actual Director narration.
It does not infer semantic structure from a keyword, a page position, an LLM
suggestion, or a test fixture.  The compact spelling is a documented technical
source notation, with the same meaning as its long spelling::

    Chart B x A y B: C 2; D 3.       # B or bar: sampled categorical bar chart
    Timeline: A at 1810; B at 1820. # explicit time values, not duration inference
    Cell: A C; B C.                 # C or cell; R or region; optional ``in A``

Timeline items also admit ``about 1810`` or ``1810..1820`` and preserve that
uncertainty.  Cellular parent declarations are retained, never erased merely
because a downstream layout cannot preserve containment.  Each native planner
must independently verify these source obligations; admission is not scientific,
historical, pedagogical, mathematical, or learner-outcome acceptance.

Pure mathematical equalities remain an explicit abstention: the current domain
grammar registry has no equation family.  They are never recast as a graph.
The producer's verified Math and Reasoning admission remains authoritative.

``derive_intents`` requires the actual ``load_director_inputs`` result and
verified ``DirectorExecution``.  The caller additionally binds these results to
the exact current Director envelope/revision and publishes the native consumer
candidate.  Native IntentBinding has no revision/reasoning fields: its narration
fingerprint and these private records retain those identities without inventing
a competing Director contract.  All returned records are PRIVATE producer data.
"""
from dataclasses import asdict
import math
import re

from bie.director.director_benchmark import DirectorExecution
from bie.director.director_inputs import DirectorInputs
from bie.director.narration_visual_sync import VisualIntent, sync_visual_intents
from bie.director.qa_contract import validate_catalog, validate_claims, validate_snapshot
from bie.director.sync_contract import IntentBinding, SyncIndex, build_sync_context
from .contracts import canonical, digest, require, sha


SCHEMA = "bie.producer.current-visual-intent/1"
POLICY = "complete-source-declaration-current-narration-v1"
MAX_DECLARATION = 512
MAX_ITEMS = 8
MAX_INTENTS = 16
LABEL = r"[A-Za-z][A-Za-z0-9_]{0,15}"
NUMBER = r"[0-9]{1,6}(?:\.[0-9]{1,4})?"
CELL_KINDS = {"C": "cell", "cell": "cell", "R": "region", "region": "region",
              "O": "organelle", "organelle": "organelle", "M": "membrane",
              "membrane": "membrane", "Q": "molecule", "molecule": "molecule"}


def _number(value):
    # Native grammar finite_number uses finite floats.  Adopt that canonical
    # representation here while retaining source value_text/time_label exactly;
    # JSON integer/float byte distinctions must not create false source drift.
    number = float(value)
    require(math.isfinite(number), "visual_source_declaration_invalid")
    return number


def _chart(text):
    match = re.fullmatch(rf"Chart (B|bar) x ({LABEL}) y ({LABEL}): (.+)\.", text)
    if match is None:
        return None
    _, x_label, y_label, rows = match.groups()
    items = []
    for row in rows.split("; "):
        item = re.fullmatch(rf"({LABEL}) ({NUMBER})", row)
        if item is None:
            return None
        label, value = item.groups()
        items.append(dict(id=label, label=label, value=_number(value), value_text=value))
    if not 2 <= len(items) <= MAX_ITEMS or len({r["id"] for r in items}) != len(items):
        return None
    return dict(semantic_kind="sampled_chart", domain="data_science", representation="graph",
        grammar_representation="data_chart", semantic_tags=["data", "comparison", "sampled"],
        grammar_inputs=dict(chart_type="bar", x_label=x_label, y_label=y_label, y_baseline=0.0,
            series=[dict(id="declared-samples", label=y_label,
                         values=[dict(x=r["label"], y=r["value"]) for r in items])]),
        rep_parameters=dict(data_points=len(items), function_defined=False, axis_semantics=True,
            units_known=False, sampled_data=True, exact_curve_claim=False, domain_restriction=False),
        semantic_obligations=dict(kind="sampled_chart", source_items=items,
            axis=dict(x_label=x_label, y_label=y_label), sampled_data=True, exact_curve_claim=False,
            y_baseline=0.0, baseline_origin="CANONICAL_NATIVE_ZERO_BASELINE_POLICY",
            uncertainty_visible=True),
        uncertainty=.5, interpretation="EXPLICIT_DECLARED_SAMPLES_NOT_ANALYTIC_FUNCTION")


def _timeline(text):
    match = re.fullmatch(r"Timeline: (.+)\.", text)
    if match is None:
        return None
    items = []
    for row in match[1].split("; "):
        item = re.fullmatch(rf"({LABEL}) at (about )?({NUMBER})(?:\.\.({NUMBER}))?", row)
        if item is None:
            return None
        label, about, lower, upper = item.groups()
        if about and upper:
            return None
        low = _number(lower)
        high = _number(upper) if upper else None
        if high is not None and low > high:
            return None
        uncertain = bool(about or (high is not None and high != low))
        items.append(dict(id=label, label=label, time_label=row.split(" at ", 1)[1],
            order_key=low, lower_bound=low if high is not None else None,
            upper_bound=high, uncertain=uncertain))
    if not 2 <= len(items) <= MAX_ITEMS or len({r["id"] for r in items}) != len(items):
        return None
    return dict(semantic_kind="timeline", domain="history", representation="timeline",
        grammar_representation="timeline", semantic_tags=["chronology", "event", "uncertainty"],
        grammar_inputs=dict(events=items, axis_label="time"),
        rep_parameters=dict(event_count=len(items), has_order=True,
            has_intervals=any(r["upper_bound"] is not None for r in items),
            uncertain_dates=any(r["uncertain"] for r in items),
            simultaneous_events=len({r["order_key"] for r in items}) != len(items)),
        semantic_obligations=dict(kind="timeline", source_items=items,
            source_order=[r["id"] for r in items],
            chronological_order=[r["id"] for r in sorted(items, key=lambda r: (r["order_key"], r["id"]))],
            duration_claim=False),
        uncertainty=.5, interpretation="SOURCE_DECLARED_CHRONOLOGY_NOT_TEMPORAL_REASONING_EXECUTION")


def _cell(text):
    match = re.fullmatch(r"Cell: (.+)\.", text)
    if match is None:
        return None
    items = []
    for row in match[1].split("; "):
        item = re.fullmatch(rf"({LABEL}) (C|cell|R|region|O|organelle|M|membrane|Q|molecule)(?: in ({LABEL}))?", row)
        if item is None:
            return None
        label, kind, parent = item.groups()
        items.append(dict(id=label, label=label, kind=CELL_KINDS[kind], parent_id=parent))
    names = {r["id"] for r in items}
    if not 1 <= len(items) <= MAX_ITEMS or len(names) != len(items):
        return None
    if not any(r["kind"] in ("cell", "region") for r in items):
        return None
    parents = {r["id"]: r["parent_id"] for r in items}
    for item in items:
        if item["parent_id"] is not None and item["parent_id"] not in names:
            return None
        seen = {item["id"]}
        parent = item["parent_id"]
        while parent is not None:
            if parent in seen:
                return None
            seen.add(parent)
            parent = parents[parent]
    return dict(semantic_kind="cellular", domain="biology", representation="diagram",
        grammar_representation="cell_diagram", semantic_tags=["structure", "cell"],
        grammar_inputs=dict(components=items, transports=[], scale_bar=None),
        rep_parameters=dict(parameter_exploration=False, mechanism_states=len(items),
                            simulation_model_evidence=False),
        semantic_obligations=dict(kind="cellular", source_items=items,
            containments=[dict(source=r["parent_id"], target=r["id"]) for r in items if r["parent_id"]],
            transports=[], physical_scale_claim=False),
        uncertainty=.5, interpretation="SOURCE_DECLARED_CELLULAR_STRUCTURE_NOT_SPATIAL_REASONING_EXECUTION")


def parse_declaration(text):
    """Parse a complete private source declaration, without guessed semantics.

    Unsupported input returns None.  A caller distinguishes ordinary abstention
    from malformed explicit declarations; no raw source is included in errors.
    """
    if type(text) is not str or not 0 < len(text) <= MAX_DECLARATION:
        return None
    return _chart(text) or _timeline(text) or _cell(text)


def _abstention(passage, code, status="ABSTAIN"):
    return dict(evidence_id=passage.evidence_id, source_passage_fingerprint=passage.fingerprint(),
                code=code, status=status, requires_review=True, accepted=False)


def _candidate_binding(inputs, execution, index, passage):
    """Require actual narration, actual source-bound objectives and actual RE.

    SyncIndex checks source/objective membership but has no concept-membership
    check.  Derive concepts only through the native input objective mapping.
    Exclude assessment/feedback utterances to avoid treating quiz questions or
    a copied expected answer as the authoritative instructional realization.
    """
    objective_map = {o.objective_id: o for o in inputs.objectives}
    source_artifacts = {eid: aid for aid, eid in inputs.evidence_artifacts}
    source_artifact = source_artifacts.get(passage.evidence_id)
    require(source_artifact is not None, "visual_source_evidence_unresolved")
    decisions = {d.decision_id: d for d in inputs.reasoning}
    segments = {s.segment_id: s for s in execution.snapshot.script.segments}
    for timed in execution.speech.utterances:
        utterance = timed.utterance
        if segments[utterance.segment_id].purpose in ("ASSESS", "FEEDBACK"):
            continue
        if passage.evidence_id not in utterance.evidence_ids or utterance.text.count(passage.quote) != 1:
            continue
        objectives = tuple(sorted(oid for oid in utterance.objective_ids
            if oid in objective_map and passage.evidence_id in objective_map[oid].evidence_ids))
        if not objectives:
            continue
        concepts = tuple(sorted({objective_map[oid].concept_id for oid in objectives}))
        require(concepts and all(type(c) is str and c for c in concepts), "visual_concept_binding_invalid")
        allowed_re = {rid for b in inputs.bindings if set(b.objective_ids) & set(objectives)
                      for rid in b.reasoning_decision_ids}
        reasoning = tuple(sorted(rid for rid in allowed_re if rid in decisions and
            any(e.artifact_id == source_artifact for e in decisions[rid].evidence_refs)))
        if not reasoning:
            continue
        start = utterance.text.index(passage.quote)
        end = start + len(passage.quote)
        words = tuple(w.word for w in timed.words if w.word.start_char >= start and w.word.end_char <= end)
        if not words or words[0].start_char != start:
            continue
        # Only punctuation following the final complete spoken token is outside
        # the native word window; no part of a lexical token may be omitted.
        if any(c.isalnum() for c in utterance.text[words[-1].end_char:end]):
            continue
        claim_ids = tuple(sorted(c.claim_id for c in execution.claims
            if c.kind == "FACT" and c.span.utterance_id == utterance.utterance_id and
               c.span.utterance_fingerprint == utterance.fingerprint() and
               c.span.start_char <= start and c.span.end_char >= end and
               passage.evidence_id in c.evidence_ids))
        if not claim_ids:
            continue
        anchor = index.anchor(utterance.utterance_id, words[0].index, words[-1].index + 1)
        return utterance, anchor, objectives, concepts, reasoning, claim_ids, start, end
    return None


def derive_intents(inputs, execution):
    """Return native typed intents, PRIVATE semantic records, and abstentions.

    Upstream source/RE/PED/Math envelopes and the current Director revision must
    already be verified by the producer/current native consumer.  This function
    rechecks native source/snapshot/timing/claims and derives all intent fields
    independently.  No caller-provided concepts, purposes, targets or source
    semantics are accepted.  Same verified inputs produce the same result.
    """
    require(isinstance(inputs, DirectorInputs) and isinstance(execution, DirectorExecution),
            "visual_native_inputs_required")
    pages, _ = validate_catalog(inputs.catalog)
    snapshot = validate_snapshot(execution.snapshot)
    validate_claims(execution.snapshot, execution.claims)
    context = build_sync_context(execution.speech, execution.pauses, execution.emphasis, execution.timeline)
    index = SyncIndex(context)
    require({u.utterance_id: u for u in execution.snapshot.utterances} ==
            {t.utterance.utterance_id: t.utterance for t in execution.speech.utterances},
            "visual_narration_revision_mismatch")
    require(set(snapshot) == set(index.utterances), "visual_narration_revision_mismatch")
    require(inputs.lesson_id == execution.architecture.lesson_id, "visual_foreign_lesson")
    require(inputs.lesson_id == execution.snapshot.script.lesson_id, "visual_foreign_lesson")
    source_ids = {p.source_id for p in pages.values()}
    require(set(execution.architecture.source_ids) == source_ids, "visual_foreign_source")
    scenes = {s.scene_id: s for s in execution.architecture.scenes}
    require(len(scenes) == len(execution.architecture.scenes), "visual_foreign_scene")
    objectives = {o.objective_id: o for o in inputs.objectives}
    require(set(execution.architecture.objective_ids) == set(objectives), "visual_objective_binding_invalid")
    for utterance in execution.snapshot.utterances:
        scene = scenes.get(utterance.scene_id)
        require(scene is not None and set(utterance.objective_ids) <= set(scene.objective_ids) and
                set(utterance.evidence_ids) <= set(scene.evidence_ids), "visual_foreign_scene")
    require(len(inputs.catalog.passages) <= 4096, "visual_source_budget")
    require(len(source_ids) == 1, "visual_foreign_source")
    intents, records, abstentions = [], [], []
    for passage in sorted(inputs.catalog.passages, key=lambda p: (p.page_id, p.start_char, p.evidence_id)):
        parsed = parse_declaration(passage.quote)
        if parsed is None:
            explicit = passage.quote.startswith(("Chart ", "Timeline:", "Cell:"))
            code = "visual_source_declaration_invalid" if explicit else (
                "visual_equation_grammar_unavailable" if "=" in passage.quote else "visual_semantics_not_admitted")
            abstentions.append(_abstention(passage, code, "BLOCKED" if explicit else "ABSTAIN"))
            continue
        candidate = _candidate_binding(inputs, execution, index, passage)
        if candidate is None:
            abstentions.append(_abstention(passage, "visual_narration_binding_unavailable", "REVIEW_REQUIRED"))
            continue
        utterance, anchor, objectives, concepts, reasoning, claim_ids, start, end = candidate
        require(len(intents) < MAX_INTENTS, "visual_intent_budget")
        identity = dict(policy=POLICY, passage=passage.fingerprint(), narration=asdict(anchor),
                        upstream=[asdict(r) for r in inputs.parent_refs], semantic=parsed)
        intent_id = "visual-intent-" + digest(identity)
        target = "visual-target-" + digest(dict(source=passage.fingerprint(), policy=POLICY))
        purpose = {"sampled_chart": "DISPLAY_DECLARED_CATEGORY_SAMPLES",
                   "timeline": "DISPLAY_DECLARED_CHRONOLOGY_WITH_UNCERTAINTY",
                   "cellular": "DISPLAY_DECLARED_CELLULAR_STRUCTURE_WITHOUT_SCALE_CLAIM"}[parsed["semantic_kind"]]
        binding = IntentBinding(intent_id, target, anchor, (passage.evidence_id,), objectives, concepts, purpose)
        kind = {"sampled_chart": "chart", "timeline": "timeline", "cellular": "diagram"}[parsed["semantic_kind"]]
        intent = VisualIntent(binding, kind)
        index.resolve(binding)
        page = pages[passage.page_id]
        record = dict(parsed, schema=SCHEMA, policy=POLICY, intent_id=intent_id, target_id=target,
            visual_kind=kind, purpose=purpose, concept_ids=list(concepts), objective_ids=list(objectives),
            evidence_refs=[passage.evidence_id], reasoning_refs=list(reasoning),
            reasoning_types=sorted({d.decision_type for d in inputs.reasoning if d.decision_id in reasoning}),
            source_id=page.source_id, source_sha256=page.source_sha256, page_number=page.page_number,
            page_id=page.page_id, region_id=passage.region_id,
            source_passage_fingerprint=passage.fingerprint(), source_text_sha256=sha(passage.quote.encode("utf-8")),
            source_span=dict(start_char=passage.start_char, end_char=passage.end_char),
            scene_id=utterance.scene_id, utterance_id=utterance.utterance_id,
            narration_fingerprint=utterance.fingerprint(), snapshot_fingerprint=execution.snapshot.fingerprint(),
            narration_span=dict(start_char=start, end_char=end, start_word=anchor.start_word, end_word=anchor.end_word),
            director_claim_ids=list(claim_ids), input_refs=[asdict(r) for r in inputs.parent_refs],
            private=True, evidence_kind="TECHNICAL_SOURCE_DERIVED", requires_review=True,
            accepted=False, academic_acceptance=False, product_accepted=False)
        for key in ("events", "components"):
            if key in record["grammar_inputs"]:
                record["grammar_inputs"][key] = [dict(r, source_ids=[passage.evidence_id])
                                                   for r in record["grammar_inputs"][key]]
        if "series" in record["grammar_inputs"]:
            record["grammar_inputs"]["series"] = [dict(r, source_ids=[passage.evidence_id])
                                                  for r in record["grammar_inputs"]["series"]]
        intents.append(intent); records.append(record)
    if intents:
        plan = sync_visual_intents(context, tuple(intents))
        require(plan.status == "READY_FOR_DOWNSTREAM_REVIEW", "visual_sync_blocked")
    return tuple(intents), records, abstentions


def validate_derived(inputs, execution, typed_intents, records):
    """Reject fabricated/edited intents by independently recomposing all fields."""
    expected, expected_records, _ = derive_intents(inputs, execution)
    require(type(typed_intents) is tuple and all(isinstance(i, VisualIntent) for i in typed_intents),
            "visual_typed_intent_required")
    require(canonical([asdict(i) for i in typed_intents]) == canonical([asdict(i) for i in expected]) and
            canonical(records) == canonical(expected_records), "visual_intent_derivation_mismatch")
    return typed_intents, records
