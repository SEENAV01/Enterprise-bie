"""Codex maker route: GPT through Navin's ChatGPT Pro subscription, called with OpenAI's own Codex CLI.

Each BIE request becomes one ``codex exec`` run (non-interactive mode, OpenAI's documented way to
script Codex): the instructions and the task go in on stdin, page images as ``--image`` files, the
output JSON schema as ``--output-schema``; ``--json`` gives the event stream with token usage and
``--output-last-message`` the final JSON answer. The run is read-only, ephemeral and starts in an
empty folder, so the model answers from the message and the images only.

Rules this client keeps (OpenAI docs, read 22 Oct 2026, learn.chatgpt.com/docs/non-interactive-mode):
- Only Codex, never the ChatGPT website. Sign-in is ChatGPT-managed (``codex login --device-auth``)
  on a private machine Navin owns. It is never used in this public repository's GitHub Actions.
- No API key is used: every variable named like a key, token or secret (``OPENAI_API_KEY``, ``CODEX_API_KEY``,
  the AICredits key) is removed from the Codex process's environment.
- ``~/.codex/auth.json`` stays in ``CODEX_HOME`` on that machine; this client never reads it.

Usage is billed to the subscription, not in rupees: each call reports ``billing: subscription``,
the token counts Codex reports and the wall time. A used-up plan window raises ``plan_limit`` (never
retried); BIE stops the run as "stopped: plan limit" and it can be resumed later.

Lean calls (seekh → BIE, from the tissue run of 23 Oct 2026): Codex sends its own agent instructions and
tool definitions with every call, which BIE never uses (14,208 input tokens for job 1's preflight of a
one-line question). A lean call replaces those instructions with ``LEAN_INSTRUCTIONS`` and switches off
the tools and features in ``LEAN_FEATURES_OFF``; the model can then not run commands, browse or start
agents at all. ``BIE_CODEX_LEAN=0`` turns it off.
"""
from __future__ import annotations

import base64
import json
import os
import queue
import re
import shlex
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from .errors import ProviderError, redact
from .messages import provider_schema, split_messages, text_of

DEFAULT_MODEL = "gpt-6.1-sol"     # the maker that passed Section 1 pages in Task 039; override with BIE_CODEX_MODEL
DEFAULT_TIMEOUT = 1800.0
SUFFIX = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
ANSWER_RULES = ("Answer from this message and the attached images only. Do not run commands, read or write files, "
                "or browse. Reply with one JSON object that matches the required schema, nothing else.")
LEAN_INSTRUCTIONS = ("You are the model engine behind BIE (Book Intelligence Engine), run by BIE through Codex with no "
                     "person watching. Each message holds BIE's instructions, one task, sometimes your earlier answer "
                     "with findings to fix, and the attached page images. Work only from that message and the images: "
                     "no commands, files, browsing, questions or other agents. Take the time the task needs, then reply "
                     "with exactly one JSON object that matches the output schema, and nothing else.")
# Codex 0.162.1 (pinned in deployment/codex-vm/setup.sh). A request captured offline against a local stand-in server
# carried about 12,200 tokens of Codex's own instructions, tools and agent texts (o200k tokenizer); with these settings
# about 3,800 remain (the few Codex always sends). Every name was checked against that version: an unknown setting or
# feature stops codex before it sends anything (--strict-config), so a renamed one fails at BIE's preflight.
LEAN_SETTINGS = ('web_search="disabled"', "agents.enabled=false", "skills.max_context_tokens=1")
LEAN_FEATURES_OFF = ("shell_tool", "unified_exec", "code_mode_host", "sleep_tool", "view_image", "browser_use", "computer_use",
                     "apps", "plugins", "image_generation", "hooks", "multi_agent", "goals", "skill_search", "tool_suggest",
                     "workspace_dependencies", "worktrees")
