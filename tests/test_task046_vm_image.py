"""Task 046 one-shot test: images through the ChatGPT plan (Codex's built-in image_gen tool) and the LOOK-01 look check,
as VM job sections ``image`` and ``look`` (offline: the fake codex executable and a fake reviewer client)."""
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

import codex_vm  # noqa: E402
import vm_image  # noqa: E402
import vm_look  # noqa: E402
from bie.brain import look  # noqa: E402
from bie.model_gateway.gemini_adapter import GeminiAdapter  # noqa: E402
from bie.model_gateway.live.codex_client import IMAGE_FEATURES_OFF, IMAGE_INSTRUCTIONS, CodexExecClient, image_events  # noqa: E402
from bie.model_gateway.live.errors import ProviderError  # noqa: E402
from bie.model_gateway.live.gateway import LiveGateway  # noqa: E402

FAKE = f"{sys.executable} {ROOT / 'bie' / 'brain' / 'fake_codex.py'}"
SECRET = "sk-task046-should-never-reach-codex-0123"
PROMPT = ("Photoreal microscopic view of one single thin layer of flat squamous epithelial cells, irregular interlocking "
          "outlines, one nucleus per cell, dark background, no text, no letters.")
PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000d49444154789c6360f8cf00000301010018dd8db00000000049454e44ae426082")
FRAME = "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/t046-oneshot/route-1/frame-1.png"


def prompts(n=2):
    return {"schema": "bie.image-prompts/1", "id": "t046-oneshot", "shot": {"shot_id": "b37.2"},
            "prompts": [{"id": f"r2-{i}", "prompt": PROMPT} for i in range(1, n + 1)]}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.state = self.base / "codex-state"
        self.home = self.base / "codex-home"

    def client(self, mode="ok", image="home"):
        env = dict(os.environ, BIE_FAKE_CODEX_MODE=mode, BIE_FAKE_CODEX_STATE=str(self.state), BIE_FAKE_CODEX_IMAGE=image,
                   OPENAI_API_KEY=SECRET, CODEX_HOME=str(self.home))
        return CodexExecClient(executable=FAKE, env=env, codex_home=str(self.home))

    def calls(self):
        return [json.loads(line) for line in (self.state / "calls.jsonl").read_text().splitlines()]


