"""Post-TEMP-003 quality gate. Synthetic oracles, not real-book acceptance.

The finite oracles enumerate outcomes independently of the production graph,
interval and route algorithms. Subcases are not counted as separate unit tests.
"""
from datetime import date
from itertools import permutations, product
import unittest

from bie.bie_core.artifact_contracts import (
    ArtifactEnvelope, LineageGraph, ProducerIdentity, ProvenanceSource,
    ProvenanceSummary,
)
from bie.reasoning.chronology_reasoning import Event, TimeSpan, chronology, relation
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.event_order_reasoning import Before, event_order
from bie.reasoning.geometry_reasoning import (
    Point, point_in_polygon, segment_relation, triangle_properties,
)
from bie.reasoning.map_reasoning import MapEdge, MapFrame, MapLocation, shortest_route
from bie.reasoning.periodization_reasoning import Period, periodization

REFS = (EvidenceRef("source:1", "primary", .95), EvidenceRef("source:2", "primary", .9))
IDS = ("source:1",)
LAST_DAY = date.max.toordinal()


def event(name, lo, hi, axis="historical_year"):
    return Event(name, name, TimeSpan(lo, hi, axis), IDS)


def point(name, x, y, refs=IDS):
    return Point(name, x, y, refs)


class GeometryQualityTests(unittest.TestCase):
    def setUp(self):
        self.square = [point("A", 0, 0), point("B", 4, 0),
                       point("C", 4, 4), point("D", 0, 4)]

    def test_one_shot_evidence_preserves_triangle_result(self):
        vertices = [point("A", 0, 0), point("B", 3, 0), point("C", 0, 4)]
        expected = triangle_properties(vertices, REFS, frame_id="f")
        actual = triangle_properties(iter(vertices), iter(REFS), frame_id="f")
        self.assertEqual(actual.result_id, expected.result_id)
        self.assertEqual(actual.value["area"], 6)

    def test_query_cannot_redefine_polygon_vertex(self):
        with self.assertRaisesRegex(ValueError, "Conflicting coordinates"):
            point_in_polygon(point("A", 2, 2), self.square, REFS, frame_id="f")

    def test_query_can_reuse_matching_vertex_with_additional_source(self):
        result = point_in_polygon(point("A", 0, 0, ("source:2",)),
                                  self.square, REFS, frame_id="f")
        self.assertEqual(result.value["relation"], "boundary")
        self.assertEqual(result.evidence_refs, REFS)

    def test_shared_segment_endpoint_can_have_additional_source(self):
        result = segment_relation(point("A", 0, 0), point("B", 1, 1),
                                  point("A", 0, 0, ("source:2",)), point("C", 1, 0),
                                  REFS, frame_id="f")
        self.assertEqual(result.value["relation"], "touching")
        self.assertEqual(result.evidence_refs, REFS)

    def test_shared_segment_endpoint_rejects_conflicting_coordinates(self):
        with self.assertRaisesRegex(ValueError, "Conflicting coordinates"):
            segment_relation(point("A", 0, 0), point("B", 1, 1),
                             point("A", 2, 0), point("C", 3, 0), REFS, frame_id="f")


class EventOrderQualityTests(unittest.TestCase):
    def order(self, events):
        return event_order(events, [Before("A", "B", IDS)], REFS)

    def test_open_lower_bound_cannot_precede_calendar_domain(self):
        result = self.order([event(x, None, 1, "gregorian_day") for x in "AB"])
        self.assertEqual(result.status, "CONFLICT")
        self.assertEqual(result.value["linear_extension"], [])
        self.assertTrue(result.requires_review)

    def test_open_upper_bound_cannot_exceed_calendar_domain(self):
        result = self.order([event(x, LAST_DAY, None, "gregorian_day") for x in "AB"])
        self.assertEqual(result.status, "CONFLICT")
        self.assertEqual(result.value["linear_extension"], [])

    def test_first_two_calendar_days_allow_strict_order(self):
        result = self.order([event(x, None, 2, "gregorian_day") for x in "AB"])
        self.assertEqual(result.status, "RESOLVED")
        self.assertEqual(result.value["linear_extension"], ["A", "B"])

    def test_last_two_calendar_days_allow_strict_order(self):
        result = self.order([event(x, LAST_DAY - 1, None, "gregorian_day") for x in "AB"])
        self.assertEqual(result.status, "RESOLVED")

    def test_historical_year_axis_keeps_its_open_bounds(self):
        for lo, hi in ((None, 1), (LAST_DAY, None)):
            with self.subTest(lo=lo, hi=hi):
                self.assertEqual(self.order([event(x, lo, hi) for x in "AB"]).status,
                                 "RESOLVED")

    def test_small_orders_against_exhaustive_date_assignments(self):
        # 64 interval combinations x 64 directed graphs = 4,096 cases.
        names = "ABC"
        possible_edges = tuple(permutations(range(3), 2))
        bounds = ((0, 0), (0, 1), (1, 2), (2, 2))
        for spans in product(bounds, repeat=3):
            assignments = tuple(product(*(range(lo, hi + 1) for lo, hi in spans)))
            events = [event(name, *span) for name, span in zip(names, spans)]
            for mask in range(1 << len(possible_edges)):
                edges = [edge for bit, edge in enumerate(possible_edges) if mask & (1 << bit)]
                feasible = any(all(times[a] < times[b] for a, b in edges)
                               for times in assignments)
                result = event_order(events, [Before(names[a], names[b], IDS) for a, b in edges], REFS)
                self.assertEqual(result.status != "CONFLICT", feasible, (spans, edges))
                if feasible:
                    positions = {name: i for i, name in enumerate(result.value["linear_extension"])}
                    self.assertTrue(all(positions[names[a]] < positions[names[b]] for a, b in edges))