# Images through the plan (Task 046 one-shot, Navin 26 October 2026): Codex's built-in ``image_gen`` tool (the
# ``image_generation`` feature, stable and on in 0.162.1; gpt-image-2 behind it) makes the picture and saves it under
# ``$CODEX_HOME/generated_images/``. No API key: the call is billed to the ChatGPT plan, whose limits it uses several
# times faster than text. Everything else stays off, as in a lean call.
IMAGE_INSTRUCTIONS = ("You are BIE's image maker, run by BIE (Book Intelligence Engine) through Codex with no person "
                      "watching. The message holds one image description written by BIE. Call the built-in image_gen tool "
                      "exactly once with that description, keeping every requirement in it, then reply with the single "
                      "word DONE. Do not run commands, read or write files, browse, ask questions or start other agents.")
# Codex reaches image_gen through its built-in ``imagegen`` skill, called headless as ``codex exec '$imagegen ...'``
# (Codex CLI docs and guides, 2026). The first live run (26 October 2026) kept the lean call's skill settings
# (skills.max_context_tokens=1, skill_search off) and sent no ``$imagegen``: all four runs replied without an image.
# Image calls therefore keep skills on and name the skill; shell, exec, apps, browsing and agents stay off, and no API
# key reaches Codex, so the skill's API-key fallback cannot run.
# The third live run (26 October 2026, job t046-oneshot-images-3) named the cause: "Code Mode is unavailable because
# code-mode host is disabled. Code mode will fail closed; enable `features.code_mode_host`". In Codex 0.162.1 every tool
# call, image_gen included, goes through the code-mode host that ships beside the codex binary, so image calls keep it
# on (it touches the isolation boundary; Navin said yes on 26 October 2026). With shell, exec, apps and plugins off, the
# only tool it can reach is image_gen; the run stays read-only in an empty folder.
IMAGE_SKILL = "$imagegen"
IMAGE_SETTINGS = tuple(s for s in LEAN_SETTINGS if not s.startswith("skills."))
IMAGE_FEATURES_OFF = tuple(f for f in LEAN_FEATURES_OFF if f not in ("image_generation", "skill_search", "code_mode_host"))
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")
IMAGE_MAGIC = {b"\x89PNG": ".png", b"\xff\xd8\xff": ".jpg", b"RIFF": ".webp"}
PLAN_LIMIT_TEXT = re.compile(r"(?i)usage limit|usage_limit|hit your usage|reached your usage|try again at|rate_limit_reached|"
                             r"quota_exceeded|usage_not_included|credits? (are )?depleted|out of credits|credit limit")
AUTH_TEXT = re.compile(r"(?i)\b401\b|unauthori[sz]ed|not logged in|authentication required|missing bearer|"
                       r"refresh token|token (has )?expired|please (log|sign) in|codex login")
NOT_FOUND_TEXT = re.compile(r"(?i)model .{0,40}(not (found|supported|available))|unknown model|\b404\b")
BAD_REQUEST_TEXT = re.compile(r"(?i)\b400\b|invalid_request|invalid schema|invalid_json_schema|output.schema")


def classify(text: str) -> str:
    if PLAN_LIMIT_TEXT.search(text):
        return "plan_limit"
    if AUTH_TEXT.search(text):
        return "auth"
    if NOT_FOUND_TEXT.search(text):
        return "not_found"
    if BAD_REQUEST_TEXT.search(text):
        return "bad_request"
    return "provider_unavailable"


def build_prompt(messages) -> tuple[str, list]:
    """(prompt text, [image parts in order]) for one Codex run; tags keep instructions, task and remakes apart."""
    system, conversation = split_messages(messages, provider="codex")
    blocks, images = [], []
    if system:
        blocks.append("<bie-instructions>\n" + system + "\n</bie-instructions>")
    first = True
    for turn in conversation:
        content = turn["content"]
        if turn["role"] == "user" and not isinstance(content, str):
            images += [p for p in content if p.get("type") == "image"]
        text = text_of(content)
        if turn["role"] == "assistant":
            blocks.append("<your-previous-answer>\n" + text + "\n</your-previous-answer>")
        elif first:
            blocks.append("<bie-task>\n" + text + "\n</bie-task>")
            first = False
        else:
            blocks.append("<bie-findings>\n" + text + "\n</bie-findings>")
    if images:
        blocks.append(f"<bie-images>{len(images)} image(s) are attached in the order the task mentions them.</bie-images>")
    blocks.append(ANSWER_RULES)
    return "\n\n".join(blocks), images


