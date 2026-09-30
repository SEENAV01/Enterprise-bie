from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from batch001_support import FIXTURE_DIR
if str(FIXTURE_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(FIXTURE_DIR))
from structural_pdf_fixtures import hierarchy_pdf_with_outline

from apps.api.section18_dev_app import app
from bie.product_app_v1.context import OperatorContext


class Batch001ApiIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {
            "BIE_DATA_ROOT": str(self.root),
            "BIE_SECTION18_LOCAL_OPERATOR": "1",
        })
        self.env.start()
        self.client = TestClient(app, raise_server_exceptions=False)
        self.pdf = hierarchy_pdf_with_outline()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def create(self, key):
        response = self.client.post("/v1/operator/runs", json={"create_key": key})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def import_pdf(self, run_id, payload=None):
        return self.client.post(
            f"/v1/operator/runs/{run_id}/source",
            content=self.pdf if payload is None else payload,
            headers={"content-type": "application/pdf", "x-source-name": "Physics.pdf"},
        )

    def test_operator_routes_are_disabled_by_default(self):
        with patch.dict(os.environ, {"BIE_SECTION18_LOCAL_OPERATOR": "0"}):
            response = self.client.post("/v1/operator/runs", json={"create_key": "disabled"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "section18_operator_disabled")

    def test_create_import_status_real_flow(self):
        run = self.create("api-flow")
        imported = self.import_pdf(run["run_id"])
        self.assertEqual(imported.status_code, 202)
        status = self.client.get(f"/v1/operator/runs/{run['run_id']}")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["state"], "READY")
        self.assertEqual(status.json()["queue_state"], "READY")

    def test_source_validation_html_executes_real_validator(self):
        response = self.client.post(
            "/v1/operator/source-validation",
            content=self.pdf,
            headers={"content-type": "application/pdf", "x-source-name": "<Book>.pdf"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Basic transport validation only", response.text)
        self.assertIn("&lt;Book&gt;.pdf", response.text)

    def test_status_view_is_accessible_html(self):
        run = self.create("api-status-view")
        self.import_pdf(run["run_id"])
        response = self.client.get(f"/v1/operator/runs/{run['run_id']}/status-view")
        self.assertEqual(response.status_code, 200)
        self.assertIn("aria-labelledby='run-status-title'", response.text)
        self.assertIn("No fabricated percentage", response.text)

    def test_timeline_view_reads_real_persisted_events(self):
        run = self.create("api-timeline")
        self.import_pdf(run["run_id"])
        response = self.client.get(f"/v1/operator/runs/{run['run_id']}/timeline")
        self.assertEqual(response.status_code, 200)
        origins = {e["origin"] for e in response.json()["events"]}
        self.assertIn("operator", origins)
        self.assertIn("canonical_queue", origins)

    def test_failure_view_uses_real_failure_evidence(self):
        run = self.create("api-failure")
        self.import_pdf(run["run_id"], b"%PDF-1.7\nmalformed")
        context = OperatorContext(self.root)
        service = context.job_service()
        try:
            self.assertEqual(service.run_once("api-failure-worker").outcome, "FAILED")
        finally:
            service.close()
        self.client.get(f"/v1/operator/runs/{run['run_id']}")
        response = self.client.get(f"/v1/operator/runs/{run['run_id']}/failure")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["failure"]["diagnostic_code"], "pdf_inspection_failed")

    def test_retry_endpoint_creates_attempt_two(self):
        run = self.create("api-retry")
        self.import_pdf(run["run_id"], b"%PDF-1.7\nmalformed")
        context = OperatorContext(self.root)
        service = context.job_service()
        try:
            service.run_once("api-retry-worker")
        finally:
            service.close()
        self.client.get(f"/v1/operator/runs/{run['run_id']}")
        response = self.client.post(f"/v1/operator/runs/{run['run_id']}/retry")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["run"]["attempt"], 2)

    def test_pause_resume_routes_control_real_queue(self):
        run = self.create("api-control")
        imported = self.import_pdf(run["run_id"]).json()
        self.assertEqual(self.client.post(f"/v1/operator/runs/{run['run_id']}/pause").json()["state"], "PAUSED")
        context = OperatorContext(self.root)
        service = context.job_service()
        try:
            task = service.queue.get("inspect-" + imported["canonical_job"]["job_id"][4:])
            self.assertEqual(task.state, "DEAD_LETTER")
        finally:
            service.close()
        self.assertEqual(self.client.post(f"/v1/operator/runs/{run['run_id']}/resume").json()["state"], "READY")

    def test_cancel_route_is_terminal(self):
        run = self.create("api-cancel")
        self.import_pdf(run["run_id"])
        response = self.client.post(f"/v1/operator/runs/{run['run_id']}/cancel")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["state"], "CANCELLED")
        retry = self.client.post(f"/v1/operator/runs/{run['run_id']}/resume")
        self.assertEqual(retry.status_code, 409)

    def test_concept_graph_endpoint_renders_real_graph_contract(self):
        graph = {
            "nodes": {
                "c1": {"concept_id": "c1", "label": "Force", "source_refs": ["src:p1"]},
                "c2": {"concept_id": "c2", "label": "Motion", "source_refs": ["src:p2"]},
            },
            "edges": [
                {"source": "c1", "target": "c2", "type": "causes", "confidence": 0.9}
            ],
        }
        response = self.client.post("/v1/operator/viewers/concept-graph", json={"graph": graph})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Concept graph", response.text)
        self.assertIn("src:p1", response.text)

    def test_prerequisite_graph_endpoint_renders_dependency_order(self):
        response = self.client.post("/v1/operator/viewers/prerequisite-graph", json={
            "nodes": ["charge", "field", "potential"],
            "edges": [
                {"prerequisite": "charge", "dependent": "field"},
                {"prerequisite": "field", "dependent": "potential"},
            ],
            "labels": {"charge": "Electric charge"},
            "source_refs": {"charge": ["src:p1"]},
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Prerequisite graph", response.text)
        self.assertIn("Teaching order:", response.text)

    def test_invalid_concept_graph_returns_safe_400(self):
        response = self.client.post("/v1/operator/viewers/concept-graph", json={
            "graph": {"nodes": {"c1": {"label": "x"}}, "edges": [{"source": "c1", "target": "missing", "type": "bad"}]}
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_concept_graph")

    def test_invalid_prerequisite_cycle_returns_safe_400(self):
        response = self.client.post("/v1/operator/viewers/prerequisite-graph", json={
            "nodes": ["a", "b"],
            "edges": [
                {"prerequisite": "a", "dependent": "b"},
                {"prerequisite": "b", "dependent": "a"},
            ],
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("cycle", response.json()["error"]["code"])

    def test_unknown_control_action_is_404(self):
        run = self.create("api-unknown-control")
        response = self.client.post(f"/v1/operator/runs/{run['run_id']}/explode")
        self.assertEqual(response.status_code, 404)

    def test_api_does_not_claim_authentication_or_product_acceptance(self):
        # The bounded development router is explicit opt-in and has no product-acceptance endpoint.
        paths = self.client.get("/openapi.json").json()["paths"]
        self.assertIn("/v1/operator/runs", paths)
        serialized = str(paths).lower()
        self.assertNotIn("product_accepted", serialized)
        self.assertNotIn("release_authorized", serialized)

    def test_prerequisite_endpoint_rejects_non_mapping_edges(self):
        response = self.client.post("/v1/operator/viewers/prerequisite-graph", json={
            "nodes": ["a", "b"],
            "edges": ["not-an-edge"],
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "prerequisite_edge_must_be_mapping")


if __name__ == "__main__":
    unittest.main()
