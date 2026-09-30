from __future__ import annotations

from pathlib import Path
import json
import os
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "productization" / "document_intelligence"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(FIXTURE_DIR) not in sys.path:
    sys.path.insert(0, str(FIXTURE_DIR))

from structural_pdf_fixtures import hierarchy_pdf_with_outline

from bie.product_app_v1.context import OperatorContext
from bie.product_app_v1.run_create import create_run
from bie.product_app_v1.run_status import RunStatusService
from bie.product_app_v1.source_import import SourceImportService


class OperatorCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.context = OperatorContext(self.root)
        self.pdf = hierarchy_pdf_with_outline()

    def tearDown(self):
        self.temp.cleanup()

    def create(self, key="run-key"):
        return create_run(self.context.operator, key)

    def imported(self, key="run-key", payload=None, name="Book.pdf"):
        run = self.create(key)
        result = SourceImportService(self.context).import_pdf(
            run["run_id"],
            self.pdf if payload is None else payload,
            display_name=name,
        )
        return result

    def run_native_once(self):
        service = self.context.job_service()
        try:
            return service.run_once("section18-test-worker")
        finally:
            service.close()

    def observe(self, run_id):
        return RunStatusService(self.context).status(run_id)

    def fail_run(self, key="failed-run"):
        result = self.imported(key, payload=b"%PDF-1.7\nmalformed")
        run_id = result["run"]["run_id"]
        outcome = self.run_native_once()
        self.assertEqual(outcome.outcome, "FAILED")
        status = self.observe(run_id)
        self.assertEqual(status["state"], "FAILED")
        return run_id

    def complete_run(self, key="complete-run"):
        result = self.imported(key)
        run_id = result["run"]["run_id"]
        outcome = self.run_native_once()
        self.assertEqual(outcome.outcome, "ACKED")
        status = self.observe(run_id)
        self.assertEqual(status["state"], "SUCCEEDED")
        return run_id
