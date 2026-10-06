"""Bounded source-bound native PED composition for BIE-PROD-032.

This module composes existing PED records.  It does not grade a learner,
invent a misconception, write narration, or certify teaching effectiveness.
One run plan contains one bounded teaching scope with concept-level units;
book/course decomposition and empirical policy calibration remain separate work.
"""
from dataclasses import asdict

from bie.director.director_inputs import TeachingBinding
from bie.pedagogy.learning_objective_generator import generate_objective
from bie.pedagogy.objective_concept_mapping import ObjectiveConceptLink, validate_link
from bie.pedagogy.objective_evidence import objective_evidence
from bie.pedagogy.objective_coverage_qa import objective_coverage_qa
from bie.pedagogy.objective_mastery_criterion import MasteryCriterion
from bie.pedagogy.assessment_blueprint import AssessmentCell, build_assessment_blueprint
from bie.pedagogy.assessment_alignment import assessment_alignment
from bie.pedagogy.cognitive_load_control import assess_load
from bie.pedagogy.cognitive_load_qa import cognitive_load_qa
from bie.pedagogy.pedagogy_provenance import build_lineage, validate_lineage_graph
from bie.pedagogy.pedagogy_plan_contract import PedagogyDecision, build_pedagogy_plan
from bie.pedagogy.prerequisite_aware_ordering import prerequisite_order
from bie.pedagogy.retrieval_questions import make_retrieval_question
from bie.pedagogy.formative_checks import make_formative_check
from bie.pedagogy.teaching_mode_selection import TeachingModeDecision

from .contracts import require, identifier, digest, canonical, strict_json, HASH, validate_document
from .pr_reasoning import (verify_knowledge, verify_prerequisite, PR_SCHEMA, RE_SCHEMA)
from .math_evidence import (SCHEMA as MATH_SCHEMA, profile_config as math_config,
                           verify_math, verify_reasoning)

PROFILE = "source_grounded_di_knowledge_pr_math_reasoning_pedagogy_v1"
SCHEMA = "bie.pedagogy.plan/1"
POLICY = "grounded-native-baseline-instructional-units-v1"
SCOPE = "RUN_BOUNDED_INSTRUCTIONAL_UNITS"
MAX_UNITS = 200
UPSTREAM = ("document", "knowledge", "prerequisite", "math", "reasoning")
CONTEXT = ("run_id", "source_sha256", "knowledge_artifact_id", "knowledge_sha256",
           "attempt", "profile", "policy", "privacy", "evidence_kind", "academic_acceptance")


def profile_config(provider="technical_source_derived", model="lexical-extractive-v1"):
    return dict(math_config(provider, model), profile=PROFILE, pedagogy_schema=SCHEMA,
                pedagogy_policy=POLICY, pedagogy_scope=SCOPE, max_pedagogy_units=MAX_UNITS)


def _context(value):
    require(type(value) is dict and all(k in value for k in CONTEXT), "pedagogy_upstream_contract")
    return {k: value[k] for k in CONTEXT}


