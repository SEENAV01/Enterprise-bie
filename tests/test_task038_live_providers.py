"""Task 038: live provider clients, transport, redaction, schema keywords and route config (offline)."""
from __future__ import annotations

import io
import json
import socket
import sys
import unittest
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.model_gateway.claude_adapter import ClaudeAdapter
from bie.model_gateway.gemini_adapter import GeminiAdapter
from bie.model_gateway.gpt_adapter import GPTAdapter
from bie.model_gateway.live.anthropic_client import API_VERSION, AnthropicClient
from bie.model_gateway.live.compat_client import OpenAICompatChatClient
from bie.model_gateway.live.config import DEFAULT_MODELS, DEFAULT_MODELS_VIA, all_keys, build_routes, key_for, model_for, route_for
from bie.model_gateway.live.errors import ProviderError, kind_for_status, redact
from bie.model_gateway.live.gemini_client import GeminiClient
from bie.model_gateway.live.messages import provider_schema, split_messages
from bie.model_gateway.live.openai_client import OpenAIClient
from bie.model_gateway.live.pricing import estimate_cost, normalize
from bie.model_gateway.live.transport import HttpTransport
from bie.model_gateway.model_interface import ModelRequest
from bie.model_gateway.schema_validation import SchemaValidationError, validate

KEY = "sk-test-0123456789abcdefSECRET"
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["items", "name"], "properties": {
    "items": {"type": "array", "minItems": 3, "maxItems": 5, "items": {"type": "integer"}},
    "name": {"type": "string", "minLength": 1}}}
MESSAGES = ({"role": "system", "content": "Be exact."}, {"role": "user", "content": "Give items."})


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def read(self, limit=-1):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Recorder:
    """An opener that records the request and replays a scripted outcome."""

    def __init__(self, outcome):
        self.outcome = outcome
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append({"url": request.full_url, "method": request.get_method(), "timeout": timeout,
                              "headers": {k.lower(): v for k, v in request.header_items()},
                              "body": json.loads(request.data.decode()) if request.data else None})
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return FakeResponse(json.dumps(self.outcome).encode() if not isinstance(self.outcome, bytes) else self.outcome)


def http_error(code, body):
    return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(json.dumps(body).encode()))


def transport(outcome):
    recorder = Recorder(outcome)
    return HttpTransport(timeout=30, opener=recorder), recorder


class TransportAndRedaction(unittest.TestCase):
    def test_status_codes_map_to_stable_kinds(self):
        expected = {400: "bad_request", 401: "auth", 403: "auth", 404: "not_found", 408: "timeout", 429: "rate_limit",
                    500: "server_error", 502: "server_error", 503: "provider_unavailable", 529: "provider_unavailable"}
        for status, kind in expected.items():
            self.assertEqual(kind_for_status(status), kind, status)

    def test_http_error_body_is_quoted_without_the_key(self):
        t, _ = transport(http_error(401, {"error": {"type": "invalid_request_error",
                                                    "message": f"Incorrect API key provided: {KEY[:10]}****{KEY[-4:]}"}}))
        with self.assertRaises(ProviderError) as caught:
            t.request_json("POST", "https://api.example/v1", {}, {}, provider="openai", secrets=(KEY,))
        error = caught.exception
        self.assertEqual((error.kind, error.status, error.retryable), ("auth", 401, False))
        self.assertNotIn(KEY[:10], str(error))
        self.assertNotIn(KEY[-4:], str(error))
        self.assertIn("invalid_request_error", str(error))

    def test_network_failures_are_retryable_kinds(self):
        for outcome, kind in ((socket.timeout("slow"), "timeout"), (urllib.error.URLError(socket.timeout()), "timeout"),
                              (urllib.error.URLError("dns"), "provider_unavailable"), (ConnectionResetError(), "provider_unavailable"),
                              (http_error(429, {"error": "slow down"}), "rate_limit")):
            t, _ = transport(outcome)
            with self.assertRaises(ProviderError) as caught:
                t.request_json("GET", "https://api.example/v1", {}, provider="p")
            self.assertEqual(caught.exception.kind, kind)
            self.assertTrue(caught.exception.retryable)

    def test_non_json_and_plain_http_fail_closed(self):
        t, _ = transport(b"<html>gateway</html>")
        with self.assertRaises(ProviderError) as caught:
            t.request_json("GET", "https://api.example/v1", {}, provider="p")
        self.assertEqual(caught.exception.kind, "malformed")
        with self.assertRaises(ProviderError) as caught:
            t.request_json("GET", "http://api.example/v1", {}, provider="p")
        self.assertEqual(caught.exception.kind, "config")

    def test_redact_removes_exact_masked_and_shaped_keys_only(self):
        text = (f"key {KEY} masked sk-te****CRET header Bearer abcdefghijklmnop google AIzaSyA1234567890 "
                f"api_key=zzzzyyyyxxxx keep risk-free desk-top task038")
        clean = redact(text, (KEY,))
        for leaked in (KEY, "sk-te", "CRET", "abcdefghijklmnop", "AIzaSyA1234567890", "zzzzyyyyxxxx"):
            self.assertNotIn(leaked, clean)
        for kept in ("risk-free", "desk-top", "task038"):
            self.assertIn(kept, clean)


