"""BIE's script stage with Claude as the writer (Navin, 26 November 2026: "tumhe hi script writing ke kaam mein baitha
deta hun vm ke raaste se"; "mujhe hubahu tumhare jaisi script chahiye"). Everything before and after stays BIE's: the
chapter map and plan come from earlier runs, the script goes in BIE's format into ``script.json``, BIE's own checks
(`studio_script.problems`) decide the status, and the films stage reads the run folder as it reads a Codex script run.

The writer is Claude Code on this machine, signed in with Navin's Claude plan (``sudo bie-claude-setup``; never an
Anthropic API key: any ``ANTHROPIC_API_KEY`` is removed from its environment). It runs in the repository checkout, so
``CLAUDE.md`` and the ``bie-script-writer`` skill load, and it works like the Claude Navin passed: it writes each heading
as a teacher speaks it, runs ``tools/script_writer_check.py`` itself and weighs the findings. It may write only inside
the run's work folder. When ``$BIE_HOME/claude/BASE_SESSION`` holds a session id (the chat Navin taught, brought to this
machine), each job forks that session (``--resume <id> --fork-session``), so the writer starts with that chat's memory.
Without it a job stops (Navin, 26 November 2026: "tumhe yaani isi chat session ke llm ai ko baithane ki baat huyi thi vm
par ... to vm par dusra naya session kaise ho gaya"); only a job that says ``"fresh": true`` (a test of the skill alone)
starts a new session. The taught chat's task opens by saying its own memory of Navin's words comes first and the skill
is only a reminder (Navin, 26 November 2026, "haan likh do").

The taught chat reaches this machine as a locked copy of its own file (Navin, 27 November 2026, "Raasta 1": teleport
cannot bring a chat started in the Claude app; "Couldn't load the history of cloud session", the server answering "not
found"). Stage ``copy`` installs a newer copy: it downloads the locked file from this repository, checks its sha256,
unlocks it with the key kept only here (``$BIE_HOME/claude/chat.key``), keeps the copy in use in
``$BIE_HOME/claude/archive/`` (never deleted: "purani copy mitayenge nahi"), installs the new one as ``BASE_SESSION``
and asks it three questions. Only a copy that answers from the chat's memory, with that memory whole (its tokens near
the size the job states), stays in use; otherwise the copy in use before comes back. The answers stay on this machine
(``copy-test.txt``); the run folder holds only the checks and numbers, never the chat's words.

What the writer may read (Navin, 27 November 2026, plan point 5): the repository and its work folder only; this
machine's Claude and Codex sign-ins, the copy and its key, the deploy key and ``/etc`` are refused, so no text in a book
can make it copy a secret into a script that is published. Each job's own copy of the chat is deleted after the job
except the last five (plan point 4); the copies in use and kept are never deleted.

    python tools/vm_claude.py script --from-run <script run> --chapter-map <naksha run> --videos h11-6-3 --out <folder>
    python tools/vm_claude.py copy --url <locked copy> --sha256 <hex> --tokens <its size> --out <folder>
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

CLAUDE_VERSION = "2.1.331"         # pinned in deployment/codex-vm/bie-claude-setup; Anthropic's Claude Code, run unmodified
MODEL = "opus"                      # Navin, 26 November 2026: "yhi same model opus ... extra effort ke sath"
EFFORT = "xhigh"
MODELS = ("opus", "opus[1m]")        # the copy's test tries these in order; the first that holds the whole memory stays
TIMEOUT = 6 * 3600
KEEP_FORKS = 5                      # job copies of the chat kept for a look at how a script was thought (plan point 4)
COPY_SOURCE = "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/"
COPY_QUESTION = ("Teen chhote jawab do: (1) gold script kis heading ki hai aur Navin ne use pass karte waqt kya kaha? "
                 "(2) niyam B8 kya kehta hai? (3) script likhte waqt sabse pehle kiski baat maanoge?")
COPY_WARN_TOKENS = 750_000          # beyond this a job's reading and writing may not fit beside the memory (plan point 3)
MAKER = "claude (Claude Code on Navin's Claude plan, the bie-script-writer skill)"
# The first words a job gives the taught chat (Navin, 26 November 2026, "haan likh do"): that chat already knows his
# words and how the gold standard was made, so the skill must not pull it away from what he told it.
TAUGHT = """You are the chat Navin taught: you wrote the gold standard with him and you remember his words and verdicts.
Your own memory of what he told you comes first; the skill is only a reminder of it. Where the skill and what he told
you differ, follow his latest word, and write in YAADEIN_NEW.md where they differed. What you write here is published:
put nothing of the chat itself into the work files beyond what the script needs (no private messages, keys or paths).

