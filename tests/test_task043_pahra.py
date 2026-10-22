"""Task 043: the cost guard (pahra): balance errors, rupee cap, preflight, estimate, same-company checker (offline)."""
from __future__ import annotations

import contextlib
import functools
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests" / "productization" / "document_intelligence"))

import run_brain  # noqa: E402
from bie.brain import cost, rulebook  # noqa: E402
from bie.brain.fake import BrainFakeClient  # noqa: E402
from bie.brain.pages import Block, Page  # noqa: E402
from bie.brain.runner import SectionRunner  # noqa: E402
from bie.brain.understanding import Course, page_step  # noqa: E402
from bie.model_gateway.gemini_adapter import GeminiAdapter  # noqa: E402
from bie.model_gateway.gpt_adapter import GPTAdapter  # noqa: E402
from bie.model_gateway.live.budget import BudgetExceeded, CostGuard, input_tokens, preflight  # noqa: E402
from bie.model_gateway.live.compat_client import OpenAICompatChatClient  # noqa: E402
from bie.model_gateway.live.errors import ProviderError, classify, kind_for_status  # noqa: E402
from bie.model_gateway.live.gateway import LiveGateway  # noqa: E402
from bie.model_gateway.live.transport import HttpTransport  # noqa: E402
from bie.model_gateway.model_interface import ModelRequest  # noqa: E402
from structural_pdf_fixtures import positioned_text_pdf  # noqa: E402

# Test prices: every fake model costs $100 per 1M tokens in and out, and a dollar is Rs 100 here.
PRICES = json.dumps({"fake": [100.0, 100.0]})
ENV = {"BIE_MODEL_PRICES_JSON": PRICES, "BIE_USD_INR": "100"}
SECRET = "sk-pahra-test-secret-0123456789"
COURSE = Course("Test chapter", "Biology", "UPSC aspirants", "UPSC", "Hinglish")
LINES = ("Tissue is a group of similar cells doing one job.", "Muscle tissue helps in movement.")


def pdf(pages=3):
    return positioned_text_pdf([[(72, 720 - i * 20, LINES[i % 2]) for i in range(12)] for _ in range(pages)])


def request(rid="understand:page-001:r1", text="Set status to ready."):
    return ModelRequest(request_id=rid, messages=({"role": "system", "content": "Be exact."}, {"role": "user", "content": text}),
                        response_schema={"type": "object", "additionalProperties": False, "required": ["status"],
                                         "properties": {"status": {"type": "string", "enum": ["ready"]}}})


def guarded(max_inr, client=None, **guard):
    client = client or BrainFakeClient("openai", usage=(2000, 1000))   # Rs 30 per call
    cost_guard = CostGuard(max_inr, rate=100.0, env=ENV, **guard)
    gateway = LiveGateway({"openai": GPTAdapter(client, "fake-openai")}, sleep=lambda s: None, env=ENV, guard=cost_guard)
    return gateway, cost_guard, client


class Broke(BrainFakeClient):
    """A provider whose wallet is empty (AICredits 402) and which echoes part of the key."""

    def _respond(self, model, messages, schema):
        raise ProviderError("balance", f"insufficient_quota | 402 | Insufficient Balance for key {SECRET}", provider=self.provider)


def run(argv, *, client=None, env=None):
    """run_brain.main with test prices, a fake client factory and captured annotations."""
    out = io.StringIO()
    patches = [mock.patch.dict(os.environ, dict(ENV, **(env or {}))), contextlib.redirect_stdout(out)]
    if client is not None:
        patches.append(mock.patch.object(run_brain, "BrainFakeClient", client))
    with contextlib.ExitStack() as stack:
        for patch in patches:
            stack.enter_context(patch)
        code = run_brain.main(argv)
    return code, out.getvalue()


