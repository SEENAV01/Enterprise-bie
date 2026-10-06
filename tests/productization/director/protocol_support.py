"""Credential-free, request-dependent Director protocol evidence.

These providers are SYNTHETIC_TEST only. They echo exact supplied source quotes
and native IDs to exercise the real production assembly; they are not semantic,
pedagogical, factual-calibration or learner-outcome evidence. Runtime production
receives configured ModelProviders, not an import of this test module.
"""
from dataclasses import dataclass
import copy
import json

from bie.director.annotated_directing import AnnotationRuntime
from bie.director.hierarchical_annotation_review import HierarchicalAnnotationReviewPolicy
from bie.director.hierarchical_annotations import HierarchicalAnnotationPolicy
from bie.director.semantic_execution import EvaluatorIdentity
from bie.model_gateway.model_interface import ModelResponse


EVIDENCE_KIND = "SYNTHETIC_TEST"
GENERATOR = EvaluatorIdentity("synthetic-task033", "source-quote-generator", "protocol/1")
CRITIC = EvaluatorIdentity("synthetic-task033", "protocol-critic", "protocol/1")
ANNOTATOR = EvaluatorIdentity("synthetic-task033", "protocol-annotator", "protocol/1")
REVIEWER = EvaluatorIdentity("synthetic-task033", "protocol-reviewer", "protocol/1")
RATIONALE = "SYNTHETIC_TEST protocol interpretation; live quality and calibration are unproven."


def _span(row, start=0, end=None):
    end = len(row["text"]) if end is None else end
    return dict(utterance_id=row["utterance_id"], start_char=start, end_char=end,
                quote=row["text"][start:end])


def _ordered_decisions(inputs):
    """Follow the actual native PED dependency graph, not source/page ordering."""
    pending = {row["decision_id"]: row for row in inputs["pedagogy"]["decisions"]}
    completed, result = set(), []
    while pending:
        ready = sorted(key for key, value in pending.items()
                       if set(value["parent_decision_ids"]) <= completed)
        if not ready:
            raise ValueError("synthetic_pedagogy_dependency_invalid")
        for key in ready:
            result.append(pending.pop(key))
            completed.add(key)
    return result


def generator_record(payload):
    inputs = payload["inputs"]
    bindings = {row["decision_id"]: row for row in inputs["teaching_bindings"]}
    objectives = {row["objective_id"]: row for row in inputs["objectives"]}
    passages = {row["evidence_id"]: row for row in inputs["source_passages"]}
    reasoning = {row["decision_id"]: row for row in inputs["reasoning"]}
    evidence_bindings = dict(inputs["evidence_artifact_bindings"])
    operation = payload["operation"]
    if operation in ("PLAN", "PLAN_WINDOW"):
        wanted = set(payload.get("window", {}).get("decision_ids", bindings))
        scenes = []
        for decision in _ordered_decisions(inputs):
            did = decision["decision_id"]
            if did not in wanted:
                continue
            binding = bindings[did]
            if binding["mode"]["mode"] != "EXPLANATION":
                raise ValueError("synthetic_teaching_mode_not_supported")
            evidence = set(decision["evidence_ids"])
            evidence.update(e for oid in binding["objective_ids"]
                            for e in objectives[oid]["evidence_ids"])
            evidence.update(e for cell in binding["assessments"] for e in cell["evidence_ids"])
            evidence.update(evidence_bindings[reference["artifact_id"]]
                            for rid in binding["reasoning_decision_ids"]
                            for reference in reasoning[rid]["evidence_refs"])
            if not evidence or not evidence <= passages.keys():
                raise ValueError("synthetic_source_evidence_missing")
            sid = payload.get("scene_id_prefix", "scene:technical:") + did
            scenes.append(dict(scene_id=sid, title="Technical instructional unit " + str(len(scenes) + 1),
                purpose="Realize the supplied source-bound instructional decision", teaching_mode="EXPLANATION",
                pedagogy_decision_ids=[did], reasoning_decision_ids=binding["reasoning_decision_ids"],
                objective_ids=binding["objective_ids"], evidence_ids=sorted(evidence),
                parent_scene_ids=[scenes[-1]["scene_id"]] if scenes else [],
                teaching_goal=objectives[binding["objective_ids"][0]]["statement"], teaching_moves=["EXPLAIN"],
                assessment_item_ids=[item for cell in binding["assessments"] for item in cell["item_ids"]]))
        result = dict(input_fingerprint=inputs["input_fingerprint"], lesson_id=inputs["lesson_id"],
                      scenes=scenes, review_reasons=["SYNTHETIC_TEST_TECHNICAL_REALIZATION"])
        if operation == "PLAN_WINDOW":
            result.update(global_input_fingerprint=payload["global_input_fingerprint"],
                          window_fingerprint=payload["window_fingerprint"])
        return result
    if operation not in ("NARRATE", "NARRATE_WINDOW"):
        raise ValueError("synthetic_operation_not_supported")
    scene = payload["scene"]
    binding = bindings[scene["pedagogy_decision_ids"][0]]
    cells = {item: cell for cell in binding["assessments"] for item in cell["item_ids"]}
    beats = [dict(move="EXPLAIN", text=passages[eid]["quote"], evidence_ids=[eid],
                  objective_ids=scene["objective_ids"], pause_after_ms=500)
             for eid in scene["evidence_ids"]]
    assessments = []
    for item in scene["assessment_item_ids"]:
        evidence = cells[item]["evidence_ids"]
        answer = "\n".join(passages[eid]["quote"] for eid in evidence)
        assessments.append(dict(item_id=item, question="What does the cited source state?",
            expected_answer=answer, success_criteria=["Use only the cited evidence."],
            evidence_ids=evidence, response_time_ms=8000))
    result = dict(input_fingerprint=inputs["input_fingerprint"], plan_fingerprint=payload["plan_fingerprint"],
                  scene_id=scene["scene_id"], beats=beats, assessments=assessments,
                  review_reasons=["SYNTHETIC_TEST_TECHNICAL_REALIZATION"])
    if "window_fingerprint" in payload:
        result.update(global_input_fingerprint=payload["global_input_fingerprint"],
                      window_fingerprint=payload["window_fingerprint"])
    return result