"""

TASK = """Use the bie-script-writer skill: read .claude/skills/bie-script-writer/SKILL.md and the files it names before you
write. Course: {course}. Language: {language}.

Write the script of heading(s) {headings} of the chapter in {work}/chapter_map.json, in BIE's script format (the same
JSON as the other headings of {work}/script.json), and put each one into {work}/script.json in place of the heading with
that number, keeping every other heading exactly as it is. The script so far is in {work}/script.json; the teaching
plan's ideas are in {work}/naksha.json when that file exists.

BIE's packet for each heading is {work}/packet-<number>.md: the heading's part of the chapter file, its items with what
each needs first and what a figure shows by name, what BIE's checks will ask, the plan's ideas, the heading just before
it and the terms already opened. Read it first. The whole chapter file ({work}/chapter.md) and the script so far
({work}/script-so-far.md) are beside it, one item or point per line: search them for anything more you need.
chapter_map.json and script.json stay as they are.

For each heading, before you hand it over, run:
{python} tools/script_writer_check.py --script {work}/script.json --chapter {work}/chapter_map.json --heading <number>
and weigh its findings as the skill says. Then add a few lines to {work}/YAADEIN_NEW.md: the heading and what you
learned.

Write only inside {work}. When you are done, reply with one line per heading: its number, its sentences and the
problems left."""


def headings_of(videos: str, chapter: dict) -> list:
    """Film ids or heading numbers ("h11-6-3", "11.6.3") as the chapter's heading numbers, in the chapter's order."""
    from bie.brain import studio_script
    wanted = {v.strip() for v in (videos or "").split(",") if v.strip()}
    out = []
    for h in studio_script.headings(chapter):
        if not wanted or h["number"] in wanted or studio_script.film_id(h["number"]) in wanted:
            out.append(h["number"])
    return out


def write_packets(work: Path, chapter: dict, so_far: dict, wanted: list, naksha: dict | None) -> list:
    """BIE's packet for each heading the writer writes, and the whole chapter file and the script so far to search (Navin,
    27 November 2026: "bs dhundhna kam kar rahe hai"; job c3 searched the one-line chapter map turn by turn). The raw
    chapter_map.json and script.json are left as they are. Returns the packet files."""
    from bie.brain import chapter_file, studio_script
    (work / "chapter.md").write_text(chapter_file.markdown(chapter), encoding="utf-8")
    parts = so_far.get("parts") or []
    (work / "script-so-far.md").write_text(
        "The script as it stood when this job began (the headings you write in this job are in script.json).\n\n"
        + studio_script.script_so_far(parts, chapter) + "\n", encoding="utf-8")
    heads = studio_script.headings(chapter)
    order = [h["number"] for h in heads]
    out = []
    for number in wanted:
        n = order.index(number)
        nxt = heads[n + 1] if n + 1 < len(heads) else None
        later = [t for h in heads[n + 1:] for t, _ in studio_script.first_terms(h) if studio_script._technical(t)]
        earlier = [p for p in parts if p.get("section") in order[:n]]
        path = work / f"packet-{number or 'opening'}.md"
        path.write_text(studio_script.packet(chapter, heads[n], earlier, naksha=naksha, later_terms=later,
                                             next_title=f"{nxt['number']} {nxt['title']}" if nxt else ""),
                        encoding="utf-8")
        out.append(path)
    return out


def refused(env: dict) -> list:
    """Folders the writer may never read (plan point 5): this machine's sign-ins, the chat's copy and key, the deploy
    key and /etc. A permission rule's "//" is the filesystem root."""
    home = Path(env.get("BIE_HOME") or "/var/lib/bie")
    places = [Path(env["CLAUDE_CONFIG_DIR"]), home / "codex", home / "claude", home / "deploy_key", Path("/etc"),
              Path("/root")]
    out = []
    for place in dict.fromkeys(str(p) for p in places):
        out += [f"Read(/{place}/**)", f"Read(/{place})"]
    return out


