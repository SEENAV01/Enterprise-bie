"""Task 038: LiveGateway retries/cache/repair/ledger and the blind-test harness, all offline (fake provider)."""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests/productization/document_intelligence"))
sys.path.insert(0, str(ROOT / "tools"))

from structural_pdf_fixtures import positioned_text_pdf

from bie.model_gateway.claude_adapter import ClaudeAdapter
from bie.model_gateway.gpt_adapter import GPTAdapter
from bie.model_gateway.live import blind_test
from bie.model_gateway.live.config import build_routes
from bie.model_gateway.live.disk_cache import DiskCache
from bie.model_gateway.live.errors import ProviderError
from bie.model_gateway.live.fake_client import FakeProviderClient
from bie.model_gateway.live.gateway import LiveGateway
from bie.model_gateway.live.ledger import UsageLedger
from bie.model_gateway.live.pricing import estimate_cost, price_for
from bie.model_gateway.model_interface import ModelRequest
from bie.model_gateway.model_provenance import ModelProvenance, validate as validate_provenance
from bie.model_gateway.retry_policy import RetryPolicy

import run_blind_test

SCHEMA = {"type": "object", "additionalProperties": False, "required": ["answer"],
          "properties": {"answer": {"type": "string", "minLength": 1}}}
REQUEST = ModelRequest("req-1", ({"role": "system", "content": "s"}, {"role": "user", "content": "u"}), response_schema=SCHEMA)
LINES = ("Green plants make food using sunlight, water and air.", "Chlorophyll in leaves absorbs the light energy.",
         "Oxygen is released as a by-product of this process.")


def chapter_pdf(pages=3, lines=30):
    return positioned_text_pdf([[(72, 720 - i * 20, f"{LINES[i % 3]}") for i in range(lines)] for _ in range(pages)])


def gateway(script=(), model="claude-opus-5-5", **kwargs):
    client = FakeProviderClient("anthropic", script=script)
    sleeps = []
    gw = LiveGateway({"anthropic": ClaudeAdapter(client, model)}, sleep=sleeps.append,
                     retry=RetryPolicy(max_attempts=3, base_delay=1.0, max_delay=8.0), **kwargs)
    return gw, client, sleeps


