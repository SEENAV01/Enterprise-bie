"""Task 045 seekh (25 October 2026): the reviewer on the free Google key on the VM, and a review output cap.

Navin, 25 October 2026: the VM's checker uses GEMINI_API_KEY (free tier, sample content only) through the direct route
with gemini-3.8-flash; the AICredits key stays on the machine unused. Job B2: v5's review ran away to the 32,000-token
cap, so a review call now has its own cap measured from earlier reviews. Offline: no network, no keys, no money.
"""
from __future__ import annotations

import io
import json
import os
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import codex_vm  # noqa: E402
import run_brain  # noqa: E402
from bie.model_gateway.gemini_adapter import GeminiAdapter  # noqa: E402
from bie.model_gateway.live.budget import CostGuard, output_cap  # noqa: E402
from bie.model_gateway.live.compat_client import OpenAICompatChatClient  # noqa: E402
from bie.model_gateway.live.errors import ProviderError, classify, retry_after  # noqa: E402
from bie.model_gateway.live.gateway import RETRY_AFTER_MAX, LiveGateway  # noqa: E402
from bie.model_gateway.live.gemini_client import GeminiClient  # noqa: E402
from bie.model_gateway.live.pricing import estimate_cost  # noqa: E402
from bie.model_gateway.live.transport import HttpTransport  # noqa: E402
from bie.model_gateway.model_interface import ModelRequest  # noqa: E402

FREE_KEY = "AIzaFAKEfreeTierKeyForTests0123456789"      # 39 characters like Navin's, not a real key
AIC_KEY = "sk-aicredits-test-0123456789abcdef"
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["verdict"],
          "properties": {"verdict": {"type": "string"}}}


def google_429(quota_ids, *, delay="37s", limit=10):
    """A Google RESOURCE_EXHAUSTED body shaped like the free tier's."""
    violations = [{"quotaMetric": "generativelanguage.googleapis.com/generate_content_free_tier_requests", "quotaId": q,
                   "quotaDimensions": {"model": "gemini-3.8-flash", "location": "global"}, "quotaValue": str(limit)}
                  for q in quota_ids]
    return {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED",
                      "message": ("You exceeded your current quota, please check your plan and billing details. * Quota "
                                  "exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, "
                                  f"limit: {limit}, model: gemini-3.8-flash\nPlease retry in {delay}."),
                      "details": [{"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": violations},
                                  {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay}]}}


class Opener:
    """Replays HTTP outcomes in order (an HTTPError or a JSON body) and records each request."""

    def __init__(self, *outcomes):
        self.outcomes, self.requests = list(outcomes), []

    def __call__(self, request, timeout):
        self.requests.append({"url": request.full_url, "headers": {k.lower(): v for k, v in request.header_items()},
                              "body": json.loads(request.data.decode()) if request.data else None})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return io.BytesIO(json.dumps(outcome).encode())


def http_error(code, body):
    return urllib.error.HTTPError("https://generativelanguage.googleapis.com", code, "err", {},
                                  io.BytesIO(json.dumps(body).encode()))


GEMINI_OK = {"modelVersion": "gemini-3.8-flash", "candidates": [{"finishReason": "STOP", "content": {"parts": [
    {"text": "{\"verdict\": \"pass\"}"}]}}], "usageMetadata": {"promptTokenCount": 30000, "candidatesTokenCount": 900,
                                                                "thoughtsTokenCount": 2100}}

VM_ENV = {"GEMINI_API_KEY": FREE_KEY, "AICREDITS_GEMINI_API_KEY": AIC_KEY}


