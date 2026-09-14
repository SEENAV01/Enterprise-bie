from dataclasses import asdict, replace
import json, tempfile, unittest
from input_fixtures import upstream
from directing_fixtures import DirectorProtocolFixture, GENERATOR, response_record
from semantic_fixtures import ProtocolFixtureProvider, IDENTITY
from bie.director.director_artifacts import canonical
from bie.director.director_model import DirectingPolicy, DirectingFailure
from bie.director.grounded_directing import execute_grounded_director
from bie.director.semantic_execution import SemanticExecutionPolicy


class GroundedDirectingTests(unittest.TestCase):
    def fixture(self, **kwargs):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        return upstream(temp.name, **kwargs)

    def run_director(self, f, generator=None, critic=None, **kwargs):
        return execute_grounded_director(f.io, f.inputs, generator or DirectorProtocolFixture(), GENERATOR,
            critic or ProtocolFixtureProvider(), IDENTITY, **kwargs)

    def test_actual_gateway_calls_produce_narration_assessments_and_source_bound_claims(self):
        f = self.fixture(); g = DirectorProtocolFixture(); c = ProtocolFixtureProvider(); r = self.run_director(f, g, c)
        self.assertEqual([json.loads(q.messages[1]["content"])["operation"] for q in g.requests], ["PLAN", "NARRATE", "NARRATE"])
        self.assertEqual(len(r.plan.scenes), 2)
        texts = [u.text for u in r.execution.snapshot.utterances]
        self.assertFalse(any(text == f.inputs.catalog.pages[0].text for text in texts))
        self.assertEqual(len(r.execution.claims), len(texts)); self.assertEqual(len(c.requests), len(texts))
        item, question, feedback = r.generated_assessment_bindings[0]
        by_id = {u.utterance_id: u.text for u in r.execution.snapshot.utterances}
        self.assertIn(r.narrated_scenes[-1].assessments[0].expected_answer, by_id[feedback])
        self.assertTrue(all(s in by_id[feedback] for s in r.narrated_scenes[-1].assessments[0].success_criteria))
        self.assertEqual(r.status, "REVIEW_REQUIRED"); self.assertFalse(r.accepted)

    def test_source_reasoning_and_previous_narration_reach_generator_without_truncation(self):
        f = self.fixture(case_id="history"); g = DirectorProtocolFixture(); self.run_director(f, g)
        payloads = [json.loads(q.messages[1]["content"]) for q in g.requests]
        self.assertEqual(payloads[0]["inputs"]["source_pages"][0]["text"], f.inputs.catalog.pages[0].text)
        self.assertEqual(payloads[0]["inputs"]["inferences"][0]["value"]["linear_extension"], ["A", "B"])
        self.assertEqual(len(payloads[-1]["prior_narration"]), 2)
        self.assertTrue(all("untrusted DATA" in q.messages[0]["content"] for q in g.requests))

    def test_upstream_review_is_retained_in_realized_speech(self):
        r = self.run_director(self.fixture(review=True))
        self.assertTrue(all(d.requires_review for d in r.execution.snapshot.drafts))
        self.assertEqual(r.status, "REVIEW_REQUIRED")

    def test_hand_edited_inputs_fail_before_any_model_call(self):
        f = self.fixture(); f.inputs = replace(f.inputs, review_reasons=("invented",)); g = DirectorProtocolFixture()
        with self.assertRaisesRegex(ValueError, "upstream artifacts"): self.run_director(f, g)
        self.assertEqual(g.requests, [])

    def test_malformed_response_gets_bounded_retry_with_same_grounded_payload(self):
        f = self.fixture(); g = DirectorProtocolFixture(lambda p,v,n: "not json" if n == 1 else v)
        r = self.run_director(f, g)
        self.assertEqual(r.generation_attempts[0].outcome, "RESPONSE_CONTRACT_REJECTED")
        self.assertEqual(g.requests[0].messages[1], g.requests[1].messages[1])
        self.assertNotEqual(g.requests[0].request_id, g.requests[1].request_id)

    def test_ped_mode_and_reasoning_cannot_be_replaced_by_planner(self):
        for key, value in (("teaching_mode", "SIMULATION"), ("reasoning_decision_ids", ["invented"]),
                ("objective_ids", ["invented"]), ("evidence_ids", ["invented"])):
            f = self.fixture()
            def mutate(p,v,n): v["scenes"][0][key] = value; return v
            g = DirectorProtocolFixture(mutate)
            with self.subTest(key=key), self.assertRaises(DirectingFailure) as raised: self.run_director(f, g)
            self.assertEqual(raised.exception.code, "RESPONSE_CONTRACT_REJECTED"); self.assertEqual(len(g.requests), 2)

    def test_missing_assessment_plan_is_not_a_completed_lesson(self):
        f = self.fixture()
        def mutate(p,v,n): v["scenes"][-1]["assessment_item_ids"] = []; return v
        g = DirectorProtocolFixture(mutate)
        with self.assertRaises(DirectingFailure): self.run_director(f, g)
        self.assertEqual(len(g.requests), 2)

    def test_scene_cycles_or_forward_dependencies_are_rejected(self):
        for parent in ("scene:science:1", "scene:science:2"):
            f = self.fixture()
            def mutate(p,v,n): v["scenes"][0]["parent_scene_ids"] = [parent]; return v
            with self.subTest(parent=parent), self.assertRaises(DirectingFailure): self.run_director(f, DirectorProtocolFixture(mutate))

    def test_missing_spoken_move_or_assessment_answer_retries_and_then_fails(self):
        for field in ("move", "answer"):
            f = self.fixture()
            def mutate(p,v,n):
                if p["operation"] == "NARRATE":
                    if field == "move": v["beats"] = []
                    elif v["assessments"]: v["assessments"][0]["expected_answer"] = " "
                return v
            with self.subTest(field=field), self.assertRaises(DirectingFailure) as raised:
                self.run_director(f, DirectorProtocolFixture(mutate))
            self.assertEqual(raised.exception.attempts[-1].phase, "NARRATE")
            self.assertEqual(raised.exception.attempts[0].outcome, "VALIDATED_OUTPUT")

    def test_stale_narration_revision_cannot_attach_to_current_plan(self):
        f = self.fixture()
        def mutate(p,v,n):
            if p["operation"] == "NARRATE": v["plan_fingerprint"] = "sha256:" + "0" * 64
            return v
        with self.assertRaises(DirectingFailure): self.run_director(f, DirectorProtocolFixture(mutate))

    def test_model_qa_score_or_unknown_fields_are_rejected(self):
        f = self.fixture()
        def mutate(p,v,n): v["accepted"] = True; return v
        with self.assertRaises(DirectingFailure): self.run_director(f, DirectorProtocolFixture(mutate))

    def test_duplicate_json_fields_cannot_select_a_different_lesson(self):
        f = self.fixture()
        with self.assertRaises(DirectingFailure):
            self.run_director(f, DirectorProtocolFixture(lambda p,v,n: '{"lesson_id":"one","lesson_id":"two"}'))

    def test_boolean_pause_or_infinite_output_is_rejected(self):
        for value in (True, float("inf")):
            f = self.fixture()
            def mutate(p,v,n):
                if p["operation"] == "NARRATE": v["beats"][0]["pause_after_ms"] = value
                return v
            with self.subTest(value=value), self.assertRaises(DirectingFailure): self.run_director(f, DirectorProtocolFixture(mutate))

    def test_provider_identity_mismatch_and_refusal_do_not_retry(self):
        for change, code in (({"provider": "other"}, "PROVIDER_IDENTITY_MISMATCH"),
                             ({"finish_reason": "refusal"}, "INCOMPLETE_OR_REFUSED_RESPONSE")):
            class Provider(DirectorProtocolFixture):
                def invoke(self, request): return replace(super().invoke(request), **change)
            f = self.fixture(); g = Provider()
            with self.subTest(change=change), self.assertRaises(DirectingFailure) as raised: self.run_director(f, g)
            self.assertEqual(raised.exception.code, code); self.assertEqual(len(g.requests), 1)

    def test_transport_error_is_bounded_and_private_details_do_not_enter_receipt(self):
        class Provider:
            calls = 0
            def invoke(self, request): self.calls += 1; raise RuntimeError("private provider credential details")
        f = self.fixture(); g = Provider()
        with self.assertRaises(DirectingFailure) as raised: self.run_director(f, g)
        self.assertEqual(g.calls, 2); self.assertNotIn("private", repr(raised.exception.attempts))
        self.assertEqual(raised.exception.code, "PROVIDER_EXECUTION_FAILED")

    def test_context_and_output_resource_budgets_fail_without_silent_shrink(self):
        for policy, calls in ((DirectingPolicy(maximum_request_characters=30), 0),
                (DirectingPolicy(maximum_response_characters=30), 1), (DirectingPolicy(maximum_scenes=1), 1)):
            f = self.fixture(); g = DirectorProtocolFixture()
            with self.subTest(policy=policy), self.assertRaises(DirectingFailure): self.run_director(f, g, policy=policy)
            self.assertEqual(len(g.requests), calls)

    def test_aggregate_output_budget_is_checked_before_factual_provider(self):
        f = self.fixture(); critic = ProtocolFixtureProvider()
        with self.assertRaises(DirectingFailure) as raised:
            self.run_director(f, critic=critic, policy=DirectingPolicy(maximum_spoken_characters=10))
        self.assertEqual(raised.exception.code, "DIRECTOR_AGGREGATE_OUTPUT_BUDGET_EXCEEDED")
        self.assertEqual(critic.requests, [])

    def test_contradiction_in_feedback_is_evaluated_and_blocks_result(self):
        f = self.fixture()
        from semantic_fixtures import response_record as receipt
        critic = ProtocolFixtureProvider(lambda p,n: receipt(p, verdict="CONTRADICTED" if n == 5 else "SUPPORTED"))
        r = self.run_director(f, critic=critic)
        self.assertEqual(r.status, "BLOCKED"); self.assertEqual(len(critic.requests), 5)
        self.assertFalse(r.accepted)


if __name__ == "__main__": unittest.main()