def _inputs(document, knowledge, prerequisite, math, reasoning, *, run_id, source_id,
            artifact_ids, artifact_hashes):
    """Recompute native upstream contracts; never trust serialized PASS flags."""
    identifier(run_id); identifier(source_id)
    require(type(artifact_ids) is dict and set(artifact_ids) == set(UPSTREAM), "pedagogy_input_identity")
    require(type(artifact_hashes) is dict and set(artifact_hashes) == set(UPSTREAM), "pedagogy_input_identity")
    for key in UPSTREAM:
        identifier(artifact_ids[key])
        require(type(artifact_hashes[key]) is str and HASH.fullmatch(artifact_hashes[key]),
                "pedagogy_input_identity")
    values = dict(document=document, knowledge=knowledge, prerequisite=prerequisite,
                  math=math, reasoning=reasoning)
    require(all(digest(value) == artifact_hashes[key] for key, value in values.items()),
            "pedagogy_upstream_hash_mismatch")
    validate_document(document); verify_knowledge(knowledge, document)
    require(document["source_artifact_id"] == source_id, "pedagogy_foreign_source")
    source_sha = document["source_sha256"]
    for value in (prerequisite, math, reasoning):
        require(value.get("run_id") == run_id and value.get("source_sha256") == source_sha,
                "pedagogy_foreign_run")
        require(value.get("knowledge_artifact_id") == artifact_ids["knowledge"] and
                value.get("knowledge_sha256") == artifact_hashes["knowledge"],
                "pedagogy_foreign_knowledge")
    require(prerequisite.get("schema") == PR_SCHEMA and math.get("schema") == MATH_SCHEMA and
            reasoning.get("schema") == RE_SCHEMA, "pedagogy_upstream_schema")
    verify_prerequisite(prerequisite, knowledge, _context(prerequisite))
    require(math.get("document_artifact_id") == artifact_ids["document"] and
            math.get("prerequisite_artifact_id") == artifact_ids["prerequisite"],
            "pedagogy_foreign_math")
    verify_math(math, document, knowledge, prerequisite, _context(math),
                artifact_ids["document"], artifact_ids["prerequisite"])
    require(math["applicability"] in ("REQUIRED", "NOT_REQUIRED") and not math["findings"],
            "pedagogy_math_review_required")
    require(reasoning.get("prerequisite_artifact_id") == artifact_ids["prerequisite"] and
            reasoning.get("math_artifact_id") == artifact_ids["math"] and
            reasoning.get("math_sha256") == artifact_hashes["math"], "pedagogy_foreign_reasoning")
    verify_reasoning(reasoning, knowledge, prerequisite, math, _context(reasoning),
                     artifact_ids["prerequisite"], artifact_ids["math"])
    require(reasoning["decisions"] and "teaching_order" in reasoning["executed_types"],
            "pedagogy_reasoning_required")
    require(type(knowledge["nodes"]) is dict and 0 < len(knowledge["nodes"]) <= MAX_UNITS,
            "pedagogy_unit_budget")
    return values


