import unittest
from dataclasses import replace
from bie.bie_core.artifact_contracts import (
    ArtifactEnvelope, ArtifactContractError, LineageGraph,
    ProducerIdentity, ProvenanceSummary, ProvenanceSource, RunContext
)

class ArtifactContractTests(unittest.TestCase):
    def setUp(self):
        self.run = RunContext.new(
            product="BIE",
            product_version="1.0.0",
            source_ids=["book-1"],
            configuration={"fps":30},
            policy_id="enterprise-default",
            environment_fingerprint="test-env",
        )
        self.prod = ProducerIdentity("document_ingestor","1.0.0","deterministic")
        self.prov = ProvenanceSummary(
            sources=[ProvenanceSource("book-1",{"page":1})]
        )

    def test_round_trip_stable_identity_material(self):
        a = ArtifactEnvelope.create("source.document","1.0.0",self.run.run_id,self.prod,[],self.prov,{},{"title":"Book"})
        a.validate()
        self.assertEqual(a.content_hash, a.recompute_content_hash())

    def test_payload_change_changes_identity(self):
        a = ArtifactEnvelope.create("source.document","1.0.0",self.run.run_id,self.prod,[],self.prov,{},{"title":"Book"})
        b = ArtifactEnvelope.create("source.document","1.0.0",self.run.run_id,self.prod,[],self.prov,{},{"title":"Book 2"})
        self.assertNotEqual(a.artifact_id,b.artifact_id)

    def test_non_source_requires_parent(self):
        a = ArtifactEnvelope.create("knowledge.concept","1.0.0",self.run.run_id,self.prod,[],self.prov,{},{"name":"Charge"})
        with self.assertRaises(ArtifactContractError):
            a.validate()

    def test_inferred_requires_reason_and_confidence(self):
        bad = ProvenanceSummary(sources=[], inferred=True)
        a = ArtifactEnvelope.create("source.document","1.0.0",self.run.run_id,self.prod,[],bad,{},{"x":1})
        with self.assertRaises(ArtifactContractError):
            a.validate()

    def test_lineage_traces_to_source(self):
        source = ArtifactEnvelope.create("source.document","1.0.0",self.run.run_id,self.prod,[],self.prov,{},{"title":"Book"})
        concept = ArtifactEnvelope.create("knowledge.concept","1.0.0",self.run.run_id,self.prod,[source.to_ref()],self.prov,{},{"name":"Charge"})
        graph = LineageGraph([source,concept])
        graph.validate()
        self.assertEqual([x.artifact_id for x in graph.trace_to_sources(concept.artifact_id)],[source.artifact_id])

    def test_hash_tamper_fails(self):
        a = ArtifactEnvelope.create("source.document","1.0.0",self.run.run_id,self.prod,[],self.prov,{},{"title":"Book"})
        tampered = replace(a, payload={"title":"Tampered"})
        with self.assertRaises(ArtifactContractError):
            tampered.validate()

if __name__ == "__main__":
    unittest.main()