class ReviewOutputCap(unittest.TestCase):
    """The reviewer's route gets its own client with the smaller cap; the maker keeps 32,000."""

    def build(self, maker, reviewer, env, reviewer_model=""):
        clean = {k: v for k, v in os.environ.items() if not k.startswith(("BIE_", "GEMINI", "GOOGLE", "AICREDITS", "OPENAI"))}
        with mock.patch.dict(os.environ, dict(clean, **env), clear=True):
            return run_brain.build_gateway(maker, reviewer, fake=False, ledger=None, max_output_tokens=32000,
                                           reviewer_model=reviewer_model)

    def test_the_measured_cap(self):
        # 99 answered review calls on blindtest-results: largest Task 045d script review 1,612 output tokens, largest of
        # any kind 3,744 (reasoning included); Gemini direct counts thinking inside the cap.
        self.assertEqual(run_brain.REVIEW_OUTPUT_TOKENS, 12000)
        self.assertGreaterEqual(run_brain.REVIEW_OUTPUT_TOKENS, 3 * 3744)
        self.assertLessEqual(run_brain.REVIEW_OUTPUT_TOKENS, 32000 // 2)

    def test_the_vm_job_codex_maker_and_free_google_reviewer(self):
        gateway, route = self.build("codex", "google", dict(VM_ENV, BIE_GEMINI_VIA="direct", BIE_GEMINI_MODEL="gemini-3.8-flash"))
        self.assertEqual(route, "google")
        client = gateway.routes["google"].client
        self.assertIsInstance(client, GeminiClient)
        self.assertEqual((client.via if hasattr(client, "via") else "direct", gateway.model_of("google")),
                         ("direct", "gemini-3.8-flash"))
        self.assertEqual(client.max_output_tokens, 12000)
        self.assertEqual(output_cap(gateway.routes["google"]), 12000)      # the guard reserves on the review cap
        self.assertEqual(client._key, FREE_KEY)                              # the free key, not the AICredits one

    def test_both_keys_without_a_route_the_direct_key_wins(self):
        gateway, _ = self.build("codex", "google", VM_ENV)
        self.assertIsInstance(gateway.routes["google"].client, GeminiClient)

    def test_a_job_can_still_choose_aicredits(self):
        gateway, _ = self.build("codex", "google", dict(VM_ENV, BIE_GEMINI_VIA="aicredits"))
        client = gateway.routes["google"].client
        self.assertIsInstance(client, OpenAICompatChatClient)
        self.assertEqual((client.via, client.max_tokens), ("aicredits", 12000))

    def test_an_api_maker_keeps_its_own_cap(self):
        gateway, _ = self.build("openai", "google", dict(VM_ENV, OPENAI_API_KEY="sk-test-maker-0123456789", BIE_GEMINI_VIA="direct"))
        self.assertEqual(gateway.routes["openai"].client.max_output_tokens, 32000)
        self.assertEqual(gateway.routes["google"].client.max_output_tokens, 12000)

    def test_a_same_company_checker_gets_the_review_cap(self):
        gateway, route = self.build("google", "google", dict(VM_ENV, BIE_GEMINI_VIA="direct"), reviewer_model="gemini-3.8-flash")
        self.assertEqual(route, "google-checker")
        self.assertEqual(gateway.routes["google"].client.max_output_tokens, 32000)
        self.assertEqual(gateway.routes["google-checker"].client.max_output_tokens, 12000)

    def test_a_missing_reviewer_key_still_stops_before_any_call(self):
        with self.assertRaises(SystemExit) as caught:
            self.build("codex", "google", {})
        self.assertIn("NOT_CONFIGURED:google", str(caught.exception))

    def test_the_flag_reaches_the_request_and_refuses_a_tiny_cap(self):
        gateway, _ = self.build("codex", "google", dict(VM_ENV, BIE_GEMINI_VIA="direct"))
        opener = Opener(GEMINI_OK)
        gateway.routes["google"].client.transport = HttpTransport(timeout=30, opener=opener)
        gateway.routes["google"].client.stream = False
        gateway.complete("google", ModelRequest(request_id="lesson:script-v5:r0:review", response_schema=SCHEMA,
                                                messages=({"role": "user", "content": "review"},)), prompt_version="v/review")
        self.assertEqual(opener.requests[0]["body"]["generationConfig"]["maxOutputTokens"], 12000)
        self.assertNotIn(FREE_KEY, opener.requests[0]["url"])                # the key travels in a header only
        with self.assertRaises(SystemExit) as caught:
            run_brain.main(["--section", "lesson", "--out", "/nonexistent-never-made", "--review-output-tokens", "500", "--fake"])
        self.assertIn("OUTPUT_TOKENS_TOO_SMALL", str(caught.exception))


class FreeTierQuota(unittest.TestCase):
    """Google answers every free-tier quota with 429 and "You exceeded your current quota" (the words of an empty wallet).
    A per-minute quota is waited out; a per-day quota or a model the tier does not serve stops the run as before."""

    MINUTE = "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"
    DAY = "GenerateRequestsPerDayPerProjectPerModel-FreeTier"

    def text(self, body):
        return json.dumps(body)

    def test_kinds(self):
        said = "RESOURCE_EXHAUSTED | You exceeded your current quota"
        self.assertEqual(classify(429, said, self.text(google_429([self.MINUTE]))), "rate_limit")
        self.assertEqual(classify(429, said, self.text(google_429([self.MINUTE, self.DAY]))), "balance")
        self.assertEqual(classify(429, said, self.text(google_429([self.DAY]))), "balance")
        self.assertEqual(classify(429, said, self.text(google_429([self.MINUTE], limit=0))), "balance")     # argon on free
        self.assertEqual(classify(429, "insufficient_quota | You exceeded your current quota"), "balance")  # OpenAI
        self.assertEqual(classify(402, "Insufficient Balance"), "balance")                                  # AICredits
        self.assertEqual(classify(429, "slow down"), "rate_limit")
        self.assertEqual(retry_after(self.text(google_429([self.MINUTE], delay="37s"))), 37.0)
        self.assertIsNone(retry_after("no wait here"))

    def gateway(self, *outcomes, stream=False):
        opener = Opener(*outcomes)
        client = GeminiClient(FREE_KEY, transport=HttpTransport(timeout=30, opener=opener), max_output_tokens=12000, stream=stream)
        waits = []
        guard = CostGuard(20, rate=94.59)
        gw = LiveGateway({"google": GeminiAdapter(client, "gemini-3.8-flash")}, sleep=waits.append, guard=guard)
        return gw, waits, guard, opener

    def request(self):
        return ModelRequest(request_id="lesson:script-v9:r0:review", response_schema=SCHEMA,
                            messages=({"role": "user", "content": "review " * 50},))

    def test_a_per_minute_quota_waits_the_asked_time_and_goes_on(self):
        gw, waits, guard, _ = self.gateway(http_error(429, google_429([self.MINUTE], delay="37s")), GEMINI_OK)
        answer = gw.complete("google", self.request(), prompt_version="v/review")
        self.assertEqual(answer.content, {"verdict": "pass"})
        self.assertEqual(len(waits), 1)
        self.assertGreaterEqual(waits[0], 37.0)
        self.assertIsNone(guard.stop_reason)
        first, second = gw.ledger.rows
        self.assertEqual((first["error_kind"], first["cost_usd"]), ("rate_limit", None))     # a refused call costs nothing
        self.assertEqual((second["outcome"], second["via"], second["model"]), ("ok", "direct", "gemini-3.8-flash"))

    def test_a_long_asked_wait_is_capped(self):
        gw, waits, _, _ = self.gateway(http_error(429, google_429([self.MINUTE], delay="600s")), GEMINI_OK)
        gw.complete("google", self.request(), prompt_version="v/review")
        self.assertEqual(waits, [RETRY_AFTER_MAX])

    def test_a_per_day_quota_stops_the_run_without_retrying(self):
        gw, waits, guard, _ = self.gateway(http_error(429, google_429([self.DAY], delay="3600s")))
        with self.assertRaises(ProviderError) as caught:
            gw.complete("google", self.request(), prompt_version="v/review")
        self.assertEqual(caught.exception.kind, "balance")
        self.assertEqual(waits, [])
        self.assertTrue(guard.stop_reason.startswith("balance"))

    def test_the_streaming_route_reads_the_quota_too(self):
        gw, _, _, opener = self.gateway(http_error(429, google_429([self.MINUTE])), stream=True)
        with self.assertRaises(ProviderError) as caught:
            gw.routes["google"].client.generate(model="gemini-3.8-flash", messages=[{"role": "user", "content": "x"}])
        self.assertEqual((caught.exception.kind, caught.exception.retry_after), ("rate_limit", 37.0))
        self.assertIn(":streamGenerateContent", opener.requests[0]["url"])
        self.assertNotIn(FREE_KEY, str(caught.exception))


class FreeTierLedger(unittest.TestCase):
    """The ledger names the route and model; the guard prices the free tier at the list price as a safe estimate."""

    def test_a_review_through_the_free_key(self):
        client = GeminiClient(FREE_KEY, transport=HttpTransport(timeout=30, opener=Opener(GEMINI_OK)), max_output_tokens=12000)
        guard = CostGuard(20, rate=94.59)
        gw = LiveGateway({"google": GeminiAdapter(client, "gemini-3.8-flash")}, sleep=lambda s: None, guard=guard)
        gw.complete("google", ModelRequest(request_id="lesson:script-v9:r0:review", response_schema=SCHEMA,
                                           messages=({"role": "user", "content": "review"},)), prompt_version="v/review")
        row = gw.ledger.rows[-1]
        self.assertEqual((row["via"], row["model"], row["billing"], row["output_tokens"], row["reasoning_tokens"]),
                         ("direct", "gemini-3.8-flash", "api", 3000, 2100))
        expected = estimate_cost("gemini-3.8-flash", {"input_tokens": 30000, "output_tokens": 3000})
        self.assertAlmostEqual(row["cost_usd"], expected)
        self.assertLess(expected * 94.59, 3.5)                    # about Rs 3 at list price; Google bills the free tier Rs 0
        self.assertAlmostEqual(guard.spent_usd, expected)


class VmJob(unittest.TestCase):
    def test_the_free_reviewer_job_passes_validation(self):
        job = codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "t045-free-reviewer-smoke", "section": "lesson",
                                 "chapter_map": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/x.json",
                                 "maker": "codex", "reviewer": "google", "models": "google=gemini-3.8-flash",
                                 "routes": "google=direct", "max_inr": 5})
        cmd = codex_vm.argv(job, Path("/tmp/out"), python="python")
        self.assertEqual(cmd[cmd.index("--routes") + 1], "google=direct")
        self.assertEqual(cmd[cmd.index("--models") + 1], "google=gemini-3.8-flash")

    def test_status_shows_which_keys_are_present_and_never_a_key(self):
        class Client:
            def login_status(self):
                return {"logged_in": False, "mode": "test"}

        clean = {k: v for k, v in os.environ.items() if not k.startswith(("BIE_", "GEMINI", "GOOGLE", "AICREDITS"))}
        with mock.patch("bie.model_gateway.live.codex_client.CodexExecClient", Client), \
                mock.patch.dict(os.environ, dict(clean, **VM_ENV, BIE_HOME="/nonexistent-bie-home"), clear=True):
            out = codex_vm.status()
        self.assertEqual(out["gemini_keys"], {"direct": True, "aicredits": True})
        self.assertEqual((out["gemini_key_set"], out["gemini_default_route"]), (True, "direct"))
        text = json.dumps(out)
        for key in (FREE_KEY, AIC_KEY):
            self.assertNotIn(key, text)
            self.assertNotIn(key[:8], text)
        with mock.patch("bie.model_gateway.live.codex_client.CodexExecClient", Client), \
                mock.patch.dict(os.environ, dict(clean, AICREDITS_GEMINI_API_KEY=AIC_KEY, BIE_HOME="/nonexistent-bie-home"),
                                clear=True):
            out = codex_vm.status()
        self.assertEqual((out["gemini_keys"], out["gemini_default_route"]), ({"direct": False, "aicredits": True}, "aicredits"))


if __name__ == "__main__":
    unittest.main()
