from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import socket
import sys
import threading
import time
import unittest
from unittest.mock import patch
from urllib.request import urlopen

from fastapi.testclient import TestClient
from pypdf import PdfWriter
import uvicorn

ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = ROOT / "tests" / "productization" / "document_intelligence"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(FIXTURE_DIR) not in sys.path:
    sys.path.insert(0, str(FIXTURE_DIR))

import apps.api.main as api_module
from apps.api.main import app
from bie.document_intelligence.real_pdf_toc_runtime import inspect_real_pdf_toc
from structural_pdf_fixtures import hierarchy_pdf_with_outline


class PdfInspectionApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = hierarchy_pdf_with_outline()
        cls.direct = inspect_real_pdf_toc(cls.data).to_safe_dict()
        cls.client = TestClient(app, raise_server_exceptions=False)

    def post_pdf(self, data: bytes | None = None, **kwargs):
        return self.client.post(
            "/v1/documents/inspect",
            content=self.data if data is None else data,
            headers={"content-type": "application/pdf"},
            **kwargs,
        )

    def test_01_app_imports_successfully(self):
        self.assertIs(api_module.app, app)

    def test_02_healthz_is_exact_and_truthful(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "bie-api", "api_version": "v1"},
        )

    def test_03_capabilities_report_local_persistent_jobs_truthfully(self):
        response = self.client.get("/v1/capabilities")
        self.assertEqual(response.status_code, 200)
        capabilities = response.json()
        self.assertFalse(capabilities["stateless"])
        self.assertTrue(capabilities["persistence"])
        self.assertFalse(capabilities["authentication"])
        self.assertTrue(capabilities["async_jobs"])
        self.assertFalse(capabilities["product_accepted"])

    def test_04_wrong_content_type_is_rejected(self):
        response = self.client.post(
            "/v1/documents/inspect",
            content=self.data,
            headers={"content-type": "application/octet-stream"},
        )
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.json()["error"]["code"], "unsupported_media_type")

    def test_05_content_type_parameters_are_allowed(self):
        response = self.client.post(
            "/v1/documents/inspect",
            content=self.data,
            headers={"content-type": "application/pdf; charset=binary"},
        )
        self.assertEqual(response.status_code, 200)

    def test_06_empty_body_is_rejected(self):
        response = self.post_pdf(b"")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "empty_body")

    def test_07_bounded_reader_rejects_oversize_payload(self):
        with patch.object(api_module, "MAX_PDF_BYTES", 8):
            response = self.post_pdf(b"%PDF-1234")
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["error"]["code"], "payload_too_large")

    def test_08_malformed_pdf_returns_safe_422(self):
        response = self.post_pdf(b"%PDF-1.7\nmalformed")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "pdf_inspection_failed",
                    "message": "PDF inspection failed",
                }
            },
        )

    def test_09_encrypted_pdf_returns_safe_422(self):
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.encrypt("api-password")
        output = BytesIO()
        writer.write(output)
        response = self.post_pdf(output.getvalue())
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "pdf_inspection_failed")

    def test_10_valid_structural_pdf_returns_200(self):
        self.assertEqual(self.post_pdf().status_code, 200)

    def test_11_success_response_has_schema_version(self):
        self.assertEqual(self.post_pdf().json()["api_schema_version"], "1.0")

    def test_12_success_response_is_exact_task_016_safe_result(self):
        self.assertEqual(self.post_pdf().json()["result"], self.direct)

    def test_13_source_hash_matches_direct_task_016_result(self):
        result = self.post_pdf().json()["result"]
        self.assertEqual(result["source_hash"], self.direct["source_hash"])

    def test_14_upstream_task_016_runtime_is_invoked(self):
        with patch.object(
            api_module,
            "inspect_real_pdf_toc",
            wraps=inspect_real_pdf_toc,
        ) as inspect:
            response = self.post_pdf()
        self.assertEqual(response.status_code, 200)
        inspect.assert_called_once_with(self.data)

    def test_15_raw_body_text_is_absent(self):
        response_text = self.post_pdf().text
        self.assertNotIn("Ordinary hierarchy fixture body line one", response_text)

    def test_16_raw_heading_and_outline_titles_are_absent(self):
        response_text = self.post_pdf().text
        self.assertNotIn("CHAPTER 1 Foundation", response_text)
        self.assertNotIn("1.1 First Section", response_text)

    def test_17_identical_requests_produce_byte_equivalent_json(self):
        first = self.post_pdf()
        second = self.post_pdf()
        self.assertEqual(first.content, second.content)

    def test_18_unexpected_failure_maps_to_safe_500(self):
        with patch.object(
            api_module,
            "inspect_real_pdf_toc",
            side_effect=RuntimeError("sensitive internal detail"),
        ):
            response = self.post_pdf()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "internal_error",
                    "message": "Internal service error",
                }
            },
        )

    def test_19_error_response_has_no_exception_or_traceback_detail(self):
        with patch.object(
            api_module,
            "inspect_real_pdf_toc",
            side_effect=RuntimeError("sensitive internal detail"),
        ):
            response = self.post_pdf()
        serialized = json.dumps(response.json(), sort_keys=True).lower()
        self.assertNotIn("sensitive", serialized)
        self.assertNotIn("traceback", serialized)
        self.assertNotIn("runtimeerror", serialized)

    def test_20_openapi_includes_inspection_endpoint(self):
        paths = self.client.get("/openapi.json").json()["paths"]
        self.assertIn("/v1/documents/inspect", paths)

    def test_21_task_016_runtime_remains_functional(self):
        result = inspect_real_pdf_toc(self.data)
        self.assertEqual(result.page_count, 5)
        self.assertEqual(result.reconciliation_match_count, 5)

    def test_22_real_uvicorn_loopback_tcp_health_smoke(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]

        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="error",
            access_log=False,
        )
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=False)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and thread.is_alive() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue(server.started, "uvicorn did not start within 10 seconds")
            with urlopen(f"http://127.0.0.1:{port}/healthz", timeout=5) as response:
                self.assertEqual(response.status, 200)
                payload = json.loads(response.read())
            self.assertEqual(
                payload,
                {"status": "ok", "service": "bie-api", "api_version": "v1"},
            )
        finally:
            server.should_exit = True
            thread.join(timeout=10)
        self.assertFalse(thread.is_alive(), "uvicorn did not shut down cleanly")


if __name__ == "__main__":
    unittest.main()
