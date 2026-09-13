"""Contract integration regressions; synthetic fixtures, never acceptance evidence."""
import ast
from dataclasses import replace
import itertools
from pathlib import Path
import sys
import unittest

from bie.reasoning.reasoning_provenance_envelope import make_reasoning_envelope
from bie.pedagogy.learning_objective_generator import generate_objective
from bie.pedagogy.pedagogy_plan_contract import PedagogyDecision, build_pedagogy_plan
from bie.pedagogy.pedagogy_provenance import build_lineage, validate_lineage_graph
from bie.pedagogy.pedagogy_section_readiness import pedagogy_readiness_gate
from bie.pedagogy.uncertainty_aware_mastery import MasteryObservation, infer_knowledge_state
from bie.pedagogy.adaptive_policy_state_machine import AdaptiveState, next_state, state_fingerprint
from bie.pedagogy.acceleration_path import choose_acceleration_path
from bie.pedagogy.book_scale_curriculum_optimizer import CurriculumUnit, CurriculumDependency, optimize_book_curriculum
from bie.pedagogy.multi_constraint_sequencer import CurriculumNode, SequenceConstraint, sequence_curriculum
from bie.pedagogy.lesson_boundary_detection import lesson_boundaries
from bie.pedagogy.domain_pedagogy_policy import PedagogyPolicy, PedagogyPolicyRegistry, default_policy_registry
from bie.pedagogy.assessment_blueprint import AssessmentCell, build_assessment_blueprint
from bie.pedagogy.assessment_alignment import assessment_alignment
from bie.pedagogy.pedagogy_realbook_fixture import SourceAnchor, PedagogyArtifactRef, REQUIRED_STAGES, evaluate_pedagogy_fixture
from bie.pedagogy.pedagogy_replay_manifest import build_pedagogy_replay_manifest, replay_diff
from bie.pedagogy.pedagogy_mode_arbitration import ModeCandidate, arbitrate_mode
from bie.pedagogy.cognitive_load_qa import cognitive_load_qa