class PeriodizationQualityTests(unittest.TestCase):
    def test_final_calendar_day_has_a_half_open_period(self):
        result = periodization([event("E", LAST_DAY, LAST_DAY, "gregorian_day")],
                               [Period("P", "Final day", LAST_DAY, LAST_DAY + 1, IDS,
                                       axis="gregorian_day")], REFS)
        self.assertEqual(result.status, "RESOLVED")
        self.assertEqual(result.value["assignments"][0]["definite_period_ids"], ["P"])

    def test_final_calendar_days_allow_uncertain_membership(self):
        result = periodization([event("E", LAST_DAY - 1, LAST_DAY, "gregorian_day")],
                               [Period("P", "Final two days", LAST_DAY - 1, LAST_DAY + 1, IDS,
                                       axis="gregorian_day")], REFS)
        self.assertEqual(result.value["assignments"][0]["status"], "ASSIGNED")

    def test_exclusive_end_does_not_extend_supported_calendar(self):
        for start, end in ((LAST_DAY, LAST_DAY + 2), (0, 2), (1, None), (True, 2)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                periodization([event("E", 1, 1, "gregorian_day")],
                              [Period("P", "Invalid", start, end, IDS, axis="gregorian_day")], REFS)

    def test_membership_against_enumerated_possible_dates(self):
        periods = [Period("P", "Before transition", -2, 0, IDS),
                   Period("Q", "After transition", 0, 2, IDS)]
        for lo in range(-3, 4):
            for hi in range(lo, 4):
                dates = set(range(lo, hi + 1))
                actual = periodization([event("E", lo, hi)], periods, REFS).value["assignments"][0]
                expected_possible, expected_definite = [], []
                for p in periods:
                    period_dates = set(range(p.start, p.end))
                    if dates & period_dates: expected_possible.append(p.period_id)
                    if dates <= period_dates: expected_definite.append(p.period_id)
                self.assertEqual(actual["possible_period_ids"], expected_possible)
                self.assertEqual(actual["definite_period_ids"], expected_definite)


class ChronologyQualityTests(unittest.TestCase):
    def test_relations_against_enumerated_possible_dates(self):
        spans = [TimeSpan(lo, hi) for lo in range(3) for hi in range(lo, 3)]
        for a, b in product(spans, repeat=2):
            pairs = tuple(product(range(a.earliest, a.latest + 1),
                                  range(b.earliest, b.latest + 1)))
            expected = ("before" if all(x < y for x, y in pairs) else
                        "after" if all(x > y for x, y in pairs) else
                        "simultaneous" if all(x == y for x, y in pairs) else "indeterminate")
            self.assertEqual(relation(a, b), expected)


class MapQualityTests(unittest.TestCase):
    def test_routes_against_all_simple_paths_in_small_graphs(self):
        # 256 graphs, with cycles, unreachable goals and equal-cost routes.
        names = "ABCD"
        candidates = (("A", "B", 2), ("A", "C", 1), ("B", "C", 1), ("C", "B", 1),
                      ("B", "D", 2), ("C", "D", 3), ("D", "A", 1), ("A", "D", 5))
        frame = MapFrame("f", 1, IDS)
        locations = [MapLocation(name, i, 0, IDS) for i, name in enumerate(names)]
        for mask in range(1 << len(candidates)):
            edges = [MapEdge(a + b, a, b, cost, IDS) for bit, (a, b, cost) in enumerate(candidates)
                     if mask & (1 << bit)]
            costs = {(e.source, e.target): e.distance_m for e in edges}
            routes = []
            for length in range(3):
                for middle in permutations("BC", length):
                    nodes = ("A", *middle, "D")
                    pairs = tuple(zip(nodes, nodes[1:]))
                    if all(pair in costs for pair in pairs):
                        routes.append((sum(costs[pair] for pair in pairs), nodes,
                                       tuple(a + b for a, b in pairs)))
            result = shortest_route(frame, locations, edges, "A", "D", REFS)
            if not routes:
                self.assertEqual(result.status, "UNREACHABLE")
            else:
                cost, nodes, used = min(routes)
                self.assertEqual(result.value, {"distance_m": cost, "node_ids": list(nodes),
                                                "edge_ids": list(used)})


class QualityIntegrationTests(unittest.TestCase):
    def test_calendar_domain_conflict_reaches_existing_review_gate(self):
        run = "00000000-0000-4000-8000-000000000002"
        source = ArtifactEnvelope.create(
            "source.document", "1.0.0", run,
            ProducerIdentity("synthetic.quality.fixture", "1.0.0", "deterministic"), [],
            ProvenanceSummary(sources=[ProvenanceSource("synthetic:calendar-boundary",
                                                       {"page": 1, "fixture": True})]), {},
            {"events": ["A", "B"], "latest_day": "0001-01-01", "assertion": "A before B"})
        ids = (source.artifact_id,)
        refs = (EvidenceRef(source.artifact_id, "primary", .9),)
        events = [Event(x, x, TimeSpan(None, 1, "gregorian_day"), ids) for x in "AB"]
        result = event_order(events, [Before("A", "B", ids)], refs)
        decision = result.to_decision(decision_type="teaching_order", subject_id="timeline",
                                      question="Can this chronology be published?")
        self.assertTrue(decision.requires_review)
        artifact = result.to_artifact(run_id=run, parents=(source,))
        graph = LineageGraph([source, artifact])
        graph.validate()
        self.assertEqual(graph.trace_to_sources(artifact.artifact_id), [source])
        self.assertEqual(artifact.payload["status"], "CONFLICT")


if __name__ == "__main__":
    unittest.main()
