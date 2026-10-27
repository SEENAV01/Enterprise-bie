"""Task 044: GPT through ChatGPT Pro (Codex CLI) as BIE's maker, Gemini as checker (offline, fake codex executable)."""
from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests" / "productization" / "document_intelligence"))

import codex_vm  # noqa: E402
import run_brain  # noqa: E402
from bie.brain import cost  # noqa: E402
from bie.brain.fake import BrainFakeClient  # noqa: E402
from bie.model_gateway.gemini_adapter import GeminiAdapter  # noqa: E402
from bie.model_gateway.gpt_adapter import GPTAdapter  # noqa: E402
from bie.model_gateway.live.budget import BudgetExceeded, CostGuard, preflight  # noqa: E402
from bie.model_gateway.live.codex_client import CodexExecClient, build_prompt, classify, parse_events  # noqa: E402
from bie.model_gateway.live.errors import ProviderError  # noqa: E402
from bie.model_gateway.live.gateway import LiveGateway  # noqa: E402
from bie.model_gateway.model_interface import ModelRequest  # noqa: E402
from structural_pdf_fixtures import positioned_text_pdf  # noqa: E402

FAKE = f"{sys.executable} {ROOT / 'bie' / 'brain' / 'fake_codex.py'}"
PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 64).decode()
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["status"],
          "properties": {"status": {"type": "string", "enum": ["ready"], "minLength": 1}}}
LINES = ("Tissue is a group of similar cells doing one job.", "Muscle tissue helps in movement.")
SECRET = "sk-task044-should-never-reach-codex-0123"


def request(rid="understand:page-001:r1", content="Set status to ready."):
    return ModelRequest(request_id=rid, response_schema=SCHEMA,
                        messages=({"role": "system", "content": "Be exact."}, {"role": "user", "content": content}))