def pedagogy_components(document, knowledge, prerequisite, math, reasoning, *, run_id,
                        source_id, artifact_ids, artifact_hashes, attempt=1):
    """Return private canonical PED plan/objectives/bindings and audit structures.

    The caller must resolve these payloads from verified canonical persistence.
    This function also recomputes their content contracts and exact hash bindings.
    Source anchor IDs remain unchanged; a downstream catalog may bind those IDs
    to actual source.block records without creating new source evidence aliases.
    """
    require(type(attempt) is int and attempt > 0, "pedagogy_attempt_identity")
    _inputs(document, knowledge, prerequisite, math, reasoning, run_id=run_id,
            source_id=source_id, artifact_ids=artifact_ids, artifact_hashes=artifact_hashes)
    blocks = {b["anchor_id"]: b for b in document["blocks"]}
    nodes = knowledge["nodes"]
    evidence = {cid: tuple(sorted(node["anchor_ids"])) for cid, node in nodes.items()}
    require(all(ids and set(ids) <= set(blocks) for ids in evidence.values()),
            "pedagogy_missing_source_evidence")
    pairs = sorted({(e["prerequisite"], e["dependent"]) for e in prerequisite["edges"]})
    order = prerequisite_order(tuple(nodes), ((a, b, .5) for a, b in pairs))
    require(tuple(prerequisite["order"]) == order, "pedagogy_prerequisite_order")
    before = {cid: [] for cid in nodes}
    for a, b in pairs:
        require(a in nodes and b in nodes and a != b, "pedagogy_invalid_prerequisite")
        before[b].append(a)
    source_position = {cid: min((blocks[a]["physical_page"], blocks[a]["reading_order"],
                                blocks[a]["block_id"]) for a in ids)
                       for cid, ids in evidence.items()}
    source_order = tuple(sorted(nodes, key=lambda cid: (source_position[cid], cid)))
    lesson_id = "lesson-" + digest(dict(run_id=run_id, source=source_id, policy=POLICY))
    unit_ids = {cid: "unit-" + digest(dict(concept=cid, policy=POLICY)) for cid in nodes}
    decision_ids = {cid: "ped-" + digest(dict(concept=cid, policy=POLICY)) for cid in nodes}
    reasoning_ids = tuple(sorted(d["decision_id"] for d in reasoning["decisions"]))
    confidence = min(.5, *(d["confidence"] for d in reasoning["decisions"]))
    objectives = []; decisions = []; bindings = []; units = []; lineages = []
    objective_links = []; retrieval = []; formative = []; requirements = []
    all_cells = []; loads = []
    for position, cid in enumerate(order):
        node = nodes[cid]; ev = evidence[cid]
        objective = generate_objective(cid, node["label"], ev)
        link = validate_link(ObjectiveConceptLink(objective.objective_id, cid, "PRIMARY", ev))
        require(objective_evidence(ev, objective.evidence_ids).grounded, "pedagogy_objective_evidence")
        decision = PedagogyDecision(decision_ids[cid], "instructional_unit", unit_ids[cid], ev,
            tuple(sorted(decision_ids[p] for p in before[cid])), "RESOLVED", confidence, True)
        # Baseline teaching policy, not a fabricated learner-readiness measurement.
        mode = TeachingModeDecision("EXPLANATION", "baseline_source_explanation_no_learner_observations",
                                    confidence, True)
        cells = tuple(AssessmentCell(objective.objective_id, cid, "APPLY", None, transfer,
            ("item-" + digest(dict(objective=objective.objective_id, transfer=transfer, policy=POLICY)),), ev)
            for transfer in (False, True))
        req = tuple((c.objective_id, c.concept_id, c.cognitive_level, c.transfer) for c in cells)
        require(build_assessment_blueprint(req, cells).passed, "pedagogy_assessment_coverage")
        binding = TeachingBinding(decision.decision_id, lesson_id, (objective.objective_id,),
                                  reasoning_ids, mode, cells)
        line = build_lineage(unit_ids[cid], source_evidence_ids=ev,
            reasoning_parent_ids=(artifact_ids["reasoning"],),
            prerequisite_parent_ids=(artifact_ids["prerequisite"],),
            math_parent_ids=(artifact_ids["math"],), confidence=confidence, requires_review=True,
            assumptions=("technical_source_derived_not_academic_evidence",))
        # Native load guardrails operate on an explicit technical policy.  These
        # weights are not empirical estimates and carry no learner observations.
        load = assess_load(min(.6, .25 + .05 * len(before[cid])), .1, .2)
        require(not load.overload, "pedagogy_cognitive_load")
        claims = sorted((c for c in knowledge["claims"] if set(c["anchor_ids"]) & set(ev)),
                        key=lambda c: c["claim_id"])
        require(claims, "pedagogy_objective_claim_required")
        recall = make_retrieval_question(cid, "Recall a cited source assertion involving " + node["label"] + ".",
                                         claims[0]["text"], tuple(claims[0]["anchor_ids"]))
        check = make_formative_check("check-" + digest(dict(concept=cid, policy=POLICY)),
            objective.objective_id, "Explain the cited source evidence for " + node["label"] + ".",
            "Explain only source-supported assertions; independent answer and rubric review required.", ev)
        math_items = tuple(sorted(e["equation_id"] for e in math["equations"]
                                 if e["anchor_id"] in ev)) if math["applicability"] == "REQUIRED" else ()
        units.append(dict(unit_id=unit_ids[cid], concept_id=cid, objective_id=objective.objective_id,
            decision_id=decision.decision_id, lesson_id=lesson_id, teaching_position=position,
            source_position=list(source_position[cid]), prerequisite_concept_ids=sorted(before[cid]),
            source_anchor_ids=list(ev), math_item_ids=list(math_items),
            math_artifact_id=artifact_ids["math"], math_sha256=artifact_hashes["math"],
            planned_mastery=asdict(MasteryCriterion()), measured_mastery=None,
            learner_state="NOT_SUPPLIED", misconception_status="NOT_EVIDENCED",
            example_status="SOURCE_EXAMPLES_NOT_PRODUCED", transfer_item_status="AUTHORING_REQUIRED",
            review_requirement="revisit_source_supported_concept_before_independent_application",
            cognitive_load=asdict(load), load_policy="TECHNICAL_DECLARED_UNIT_GUARDRAIL"))
        objectives.append(objective); decisions.append(decision); bindings.append(binding)
        objective_links.append(asdict(link)); lineages.append(line)
        retrieval.append(dict(question=asdict(recall), kind="VERBATIM_SOURCE_RECALL_REQUIREMENT",
                              measured=False, counts_as_mastery=False))
        formative.append(dict(check=asdict(check), planned=True, measured=False))
        requirements.extend(req); all_cells.extend(cells); loads.append((unit_ids[cid], load.total))
    require(not validate_lineage_graph(lineages), "pedagogy_lineage_cycle")
    plan = build_pedagogy_plan(plan_id="plan-" + digest(dict(run=run_id, inputs=artifact_hashes, policy=POLICY)),
        source_id=source_id, objective_ids=(o.objective_id for o in objectives),
        lesson_ids=(lesson_id,), decisions=decisions, policy_version=POLICY)
    coverage = objective_coverage_qa({b.objective_ids[0]: [i for c in b.assessments for i in c.item_ids]
                                    for b in bindings}, plan.objective_ids)
    alignment = assessment_alignment({o.objective_id: "APPLY" for o in objectives},
        ((item, c.objective_id, c.cognitive_level) for c in all_cells for item in c.item_ids))
    load_report = cognitive_load_qa(loads)
    require(coverage.passed and alignment.passed and load_report.passed, "pedagogy_native_validation")
    result = dict(schema=SCHEMA, run_id=run_id, source_id=source_id,
        source_sha256=document["source_sha256"], profile=PROFILE, policy=POLICY,
        scope=SCOPE, attempt=attempt,
        upstream={name: dict(artifact_id=artifact_ids[name], sha256=artifact_hashes[name]) for name in UPSTREAM},
        privacy="PRIVATE", evidence_kind="TECHNICAL_SOURCE_DERIVED",
        plan=asdict(plan), objectives=[asdict(o) for o in objectives], bindings=[asdict(b) for b in bindings],
        units=units, source_order=list(source_order), teaching_order=list(order),
        tie_break="canonical_native_concept_id_tie_break_technical_not_pedagogical_truth",
        objective_links=objective_links, lineages=[asdict(x) for x in lineages],
        assessment_requirements=[list(x) for x in requirements], retrieval_requirements=retrieval,
        formative_requirements=formative, misconception_plans=[], learner_state=None,
        measured_learner_mastery=False, math_applicability=math["applicability"],
        math_requirements=dict(artifact_id=artifact_ids["math"], sha256=artifact_hashes["math"],
            equation_ids=sorted(e["equation_id"] for e in math["equations"]),
            derivation_step_count=len(math["derivation_steps"]), evidence_regenerated=False),
        uncertainty=reasoning["uncertainty"], requires_review=True,
        native_checks=dict(objective_coverage=asdict(coverage), assessment_alignment=asdict(alignment),
                           cognitive_load=asdict(load_report)),
        provider_executed=False, academic_acceptance=False, product_accepted=False)
    # Native Director codecs compare canonical JSON structures, including array
    # shape.  Normalize tuple-valued frozen native records before returning.
    return strict_json(canonical(result))


def verify_components(value, document, knowledge, prerequisite, math, reasoning, **identity):
    require(type(value) is dict and canonical(value) == canonical(pedagogy_components(
        document, knowledge, prerequisite, math, reasoning, **identity)), "invalid_pedagogy_candidate")
    return value