def _annotation_record(payload):
    """Cover actual words/IDs without inventing concepts, terms or relations."""
    rows = payload["utterances"]
    index = {row["utterance_id"]: row for row in rows}
    concepts = {row["objective_id"]: row["concept_id"] for row in payload["inputs"]["objectives"]}
    common = dict(confidence=.95, rationale=RATIONALE)
    prefix = payload.get("annotation_id_prefix", "technical:")
    claims = []
    for number, sentence in enumerate(payload["complete_sentence_spans"]):
        row = index[sentence["utterance_id"]]
        selected = _span(row, sentence["start_char"], sentence["end_char"])
        claims.append(dict(claim_id=prefix + "claim:" + str(number), span=selected,
                           kind="QUESTION" if selected["quote"].endswith("?") else "FACT",
                           evidence_ids=row["evidence_ids"], **common))
    questions = {question: item for item, question, answer in payload["assessment_bindings"]}
    answers = {answer: item for item, question, answer in payload["assessment_bindings"]}
    discourse, pacing, seen = [], [], set()
    by_scene = {}
    for number, row in enumerate(rows):
        uid = row["utterance_id"]
        by_scene.setdefault(row["scene_id"], []).append(row)
        referenced = {concepts[oid] for oid in row["objective_ids"]}
        discourse.append(dict(utterance_id=uid, introduced_concepts=sorted(referenced - seen),
            required_concepts=sorted(referenced & seen), references=[],
            opens_questions=[questions[uid]] if uid in questions else [],
            answers_questions=[answers[uid]] if uid in answers else [], **common))
        seen.update(referenced)
        obligation = payload["pacing_obligations"][uid]
        pacing.append(dict(beat_id=prefix + "pace:" + str(number), span=_span(row),
            mode=obligation["required_mode"] or "EXPLAIN", concept_ids=sorted(referenced),
            evidence_ids=row["evidence_ids"], objective_ids=row["objective_ids"],
            minimum_reflection_ms=obligation["minimum_reflection_ms"], **common))
    order = list(by_scene)
    transitions = [dict(from_scene=left, to_scene=right, relation="UNRESOLVED", cue_span=None,
                        **common) for left, right in zip(order, order[1:])]
    return {key: payload[key] for key in ("input_fingerprint", "snapshot_fingerprint", "plan_fingerprint")} | dict(
        claims=claims, discourse=discourse, transitions=transitions, terms=[], advisories=[],
        repetitions=[], emphasis=[], pacing=pacing, review_reasons=["SYNTHETIC_TEST_UNCALIBRATED_ANNOTATIONS"])


