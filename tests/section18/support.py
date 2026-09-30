from __future__ import annotations

import gc
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "productization" / "document_intelligence"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(FIXTURES) not in sys.path:
    sys.path.insert(0, str(FIXTURES))

from apps.api.main import app
from bie.app_product.operator_service import OperatorJobService
from structural_pdf_fixtures import hierarchy_pdf_with_outline


class Section18Case(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pdf = hierarchy_pdf_with_outline()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"BIE_DATA_ROOT": str(self.root)})
        self.env.start()
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self):
        self.env.stop()
        gc.collect()
        self.temp.cleanup()

    def service(self) -> OperatorJobService:
        return OperatorJobService(self.root)

    def create(self, data=None, key="section18-case-1"):
        response = self.client.post(
            "/v1/app/runs",
            content=self.pdf if data is None else data,
            headers={"content-type": "application/pdf", "Idempotency-Key": key},
        )
        self.assertEqual(response.status_code, 202, response.text)
        return response.json()["run"]

    def register_json_artifact(
        self,
        job_id: str,
        artifact_id: str,
        artifact_type: str,
        payload: object,
    ):
        service = self.service()
        try:
            service._register_blob(
                artifact_id,
                artifact_type,
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
                job_id,
                parents=[],
                metadata={"section18_fixture": True},
            )
        finally:
            service.close()
