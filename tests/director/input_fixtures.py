"""Authored upstream fixtures executing actual canonical RE/PED functions.

No PDF extraction, learner assessment, comprehensive RE/PED assembly or model
quality is asserted. Source strings and curriculum signals are controlled data.
"""
from dataclasses import asdict, replace
import hashlib
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid5, NAMESPACE_URL

from bie.infrastructure.artifact_store import ArtifactCatalog, FileSystemCAS
from bie.director.director_artifacts import DirectorArtifactIO, canonical
from bie.director.director_inputs import (TeachingBinding, publish_source_catalog, load_source_catalog,
    publish_reasoning, publish_pedagogy, load_director_inputs)
from bie.director.qa_contract import SourceCatalog, SourcePage, SourcePassage
from bie.director.source_grounding_qa import SourceBytes
from bie.reasoning.decision_contracts import ReasoningDecision, EvidenceRef
from bie.reasoning.teaching_order import Candidate, decide as teaching_order
from bie.reasoning.chronology_reasoning import Event, year
from bie.reasoning.event_order_reasoning import event_order
from bie.pedagogy.learning_objective_generator import generate_objective
from bie.pedagogy.teaching_mode_selection import select_teaching_mode
from bie.pedagogy.assessment_blueprint import AssessmentCell, build_assessment_blueprint
from bie.pedagogy.pedagogy_plan_contract import PedagogyDecision, build_pedagogy_plan


CASES = {
    "science": {"title": "How a metal carries charge", "label": "mobile electrons in solid copper", "level": "UNDERSTAND",
        "text": "Solid copper conducts electric current because some electrons can move through the metal. The copper ions remain near their lattice positions. Current does not require copper ions to travel down the wire. This explanation concerns the solid metal; it does not assert that every copper compound conducts."},
    "economics": {"title": "Why money changes exchange", "label": "the double coincidence of wants", "level": "ANALYZE",
        "text": "In direct barter, each trader must want what the other offers. This is called the double coincidence of wants. A commonly accepted medium of exchange lets a seller receive money and buy from a different person later. Money can therefore separate selling from buying, but its usefulness depends on acceptance. This does not mean every object called money is accepted everywhere."},
    "history": {"title": "Ordering events without inventing a cause", "label": "temporal order and causal limits", "level": "UNDERSTAND",
        "text": "In this fictional archive exercise, event A is dated 1900 CE and event B is dated 1910 CE. These dates establish that A preceded B. Temporal precedence alone does not establish that A caused B. A causal explanation needs additional evidence beyond the dates."},
}


def upstream(root, case_id="science", *, review=False, media_type="text/plain; charset=utf-8", source_data=None):
    spec = CASES[case_id]; root = Path(root); root.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid5(NAMESPACE_URL, "bie-dir-execution-fixture/1/" + case_id))
    io = DirectorArtifactIO(ArtifactCatalog(FileSystemCAS(root / "cas")))
    text = spec["text"]; data = source_data if source_data is not None else text.encode()
    sha = "sha256:" + hashlib.sha256(data).hexdigest()
    page = SourcePage("page:" + case_id, "source:" + case_id, sha, 1, text, "authored-text-fixture/1")
    passage = SourcePassage("evidence:" + case_id, page.page_id, page.fingerprint(), "body", 0, len(text), text)
    catalog = SourceCatalog((page,), (passage,)); sources = (SourceBytes(page.source_id, data, media_type),)
    source_ref = publish_source_catalog(io, run_id, catalog, sources)
    _, _, _, refs, _ = load_source_catalog(io, source_ref)
    evidence = (EvidenceRef(refs[passage.evidence_id].artifact_id, "primary", .95),)
    objective = generate_objective("concept:" + case_id, spec["label"], (passage.evidence_id,))
    actual_order = teaching_order((Candidate(objective.concept_id, 0, 0, .9),))
    decision = ReasoningDecision("reasoning:" + case_id, "teaching_order", objective.concept_id,
        "Which grounded concept is ready to teach?", canonical({"ordered_concepts": actual_order}),
        "Canonical teaching_order sorted the supplied curriculum candidate by depth, source position and salience.",
        .95, list(evidence), requires_review=review)
    inferences = ()
    if case_id == "history":
        result = event_order((Event("A", "Fictional archive event A", year("1900 CE"), (evidence[0].artifact_id,)),
            Event("B", "Fictional archive event B", year("1910 CE"), (evidence[0].artifact_id,))), (), evidence)
        decision = result.to_decision(decision_type="teaching_order", subject_id=objective.concept_id,
            question="Which event precedes the other, without asserting causation?")
        if review: decision = replace(decision, requires_review=True)
        inferences = (result,)
    reasoning_ref = publish_reasoning(io, run_id, source_ref, (decision,), inferences)
    mode = select_teaching_mode(objective_level=spec["level"], prerequisite_readiness=.8,
        mathematical_density=.1, dynamic_system=False, source_supports_derivation=False)
    cell = AssessmentCell(objective.objective_id, objective.concept_id, spec["level"], None, False,
        ("assessment:" + case_id,), objective.evidence_ids)
    blueprint = build_assessment_blueprint(((objective.objective_id, objective.concept_id, spec["level"], False),), (cell,))
    ped_decision = PedagogyDecision("pedagogy:" + case_id, "teaching_mode", "mode:" + case_id,
        objective.evidence_ids, requires_review=review)
    plan = build_pedagogy_plan(plan_id="ped-plan:" + case_id, source_id=page.source_id,
        objective_ids=(objective.objective_id,), lesson_ids=("lesson:" + case_id,), decisions=(ped_decision,), policy_version="canonical-fixture/1")
    binding = TeachingBinding(ped_decision.decision_id, "lesson:" + case_id, (objective.objective_id,),
        (decision.decision_id,), mode, blueprint.cells)
    pedagogy_ref = publish_pedagogy(io, run_id, source_ref, reasoning_ref, plan, (objective,), (binding,))
    config = {"lesson_id": "lesson:" + case_id, "title": spec["title"], "language": "en"}
    inputs = load_director_inputs(io, reasoning_ref, pedagogy_ref, run_id=run_id, **config)
    return SimpleNamespace(root=root, case_id=case_id, run_id=run_id, io=io, source_ref=source_ref,
        reasoning_ref=reasoning_ref, pedagogy_ref=pedagogy_ref, inputs=inputs, config=config,
        objective=objective, decision=decision, plan=plan, binding=binding, actual_teaching_order=actual_order)


def replace_artifact(fixture, ref, *, payload=None, parents=None, metadata=None):
    old = fixture.io.load(ref)
    return fixture.io.derive(old.artifact_type, old.run_id, tuple(old.parent_refs) if parents is None else parents,
        old.payload if payload is None else payload, stage_id="TEST_MUTATION",
        metadata=old.metadata if metadata is None else metadata)


def load(fixture, **changes):
    refs = {"reasoning_ref": fixture.reasoning_ref, "pedagogy_ref": fixture.pedagogy_ref, **changes}
    return load_director_inputs(fixture.io, **refs, run_id=fixture.run_id, **fixture.config)
