from dataclasses import asdict, replace
import copy, tempfile, unittest
from input_fixtures import upstream, replace_artifact, load
from bie.bie_core.artifact_contracts import ArtifactEnvelope, ProvenanceSource, ProvenanceSummary
from bie.director.director_artifacts import parse_json, canonical
from bie.director.director_inputs import publish_reasoning, publish_pedagogy, load_director_inputs
from bie.reasoning.decision_contracts import EvidenceRef, ReasoningDecision
from bie.reasoning.grounded_result import GroundedResult
from bie.pedagogy.pedagogy_plan_contract import build_pedagogy_plan


class UpstreamAdapterTests(unittest.TestCase):
    def fixture(self, **kwargs):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        return upstream(temp.name, **kwargs)

    def test_roundtrip_consumes_actual_canonical_objects_and_verified_source_bytes(self):
        f = self.fixture(); r = load(f)
        self.assertIsInstance(r.reasoning[0], ReasoningDecision)
        self.assertEqual(r.objectives[0], f.objective)
        self.assertEqual(r.catalog.pages[0].text.encode(), r.sources[0].data)
        graph = f.io.load_graph(r.parent_refs)
        self.assertTrue(all(ref.artifact_id in graph for a in graph.values() for ref in a.parent_refs))
        self.assertEqual(r.review_reasons, ())

    def test_actual_temporal_inference_is_preserved_and_assumptions_require_review(self):
        f = self.fixture(case_id="history"); r = load(f)
        self.assertIsInstance(r.inferences[0], GroundedResult)
        self.assertEqual(r.inferences[0].value["linear_extension"], ["A", "B"])
        self.assertEqual(r.reasoning[0].selected_option, r.inferences[0].value_json)
        self.assertIn("UPSTREAM_INFERENCE_REVIEW", r.review_reasons)

    def test_published_artifact_snapshots_mutable_canonical_decision_lists(self):
        f = self.fixture(); before = load(f)
        f.decision.evidence_refs.clear()
        self.assertEqual(load(f), before)

    def test_stale_full_reference_is_rejected_even_when_artifact_id_exists(self):
        f = self.fixture()
        for change in ({"content_hash": "0" * 64}, {"artifact_type": "pedagogy.plan"}, {"schema_version": "2.0.0"}):
            with self.subTest(change=change), self.assertRaises(ValueError): f.io.load(replace(f.reasoning_ref, **change))

    def test_source_bytes_corruption_is_detected_at_load(self):
        f = self.fixture()
        root = next(a for a in f.io.load_graph(f.inputs.parent_refs).values() if a.artifact_type == "source.document")
        blob = root.payload["blob"]
        f.io.catalog.cas._path(blob["digest"]).write_bytes(b"corrupted")
        with self.assertRaises(ValueError): load(f)

    def test_nontext_extraction_remains_review_and_utf8_mismatch_fails(self):
        f = self.fixture(media_type="application/pdf", source_data=b"controlled nontext bytes; not a real PDF")
        self.assertIn("EXTRACTION_ACCURACY_UNVERIFIED", f.inputs.review_reasons)
        with self.assertRaises(ValueError): self.fixture(source_data=b"text different from supplied extraction")

    def test_rehashing_an_envelope_does_not_hide_source_provenance_mismatch(self):
        f = self.fixture(); old = next(a for a in f.io.load_graph(f.inputs.parent_refs).values() if a.artifact_type == "source.document")
        forged = ArtifactEnvelope.create(old.artifact_type, old.schema_version, old.run_id, old.producer, [],
            ProvenanceSummary([ProvenanceSource("wrong-source", {"kind": "whole_source"}, old.payload["source_sha256"])]),
            old.metadata, old.payload)
        ref = f.io.put(forged, "SOURCE")
        with self.assertRaisesRegex(ValueError, "provenance"): f.io.source_bytes(ref)

    def test_source_catalog_cannot_substitute_a_rehashed_page_for_original_block(self):
        f = self.fixture(); payload = copy.deepcopy(f.io.load(f.source_ref).payload)
        payload["catalog"]["pages"][0]["extractor_version"] = "changed"
        altered = replace_artifact(f, f.source_ref, payload=payload)
        from bie.director.director_inputs import load_source_catalog
        with self.assertRaises(ValueError): load_source_catalog(f.io, altered)

    def test_reasoning_alias_cannot_replace_actual_source_artifact_reference(self):
        f = self.fixture(); d = replace(f.decision, evidence_refs=[EvidenceRef("evidence:science", "primary", .95)])
        with self.assertRaises(ValueError): publish_reasoning(f.io, f.run_id, f.source_ref, (d,))

    def test_reasoning_cycles_and_unresolved_dependencies_fail(self):
        f = self.fixture()
        for decisions in ((replace(f.decision, depends_on_decisions=["missing"]),),
            (replace(f.decision, depends_on_decisions=["r2"]), replace(f.decision, decision_id="r2", depends_on_decisions=[f.decision.decision_id]))):
            with self.subTest(decisions=decisions), self.assertRaises(ValueError):
                publish_reasoning(f.io, f.run_id, f.source_ref, decisions)

    def test_reasoning_boolean_nonfinite_or_string_sequence_cannot_pass(self):
        f = self.fixture()
        for change in ({"confidence": True}, {"confidence": float("nan")}, {"premises": "not-an-array"}, {"requires_review": 0}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                publish_reasoning(f.io, f.run_id, f.source_ref, (replace(f.decision, **change),))

    def test_review_propagates_and_cannot_be_weakened_by_plan_flag(self):
        f = self.fixture(review=True)
        self.assertIn("UPSTREAM_RE_REVIEW", f.inputs.review_reasons)
        self.assertIn("UPSTREAM_PED_REVIEW", f.inputs.review_reasons)
        payload = copy.deepcopy(f.io.load(f.pedagogy_ref).payload); payload["plan"]["requires_review"] = False
        ref = replace_artifact(f, f.pedagogy_ref, payload=payload, metadata={"requires_review": False})
        with self.assertRaises(ValueError): load(f, pedagogy_ref=ref)

    def test_updated_reasoning_requires_matching_pedagogy_revision(self):
        f = self.fixture(); updated = publish_reasoning(f.io, f.run_id, f.source_ref,
            (replace(f.decision, rationale_summary="Updated rationale, same evidence."),))
        with self.assertRaisesRegex(ValueError, "pairing"): load(f, reasoning_ref=updated)

    def test_assessment_omission_or_wrong_concept_is_not_a_completed_ped_input(self):
        f = self.fixture()
        for binding in (replace(f.binding, assessments=()),
                replace(f.binding, assessments=(replace(f.binding.assessments[0], concept_id="wrong"),))):
            with self.subTest(binding=binding), self.assertRaises(ValueError):
                publish_pedagogy(f.io, f.run_id, f.source_ref, f.reasoning_ref, f.plan, (f.objective,), (binding,))

    def test_cross_lesson_prerequisite_is_not_silently_assumed_mastered(self):
        f = self.fixture(); second = replace(f.plan.decisions[0], decision_id="pedagogy:second", parent_decision_ids=(f.binding.decision_id,))
        plan = build_pedagogy_plan(plan_id="two-lessons", source_id=f.plan.source_id, objective_ids=f.plan.objective_ids,
            lesson_ids=(f.binding.lesson_id, "lesson:second"), decisions=f.plan.decisions + (second,), policy_version="test/1")
        binding = replace(f.binding, decision_id=second.decision_id, lesson_id="lesson:second",
            assessments=(replace(f.binding.assessments[0], item_ids=("assessment:second",)),))
        ref = publish_pedagogy(f.io, f.run_id, f.source_ref, f.reasoning_ref, plan, (f.objective,), (f.binding, binding))
        with self.assertRaisesRegex(ValueError, "cross-lesson"):
            load_director_inputs(f.io, f.reasoning_ref, ref, run_id=f.run_id, **{**f.config, "lesson_id": "lesson:second"})

    def test_actual_inference_result_cannot_be_replaced_by_a_decision_with_same_id(self):
        f = self.fixture(case_id="history"); payload = copy.deepcopy(f.io.load(f.reasoning_ref).payload)
        payload["decisions"][0]["selected_option"] = '{"unsupported":"replacement"}'
        ref = replace_artifact(f, f.reasoning_ref, payload=payload)
        with self.assertRaisesRegex(ValueError, "actual inference"): load(f, reasoning_ref=ref)

    def test_strict_json_rejects_duplicate_fields_and_nonfinite_exponents(self):
        for text in ('{"x":1,"x":2}', '{"x":1e999}', '{"x":NaN}'):
            with self.subTest(text=text), self.assertRaises(ValueError): parse_json(text)

    def test_cross_run_ancestry_cannot_be_implicitly_reused(self):
        f = self.fixture()
        with self.assertRaisesRegex(ValueError, "cross-run"):
            load_director_inputs(f.io, f.reasoning_ref, f.pedagogy_ref, run_id="different-run", **f.config)


if __name__ == "__main__": unittest.main()