class BalanceErrors(unittest.TestCase):
    def test_used_up_balance_is_its_own_kind_and_never_retried(self):
        self.assertEqual(kind_for_status(402), "balance")
        self.assertEqual(classify(429, "insufficient_quota | credit_balance_exhausted | You have no credits remaining."), "balance")
        self.assertEqual(classify(400, "insufficient_quota | 402 | API Key Budget Exceeded"), "balance")
        self.assertEqual(classify(429, "slow down"), "rate_limit")
        self.assertEqual(classify(None, {"type": "billing_error"}), "balance")
        self.assertEqual(classify(None, "overloaded"), "server_error")
        self.assertFalse(ProviderError("balance").retryable)
        self.assertFalse(ProviderError("budget").retryable)

    def test_transport_reads_the_aicredits_402(self):
        body = {"error": {"type": "insufficient_quota", "code": 402, "message": "API Key Budget Exceeded. Raise this key's budget"}}
        def opener(req, timeout):
            raise urllib.error.HTTPError("https://x", 402, "err", {}, io.BytesIO(json.dumps(body).encode()))
        with self.assertRaises(ProviderError) as caught:
            HttpTransport(timeout=5, opener=opener).request_json("POST", "https://api.example/v1", {}, {}, provider="aicredits")
        self.assertEqual((caught.exception.kind, caught.exception.status), ("balance", 402))

    def test_a_used_up_balance_stops_the_run_after_one_call(self):
        gateway, guard, client = guarded(1000, client=Broke("openai"))
        with self.assertRaises(ProviderError) as caught:
            gateway.complete("openai", request(), prompt_version="t/1")
        self.assertEqual(caught.exception.kind, "balance")
        self.assertEqual([r["outcome"] for r in gateway.ledger.rows], ["error"])     # no retries
        self.assertTrue(guard.stopped)
        self.assertTrue(guard.stop_reason.startswith("balance"))
        with self.assertRaises(BudgetExceeded):
            gateway.complete("openai", request("understand:page-002:r1"), prompt_version="t/1")
        self.assertEqual(gateway.ledger.rows[-1]["outcome"], "stopped")


