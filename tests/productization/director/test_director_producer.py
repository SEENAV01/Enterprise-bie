"""Task033 actual native production controls; synthetic protocol evidence only."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, replace
import gc
import json
from pathlib import Path
import secrets
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests/productization/document_intelligence"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from structural_pdf_fixtures import positioned_text_pdf
from protocol_support import make_stack
from apps.operator.contracts import Credentials, Principal, OperatorError
from apps.operator.service import Service
from apps.operator.director_producer import DirectorProducerControlPlane
from bie.bie_core.artifact_contracts import ArtifactRef
from bie.director.director_model import DirectingPolicy
from bie.director.director_artifacts import envelope_from_dict, reference
from bie.director.production_adoption import DirectorProductionAssembly
from bie.infrastructure.artifact_store import BlobRef
from bie.model_gateway.model_interface import ModelResponse
from bie.productization.contracts import ProducerError, canonical, digest, strict_json
from bie.productization.director_contract import (
    PROFILE, SCHEMA, POLICY, director_config, profile_config, run_identity,
)
from bie.productization.director_slice import DirectorProducerService, STAGES
from bie.productization.director_storage import native_runtime


def pdf(lines=("2 + 3 = 5",)):
    return positioned_text_pdf([[(72, 740 - 40 * i, text) for i, text in enumerate(
        ("Birds requires Flight.",) + tuple(lines))]])


def settings(stack=None, **changes):
    stack = stack or make_stack()
    values = dict(title="Governed source exercise", language="en", providers=stack.descriptor(),
                  evidence_kind=stack.evidence_kind)
    values.update(changes)
    return director_config(**values)


def decoded_strings(value):
    """Inspect decoded values so JSON escaping cannot conceal a path leak."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, cell in value.items():
            yield from decoded_strings(key)
            yield from decoded_strings(cell)
    elif isinstance(value, (list, tuple)):
        for cell in value:
            yield from decoded_strings(cell)


class ProducerFixture(unittest.TestCase):
    """Shared genuine PDF/CAS/SQLite fixture, also used by recovery tests."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        prepared = getattr(type(self), "_prepared", None)
        if prepared is not None:
            # Only negative-control classes reuse this verified predecessor
            # snapshot. Each test gets independent actual SQLite/CAS files;
            # native runtime handles were closed before snapshot publication.
            shutil.copytree(prepared.root, self.root, dirs_exist_ok=True)
        self.credentials = Credentials()
        self.token = secrets.token_urlsafe(40)
        self.p = Principal("task033-test", "local", frozenset({
            "read", "source", "create", "worker", "control", "admin_recover"}), time.time() + 900)
        self.credentials.grant(self.token, self.p)
        self.operator = Service(self.root, self.credentials)
        self.stack = make_stack()
        self.config = profile_config(director=settings(self.stack))
        self.port = DirectorProducerControlPlane(self.operator, enabled_profiles={PROFILE})
        if prepared is None:
            self.source = self.operator.import_pdf(self.p, pdf())
            self.run = self.port.admit(self.p, self.source["source_id"], "intent",
                                       producer_config=self.config)["run_id"]
        else:
            self.source = self.operator.source(self.p, prepared.source["source_id"])
            self.run = prepared.run

    def tearDown(self):
        gc.collect()
        self.tmp.cleanup()

    def step(self, run=None, stack=True, **options):
        if stack:
            options["director_stack"] = self.stack
        return self.port.work_once(self.p, run or self.run, **options)

    def until_director(self, run=None):
        current = self.port.status(self.p, run or self.run)
        if current["stages"]["DIRECTOR"] == "READY":
            self.assertEqual(current["stages"]["PEDAGOGY"], "SUCCEEDED")
            return current
        for _ in STAGES[:-1]:
            result = self.step(run)
        self.assertEqual(result["stages"]["PEDAGOGY"], "SUCCEEDED")
        self.assertEqual(result["stages"]["DIRECTOR"], "READY")
        return result

    def complete(self, run=None):
        for _ in STAGES:
            result = self.step(run)
            if result["slice_complete"] or any(
                    value in ("BLOCKED", "FAILED") for value in result["stages"].values()):
                break
        return result

    def admit_other(self, lines, key="other", config=None):
        source = self.operator.import_pdf(self.p, pdf(lines))
        run = self.port.admit(self.p, source["source_id"], key,
                             producer_config=config or self.config)["run_id"]
        return run

    def failed(self, result, code=None):
        self.assertIn(result["stages"]["DIRECTOR"], ("BLOCKED", "FAILED"))
        self.assertFalse(result["slice_complete"])
        self.assertIsNone(result["director"])
        if code:
            self.assertIn(code, result["safe_diagnostics"]["DIRECTOR"])
        self.assertTrue(all(state == "NOT_RUN" for state in result["downstream"].values()))

    def native_result(self):
        with self.port.native(self.p, self.run, "read") as native:
            output, receipt = native.verified_director(self.run, "local")
            return output, receipt

    def budget(self, **changes):
        policy = replace(DirectingPolicy(), **changes)
        @contextmanager
        def lowered(service, run, stack, **options):
            with native_runtime(service, run, stack, policy=policy, **options) as assembly:
                yield assembly
        return patch("bie.productization.director_slice.native_runtime", lowered)

    def tamper_stage(self, stage):
        with self.port.native(self.p, self.run, "read") as native:
            aid, row = native.stage_ref(self.run, stage)
            native.cas._path(row.blob_digest).write_bytes(b"deliberate-cas-tamper")
            return aid


class PreparedProducerFixture(ProducerFixture):
    """Persisted upstream fixture, not mocked stages or generated test results."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        fixture = ProducerFixture()
        fixture.setUp()
        try:
            fixture.until_director()
        except BaseException:
            fixture.tearDown()
            raise
        cls._prepared = fixture
        cls.addClassCleanup(fixture.tearDown)