def parse_events(stdout: str) -> dict:
    """The parts of a ``codex exec --json`` stream BIE needs: thread id, usage, final message, errors."""
    out = {"thread_id": None, "usage": {}, "message": None, "errors": [], "failed": None, "completed": False}
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        kind = event.get("type")
        if kind == "thread.started":
            out["thread_id"] = event.get("thread_id")
        elif kind == "turn.completed":
            out["completed"] = True
            out["usage"] = event.get("usage") or {}
        elif kind == "turn.failed":
            out["failed"] = str((event.get("error") or {}).get("message") or "turn failed")
        elif kind == "error":
            out["errors"].append(str(event.get("message") or ""))
        elif kind == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                out["message"] = item["text"]
            elif item.get("type") == "error":
                out["errors"].append(str(item.get("message") or ""))
    return out


def _image_suffix(data: bytes) -> str:
    return next((suffix for magic, suffix in IMAGE_MAGIC.items() if data.startswith(magic)), "")


def image_events(stdout: str) -> dict:
    """What a ``codex exec --json`` stream says about generated images: the event and item types seen, any saved path,
    any base64 result (decoded), the revised prompt. Codex's image items are read by shape, not by one exact name."""
    out = {"types": [], "paths": [], "images": [], "revised_prompt": None}

    def walk(value):
        if isinstance(value, dict):
            kind = value.get("type")
            if isinstance(kind, str) and kind not in out["types"]:
                out["types"].append(kind)
            for key, item in value.items():
                if key in ("path", "saved_path", "file_path", "output_path") and isinstance(item, str) \
                        and item.lower().endswith(IMAGE_SUFFIXES):
                    out["paths"].append(item)
                elif key == "revised_prompt" and isinstance(item, str):
                    out["revised_prompt"] = item
                elif key in ("result", "b64_json", "image_base64") and isinstance(item, str) and len(item) > 200:
                    try:
                        data = base64.b64decode(item, validate=True)
                    except (ValueError, TypeError):
                        data = b""
                    if _image_suffix(data):
                        out["images"].append(data)
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                walk(json.loads(line))
            except ValueError:
                continue
    return out