class CapStop(unittest.TestCase):
    def test_a_call_that_would_cross_the_cap_is_not_sent(self):
        gateway, guard, client = guarded(50)
        gateway.complete("openai", request(), prompt_version="t/1", expected_output_tokens=1000)
        self.assertAlmostEqual(guard.spent_inr, 30.0)
        with self.assertRaises(BudgetExceeded) as caught:
            gateway.complete("openai", request("understand:page-002:r1"), prompt_version="t/1", expected_output_tokens=3000)
        self.assertEqual(caught.exception.kind, "budget")
        self.assertIn("would cross the cap of Rs 50", str(caught.exception))
        self.assertEqual(len(client.calls), 1)                       # the refused call never reached the provider
        self.assertEqual(gateway.ledger.rows[-1]["outcome"], "stopped")
        self.assertEqual(gateway.ledger.rows[-1]["error_kind"], "budget")
        # Once stopped, the guard stays stopped, even for a call that would fit.
        with self.assertRaises(BudgetExceeded):
            gateway.complete("openai", request("understand:page-003:r1"), prompt_version="t/1", expected_output_tokens=1)
        self.assertEqual(len(client.calls), 1)
        report = guard.report()
        self.assertEqual((report["calls_allowed"], report["calls_refused"], report["stopped"]), (1, 2, True))
        self.assertEqual(report["by_section_inr"], {"understand": 30.0})

    def test_retries_and_repairs_pay_their_way_too(self):
        class Flaky(BrainFakeClient):
            failures = 1
            def _respond(self, model, messages, schema):
                if self.failures:
                    self.failures -= 1
                    raise ProviderError("timeout", "slow", provider=self.provider)
                return super()._respond(model, messages, schema)
        gateway, guard, client = guarded(1000, client=Flaky("openai", usage=(2000, 1000)))
        gateway.complete("openai", request(), prompt_version="t/1", expected_output_tokens=1000)
        self.assertEqual(guard.calls, 2)                             # the retry was reserved as well
        self.assertAlmostEqual(guard.spent_inr, 30.0)                 # the failed attempt cost nothing
        self.assertEqual(guard.in_flight_usd, 0.0)

    def test_unpriced_model_fails_closed(self):
        guard = CostGuard(1000, rate=100.0, env={})
        gateway = LiveGateway({"openai": GPTAdapter(BrainFakeClient("openai"), "unknown-model-x")}, sleep=lambda s: None,
                              env={}, guard=guard)
        with self.assertRaises(BudgetExceeded) as caught:
            gateway.complete("openai", request(), prompt_version="t/1")
        self.assertIn("no price for model unknown-model-x", str(caught.exception))

    def test_projection_counts_hinglish_and_images_generously(self):
        ascii_only = input_tokens([{"role": "user", "content": "a" * 350}])
        hinglish = input_tokens([{"role": "user", "content": "क" * 350}])
        image = input_tokens([{"role": "user", "content": [{"type": "text", "text": "x"}, {"type": "image", "data": ""}]}])
        self.assertEqual(ascii_only, 100 + 50)
        self.assertEqual(hinglish, 350 + 50)
        self.assertGreaterEqual(image, 1600)

    def test_cap_must_be_positive(self):
        with self.assertRaises(ValueError):
            CostGuard(0)

    def test_a_stopped_step_is_not_a_failed_step(self):
        gateway, guard, _ = guarded(1000)
        runner = SectionRunner(LiveGateway({"anthropic": gateway.routes["openai"], "openai": GPTAdapter(BrainFakeClient("openai"), "fake-openai")},
                                           sleep=lambda s: None, env=ENV, guard=guard),
                               maker="anthropic", reviewer="openai", rulebook=rulebook.load())
        guard.trip("budget: test")
        page = Page(1, (Block("p0001-b0001", "Cells form tissues.", (0, 0, 1, 1)),), None)
        result = runner.run(page_step(COURSE, page, page_count=1, rulebook=runner.rulebook))
        self.assertEqual(result.status, "stopped")
        self.assertFalse(result.passed)
        self.assertEqual(result.rounds[0]["maker_error"]["kind"], "budget")