class ProfileAndConfigurationTests(unittest.TestCase):
    def test_eight_stage_scope(self):
        self.assertEqual(STAGES, ("SOURCE", "DOCUMENT_INTELLIGENCE", "KNOWLEDGE", "PREREQUISITE",
                                  "MATH", "REASONING", "PEDAGOGY", "DIRECTOR"))

    def test_task029_scope_is_still_three(self):
        from bie.productization.durable_slice import STAGES as legacy
        self.assertEqual(legacy, STAGES[:3])

    def test_task030_scope_is_still_five(self):
        from bie.productization.reasoning_slice import STAGES as legacy
        self.assertEqual(legacy, ("SOURCE", "DOCUMENT_INTELLIGENCE", "KNOWLEDGE", "PREREQUISITE", "REASONING"))

    def test_task031_scope_is_still_six(self):
        from bie.productization.math_slice import STAGES as legacy
        self.assertEqual(legacy, STAGES[:6])

    def test_task032_scope_is_still_seven(self):
        from bie.productization.pedagogy_slice import STAGES as legacy
        self.assertEqual(legacy, STAGES[:7])

    def test_existing_graph_contract_not_redesigned(self):
        contract = DirectorProducerService.graph_for().stages["DIRECTOR"]
        self.assertEqual(set(contract.required_predecessors), {"PEDAGOGY", "REASONING"})
        self.assertEqual(set(contract.consumes), {"pedagogy.plan", "reasoning.decision_set"})
        self.assertEqual(contract.emits, "director.plan")

    def test_audio_remains_unreconciled(self):
        self.assertNotIn("AUDIO", DirectorProducerService.graph_for().stages)

    def test_new_profile_identity_is_deterministic_and_distinct(self):
        from bie.productization.pedagogy_slice import run_identity as old
        self.assertEqual(run_identity("local", "intent"), run_identity("local", "intent"))
        self.assertNotEqual(run_identity("local", "intent"), old("local", "intent"))
        self.assertNotEqual(run_identity("local", "intent"), run_identity("foreign", "intent"))

    def test_title_is_explicit_not_defaulted(self):
        for title in ("", " ", " padded ", None, "x" * 257):
            with self.subTest(title_type=type(title).__name__), self.assertRaises(ProducerError):
                settings(title=title)

    def test_language_is_explicit_not_defaulted(self):
        for language in ("", "English", "en/path", None):
            with self.subTest(language=language), self.assertRaises(ProducerError):
                settings(language=language)

    def test_missing_director_configuration_fails_closed(self):
        with self.assertRaisesRegex(ProducerError, "director_configuration_required"):
            profile_config()

    def test_native_budgets_are_preserved(self):
        value = settings()
        self.assertEqual(value["directing_policy"], asdict(DirectingPolicy()))
        self.assertEqual(value["directing_policy"]["maximum_attempts"], 2)
        self.assertEqual(value["directing_policy"]["maximum_stage_attempts"], 3)

    def test_policy_cannot_be_widened_in_intent(self):
        value = settings()
        value["directing_policy"]["maximum_scenes"] += 1
        with self.assertRaisesRegex(ProducerError, "director_policy_conflict"):
            profile_config(director=value)

    def test_foreign_provider_role_rejected(self):
        value = settings()
        value["providers"]["extra"] = value["providers"]["critic"]
        with self.assertRaises(ProducerError):
            profile_config(director=value)

    def test_provider_identities_do_not_require_a_vendor(self):
        providers = {role: dict(provider="configured-neutral", model=role, adapter_version="adapter/1")
                     for role in ("generator", "critic", "annotator", "reviewer")}
        value = settings(providers=providers, evidence_kind="CONFIGURED_PROVIDER_UNACCEPTED")
        self.assertEqual(value["providers"], providers)

    def test_revision_cannot_implicitly_reuse_first_key(self):
        for revision in (0, 4, True):
            with self.subTest(revision=revision), self.assertRaises(ProducerError):
                settings(revision=revision)
        with self.assertRaises(ProducerError):
            settings(revision=2)

    def test_revision_intent_has_new_identity(self):
        from bie.productization.director_contract import native_key
        ref = ArtifactRef("reasoning.decision_set:" + "a" * 64, "reasoning.decision_set", "1.0.0", "sha256:" + "a" * 64)
        ped = ArtifactRef("pedagogy.plan:" + "b" * 64, "pedagogy.plan", "1.0.0", "sha256:" + "b" * 64)
        old = settings()
        revised = settings(revision=2, previous_key="prior-director-key")
        self.assertNotEqual(native_key("run", ref, ped, old), native_key("run", ref, ped, revised))

    def test_annotation_reviewer_requires_distinct_model_identity(self):
        stack = make_stack()
        stack.annotations = replace(stack.annotations,
            reviewer_identity=stack.annotations.annotator_identity)
        with self.assertRaises(ValueError):
            stack.descriptor()