def command(task: str, work: Path, *, binary: str, base: str = "", python: str = sys.executable, model: str = MODEL,
            env: dict | None = None) -> list:
    """The Claude Code call: print mode, JSON result, the model and effort Navin chose, and only the tools the writer
    needs: read the repository and the work folder, write and edit only in the work folder, run the self-check; the
    sign-ins, keys and the chat's copy are refused."""
    env = env if env is not None else environment()
    cmd = [binary, "-p", task, "--model", model, "--effort", EFFORT, "--output-format", "json",
           "--permission-mode", "dontAsk", "--add-dir", str(work),
           "--allowedTools", f"Read(/{ROOT}/**)", f"Read(/{work}/**)", "Glob", "Grep", f"Write(/{work}/**)",
           f"Edit(/{work}/**)", f"Bash({python} tools/script_writer_check.py *)",
           "--disallowedTools", *refused(env)]
    if base:
        cmd += ["--resume", base, "--fork-session"]
    return cmd


def conf_dir(env: dict) -> Path:
    return Path(env["CLAUDE_CONFIG_DIR"])


def project_dir(env: dict) -> Path:
    """Where Claude Code keeps the chats of jobs run in the repository (its folder name: the path, "-" for the rest)."""
    return conf_dir(env) / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(ROOT))


def model_of(env: dict) -> str:
    """The model setting the copy's test found to hold the whole memory (``MODEL`` until a copy has been tested)."""
    path = conf_dir(env) / "MODEL"
    value = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    return value if value in MODELS else MODEL


def prune_forks(env: dict, keep: int = KEEP_FORKS) -> list:
    """Delete the job copies of the chat beyond the newest ``keep`` (plan point 4); the copy in use is never touched."""
    folder = project_dir(env)
    if not folder.is_dir():
        return []
    base = base_session(env)
    forks = sorted((p for p in folder.glob("*.jsonl") if p.stem != base), key=lambda p: p.stat().st_mtime, reverse=True)
    gone = []
    for path in forks[keep:]:
        path.unlink(missing_ok=True)
        shutil.rmtree(folder / path.stem, ignore_errors=True)                 # a job's own helpers, when it had any
        gone.append(path.stem)
    return gone


def environment() -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    env.setdefault("CLAUDE_CONFIG_DIR", str(Path(os.environ.get("BIE_HOME") or "/var/lib/bie") / "claude"))
    return env


def login_status(*, run=subprocess.run, binary: str = "") -> dict:
    """Whether Claude Code is installed and signed in here, and how (``claude auth status``); never an account detail."""
    env = environment()
    binary = binary or shutil.which("claude") or ""
    if not binary:
        return {"installed": False, "logged_in": False, "fix": "sudo bie-claude-setup"}
    try:
        done = run([binary, "auth", "status"], env=env, capture_output=True, text=True, timeout=60)
        info = json.loads(done.stdout or "{}")
    except Exception:                                      # an old binary or a broken config: say so, nothing more
        return {"installed": True, "logged_in": False, "fix": "sudo bie-claude-setup"}
    method = str(info.get("authMethod") or "none")
    return {"installed": True, "logged_in": done.returncode == 0 and method not in ("none", "api_key"),
            "method": method, "base_session": bool(base_session(env))}


