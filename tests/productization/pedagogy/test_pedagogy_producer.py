"""Actual native producer/Director boundaries; technical evidence only."""
from copy import deepcopy
import gc
import json
from pathlib import Path
import secrets
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests/productization/document_intelligence"))
from structural_pdf_fixtures import positioned_text_pdf
from apps.operator.contracts import Credentials, Principal
from apps.operator.service import Service
from apps.operator.pedagogy_producer import PedagogyProducerControlPlane
from bie.document_intelligence.real_pdf_text_runtime import inspect_real_pdf_text
from bie.productization.contracts import structured_document, digest, canonical, ProducerError
from bie.productization.candidates import produce
from bie.productization.pr_reasoning import prerequisite_artifact
from bie.productization.math_evidence import binding, math_artifact, reasoning_artifact
from bie.productization.pedagogy_plan import (
    PROFILE, SCHEMA, POLICY, profile_config, pedagogy_components, verify_components,
)
from bie.productization.pedagogy_slice import PedagogyProducerService, STAGES


def pdf(lines=("2 + 3 = 5",)):
    return positioned_text_pdf([[(72, 740 - 40 * i, text) for i, text in enumerate(
        ("Birds requires Flight.",) + tuple(lines))]])


def inputs(lines=()):
    document = structured_document(inspect_real_pdf_text(pdf(lines)), "prod-test-source", "a" * 64)
    knowledge = produce(document, profile_config())[1]
    context = binding("prod-test", document["source_sha256"], "artifact-knowledge", digest(knowledge), 1)
    prerequisite = prerequisite_artifact(knowledge, context)
    math = math_artifact(document, knowledge, prerequisite, context, "artifact-document", "artifact-pr")
    reasoning = reasoning_artifact(knowledge, prerequisite, math, context, "artifact-pr", "artifact-math")
    values = (document, knowledge, prerequisite, math, reasoning)
    ids = dict(document="artifact-document", knowledge="artifact-knowledge", prerequisite="artifact-pr",
               math="artifact-math", reasoning="artifact-reasoning")
    kwargs = dict(run_id="prod-test", source_id="prod-test-source", artifact_ids=ids,
                  artifact_hashes={key: digest(value) for key, value in zip(ids, values)}, attempt=1)
    return values, kwargs, pedagogy_components(*values, **kwargs)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.values, self.kwargs, self.value = inputs()

    def bad(self, edit):
        value = deepcopy(self.value)
        edit(value)
        with self.assertRaises(ProducerError):
            verify_components(value, *self.values, **self.kwargs)

    def test_native_pdf_source_content(self):
        self.assertTrue(any("Birds requires Flight." in b["text"] for b in self.values[0]["blocks"]))

    def test_typed_plan(self):
        self.assertEqual(self.value["schema"], SCHEMA)
        self.assertTrue(self.value["plan"]["requires_review"])

    def test_objectives_bind_actual_concepts(self):
        self.assertEqual({o["concept_id"] for o in self.value["objectives"]}, set(self.values[1]["nodes"]))

    def test_objectives_bind_source_evidence(self):
        anchors = {b["anchor_id"] for b in self.values[0]["blocks"]}
        self.assertTrue(all(o["evidence_ids"] and set(o["evidence_ids"]) <= anchors for o in self.value["objectives"]))

    def test_nonexistent_objective_rejected(self):
        self.bad(lambda c: c["objectives"][0].update(concept_id="invented"))

    def test_invented_evidence_rejected(self):
        self.bad(lambda c: c["objectives"][0].update(evidence_ids=["foreign-anchor"]))

    def test_generic_objective_rejected(self):
        self.bad(lambda c: c["objectives"][0].update(statement="Understand the chapter"))

    def test_prerequisite_aware_order(self):
        order = self.value["teaching_order"]
        for edge in self.values[2]["edges"]:
            self.assertLess(order.index(edge["prerequisite"]), order.index(edge["dependent"]))

    def test_prerequisite_violation_rejected(self):
        self.bad(lambda c: c.update(teaching_order=list(reversed(c["teaching_order"]))))

    def test_source_order_separate(self):
        self.assertIn("source_order", self.value)
        self.assertIn("teaching_order", self.value)
        self.assertEqual(set(self.value["source_order"]), set(self.value["teaching_order"]))
        self.assertTrue(all("source_position" in u for u in self.value["units"]))

    def test_source_change_changes_plan(self):
        _, _, other = inputs(("Flight requires Wings.",))
        self.assertNotEqual(digest(other), digest(self.value))

    def test_prefilled_plan_not_required(self):
        self.assertNotIn("pedagogy", self.values[1])
        self.assertTrue(self.value["objectives"])

    def test_required_math_bound(self):
        values, kwargs, value = inputs(("2 + 3 = 5",))
        self.assertEqual(value["math_applicability"], "REQUIRED")
        self.assertEqual(value["math_requirements"]["sha256"], digest(values[3]))
        self.assertEqual(value["math_requirements"]["artifact_id"], kwargs["artifact_ids"]["math"])
        self.assertTrue(value["math_requirements"]["equation_ids"])

    def test_no_math_instruction_fabricated(self):
        self.assertEqual(self.value["math_applicability"], "NOT_REQUIRED")
        self.assertEqual(self.value["math_requirements"]["equation_ids"], [])
        self.assertTrue(all(not u["math_item_ids"] for u in self.value["units"]))

    def test_math_result_not_rewritten(self):
        before = canonical(self.values[3])
        pedagogy_components(*self.values, **self.kwargs)
        self.assertEqual(before, canonical(self.values[3]))

    def test_uncertainty_retained(self):
        self.assertEqual(canonical(self.value["uncertainty"]), canonical(self.values[4]["uncertainty"]))
        self.assertTrue(self.value["requires_review"])

    def test_certainty_not_promoted(self):
        self.assertLessEqual(max(d["confidence"] for d in self.value["plan"]["decisions"]), .5)
        self.bad(lambda c: c.update(requires_review=False))

    def test_no_unsupported_misconception(self):
        self.assertEqual(self.value["misconception_plans"], [])
        self.assertTrue(all(u["misconception_status"] == "NOT_EVIDENCED" for u in self.value["units"]))

    def test_invented_misconception_rejected(self):
        self.bad(lambda c: c.update(misconception_plans=[{"misconception_id": "fiction"}]))

    def test_mastery_is_planned(self):
        self.assertFalse(self.value["measured_learner_mastery"])
        self.assertTrue(all(u["planned_mastery"] and u["measured_mastery"] is None for u in self.value["units"]))

    def test_fabricated_mastery_rejected(self):
        self.bad(lambda c: c["units"][0].update(measured_mastery=.9))

    def test_no_learner_observations(self):
        self.assertIsNone(self.value["learner_state"])
        self.assertTrue(all(u["learner_state"] == "NOT_SUPPLIED" for u in self.value["units"]))

    def test_fabricated_learner_rejected(self):
        self.bad(lambda c: c.update(learner_state={"past_attempts": 3}))

    def test_load_is_bounded_technical_policy(self):
        self.assertTrue(all(not u["cognitive_load"]["overload"] for u in self.value["units"]))
        self.assertTrue(all(u["load_policy"] == "TECHNICAL_DECLARED_UNIT_GUARDRAIL" for u in self.value["units"]))

    def test_assessment_obligations_not_outcomes(self):
        self.assertTrue(all(r["planned"] and not r["measured"] for r in self.value["formative_requirements"]))
        self.assertTrue(all(not r["counts_as_mastery"] for r in self.value["retrieval_requirements"]))

    def test_deterministic_same_inputs(self):
        self.assertEqual(canonical(self.value), canonical(pedagogy_components(*self.values, **self.kwargs)))

    def test_foreign_reasoning(self):
        values = list(deepcopy(self.values)); values[4]["run_id"] = "foreign"
        kwargs = deepcopy(self.kwargs); kwargs["artifact_hashes"]["reasoning"] = digest(values[4])
        with self.assertRaises(ProducerError): pedagogy_components(*values, **kwargs)

    def test_foreign_math(self):
        values = list(deepcopy(self.values)); values[3]["run_id"] = "foreign"
        kwargs = deepcopy(self.kwargs); kwargs["artifact_hashes"]["math"] = digest(values[3])
        with self.assertRaises(ProducerError): pedagogy_components(*values, **kwargs)

    def test_foreign_knowledge_identity(self):
        kwargs = deepcopy(self.kwargs); kwargs["artifact_ids"]["knowledge"] = "foreign"
        with self.assertRaises(ProducerError): pedagogy_components(*self.values, **kwargs)

    def test_tampered_reasoning(self):
        values = list(deepcopy(self.values)); values[4]["decisions"][0]["selected_option"] = "fiction"
        kwargs = deepcopy(self.kwargs); kwargs["artifact_hashes"]["reasoning"] = digest(values[4])
        with self.assertRaises(ProducerError): pedagogy_components(*values, **kwargs)

    def test_foreign_source(self):
        kwargs = dict(self.kwargs, source_id="foreign-source")
        with self.assertRaises(ProducerError): pedagogy_components(*self.values, **kwargs)

    def test_unknown_field_rejected(self):
        self.bad(lambda c: c.update(script="spoken script"))

    def test_bounded_scope_not_course(self):
        self.assertEqual(len(self.value["plan"]["lesson_ids"]), 1)
        self.assertEqual(self.value["scope"], "RUN_BOUNDED_INSTRUCTIONAL_UNITS")

    def test_source_lineage_each_unit(self):
        self.assertTrue(all(l["reasoning_parent_ids"] == [self.kwargs["artifact_ids"]["reasoning"]]
                            and l["math_parent_ids"] == [self.kwargs["artifact_ids"]["math"]]
                            for l in self.value["lineages"]))