class DurableDirectorTests(ProducerFixture):
    def test_real_source_eight_stage_success(self):
        result = self.complete()
        self.assertEqual(result["stages"], {s: "SUCCEEDED" for s in STAGES})
        self.assertTrue(result["slice_complete"])

    def test_pedagogy_success_does_not_complete_director_slice(self):
        result = self.until_director()
        self.assertFalse(result["slice_complete"])
        self.assertEqual(self.stack.calls, {"generator": 0, "critic": 0, "annotator": 0, "reviewer": 0})

    def test_director_admission_waits_for_verified_reasoning_and_pedagogy(self):
        self.assertEqual(self.port.status(self.p, self.run)["stages"]["DIRECTOR"], "PENDING")
        for _ in STAGES[:6]:
            result = self.step()
        self.assertEqual(result["stages"]["DIRECTOR"], "PENDING")
        self.assertFalse(self.stack.generator.requests)

    def test_exact_persisted_native_inputs_are_consumed(self):
        self.until_director()
        with self.port.native(self.p, self.run, "read") as native:
            request, _, _ = native.request(self.run, "local")
            ped_before = native.read(self.run, request.pedagogy_ref.artifact_id)
            re_before = native.read(self.run, request.reasoning_ref.artifact_id)
        result = self.step()
        self.assertEqual(result["stages"]["DIRECTOR"], "SUCCEEDED")
        output, receipt = self.native_result()
        self.assertEqual(receipt["native_reasoning_ref"], asdict(request.reasoning_ref))
        self.assertEqual(receipt["native_pedagogy_ref"], asdict(request.pedagogy_ref))
        self.assertIn(request.pedagogy_ref, output.parent_refs)
        self.assertIn(request.reasoning_ref, output.parent_refs)
        with self.port.native(self.p, self.run, "read") as native:
            self.assertEqual(native.read(self.run, request.pedagogy_ref.artifact_id), ped_before)
            self.assertEqual(native.read(self.run, request.reasoning_ref.artifact_id), re_before)

    def test_native_annotated_schema_not_parallel_schema(self):
        self.complete()
        output, _ = self.native_result()
        self.assertEqual(output.artifact_type, "director.plan")
        self.assertEqual(output.schema_version, "1.0.0")
        self.assertEqual(output.payload["schema_version"], SCHEMA)

    def test_review_only_component_cannot_claim_acceptance(self):
        self.complete()
        output, receipt = self.native_result()
        for row in (output.metadata, receipt):
            self.assertTrue(row["requires_review"])
            self.assertFalse(row["accepted"])
            self.assertFalse(row["release_ready"])
        self.assertFalse(receipt["product_accepted"])

    def test_metadata_from_exact_plan_and_governed_configuration(self):
        self.complete()
        with self.port.native(self.p, self.run, "read") as native:
            request, components, _ = native.request(self.run, "local")
        self.assertEqual(request.lesson_id, components["plan"]["lesson_ids"][0])
        self.assertEqual(request.title, self.config["director"]["title"])
        self.assertEqual(request.language, self.config["director"]["language"])
        self.assertEqual(self.stack.generator.requests[0].messages[0]["role"], "system")

    def test_generator_and_critic_native_calls_execute(self):
        self.complete()
        self.assertGreater(self.stack.calls["generator"], 1)
        self.assertGreater(self.stack.calls["critic"], 0)
        operations = [json.loads(r.messages[1]["content"]).get("operation") for r in self.stack.generator.requests]
        self.assertIn("PLAN", operations)
        self.assertIn("NARRATE", operations)
        self.assertTrue(all(r.temperature == 0 for r in self.stack.generator.requests + self.stack.critic.requests))

    def test_configured_protocol_transport_does_not_prove_live_model_execution(self):
        # A configured provider interface can still be a local protocol double.
        # Its actual invocations cannot establish live transport/model quality.
        self.stack.evidence_kind = "CONFIGURED_PROVIDER_UNACCEPTED"
        configured = profile_config(director=settings(self.stack))
        run = self.port.admit(self.p, self.source["source_id"], "configured-runtime",
                              producer_config=configured)["run_id"]
        result = self.complete(run)
        self.assertEqual(result["stages"]["DIRECTOR"], "SUCCEEDED")
        self.assertTrue(result["configured_provider_invoked"])
        self.assertIsNone(result["live_provider_executed"])
        self.assertGreater(self.stack.calls["generator"], 1)
        self.assertGreater(self.stack.calls["critic"], 0)
        with self.port.native(self.p, run, "read") as native:
            _, receipt = native.verified_director(run, "local")
        self.assertTrue(receipt["configured_provider_invoked"])
        self.assertIsNone(receipt["live_provider_executed"])
        self.assertEqual(receipt["evidence_kind"], "CONFIGURED_PROVIDER_UNACCEPTED")
        self.assertFalse(receipt["academic_acceptance"])
        self.assertFalse(receipt["product_accepted"])

    def test_hierarchical_annotation_and_independent_review_execute(self):
        self.complete()
        operations = {json.loads(r.messages[1]["content"])["operation"] for r in self.stack.annotator.requests}
        self.assertIn("ANNOTATE_SCENE", operations)
        self.assertIn("ANNOTATE_DISCOURSE_LEAF", operations)
        self.assertGreater(self.stack.calls["reviewer"], 0)
        self.assertNotEqual(self.stack.annotations.annotator_identity, self.stack.annotations.reviewer_identity)

    def test_private_narration_exists_but_safe_status_excludes_it(self):
        result = self.complete()
        output, _ = self.native_result()
        self.assertIn("Birds", canonical(output.payload).decode())
        safe = "\n".join(decoded_strings(result))
        for private in ("Birds", "Flight", "2 + 3", self.token, str(self.root)):
            self.assertNotIn(private, safe)

    def test_safe_receipt_excludes_source_prompts_and_model_responses(self):
        self.complete()
        _, receipt = self.native_result()
        safe = "\n".join(decoded_strings(receipt))
        for private in ("Birds", "Flight", "2 + 3", self.token, str(self.root), "source_pages", "messages"):
            self.assertNotIn(private, safe)

    def test_supported_math_expression_is_retained(self):
        result = self.complete()
        self.assertEqual(result["math"]["applicability"], "REQUIRED")
        output, receipt = self.native_result()
        self.assertIn("2 + 3 = 5", canonical(output.payload).decode())
        with self.port.native(self.p, self.run, "read") as native:
            _, _, _, components, _ = native.verified_pedagogy(self.run, "local")
        self.assertEqual(receipt["math_artifact_id"], components["upstream"]["math"]["artifact_id"])
        self.assertEqual(receipt["math_sha256"], components["upstream"]["math"]["sha256"])

    def test_explicit_non_math_path_reaches_director(self):
        run = self.admit_other((), "non-math")
        result = self.complete(run)
        self.assertEqual(result["math"]["applicability"], "NOT_REQUIRED")
        self.assertEqual(result["stages"]["DIRECTOR"], "SUCCEEDED")

    def test_unsupported_math_never_invokes_director(self):
        run = self.admit_other(("Compute the matrix inverse.",), "unsupported")
        result = self.complete(run)
        self.assertEqual(result["stages"]["MATH"], "BLOCKED")
        self.assertEqual(result["stages"]["REASONING"], "PENDING")
        self.assertEqual(result["stages"]["PEDAGOGY"], "PENDING")
        self.assertEqual(result["stages"]["DIRECTOR"], "PENDING")
        self.assertEqual(self.stack.calls, {"generator": 0, "critic": 0, "annotator": 0, "reviewer": 0})

    def test_explicit_derivation_needs_native_teaching_obligations(self):
        run = self.admit_other(("Step: 2 + 3 = 5 => 5 = 2 + 3",), "derivation")
        result = self.complete(run)
        self.assertEqual(result["stages"]["MATH"], "SUCCEEDED")
        self.assertEqual(result["stages"]["PEDAGOGY"], "SUCCEEDED")
        self.failed(result, "director_math_teaching_contract_required")
        self.assertFalse(self.stack.generator.requests)

    def test_visual_animation_and_all_later_stages_not_run(self):
        result = self.complete()
        self.assertEqual(result["downstream"]["VISUAL"], "NOT_RUN")
        self.assertEqual(result["downstream"]["ANIMATION"], "NOT_RUN")
        self.assertTrue(all(v == "NOT_RUN" for v in result["downstream"].values()))

    def test_narration_does_not_close_audio(self):
        self.complete()
        _, receipt = self.native_result()
        self.assertFalse(receipt["audio_complete"])
        self.assertFalse(receipt["visual_executed"])

    def test_queue_ack_is_after_verified_native_output_commit(self):
        self.complete()
        with self.port.native(self.p, self.run, "read") as native:
            self.assertEqual(native.queue.stats()["ACKED"], 8)
            output, receipt = native.verified_director(self.run, "local")
            self.assertEqual(native.record(self.run, output.artifact_id).blob_digest, receipt["output_sha256"])

    def test_inspection_and_legacy_workers_cannot_take_director_work(self):
        from apps.api.job_service import CAPABILITY as inspection_capability
        self.until_director()
        with self.port.native(self.p, self.run, "read") as native:
            for capability in (inspection_capability, "producer:source_grounded_di_knowledge_v1",
                               "producer:source_grounded_di_knowledge_pr_math_reasoning_pedagogy_v1"):
                self.assertIsNone(native.queue.poll("foreign-worker", capability_tags=[capability]))

    def test_same_intent_replays_without_provider_invocations(self):
        result = self.complete()
        calls = deepcopy(self.stack.calls)
        self.assertEqual(self.port.admit(self.p, self.source["source_id"], "intent", producer_config=self.config), result)
        self.assertEqual(self.step(), result)
        self.assertEqual(self.stack.calls, calls)

    def test_conflicting_source_under_same_intent_rejected(self):
        other = self.operator.import_pdf(self.p, pdf(("3 + 4 = 7",)))
        with self.assertRaises(Exception):
            self.port.admit(self.p, other["source_id"], "intent", producer_config=self.config)

    def test_changed_director_configuration_conflicts(self):
        changed = profile_config(director=settings(self.stack, title="Different governed title"))
        with self.assertRaises(Exception):
            self.port.admit(self.p, self.source["source_id"], "intent", producer_config=changed)

    def test_read_restart_requires_no_configured_provider(self):
        expected = self.complete()
        reopened = DirectorProducerControlPlane(Service(self.root, self.credentials), enabled_profiles={PROFILE})
        calls = deepcopy(self.stack.calls)
        self.assertEqual(reopened.status(self.p, self.run), expected)
        self.assertEqual(self.stack.calls, calls)

    def test_native_catalog_uses_same_cas_and_not_overall_run_state(self):
        self.complete()
        with self.port.native(self.p, self.run, "read") as native:
            with native_runtime(native, self.run, None) as assembly:
                self.assertIs(assembly.io.catalog.cas, native.cas)
                self.assertIn("DIRECTOR", native.persistence.load_run_state(self.run)["stages"])
                tables = {r[0] for r in assembly.io.catalog.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertNotIn("run_states", tables)

    def test_visual_input_validator_gap_not_invented(self):
        result = self.complete()
        self.assertEqual(result["director"]["visual_input_validator"], "NOT_AVAILABLE_FOR_NATIVE_ARTIFACT_PAIR")

    def test_foreign_tenant_denied(self):
        with self.port.native(self.p, self.run, "read") as native:
            with self.assertRaises(ProducerError):
                native.status(self.run, "foreign")

    def test_operator_controls_remain_fail_closed(self):
        with self.assertRaisesRegex(ProducerError, "producer_control_not_supported"):
            self.port.control(self.p, self.run, "pause")


class ProviderFailureTests(PreparedProducerFixture):
    def setUp(self):
        super().setUp()
        self.until_director()

    def test_missing_provider_is_blocked_not_empty_success(self):
        self.failed(self.step(stack=False), "director_provider_unavailable")
        self.assertFalse(self.stack.generator.requests)

    def test_mixed_provider_options_and_explicit_configuration_rejected(self):
        for options in ({"provider": "contradictory-provider"},
                        {"model": "contradictory-model"},
                        {"provider": self.config["provider"], "model": self.config["model"]}):
            with self.subTest(fields=sorted(options)), self.assertRaisesRegex(
                    OperatorError, "producer_configuration_conflict"):
                self.port.admit(self.p, self.source["source_id"], "intent",
                                producer_config=self.config, **options)
        self.assertFalse(self.stack.generator.requests)

    def test_provider_execution_failure_is_bounded_and_safe(self):
        def broken(_):
            raise RuntimeError("private provider credential and traceback")
        self.stack.generator.invoke = broken
        result = self.step()
        self.failed(result, "PROVIDER_EXECUTION_FAILED")
        self.assertNotIn("credential", json.dumps(result))

    def test_provider_identity_mismatch_rejected(self):
        original = self.stack.generator.invoke
        def foreign(request):
            return replace(original(request), provider="foreign-provider")
        self.stack.generator.invoke = foreign
        self.failed(self.step(), "PROVIDER_IDENTITY_MISMATCH")
        self.assertEqual(len(self.stack.generator.requests), 1)

    def test_runtime_identity_intent_mismatch_before_invocation(self):
        self.stack.generator_identity = replace(self.stack.generator_identity, model="foreign-model")
        self.failed(self.step(), "director_provider_identity_mismatch")
        self.assertFalse(self.stack.generator.requests)

    def test_runtime_annotation_policy_cannot_override_committed_intent(self):
        changed = replace(self.stack.annotations.policy, maximum_scenes_per_leaf=1)
        self.stack.annotations = replace(self.stack.annotations, policy=changed)
        self.failed(self.step(), "director_policy_conflict")
        self.assertFalse(self.stack.generator.requests)

    def test_malformed_generator_response_fails_closed(self):
        self.stack.generator.transform = lambda payload, value, number: "not-json"
        self.failed(self.step(), "RESPONSE_CONTRACT_REJECTED")
        self.assertEqual(len(self.stack.generator.requests), 2)

    def test_schema_invalid_generator_response_fails_closed(self):
        self.stack.generator.transform = lambda payload, value, number: dict(value, unknown="unsafe")
        self.failed(self.step(), "RESPONSE_CONTRACT_REJECTED")

    def test_refusal_is_terminal(self):
        original = self.stack.generator.invoke
        self.stack.generator.invoke = lambda request: replace(original(request), finish_reason="refusal")
        self.failed(self.step(), "INCOMPLETE_OR_REFUSED_RESPONSE")
        self.assertEqual(len(self.stack.generator.requests), 1)

    def test_incomplete_response_has_only_bounded_retries(self):
        original = self.stack.generator.invoke
        self.stack.generator.invoke = lambda request: replace(original(request), finish_reason="length")
        self.failed(self.step(), "INCOMPLETE_OR_REFUSED_RESPONSE")
        self.assertEqual(len(self.stack.generator.requests), 2)

    def test_response_budget_overflow_is_terminal(self):
        self.stack.generator.transform = lambda payload, value, number: "x" * 64001
        self.failed(self.step(), "DIRECTOR_OUTPUT_BUDGET_EXCEEDED")
        self.assertEqual(len(self.stack.generator.requests), 1)

    def test_context_budget_overflow_fails_before_provider_call(self):
        with self.budget(maximum_request_characters=100):
            result = self.step()
        self.failed(result, "DIRECTOR_CONTEXT_BUDGET_EXCEEDED")
        self.assertFalse(self.stack.generator.requests)

    def test_scene_budget_is_enforced_without_truncation(self):
        with self.budget(maximum_scenes=1):
            result = self.step()
        self.failed(result, "DIRECTOR_OUTPUT_BUDGET_EXCEEDED")

    def test_beat_budget_is_enforced_without_truncation(self):
        with self.budget(maximum_total_beats=1):
            result = self.step()
        self.failed(result, "DIRECTOR_AGGREGATE_OUTPUT_BUDGET_EXCEEDED")

    def test_spoken_character_budget_is_enforced(self):
        with self.budget(maximum_spoken_characters=1):
            result = self.step()
        self.failed(result, "DIRECTOR_AGGREGATE_OUTPUT_BUDGET_EXCEEDED")

    def test_dropped_objective_rejected_by_native_plan_validator(self):
        def drop(payload, value, number):
            if payload["operation"] == "PLAN":
                value["scenes"][0]["objective_ids"] = ["invented-objective"]
            return value
        self.stack.generator.transform = drop
        self.failed(self.step(), "RESPONSE_CONTRACT_REJECTED")

    def test_changed_teaching_mode_rejected(self):
        def change(payload, value, number):
            if payload["operation"] == "PLAN":
                value["scenes"][0]["teaching_mode"] = "DERIVATION"
            return value
        self.stack.generator.transform = change
        self.failed(self.step(), "RESPONSE_CONTRACT_REJECTED")

    def test_prerequisite_teaching_order_cannot_be_reversed(self):
        def reverse(payload, value, number):
            if payload["operation"] == "PLAN":
                value["scenes"].reverse()
            return value
        self.stack.generator.transform = reverse
        self.failed(self.step(), "RESPONSE_CONTRACT_REJECTED")

    def test_foreign_source_anchor_cannot_be_narrated(self):
        def foreign(payload, value, number):
            if payload["operation"] == "NARRATE":
                value["beats"][0]["evidence_ids"] = ["foreign-source-anchor"]
            return value
        self.stack.generator.transform = foreign
        self.failed(self.step(), "RESPONSE_CONTRACT_REJECTED")

    def test_required_assessment_cannot_be_dropped(self):
        def drop(payload, value, number):
            if payload["operation"] == "NARRATE":
                value["assessments"] = []
            return value
        self.stack.generator.transform = drop
        self.failed(self.step(), "RESPONSE_CONTRACT_REJECTED")

    def test_critic_execution_failure_cannot_be_outer_success(self):
        def broken(_):
            raise RuntimeError("private source in provider transport")
        self.stack.critic.invoke = broken
        self.failed(self.step(), "director_critic_execution_incomplete")

    def test_critic_identity_mismatch_cannot_be_outer_success(self):
        original = self.stack.critic.invoke
        self.stack.critic.invoke = lambda request: replace(original(request), model="foreign-critic")
        self.failed(self.step(), "director_critic_execution_incomplete")

    def test_critic_malformed_receipt_cannot_be_outer_success(self):
        self.stack.critic.transform = lambda payload, value, number: dict(value, claim_id="invented-claim")
        self.failed(self.step(), "director_critic_execution_incomplete")

    def test_source_factual_contradiction_blocks_native_director(self):
        self.stack.critic.transform = lambda payload, value, number: dict(value, verdict="CONTRADICTED")
        self.failed(self.step(), "DIRECTOR_QA_BLOCKED")

    def test_annotation_schema_failure_fails_closed(self):
        self.stack.annotator.transform = lambda payload, value, number: {"unexpected": "record"}
        self.failed(self.step(), "RESPONSE_CONTRACT_REJECTED")

    def test_annotation_reviewer_failure_cannot_be_outer_success(self):
        def broken(_):
            raise RuntimeError("unavailable reviewer")
        self.stack.reviewer.invoke = broken
        self.failed(self.step(), "director_annotation_review_incomplete")


class ArtifactSafetyTests(PreparedProducerFixture):
    def setUp(self):
        super().setUp()
        self.until_director()

    def native_replay(self):
        """Obtain the real native committed replay record, never a fake result."""
        self.assertEqual(self.step()["stages"]["DIRECTOR"], "SUCCEEDED")
        with self.port.native(self.p, self.run, "read") as native:
            request, _, _ = native.request(self.run, "local")
            with native_runtime(native, self.run, None) as assembly:
                claim = assembly.idempotency.get(request.idempotency_key)
                _, algorithm, sha, size = claim.result_ref.split(":")
                record = strict_json(native.cas.get_bytes(BlobRef(algorithm, sha, int(size))))
        return claim, record, request.reasoning_ref.artifact_id

    def set_native_claim_result(self, value):
        with self.port.native(self.p, self.run, "read") as native:
            request, _, _ = native.request(self.run, "local")
            with native_runtime(native, self.run, None) as assembly:
                assembly.idempotency.db.execute("UPDATE claims SET result_ref=? WHERE key=?",
                                               (value, request.idempotency_key))
                assembly.idempotency.db.commit()

    def reject_replay(self):
        calls = dict(self.stack.calls)
        with self.assertRaisesRegex(ProducerError, "director_native_replay_mismatch"):
            self.port.status(self.p, self.run)
        self.assertEqual(self.stack.calls, calls)

    def test_tampered_reasoning_stops_before_generation(self):
        self.tamper_stage("REASONING")
        with self.assertRaises(Exception):
            self.step()
        self.assertFalse(self.stack.generator.requests)

    def test_tampered_pedagogy_stops_before_generation(self):
        self.tamper_stage("PEDAGOGY")
        with self.assertRaises(Exception):
            self.step()
        self.assertFalse(self.stack.generator.requests)

    def test_foreign_reasoning_run_cannot_unlock_director(self):
        with self.port.native(self.p, self.run, "read") as native:
            aid, _ = native.stage_ref(self.run, "REASONING")
            with native.persistence._conn() as db:
                db.execute("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?", (aid,))
        with self.assertRaises(Exception):
            self.step()
        self.assertFalse(self.stack.generator.requests)

    def test_foreign_pedagogy_run_cannot_unlock_director(self):
        with self.port.native(self.p, self.run, "read") as native:
            aid, _ = native.stage_ref(self.run, "PEDAGOGY")
            with native.persistence._conn() as db:
                db.execute("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?", (aid,))
        with self.assertRaises(Exception):
            self.step()
        self.assertFalse(self.stack.generator.requests)

    def test_source_bytes_tamper_prevents_native_execution(self):
        self.operator.cas._path(self.source["sha256"]).write_bytes(b"source-bytes-tamper")
        with self.assertRaises(Exception):
            self.step()
        self.assertFalse(self.stack.generator.requests)

    def test_exact_source_catalog_tamper_prevents_generation(self):
        with self.port.native(self.p, self.run, "read") as native:
            request, _, _ = native.request(self.run, "local")
            pedagogy = native.read(self.run, request.pedagogy_ref.artifact_id)
            source_ref = reference(pedagogy["payload"]["source_catalog_ref"])
            row = native.record(self.run, source_ref.artifact_id)
            native.cas._path(row.blob_digest).write_bytes(b"catalog-tamper")
        with self.assertRaises(Exception):
            self.step()
        self.assertFalse(self.stack.generator.requests)

    def test_native_director_cas_tamper_rejected_on_read(self):
        self.step()
        output, receipt = self.native_result()
        self.operator.cas._path(receipt["output_sha256"]).write_bytes(b"director-tamper")
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)

    def test_native_catalog_sql_tamper_rejected(self):
        self.step()
        output, _ = self.native_result()
        with self.port.native(self.p, self.run, "read") as native:
            with native_runtime(native, self.run, None) as assembly:
                assembly.io.catalog.db.execute("UPDATE artifact_records SET record_json='{}' WHERE artifact_id=?", (output.artifact_id,))
                assembly.io.catalog.db.commit()
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)

    def test_native_replay_cas_tamper_rejected_on_status(self):
        claim, _, _ = self.native_replay()
        self.operator.cas._path(claim.result_ref.split(":")[2]).write_bytes(b"replay-cas-tamper")
        self.reject_replay()

    def test_missing_native_replay_cas_rejected_on_status(self):
        claim, _, _ = self.native_replay()
        # This is a single identified runtime blob inside the isolated fixture.
        self.operator.cas._path(claim.result_ref.split(":")[2]).unlink()
        self.reject_replay()

    def test_missing_or_malformed_native_claim_result_ref_rejected(self):
        self.native_replay()
        for result_ref in (None, "not-a-cas-reference", "cas:sha256:" + "0" * 64 + ":1"):
            with self.subTest(reference_kind="null" if result_ref is None else "invalid"):
                self.set_native_claim_result(result_ref)
                self.reject_replay()

    def test_foreign_upstream_artifact_cannot_replay_as_director_output(self):
        _, record, foreign_output = self.native_replay()
        # Keep the exact native fingerprint/schema, but substitute a genuine
        # upstream artifact. Its valid ancestry cannot make it Director output.
        record["value"]["output_artifact_refs"] = [foreign_output]
        blob = self.operator.cas.put_bytes(canonical(record))
        self.set_native_claim_result("cas:sha256:" + blob.digest + ":" + str(blob.size))
        self.reject_replay()

    def test_native_failed_replay_cannot_back_successful_outer_status(self):
        _, record, _ = self.native_replay()
        record["outcome"] = "FAILED"
        record["value"] = dict(diagnostics=["technical-negative-control"],
                               evidence_refs=[], remediation_owner="INFRA")
        blob = self.operator.cas.put_bytes(canonical(record))
        self.set_native_claim_result("cas:sha256:" + blob.digest + ":" + str(blob.size))
        self.reject_replay()


if __name__ == "__main__":
    unittest.main()
