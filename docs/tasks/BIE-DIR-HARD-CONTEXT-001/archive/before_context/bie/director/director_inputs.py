"""BIE-DIR-HARD-INPUTS-001: strict adapters for real canonical RE/PED objects.

Binding records attach actual PED mode/assessment outputs to their decisions;
they contain no scene plan, narration, model verdict or precomputed QA score.
"""
from dataclasses import asdict, dataclass, replace
import hashlib
from bie.bie_core.artifact_contracts import ArtifactEnvelope, ArtifactRef, ProducerIdentity, ProvenanceSource, ProvenanceSummary
from bie.reasoning.decision_contracts import ReasoningDecision, DecisionAlternative, EvidenceRef
from bie.reasoning.grounded_result import GroundedResult
from bie.pedagogy.learning_objective_generator import LearningObjective
from bie.pedagogy.pedagogy_plan_contract import UnifiedPedagogyPlan, PedagogyDecision, build_pedagogy_plan
from bie.pedagogy.teaching_mode_selection import TeachingModeDecision, MODES
from bie.pedagogy.assessment_blueprint import AssessmentCell, build_assessment_blueprint
from .director_artifacts import canonical, fingerprint, fields, parse_json, reference, array
from .contract_validation import ids, items, nonblank, finite, acyclic
from .qa_contract import SourceCatalog, SourcePage, SourcePassage, validate_catalog, immutable
from .source_grounding_qa import SourceBytes


@dataclass(frozen=True)
class TeachingBinding:
    decision_id: str
    lesson_id: str
    objective_ids: tuple[str, ...]
    reasoning_decision_ids: tuple[str, ...]
    mode: TeachingModeDecision
    assessments: tuple[AssessmentCell, ...]


@dataclass(frozen=True)
class DirectorInputs:
    lesson_id: str
    title: str
    language: str
    catalog: SourceCatalog
    sources: tuple[SourceBytes, ...]
    reasoning: tuple[ReasoningDecision, ...]
    inferences: tuple[GroundedResult, ...]
    pedagogy: UnifiedPedagogyPlan
    objectives: tuple[LearningObjective, ...]
    bindings: tuple[TeachingBinding, ...]
    evidence_artifacts: tuple[tuple[str, str], ...]
    parent_refs: tuple[ArtifactRef, ...]
    review_reasons: tuple[str, ...]

    def to_model_data(self):
        result = asdict(self)
        result["sources"] = [{"source_id": s.source_id, "sha256": "sha256:" + hashlib.sha256(s.data).hexdigest(),
                              "media_type": s.media_type, "bytes": len(s.data)} for s in self.sources]
        result["inferences"] = [r.to_dict() for r in self.inferences]
        return result

    def fingerprint(self):
        return fingerprint(self.to_model_data())


def _catalog(value):
    fields(value, ("pages", "passages"), "source catalog")
    result = SourceCatalog(tuple(SourcePage(**fields(p, SourcePage.__dataclass_fields__, "source page")) for p in value["pages"]),
                           tuple(SourcePassage(**fields(p, SourcePassage.__dataclass_fields__, "source passage")) for p in value["passages"]))
    pages, passages = validate_catalog(result)
    if not pages or not passages:
        raise ValueError("nonempty extracted source catalog required")
    return result


def _sources(catalog, sources):
    if type(sources) is not tuple or any(not isinstance(s, SourceBytes) for s in sources):
        raise ValueError("expected immutable SourceBytes records")
    ids(tuple(s.source_id for s in sources), "source ids")
    by_id = {s.source_id: s for s in sources}
    if set(by_id) != {p.source_id for p in catalog.pages}:
        raise ValueError("source bytes must exactly cover the catalog")
    review = set()
    for page in catalog.pages:
        source = by_id[page.source_id]
        nonblank(source.media_type, "media type")
        if type(source.data) is not bytes or not source.data or "sha256:" + hashlib.sha256(source.data).hexdigest() != page.source_sha256:
            raise ValueError("source bytes do not match catalog")
        if source.media_type == "text/plain; charset=utf-8":
            if page.page_number != 1 or source.data.decode("utf-8") != page.text:
                raise ValueError("UTF-8 extraction must equal the complete one-page source")
        else:
            review.add("EXTRACTION_ACCURACY_UNVERIFIED")
    return tuple(sorted(review))