class ProviderClients(unittest.TestCase):
    def test_anthropic_request_and_response(self):
        t, rec = transport({"model": "claude-opus-5-5-20261001", "stop_reason": "end_turn",
                            "content": [{"type": "text", "text": '{"items": [1, 2, 3], "name": "x"}'}],
                            "usage": {"input_tokens": 100, "output_tokens": 40, "cache_read_input_tokens": 10}})
        client = AnthropicClient(KEY, transport=t)
        out = ClaudeAdapter(client, "claude-opus-5-5").invoke(ModelRequest("r", MESSAGES, response_schema=SCHEMA))
        sent = rec.requests[0]
        self.assertEqual(sent["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(sent["headers"]["x-api-key"], KEY)
        self.assertEqual(sent["headers"]["anthropic-version"], API_VERSION)
        self.assertEqual(sent["body"]["system"], "Be exact.")
        self.assertEqual(sent["body"]["messages"], [{"role": "user", "content": "Give items."}])
        sent_schema = sent["body"]["output_config"]["format"]
        self.assertEqual(sent_schema["type"], "json_schema")
        self.assertNotIn("minItems", json.dumps(sent_schema))
        self.assertNotIn("minLength", json.dumps(sent_schema))
        self.assertFalse(sent_schema["schema"]["additionalProperties"])
        self.assertNotIn(KEY, json.dumps(sent["body"]))
        self.assertNotIn("temperature", sent["body"])
        self.assertEqual(out["content"], '{"items": [1, 2, 3], "name": "x"}')
        self.assertEqual(out["usage"]["input_tokens"], 110)
        self.assertEqual(client.last_model, "claude-opus-5-5-20261001")

    def test_anthropic_refusal_and_truncation(self):
        for stop, kind in (("refusal", "refusal"), ("max_tokens", "truncated")):
            t, _ = transport({"stop_reason": stop, "content": [{"type": "text", "text": "{"}], "usage": {}})
            with self.assertRaises(ProviderError) as caught:
                AnthropicClient(KEY, transport=t).messages_create(model="m", messages=MESSAGES, schema=SCHEMA)
            self.assertEqual(caught.exception.kind, kind)

    def test_openai_request_and_response(self):
        t, rec = transport({"model": "gpt-6.1-sol-2026-09", "status": "completed", "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [{"type": "output_text", "text": '{"items": [1, 2, 3], "name": "y"}'}]}],
            "usage": {"input_tokens": 90, "output_tokens": 300, "output_tokens_details": {"reasoning_tokens": 200}}})
        client = OpenAIClient(KEY, transport=t)
        out = GPTAdapter(client, "gpt-6.1-sol").invoke(ModelRequest("r", MESSAGES, response_schema=SCHEMA))
        sent = rec.requests[0]
        self.assertEqual(sent["url"], "https://api.openai.com/v1/responses")
        self.assertEqual(sent["headers"]["authorization"], "Bearer " + KEY)
        self.assertEqual(sent["body"]["instructions"], "Be exact.")
        self.assertFalse(sent["body"]["store"])
        fmt = sent["body"]["text"]["format"]
        self.assertEqual((fmt["type"], fmt["strict"]), ("json_schema", True))
        self.assertNotIn("maxItems", json.dumps(fmt))
        self.assertEqual(out["usage"]["reasoning_tokens"], 200)
        self.assertEqual(out["content"], '{"items": [1, 2, 3], "name": "y"}')

    def test_openai_incomplete_and_refusal(self):
        cases = (({"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}}, "truncated"),
                 ({"status": "incomplete", "incomplete_details": {"reason": "content_filter"}}, "refusal"),
                 ({"status": "completed", "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "no"}]}]}, "refusal"))
        for body, kind in cases:
            t, _ = transport(body)
            with self.assertRaises(ProviderError) as caught:
                OpenAIClient(KEY, transport=t).responses_create(model="m", messages=MESSAGES)
            self.assertEqual(caught.exception.kind, kind)

    def test_gemini_request_and_response(self):
        t, rec = transport({"modelVersion": "gemini-3.1-pro-001", "candidates": [{"finishReason": "STOP", "content": {"parts": [
            {"text": "thinking...", "thought": True}, {"text": '{"items": [1, 2, 3], "name": "z"}'}]}}],
            "usageMetadata": {"promptTokenCount": 50, "candidatesTokenCount": 20, "thoughtsTokenCount": 30}})
        client = GeminiClient(KEY, transport=t)
        out = GeminiAdapter(client, "gemini-3.1-pro").invoke(ModelRequest("r", MESSAGES, response_schema=SCHEMA))
        sent = rec.requests[0]
        self.assertEqual(sent["url"], "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro:generateContent")
        self.assertNotIn(KEY, sent["url"])
        self.assertEqual(sent["headers"]["x-goog-api-key"], KEY)
        self.assertEqual(sent["body"]["systemInstruction"], {"parts": [{"text": "Be exact."}]})
        config = sent["body"]["generationConfig"]
        self.assertEqual(config["responseMimeType"], "application/json")
        self.assertNotIn("additionalProperties", json.dumps(config["responseJsonSchema"]))
        self.assertEqual(config["responseJsonSchema"]["properties"]["items"]["minItems"], 3)
        self.assertEqual(out["content"], '{"items": [1, 2, 3], "name": "z"}')
        self.assertEqual(out["usage"]["output_tokens"], 50)
        self.assertEqual(out["finish_reason"], "STOP")

    def test_gemini_blocks_and_truncation(self):
        cases = (({"promptFeedback": {"blockReason": "SAFETY"}}, "refusal"),
                 ({"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "{"}]}}]}, "truncated"),
                 ({"candidates": [{"finishReason": "RECITATION", "content": {"parts": []}}]}, "refusal"),
                 ({"candidates": []}, "malformed"))
        for body, kind in cases:
            t, _ = transport(body)
            with self.assertRaises(ProviderError) as caught:
                GeminiClient(KEY, transport=t).generate(model="m", messages=MESSAGES)
            self.assertEqual(caught.exception.kind, kind)

    def test_model_listing(self):
        t, rec = transport({"data": [{"id": "claude-opus-5-5"}, {"id": "claude-haiku-5-5"}]})
        self.assertEqual(AnthropicClient(KEY, transport=t).list_models(), ["claude-haiku-5-5", "claude-opus-5-5"])
        self.assertEqual(rec.requests[0]["method"], "GET")
        t, _ = transport({"models": [{"name": "models/gemini-3.1-pro", "supportedGenerationMethods": ["generateContent"]},
                                     {"name": "models/text-embedding", "supportedGenerationMethods": ["embedContent"]}]})
        self.assertEqual(GeminiClient(KEY, transport=t).list_models(), ["gemini-3.1-pro"])
        t, _ = transport({"data": [{"id": "gpt-6.1-sol"}]})
        self.assertEqual(OpenAIClient(KEY, transport=t).list_models(), ["gpt-6.1-sol"])

    def test_missing_key_and_bad_messages_fail_before_any_request(self):
        for cls in (AnthropicClient, OpenAIClient, GeminiClient):
            with self.assertRaises(ProviderError) as caught:
                cls("")
            self.assertEqual(caught.exception.kind, "config")
        with self.assertRaises(ProviderError):
            split_messages(({"role": "assistant", "content": "x"},), provider="p")
        with self.assertRaises(ProviderError):
            split_messages(({"role": "user", "content": "x"}, {"role": "system", "content": "late"}), provider="p")


class SequenceRecorder(Recorder):
    """Replays one outcome per request."""

    def __call__(self, request, timeout):
        outcome, rest = self.outcome[0], self.outcome[1:]
        self.outcome = rest or [outcome]
        holder = Recorder(outcome)
        holder.requests = self.requests
        return holder(request, timeout)


CHAT_OK = {"model": "anthropic/claude-opus-5.5", "choices": [{"index": 0, "finish_reason": "stop", "message": {
    "role": "assistant", "content": '{"items": [1, 2, 3], "name": "w"}'}}],
    "usage": {"prompt_tokens": 70, "completion_tokens": 30, "completion_tokens_details": {"reasoning_tokens": 5}}}


class AICreditsRoute(unittest.TestCase):
    def test_chat_request_carries_schema_no_cache_and_bearer_key(self):
        rec = SequenceRecorder([CHAT_OK])
        client = OpenAICompatChatClient(KEY, transport=HttpTransport(timeout=30, opener=rec))
        out = ClaudeAdapter(client, "anthropic/claude-opus-5.5").invoke(ModelRequest("r", MESSAGES, response_schema=SCHEMA))
        sent = rec.requests[0]
        self.assertEqual(sent["url"], "https://api.aicredits.in/v1/chat/completions")
        self.assertEqual(sent["headers"]["authorization"], "Bearer " + KEY)
        body = sent["body"]
        self.assertTrue(body["no_cache"])  # the gateway's semantic cache must never answer for the model
        self.assertEqual(body["model"], "anthropic/claude-opus-5.5")
        self.assertEqual(body["messages"][0]["role"], "system")
        self.assertIn("Be exact.", body["messages"][0]["content"])
        self.assertIn('"minItems": 3', body["messages"][0]["content"])  # schema also in the prompt
        self.assertEqual(body["response_format"]["type"], "json_schema")
        self.assertEqual(out["content"], '{"items": [1, 2, 3], "name": "w"}')
        self.assertEqual((out["usage"]["input_tokens"], out["usage"]["output_tokens"]), (70, 30))
        self.assertEqual((client.via, client.last_model), ("aicredits", "anthropic/claude-opus-5.5"))

    def test_json_schema_rejection_falls_back_to_json_object_once_and_for_good(self):
        rec = SequenceRecorder([http_error(400, {"error": {"message": "response_format json_schema not supported"}}), CHAT_OK])
        client = OpenAICompatChatClient(KEY, transport=HttpTransport(timeout=30, opener=rec))
        client.generate(model="google/gemini-3.1-pro-preview", messages=MESSAGES, schema=SCHEMA)
        client.generate(model="google/gemini-3.1-pro-preview", messages=MESSAGES, schema=SCHEMA)
        formats = [r["body"]["response_format"]["type"] for r in rec.requests]
        self.assertEqual(formats, ["json_schema", "json_object", "json_object"])
        rec = SequenceRecorder([http_error(400, {"error": {"message": "bad model"}})])
        with self.assertRaises(ProviderError):
            OpenAICompatChatClient(KEY, transport=HttpTransport(timeout=30, opener=rec)).chat(model="m", messages=MESSAGES)
        self.assertEqual(len(rec.requests), 1)  # no schema: nothing to fall back from

    def test_finish_reasons_and_errors(self):
        cases = (({"choices": [{"finish_reason": "length", "message": {"content": "{"}}]}, "truncated"),
                 ({"choices": [{"finish_reason": "content_filter", "message": {"content": None}}]}, "refusal"),
                 ({"choices": []}, "malformed"),
                 ({"error": {"message": "upstream"}}, "server_error"))
        for body, kind in cases:
            client = OpenAICompatChatClient(KEY, transport=HttpTransport(timeout=30, opener=Recorder(body)))
            with self.assertRaises(ProviderError) as caught:
                client.chat(model="m", messages=MESSAGES)
            self.assertEqual(caught.exception.kind, kind)

    def test_public_model_list(self):
        rec = Recorder({"object": "list", "data": [{"id": "anthropic/claude-opus-5.5"}, {"id": "google/gemini-3.1-pro-preview"}]})
        models = OpenAICompatChatClient(KEY, transport=HttpTransport(timeout=30, opener=rec)).list_models()
        self.assertEqual(models, ["anthropic/claude-opus-5.5", "google/gemini-3.1-pro-preview"])
        self.assertEqual(rec.requests[0]["url"], "https://api.aicredits.in/api/models")
        self.assertNotIn("authorization", rec.requests[0]["headers"])

    def test_route_rule_direct_wins_then_aicredits_then_forced(self):
        env = {"OPENAI_API_KEY": "sk-openai-direct-key", "AICREDITS_API_KEY": "sk-aicredits-key-123"}
        self.assertEqual(route_for("openai", env), ("direct", "sk-openai-direct-key"))
        self.assertEqual(route_for("anthropic", env), ("aicredits", "sk-aicredits-key-123"))
        self.assertEqual(route_for("google", env), ("aicredits", "sk-aicredits-key-123"))
        split = {**env, "AICREDITS_ANTHROPIC_API_KEY": "sk-ac-claude-key", "AICREDITS_GEMINI_API_KEY": "sk-ac-gemini-key"}
        self.assertEqual(route_for("anthropic", split), ("aicredits", "sk-ac-claude-key"))
        self.assertEqual(route_for("google", split), ("aicredits", "sk-ac-gemini-key"))
        self.assertIn("sk-ac-gemini-key", all_keys(split))
        self.assertEqual(route_for("openai", {**env, "BIE_OPENAI_VIA": "aicredits"}), ("aicredits", "sk-aicredits-key-123"))
        self.assertEqual(route_for("anthropic", {**env, "BIE_ANTHROPIC_VIA": "direct"}), ("", ""))
        with self.assertRaises(ValueError):
            route_for("google", {"BIE_GEMINI_VIA": "openrouter"})
        routes, missing = build_routes(env=env)
        self.assertEqual(missing, [])
        self.assertIsInstance(routes["openai"].client, OpenAIClient)
        self.assertIsInstance(routes["anthropic"].client, OpenAICompatChatClient)
        self.assertEqual(routes["anthropic"].model, DEFAULT_MODELS_VIA["aicredits"]["anthropic"])
        self.assertEqual(routes["google"].model, "google/gemini-4-argon")
        self.assertEqual(sorted(all_keys(env)), sorted(env.values()))

    def test_reseller_ids_are_priced_with_the_reseller_markup(self):
        self.assertEqual(normalize("anthropic/claude-opus-5.5"), "claude-opus-5-5")
        self.assertEqual(normalize("google/gemini-3.1-pro-preview"), "gemini-3.1-pro-preview")
        usage = {"input_tokens": 1_000_000, "output_tokens": 0}
        self.assertEqual(estimate_cost("anthropic/claude-opus-5.5", usage), 4.0)
        self.assertEqual(estimate_cost("anthropic/claude-opus-5.5", usage, via="aicredits"), 4.4)


class SchemaKeywords(unittest.TestCase):
    def test_strict_mode_enforces_new_keywords(self):
        good = {"items": [1, 2, 3], "name": "a"}
        self.assertTrue(validate(good, SCHEMA, strict=True))
        for bad in ({"items": [1, 2], "name": "a"}, {"items": [1] * 6, "name": "a"}, {"items": [1, 2, 3.5], "name": "a"},
                    {"items": [1, 2, True], "name": "a"}, {"items": [1, 2, 3], "name": "  "}, {**good, "extra": 1}):
            with self.assertRaises(SchemaValidationError):
                validate(bad, SCHEMA, strict=True)

    def test_default_mode_keeps_original_behaviour(self):
        self.assertTrue(validate({"items": [1], "name": "", "extra": 1}, SCHEMA))

    def test_provider_schema_keeps_only_supported_keywords(self):
        self.assertNotIn("minItems", json.dumps(provider_schema(SCHEMA, "anthropic")))
        self.assertIn("additionalProperties", json.dumps(provider_schema(SCHEMA, "openai")))
        self.assertNotIn("additionalProperties", json.dumps(provider_schema(SCHEMA, "google")))
        self.assertEqual(provider_schema(SCHEMA, "fake"), SCHEMA)
        self.assertIn("minItems", json.dumps(SCHEMA))  # the original is not modified


class RouteConfig(unittest.TestCase):
    def test_keys_and_models_come_from_environment(self):
        env = {"ANTHROPIC_API_KEY": KEY, "GOOGLE_API_KEY": "AIza-test-key", "BIE_GEMINI_MODEL": "gemini-x"}
        routes, missing = build_routes(env=env)
        self.assertEqual(sorted(routes), ["anthropic", "google"])
        self.assertEqual(missing, ["openai"])
        self.assertEqual(routes["anthropic"].model, DEFAULT_MODELS["anthropic"])
        self.assertEqual(routes["google"].model, "gemini-x")
        self.assertEqual(key_for("google", env), "AIza-test-key")
        self.assertEqual(model_for("openai", {}), DEFAULT_MODELS["openai"])

    def test_missing_keys_are_never_faked_and_fake_uses_real_adapters(self):
        routes, missing = build_routes(env={})
        self.assertEqual((routes, missing), ({}, ["anthropic", "openai", "google"]))
        routes, missing = build_routes(env={}, fake=True)
        self.assertEqual(missing, [])
        self.assertIsInstance(routes["anthropic"], ClaudeAdapter)
        self.assertIsInstance(routes["openai"], GPTAdapter)
        self.assertIsInstance(routes["google"], GeminiAdapter)
        with self.assertRaises(ValueError):
            build_routes(["mistral"], env={})


if __name__ == "__main__":
    unittest.main(verbosity=2)
