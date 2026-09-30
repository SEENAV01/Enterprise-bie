from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from tests.section18.support import Section18Case


class _IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.tags = []
    def handle_starttag(self, tag, attrs):
        row = dict(attrs)
        if row.get("id"):
            self.ids.add(row["id"])
        self.tags.append((tag, row))


class WebContractTests(Section18Case):
    @property
    def web_root(self):
        return Path(__file__).resolve().parents[2] / "apps" / "web" / "section18"

    def test_001_operator_app_is_served(self):
        response = self.client.get("/app/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("BIE Operator Console", response.text)

    def test_002_required_interactive_elements_are_present(self):
        parser = _IdCollector()
        parser.feed(self.client.get("/app/").text)
        required = {
            "main", "sourceForm", "sourceFile", "validateButton", "createButton",
            "refreshButton", "runFacts", "timeline", "failureView", "artifactId",
            "graphCanvas", "graphMessage",
        }
        self.assertTrue(required.issubset(parser.ids), sorted(required - parser.ids))

    def test_003_file_picker_is_pdf_scoped(self):
        parser = _IdCollector()
        parser.feed(self.client.get("/app/").text)
        picker = next(attrs for tag, attrs in parser.tags if attrs.get("id") == "sourceFile")
        self.assertEqual(picker.get("type"), "file")
        self.assertIn("application/pdf", picker.get("accept", ""))

    def test_004_script_uses_real_section18_api_routes(self):
        script = (self.web_root / "app.js").read_text(encoding="utf-8")
        for path in [
            "/v1/app/sources/validate",
            "/v1/app/runs",
            "/timeline",
            "/failure",
            "/graphs/",
        ]:
            self.assertIn(path, script)

    def test_005_script_has_no_mock_progress_or_static_success_data(self):
        script = (self.web_root / "app.js").read_text(encoding="utf-8").lower()
        self.assertNotIn("progresspercent", script)
        self.assertNotIn("mock", script)
        self.assertNotIn("demo data", script)
        self.assertNotIn("fake", script)

    def test_006_script_does_not_use_innerhtml_or_eval(self):
        script = (self.web_root / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", script)
        self.assertNotIn("eval(", script)
        self.assertIn("textContent", script)

    def test_007_keyboard_focus_style_and_skip_link_exist(self):
        css = (self.web_root / "styles.css").read_text(encoding="utf-8")
        html = (self.web_root / "index.html").read_text(encoding="utf-8")
        self.assertIn(":focus-visible", css)
        self.assertIn("skip-link", html)
        self.assertIn('href="#main"', html)

    def test_008_mobile_layout_is_explicit(self):
        css = (self.web_root / "styles.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("grid-template-columns: 1fr", css)

    def test_009_graph_has_accessible_title_and_description(self):
        html = (self.web_root / "index.html").read_text(encoding="utf-8")
        self.assertIn('aria-labelledby="graphTitle graphDescription"', html)
        self.assertIn('id="graphTitle"', html)
        self.assertIn('id="graphDescription"', html)

    def test_010_openapi_contains_section18_routes(self):
        paths = self.client.get("/openapi.json").json()["paths"]
        expected = {
            "/v1/app/sources/validate",
            "/v1/app/runs",
            "/v1/app/runs/{job_id}",
            "/v1/app/runs/{job_id}/timeline",
            "/v1/app/runs/{job_id}/failure",
            "/v1/app/runs/{job_id}/retry",
            "/v1/app/runs/{job_id}/pause",
            "/v1/app/runs/{job_id}/resume",
            "/v1/app/runs/{job_id}/cancel",
            "/v1/app/runs/{job_id}/graphs/{kind}",
        }
        self.assertTrue(expected.issubset(paths), sorted(expected - set(paths)))

    def test_011_existing_api_routes_remain_present(self):
        paths = self.client.get("/openapi.json").json()["paths"]
        for route in [
            "/healthz",
            "/v1/capabilities",
            "/v1/documents/inspect",
            "/v1/jobs/document-inspection",
            "/v1/jobs/{job_id}",
            "/v1/jobs/{job_id}/result",
        ]:
            self.assertIn(route, paths)

    def test_012_static_assets_are_served(self):
        css = self.client.get("/app/styles.css")
        script = self.client.get("/app/app.js")
        self.assertEqual(css.status_code, 200)
        self.assertEqual(script.status_code, 200)
        self.assertIn("focus-visible", css.text)
        self.assertIn("validateSelected", script.text)


if __name__ == "__main__":
    import unittest
    unittest.main()