class CanonicalPedIntegrationTests(unittest.TestCase):
    def checks(self):
        return dict.fromkeys(("objective_coverage", "prerequisite_coverage", "assessment_alignment",
                              "cognitive_load_safe", "realbook_fixture", "integration_contract"), True)

    def plan(self, decisions, **kw):
        data = dict(plan_id="plan", source_id="source", objective_ids=["objective"], lesson_ids=["lesson"],
                    decisions=decisions, policy_version="policy-v1")
        data.update(kw)
        return build_pedagogy_plan(**data)

    def replay(self, **kw):
        data = dict(input_hashes={"source": "source-hash"}, policy_version="p1", learner_state_version="l1",
                    reasoning_fingerprints={"r": "r-hash"}, output_hashes={"plan": "plan-hash"},
                    environment_fingerprint="python-test")
        data.update(kw)
        return build_pedagogy_replay_manifest(**data)

    def unit(self, name, order=0, minutes=10, load=.4):
        return CurriculumUnit(name, order, .8, load, .4, .2, minutes)

    def base_state(self):
        return AdaptiveState("learner", "concept", "STANDARD", .5, 1, ("prior-evidence",))

    def advance(self, **kw):
        data = dict(prerequisite_ready=True, misconception_detected=False, transfer_passed=True,
                    new_mastery=.95, evidence_ids=["assessment-evidence"])
        data.update(kw)
        return next_state(self.base_state(), **data)

    def fixture(self):
        return [PedagogyArtifactRef(f"a{i}", stage, ("anchor",), () if i == 0 else (f"a{i-1}",))
                for i, stage in enumerate(REQUIRED_STAGES)]

    def test_reasoning_to_pedagogy_review_and_replay(self):
        upstream = make_reasoning_envelope(artifact_id="r", reasoning_family="CAUSAL", status="CONFLICT",
                                          evidence_ids=["contradiction", "source"], confidence=.6, requires_review=True)
        objective = generate_objective("concept", "source-grounded claim", iter(upstream.evidence_ids))
        lineage = build_lineage(objective.objective_id, source_evidence_ids=objective.evidence_ids,
                                reasoning_parent_ids=[upstream.artifact_id], confidence=upstream.confidence,
                                requires_review=upstream.requires_review)
        self.assertEqual(lineage.reasoning_parent_ids, ("r",))
        self.assertEqual(lineage.source_evidence_ids, upstream.evidence_ids)
        decision = PedagogyDecision("d", "objective", objective.objective_id, lineage.source_evidence_ids,
                                    status=upstream.status, confidence=lineage.confidence, requires_review=lineage.requires_review)
        plan = self.plan([decision])
        self.assertTrue(plan.requires_review)
        gate = pedagogy_readiness_gate(self.checks(), review_items=[d.decision_id for d in plan.decisions if d.requires_review],
                                      provenance_complete=True, reproducible=True)
        self.assertFalse(gate.passed)
        a = self.replay(reasoning_fingerprints={"r": upstream.fingerprint()}, output_hashes={"plan": plan.fingerprint()})
        b = self.replay(reasoning_fingerprints={"r": replace(upstream, uncertainty=("new uncertainty",)).fingerprint()},
                        output_hashes={"plan": plan.fingerprint()})
        self.assertEqual(replay_diff(a, b), ("reasoning_fingerprints",))

    def test_lineage_rejects_blank_upstream_and_source_ids(self):
        for field in ("source_evidence_ids", "reasoning_parent_ids", "prerequisite_parent_ids", "math_parent_ids"):
            with self.subTest(field=field):
                data = dict(source_evidence_ids=["e"], reasoning_parent_ids=["r"])
                data[field] = [" "]
                with self.assertRaises(ValueError):
                    build_lineage("artifact", **data)

    def test_lineage_detects_cycles_across_parent_families(self):
        a = build_lineage("a", source_evidence_ids=["e"], reasoning_parent_ids=["r"], prerequisite_parent_ids=["b"])
        b = build_lineage("b", source_evidence_ids=["e"], reasoning_parent_ids=["r"], math_parent_ids=["a"])
        self.assertTrue(validate_lineage_graph([a, b]))

    def test_lineage_book_scale_chain_does_not_recurse(self):
        lines = [build_lineage(f"p{i:04}", source_evidence_ids=["e"],
                              reasoning_parent_ids=[f"p{i+1:04}" if i < 1199 else "upstream-r"])
                 for i in range(1200)]
        self.assertEqual(validate_lineage_graph(lines), ())

    def test_plan_rejects_parent_cycles(self):
        for decisions in ([PedagogyDecision("a", "x", "p", ("e",), ("a",))],
                          [PedagogyDecision("a", "x", "p", ("e",), ("b",)), PedagogyDecision("b", "x", "q", ("e",), ("a",))]):
            with self.subTest(decisions=decisions), self.assertRaises(ValueError):
                self.plan(decisions)

    def test_plan_fingerprint_normalizes_evidence_sets(self):
        a = PedagogyDecision("a", "x", "p", ("e1", "e2"))
        b = replace(a, evidence_ids=("e2", "e1", "e1"))
        self.assertEqual(self.plan([a]).fingerprint(), self.plan([b]).fingerprint())
        self.assertNotEqual(self.plan([a]).fingerprint(), self.plan([replace(a, evidence_ids=("e1",))]).fingerprint())

    def test_plan_rejects_blank_grounding(self):
        for bad in (("",), (" ",), "e"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.plan([PedagogyDecision("d", "x", "p", bad)])

    def test_all_upstream_nonresolved_statuses_stay_reviewable(self):
        for status in ("AMBIGUOUS", "CONFLICT", "ABSTAINED", "INSUFFICIENT_EVIDENCE", "UNREACHABLE"):
            with self.subTest(status=status):
                d = PedagogyDecision("d", "x", "p", ("e",), status=status, requires_review=True)
                self.assertTrue(self.plan([d]).requires_review)
                with self.assertRaises(ValueError):
                    self.plan([replace(d, requires_review=False)])

    def test_uncertain_and_conflicting_mastery_remain_reviewable(self):
        for obs in ([], [MasteryObservation("a", "concept", .99, .01, evidence_ids=("e",))],
                    [MasteryObservation("a", "concept", .1, 1, evidence_ids=("e1",)),
                     MasteryObservation("b", "concept", .9, 1, evidence_ids=("e2",))]):
            with self.subTest(obs=obs):
                state = infer_knowledge_state("concept", obs)
                self.assertTrue(state.requires_review)
                self.assertGreaterEqual(state.mean_mastery, state.lower_bound)
                self.assertLessEqual(state.mean_mastery, state.upper_bound)

    def test_mastery_policy_rejects_invalid_settings(self):
        obs = [MasteryObservation("a", "concept", .8, 1, evidence_ids=("e",))]
        for field, value in (("recency_decay", -1), ("recency_decay", 2), ("recency_decay", float("nan")),
                             ("conflict_gap", -1), ("review_confidence_below", 2)):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                infer_knowledge_state("concept", obs, **{field: value})
        for age in (float("nan"), .5, True):
            with self.subTest(age=age), self.assertRaises(ValueError):
                infer_knowledge_state("concept", [replace(obs[0], age_steps=age)])

    def test_mastery_fingerprint_is_permutation_invariant(self):
        obs = [MasteryObservation(str(i), "concept", s, r, evidence_ids=(str(i),))
               for i, (s, r) in enumerate(((.1, .13), (.2, .37), (.9, .99), (.7, .51)))]
        fingerprints = {infer_knowledge_state("concept", order).fingerprint() for order in itertools.permutations(obs)}
        self.assertEqual(len(fingerprints), 1)

    def test_uncertainty_survives_adaptation(self):
        for obs in ([], [MasteryObservation("a", "concept", .99, .01, evidence_ids=("low-reliability",))],
                    [MasteryObservation("a", "concept", .1, 1, evidence_ids=("e1",)),
                     MasteryObservation("b", "concept", .9, 1, evidence_ids=("e2",))]):
            with self.subTest(obs=obs):
                knowledge = infer_knowledge_state("concept", obs)
                state, transition = self.advance(new_mastery=knowledge.mean_mastery, knowledge_state=knowledge)
                self.assertNotIn(state.state, {"ACCELERATE", "MASTERED"})
                self.assertTrue(state.requires_review)
                self.assertTrue(transition.requires_review)

    def test_prerequisite_gap_blocks_even_high_mastery(self):
        self.assertFalse(choose_acceleration_path(.99, .99, .2).eligible)
        state, _ = self.advance(prerequisite_ready=False)
        self.assertEqual(state.state, "BRIDGE")

    def test_existing_low_confidence_state_cannot_silently_advance(self):
        current=replace(self.base_state(),mastery_confidence=.2)
        state,_=next_state(current,prerequisite_ready=True,misconception_detected=False,
                           transfer_passed=True,new_mastery=.99,evidence_ids=["new"])
        self.assertTrue(state.requires_review)
        self.assertNotIn(state.state,{"ACCELERATE","MASTERED"})

    def test_adaptation_preserves_prior_evidence_and_replays(self):
        a, _ = self.advance(evidence_ids=iter(["new-b", "new-a"]))
        b, _ = self.advance(evidence_ids=["new-a", "new-b"])
        self.assertEqual(state_fingerprint(a), state_fingerprint(b))
        self.assertIn("prior-evidence", a.evidence_ids)
        self.assertEqual(a.version, 2)

    def test_hard_curriculum_constraints_override_priority(self):
        units = [self.unit("advanced", 0), self.unit("basic", 1)]
        deps = [CurriculumDependency("basic", "advanced", "PREREQUISITE"),
                CurriculumDependency("advanced", "basic", "SOURCE_ORDER", False)]
        for us in (units, list(reversed(units))):
            plan = optimize_book_curriculum(us, reversed(deps))
            self.assertLess(plan.order.index("basic"), plan.order.index("advanced"))
            self.assertIn(("advanced", "basic", "SOURCE_ORDER"), plan.violated_soft_constraints)
        seq = sequence_curriculum([CurriculumNode("advanced", 0, .4, 1), CurriculumNode("basic", 1, .4, 0)],
                                  [SequenceConstraint("basic", "advanced", "PREREQUISITE")])
        self.assertEqual(seq.order, ("basic", "advanced"))

    def test_book_groups_respect_both_budgets(self):
        units = [self.unit(str(i), i, minutes=8 + i, load=.2 + .1 * (i % 4)) for i in range(20)]
        plan = optimize_book_curriculum(units, [], max_lesson_minutes=45, max_lesson_load=1.1)
        by = {u.unit_id: u for u in units}
        self.assertEqual(sorted(itertools.chain.from_iterable(plan.lesson_groups)), sorted(by))
        for group in plan.lesson_groups:
            self.assertLessEqual(sum(by[i].estimated_minutes for i in group), 45)
            self.assertLessEqual(sum(by[i].cognitive_load for i in group), 1.1)

    def test_unsplittable_unit_and_invalid_book_budgets_rejected(self):
        for units, kwargs in (([self.unit("long", minutes=46)], {}),
                              ([self.unit("heavy", load=.8)], {"max_lesson_load": .5}),
                              ([self.unit("bad", minutes=float("nan"))], {}),
                              ([self.unit("normal")], {"max_lesson_minutes": float("nan")}),
                              ([self.unit("normal")], {"max_lesson_load": 0})):
            with self.subTest(units=units, kwargs=kwargs), self.assertRaises(ValueError):
                optimize_book_curriculum(units, [], **kwargs)

    def test_adjacent_load_guard_rejects_nan_budget(self):
        with self.assertRaises(ValueError):
            sequence_curriculum([CurriculumNode("a", 0, 1, .5), CurriculumNode("b", 1, 1, .5)], [],
                                max_adjacent_load=float("nan"))

    def test_atomic_lesson_boundary_rejects_oversize_or_nan_load(self):
        for cost in (3, float("nan"), -1):
            with self.subTest(cost=cost), self.assertRaises(ValueError):
                lesson_boundaries([("a", "topic", cost)], max_load=2)

    def test_policy_requires_every_declared_evidence_kind(self):
        registry = PedagogyPolicyRegistry([PedagogyPolicy("p", ("CAUSAL",), ("ANALYZE",), ("SIMULATION",),
                                                                         ("mechanism", "observation"))])
        self.assertEqual(registry.match(content_types=["CAUSAL"], objective_level="ANALYZE",
                                       available_evidence_kinds=["mechanism"]), ())
        self.assertTrue(registry.match(content_types=["CAUSAL"], objective_level="ANALYZE",
                                       available_evidence_kinds=["mechanism", "observation"]))

    def test_policy_uses_content_type_and_learning_intent(self):
        registry = default_policy_registry()
        for content_type, level, evidence, expected in (("PROGRAMMING", "CREATE", "code_example", "programming"),
                    ("SOURCE_CRITICISM", "EVALUATE", "primary_source", "source_criticism"),
                    ("SPATIAL", "APPLY", "spatial_evidence", "spatial_reasoning")):
            with self.subTest(content=content_type):
                self.assertEqual(registry.match(content_types=[content_type], objective_level=level,
                                               available_evidence_kinds=[evidence])[0].policy_id, expected)
        self.assertEqual(registry.match(content_types=["SOURCE_CRITICISM"], objective_level="REMEMBER",
                                       available_evidence_kinds=["primary_source"]), ())

    def test_assessment_gaps_and_cognitive_mismatch_detected(self):
        cell = AssessmentCell("o", "c", "APPLY", None, False, ("q",), ("e",))
        report = build_assessment_blueprint([("o", "c", "APPLY", False), ("o", "c", "APPLY", True)], [cell])
        self.assertFalse(report.passed)
        self.assertEqual(report.uncovered_requirements, (("o", "c", "APPLY", True),))
        self.assertFalse(assessment_alignment({"o": "APPLY"}, [("q", "o", "REMEMBER")]).passed)

    def test_assessment_blank_item_and_evidence_ids_rejected(self):
        cell = AssessmentCell("o", "c", "APPLY", None, False, ("q",), ("e",))
        for field in ("item_ids", "evidence_ids"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_assessment_blueprint([("o", "c", "APPLY", False)], [replace(cell, **{field: ("",)})])

    def test_readiness_blocks_unresolved_reviews_and_incomplete_provenance(self):
        for data in (dict(review_items=["review"]), dict(provenance_complete=False), dict(reproducible=False)):
            kwargs = dict(provenance_complete=True, reproducible=True); kwargs.update(data)
            with self.subTest(data=data):
                self.assertFalse(pedagogy_readiness_gate(self.checks(), **kwargs).passed)

    def test_readiness_rejects_truthy_non_boolean_evidence(self):
        for value in ("False", 1, float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                checks = self.checks(); checks["integration_contract"] = value
                pedagogy_readiness_gate(checks, provenance_complete=True, reproducible=True)
        with self.assertRaises(ValueError):
            pedagogy_readiness_gate(self.checks(), provenance_complete="False", reproducible=True)

    def test_fixture_ungrounded_stages_cannot_pass(self):
        arts = [replace(x, evidence_ids=()) for x in self.fixture()]
        self.assertFalse(evaluate_pedagogy_fixture("f", [SourceAnchor("anchor", 1, "synthetic text")], arts).passed)

    def test_fixture_parent_cycle_cannot_pass(self):
        arts = self.fixture(); arts[0] = replace(arts[0], parent_ids=(arts[-1].artifact_id,))
        self.assertFalse(evaluate_pedagogy_fixture("f", [SourceAnchor("anchor", 1, "synthetic text")], arts).passed)

    def test_replay_requires_input_upstream_and_output_bindings(self):
        for key in ("input_hashes", "reasoning_fingerprints", "output_hashes"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.replay(**{key: {}})

    def test_mode_hysteresis_does_not_clear_review(self):
        candidates = [ModeCandidate("EXPLANATION", .8, .8, .8, .8), ModeCandidate("INQUIRY", .81, .81, .81, .81)]
        decision = arbitrate_mode(candidates, previous_mode="EXPLANATION")
        self.assertEqual(decision.selected_mode, "EXPLANATION")
        self.assertTrue(decision.requires_review)
        self.assertTrue(arbitrate_mode([ModeCandidate("EXPLANATION", .1, .1, .1, .1)]).requires_review)

    def test_mode_without_evidence_is_ineligible(self):
        unsupported=ModeCandidate("DERIVATION",1,0,1,1)
        supported=ModeCandidate("EXPLANATION",.4,.4,.4,.4)
        self.assertEqual(arbitrate_mode([unsupported,supported]).selected_mode,"EXPLANATION")
        with self.assertRaises(ValueError):
            arbitrate_mode([unsupported])

    def test_cognitive_load_nan_does_not_pass_qa(self):
        with self.assertRaises(ValueError):
            cognitive_load_qa([("lesson", float("nan"))])

    def test_objective_cannot_be_grounded_by_empty_iterator(self):
        for evidence in (iter(()), ("",), "e"):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                generate_objective("c", "concept", evidence)

    def test_no_production_archive_imports(self):
        root = Path(__file__).resolve().parents[2]
        suspicious = []
        for p in itertools.chain((root / "bie").rglob("*.py"), (root / "apps").rglob("*.py")):
            for node in ast.walk(ast.parse(p.read_text())):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
                if any(name.split(".")[0] in {"historical", "backups", "batches"} for name in names):
                    suspicious.append(str(p))
        self.assertEqual(suspicious, [])
        for name, module in tuple(sys.modules.items()):
            if name.startswith("bie.") and getattr(module, "__file__", None):
                rel = Path(module.__file__).resolve().relative_to(root)
                self.assertEqual(rel.parts[0], "bie")
