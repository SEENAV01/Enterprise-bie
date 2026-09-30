from __future__ import annotations

import json
from unittest.mock import patch

from bie.app_product.graph_views import GraphViewError, GraphViewService
from bie.infrastructure.artifact_store import BlobRef

from tests.section18.support import Section18Case


class GraphViewerTests(Section18Case):
    def graph_payload(self):
        return {
            "nodes": {
                "charge": {
                    "label": "Electric charge",
                    "node_type": "concept",
                    "source_refs": ["source-anchor-1"],
                },
                "force": {
                    "label": "Electrostatic force",
                    "node_type": "concept",
                    "source_refs": ["source-anchor-2"],
                },
                "field": {
                    "label": "Electric field",
                    "node_type": "concept",
                    "source_refs": ["source-anchor-3"],
                },
            },
            "edges": [
                {
                    "id": "related-1",
                    "source": "charge",
                    "target": "force",
                    "type": "RELATED",
                    "source_refs": ["claim-1"],
                },
                {
                    "id": "prereq-1",
                    "source": "charge",
                    "target": "field",
                    "type": "PREREQUISITE",
                    "source_refs": ["claim-2"],
                },
            ],
        }

    def test_001_concept_graph_reads_actual_persisted_artifact(self):
        run = self.create()
        self.register_json_artifact(run["job_id"], "graph-1", "knowledge.graph", self.graph_payload())
        service = self.service()
        try:
            view = GraphViewService(service.persistence, service.cas).view(
                run["job_id"], "graph-1", "concept"
            )
        finally:
            service.close()
        self.assertEqual(view["node_count"], 3)
        self.assertEqual(view["edge_count"], 2)
        self.assertEqual(view["artifact_id"], "graph-1")
        self.assertFalse(view["product_accepted"])

    def test_002_concept_graph_api_exposes_only_normalized_view(self):
        run = self.create()
        self.register_json_artifact(run["job_id"], "graph-2", "knowledge.graph", self.graph_payload())
        response = self.client.get(
            "/v1/app/runs/" + run["job_id"] + "/graphs/concept",
            params={"artifact_id": "graph-2"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        value = response.json()
        self.assertEqual(value["kind"], "concept")
        self.assertEqual(value["node_count"], 3)
        self.assertNotIn("payload", value)

    def test_003_prerequisite_graph_filters_relationships(self):
        run = self.create()
        self.register_json_artifact(run["job_id"], "graph-3", "knowledge.graph", self.graph_payload())
        value = self.client.get(
            "/v1/app/runs/" + run["job_id"] + "/graphs/prerequisite",
            params={"artifact_id": "graph-3"},
        ).json()
        self.assertEqual(value["edge_count"], 1)
        self.assertEqual(value["edges"][0]["relation"], "PREREQUISITE")
        self.assertEqual(value["edges"][0]["source"], "charge")
        self.assertEqual(value["edges"][0]["target"], "field")

    def test_004_prerequisite_view_reads_teaching_context_shape(self):
        run = self.create()
        payload = {
            "knowledge_graph": {"nodes": self.graph_payload()["nodes"], "edges": []},
            "prerequisites": [
                {
                    "prerequisite_id": "charge",
                    "concept_id": "field",
                    "evidence_ids": ["evidence-1"],
                }
            ],
        }
        self.register_json_artifact(run["job_id"], "context-1", "pedagogy.teaching_context", payload)
        value = self.client.get(
            "/v1/app/runs/" + run["job_id"] + "/graphs/prerequisite",
            params={"artifact_id": "context-1"},
        ).json()
        self.assertEqual(value["edge_count"], 1)
        self.assertEqual(value["edges"][0]["source_refs"], ["evidence-1"])

    def test_005_cross_run_artifact_is_not_disclosed(self):
        first = self.create(key="graph-run-one")
        second = self.create(key="graph-run-two")
        self.register_json_artifact(first["job_id"], "private-graph", "knowledge.graph", self.graph_payload())
        response = self.client.get(
            "/v1/app/runs/" + second["job_id"] + "/graphs/concept",
            params={"artifact_id": "private-graph"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "graph_artifact_not_found")

    def test_006_missing_artifact_is_safe_404(self):
        run = self.create()
        response = self.client.get(
            "/v1/app/runs/" + run["job_id"] + "/graphs/concept",
            params={"artifact_id": "does-not-exist"},
        )
        self.assertEqual(response.status_code, 404)

    def test_007_malformed_artifact_json_is_rejected(self):
        run = self.create()
        service = self.service()
        try:
            service._register_blob(
                "bad-json", "knowledge.graph", b"{not-json", run["job_id"],
                parents=[], metadata={"section18_fixture": True},
            )
        finally:
            service.close()
        response = self.client.get(
            "/v1/app/runs/" + run["job_id"] + "/graphs/concept",
            params={"artifact_id": "bad-json"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "artifact_json_invalid")

    def test_008_edge_to_missing_node_is_rejected(self):
        run = self.create()
        payload = self.graph_payload()
        payload["edges"].append({
            "source": "charge",
            "target": "invented",
            "type": "RELATED",
        })
        self.register_json_artifact(run["job_id"], "broken-edge", "knowledge.graph", payload)
        response = self.client.get(
            "/v1/app/runs/" + run["job_id"] + "/graphs/concept",
            params={"artifact_id": "broken-edge"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "graph_edge_endpoint_missing")

    def test_009_source_refs_are_preserved_for_navigation(self):
        run = self.create()
        self.register_json_artifact(run["job_id"], "graph-refs", "knowledge.graph", self.graph_payload())
        value = self.client.get(
            "/v1/app/runs/" + run["job_id"] + "/graphs/concept",
            params={"artifact_id": "graph-refs"},
        ).json()
        by_id = {node["id"]: node for node in value["nodes"]}
        self.assertEqual(by_id["charge"]["source_refs"], ["source-anchor-1"])
        self.assertEqual(value["edges"][0]["source_refs"], ["claim-1"])

    def test_010_service_uses_cas_integrity_read(self):
        run = self.create()
        self.register_json_artifact(run["job_id"], "graph-cas", "knowledge.graph", self.graph_payload())
        service = self.service()
        try:
            with patch.object(service.cas, "get_bytes", wraps=service.cas.get_bytes) as read:
                GraphViewService(service.persistence, service.cas).view(
                    run["job_id"], "graph-cas", "concept"
                )
            read.assert_called_once()
        finally:
            service.close()

    def test_011_empty_graph_is_truthful_not_fabricated(self):
        run = self.create()
        self.register_json_artifact(run["job_id"], "empty-graph", "knowledge.graph", {"nodes": {}, "edges": []})
        value = self.client.get(
            "/v1/app/runs/" + run["job_id"] + "/graphs/concept",
            params={"artifact_id": "empty-graph"},
        ).json()
        self.assertTrue(value["empty"])
        self.assertEqual(value["node_count"], 0)
        self.assertEqual(value["edge_count"], 0)

    def test_012_unsupported_graph_kind_is_rejected(self):
        run = self.create()
        self.register_json_artifact(run["job_id"], "graph-kind", "knowledge.graph", self.graph_payload())
        response = self.client.get(
            "/v1/app/runs/" + run["job_id"] + "/graphs/reasoning",
            params={"artifact_id": "graph-kind"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "unsupported_graph_kind")


if __name__ == "__main__":
    import unittest
    unittest.main()