class Gateway(unittest.TestCase):
    def test_success_returns_validated_content_and_provenance(self):
        gw, client, _ = gateway()
        response = gw.complete("anthropic", REQUEST, prompt_version="p/1")
        self.assertEqual(set(response.content), {"answer"})
        self.assertEqual((response.provider, response.model), ("anthropic", "claude-opus-5-5"))
        prov = response.provenance
        validate_provenance(ModelProvenance(**{k: prov[k] for k in ("provider", "model", "request_hash", "prompt_version",
                                                                    "started_at", "finished_at")}))
        self.assertEqual((prov["attempts"], prov["cache_hit"], prov["returned_model"]), (1, False, "fake-claude-opus-5-5"))
        self.assertEqual(len(client.calls), 1)

    def test_transient_errors_retry_with_backoff_then_succeed(self):
        gw, client, sleeps = gateway(["rate_limit", "server_error"])
        gw.complete("anthropic", REQUEST, prompt_version="p/1")
        self.assertEqual(sleeps, [1.0, 2.0])
        self.assertEqual([r["outcome"] for r in gw.ledger.rows], ["error", "error", "ok"])
        self.assertEqual([r["error_kind"] for r in gw.ledger.rows[:2]], ["rate_limit", "server_error"])

    def test_retries_are_bounded_and_permanent_errors_are_not_retried(self):
        gw, _, sleeps = gateway(["timeout", "timeout", "timeout", "ok"])
        with self.assertRaises(ProviderError) as caught:
            gw.complete("anthropic", REQUEST, prompt_version="p/1")
        self.assertEqual((caught.exception.kind, len(sleeps)), ("timeout", 2))
        gw, client, sleeps = gateway(["auth"])
        with self.assertRaises(ProviderError) as caught:
            gw.complete("anthropic", REQUEST, prompt_version="p/1")
        self.assertEqual((caught.exception.kind, sleeps, len(client.calls)), ("auth", [], 1))

    def test_invalid_output_gets_one_repair_turn_with_the_error(self):
        for bad in ("invalid", "garbage"):
            gw, client, _ = gateway([bad])
            response = gw.complete("anthropic", REQUEST, prompt_version="p/1")
            self.assertIn("answer", response.content)
            repair = client.calls[1]["messages"]
            self.assertEqual([m["role"] for m in repair], ["system", "user", "assistant", "user"])
            self.assertIn("did not match the required JSON schema", repair[-1]["content"])
            self.assertEqual([r["outcome"] for r in gw.ledger.rows], ["schema_invalid", "ok"])
        gw, _, _ = gateway(["invalid", "invalid"])
        with self.assertRaises(ProviderError) as caught:
            gw.complete("anthropic", REQUEST, prompt_version="p/1")
        self.assertEqual(caught.exception.kind, "schema_invalid")

    def test_content_check_problems_are_repaired_like_schema_errors(self):
        seen = []

        def check(value):
            seen.append(value)
            return ["first answer rejected"] if len(seen) == 1 else []

        gw, client, _ = gateway()
        gw.complete("anthropic", REQUEST, prompt_version="p/1", check=check)
        self.assertEqual(len(client.calls), 2)
        self.assertIn("first answer rejected", client.calls[1]["messages"][-1]["content"])

    def test_cache_hit_skips_the_provider_and_is_keyed_by_prompt_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            gw, client, _ = gateway(cache=DiskCache(tmp))
            first = gw.complete("anthropic", REQUEST, prompt_version="p/1")
            second = gw.complete("anthropic", REQUEST, prompt_version="p/1")
            self.assertEqual(first.content, second.content)
            self.assertTrue(second.provenance["cache_hit"])
            self.assertEqual(len(client.calls), 1)
            gw.complete("anthropic", REQUEST, prompt_version="p/2")
            self.assertEqual(len(client.calls), 2)
            self.assertEqual([r["cache_hit"] for r in gw.ledger.rows], [False, True, False])
            with self.assertRaises(ProviderError):
                gw.complete("anthropic", REQUEST, prompt_version="p/1", check=lambda value: ["stricter now"])
            self.assertEqual(len(client.calls), 4)  # a cached answer that fails today's check is not reused
            stored = "".join(p.read_text() for p in Path(tmp).rglob("*.json"))
            self.assertNotIn("sk-", stored)

    def test_ledger_rows_costs_and_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = UsageLedger(Path(tmp) / "ledger.jsonl")
            gw, _, _ = gateway(["rate_limit"], model="claude-opus-5-5", ledger=ledger)
            gw.complete("anthropic", REQUEST, prompt_version="p/1")
            rows = [json.loads(line) for line in (Path(tmp) / "ledger.jsonl").read_text().splitlines()]
        self.assertEqual([r["seq"] for r in rows], [1, 2])
        self.assertEqual(rows[1]["cost_usd"], 0.0)  # the fake provider is priced at zero, never as the real model
        summary = ledger.summary()["anthropic"]
        self.assertEqual((summary["calls"], summary["failed_calls"], summary["input_tokens"]), (2, 1, 1200))

    def test_pricing_is_prefix_based_overridable_and_never_guessed(self):
        self.assertEqual(price_for("claude-opus-5-5-20261001")[:2], (4.0, 20.0))
        self.assertEqual(price_for("models/gemini-3.1-pro-preview")[:2], (2.0, 12.0))
        self.assertIsNone(price_for("mystery-model"))
        self.assertIsNone(estimate_cost("mystery-model", {"input_tokens": 10}))
        self.assertEqual(estimate_cost("claude-opus-5-5", {"input_tokens": 1_000_000, "output_tokens": 100_000}), 6.0)
        env = {"BIE_MODEL_PRICES_JSON": json.dumps({"mystery-model": [1, 2]})}
        self.assertEqual(estimate_cost("mystery-model", {"input_tokens": 1_000_000, "output_tokens": 0}, env), 1.0)
        ledger = UsageLedger()
        ledger.record(provider="x", outcome="ok", cache_hit=False, input_tokens=5, output_tokens=5, cost_usd=None)
        self.assertFalse(ledger.summary()["x"]["cost_complete"])

    def test_requests_are_validated_before_any_call(self):
        gw, client, _ = gateway()
        with self.assertRaises(ProviderError):
            gw.complete("openai", REQUEST, prompt_version="p/1")
        with self.assertRaises(ProviderError):
            gw.complete("anthropic", REQUEST, prompt_version="")
        with self.assertRaises(ValueError):
            gw.complete("anthropic", ModelRequest("", REQUEST.messages), prompt_version="p/1")
        self.assertEqual(client.calls, [])