def publish_source_catalog(io, run_id, catalog, sources):
    """Wrap actual extraction and source bytes, without claiming to run BI/OCR."""
    catalog = _catalog(parse_json(canonical(asdict(catalog))))
    review = _sources(catalog, sources)
    roots = {}
    for source in sources:
        blob = io.catalog.cas.put_bytes(source.data)
        artifact = ArtifactEnvelope.create("source.document", "1.0.0", run_id,
            ProducerIdentity("bie.director.source_adapter", "1.0.0", "deterministic"), [],
            ProvenanceSummary([ProvenanceSource(source.source_id, {"kind": "whole_source"}, "sha256:" + blob.digest)]),
            {"requires_review": bool(review)},
            {"source_id": source.source_id, "source_sha256": "sha256:" + blob.digest,
             "media_type": source.media_type, "blob": asdict(blob)})
        roots[source.source_id] = io.put(artifact, "SOURCE")
    pages, _ = validate_catalog(catalog)
    bindings = []
    for passage in catalog.passages:
        page = pages[passage.page_id]
        artifact = ArtifactEnvelope.create("source.block", "1.0.0", run_id,
            ProducerIdentity("bie.director.extraction_adapter", "1.0.0", "deterministic"), [roots[page.source_id]],
            ProvenanceSummary([ProvenanceSource(page.source_id, {"page": page.page_number, "region": passage.region_id,
                "start_char": passage.start_char, "end_char": passage.end_char}, page.source_sha256,
                "sha256:" + hashlib.sha256(passage.quote.encode()).hexdigest())]),
            {"requires_review": bool(review)}, {"page": asdict(page), "passage": asdict(passage)})
        bindings.append({"evidence_id": passage.evidence_id, "artifact_ref": asdict(io.put(artifact, "DOCUMENT_INTELLIGENCE"))})
    return io.derive("document.source_catalog", run_id, tuple(reference(b["artifact_ref"]) for b in bindings),
        {"catalog": asdict(catalog), "evidence_bindings": bindings, "source_refs": [asdict(roots[k]) for k in sorted(roots)]},
        stage_id="DOCUMENT_INTELLIGENCE", metadata={"requires_review": bool(review), "review_reasons": list(review)})


def load_source_catalog(io, ref):
    graph = io.load_graph((ref,)); artifact = graph[ref.artifact_id]
    if artifact.artifact_type != "document.source_catalog" or artifact.schema_version != "1.0.0":
        raise ValueError("unsupported source catalog envelope")
    payload = fields(artifact.payload, ("catalog", "evidence_bindings", "source_refs"), "source catalog payload")
    catalog = _catalog(payload["catalog"]); pages, passages = validate_catalog(catalog)
    bindings = {}
    for binding in payload["evidence_bindings"]:
        fields(binding, ("evidence_id", "artifact_ref"), "evidence binding")
        eid = binding["evidence_id"]; ref = reference(binding["artifact_ref"])
        if eid not in passages or eid in bindings or ref not in artifact.parent_refs:
            raise ValueError("source evidence binding mismatch")
        block = io.load(ref); passage = passages[eid]
        if block.artifact_type != "source.block" or block.schema_version != "1.0.0" or block.payload != {"page": asdict(pages[passage.page_id]), "passage": asdict(passage)}:
            raise ValueError("catalog differs from source block")
        bindings[eid] = ref
    if set(bindings) != set(passages) or set(r.artifact_id for r in artifact.parent_refs) != {r.artifact_id for r in bindings.values()}:
        raise ValueError("catalog passage coverage mismatch")
    sources = []; source_refs = {}
    for raw in payload["source_refs"]:
        ref = reference(raw)
        if ref.artifact_id not in graph:
            raise ValueError("source document outside ancestry")
        source = io.load(ref)
        sources.append(SourceBytes(source.payload["source_id"], io.source_bytes(ref), source.payload["media_type"]))
        source_refs[source.payload["source_id"]] = ref
    review = _sources(catalog, tuple(sources))
    for eid, ref in bindings.items():
        block = io.load(ref); passage = passages[eid]; page = pages[passage.page_id]
        expected = ProvenanceSource(page.source_id, {"page": page.page_number, "region": passage.region_id,
            "start_char": passage.start_char, "end_char": passage.end_char}, page.source_sha256,
            "sha256:" + hashlib.sha256(passage.quote.encode()).hexdigest())
        if block.parent_refs != [source_refs[page.source_id]] or block.provenance_summary.sources != [expected]:
            raise ValueError("source block provenance/parent mismatch")
    return artifact, catalog, tuple(sources), bindings, review


