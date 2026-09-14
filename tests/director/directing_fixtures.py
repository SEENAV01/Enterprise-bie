"""Preauthored provider responses, deliberately outside production generation.

These responses test execution/protocol behavior. They do not establish that a
live model can produce good teaching, or that an uncalibrated critic is correct.
"""
from dataclasses import replace
import copy, json
from bie.model_gateway.model_interface import ModelResponse
from bie.director.semantic_execution import EvaluatorIdentity
from bie.director.director_artifacts import canonical
from bie.director.director_model import DirectingPolicy
from bie.director.director_executor import DirectorStageExecutor
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore
from bie.infrastructure.orchestrator import ExecutionContext
from semantic_fixtures import ProtocolFixtureProvider, IDENTITY

GENERATOR = EvaluatorIdentity("protocol-fixture", "director", "adapter/1")
SCRIPTS = {
    "science": [
        {"title": "What moves in the wire?", "moves": ["EXPLAIN", "CONFRONT"], "text": [
            "Imagine tracing the charge through solid copper. Some electrons are free to move through the metal, so charge can pass along it. The explanation depends on mobile electrons in the solid metal.",
            "Now separate the motion of charge from the motion of the lattice. Copper ions stay near their lattice positions. We should not picture the ions travelling along the wire just because there is a current." ]},
        {"title": "Keep the explanation within its evidence", "moves": ["TRANSFER"], "text": [
            "Before applying this explanation elsewhere, keep its boundary in view. The source describes solid copper. It does not establish that every copper compound conducts, so the material being discussed matters."]},
    ],
    "economics": [
        {"title": "Separate the matching problem from acceptance", "moves": ["ELICIT", "EXPLAIN", "PROBE"], "text": [
            "Suppose each trader must want what the other offers. What would have to match before their direct barter could go ahead? Focus on their wants, as well as what they have available.",
            "This matching requirement is the double coincidence of wants. With a commonly accepted medium of exchange, a seller can receive money and buy from a different person later. Selling and buying can therefore be separated.",
            "Now ask what the word accepted contributes. Calling an object money does not prove that everyone accepts it everywhere. The exchange advantage depends on people accepting the medium."]},
    ],
    "history": [
        {"title": "Read the declared dates", "moves": ["EXPLAIN"], "text": [
            "This is a fictional archive exercise. Event A is dated 1900 CE and event B is dated 1910 CE. Keep those source dates attached to the events as we compare them."]},
        {"title": "Use the actual temporal result", "moves": ["EXPLAIN"], "text": [
            "The earlier date belongs to A, so A preceded B. This is the temporal order supported by the dates. We can state that order without adding a causal story."]},
        {"title": "Locate the boundary of the inference", "moves": ["CONFRONT"], "text": [
            "A came before B, but before does not by itself mean because of. To say that A caused B, we would need additional causal evidence beyond these dates."]},
    ],
}
ASSESSMENTS = {
    "science": ("Does current in solid copper require its ions to travel down the wire? Explain what carries the moving charge.",
        "No. Some electrons move through the metal while the copper ions remain near their lattice positions.",
        ["Distinguish the mobile electrons from the ions near their lattice positions.", "Keep the claim limited to the solid copper described by the source."]),
    "economics": ("Why can an accepted medium of exchange help when traders do not each want what the other offers?",
        "It lets a seller receive money and buy from a different person later, separating selling from buying.",
        ["Explain how this avoids requiring the same pair of traders to satisfy the double coincidence of wants.", "State that the medium must be accepted; acceptance everywhere is not established."]),
    "history": ("Do the dates establish that A caused B, or only that A preceded B? Explain the limit.",
        "They establish that A preceded B. They do not by themselves establish that A caused B.",
        ["Separate temporal precedence from causation.", "Recognize that causal explanation needs additional evidence beyond the dates."]),
}