def base_session(env: dict) -> str:
    path = Path(env["CLAUDE_CONFIG_DIR"]) / "BASE_SESSION"
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def script(args, *, run=subprocess.run, binary: str = "") -> dict:
    import vm_studio
    from bie.brain import studio_script
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    summary = {"schema": "bie.studio-run/1", "section": "studio", "stage": "script", "status": "failed", "maker": MAKER,
               "model": f"{MODEL}, effort {EFFORT}", "cost": {"total_inr": 0.0}, "error": None}
    try:
        base = args.chapter_map or args.from_run
        chapter = vm_studio.read_json(base, "chapter_map.json")
        plans = vm_studio.maybe_json(base, "naksha.json")
        old = vm_studio.maybe_json(args.from_run, "script.json") if args.from_run else None
        wanted = headings_of(args.videos, chapter)
        if not wanted:
            raise SystemExit(f"videos: no heading of the chapter matches {args.videos!r}")
        work = out / "work"
        work.mkdir(exist_ok=True)
        (work / "chapter_map.json").write_text(json.dumps(chapter, ensure_ascii=False), encoding="utf-8")
        if isinstance(plans, dict):
            (work / "naksha.json").write_text(json.dumps(plans, ensure_ascii=False), encoding="utf-8")
        title = (chapter.get("map") or {}).get("chapter_title", "")
        so_far = old if isinstance(old, dict) and old.get("parts") else {"chapter_title": title, "parts": []}
        (work / "script.json").write_text(studio_script.dump(so_far), encoding="utf-8")
        write_packets(work, chapter, so_far, wanted, plans if isinstance(plans, dict) else None)
        env = environment()
        binary = binary or shutil.which("claude") or "claude"
        base = base_session(env)
        if not base and not getattr(args, "fresh", False):
            raise SystemExit("the chat Navin taught is not on this machine yet (sudo bie-claude-setup, step 3); "
                             "a job without it needs \"fresh\": true")
        task = (TAUGHT if base else "") + TASK.format(course=args.course or "", language=args.language or "Hinglish",
                                                      headings=", ".join(wanted), work=work, python=sys.executable)
        model = model_of(env)
        cmd = command(task, work, binary=binary, base=base, model=model, env=env)
        summary["base_session"] = bool(cmd.count("--fork-session"))
        summary["model"] = f"{model}, effort {EFFORT}"
        try:
            done = run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=TIMEOUT)
        except FileNotFoundError:
            raise SystemExit("Claude Code is not installed on this machine: sudo bie-claude-setup") from None
        except subprocess.TimeoutExpired:
            raise SystemExit(f"the writer did not finish within {TIMEOUT // 3600} hours") from None
        result = {}
        try:
            result = json.loads(done.stdout or "{}")
        except json.JSONDecodeError:
            result = {"result": (done.stdout or "")[-2000:]}
        if done.returncode != 0 or result.get("is_error"):
            text = str(result.get("result") or done.stderr or done.stdout)[-400:]
            raise SystemExit("the writer stopped: " + text + ("" if "login" not in text.lower() else
                                                             " (sign in once: sudo bie-claude-setup)"))
        usage = result.get("usage") or {}
        summary.update(usage={"input_tokens": int(usage.get("input_tokens") or 0)
                              + int(usage.get("cache_read_input_tokens") or 0)
                              + int(usage.get("cache_creation_input_tokens") or 0),
                              "output_tokens": int(usage.get("output_tokens") or 0)},
                       turns=result.get("num_turns"), writer_reply=str(result.get("result") or "")[-1500:],
                       notional_usd=result.get("total_cost_usd"))
        written = json.loads((work / "script.json").read_text(encoding="utf-8"))
        heads = {h["number"]: h for h in studio_script.headings(chapter)}
        order = list(heads)
        problems, rounds = {}, []
        for number in wanted:
            part = next((p for p in written.get("parts") or [] if p.get("section") == number), None)
            if part is None:
                problems[number] = ["the writer did not write this heading"]
                continue
            n = order.index(number)
            earlier = [p for p in written["parts"] if p.get("section") in order[:n]]
            later = [t for h in list(heads.values())[n + 1:] for t, _ in studio_script.first_terms(h)
                     if studio_script._technical(t)]
            found = studio_script.problems(part, heads[number], chapter, earlier, later)
            rounds.append({"section": number, "rounds": [{"round": 1, "problems": found, "writer": "claude"}]})
            if found:
                problems[number] = found
        record = {"parts": written.get("parts") or [], "rounds": rounds, "problems": problems,
                  "usage": summary["usage"]}
        (out / "script.json").write_text(studio_script.dump({"chapter_title": written.get("chapter_title") or title,
                                                             "parts": record["parts"]}), encoding="utf-8")
        (out / "record.json").write_text(studio_script.dump({"rounds": rounds, "problems": problems,
                                                             "usage": summary["usage"]}), encoding="utf-8")
        (out / "SCRIPT.md").write_text(studio_script.markdown(chapter, record), encoding="utf-8")
        (out / "SCRIPT.html").write_text(studio_script.html(chapter, record), encoding="utf-8")
        shutil.copy(work / "chapter_map.json", out / "chapter_map.json")          # for the films stage
        if (work / "naksha.json").exists():
            shutil.copy(work / "naksha.json", out / "naksha.json")
        if (work / "YAADEIN_NEW.md").exists():                                    # folded into the skill by a reviewed PR
            shutil.copy(work / "YAADEIN_NEW.md", out / "YAADEIN_NEW.md")
        summary.update(status="ok" if not problems else "needs_fix", rewritten=wanted, problems=problems,
                       script=studio_script.counts(chapter, record["parts"]))
    except SystemExit as exc:
        summary["error"] = str(exc)
    except Exception as exc:                        # the runner publishes the folder either way; the error says why
        summary["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    shutil.rmtree(out / "work", ignore_errors=True)
    try:
        summary["forks_deleted"] = len(prune_forks(environment()))
    except Exception:                                   # tidying never decides a job
        pass
    summary["minutes"] = round((time.time() - started) / 60, 1)
    (out / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return summary


def unlock(data: bytes, key: Path) -> bytes:
    """The copy as Claude Code wrote it: AES-256-CBC with PBKDF2 (openssl enc), then gzip."""
    done = subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-pass",
                           f"file:{key}"], input=data, capture_output=True, timeout=300)
    if done.returncode != 0:
        raise SystemExit("the copy did not unlock with this machine's key (chat.key)")
    return gzip.decompress(done.stdout)