def _decision(value):
    fields(value, ReasoningDecision.__dataclass_fields__, "reasoning decision")
    result = ReasoningDecision(**{**value,
        "evidence_refs": tuple(EvidenceRef(**fields(e, EvidenceRef.__dataclass_fields__, "reasoning evidence")) for e in value["evidence_refs"]),
        "alternatives": tuple(DecisionAlternative(**fields(a, DecisionAlternative.__dataclass_fields__, "reasoning alternative")) for a in value["alternatives"]),
        **{key: tuple(array(value[key], key)) for key in ("premises", "constraints", "uncertainty", "downstream_effects", "depends_on_decisions", "policy_tags")}})
    immutable(result)
    for key in ("decision_id", "decision_type", "subject_id", "question", "selected_option", "rationale_summary"):
        nonblank(getattr(result, key), key)
    for key in ("premises", "constraints", "uncertainty", "downstream_effects", "depends_on_decisions", "policy_tags"):
        ids(getattr(result, key), key, required=False)
    if type(result.requires_review) is not bool:
        raise ValueError("reasoning review flag must be boolean")
    finite(result.confidence, "reasoning confidence", high=1)
    for evidence in result.evidence_refs:
        nonblank(evidence.artifact_id, "reasoning evidence id"); finite(evidence.strength, "evidence strength", high=1)
        if evidence.note is not None: nonblank(evidence.note, "evidence note")
    ids(tuple(e.artifact_id for e in result.evidence_refs), "reasoning evidence")
    for alternative in result.alternatives:
        nonblank(alternative.option_id, "option id"); nonblank(alternative.description, "option description")
        if alternative.score is not None: finite(alternative.score, "alternative score", high=1)
        if alternative.rejected_reason is not None: nonblank(alternative.rejected_reason, "rejected reason")
    result.validate(critical=True)
    return result


def _inference(value):
    fields(value, ("result_id", "schema_version", "task_id", "operation", "status", "inputs", "value", "evidence_refs", "assumptions", "uncertainty", "confidence", "requires_review"), "reasoning inference")
    finite(value["confidence"], "inference confidence", high=1)
    if type(value["requires_review"]) is not bool: raise ValueError("inference review flag must be boolean")
    result = GroundedResult(value["task_id"], value["operation"], value["status"], canonical(value["inputs"]), canonical(value["value"]),
        tuple(EvidenceRef(**r) for r in value["evidence_refs"]), tuple(value["assumptions"]), tuple(value["uncertainty"]), value["schema_version"])
    if result.to_dict() != value: raise ValueError("stale reasoning inference")
    return result