def response_record(payload):
    inputs = payload["inputs"]; case_id = inputs["lesson_id"].split(":")[-1]
    binding = inputs["teaching_bindings"][0]; evidence = inputs["objectives"][0]["evidence_ids"]
    if payload["operation"] == "PLAN":
        scenes = []
        for i, script in enumerate(SCRIPTS[case_id]):
            scene_id = "scene:" + case_id + ":" + str(i + 1)
            scenes.append({"scene_id": scene_id, "title": script["title"], "purpose": "Teach " + script["title"],
                "teaching_mode": binding["mode"]["mode"], "pedagogy_decision_ids": [binding["decision_id"]],
                "reasoning_decision_ids": binding["reasoning_decision_ids"], "objective_ids": binding["objective_ids"],
                "evidence_ids": evidence, "parent_scene_ids": [scenes[-1]["scene_id"]] if scenes else [],
                "teaching_goal": script["title"], "teaching_moves": script["moves"],
                "assessment_item_ids": list(binding["assessments"][0]["item_ids"]) if i == len(SCRIPTS[case_id]) - 1 else []})
        return {"input_fingerprint": inputs["input_fingerprint"], "lesson_id": inputs["lesson_id"], "scenes": scenes, "review_reasons": []}
    scene = payload["scene"]; index = int(scene["scene_id"].split(":")[-1]) - 1; script = SCRIPTS[case_id][index]
    beats = [{"move": move, "text": text, "evidence_ids": evidence, "objective_ids": binding["objective_ids"], "pause_after_ms": 500}
        for move, text in zip(script["moves"], script["text"])]
    question, answer, criteria = ASSESSMENTS[case_id]
    return {"input_fingerprint": inputs["input_fingerprint"], "plan_fingerprint": payload["plan_fingerprint"],
        "scene_id": scene["scene_id"], "beats": beats, "assessments": [
            {"item_id": item, "question": question, "expected_answer": answer, "success_criteria": criteria,
             "evidence_ids": evidence, "response_time_ms": 8000} for item in scene["assessment_item_ids"]], "review_reasons": []}


class DirectorProtocolFixture:
    def __init__(self, transform=None): self.requests = []; self.transform = transform
    def invoke(self, request):
        self.requests.append(request); payload = json.loads(request.messages[1]["content"])
        value = response_record(payload)
        if self.transform: value = self.transform(payload, copy.deepcopy(value), len(self.requests))
        return ModelResponse(GENERATOR.provider, GENERATOR.model, value, {}, "completed", {"test_fixture": True})


def executor(fixture, generator=None, critic=None, **kwargs):
    store = SQLiteIdempotencyStore(str(fixture.root / "idempotency.sqlite"))
    generator = generator or DirectorProtocolFixture(); critic = critic or ProtocolFixtureProvider()
    result = DirectorStageExecutor(fixture.io, store, generator, GENERATOR, critic, IDENTITY, **kwargs)
    return result, generator, critic, store


def context(fixture, **changes):
    return replace(ExecutionContext(fixture.run_id, "DIRECTOR", 1, "fixture-key:" + fixture.case_id,
        [fixture.pedagogy_ref.artifact_id, fixture.reasoning_ref.artifact_id], {"director": fixture.config}), **changes)


from bie.infrastructure.orchestrator import EnterpriseOrchestrator, InMemoryArtifactResolver, StageDefinition
from bie.infrastructure.run_state import build_run_state
from bie.director.director_executor import register_director_stage

def orchestrator(f, execute):
    # Actual upstream artifact-producing functions have already executed. This
    # focused harness records those real outputs; it does not fake full BI/KI.
    state = build_run_state(f.run_id, {"REASONING": [], "PEDAGOGY": ["REASONING"], "DIRECTOR": ["PEDAGOGY", "REASONING"]})
    resolver = InMemoryArtifactResolver()
    for sid, ref, inputs in (("REASONING", f.reasoning_ref, [f.source_ref.artifact_id]),
                            ("PEDAGOGY", f.pedagogy_ref, [f.reasoning_ref.artifact_id])):
        state.mark_ready(sid); state.start(sid, inputs)
        state.succeed(sid, [ref.artifact_id], [ref.artifact_id]); resolver.register_stage_outputs(f.run_id, sid, [ref.artifact_id])
    definitions = {"REASONING": StageDefinition("REASONING", [], ["document.source_catalog"], "reasoning.decision_set", "RE"),
        "PEDAGOGY": StageDefinition("PEDAGOGY", ["REASONING"], ["reasoning.decision_set"], "pedagogy.plan", "PED")}
    definitions, executors = register_director_stage(definitions, {}, execute)
    return EnterpriseOrchestrator(state, definitions, executors, resolver, {"director": f.config})