class BlindTest(unittest.TestCase):
    def test_chapter_text_comes_from_the_document_intelligence_runtime(self):
        chapter = blind_test.chapter_from_pdf(chapter_pdf(pages=3))
        self.assertEqual((chapter.page_count, chapter.pages_used), (3, (1, 2, 3)))
        self.assertIn("[Page 2]\nGreen plants make food", chapter.text)
        self.assertEqual(len(chapter.source_sha256), 64)
        part = blind_test.chapter_from_pdf(chapter_pdf(pages=4), pages="2-3")
        self.assertEqual(part.pages_used, (2, 3))
        self.assertNotIn("[Page 1]", part.text)

    def test_chapter_limits_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "scanned"):
            blind_test.chapter_from_pdf(chapter_pdf(pages=1, lines=3))
        with self.assertRaisesRegex(ValueError, "one chapter"):
            blind_test.chapter_from_pdf(chapter_pdf(pages=3), max_pages=2)
        with self.assertRaisesRegex(ValueError, "outside"):
            blind_test.chapter_from_pdf(chapter_pdf(pages=3), pages="2-9")

    def test_every_provider_gets_the_identical_prompt(self):
        routes, _ = build_routes(fake=True)
        gw = LiveGateway(routes)
        chapter = blind_test.chapter_from_pdf(chapter_pdf())
        results = blind_test.run(gw, chapter, class_level="Class 7", language="Hindi", subject="Science")
        self.assertEqual({r["status"] for r in results.values()}, {"ok"})
        sent = [route.client.calls[0]["messages"] for route in routes.values()]
        self.assertTrue(all(messages == sent[0] for messages in sent))
        self.assertIn("in Hindi, for Class 7 learners", sent[0][0]["content"])
        self.assertIn(chapter.text, sent[0][1]["content"])
        self.assertIn("untrusted data", sent[0][0]["content"])

    def test_content_rules(self):
        lesson = {"questions": [{"options": ["a", "b", "b", "c"], "correct_option_index": 4}],
                  "narration_script": {"scenes": [{"scene_number": 2, "duration_seconds": 0}]},
                  "lesson_plan": {"sections": [{"minutes": 0}]}}
        problems = " | ".join(blind_test.check_lesson(lesson))
        for expected in ("correct_option_index", "options must be different", "scene_number", "duration_seconds", "minutes"):
            self.assertIn(expected, problems)

    def test_section_numbers_written_by_a_model_are_not_doubled(self):
        routes, _ = build_routes(fake=True)
        chapter = blind_test.chapter_from_pdf(chapter_pdf())
        lesson = blind_test.run(LiveGateway(routes), chapter, class_level="x", language="y")["anthropic"]["lesson"]
        lesson["lesson_plan"]["sections"][0]["title"] = "1. Tissue kya hai"
        lesson["lesson_plan"]["sections"][1]["title"] = "2) Epithelium"
        text = "\n".join(blind_test.render_lesson(lesson))
        self.assertIn("**1. Tissue kya hai**", text)
        self.assertIn("**2. Epithelium**", text)

    def test_report_hides_providers_and_key_maps_back(self):
        routes, _ = build_routes(fake=True, fake_scripts={"openai": ["auth"]})
        gw = LiveGateway(routes)
        chapter = blind_test.chapter_from_pdf(chapter_pdf())
        results = blind_test.run(gw, chapter, class_level="Class 7", language="English")
        by_letter, key = blind_test.anonymise(results, seed=3)
        report = blind_test.render_report(by_letter, chapter=chapter, class_level="Class 7", language="English", subject="")
        public = report + json.dumps(by_letter)
        for hidden in ("anthropic", "openai", "google", "claude", "gpt", "gemini", "Claude", "GPT", "Gemini"):
            self.assertNotIn(hidden, public)
        self.assertEqual(sorted(by_letter), ["A", "B", "C"])
        self.assertEqual(sorted(item["provider"] for item in key.values()), ["anthropic", "google", "openai"])
        failed = [letter for letter, item in key.items() if item["provider"] == "openai"][0]
        self.assertEqual(by_letter[failed]["status"], "failed")
        self.assertIn(f"## Option {failed}\n\nIs option ka jawab nahi aa paaya", report)
        self.assertEqual(report.count("**Q5.**"), 2)
        orders = {tuple(item["provider"] for _, item in sorted(blind_test.anonymise(results, seed=s)[1].items())) for s in range(12)}
        self.assertGreater(len(orders), 1)