class ImagesThroughThePlan(Base):
    def test_one_image_is_saved_from_codex_home_with_only_the_image_tool_on(self):
        info = self.client().generate_image(PROMPT, self.base / "out" / "r2-1")
        self.assertEqual((info["file"], info["found_by"], info["bytes"]), ("r2-1.png", "codex_home", len(PNG)))
        self.assertEqual((self.base / "out" / "r2-1.png").read_bytes(), PNG)
        self.assertIn("image_generation", info["event_types"])
        call = self.calls()[-1]
        self.assertNotIn("image_generation", call["disabled"])
        self.assertEqual(set(call["disabled"]), set(IMAGE_FEATURES_OFF))
        self.assertIn("shell_tool", call["disabled"])
        self.assertEqual(call["instructions"], IMAGE_INSTRUCTIONS)
        self.assertFalse(call["api_key_visible"])
        self.assertIn("read-only", call["args"])

    def test_an_image_only_in_the_event_stream_is_decoded_and_none_is_an_error(self):
        info = self.client(image="base64").generate_image(PROMPT, self.base / "out" / "r2-2")
        self.assertEqual(info["found_by"], "event_base64")
        self.assertTrue((self.base / "out" / "r2-2.png").read_bytes().startswith(b"\x89PNG"))
        with self.assertRaises(ProviderError) as err:
            self.client(image="none").generate_image(PROMPT, self.base / "out" / "r2-3")
        self.assertEqual(err.exception.kind, "malformed")

    def test_event_shapes_are_read_without_one_exact_name(self):
        line = json.dumps({"type": "item.completed", "item": {"type": "image_generation_call", "revised_prompt": "x",
                                                              "result": base64.b64encode(PNG * 4).decode()}})
        found = image_events(line + "\n" + json.dumps({"type": "item.completed", "item": {"type": "x", "path": "/a/b.png"}}))
        self.assertEqual((found["revised_prompt"], found["paths"], len(found["images"])), ("x", ["/a/b.png"], 1))

    def test_the_tool_makes_every_image_and_reads_the_plan_before_and_after(self):
        summary = vm_image.run(prompts(2), self.base / "run", client=self.client())
        self.assertEqual((summary["status"], [r["status"] for r in summary["images"]]), ("ok", ["made", "made"]))
        self.assertIn("rateLimits.primary.usedPercent", summary["plan_usage_before"])
        self.assertIn("rateLimits.primary.usedPercent", summary["plan_usage_after"])
        self.assertEqual(summary["cost"]["total_inr"], 0.0)
        self.assertTrue((self.base / "run" / "images" / "r2-2.png").exists())
        for name in ("SUMMARY.json", "prompts.json", "IMAGES.md"):
            self.assertTrue((self.base / "run" / name).exists(), name)

    def test_a_used_up_plan_stops_the_run(self):
        summary = vm_image.run(prompts(3), self.base / "run", client=self.client(mode="plan_limit_after=1"))
        self.assertEqual(summary["status"], "stopped: plan limit")
        self.assertEqual([r["status"] for r in summary["images"]], ["made", "failed"])

    def test_not_signed_in_stops_before_any_image(self):
        summary = vm_image.run(prompts(1), self.base / "run", client=self.client(mode="auth_missing"))
        self.assertEqual((summary["status"], summary["images"]), ("stopped: not signed in", []))

    def test_prompt_files_are_checked(self):
        self.assertEqual(len(vm_image.load_prompts(json.dumps(prompts(4)))["prompts"]), 4)
        bad = [dict(prompts(), schema="x"), prompts(5), dict(prompts(1), prompts=[{"id": "Bad", "prompt": PROMPT}]),
               dict(prompts(1), prompts=[{"id": "a", "prompt": "short"}]),
               dict(prompts(1), prompts=[{"id": "a", "prompt": PROMPT + "\x07"}]),
               dict(prompts(1), prompts=[{"id": "a", "prompt": PROMPT}, {"id": "a", "prompt": PROMPT}])]
        for data in bad:
            with self.subTest(data=str(data)[:80]), self.assertRaises(ValueError):
                vm_image.load_prompts(json.dumps(data))


class Reviewer:
    """A fake Google client that answers the LOOK-01 schema and remembers what it was sent."""
    via = "direct"

    def __init__(self):
        self.calls = []

    def generate(self, *, model, messages, schema=None):
        self.calls.append(messages)
        value = {"scores": {a: 4 for a, _ in look.AXES}, "reasons": {a: f"the {a} reads clearly below the reference" for a, _ in look.AXES},
                 "biggest_gap": "the cells look like plastic tiles", "verdict": "far"}
        return {"content": json.dumps(value), "finish_reason": "stop", "model": model,
                "usage": {"input_tokens": 3000, "output_tokens": 400}}