def fetch(url: str) -> bytes:
    if not url.startswith(("https://", "http://")):                         # a file on this machine (tests)
        return Path(url).read_bytes()
    import urllib.request
    with urllib.request.urlopen(url, timeout=300) as answer:
        return answer.read()


def session_of(text: str) -> str:
    """The chat's session id, as its own lines name it."""
    for line in text.splitlines()[:200]:
        try:
            sid = json.loads(line).get("sessionId")
        except (json.JSONDecodeError, AttributeError):
            continue
        if sid and re.fullmatch(r"[0-9a-f-]{36}", str(sid)):
            return str(sid)
    raise SystemExit("the copy names no session id")


def ask(binary: str, sid: str, model: str, env: dict, run) -> dict:
    """One question to the copy, on a copy of it (``--fork-session``), with no tools."""
    cmd = [binary, "-p", COPY_QUESTION, "--resume", sid, "--fork-session", "--model", model, "--effort", "low",
           "--output-format", "json", "--permission-mode", "dontAsk"]
    done = run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=1800)
    try:
        result = json.loads(done.stdout or "{}")
    except json.JSONDecodeError:
        result = {"is_error": True, "result": (done.stdout or done.stderr or "")[-400:]}
    if done.returncode != 0 and not result.get("is_error"):
        result = dict(result, is_error=True, result=str(result.get("result") or done.stderr or "")[-400:])
    usage = result.get("usage") or {}
    result["tokens"] = sum(int(usage.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens",
                                                             "cache_creation_input_tokens"))
    return result