class CodexExecClient:
    """A client the existing ``GPTAdapter`` can call (``responses_create``), backed by ``codex exec``."""

    provider = "openai"
    via = "codex"
    billing = "subscription"

    def __init__(self, *, executable: str | None = None, timeout: float = DEFAULT_TIMEOUT, codex_home: str | None = None,
                 reasoning_effort: str | None = None, lean: bool | None = None, env=None, run=subprocess.run,
                 clock=time.monotonic):
        self.command = shlex.split(executable or os.environ.get("BIE_CODEX_BIN") or "codex")
        self.timeout = timeout
        self.codex_home = codex_home or os.environ.get("CODEX_HOME")
        self.reasoning_effort = reasoning_effort or os.environ.get("BIE_CODEX_REASONING") or None
        self.lean = lean if lean is not None else os.environ.get("BIE_CODEX_LEAN", "1") != "0"
        self._env, self._run, self._clock = env, run, clock
        self.last_model = None
        self.last_thread = None
        self.last_seconds = None

    def child_env(self):
        """The environment for Codex: no API key (ChatGPT sign-in only) and no other secret (the Gemini key stays
        with BIE's checker; the model never sees it, even through a command it might run)."""
        env = dict(os.environ if self._env is None else self._env)
        for name in list(env):
            if any(word in name.upper() for word in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
                env.pop(name)
        if self.codex_home:
            env["CODEX_HOME"] = self.codex_home
        return env

    def _secrets(self):
        env = self._env if self._env is not None else os.environ
        return [v for k, v in env.items() if v and len(v) >= 12 and ("KEY" in k or "TOKEN" in k)]

    def _fail(self, text: str, *, kind: str | None = None):
        clean = redact(text, self._secrets())
        raise ProviderError(kind or classify(clean), clean[-300:], provider="codex")

    # The adapters' method names.
    def responses_create(self, *, model, messages, response_schema=None):
        return self.chat(model=model, messages=messages, schema=response_schema)

    def messages_create(self, *, model, messages, schema=None):
        return self.chat(model=model, messages=messages, schema=schema)

    def generate(self, *, model, messages, schema=None):
        return self.chat(model=model, messages=messages, schema=schema)

    def chat(self, *, model, messages, schema=None):
        prompt, images = build_prompt(messages)
        with tempfile.TemporaryDirectory(prefix="bie-codex-") as folder:
            folder = Path(folder)
            work = folder / "work"
            work.mkdir()
            last = folder / "last-message.json"
            cmd = self.command + ["exec", "--json", "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only",
                                  "--ignore-rules", "--color", "never", "-C", str(work), "-o", str(last), "-m", model]
            if self.reasoning_effort:
                cmd += ["-c", f'model_reasoning_effort="{self.reasoning_effort}"']
            if self.lean:
                instructions = folder / "instructions.md"
                instructions.write_text(LEAN_INSTRUCTIONS, encoding="utf-8")
                cmd += ["--strict-config", "-c", f"model_instructions_file={json.dumps(str(instructions))}"]
                for setting in LEAN_SETTINGS:
                    cmd += ["-c", setting]
                for feature in LEAN_FEATURES_OFF:
                    cmd += ["--disable", feature]
            if schema is not None:
                schema_path = folder / "schema.json"
                schema_path.write_text(json.dumps(provider_schema(schema, "openai"), ensure_ascii=False), encoding="utf-8")
                cmd += ["--output-schema", str(schema_path)]
            for number, part in enumerate(images, 1):
                path = folder / f"image-{number:02d}{SUFFIX[part['media_type']]}"
                path.write_bytes(base64.b64decode(part["data"]))
                cmd += ["--image", str(path)]
            cmd += ["--", "-"]          # "--": "-" (the prompt on stdin) is not read as one more --image file
            started = self._clock()
            try:
                done = self._run(cmd, input=prompt, capture_output=True, text=True, timeout=self.timeout, env=self.child_env())
            except FileNotFoundError:
                raise ProviderError("config", "the codex CLI is not installed here (set BIE_CODEX_BIN)", provider="codex") from None
            except subprocess.TimeoutExpired:
                raise ProviderError("timeout", f"codex exec did not finish within {self.timeout:.0f} s", provider="codex") from None
            self.last_seconds = round(self._clock() - started, 3)
            events = parse_events(done.stdout or "")
            self.last_thread = events["thread_id"]
            answer = last.read_text(encoding="utf-8").strip() if last.exists() else ""
        if done.returncode != 0 or events["failed"] or not events["completed"]:
            detail = events["failed"] or (events["errors"][-1] if events["errors"] else "") or (done.stderr or "")[-600:]
            self._fail(detail or f"codex exec exited with {done.returncode}")
        answer = answer or (events["message"] or "").strip()
        if not answer:
            raise ProviderError("malformed", "codex exec returned no final message", provider="codex")
        self.last_model = model
        usage = events["usage"]
        return {"content": answer, "finish_reason": "stop", "model": model,
                "usage": {"input_tokens": int(usage.get("input_tokens") or 0),
                          "output_tokens": int(usage.get("output_tokens") or 0),
                          "cached_input_tokens": int(usage.get("cached_input_tokens") or 0),
                          "reasoning_tokens": int(usage.get("reasoning_output_tokens") or 0)}}

    def home(self) -> Path:
        return Path(self.codex_home or os.environ.get("CODEX_HOME") or Path.home() / ".codex")

    def generate_image(self, prompt: str, out: Path, *, model: str | None = None) -> dict:
        """One picture from Codex's built-in ``image_gen`` tool through the ChatGPT plan, saved to ``out`` (its suffix
        follows the image's format). Returns where Codex put it, the seconds, the usage and the event types seen. The run
        is read-only and starts in an empty folder; only the image tool is on."""
        images_dir = self.home() / "generated_images"
        before = {p: p.stat().st_mtime for p in images_dir.rglob("*") if p.is_file()} if images_dir.exists() else {}
        with tempfile.TemporaryDirectory(prefix="bie-codex-image-") as folder:
            folder = Path(folder)
            work = folder / "work"
            work.mkdir()
            last = folder / "last-message.txt"
            instructions = folder / "instructions.md"
            instructions.write_text(IMAGE_INSTRUCTIONS, encoding="utf-8")
            cmd = self.command + ["exec", "--json", "--skip-git-repo-check", "--sandbox", "read-only", "--ignore-rules",
                                  "--color", "never", "-C", str(work), "-o", str(last), "-m", model or DEFAULT_MODEL,
                                  "--strict-config", "-c", f"model_instructions_file={json.dumps(str(instructions))}"]
            for setting in IMAGE_SETTINGS:
                cmd += ["-c", setting]
            for feature in IMAGE_FEATURES_OFF:
                cmd += ["--disable", feature]
            cmd += ["--", "-"]
            started = self._clock()
            try:
                message = f"{IMAGE_SKILL} <bie-image-prompt>\n{prompt}\n</bie-image-prompt>"
                done = self._run(cmd, input=message, capture_output=True,
                                 text=True, timeout=self.timeout, env=self.child_env())
            except FileNotFoundError:
                raise ProviderError("config", "the codex CLI is not installed here (set BIE_CODEX_BIN)", provider="codex") from None
            except subprocess.TimeoutExpired:
                raise ProviderError("timeout", f"codex exec did not finish within {self.timeout:.0f} s", provider="codex") from None
            seconds = round(self._clock() - started, 3)
            events = parse_events(done.stdout or "")
            found = image_events(done.stdout or "")
            in_work = sorted(p for p in work.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES)
            work_bytes = in_work[-1].read_bytes() if in_work else b""
        if done.returncode != 0 or events["failed"] or not events["completed"]:
            detail = events["failed"] or (events["errors"][-1] if events["errors"] else "") or (done.stderr or "")[-600:]
            self._fail(detail or f"codex exec exited with {done.returncode}")
        fresh = sorted((p for p in images_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
                        and before.get(p) != p.stat().st_mtime), key=lambda p: p.stat().st_mtime) if images_dir.exists() else []
        data, found_by, source = b"", "", ""
        if fresh:
            data, found_by, source = fresh[-1].read_bytes(), "codex_home", fresh[-1].name
        elif any(Path(p).is_file() for p in found["paths"]):
            path = Path(next(p for p in reversed(found["paths"]) if Path(p).is_file()))
            data, found_by, source = path.read_bytes(), "event_path", path.name
        elif found["images"]:
            data, found_by = found["images"][-1], "event_base64"
        elif work_bytes:
            data, found_by = work_bytes, "work_folder"
        suffix = _image_suffix(data)
        if not suffix:
            # what Codex said, so a failed run names its cause (26 October 2026: the first live run left an error item
            # and a reply that BIE did not keep); redacted like every other Codex failure text
            said = redact("; ".join(e for e in events["errors"][-2:] if e)[-400:], self._secrets())
            reply = redact((events["message"] or "")[:300], self._secrets())
            raise ProviderError("malformed", "codex exec finished but no generated image was found (event types: "
                                + ", ".join(found["types"][:12]) + ")" + (f"; codex error: {said}" if said else "")
                                + (f"; reply: {reply}" if reply else ""), provider="codex")
        out = Path(out).with_suffix(suffix)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        usage = events["usage"]
        self.last_thread, self.last_seconds, self.last_model = events["thread_id"], seconds, model or DEFAULT_MODEL
        return {"file": out.name, "bytes": len(data), "seconds": seconds, "found_by": found_by, "codex_file": source,
                "thread": events["thread_id"], "revised_prompt": found["revised_prompt"], "event_types": found["types"],
                "final_message": (events["message"] or "")[:200],
                "usage": {"input_tokens": int(usage.get("input_tokens") or 0), "output_tokens": int(usage.get("output_tokens") or 0),
                          "reasoning_tokens": int(usage.get("reasoning_output_tokens") or 0)}}

    def login_status(self) -> dict:
        """``codex login status`` without reading the auth file: {"logged_in": bool, "mode": first line}."""
        try:
            done = self._run(self.command + ["login", "status"], capture_output=True, text=True, timeout=60, env=self.child_env())
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            return {"logged_in": False, "mode": f"codex not runnable: {type(exc).__name__}"}
        lines = [line.strip() for line in (done.stdout or "").splitlines() + (done.stderr or "").splitlines()]
        lines = [line for line in lines if line and not line.startswith("WARNING")]
        first = redact(lines[0] if lines else "", self._secrets())[:120]
        return {"logged_in": done.returncode == 0, "mode": first}

    def plan_usage(self, timeout: float = 30.0) -> dict:
        """The plan's usage windows from the Codex app server (``account/rateLimits/read``), numbers only.

        Experimental in Codex; any problem returns {"unavailable": reason} instead of failing the run."""
        try:
            proc = subprocess.Popen(self.command + ["app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, text=True, env=self.child_env())
        except OSError as exc:
            return {"unavailable": type(exc).__name__}
        lines = queue.Queue()
        reader = threading.Thread(target=lambda: [lines.put(line) for line in proc.stdout], daemon=True)
        reader.start()
        try:
            def send(message):
                proc.stdin.write(json.dumps(message) + "\n")
                proc.stdin.flush()

            def answer(request_id):
                end = time.monotonic() + timeout
                while time.monotonic() < end:
                    try:
                        line = lines.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    try:
                        message = json.loads(line)
                    except ValueError:
                        continue
                    if message.get("id") == request_id:
                        return message
                return None

            send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "bie", "title": "BIE", "version": "1"}}})
            if answer(1) is None:
                return {"unavailable": "no answer from codex app-server"}
            send({"method": "initialized"})
            send({"id": 2, "method": "account/rateLimits/read"})
            reply = answer(2)
            if reply is None:
                return {"unavailable": "no answer to account/rateLimits/read"}
            if "error" in reply:
                return {"unavailable": str((reply.get("error") or {}).get("message") or "error")[:160]}
            return _usage_numbers(reply.get("result") or {})
        except (OSError, ValueError) as exc:
            return {"unavailable": type(exc).__name__}
        finally:
            proc.kill()
            proc.wait(timeout=10)
            reader.join(timeout=5)
            for stream in (proc.stdin, proc.stdout):
                stream.close()


def _usage_numbers(value, prefix=""):
    """Numeric fields and plan names only (no account ids, e-mail or tokens)."""
    out = {}
    for key, item in (value.items() if isinstance(value, dict) else ()):
        path = prefix + str(key)
        if isinstance(item, dict):
            out.update(_usage_numbers(item, path + "."))
        elif isinstance(item, (int, float)) and not isinstance(item, bool):
            out[path] = item
        elif isinstance(item, str) and "plan" in key.lower() and len(item) < 40:
            out[path] = item
    return out