class ProfileTests(unittest.TestCase):
    def test_task032_native_uuid_identity_is_deterministic(self):
        from bie.productization.pedagogy_slice import run_identity, run_identity_valid
        value = run_identity("local", "intent")
        self.assertTrue(run_identity_valid(value))
        self.assertEqual(value, run_identity("local", "intent"))
        self.assertNotEqual(value, run_identity("local", "revision"))
        self.assertNotEqual(value, run_identity("other", "intent"))

    def test_task032_identity_cannot_accept_legacy_run(self):
        from bie.productization.pedagogy_slice import run_identity_valid
        for value in ("prod-existing", "not-a-uuid", None):
            self.assertFalse(run_identity_valid(value))

    def test_legacy_identity_policy_is_not_migrated(self):
        from bie.productization.durable_slice import KnowledgeProducerService
        from bie.productization.reasoning_slice import ReasoningProducerService
        from bie.productization.math_slice import MathProducerService
        for service in (KnowledgeProducerService, ReasoningProducerService, MathProducerService):
            value = service.identity_for("local", "intent")
            self.assertTrue(value.startswith("prod-"))
            self.assertTrue(service.run_identity_valid(value))

    def test_legacy_three_stage_scope(self):
        from bie.productization.durable_slice import STAGES as old
        self.assertEqual(old, ("SOURCE", "DOCUMENT_INTELLIGENCE", "KNOWLEDGE"))

    def test_legacy_five_stage_scope(self):
        from bie.productization.reasoning_slice import STAGES as old
        self.assertEqual(len(old), 5); self.assertNotIn("MATH", old); self.assertNotIn("PEDAGOGY", old)

    def test_legacy_six_stage_scope(self):
        from bie.productization.math_slice import STAGES as old
        self.assertEqual(len(old), 6); self.assertNotIn("PEDAGOGY", old)

    def test_seven_stage_scope(self):
        self.assertEqual(STAGES, ("SOURCE", "DOCUMENT_INTELLIGENCE", "KNOWLEDGE", "PREREQUISITE", "MATH", "REASONING", "PEDAGOGY"))

    def test_graph_contract_unchanged(self):
        g = PedagogyProducerService.graph_for()
        self.assertEqual(g.stages["PEDAGOGY"].consumes, ["reasoning.decision_set"])
        self.assertEqual(g.stages["PEDAGOGY"].required_predecessors, ["REASONING"])

    def test_audio_remains_open(self):
        self.assertNotIn("AUDIO", PedagogyProducerService.graph_for().stages)

    def test_worker_capability_isolation(self):
        from bie.productization.math_slice import MathProducerService
        from bie.productization.durable_slice import CAPABILITY
        self.assertNotIn(PedagogyProducerService.capability, (CAPABILITY, MathProducerService.capability, "pdf.inspect"))


class DurableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.credentials = Credentials(); self.token = secrets.token_urlsafe(40)
        self.p = Principal("test", "local", frozenset({"read", "source", "create", "worker", "control", "admin_recover"}), time.time()+900)
        self.credentials.grant(self.token, self.p)
        self.operator = Service(self.root, self.credentials)
        self.port = PedagogyProducerControlPlane(self.operator, enabled_profiles={PROFILE})
        self.source = self.operator.import_pdf(self.p, pdf())
        self.run = self.port.admit(self.p, self.source["source_id"], "intent")["run_id"]

    def tearDown(self):
        gc.collect(); self.tmp.cleanup()

    def complete(self):
        result = None
        for _ in STAGES: result = self.port.work_once(self.p, self.run)
        return result

    def test_seven_stage_success(self):
        self.assertEqual(self.complete()["stages"], {s: "SUCCEEDED" for s in STAGES})

    def test_reasoning_success_not_slice_completion(self):
        for _ in range(6): r = self.port.work_once(self.p, self.run)
        self.assertEqual(r["stages"]["PEDAGOGY"], "READY"); self.assertFalse(r["slice_complete"])

    def test_pedagogy_not_admitted_early(self):
        self.assertEqual(self.port.status(self.p, self.run)["stages"]["PEDAGOGY"], "PENDING")

    def test_exact_director_input_compatibility(self):
        self.complete()
        with self.port.native(self.p, self.run, "read") as n:
            actual = n.director_inputs(self.run, "local")
            self.assertTrue(actual.objectives); self.assertTrue(actual.review_reasons)
            self.assertEqual(len(actual.reasoning), 2)

    def test_director_not_executed(self):
        r = self.complete(); self.assertEqual(r["downstream"]["DIRECTOR"], "NOT_RUN")
        with self.port.native(self.p, self.run, "read") as n:
            self.assertNotIn("DIRECTOR", n.persistence.load_run_state(self.run)["stages"])

    def test_downstream_visual_not_run(self):
        self.assertTrue(all(v == "NOT_RUN" for v in self.complete()["downstream"].values()))

    def test_ack_after_verified_persistence(self):
        self.complete()
        with self.port.native(self.p, self.run, "read") as n:
            self.assertEqual(n.queue.stats()["ACKED"], 7)

    def test_safe_status_no_text(self):
        raw = json.dumps(self.complete())
        for secret in ("Birds", "Flight", "2 + 3", str(self.root), self.token): self.assertNotIn(secret, raw)

    def test_private_native_text_is_persisted(self):
        self.complete()
        with self.port.native(self.p, self.run, "read") as n:
            _, _, value, c, actual = n.verified_pedagogy(self.run, "local")
            self.assertIn("Birds", canonical(value).decode())
            self.assertTrue(actual.sources)

    def test_safe_evidence_no_source(self):
        self.complete()
        with self.port.native(self.p, self.run, "read") as n:
            for ref in n.persistence.evidence_for_run(self.run):
                raw = canonical(n.read(self.run, ref)).decode()
                for secret in ("Birds", "2 + 3", str(self.root), self.token): self.assertNotIn(secret, raw)

    def test_same_intent_replay(self):
        r = self.complete(); self.assertEqual(self.port.admit(self.p, self.source["source_id"], "intent"), r)

    def test_conflicting_intent(self):
        other = self.operator.import_pdf(self.p, pdf(("3 + 4 = 7",)))
        with self.assertRaises(Exception): self.port.admit(self.p, other["source_id"], "intent")

    def test_restart_identity(self):
        r = self.complete()
        other = PedagogyProducerControlPlane(Service(self.root, self.credentials), enabled_profiles={PROFILE})
        self.assertEqual(other.status(self.p, self.run), r)

    def test_pedagogy_cas_tamper(self):
        r = self.complete(); self.operator.cas._path(r["pedagogy"]["sha256"]).write_bytes(b"tamper")
        with self.assertRaises(Exception): self.port.status(self.p, self.run)

    def test_foreign_pedagogy_record(self):
        r = self.complete()
        with self.port.native(self.p, self.run, "read") as n:
            with n.persistence._conn() as db:
                db.execute("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?", (r["pedagogy"]["artifact_id"],))
            with self.assertRaises(Exception): n.status(self.run, "local")

    def test_reasoning_tamper_prevents_pedagogy(self):
        for _ in range(6): r = self.port.work_once(self.p, self.run)
        self.operator.cas._path(r["reasoning"]["sha256"]).write_bytes(b"tamper")
        with self.assertRaises(Exception): self.port.work_once(self.p, self.run)

    def test_provider_unavailable_blocks_upstream(self):
        run = self.port.admit(self.p, self.source["source_id"], "unavailable", provider="missing", model="missing")["run_id"]
        for _ in range(3): r = self.port.work_once(self.p, run)
        self.assertEqual(r["stages"]["KNOWLEDGE"], "BLOCKED")
        self.assertEqual(r["stages"]["PEDAGOGY"], "PENDING")

    def test_malformed_candidate_fails_closed(self):
        for _ in range(6): self.port.work_once(self.p, self.run)
        with patch("bie.productization.pedagogy_slice.pedagogy_components", return_value={"schema": "foreign"}):
            r = self.port.work_once(self.p, self.run)
        self.assertEqual(r["stages"]["PEDAGOGY"], "FAILED")
        self.assertEqual(r["safe_diagnostics"]["PEDAGOGY"], ["invalid_pedagogy_candidate"])

    def test_unsupported_math_cannot_reach_pedagogy(self):
        src = self.operator.import_pdf(self.p, pdf(("Compute the matrix inverse.",)))
        run = self.port.admit(self.p, src["source_id"], "unsupported")["run_id"]
        for _ in range(7): r = self.port.work_once(self.p, run)
        self.assertEqual(r["stages"]["MATH"], "BLOCKED")
        self.assertEqual(r["stages"]["PEDAGOGY"], "PENDING")
        self.assertIsNone(r["pedagogy"])

    def test_no_math_explicit_pedagogy(self):
        src = self.operator.import_pdf(self.p, pdf(()))
        run = self.port.admit(self.p, src["source_id"], "no-math")["run_id"]
        for _ in range(7): r = self.port.work_once(self.p, run)
        self.assertTrue(r["slice_complete"]); self.assertEqual(r["math"]["applicability"], "NOT_REQUIRED")

    def test_control_remains_fail_closed(self):
        with self.assertRaisesRegex(ProducerError, "producer_control_not_supported"):
            self.port.control(self.p, self.run, "pause")

    def test_foreign_tenant_denied(self):
        with self.port.native(self.p, self.run, "read") as n:
            with self.assertRaises(ProducerError): n.status(self.run, "foreign")

    def test_queue_isolation_real_poll(self):
        with self.port.native(self.p, self.run, "read") as n:
            self.assertIsNone(n.queue.poll("legacy", capability_tags=["pdf.inspect"]))
            self.assertIsNone(n.queue.poll("old", capability_tags=["producer:source_grounded_di_knowledge_v1"]))


class RealProcessTests(unittest.TestCase):
    def test_native_seven_stage_restart_and_director_compatibility(self):
        from scripts.smoke_bie_pedagogy import run_smoke
        result = run_smoke()
        self.assertTrue(result["passed"])
        for label in ("supported_math", "non_math"):
            self.assertTrue(result[label]["restart_in_second_process"])
            self.assertTrue(result[label]["director_input_compatibility"])
            self.assertFalse(result[label]["director_executed"])


if __name__ == "__main__": unittest.main()