class LookCheck(Base):
    REQUEST = {"schema": "bie.look-request/1", "shot": {"sentence": "Simple squamous में पतली exchange boundary", "must_show": "one thin layer"},
               "reference": {"private_set": "t046-squamous", "description": "photoreal tissue, translucent cells, shallow focus"},
               "routes": {"route-1": [FRAME], "route-2": [FRAME.replace("route-1", "route-2")]}}

    def gateway(self, client):
        return LiveGateway({"google": GeminiAdapter(client, "gemini-3.8-flash")}, sleep=lambda s: None)

    def opener(self, request, timeout=0):
        return contextlib.closing(io.BytesIO(PNG))

    def test_requests_are_checked(self):
        vm_look.load_request(json.dumps(self.REQUEST))
        bad = [dict(self.REQUEST, schema="x"),
               dict(self.REQUEST, routes={"route-1": ["https://example.com/a.png"]}),
               dict(self.REQUEST, routes={"route-1": [FRAME] * 4}),
               dict(self.REQUEST, reference={"description": ""}),
               dict(self.REQUEST, reference={"private_set": "../etc", "description": "x"}),
               dict(self.REQUEST, shot={})]
        for data in bad:
            with self.subTest(data=str(data)[:80]), self.assertRaises(ValueError):
                vm_look.load_request(json.dumps(data))

    def test_private_reference_frames_are_sent_but_never_written_out(self):
        refs = self.base / "bie" / "private" / "refs" / "t046-squamous"
        refs.mkdir(parents=True)
        for i in range(3):
            (refs / f"bench-{i}.png").write_bytes(PNG + bytes([i]))
        client = Reviewer()
        summary = vm_look.run(json.loads(json.dumps(self.REQUEST)), self.base / "out", max_inr=5, gateway=self.gateway(client),
                              opener=self.opener, home=self.base / "bie")
        self.assertEqual((summary["status"], summary["reference"]), ("ok", "frames"))
        self.assertEqual([r["name"] for r in summary["reference_files"]], ["bench-0.png", "bench-1.png", "bench-2.png"])
        images = [p for p in client.calls[0][1]["content"] if p["type"] == "image"]
        self.assertEqual(len(images), 4)                                   # 3 reference frames + 1 of ours
        written = b"".join(p.read_bytes() for p in (self.base / "out").iterdir())
        for i in range(3):
            self.assertNotIn(base64.b64encode(PNG + bytes([i])), written)
        self.assertEqual(summary["table"]["route-1"], {"mean": 4.0, "same_class": 4, "verdict": "far"})
        self.assertTrue((self.base / "out" / "LOOK.md").read_text(encoding="utf-8").startswith("# LOOK-01"))

    def test_without_the_private_set_the_written_description_is_used_and_said(self):
        client = Reviewer()
        summary = vm_look.run(json.loads(json.dumps(self.REQUEST)), self.base / "out", max_inr=5, gateway=self.gateway(client),
                              opener=self.opener, home=self.base / "nowhere")
        self.assertEqual(summary["reference"], "description")
        text = client.calls[0][1]["content"][0]["text"]
        self.assertIn("photoreal tissue, translucent cells", text)
        self.assertEqual(len([p for p in client.calls[0][1]["content"] if p["type"] == "image"]), 1)


