"""Required cross-contract integration checks; synthetic, not real-book acceptance."""
import json
import unittest
from dataclasses import replace
from bie.reasoning.chronology_reasoning import Event, TimeSpan
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.event_order_reasoning import Before
from bie.reasoning.periodization_reasoning import Period
from bie.reasoning.temporal_reasoning_engine import temporal_reasoning_engine
from bie.reasoning.temporal_synthesis_reasoning import synthesize_timeline
from bie.reasoning.temporal_interval_reasoning import interval_relation
from bie.reasoning.temporal_causal_guard import assess_temporal_causal_claim
from bie.reasoning.temporal_causal_order_guard import validate_causal_temporal_order
from bie.reasoning.temporal_precision_compatibility import PreciseTime, compatible_precision, exact_comparison_allowed
from bie.reasoning.temporal_derived_lineage import build_derived_temporal_result
from bie.reasoning.temporal_result_contract import TemporalResultContract, validate_temporal_result
from bie.reasoning.temporal_integration_contract import TemporalIntegrationPayload, downstream_safe
from bie.reasoning.grounded_causal_graph import CausalEdge, build_grounded_causal_graph
from bie.reasoning.grounded_counterfactual import CounterfactualIntervention, evaluate_counterfactual
from bie.reasoning.reasoning_provenance_envelope import make_reasoning_envelope
from bie.reasoning.reasoning_status_semantics import normalize_status, aggregate_status
from bie.reasoning.reasoning_integration_gate import ReasoningStageEvidence, reasoning_integration_gate
from bie.reasoning.cross_family_arbitration import FamilyConstraint, arbitrate_constraints
from bie.reasoning.reasoning_replay_manifest import build_replay_manifest, compare_replay
from bie.reasoning.reasoning_realbook_fixture import SourceAnchor, RealBookReasoningFixture, evaluate_realbook_fixture
from bie.reasoning.spatial_frame_units import SpatialFrame, SpatialPoint, FrameTransform, assert_compatible, transform_point
from bie.reasoning.structured_uncertainty import UncertaintyComponent, assess_uncertainty
from bie.reasoning.transitive_invalidation import DecisionDependency, propagate_invalidation
from bie.reasoning.graph_cycle_hardening import find_canonical_cycles, propose_cycle_breaks


def timeline_data():
    return ([Event('a', 'A', TimeSpan(1, 1), ('e',)), Event('b', 'B', TimeSpan(2, 2), ('e',))],
            [Before('a', 'b', ('e',))], [Period('p', 'P', 1, 3, ('e',))],
            [EvidenceRef('e', 'primary', .9, 'synthetic contract fixture')])


def stage_data(review=False):
    return [ReasoningStageEvidence('evidence', 'src'),
            ReasoningStageEvidence('decision', 'd', ('e',), ('src',), review),
            ReasoningStageEvidence('graph', 'g', ('e',), ('d',)),
            ReasoningStageEvidence('uncertainty', 'u', ('e',), ('d',)),
            ReasoningStageEvidence('qa', 'q', ('e',), ('d', 'g', 'u'))]


