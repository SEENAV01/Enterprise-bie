"""A deterministic stand-in for the ``codex`` CLI, for offline tests of the Codex maker route.

Run as ``python -m bie.brain.fake_codex <codex arguments>`` (set ``BIE_CODEX_BIN`` to that command). It
answers ``codex exec`` like the real CLI does (JSONL events on stdout, the final message in the
``--output-last-message`` file) with the brain fake's answers, plus ``login status`` and the two
``app-server`` calls BIE uses. It proves BIE's plumbing (prompt, schema, images, usage, errors), never
quality. ``BIE_FAKE_CODEX_MODE``:

  ok (default)      every call succeeds
  schema_error      ``exec`` answers ``{}`` (does not match the schema)
  schema_error_after=N  the first N ``exec`` calls answer properly, later ones answer ``{}``
  plan_limit_after=N  the first N ``exec`` calls succeed, then the plan window is used up
  auth_missing      not signed in: ``login status`` exits 1 and ``exec`` fails with 401

``BIE_FAKE_CODEX_STATE`` (a folder) keeps the call counter and a JSONL log of every call (arguments, image
count, whether an API key was visible).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PLAN_LIMIT = "You've hit your usage limit. Upgrade to Pro or try again at 3:05 PM."
UNAUTHORIZED = "unexpected status 401 Unauthorized: Missing bearer or basic authentication in header"


def _state():
    folder = Path(os.environ.get("BIE_FAKE_CODEX_STATE") or ".fake-codex")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _log(entry):
    with (_state() / "calls.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def _count():
    path = _state() / "exec-count"
    number = int(path.read_text()) + 1 if path.exists() else 1
    path.write_text(str(number))
    return number


def _mode():
    return os.environ.get("BIE_FAKE_CODEX_MODE", "ok")


def _section(prompt, tag):
    match = re.search(rf"<{tag}>\n(.*?)\n</{tag}>", prompt, re.S)
    return match.group(1) if match else ""


def _answer(prompt, schema, images):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from bie.brain.fake import BrainFakeClient

    props = (schema or {}).get("properties", {})
    if list(props) == ["number"]:                       # the vision check: the fake "reads" only if an image came
        return {"number": "47" if images else "none"}
    system = _section(prompt, "bie-instructions") or "fake"
    task = _section(prompt, "bie-task") or prompt
    client = BrainFakeClient("openai")
    raw = client._respond("fake-codex", [{"role": "system", "content": system}, {"role": "user", "content": task}], schema)
    return json.loads(raw["content"])


# A 1x1 PNG; the fake writes it where Codex 0.162.1 keeps generated images. BIE_FAKE_CODEX_IMAGE: home (default, a file
# under $CODEX_HOME/generated_images), base64 (only in the event stream), none (no image at all).
PIXEL = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                      "1f15c4890000000d49444154789c6360f8cf00000301010018dd8db00000000049454e44ae426082")


def _image(prompt, number, options, disabled):
    import base64
    where = os.environ.get("BIE_FAKE_CODEX_IMAGE", "home")
    if "image_generation" in disabled:
        where = "none"
    item = {"id": "item_img", "type": "image_generation", "revised_prompt": prompt[19:80]}
    if where == "home":
        folder = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "generated_images" / f"fake-thread-{number}"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"ig_{number:03d}.png").write_bytes(PIXEL)
    elif where == "base64":
        item["result"] = base64.b64encode(PIXEL * 8).decode()
    if where != "none":
        print(json.dumps({"type": "item.completed", "item": item}))
    if "-o" in options:
        Path(options["-o"]).write_text("DONE", encoding="utf-8")
    print(json.dumps({"type": "item.completed", "item": {"id": "item_1", "type": "agent_message", "text": "DONE"}}))
    print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": len(prompt) // 4, "cached_input_tokens": 0,
                                                           "output_tokens": 4, "reasoning_output_tokens": 0}}))
    return 0


def _exec(args):
    options, images, settings, disabled, i = {}, [], [], [], 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            break
        if arg in ("-o", "--output-last-message", "--output-schema", "-m", "--model", "-C", "--cd", "-s", "--sandbox",
                   "--color"):
            options[arg] = args[i + 1]
            i += 2
        elif arg in ("-c", "--config"):
            settings.append(args[i + 1])
            i += 2
        elif arg == "--disable":
            disabled.append(args[i + 1])
            i += 2
        elif arg in ("-i", "--image"):
            images.append(args[i + 1])
            i += 2
        else:
            i += 1
    instructions = next((json.loads(s.split("=", 1)[1]) for s in settings if s.startswith("model_instructions_file=")), None)
    prompt = sys.stdin.read() if args and args[-1] == "-" else ""
    number = _count()
    mode = _mode()
    _log({"call": number, "args": args, "images": [Path(p).suffix for p in images],
          "images_exist": all(Path(p).exists() for p in images), "settings": settings, "disabled": disabled,
          "instructions": Path(instructions).read_text(encoding="utf-8") if instructions else None,
          "api_key_visible": any(any(w in k for w in ("KEY", "TOKEN", "SECRET")) for k in os.environ),
          "codex_home": os.environ.get("CODEX_HOME"), "model": options.get("-m"), "prompt_chars": len(prompt)})
    print(json.dumps({"type": "thread.started", "thread_id": f"fake-thread-{number}"}))
    print(json.dumps({"type": "turn.started"}))
    failure = None
    if mode == "auth_missing":
        failure = UNAUTHORIZED
    elif mode.startswith("plan_limit_after=") and number > int(mode.split("=", 1)[1]):
        failure = PLAN_LIMIT
    if failure:
        print(json.dumps({"type": "error", "message": failure}))
        print(json.dumps({"type": "turn.failed", "error": {"message": failure}}))
        return 1
    if "<bie-image-prompt>" in prompt:                  # Codex's built-in image_gen tool: the picture lands in CODEX_HOME
        return _image(prompt, number, options, disabled)
    schema = json.loads(Path(options["--output-schema"]).read_text(encoding="utf-8")) if "--output-schema" in options else None
    broken = mode == "schema_error" or (mode.startswith("schema_error_after=") and number > int(mode.split("=", 1)[1]))
    value = {} if broken else _answer(prompt, schema, images)
    text = json.dumps(value, ensure_ascii=False)
    if "-o" in options:
        Path(options["-o"]).write_text(text, encoding="utf-8")
    print(json.dumps({"type": "item.completed", "item": {"id": "item_0", "type": "agent_message", "text": text}}))
    print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": len(prompt) // 4, "cached_input_tokens": 0,
                                                           "output_tokens": len(text) // 4, "reasoning_output_tokens": 0}}))
    return 0


def _app_server():
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except ValueError:
            continue
        method, ident = message.get("method"), message.get("id")
        if ident is None:
            continue
        if method == "initialize":
            reply = {"id": ident, "result": {"userAgent": "fake-codex"}}
        elif method == "account/rateLimits/read" and _mode() == "auth_missing":
            reply = {"id": ident, "error": {"code": -32600, "message": "codex account authentication required to read rate limits"}}
        elif method == "account/rateLimits/read":
            used = min(100, 10 + 5 * len((_state() / "calls.jsonl").read_text().splitlines())) \
                if (_state() / "calls.jsonl").exists() else 10
            reply = {"id": ident, "result": {"rateLimits": {"planType": "pro", "primary": {"usedPercent": used, "windowDurationMins": 300},
                                                            "secondary": {"usedPercent": used // 4, "windowDurationMins": 10080}},
                                             "email": "never-recorded@example.com"}}
        else:
            reply = {"id": ident, "error": {"code": -32601, "message": "not supported by the fake"}}
        print(json.dumps(reply), flush=True)
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:2] == ["login", "status"]:
        if _mode() == "auth_missing":
            print("Not logged in")
            return 1
        print("Logged in using ChatGPT")
        return 0
    if args[:1] == ["exec"]:
        return _exec(args[1:])
    if args[:1] == ["app-server"]:
        return _app_server()
    print("fake codex: unsupported command " + " ".join(args[:2]), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