class Preflight(unittest.TestCase):
    def test_preflight_passes_and_costs_little(self):
        gateway, guard, _ = guarded(1000)
        checked = preflight(gateway)
        self.assertTrue(checked["passed"])
        self.assertEqual(checked["routes"]["openai"]["status"], "ok")
        self.assertEqual(gateway.ledger.rows[0]["request_id"], "preflight:openai")

    def test_preflight_reports_a_used_up_balance(self):
        gateway, guard, _ = guarded(1000, client=Broke("openai"))
        checked = preflight(gateway)
        self.assertFalse(checked["passed"])
        self.assertEqual(checked["routes"]["openai"]["error_kind"], "balance")
        self.assertTrue(guard.stopped)                                # nothing else runs after a failed preflight

    def test_every_route_is_checked_on_its_own(self):
        guard = CostGuard(1000, rate=100.0, env=ENV)
        gateway = LiveGateway({"openai": GPTAdapter(Broke("openai"), "fake-openai"),
                               "google": GeminiAdapter(BrainFakeClient("google"), "fake-google")},
                              sleep=lambda s: None, env=ENV, guard=guard)
        checked = preflight(gateway)
        self.assertEqual({r: e["status"] for r, e in checked["routes"].items()}, {"openai": "failed", "google": "ok"})
        self.assertEqual(guard.stop_reason, "preflight: openai balance")

    def test_wallet_balance_is_read_for_aicredits_routes(self):
        class Stub:
            def __init__(self):
                self.urls = []
            def request_json(self, method, url, headers, body=None, *, provider, secrets=()):
                self.urls.append(url)
                if url.endswith("/credits"):
                    return {"balance_inr": 512.5, "currency": "INR", "user": {"credits": 3, "name": "x"}}
                if url.endswith("/api/models"):
                    return {"data": [
                        {"id": "google/gemini-4-argon", "input_cost_per_token": 2e-06, "output_cost_per_token": 1e-05,
                         "cached_input_cost_per_token": 1e-07, "input_cost_per_token_inr": 0.000198647, "exchange_rate": 94.593871,
                         "context_length": 1048576, "input_modalities": ["text", "image"], "description": "dropped"},
                        {"id": "google/documented-form", "input_cost_per_1m": 2, "output_cost_per_1m": 10, "context_window": 1000},
                        {"name": "no id"}]}
                return {"model": "google/gemini-4-argon", "choices": [{"message": {"content": '{"status": "ready"}'},
                                                                        "finish_reason": "stop"}],
                        "usage": {"prompt_tokens": 30, "completion_tokens": 5}}
        stub = Stub()
        client = OpenAICompatChatClient(SECRET, transport=stub)
        self.assertEqual(client.credits(), {"balance_inr": 512.5, "user.credits": 3})
        self.assertEqual(client.list_model_details(), [
            {"id": "google/documented-form", "context_window": 1000, "usd_per_1m": {"input": 2, "output": 10}},
            {"id": "google/gemini-4-argon", "exchange_rate": 94.593871, "context_window": 1048576,
             "usd_per_1m": {"input": 2.0, "output": 10.0, "cached_input": 0.1}, "inr_per_1m": {"input": 198.647},
             "input_modalities": ["text", "image"]}])
        self.assertEqual(client.list_models(), ["google/documented-form", "google/gemini-4-argon"])
        guard = CostGuard(10, rate=100.0)
        gateway = LiveGateway({"google": GeminiAdapter(client, "google/gemini-4-argon")}, sleep=lambda s: None, guard=guard)
        checked = preflight(gateway)
        self.assertTrue(checked["passed"])
        self.assertEqual(checked["routes"]["google"]["wallet"], {"balance_inr": 512.5, "user.credits": 3})
        self.assertLess(guard.spent_inr, 0.1)


class Estimate(unittest.TestCase):
    def test_section_one_estimate_comes_from_the_measured_runs(self):
        est = cost.estimate("understand", 14, rate=88.0, maker_model="gpt-6.1-sol", reviewer_model="google/gemini-4-argon")
        self.assertEqual(est["price_scale"], 1.0)
        self.assertEqual(est["sections"]["understand"], {"inr": 222.99, "inr_per_page": 15.93, "basis": "measured",
                                                          "source": "run 39620281561, 14 pages"})
        self.assertEqual(est["sections"]["connect"]["inr"], 73.92)
        self.assertEqual(est["total_inr"], 296.91)
        self.assertEqual(est["measured_share_inr"], 296.91)
        line = cost.estimate_line(est, 300)
        self.assertTrue(line.startswith("Andaaza Rs 296.91, seema Rs 300"), line)

    def test_unmeasured_sections_are_marked_assumed(self):
        est = cost.estimate("chain", 10, rate=88.0, maker_model="gpt-6.1-sol", reviewer_model="google/gemini-4-argon",
                            with_visual=True)
        self.assertEqual(list(est["sections"]), ["understand", "connect", "notes", "game", "lesson", "director", "visual"])
        self.assertEqual({k for k, v in est["sections"].items() if v["basis"] == "assumed"},
                         {"notes", "game", "lesson", "director", "visual"})
        self.assertIn("(assumed)", cost.estimate_line(est, 300))
        self.assertLess(est["measured_share_inr"], est["total_inr"])

    def test_cheaper_models_scale_the_estimate_and_unknown_models_do_not(self):
        cheap = cost.estimate("understand", 10, rate=88.0, maker_model="gemini-2.5-flash", reviewer_model="google/gemini-4-argon")
        self.assertEqual(cheap["price_scale"], 0.363)
        unknown = cost.estimate("understand", 10, rate=88.0, maker_model="mystery", reviewer_model="google/gemini-4-argon")
        self.assertIsNone(unknown["price_scale"])
        base = cost.estimate("understand", 10, rate=88.0)
        self.assertEqual(unknown["total_inr"], base["total_inr"])
        self.assertLess(cheap["total_inr"], base["total_inr"])

    def test_actual_cost_per_section_and_page(self):
        rows = [{"request_id": "preflight:google", "cost_usd": 0.001}, {"request_id": "understand:page-001:r1", "cost_usd": 0.1},
                {"request_id": "understand:page-001:r1:review", "cost_usd": 0.05}, {"request_id": "connect:chapter:r1", "cost_usd": None}]
        got = cost.actual(rows, pages=2, rate=100.0)
        self.assertEqual(got["sections"]["understand"], {"name": "Section 1 · page reading", "calls": 2, "usd": 0.15,
                                                         "inr": 15.0, "inr_per_page": 7.5})
        self.assertEqual(got["total_inr"], 15.1)
        self.assertEqual(got["inr_per_page"], 7.55)