def install_copy(args, *, run=subprocess.run, binary: str = "") -> dict:
    """Stage ``copy``: put a newer copy of the taught chat in use, only if it passes its test (see the module text)."""
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    summary = {"schema": "bie.studio-run/1", "section": "studio", "stage": "copy", "status": "failed", "maker": MAKER,
               "cost": {"total_inr": 0.0}, "error": None, "sha256": args.sha256}
    env = environment()
    conf, folder = conf_dir(env), project_dir(env)
    binary = binary or shutil.which("claude") or "claude"
    old_sid = base_session(env)
    kept = None
    try:
        key = conf / "chat.key"
        if not key.exists():
            raise SystemExit("this machine has no key for the copy yet (sudo bie-claude-setup, step 3)")
        data = fetch(args.url)
        if hashlib.sha256(data).hexdigest() != args.sha256:
            raise SystemExit("the downloaded copy is not the one the job names (sha256 differs)")
        text = unlock(data, key).decode("utf-8")
        sid = session_of(text)
        summary.update(session=sid, lines=text.count("\n"))
        folder.mkdir(parents=True, exist_ok=True)
        if old_sid and (folder / f"{old_sid}.jsonl").exists():                # kept, never deleted
            (conf / "archive").mkdir(exist_ok=True)
            stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
            kept = conf / "archive" / f"{stamp}-{old_sid[:8]}.jsonl"
            shutil.move(str(folder / f"{old_sid}.jsonl"), kept)
            summary["archived"] = kept.name
        (folder / f"{sid}.jsonl").write_text(text, encoding="utf-8")
        (conf / "BASE_SESSION").write_text(sid + "\n", encoding="utf-8")
        tries = []
        for model in MODELS:
            answer = ask(binary, sid, model, env, run)
            if answer.get("session_id"):                                      # the test's own copy goes at once
                (folder / f"{answer['session_id']}.jsonl").unlink(missing_ok=True)
            reply = str(answer.get("result") or "")
            tries.append({"model": model, "tokens": answer["tokens"], "error": bool(answer.get("is_error"))})
            if not answer.get("is_error"):
                break
            if not re.search(r"too long|context|too many tokens", reply, re.I):
                break                                                         # not a size problem: no other model helps
        summary["tries"] = tries
        expected = int(getattr(args, "tokens", 0) or 0)
        checks = {"answered": not answer.get("is_error"), "knows_the_gold": "11.6.3" in reply,
                  "memory_whole": answer["tokens"] >= (0.8 * expected if expected else 100_000)}
        summary.update(tokens=answer["tokens"], expected_tokens=expected or None, checks=checks,
                       model=tries[-1]["model"])
        (conf / "copy-test.txt").write_text(reply, encoding="utf-8")         # the chat's words stay on this machine
        if not all(checks.values()):
            raise SystemExit("the new copy did not pass its test: " + ", ".join(k for k, ok in checks.items() if not ok))
        (conf / "MODEL").write_text(tries[-1]["model"] + "\n", encoding="utf-8")
        if answer["tokens"] > COPY_WARN_TOKENS:
            summary["warning"] = f"the copy holds {answer['tokens']} tokens; a job may not fit beside it"
        summary["status"] = "ok"
    except SystemExit as exc:
        summary["error"] = str(exc)
    except Exception as exc:
        summary["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    if summary["status"] != "ok" and summary.get("session"):                  # the copy in use before comes back
        sid = summary["session"]
        if kept is not None:
            (folder / f"{sid}.jsonl").unlink(missing_ok=True)
            shutil.move(str(kept), folder / f"{old_sid}.jsonl")
            summary["restored"] = True
        elif not old_sid:
            (folder / f"{sid}.jsonl").unlink(missing_ok=True)
        if old_sid:
            (conf / "BASE_SESSION").write_text(old_sid + "\n", encoding="utf-8")
        else:
            (conf / "BASE_SESSION").unlink(missing_ok=True)
    summary["minutes"] = round((time.time() - started) / 60, 1)
    (out / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("stage", choices=["script", "copy"])
    parser.add_argument("--from-run", default="")
    parser.add_argument("--chapter-map", default="")
    parser.add_argument("--videos", default="")
    parser.add_argument("--course", default="")
    parser.add_argument("--language", default="Hinglish")
    parser.add_argument("--max-rounds", default="")           # the writer weighs the checks itself; kept for the job form
    parser.add_argument("--fresh", action="store_true")      # a new session from the skill alone, not the taught chat
    parser.add_argument("--url", default="")                 # stage copy: the locked copy of the taught chat
    parser.add_argument("--sha256", default="")
    parser.add_argument("--tokens", default="0")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.stage == "copy":
        summary = install_copy(args)
        print(json.dumps({k: summary.get(k) for k in ("status", "error", "minutes", "tokens", "checks")}, ensure_ascii=False))
        return 0 if summary["status"] == "ok" else 1
    summary = script(args)
    print(json.dumps({k: summary.get(k) for k in ("status", "error", "minutes", "rewritten")}, ensure_ascii=False))
    return 0 if summary["status"] in ("ok", "needs_fix") else 1


if __name__ == "__main__":
    raise SystemExit(main())