def publish_reasoning(io, run_id, source_ref, decisions, inferences=()):
    source, _, _, bindings, _ = load_source_catalog(io, source_ref)
    if source.run_id != run_id: raise ValueError("cross-run source")
    decisions = tuple(_decision(parse_json(canonical(asdict(d)))) for d in items(decisions, "reasoning decisions"))
    ids(tuple(d.decision_id for d in decisions), "reasoning decisions")
    acyclic({d.decision_id: d.depends_on_decisions for d in decisions})
    allowed = {ref.artifact_id: ref for ref in bindings.values()}
    if any(e.artifact_id not in allowed for d in decisions for e in d.evidence_refs):
        raise ValueError("reasoning evidence must resolve to this catalog's actual source-block artifacts")
    inferences = items(inferences, "inferences", required=False)
    inference_refs = []
    for result in inferences:
        if not isinstance(result, GroundedResult): raise ValueError("expected canonical GroundedResult")
        if any(e.artifact_id not in allowed for e in result.evidence_refs): raise ValueError("inference evidence outside source")
        envelope = result.to_artifact(run_id=run_id, parents=tuple(io.load(allowed[e.artifact_id]) for e in result.evidence_refs))
        inference_refs.append(io.put(envelope, "REASONING"))
    ids(tuple(r.artifact_id for r in inference_refs), "inference refs", required=False)
    review = any(d.requires_review or d.uncertainty or any(e.role == "contradicting" for e in d.evidence_refs) for d in decisions)
    review = review or any(r.requires_review or r.assumptions for r in inferences)
    return io.derive("reasoning.decision_set", run_id, (source_ref,) + tuple(inference_refs),
        {"source_catalog_ref": asdict(source_ref), "decisions": [asdict(d) for d in decisions], "inference_refs": [asdict(r) for r in inference_refs]},
        stage_id="REASONING", metadata={"requires_review": bool(review)})


def _pedagogy(value):
    fields(value, UnifiedPedagogyPlan.__dataclass_fields__, "pedagogy plan")
    decisions = tuple(PedagogyDecision(**{**fields(d, PedagogyDecision.__dataclass_fields__, "pedagogy decision"),
        "evidence_ids": ids(d["evidence_ids"], "PED evidence"),
        "parent_decision_ids": ids(d["parent_decision_ids"], "PED parents", required=False)}) for d in value["decisions"])
    for decision in decisions:
        finite(decision.confidence, "PED confidence", high=1)
    result = build_pedagogy_plan(plan_id=value["plan_id"], source_id=value["source_id"], objective_ids=value["objective_ids"],
        lesson_ids=value["lesson_ids"], decisions=decisions, policy_version=value["policy_version"])
    if parse_json(canonical(asdict(result))) != value: raise ValueError("noncanonical or weakened PED plan")
    return result


def _binding(value):
    fields(value, TeachingBinding.__dataclass_fields__, "teaching binding")
    mode = TeachingModeDecision(**fields(value["mode"], TeachingModeDecision.__dataclass_fields__, "canonical teaching mode"))
    if mode.mode not in MODES or type(mode.requires_review) is not bool: raise ValueError("unsupported teaching mode")
    nonblank(mode.reason, "teaching-mode reason"); finite(mode.confidence, "mode confidence", high=1)
    if mode.confidence < .75 and not mode.requires_review: raise ValueError("uncertain teaching mode needs review")
    cells = tuple(AssessmentCell(**{**fields(c, AssessmentCell.__dataclass_fields__, "assessment cell"),
        "item_ids": ids(c["item_ids"], "assessment items"), "evidence_ids": ids(c["evidence_ids"], "assessment evidence")}) for c in value["assessments"])
    result = TeachingBinding(nonblank(value["decision_id"], "PED decision id"), nonblank(value["lesson_id"], "lesson id"),
        ids(value["objective_ids"], "binding objectives"), ids(value["reasoning_decision_ids"], "binding RE decisions"), mode, cells)
    immutable(result)
    if not cells: raise ValueError("actual canonical assessment cells required")
    return result