class RunBrain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name, "chapter.pdf")
        self.source.write_bytes(pdf(3))

    def args(self, out, *extra):
        return ["--fake", "--section", "understand", "--source", str(self.source), "--out", str(Path(self.tmp.name, out)),
                "--workers", "1", *extra]

    def read(self, out, name):
        return json.loads(Path(self.tmp.name, out, name).read_text(encoding="utf-8"))

    def test_cap_stop_keeps_passed_work(self):
        # Every fake call really costs Rs 300 (20,000 + 10,000 tokens); its projection is about Rs 115-160.
        # Rs 1,850: preflight (600) and pages 1 and 2 (1,200) fit; page 3 (1,800 + ~150) would cross.
        code, log = run(self.args("cap", "--max-inr", "1850"), client=functools.partial(BrainFakeClient, usage=(20000, 10000)))
        self.assertEqual(code, 0)
        summary = self.read("cap", "SUMMARY.json")
        self.assertEqual(summary["status"], "stopped: budget")
        self.assertIn("would cross the cap of Rs 1850", summary["stop_reason"])
        chapter = self.read("cap", "chapter_map.json")
        self.assertEqual([p["status"] for p in chapter["pages"]], ["passed", "passed", "stopped"])
        self.assertEqual(chapter["map_status"], "stopped")
        self.assertTrue(chapter["items"])                                  # the passed pages' items are kept
        ledger = [json.loads(line) for line in Path(self.tmp.name, "cap", "LEDGER.jsonl").read_text().splitlines()]
        sent = [r for r in ledger if r["outcome"] == "ok"]
        self.assertEqual(len(sent), 6)                                      # 2 preflight + 2 pages x (maker + reviewer)
        self.assertTrue(any(r["outcome"] == "stopped" for r in ledger))
        spent = summary["cost"]
        self.assertEqual(spent["total_inr"], 1800.0)
        self.assertLessEqual(spent["total_inr"], 1850)
        self.assertEqual(spent["sections"]["understand"]["inr"], 1200.0)
        self.assertEqual(spent["inr_per_page"], 600.0)
        self.assertTrue(spent["cap"]["stopped"])
        self.assertIsNone(spent["real_bill_inr"])
        self.assertIn("not the bill", spent["note"])
        self.assertIn("pahra andaaza::Andaaza Rs", log)
        self.assertIn("::warning title=pahra kharch::Kharch Rs 1800", log)

    def test_chain_does_not_start_the_next_section_after_a_stop(self):
        code, _ = run(["--fake", "--section", "chain", "--source", str(self.source), "--out", str(Path(self.tmp.name, "chain")),
                       "--workers", "1", "--max-inr", "1850"], client=functools.partial(BrainFakeClient, usage=(20000, 10000)))
        self.assertEqual(code, 0)
        summary = self.read("chain", "SUMMARY.json")
        self.assertEqual(summary["status"], "stopped: budget")
        for later in ("notes_quality", "game_quality", "lesson_quality", "director_quality"):
            self.assertNotIn(later, summary)
        self.assertFalse(Path(self.tmp.name, "chain", "lesson_plan.json").exists())

    def test_preflight_stop_runs_no_section_and_leaks_no_key(self):
        code, log = run(self.args("broke"), client=Broke, env={"AICREDITS_GEMINI_API_KEY": SECRET})
        self.assertEqual(code, 1)
        summary = self.read("broke", "SUMMARY.json")
        self.assertEqual(summary["status"], "stopped: preflight")
        self.assertFalse(summary["preflight"]["passed"])
        self.assertEqual({r["error_kind"] for r in summary["preflight"]["routes"].values()}, {"balance"})
        self.assertFalse(Path(self.tmp.name, "broke", "chapter_map.json").exists())
        self.assertFalse(Path(self.tmp.name, "broke", "records").exists())
        ledger = Path(self.tmp.name, "broke", "LEDGER.jsonl").read_text()
        self.assertEqual({json.loads(line)["request_id"] for line in ledger.splitlines()}, {"preflight:openai", "preflight:google"})
        self.assertEqual(summary["cost"]["total_inr"], 0.0)
        self.assertIn("::error title=pahra preflight openai::", log)
        self.assertIn("top up or raise the key budget", log)
        for text in (log, Path(self.tmp.name, "broke", "SUMMARY.json").read_text()):
            self.assertNotIn(SECRET, text)
            self.assertNotIn(SECRET[:8], text)

    def test_ok_run_reports_rupees_per_section(self):
        code, log = run(self.args("ok", "--max-inr", "100000"), client=functools.partial(BrainFakeClient, usage=(2000, 1000)))
        self.assertEqual(code, 0)
        summary = self.read("ok", "SUMMARY.json")
        self.assertEqual(summary["status"], "ok")
        self.assertEqual(set(summary["cost"]["sections"]), {"preflight", "understand", "connect"})
        self.assertEqual(summary["cost"]["pages"], 3)
        self.assertEqual(summary["estimate"]["pages"], 3)
        self.assertEqual(summary["cost"]["cap"]["cap_inr"], 100000.0)
        self.assertEqual(summary["reviewer_independence"], "other_company")

    def test_same_company_checker_is_marked_in_every_record(self):
        code, _ = run(self.args("same", "--maker", "google", "--reviewer", "google", "--reviewer-model", "google/gemini-3.1-pro",
                                "--pages", "1"))
        self.assertEqual(code, 0)
        summary = self.read("same", "SUMMARY.json")
        self.assertEqual(summary["reviewer_route"], "google-checker")
        self.assertEqual(summary["reviewer_independence"], "same_company_temporary")
        self.assertEqual(summary["models"], {"google": "fake-google", "google-checker": "fake-google-gemini-3.1-pro"})
        chapter = self.read("same", "chapter_map.json")
        self.assertEqual(chapter["reviewer_independence"], "same_company_temporary")
        record = self.read("same", "records/understand--page-001.json")
        self.assertEqual((record["reviewer_route"], record["reviewer_model"], record["reviewer_independence"]),
                         ("google-checker", "fake-google-gemini-3.1-pro", "same_company_temporary"))
        self.assertIn("temporary", Path(self.tmp.name, "same", "MAP.md").read_text(encoding="utf-8"))

    def test_same_company_needs_another_model(self):
        with self.assertRaises(SystemExit):
            run(self.args("x", "--maker", "google", "--reviewer", "google"))
        with self.assertRaises(SystemExit):
            run_brain.build_gateway("google", "google", fake=True, ledger=None, max_output_tokens=10, reviewer_model="google")


if __name__ == "__main__":
    unittest.main()