class Runner(unittest.TestCase):
    def run_cli(self, *args, env=None):
        out = io.StringIO()
        clean = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}
        with mock.patch.dict(os.environ, {**clean, **(env or {})}, clear=True), contextlib.redirect_stdout(out):
            code = run_blind_test.main(list(args))
        return code, out.getvalue()

    def test_fake_blind_test_writes_report_results_key_and_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "chapter.pdf"
            pdf.write_bytes(chapter_pdf())
            code, printed = self.run_cli("--mode", "blind-test", "--fake", "--source", str(pdf), "--out", tmp + "/out",
                                         "--class-level", "Class 6", "--language", "Hindi")
            out = Path(tmp) / "out"
            self.assertEqual(code, 0, printed)
            self.assertEqual(sorted(p.name for p in out.iterdir()),
                             ["KEY.json", "LEDGER.jsonl", "REPORT.md", "RESULTS.json", "SUMMARY.json"])
            summary = json.loads((out / "SUMMARY.json").read_text())
            self.assertEqual((summary["passed"], summary["product_accepted"]), (True, False))
            self.assertEqual(summary["providers_ok"], ["anthropic", "google", "openai"])
            self.assertIn("::notice title=blind-test chapter::", printed)
            self.assertEqual(len((out / "LEDGER.jsonl").read_text().splitlines()), 3)

    def test_probe_and_smoke_without_keys_report_not_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, printed = self.run_cli("--mode", "probe", "--out", tmp)
            self.assertEqual(code, 1)
            probe = json.loads((Path(tmp) / "PROBE.json").read_text())
            self.assertEqual({v["status"] for v in probe.values()}, {"not_configured"})
            code, printed = self.run_cli("--mode", "smoke", "--out", tmp)
            self.assertEqual(code, 1)
            self.assertIn("no provider is configured", printed)

    def test_fake_probe_and_smoke_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, printed = self.run_cli("--mode", "probe", "--fake", "--out", tmp)
            self.assertEqual(code, 0, printed)
            code, printed = self.run_cli("--mode", "smoke", "--fake", "--out", tmp)
            self.assertEqual(code, 0, printed)
            self.assertEqual(printed.count("::notice title=smoke"), 3)

    def test_keys_never_reach_outputs(self):
        key = "sk-ant-api03-SECRETSECRETSECRET-abcdef"
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "chapter.pdf"
            pdf.write_bytes(chapter_pdf())
            printed = ""
            # No network in tests: the real client is built and its call fails; the error must not carry the key.
            with mock.patch("urllib.request.urlopen", side_effect=OSError(f"refused for {key}")), mock.patch("time.sleep"):
                for mode in ("probe", "smoke", "blind-test"):
                    code, text = self.run_cli("--mode", mode, "--source", str(pdf), "--out", f"{tmp}/{mode}",
                                              "--providers", "anthropic", env={"ANTHROPIC_API_KEY": key})
                    self.assertEqual(code, 1, text)
                    printed += text
            written = printed + "".join(p.read_text() for p in Path(tmp).rglob("*") if p.is_file() and p.suffix != ".pdf")
            self.assertNotIn(key, written)
            self.assertNotIn("SECRETSECRET", written)

    def test_probe_through_aicredits_with_route_and_model_overrides(self):
        class Listing:
            def read(self, limit=-1):
                return json.dumps({"object": "list", "data": [{"id": "anthropic/claude-opus-5.5"},
                                                              {"id": "anthropic/claude-sonnet-5.5"},
                                                              {"id": "google/gemini-4-argon"}]}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        with tempfile.TemporaryDirectory() as tmp, mock.patch("urllib.request.urlopen", return_value=Listing()):
            code, printed = self.run_cli("--mode", "probe", "--providers", "anthropic,google", "--out", tmp,
                                         "--models", "anthropic=anthropic/claude-sonnet-5.5", "--routes", "google=aicredits",
                                         env={"AICREDITS_API_KEY": "sk-aicredits-secret-value-1"})
            probe = json.loads((Path(tmp) / "PROBE.json").read_text())
        self.assertEqual(code, 0, printed)
        self.assertEqual(probe["anthropic"]["via"], "aicredits")
        self.assertEqual(probe["anthropic"]["configured_model"], "anthropic/claude-sonnet-5.5")
        self.assertTrue(probe["google"]["configured_model_available"])
        self.assertIn("via aicredits", printed)
        self.assertNotIn("sk-aicredits-secret-value-1", printed)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(SystemExit) as caught:
            self.run_cli("--mode", "probe", "--out", tmp, "--routes", "google")
        self.assertEqual(str(caught.exception), "BAD_ROUTE_OVERRIDE:google")

    def test_source_must_be_a_pdf_over_https_or_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = Path(tmp) / "notes.txt"
            text.write_text("not a pdf")
            for source, code in ((str(text), "SOURCE_IS_NOT_A_PDF"), ("http://example.com/a.pdf", "SOURCE_URL_MUST_BE_HTTPS")):
                with self.assertRaises(SystemExit) as caught:
                    self.run_cli("--mode", "blind-test", "--fake", "--source", source, "--out", tmp + "/o")
                self.assertEqual(str(caught.exception), code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