def annotator_record(payload):
    operation = payload["operation"]
    if operation == "ANNOTATE_DISCOURSE_RETRIEVAL":
        return {key: payload[key] for key in
                ("input_fingerprint", "snapshot_fingerprint", "plan_fingerprint", "scope_fingerprint")} | dict(
            reference_links=[], repetitions=[], review_reasons=["SYNTHETIC_TEST_NO_RELATION_INFERRED"])
    value = _annotation_record(payload)
    value["scope_fingerprint"] = payload["scope_fingerprint"]
    if operation == "ANNOTATE_SCENE":
        return value
    if operation == "ANNOTATE_DISCOURSE_LEAF":
        return {key: value[key] for key in ("input_fingerprint", "snapshot_fingerprint", "plan_fingerprint",
            "scope_fingerprint", "discourse", "transitions", "terms", "repetitions", "review_reasons")}
    if operation == "ANNOTATE_DISCOURSE_BOUNDARY":
        return {key: value[key] for key in ("input_fingerprint", "snapshot_fingerprint", "plan_fingerprint",
            "scope_fingerprint", "transitions", "review_reasons")}
    raise ValueError("synthetic_annotation_operation_not_supported")


def critic_record(payload):
    return {key: payload[key] for key in ("claim_id", "claim_fingerprint", "passage_fingerprints")} | dict(
        verdict="SUPPORTED", confidence=.95, rationale=RATIONALE)


def reviewer_record(payload):
    return {key: payload[key] for key in
            ("input_fingerprint", "snapshot_fingerprint", "annotation_fingerprint", "review_scope_fingerprint")} | dict(
        judgments=[dict(subject_id=subject, verdict="SUPPORTED", confidence=.95, rationale=RATIONALE)
                   for subject in payload["required_subject_ids"]])


class ProtocolProvider:
    def __init__(self, identity, record, transform=None):
        self.identity, self.record, self.transform = identity, record, transform
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        payload = json.loads(request.messages[1]["content"])
        value = self.record(payload)
        if self.transform:
            value = self.transform(payload, copy.deepcopy(value), len(self.requests))
        return ModelResponse(self.identity.provider, self.identity.model, value, {}, "completed",
                             dict(evidence_kind=EVIDENCE_KIND, live_quality_evidence=False))


@dataclass
class ProtocolStack:
    generator: ProtocolProvider
    critic: ProtocolProvider
    annotator: ProtocolProvider
    reviewer: ProtocolProvider
    annotations: AnnotationRuntime
    generator_identity: EvaluatorIdentity = GENERATOR
    critic_identity: EvaluatorIdentity = CRITIC
    evidence_kind: str = EVIDENCE_KIND

    def descriptor(self):
        from bie.productization.director_contract import DirectorProviderStack
        return DirectorProviderStack(self.generator, self.generator_identity,
            self.critic, self.critic_identity, self.annotations, self.evidence_kind).descriptor()

    @property
    def calls(self):
        return dict(generator=len(self.generator.requests), critic=len(self.critic.requests),
                    annotator=len(self.annotator.requests), reviewer=len(self.reviewer.requests))


def make_stack():
    generator = ProtocolProvider(GENERATOR, generator_record)
    critic = ProtocolProvider(CRITIC, critic_record)
    annotator = ProtocolProvider(ANNOTATOR, annotator_record)
    reviewer = ProtocolProvider(REVIEWER, reviewer_record)
    annotations = AnnotationRuntime(annotator, ANNOTATOR, reviewer, REVIEWER,
                                   HierarchicalAnnotationPolicy(), HierarchicalAnnotationReviewPolicy())
    return ProtocolStack(generator, critic, annotator, reviewer, annotations)


def config_for_stack(stack=None, *, title="Explicit synthetic source lesson", language="en"):
    """Test-only explicit governance input, never a production fallback title."""
    from bie.productization.director_contract import director_config
    stack = make_stack() if stack is None else stack
    return director_config(title=title, language=language, providers=stack.descriptor(),
                           evidence_kind=stack.evidence_kind)


DEFAULT_DIRECTOR = config_for_stack()