def _ped_payload(payload, catalog, reasoning):
    fields(payload, ("source_catalog_ref", "reasoning_ref", "plan", "objectives", "bindings"), "pedagogy artifact payload")
    plan = _pedagogy(payload["plan"])
    objectives = tuple(LearningObjective(**{**fields(o, LearningObjective.__dataclass_fields__, "objective"),
        "evidence_ids": ids(o["evidence_ids"], "objective evidence")}) for o in payload["objectives"])
    ids(tuple(o.objective_id for o in objectives), "objectives")
    if {o.objective_id for o in objectives} != set(plan.objective_ids): raise ValueError("PED objective coverage mismatch")
    passages = {p.evidence_id for p in catalog.passages}; by_objective = {o.objective_id: o for o in objectives}
    if plan.source_id not in {p.source_id for p in catalog.pages}: raise ValueError("PED source mismatch")
    for objective in objectives:
        nonblank(objective.concept_id, "concept id"); nonblank(objective.statement, "objective statement")
        if not set(objective.evidence_ids) <= passages: raise ValueError("objective outside source catalog")
    if any(not set(d.evidence_ids) <= passages for d in plan.decisions): raise ValueError("PED evidence outside catalog")
    bindings = tuple(_binding(v) for v in payload["bindings"])
    ids(tuple(b.decision_id for b in bindings), "teaching binding decision ids")
    by_decision = {d.decision_id: d for d in plan.decisions}; re_ids = {d.decision_id for d in reasoning}
    if {b.decision_id for b in bindings} != set(by_decision): raise ValueError("every PED decision needs an explicit teaching binding")
    if {b.lesson_id for b in bindings} != set(plan.lesson_ids): raise ValueError("PED lesson coverage mismatch")
    if {o for b in bindings for o in b.objective_ids} != set(plan.objective_ids): raise ValueError("teaching objectives mismatch")
    for binding in bindings:
        if not set(binding.reasoning_decision_ids) <= re_ids: raise ValueError("unresolved RE binding")
        decision = by_decision[binding.decision_id]
        evidence = {e for oid in binding.objective_ids for e in by_objective[oid].evidence_ids}
        if not evidence <= set(decision.evidence_ids): raise ValueError("PED decision does not ground its bound objectives")
        for cell in binding.assessments:
            if cell.objective_id not in binding.objective_ids or cell.concept_id != by_objective[cell.objective_id].concept_id:
                raise ValueError("assessment objective/concept mismatch")
            if not set(cell.evidence_ids) <= evidence: raise ValueError("assessment evidence outside objective")
            if cell.misconception_id is not None: nonblank(cell.misconception_id, "misconception id")
        requirements = tuple((c.objective_id, c.concept_id, c.cognitive_level, c.transfer) for c in binding.assessments)
        report = build_assessment_blueprint(requirements, binding.assessments)
        if not report.passed or {c.objective_id for c in report.cells} != set(binding.objective_ids):
            raise ValueError("assessment coverage mismatch")
    return plan, objectives, bindings


def publish_pedagogy(io, run_id, source_ref, reasoning_ref, plan, objectives, bindings):
    source, catalog, _, _, _ = load_source_catalog(io, source_ref)
    re_artifact = io.load(reasoning_ref)
    if re_artifact.artifact_type != "reasoning.decision_set" or reference(re_artifact.payload["source_catalog_ref"]) != source_ref:
        raise ValueError("reasoning/source binding mismatch")
    reasoning = tuple(_decision(d) for d in re_artifact.payload["decisions"])
    payload = parse_json(canonical({"source_catalog_ref": asdict(source_ref), "reasoning_ref": asdict(reasoning_ref),
        "plan": asdict(plan), "objectives": [asdict(o) for o in objectives], "bindings": [asdict(b) for b in bindings]}))
    plan, objectives, bindings = _ped_payload(payload, catalog, reasoning)
    review = plan.requires_review or any(b.mode.requires_review for b in bindings) or re_artifact.metadata.get("requires_review") is True
    return io.derive("pedagogy.plan", run_id, (source_ref, reasoning_ref), payload, stage_id="PEDAGOGY", metadata={"requires_review": review})


