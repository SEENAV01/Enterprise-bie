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

    python tools/vm_claude.py script --from-run <script run> --chapter-map <naksha run> --videos h11-6-3 --out <folder>
"""
from __future__ import annotations

import argparse
import json
import os
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
TIMEOUT = 6 * 3600
MAKER = "claude (Claude Code on Navin's Claude plan, the bie-script-writer skill)"
# The first words a job gives the taught chat (Navin, 26 November 2026, "haan likh do"): that chat already knows his
# words and how the gold standard was made, so the skill must not pull it away from what he told it.
TAUGHT = """You are the chat Navin taught: you wrote the gold standard with him and you remember his words and verdicts.
Your own memory of what he told you comes first; the skill is only a reminder of it. Where the skill and what he told
you differ, follow his latest word, and write in YAADEIN_NEW.md where they differed.

"""

TASK = """Use the bie-script-writer skill: read .claude/skills/bie-script-writer/SKILL.md and the files it names before you
write. Course: {course}. Language: {language}.

Write the script of heading(s) {headings} of the chapter in {work}/chapter_map.json, in BIE's script format (the same
JSON as the other headings of {work}/script.json), and put each one into {work}/script.json in place of the heading with
that number, keeping every other heading exactly as it is. The script so far is in {work}/script.json; the teaching
plan's ideas are in {work}/naksha.json when that file exists.

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


def command(task: str, work: Path, *, binary: str, base: str = "", python: str = sys.executable) -> list:
    """The Claude Code call: print mode, JSON result, the model and effort Navin chose, and only the tools the writer
    needs (read anything, write and edit only in the work folder, run the self-check)."""
    cmd = [binary, "-p", task, "--model", MODEL, "--effort", EFFORT, "--output-format", "json",
           "--permission-mode", "dontAsk", "--add-dir", str(work),
           "--allowedTools", "Read", "Glob", "Grep", f"Write(/{work}/**)", f"Edit(/{work}/**)",
           f"Bash({python} tools/script_writer_check.py *)"]
    if base:
        cmd += ["--resume", base, "--fork-session"]
    return cmd


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
        env = environment()
        binary = binary or shutil.which("claude") or "claude"
        base = base_session(env)
        if not base and not getattr(args, "fresh", False):
            raise SystemExit("the chat Navin taught is not on this machine yet (sudo bie-claude-setup, step 3); "
                             "a job without it needs \"fresh\": true")
        task = (TAUGHT if base else "") + TASK.format(course=args.course or "", language=args.language or "Hinglish",
                                                      headings=", ".join(wanted), work=work, python=sys.executable)
        cmd = command(task, work, binary=binary, base=base)
        summary["base_session"] = bool(cmd.count("--fork-session"))
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
    summary["minutes"] = round((time.time() - started) / 60, 1)
    (out / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("stage", choices=["script"])
    parser.add_argument("--from-run", default="")
    parser.add_argument("--chapter-map", default="")
    parser.add_argument("--videos", default="")
    parser.add_argument("--course", default="")
    parser.add_argument("--language", default="Hinglish")
    parser.add_argument("--max-rounds", default="")           # the writer weighs the checks itself; kept for the job form
    parser.add_argument("--fresh", action="store_true")      # a new session from the skill alone, not the taught chat
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    summary = script(args)
    print(json.dumps({k: summary.get(k) for k in ("status", "error", "minutes", "rewritten")}, ensure_ascii=False))
    return 0 if summary["status"] in ("ok", "needs_fix") else 1


if __name__ == "__main__":
    raise SystemExit(main())