class FakeCodex(unittest.TestCase):
    """Helpers: a state folder and environment for the fake codex executable."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name, "codex-state")

    def env(self, mode="ok", **extra):
        return dict(os.environ, BIE_FAKE_CODEX_MODE=mode, BIE_FAKE_CODEX_STATE=str(self.state), OPENAI_API_KEY=SECRET,
                    CODEX_API_KEY=SECRET, **extra)

    def client(self, mode="ok", **extra):
        return CodexExecClient(executable=FAKE, env=self.env(mode, **extra))

    def calls(self):
        path = self.state / "calls.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


class Prompt(unittest.TestCase):
    def test_instructions_task_findings_and_images_are_kept_apart(self):
        image = {"type": "image", "media_type": "image/png", "data": PNG}
        prompt, images = build_prompt([
            {"role": "system", "content": "RULES"},
            {"role": "user", "content": [{"type": "text", "text": "TASK p0001-b0001 | text"}, image]},
            {"role": "assistant", "content": "{\"old\": 1}"},
            {"role": "user", "content": "FIX THIS"}])
        self.assertIn("<bie-instructions>\nRULES\n</bie-instructions>", prompt)
        self.assertIn("<bie-task>\nTASK p0001-b0001 | text\n</bie-task>", prompt)
        self.assertIn("<your-previous-answer>\n{\"old\": 1}\n</your-previous-answer>", prompt)
        self.assertIn("<bie-findings>\nFIX THIS\n</bie-findings>", prompt)
        self.assertIn("1 image(s) are attached", prompt)
        self.assertIn("Do not run commands", prompt)
        self.assertEqual(images, [image])

    def test_event_stream_is_read_like_codex_writes_it(self):
        stream = "\n".join(json.dumps(e) for e in [
            {"type": "thread.started", "thread_id": "t1"}, {"type": "turn.started"},
            {"type": "item.completed", "item": {"id": "i0", "type": "reasoning", "text": "thinking"}},
            {"type": "item.completed", "item": {"id": "i1", "type": "agent_message", "text": "{\"status\": \"ready\"}"}},
            {"type": "turn.completed", "usage": {"input_tokens": 24763, "cached_input_tokens": 24448, "output_tokens": 122,
                                                 "reasoning_output_tokens": 7}}]) + "\nnot json\n"
        got = parse_events(stream)
        self.assertEqual((got["thread_id"], got["message"], got["completed"]), ("t1", "{\"status\": \"ready\"}", True))
        self.assertEqual(got["usage"]["cached_input_tokens"], 24448)

    def test_errors_are_classified(self):
        self.assertEqual(classify("You've hit your usage limit. Upgrade to Pro or try again at 3:05 PM."), "plan_limit")
        self.assertEqual(classify("You've reached your usage limit. Increase your limits to continue using codex."), "plan_limit")
        self.assertEqual(classify("unexpected status 401 Unauthorized: Missing bearer or basic authentication"), "auth")
        self.assertEqual(classify("Not logged in"), "auth")
        self.assertEqual(classify("stream disconnected before completion"), "provider_unavailable")
        self.assertFalse(ProviderError("plan_limit").retryable)


class Client(FakeCodex):
    def test_success_with_schema_image_usage_and_no_api_key(self):
        client = self.client()
        content = [{"type": "text", "text": "Set status to ready."}, {"type": "image", "media_type": "image/jpeg", "data": PNG}]
        raw = client.responses_create(model="gpt-6.1-sol", messages=request(content=content).messages, response_schema=SCHEMA)
        self.assertEqual(json.loads(raw["content"]), {"status": "ready"})
        self.assertGreater(raw["usage"]["input_tokens"], 0)
        self.assertIsNotNone(client.last_seconds)
        call = self.calls()[0]
        self.assertFalse(call["api_key_visible"])                 # ChatGPT sign-in only, never an API key
        self.assertEqual(call["images"], [".jpg"])
        self.assertTrue(call["images_exist"])
        for flag in ("--json", "--ephemeral", "--skip-git-repo-check", "--output-schema", "-o", "--ignore-rules"):
            self.assertIn(flag, call["args"])
        self.assertEqual(call["args"][call["args"].index("--sandbox") + 1], "read-only")
        self.assertEqual(call["model"], "gpt-6.1-sol")

    def test_schema_is_sent_with_openai_keywords_only(self):
        seen = {}

        def run(cmd, **kwargs):
            seen["schema"] = json.loads(Path(cmd[cmd.index("--output-schema") + 1]).read_text())
            Path(cmd[cmd.index("-o") + 1]).write_text('{"status": "ready"}')
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({"type": "turn.completed", "usage": {}}), stderr="")
        CodexExecClient(executable="codex", run=run).responses_create(model="m", messages=request().messages, response_schema=SCHEMA)
        self.assertNotIn("minLength", json.dumps(seen["schema"]))

    def test_plan_limit_auth_missing_and_no_cli(self):
        with self.assertRaises(ProviderError) as caught:
            self.client("plan_limit_after=0").responses_create(model="m", messages=request().messages, response_schema=SCHEMA)
        self.assertEqual(caught.exception.kind, "plan_limit")
        with self.assertRaises(ProviderError) as caught:
            self.client("auth_missing").responses_create(model="m", messages=request().messages, response_schema=SCHEMA)
        self.assertEqual(caught.exception.kind, "auth")
        with self.assertRaises(ProviderError) as caught:
            CodexExecClient(executable="/nonexistent/codex").responses_create(model="m", messages=request().messages)
        self.assertEqual(caught.exception.kind, "config")

    def test_timeout_is_a_timeout(self):
        def run(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, 1)
        with self.assertRaises(ProviderError) as caught:
            CodexExecClient(executable="codex", run=run, timeout=1).responses_create(model="m", messages=request().messages)
        self.assertEqual(caught.exception.kind, "timeout")

    def test_login_status_and_plan_usage(self):
        self.assertEqual(self.client().login_status(), {"logged_in": True, "mode": "Logged in using ChatGPT"})
        self.assertFalse(self.client("auth_missing").login_status()["logged_in"])
        usage = self.client().plan_usage()
        self.assertEqual(usage["rateLimits.planType"], "pro")
        self.assertIn("rateLimits.primary.usedPercent", usage)
        self.assertNotIn("email", json.dumps(usage))                  # numbers and the plan name only
        self.assertIn("unavailable", self.client("auth_missing").plan_usage())


class GatewayAndGuard(FakeCodex):
    def gateway(self, mode="ok", cap=1.0):
        guard = CostGuard(cap, rate=100.0)
        routes = {"codex": GPTAdapter(self.client(mode), "gpt-6.1-sol"), "google": GeminiAdapter(BrainFakeClient("google"), "fake-google")}
        return LiveGateway(routes, sleep=lambda s: None, guard=guard), guard

    def test_subscription_calls_cost_no_rupees_and_are_marked(self):
        gateway, guard = self.gateway(cap=1.0)                      # a Rs 1 cap does not stop subscription calls
        for n in range(3):
            gateway.complete("codex", request(f"understand:page-00{n}:r1"), prompt_version="t/1")
        rows = gateway.ledger.rows
        self.assertEqual({(r["billing"], r["via"], r["cost_usd"]) for r in rows}, {("subscription", "codex", 0.0)})
        self.assertGreater(rows[0]["latency_ms"], 0)
        self.assertEqual(guard.spent_inr, 0.0)

    def test_plan_limit_is_not_retried_and_stops_the_run(self):
        gateway, guard = self.gateway("plan_limit_after=0")
        with self.assertRaises(ProviderError) as caught:
            gateway.complete("codex", request(), prompt_version="t/1")
        self.assertEqual(caught.exception.kind, "plan_limit")
        self.assertEqual(len(self.calls()), 1)
        self.assertTrue(guard.stop_reason.startswith("plan_limit"))
        with self.assertRaises(BudgetExceeded):
            gateway.complete("google", request("understand:page-002:r1:review"), prompt_version="t/1")

    def test_preflight_checks_sign_in_plan_usage_and_vision(self):
        gateway, _ = self.gateway(cap=100.0)
        checked = preflight(gateway, vision=True)
        self.assertTrue(checked["passed"])
        codex = checked["routes"]["codex"]
        self.assertEqual((codex["login"]["logged_in"], codex["vision"]), (True, "ok"))
        self.assertIn("rateLimits.primary.usedPercent", codex["plan_usage_before"])
        self.assertEqual(checked["routes"]["google"]["vision"], "ok")
        self.assertEqual(self.calls()[-1]["images"], [".png"])

    def test_preflight_stops_without_any_call_when_codex_is_not_signed_in(self):
        gateway, guard = self.gateway("auth_missing", cap=100.0)
        checked = preflight(gateway)
        self.assertFalse(checked["passed"])
        self.assertEqual(checked["routes"]["codex"]["error_kind"], "auth")
        self.assertEqual(self.calls(), [])                            # no exec call was made
        self.assertTrue(guard.stopped)

    def test_a_model_that_cannot_see_images_fails_the_vision_check(self):
        class Blind(BrainFakeClient):
            def _respond(self, model, messages, schema):
                if "number" in (schema or {}).get("properties", {}):
                    return {"content": '{"number": "none"}', "finish_reason": "stop", "model": model,
                            "usage": {"input_tokens": 1, "output_tokens": 1}}
                return super()._respond(model, messages, schema)
        gateway = LiveGateway({"google": GeminiAdapter(Blind("google"), "fake-google")}, sleep=lambda s: None)
        checked = preflight(gateway, vision=True)
        self.assertEqual(checked["routes"]["google"]["error_kind"], "vision")


class Estimate(unittest.TestCase):
    def test_a_codex_maker_leaves_only_the_checker_share(self):
        api = cost.estimate("understand", 4, rate=94.59, maker_model="gpt-6.1-sol", reviewer_model="google/gemini-4-argon")
        plan = cost.estimate("understand", 4, rate=94.59, maker_model="gpt-6.1-sol", reviewer_model="google/gemini-4-argon",
                             maker_subscription=True)
        self.assertEqual(plan["maker_billing"], "subscription")
        self.assertEqual(plan["price_scale"], 0.16)
        self.assertAlmostEqual(plan["total_inr"], api["total_inr"] * 0.16, delta=0.05)


class RunBrainWithCodex(FakeCodex):
    def setUp(self):
        super().setUp()
        self.source = Path(self.tmp.name, "chapter.pdf")
        self.source.write_bytes(positioned_text_pdf([[(72, 720 - i * 20, LINES[i % 2]) for i in range(12)] for _ in range(3)]))

    def run_brain(self, out, mode="ok", *extra):
        env = {"BIE_CODEX_BIN": FAKE, "BIE_FAKE_CODEX_MODE": mode, "BIE_FAKE_CODEX_STATE": str(self.state), "OPENAI_API_KEY": SECRET}
        log = io.StringIO()
        with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(log):
            code = run_brain.main(["--fake", "--maker", "codex", "--reviewer", "google", "--section", "understand",
                                   "--source", str(self.source), "--out", str(Path(self.tmp.name, out)), "--workers", "1",
                                   "--max-inr", "30", *extra])
        summary = json.loads(Path(self.tmp.name, out, "SUMMARY.json").read_text(encoding="utf-8"))
        return code, summary, log.getvalue()

    def test_codex_maker_and_gemini_checker_pass_the_chapter(self):
        code, summary, log = self.run_brain("ok")
        self.assertEqual((code, summary["status"]), (0, "ok"))
        self.assertEqual(summary["models"], {"codex": "gpt-6.1-sol", "google": "fake-google"})
        self.assertEqual(summary["reviewer_independence"], "other_company")
        self.assertEqual(summary["preflight"]["routes"]["codex"]["vision"], "ok")
        self.assertEqual(summary["cost"]["subscription"]["calls"], 2 + 3 + 1)      # preflight x2, 3 pages, the map
        self.assertTrue(all("seconds" in p for p in summary["pages"]))
        self.assertIn("rateLimits.primary.usedPercent", summary["plan_usage_after"]["codex"])
        self.assertIn("pahra plan codex::before the run", log)
        self.assertFalse(any(c["api_key_visible"] for c in self.calls()))
        page_calls = [c for c in self.calls() if c["prompt_chars"] > 1000]
        self.assertTrue(page_calls and all(c["images"] == [".png"] for c in page_calls[:3]))   # both eyes reach the maker
        self.assertNotIn(SECRET, Path(self.tmp.name, "ok", "SUMMARY.json").read_text())
        record = json.loads(Path(self.tmp.name, "ok", "records", "understand--page-001.json").read_text())
        self.assertEqual((record["maker_route"], record["maker_model"]), ("codex", "gpt-6.1-sol"))

    def test_codex_checks_its_own_work_in_a_fresh_call_when_navin_says_so(self):
        """Navin, 27 October 2026: no waiting on the free Google key and no paid call; the checker on the plan too."""
        env = {"BIE_CODEX_BIN": FAKE, "BIE_FAKE_CODEX_MODE": "ok", "BIE_FAKE_CODEX_STATE": str(self.state)}
        with mock.patch.dict(os.environ, env, clear=False), contextlib.redirect_stdout(io.StringIO()):
            code = run_brain.main(["--fake", "--maker", "codex", "--reviewer", "codex", "--reviewer-model", "same", "--section",
                                   "understand", "--source", str(self.source), "--out", str(Path(self.tmp.name, "own")),
                                   "--workers", "1", "--max-inr", "30"])
        summary = json.loads(Path(self.tmp.name, "own", "SUMMARY.json").read_text(encoding="utf-8"))
        self.assertEqual((code, summary["status"]), (0, "ok"))
        self.assertEqual(summary["models"], {"codex": "gpt-6.1-sol", "codex-checker": "gpt-6.1-sol"})
        self.assertEqual((summary["reviewer_route"], summary["reviewer_independence"]), ("codex-checker", "same_model_temporary"))
        self.assertEqual(summary["estimate"]["reviewer_billing"], "subscription")
        self.assertEqual(summary["estimate"]["total_inr"], 0.0)
        self.assertEqual(summary["cost"]["total_inr"], 0.0)
        self.assertEqual(summary["cost"]["subscription"]["calls"], 4 + 3 + 3 + 1 + 1)   # preflight x2 per route, 3 pages + reviews, map + review
        self.assertEqual(summary["preflight"]["routes"]["codex-checker"]["login"]["logged_in"], True)
        record = json.loads(Path(self.tmp.name, "own", "records", "understand--page-001.json").read_text())
        self.assertEqual((record["reviewer_route"], record["reviewer_model"], record["reviewer_independence"]),
                         ("codex-checker", "gpt-6.1-sol", "same_model_temporary"))
        self.assertTrue(record["rounds"][0]["review"]["value"]["verdict"] == "pass")
        with self.assertRaises(SystemExit):           # the weakest check is never silent: it must be asked for
            run_brain.main(["--fake", "--maker", "codex", "--reviewer", "codex", "--section", "understand",
                            "--source", str(self.source), "--out", str(Path(self.tmp.name, "bad"))])

    def test_plan_limit_stops_resumably_and_a_resume_finishes(self):
        # preflight uses 2 calls, page 1 the 3rd; the 4th call (page 2) hits the plan limit
        code, summary, log = self.run_brain("first", "plan_limit_after=3")
        self.assertEqual((code, summary["status"]), (0, "stopped: plan limit"))
        self.assertEqual([p["status"] for p in summary["pages"]], ["passed", "stopped", "stopped"])
        self.assertIn("::warning title=bie brain understand", log)
        (self.state / "exec-count").write_text("0")                  # the plan window has reset
        code, summary, _ = self.run_brain("second", "ok", "--resume-from", str(Path(self.tmp.name, "first")))
        self.assertEqual((code, summary["status"]), (0, "ok"))
        self.assertEqual(summary["resume"], {"pages_reused": 1, "pages_to_run": 2})
        self.assertEqual([p["reused"] for p in summary["pages"]], [True, False, False])
        self.assertEqual(summary["map_status"], "passed")

    def test_schema_error_fails_the_step_after_one_repair(self):
        code, summary, _ = self.run_brain("bad", "schema_error_after=2")
        self.assertEqual(summary["pages"][0]["status"], "failed")
        record = json.loads(Path(self.tmp.name, "bad", "records", "understand--page-001.json").read_text())
        self.assertEqual(record["rounds"][0]["maker_error"]["kind"], "schema_invalid")

    def test_auth_missing_stops_at_preflight(self):
        code, summary, log = self.run_brain("noauth", "auth_missing")
        self.assertEqual((code, summary["status"]), (1, "stopped: preflight"))
        self.assertEqual(summary["preflight"]["routes"]["codex"]["error_kind"], "auth")
        self.assertIn("sign in again with bie-setup", log)
        self.assertFalse(Path(self.tmp.name, "noauth", "chapter_map.json").exists())


class VmJobs(FakeCodex):
    JOB = {"job": "bie.vm-job/1", "id": "t044-smoke", "section": "understand",
           "source": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-inputs/chapters/tissues-and-its-types.pdf",
           "resume_from": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/39627682253-brain-chain",
           "course": "title=10. Tissues and Its Types;subject=Science and Technology", "models": "google=google/gemini-4-argon",
           "routes": "google=aicredits", "max_inr": 30}

    def test_validation_keeps_jobs_to_a_fixed_shape(self):
        job = codex_vm.validate(dict(self.JOB))
        self.assertEqual((job["maker"], job["reviewer"], job["workers"]), ("codex", "google", 2))
        bad = [dict(self.JOB, id="Bad id"), dict(self.JOB, source="http://insecure"), dict(self.JOB, section="rm"),
               dict(self.JOB, course="a\nb"), dict(self.JOB, models="google=x;rm -rf /"), dict(self.JOB, max_inr=5000),
               dict(self.JOB, workers=True), dict(self.JOB, extra="x"), dict(self.JOB, maker="anthropic"),
               dict(self.JOB, fake=True), {k: v for k, v in self.JOB.items() if k != "source"}]
        for job in bad:
            with self.subTest(job=str(job)[:60]), self.assertRaises(codex_vm.JobError):
                codex_vm.validate(job)

    def test_a_codex_checker_is_a_valid_job(self):
        job = codex_vm.validate(dict(self.JOB, reviewer="codex", reviewer_model="same", models="", routes=""))
        self.assertEqual((job["maker"], job["reviewer"], job["reviewer_model"]), ("codex", "codex", "same"))
        argv = codex_vm.argv(job, Path(self.tmp.name, "out"))
        self.assertEqual(argv[argv.index("--reviewer") + 1], "codex")
        self.assertEqual(argv[argv.index("--reviewer-model") + 1], "same")
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate(dict(self.JOB, reviewer="anthropic"))

    def test_argv_has_no_shell_and_every_value_as_one_argument(self):
        cmd = codex_vm.argv(codex_vm.validate(dict(self.JOB)), Path("/out"), python="py")
        self.assertEqual(cmd[:3], ["py", "-B", str(ROOT / "tools" / "run_brain.py")])
        self.assertEqual(cmd[cmd.index("--course") + 1], self.JOB["course"])
        self.assertEqual(cmd[cmd.index("--maker") + 1], "codex")
        self.assertEqual(cmd[cmd.index("--max-inr") + 1], "30")

    def test_poll_runs_a_queued_job_and_publishes_results(self):
        base = Path(self.tmp.name)
        remote = base / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        seed = base / "seed"
        subprocess.run(["git", "init", "-q", str(seed)], check=True)
        source = base / "chapter.pdf"
        source.write_bytes(positioned_text_pdf([[(72, 720 - i * 20, LINES[i % 2]) for i in range(12)]]))
        job = {"job": "bie.vm-job/1", "id": "t044-local", "section": "understand", "source": "https://example.invalid/x.pdf",
               "course": "title=Offline;subject=Biology", "max_inr": 30, "workers": 1, "fake": True}
        (seed / "jobs").mkdir()
        (seed / "jobs" / "t044-local.json").write_text(json.dumps(job))
        git = ["git", "-C", str(seed), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["checkout", "-q", "-b", "codex-jobs"], check=True)
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "job"], check=True)
        subprocess.run(git + ["push", "-q", str(remote), "codex-jobs"], check=True)
        env = {"BIE_HOME": str(base / "home"), "BIE_REPO_URL": str(remote), "BIE_VM_ALLOW_FAKE": "1", "BIE_CODEX_BIN": FAKE,
               "BIE_FAKE_CODEX_STATE": str(self.state), "BIE_FAKE_CODEX_MODE": "ok"}
        original = codex_vm.argv

        def argv_with_local_pdf(job, out, python=sys.executable):
            cmd = original(job, out, python)
            cmd[cmd.index("--source") + 1] = str(source)               # no network in tests
            return cmd
        with mock.patch.dict(os.environ, env), mock.patch.object(codex_vm, "argv", argv_with_local_pdf), \
                contextlib.redirect_stdout(io.StringIO()):
            results = codex_vm.poll(update_main=False)
            again = codex_vm.poll(update_main=False)
        self.assertEqual([r["status"] for r in results], ["ok"])
        self.assertEqual(again, [])                                    # a finished job is never run twice
        show = lambda ref: subprocess.run(["git", "--git-dir", str(remote), "show", ref], capture_output=True, text=True).stdout
        result = json.loads(show("codex-jobs:jobs/t044-local.result.json"))
        self.assertEqual((result["status"], result["results"]), ("ok", "blindtest-results:runs/vm-t044-local-brain-understand"))
        summary = json.loads(show("blindtest-results:runs/vm-t044-local-brain-understand/SUMMARY.json"))
        self.assertEqual(summary["models"]["codex"], "gpt-6.1-sol")

    def test_a_refused_job_is_reported_not_run(self):
        rep = mock.Mock()
        rep.show.return_value = json.dumps(dict(self.JOB, id="other-name"))
        result = codex_vm.run_one(rep, "jobs/t044-smoke.json")
        self.assertEqual(result["status"], "refused")
        self.assertIn("id: must match", result["error"])
        rep.commit_files.assert_not_called()


if __name__ == "__main__":
    unittest.main()