class CanonicalReasoningIntegrationTests(unittest.TestCase):
    def test_before_does_not_establish_causation(self):
        relation = interval_relation(TimeSpan(1, 2), TimeSpan(3, 4))
        assessment = assess_temporal_causal_claim(relation.upper())
        self.assertFalse(assessment.causal_claim_allowed)
        self.assertTrue(assessment.requires_review)
        self.assertEqual(assessment.reason_code, 'BEFORE_DOES_NOT_IMPLY_CAUSES')
        self.assertIn('NOT_CAUSALLY_PROVEN', validate_causal_temporal_order(2, 3).status)

    def test_causal_contradictions_remain_reviewable(self):
        graph = build_grounded_causal_graph(['a', 'b'], [CausalEdge('a', 'b', ('e',), ('opposing',))])
        self.assertTrue(graph.requires_review)
        self.assertEqual(graph.edges[0].contradicting_evidence_ids, ('opposing',))
        checked = assess_temporal_causal_claim('BEFORE', causal_evidence_ids=('e',),
                    mechanism_supported=True, contradicting_evidence_ids=('opposing',))
        self.assertFalse(checked.causal_claim_allowed)

    def test_counterfactual_preserves_contradicting_source_ids(self):
        result = evaluate_counterfactual(CounterfactualIntervention('x', '0', '1', evidence_ids=('e',)),
                    causal_path_supported=True, causal_confidence=.9, predicted_effect='y',
                    contradicting_evidence_ids=('opposing',))
        self.assertTrue(result.requires_review)
        self.assertNotEqual(result.status, 'RESOLVED')
        self.assertIn('opposing', result.evidence_ids)

    def test_all_nonresolved_statuses_require_review(self):
        for state in ('AMBIGUOUS', 'CONFLICT', 'UNREACHABLE', 'ABSTAINED', 'INSUFFICIENT_EVIDENCE'):
            with self.subTest(state=state):
                status = normalize_status(state)
                self.assertTrue(status.requires_review)
                self.assertFalse(status.releasable)
                self.assertFalse(downstream_safe(TemporalIntegrationPayload('r', state, None, ('e',), False)))

    def test_temporal_abstention_maps_to_central_status(self):
        temporal = validate_temporal_result(TemporalResultContract('ABSTAIN', None, ('e',)))
        result = normalize_status(temporal.status)
        self.assertEqual(result.status, 'ABSTAINED')
        self.assertTrue(aggregate_status('RESOLVED', temporal.status).requires_review)

    def test_low_confidence_cross_family_result_requires_review(self):
        result = arbitrate_constraints([FamilyConstraint('temporal', 'p', 'SUPPORTS', 'RESOLVED', ('e',), .4)])
        self.assertTrue(result.requires_review)
        self.assertEqual(result.confidence, .4)

    def test_low_confidence_envelope_cannot_claim_no_review(self):
        with self.assertRaises(ValueError):
            make_reasoning_envelope(artifact_id='r', reasoning_family='temporal', status='RESOLVED',
                                    evidence_ids=('e',), confidence=.4, requires_review=False)

    def test_evidence_and_derived_parent_lineage_survive_envelope(self):
        component = temporal_reasoning_engine(*timeline_data())
        parent_ids = (component.value['chronology_result_id'], component.value['synthesis_result_id'])
        derived = build_derived_temporal_result('derived', 'grounded timeline', reversed(parent_ids), ['e'])
        envelope = make_reasoning_envelope(artifact_id=derived.result_id, reasoning_family='temporal',
                    status=component.status, evidence_ids=derived.evidence_ids,
                    parent_artifact_ids=derived.parent_result_ids, confidence=component.confidence,
                    requires_review=component.requires_review)
        payload = json.loads(envelope.canonical_json())
        self.assertEqual(set(payload['parent_artifact_ids']), set(parent_ids))
        self.assertEqual(payload['evidence_ids'], ['e'])

    def test_temporal_engine_preserves_one_shot_inputs(self):
        values = timeline_data()
        expected = temporal_reasoning_engine(*values)
        actual = temporal_reasoning_engine(*(iter(v) for v in values))
        self.assertEqual(actual.result_id, expected.result_id)

    def test_synthesis_fingerprint_preserves_one_shot_constraint_lineage(self):
        values = timeline_data()
        expected = synthesize_timeline(*values)
        actual = synthesize_timeline(*(iter(v) for v in values))
        self.assertEqual(actual.result_id, expected.result_id)
        self.assertEqual(len(json.loads(actual.inputs_json)['constraints']), 1)

    def test_temporal_conflict_reaches_existing_decision_contract(self):
        e, c, p, refs = timeline_data()
        c.append(Before('b', 'a', ('e',)))
        result = temporal_reasoning_engine(e, c, p, refs)
        decision = result.to_decision(decision_type='teaching_order', subject_id='lesson', question='Order?')
        self.assertEqual(result.status, 'CONFLICT')
        self.assertTrue(decision.requires_review)
        self.assertFalse(reasoning_integration_gate(stage_data(decision.requires_review)).passed)

    def test_temporal_axis_and_precision_safety(self):
        with self.assertRaises(ValueError):
            interval_relation(TimeSpan(1, 2), TimeSpan(1, 2, 'gregorian_day'))
        a, b = PreciseTime(1, 'year'), PreciseTime(1, 'day')
        self.assertEqual(compatible_precision(a, b), 'year')
        self.assertFalse(exact_comparison_allowed(a, b))

    def test_spatial_frames_units_and_transform_provenance(self):
        frame = SpatialFrame('map', 2, 'm', ('x', 'y'))
        source = SpatialPoint(frame, (1, 2), ('e',))
        for other in (replace(frame, frame_id='other'), replace(frame, unit='km'),
                      replace(frame, axis_names=('y', 'x'))):
            with self.subTest(other=other), self.assertRaises(ValueError):
                assert_compatible(source, SpatialPoint(other, (1, 2)))
        target = replace(frame, frame_id='map_km', unit='km')
        point = transform_point(source, target, FrameTransform('map', 'map_km', 'm_to_km', ('transform_e',)),
                                lambda xy: tuple(x / 1000 for x in xy))
        self.assertEqual(point.coordinates, (.001, .002))
        self.assertEqual(set(point.provenance_ids), {'e', 'transform_e', 'm_to_km'})

    def test_nonfinite_spatial_coordinates_are_rejected(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                SpatialPoint(SpatialFrame('map', 1, 'm', ('x',)), (value,), ('e',)).validate()

    def test_nonfinite_uncertainty_bounds_are_rejected(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                assess_uncertainty([UncertaintyComponent('u', 'MEASUREMENT', 'range', ('e',), value, value)])

    def test_transitive_invalidation_is_deterministic_through_cycles(self):
        evidence = {'d0': ('e',), 'd1': (), 'd2': ()}
        edges = [DecisionDependency('d0', 'd1'), DecisionDependency('d1', 'd2'), DecisionDependency('d2', 'd1')]
        a = propagate_invalidation(evidence, edges, ['e'])
        b = propagate_invalidation(dict(reversed(list(evidence.items()))), reversed(edges), ['e'])
        self.assertEqual(a, b)
        self.assertEqual(a[-1].propagation_path, ('d0', 'd1', 'd2'))

    def test_cycle_proposals_reference_actual_directed_edges(self):
        for edges in ([('a', 'c'), ('c', 'b'), ('b', 'a')], [('a', 'a')]):
            with self.subTest(edges=edges):
                nodes = sorted({n for pair in edges for n in pair})
                witnesses = find_canonical_cycles(nodes, edges)
                self.assertTrue(witnesses)
                for witness in witnesses:
                    self.assertLessEqual(set(witness.edges), set(edges))
                self.assertLessEqual(set(propose_cycle_breaks(witnesses)), set(edges))

    def test_cyclic_derived_lineage_cannot_pass_integration_gate(self):
        values = stage_data()
        values[1] = replace(values[1], parent_artifact_ids=('q',))
        self.assertFalse(reasoning_integration_gate(values).passed)

    def test_cross_family_conflict_preserves_opposition_and_evidence(self):
        values = [FamilyConstraint('temporal', 'p', 'SUPPORTS', 'RESOLVED', ('e',), .9),
                  FamilyConstraint('causal', 'p', 'OPPOSES', 'RESOLVED', ('opposing',), .8)]
        a, b = arbitrate_constraints(values), arbitrate_constraints(reversed(values))
        self.assertEqual(a, b)
        self.assertEqual(a.status, 'CONFLICT')
        self.assertEqual(set(a.evidence_ids), {'e', 'opposing'})
        self.assertTrue(a.requires_review)

    def test_replay_fingerprint_tracks_config_and_evidence_bindings(self):
        args = dict(input_hashes={'b': 'h2', 'a': 'h1'}, policy_version='p1', config_hash='c1',
                    decision_fingerprints={'d': 'dh'}, output_hashes={'o': 'oh'}, environment_fingerprint='env')
        a = build_replay_manifest(**args)
        b = build_replay_manifest(**dict(args, input_hashes={'a': 'h1', 'b': 'h2'}))
        self.assertEqual(a.fingerprint(), b.fingerprint())
        changed = build_replay_manifest(**dict(args, config_hash='c2'))
        self.assertEqual(compare_replay(a, changed), ('config_hash',))
        self.assertNotEqual(a.fingerprint(), changed.fingerprint())

    def test_fixture_gate_does_not_release_low_confidence_arbitration(self):
        fixture = RealBookReasoningFixture('synthetic_fixture', (SourceAnchor('e', 1, 'synthetic excerpt'),),
                    tuple(stage_data()), (FamilyConstraint('temporal', 'p', 'SUPPORTS', 'RESOLVED', ('e',), .4),))
        self.assertFalse(evaluate_realbook_fixture(fixture).passed)