def load_director_inputs(io, reasoning_ref, pedagogy_ref, *, lesson_id, title, language, run_id):
    for value in (lesson_id, title, language, run_id): nonblank(value, "director request")
    graph = io.load_graph((reasoning_ref, pedagogy_ref))
    re_artifact = io.load(reasoning_ref); ped_artifact = io.load(pedagogy_ref)
    if any(a.run_id != run_id for a in graph.values()): raise ValueError("cross-run artifact ancestry")
    if (re_artifact.artifact_type, ped_artifact.artifact_type) != ("reasoning.decision_set", "pedagogy.plan"):
        raise ValueError("expected actual reasoning and pedagogy envelopes")
    if re_artifact.schema_version != "1.0.0" or ped_artifact.schema_version != "1.0.0": raise ValueError("unsupported adapter schema")
    rp = fields(re_artifact.payload, ("source_catalog_ref", "decisions", "inference_refs"), "reasoning payload")
    source_ref = reference(rp["source_catalog_ref"])
    if source_ref not in re_artifact.parent_refs: raise ValueError("source catalog not in RE parents")
    source, catalog, sources, evidence_bindings, source_review = load_source_catalog(io, source_ref)
    reasoning = tuple(_decision(d) for d in rp["decisions"])
    ids(tuple(d.decision_id for d in reasoning), "RE decision ids")
    acyclic({d.decision_id: d.depends_on_decisions for d in reasoning})
    allowed = {ref.artifact_id for ref in evidence_bindings.values()}
    if any(e.artifact_id not in allowed for d in reasoning for e in d.evidence_refs): raise ValueError("unresolved RE source evidence")
    inferences = []
    for raw in rp["inference_refs"]:
        ref = reference(raw)
        if ref not in re_artifact.parent_refs: raise ValueError("inference is not a reasoning parent")
        artifact = io.load(ref)
        if artifact.artifact_type != "reasoning.inference": raise ValueError("expected actual inference artifact")
        result = _inference(artifact.payload)
        if not {e.artifact_id for e in result.evidence_refs} <= allowed: raise ValueError("inference evidence outside catalog")
        if {e.artifact_id for e in result.evidence_refs} != {p.artifact_id for p in artifact.parent_refs}:
            raise ValueError("inference parent/evidence mismatch")
        inferences.append(result)
    by_inference = {r.result_id: r for r in inferences}
    if len(by_inference) != len(inferences): raise ValueError("duplicate inference artifact")
    for decision in reasoning:
        result = by_inference.get(decision.decision_id)
        if result and (decision.selected_option != result.value_json or tuple(decision.evidence_refs) != result.evidence_refs
                       or decision.confidence != result.confidence or result.requires_review and not decision.requires_review):
            raise ValueError("reasoning decision differs from its actual inference")
    pp = ped_artifact.payload
    if reference(pp["reasoning_ref"]) != reasoning_ref or reference(pp["source_catalog_ref"]) != source_ref:
        raise ValueError("stale PED/RE/source pairing")
    if set(ped_artifact.parent_refs) != {source_ref, reasoning_ref}: raise ValueError("PED parent refs mismatch")
    plan, objectives, bindings = _ped_payload(pp, catalog, reasoning)
    if lesson_id not in plan.lesson_ids: raise ValueError("lesson not in actual PED plan")
    selected = tuple(b for b in bindings if b.lesson_id == lesson_id)
    selected_ids = {b.decision_id for b in selected}
    # A cross-lesson prerequisite needs an explicit mastery/bridge artifact. Do
    # not assume that an earlier lesson was understood or silently drop its edge.
    if any(not set(d.parent_decision_ids) <= selected_ids for d in plan.decisions if d.decision_id in selected_ids):
        raise ValueError("cross-lesson prerequisite needs an explicit upstream bridge")
    needed_objectives = {oid for b in selected for oid in b.objective_ids}
    review = set(source_review)
    if plan.requires_review: review.add("UPSTREAM_PED_REVIEW")
    if any(d.requires_review or d.uncertainty or any(e.role == "contradicting" for e in d.evidence_refs) for d in reasoning): review.add("UPSTREAM_RE_REVIEW")
    if any(r.requires_review or r.assumptions for r in inferences): review.add("UPSTREAM_INFERENCE_REVIEW")
    if any(b.mode.requires_review for b in selected): review.add("UPSTREAM_MODE_REVIEW")
    if any(a.metadata.get("requires_review") is True for a in graph.values()): review.add("UPSTREAM_ARTIFACT_REVIEW")
    return DirectorInputs(lesson_id, title, language, catalog, sources, reasoning, tuple(inferences), plan,
        tuple(o for o in objectives if o.objective_id in needed_objectives), selected,
        tuple(sorted((ref.artifact_id, eid) for eid, ref in evidence_bindings.items())),
        (source_ref, reasoning_ref, pedagogy_ref), tuple(sorted(review)))