class VmJobSections(Base):
    IMAGE = {"job": "bie.vm-job/1", "id": "t046-oneshot-images", "section": "image", "max_images": 4,
             "prompts": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/t046-oneshot/prompts.json"}
    LOOK = {"job": "bie.vm-job/1", "id": "t046-oneshot-look", "section": "look", "max_inr": 5, "routes": "google=direct",
            "models": "google=gemini-3.8-flash",
            "request": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/t046-oneshot/look-request.json"}

    def test_the_new_sections_keep_a_fixed_shape(self):
        codex_vm.validate(dict(self.IMAGE))
        codex_vm.validate(dict(self.LOOK))
        bad = [{k: v for k, v in self.IMAGE.items() if k != "prompts"}, dict(self.IMAGE, max_images=5),
               dict(self.IMAGE, max_images=True), dict(self.IMAGE, prompts="http://x"), {k: v for k, v in self.LOOK.items() if k != "request"},
               dict(self.IMAGE, section="lesson", chapter_map="https://x.example/c.json")]
        for job in bad:
            with self.subTest(job=str(job)[:70]), self.assertRaises(codex_vm.JobError):
                codex_vm.validate(job)

    def test_argv_runs_the_fixed_tools_without_a_shell(self):
        cmd = codex_vm.argv(codex_vm.validate(dict(self.IMAGE)), Path("/out"), python="py")
        self.assertEqual(cmd, ["py", "-B", str(ROOT / "tools" / "vm_image.py"), "--prompts", self.IMAGE["prompts"], "--out", "/out",
                               "--max-images", "4"])
        cmd = codex_vm.argv(codex_vm.validate(dict(self.LOOK)), Path("/out"), python="py")
        self.assertEqual(cmd[:3], ["py", "-B", str(ROOT / "tools" / "vm_look.py")])
        self.assertEqual(cmd[cmd.index("--routes") + 1], "google=direct")

    def test_a_poll_that_moved_main_runs_again_with_the_new_code_once(self):
        """26 October 2026: the first image job after PR #77 was refused as "unknown fields" because the poll had loaded
        the runner before it checked out the new main. Now a poll that moves the checkout starts itself again, once."""
        heads = iter(["old", "new"])

        def git(cmd, **kw):
            out = next(heads) if cmd[-2:] == ["rev-parse", "HEAD"] else ""
            return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")

        class Started(Exception):
            pass

        def execve(path, args, env):
            raise Started(path, args, env)

        env = {"BIE_HOME": str(self.base / "home")}
        with mock.patch.dict(os.environ, env), mock.patch.object(codex_vm.subprocess, "run", git), \
                mock.patch.object(codex_vm.os, "execve", execve), self.assertRaises(Started) as started:
            os.environ.pop(codex_vm.FRESH_ENV, None)
            codex_vm.poll(python="py")
        path, args, new_env = started.exception.args
        self.assertEqual((path, args), ("py", ["py", "-B", str(ROOT / "tools" / "codex_vm.py"), "poll"]))
        self.assertEqual(new_env[codex_vm.FRESH_ENV], "1")
        lock = self.base / "home" / "poll.lock"
        with lock.open("w") as handle:                                   # the lock was released before the new start
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for heads_seen, fresh in ((["same", "same"], None), (["old", "new"], "1")):    # no move, or already the new code
            heads = iter(heads_seen)
            with self.subTest(heads=heads_seen, fresh=fresh), \
                    mock.patch.dict(os.environ, dict(env, **({codex_vm.FRESH_ENV: fresh} if fresh else {}))), \
                    mock.patch.object(codex_vm.subprocess, "run", git), mock.patch.object(codex_vm.os, "execve", execve), \
                    mock.patch.object(codex_vm, "repo") as rep, mock.patch.object(codex_vm, "queued", return_value=[]):
                if not fresh:
                    os.environ.pop(codex_vm.FRESH_ENV, None)
                (self.base / "home" / "pyproject.sha256").write_text(
                    __import__("hashlib").sha256((ROOT / "pyproject.toml").read_bytes()).hexdigest())
                self.assertEqual(codex_vm.poll(python="py"), [])
                rep.return_value.fetch.assert_called_once_with(codex_vm.JOBS_BRANCH)

    def test_poll_publishes_the_image_files(self):
        remote = self.base / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        seed = self.base / "seed"
        subprocess.run(["git", "init", "-q", str(seed)], check=True)
        prompt_file = self.base / "prompts.json"
        prompt_file.write_text(json.dumps(prompts(2)))
        (seed / "jobs").mkdir()
        (seed / "jobs" / "t046-oneshot-images.json").write_text(json.dumps(self.IMAGE))
        git = ["git", "-C", str(seed), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["checkout", "-q", "-b", "codex-jobs"], check=True)
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "job"], check=True)
        subprocess.run(git + ["push", "-q", str(remote), "codex-jobs"], check=True)
        env = {"BIE_HOME": str(self.base / "home"), "BIE_REPO_URL": str(remote), "BIE_CODEX_BIN": FAKE, "CODEX_HOME": str(self.home),
               "BIE_FAKE_CODEX_STATE": str(self.state), "BIE_FAKE_CODEX_MODE": "ok", "BIE_FAKE_CODEX_IMAGE": "home"}
        original = codex_vm.argv

        def argv_with_local_prompts(job, out, python=sys.executable):
            cmd = original(job, out, python)
            cmd[cmd.index("--prompts") + 1] = str(prompt_file)              # no network in tests
            return cmd
        with mock.patch.dict(os.environ, env), mock.patch.object(codex_vm, "argv", argv_with_local_prompts), \
                contextlib.redirect_stdout(io.StringIO()):
            results = codex_vm.poll(update_main=False)
        self.assertEqual([(r["status"], r["images_made"]) for r in results], [("ok", 2)])
        show = lambda ref: subprocess.run(["git", "--git-dir", str(remote), "show", ref], capture_output=True).stdout
        self.assertEqual(show("blindtest-results:runs/vm-t046-oneshot-images-brain-image/images/r2-1.png"), PNG)
        result = json.loads(show("codex-jobs:jobs/t046-oneshot-images.result.json"))
        self.assertEqual((result["status"], result["images_made"], result["cost_inr"]), ("ok", 2, 0.0))
        self.assertIn("rateLimits.primary.usedPercent", result["plan_usage_before"])


if __name__ == "__main__":
    unittest.main()
