"""Synthetic source-to-inference-to-decision/IR contracts; NOT real-book E2E."""
from dataclasses import asdict, replace
import json
import unittest

from bie.bie_core.artifact_contracts import ArtifactEnvelope, ProducerIdentity, ProvenanceSource, ProvenanceSummary, LineageGraph
from bie.reasoning.decision_contracts import EvidenceRef, ReasoningDecisionGraph
from bie.reasoning.grounded_result import inference, GroundedResult
from bie.reasoning.map_reasoning import MapFrame, MapLocation, relative_position
from bie.reasoning.chronology_reasoning import Event, year, chronology
from bie.reasoning.event_order_reasoning import Before, event_order
from bie.reasoning.periodization_reasoning import Period, periodization
from bie.game_engine.contracts import Challenge, FeedbackPolicy

RUN = "00000000-0000-4000-8000-000000000001"


class GroundedIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.source = ArtifactEnvelope.create("source.document", "1.0.0", RUN, ProducerIdentity("synthetic.fixture", "1.0.0", "deterministic"), [], ProvenanceSummary(sources=[ProvenanceSource("synthetic:chapter", {"page": 1, "fixture": True})]), {}, {"map_scale_m": 100, "locations": {"A": [0, 0], "B": [3, 4]}, "events": [{"id": "A", "year": "1 BCE"}, {"id": "B", "year": "1 CE"}]})
        self.source.validate()
        self.refs = (EvidenceRef(self.source.artifact_id, "primary", .9),)
        self.ids = (self.source.artifact_id,)
        self.result = relative_position(MapFrame("map", 100, self.ids), MapLocation("A", 0, 0, self.ids), MapLocation("B", 3, 4, self.ids), self.refs)

    def test_existing_artifact_lineage(self):
        a=self.result.to_artifact(run_id=RUN,parents=(self.source,));g=LineageGraph([self.source,a]);g.validate();self.assertEqual(g.trace_to_sources(a.artifact_id),[self.source])

    def test_existing_rich_decision(self):
        d=self.result.to_decision(decision_type="representation_selection",subject_id="map",question="How are A and B positioned?")
        ReasoningDecisionGraph([d]).validate();self.assertEqual(d.evidence_refs,list(self.refs));self.assertFalse(d.requires_review)

    def test_game_challenge_grounding(self):
        d=self.result.to_decision(decision_type="game_revision_strategy",subject_id="map",question="What must the map challenge assess?")
        challenge=Challenge("C","Map distance","Use the scale to determine A–B distance","map_interaction","distance_m == 500",["select"],[],FeedbackPolicy("Correct","Check the scale"),1.0,.5,concept_refs=["map_scale"],reasoning_decision_refs=[d.decision_id],source_artifact_refs=[self.source.artifact_id])
        challenge.validate();self.assertEqual(challenge.reasoning_decision_refs,[self.result.result_id])

    def test_temporal_pipeline_shared_source(self):
        events=[Event("A","Earlier",year("1 BCE"),self.ids),Event("B","Later",year("1 CE"),self.ids)]
        a=chronology(events,self.refs);b=event_order(events,[Before("A","B",self.ids)],self.refs);c=periodization(events,[Period("P","Transition",0,2,self.ids)],self.refs)
        self.assertEqual(a.value["proven_before"],[["A","B"]]);self.assertEqual(b.value["linear_extension"],["A","B"])
        artifacts=[x.to_artifact(run_id=RUN,parents=(self.source,)) for x in (a,b,c)];LineageGraph([self.source,*artifacts]).validate()
        self.assertTrue(all(v["status"]=="ASSIGNED" for v in c.value["assignments"]))

    def test_unresolved_parent_rejected(self):
        with self.assertRaises(ValueError):self.result.to_artifact(run_id=RUN,parents=())

    def test_corrupted_parent_rejected(self):
        with self.assertRaises(ValueError):self.result.to_artifact(run_id=RUN,parents=(replace(self.source,content_hash="0"*64),))

    def test_low_confidence_escalates(self):
        r=inference("T","operation",{}, {"x":1},(EvidenceRef("e","primary",.2),))
        d=r.to_decision(decision_type="teaching_order",subject_id="x",question="Order?");self.assertTrue(d.requires_review);d.validate(critical=True)

    def test_conflict_cannot_auto_produce(self):
        r=inference("T","operation",{}, {"x":None},self.refs,status="CONFLICT")
        self.assertTrue(r.to_decision(decision_type="evidence_arbitration",subject_id="x",question="Resolve?").requires_review)

    def test_canonical_roundtrip(self):
        data=asdict(self.result);data["evidence_refs"]=tuple(EvidenceRef(**x) for x in data["evidence_refs"])
        copy=GroundedResult(**data);self.assertEqual(copy.result_id,self.result.result_id);json.dumps(copy.to_dict(),allow_nan=False)

    def test_output_mutation_does_not_change_result(self):
        id=self.result.result_id;v=self.result.value;v["distance_m"]=0;self.assertEqual(self.result.result_id,id);self.assertEqual(self.result.value["distance_m"],500)

    def test_bad_evidence(self):
        for refs in [(),(EvidenceRef(" ","primary",.9),),(EvidenceRef("e","primary",float("nan")),),(EvidenceRef("e","primary",.9),EvidenceRef("e","primary",.8))]:
            with self.subTest(refs=refs),self.assertRaises(ValueError):inference("T","operation",{}, {},refs)

    def test_nonfinite_payload(self):
        with self.assertRaises(ValueError):inference("T","operation",{}, {"x":float("nan")},self.refs)

    def test_legacy_module_identity(self):
        from app.bie.reasoning.map_reasoning import MapLocation as OldLocation
        from app.bie.enterprise.run_state import RunStateMachine as OldState
        from bie.infrastructure.run_state import RunStateMachine
        self.assertIs(OldLocation,MapLocation);self.assertIs(OldState,RunStateMachine)
