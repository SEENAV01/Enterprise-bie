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

Stage ``chapter`` (Navin, 28 November 2026: "Option 1 chapter job ka code banaunga") writes a chapter's headings one after
another in the chapter's order, each by its own fork of the taught chat with the script so far, the headings this job
wrote before it included, so every heading is written the way c3 was. The headings Navin chose (``--keep``, taken from
``--keep-from`` where that run holds them) are never changed: a fork that touches any heading but its own has that
heading put back. One call writes one heading and ends ``paused`` with the time to go on, so the machine runs other jobs
between headings; after ``--per-window`` headings in one of the plan's five-hour windows (room for Navin's own chats on
the same plan), or when the plan's limit stops the writer, the job waits for the window to open again and the stopped
fork goes on where it stopped. Its state lives beside the run folder (``<out>.work``), is never published, and goes when
the chapter is done.

    python tools/vm_claude.py script --from-run <script run> --chapter-map <naksha run> --videos h11-6-3 --out <folder>
    python tools/vm_claude.py chapter --from-run <script run> --chapter-map <naksha run> --keep h11-6-2,h11-7-2 --out <folder>
    python tools/vm_claude.py copy --url <locked copy> --sha256 <hex> --tokens <its size> --out <folder>
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
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

WRITE = """Write the script of heading(s) {headings} of the chapter in {work}/chapter_map.json, in BIE's script format (the same
JSON as the other headings of {work}/script.json), and put each one into {work}/script.json in place of the heading with
that number, keeping every other heading exactly as it is. The script so far is in {work}/script.json; the teaching
plan's ideas are in {work}/naksha.json when that file exists.
"""

# A verdict on a heading the writer wrote in an earlier run (Navin, 27 November 2026: "C3 is our golden benchmark after
# rectifying recap ke sath yaad rakhein ant mein shuru ka sawal aur khula chhodo"): the writer applies it to that heading
# and keeps every other line, so what he chose stays what he chose.
VERDICT = """Navin gave his verdict on heading {headings} as it stands in {work}/script.json (you wrote it in an earlier job,
and he chose it):

{verdict}

Apply the verdict to that heading in {work}/script.json and to nothing else: change only the lines and fields the verdict
is about, and keep every other point, line and field of the heading word for word as it is; every other heading stays
exactly as it is. The chapter is in {work}/chapter_map.json; the teaching plan's ideas are in {work}/naksha.json when
that file exists.
"""

TASK = """Use the bie-script-writer skill: read .claude/skills/bie-script-writer/SKILL.md and the files it names before you
write. Course: {course}. Language: {language}.

{job}
For each heading, before you hand it over, run:
{python} tools/script_writer_check.py --script {work}/script.json --chapter {work}/chapter_map.json --heading <number>
and weigh its findings as the skill says. Then add a few lines to {work}/YAADEIN_NEW.md: the heading and what you
learned.

Write only inside {work}. When you are done, reply with one line per heading: its number, its sentences and the
problems left."""

# A chapter job's heading (stage chapter): the WRITE task as c3 had it, and what this copy must know of the others.
CHAPTER = """This is a chapter job: BIE has the chapter's headings written one after another in the chapter's order, each by a
new copy of you, and this copy writes heading {heading} only. Its self-check is:
{check}
In {work}/script.json:
{lines}{work}/YAADEIN_NEW.md holds what the earlier copies of this job learned; read it, and add yours at its bottom.
"""
CHAPTER_WRITTEN = """- heading(s) {names} were written earlier in this job by copies of you: build on them as on your own script. This
  heading's opening recap recalls the heading just before it as it is written there, and its question takes up the
  question that heading left open.
"""
CHAPTER_KEPT = """- heading(s) {names} are the ones Navin chose: never change them. Where the next heading is one of them, end on its
  opening question left open, and teach in this heading what its opening recap recalls.
"""
CHAPTER_OLD = """- the other headings are BIE's older script and are written again after you: never take your way of saying things
  from them.
"""
# The same fork, when the plan's limit stopped it part-way (the task again, so nothing depends on what the fork kept).
CONTINUE = """The plan's usage limit stopped you part-way through this task; it has opened again. Go on from where you stopped:
what you already wrote in {work} stays, so read it there first. The task, as it was:

"""
WINDOW = 5 * 3600                  # the plan's session window
PER_WINDOW = 4                     # headings a chapter job writes in one window (about 14 % of a window each, c3)
RETRIES = 2                        # a heading that stopped for another reason is tried again this many times
RETRY_WAIT = 15 * 60
# The plan's limit, as Claude Code says it ("Claude AI usage limit reached|<time>", "5-hour limit reached ∙ resets 3pm",
# "You've hit your session limit · resets 3:00pm (Asia/Kolkata)"); never a long prompt ("Prompt is too long").
LIMIT = re.compile(r"usage limit|limit reached|hit your (?:\w+ )?limit|\b(?:session|weekly|5-hour|opus) limit|"
                   r"out of (?:extra )?usage", re.IGNORECASE)
RESETS = re.compile(r"resets?\s+(?:at\s+|on\s+)?(?:(?P<mon>[A-Z][a-z]{2})[a-z]*\s+(?P<day>\d{1,2}),?\s+(?:at\s+)?)?"
                    r"(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<ap>[ap]\.?m\.?)?(?:\s*\((?P<tz>[A-Za-z_]+(?:/[A-Za-z_]+)*)\))?",
                    re.IGNORECASE)
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


def headings_of(videos: str, chapter: dict) -> list:
    """Film ids or heading numbers ("h11-6-3", "11.6.3") as the chapter's heading numbers, in the chapter's order."""
    from bie.brain import studio_script
    wanted = {v.strip() for v in (videos or "").split(",") if v.strip()}
    out = []
    for h in studio_script.headings(chapter):
        if not wanted or h["number"] in wanted or studio_script.film_id(h["number"]) in wanted:
            out.append(h["number"])
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
            env: dict | None = None, fork: bool = True) -> list:
    """The Claude Code call: print mode, JSON result, the model and effort Navin chose, and only the tools the writer
    needs: read the repository and the work folder, write and edit only in the work folder, run the self-check; the
    sign-ins, keys and the chat's copy are refused. ``fork=False`` goes on in ``base`` itself (a chapter job's fork that
    the plan's limit stopped)."""
    env = env if env is not None else environment()
    cmd = [binary, "-p", task, "--model", model, "--effort", EFFORT, "--output-format", "json",
           "--permission-mode", "dontAsk", "--add-dir", str(work),
           "--allowedTools", f"Read(/{ROOT}/**)", f"Read(/{work}/**)", "Glob", "Grep", f"Write(/{work}/**)",
           f"Edit(/{work}/**)", f"Bash({python} tools/script_writer_check.py *)",
           "--disallowedTools", *refused(env)]
    if base:
        cmd += ["--resume", base] + (["--fork-session"] if fork else [])
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


def changes(before: dict, after: dict) -> dict:
    """What a verdict job changed in one heading, point by point and line by line, so the review shows that every line
    outside the verdict stayed as Navin chose it."""
    old = {p.get("id"): p for p in before.get("points") or []}
    new = {p.get("id"): p for p in after.get("points") or []}
    points = []
    for pid in list(dict.fromkeys(list(old) + list(new))):
        a, b = old.get(pid) or {}, new.get(pid) or {}
        if a == b:
            continue
        says_a, says_b = list(a.get("says") or []), list(b.get("says") or [])
        points.append({"id": pid, "added": not a, "removed": not b,
                       "lines_removed": [s for s in says_a if s not in says_b],
                       "lines_added": [s for s in says_b if s not in says_a],
                       "fields": sorted(k for k in set(a) | set(b) if k != "says" and a.get(k) != b.get(k))})
    fields = sorted(k for k in set(before) | set(after) if k != "points" and before.get(k) != after.get(k))
    return {"points_changed": points, "points_same": sum(1 for pid in old if old[pid] == new.get(pid)),
            "fields_changed": fields}


class Limit(Exception):
    """The plan's session or weekly limit stopped the writer; ``reset`` is when it opens again (epoch seconds) and
    ``session`` the chat that stopped, to go on in it."""

    def __init__(self, text: str, reset: float, session: str = ""):
        super().__init__(text)
        self.text, self.reset, self.session = text, reset, session


def reset_at(text: str, now: float | None = None) -> float:
    """When the plan opens again, from Claude Code's words (an epoch after "|", or "resets 3pm", "resets 3:00pm
    (Asia/Kolkata)", "resets Dec 2, 5am"), a few minutes late to be safe; an hour from now when it names no time."""
    from zoneinfo import ZoneInfo
    now = time.time() if now is None else now
    found = re.search(r"\|(\d{10})\b", text)
    if found:
        return max(float(found.group(1)), now) + 180
    found = RESETS.search(text)
    if not found:
        return now + 3600
    try:
        zone = ZoneInfo(found["tz"]) if found["tz"] else datetime.now().astimezone().tzinfo
    except Exception:                                       # a zone this machine does not know: its own clock
        zone = datetime.now().astimezone().tzinfo
    hour, minute = int(found["h"]), int(found["m"] or 0)
    noon = (found["ap"] or "").lower().replace(".", "")
    if noon == "pm" and hour < 12:
        hour += 12
    if noon == "am" and hour == 12:
        hour = 0
    if hour > 23 or minute > 59:
        return now + 3600
    here = datetime.fromtimestamp(now, zone)
    when = here.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if found["mon"] and found["mon"][:3].lower() in MONTHS:
        when = when.replace(month=MONTHS.index(found["mon"][:3].lower()) + 1, day=int(found["day"]))
        if when <= here:
            when = when.replace(year=when.year + 1)
    elif when <= here:
        when += timedelta(days=1)
    return min(when.timestamp(), now + 8 * 86400) + 180


def call_writer(cmd: list, env: dict, run=subprocess.run, timeout: int = TIMEOUT) -> dict:
    """One Claude Code call; its JSON result, or Limit when the plan's limit stopped it, or SystemExit saying why."""
    try:
        done = run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise SystemExit("Claude Code is not installed on this machine: sudo bie-claude-setup") from None
    except subprocess.TimeoutExpired:
        raise SystemExit(f"the writer did not finish within {timeout // 3600} hours") from None
    result = {}
    try:
        result = json.loads(done.stdout or "{}")
    except json.JSONDecodeError:
        result = {"result": (done.stdout or "")[-2000:]}
    if not isinstance(result, dict):
        result = {"result": str(result)[-2000:]}
    if done.returncode != 0 or result.get("is_error"):
        text = str(result.get("result") or done.stderr or done.stdout)[-400:]
        if LIMIT.search(text):
            raise Limit(text, reset_at(text), str(result.get("session_id") or ""))
        raise SystemExit("the writer stopped: " + text + ("" if "login" not in text.lower() else
                                                         " (sign in once: sudo bie-claude-setup)"))
    return result


def usage_of(result: dict) -> dict:
    usage = result.get("usage") or {}
    return {"input_tokens": int(usage.get("input_tokens") or 0) + int(usage.get("cache_read_input_tokens") or 0)
            + int(usage.get("cache_creation_input_tokens") or 0), "output_tokens": int(usage.get("output_tokens") or 0)}


def bie_checks(parts: list, chapter: dict, wanted: list) -> tuple:
    """BIE's own checks (``studio_script.problems``) on the headings written, with the earlier headings of the same
    script as what was taught before: (rounds, problems)."""
    from bie.brain import studio_script
    heads = {h["number"]: h for h in studio_script.headings(chapter)}
    order = list(heads)
    problems, rounds = {}, []
    for number in wanted:
        part = next((p for p in parts if p.get("section") == number), None)
        if part is None:
            problems[number] = ["the writer did not write this heading"]
            continue
        n = order.index(number)
        earlier = [p for p in parts if p.get("section") in order[:n]]
        later = [t for h in list(heads.values())[n + 1:] for t, _ in studio_script.first_terms(h)
                 if studio_script._technical(t)]
        found = studio_script.problems(part, heads[number], chapter, earlier, later)
        rounds.append({"section": number, "rounds": [{"round": 1, "problems": found, "writer": "claude"}]})
        if found:
            problems[number] = found
    return rounds, problems


def write_outputs(out: Path, work: Path, chapter: dict, title: str, parts: list, rounds: list, problems: dict,
                  usage: dict) -> list:
    """The run folder as the films stage reads it: script.json, record.json, SCRIPT.md and .html, the chapter map and
    plan, and what the writer learned (YAADEIN_NEW.md, folded into the skill by a reviewed PR)."""
    from bie.brain import studio_script
    record = {"parts": parts, "rounds": rounds, "problems": problems, "usage": usage}
    (out / "script.json").write_text(studio_script.dump({"chapter_title": title, "parts": parts}), encoding="utf-8")
    (out / "record.json").write_text(studio_script.dump({"rounds": rounds, "problems": problems, "usage": usage}),
                                     encoding="utf-8")
    (out / "SCRIPT.md").write_text(studio_script.markdown(chapter, record), encoding="utf-8")
    (out / "SCRIPT.html").write_text(studio_script.html(chapter, record), encoding="utf-8")
    shutil.copy(work / "chapter_map.json", out / "chapter_map.json")              # for the films stage
    for name in ("naksha.json", "YAADEIN_NEW.md"):
        if (work / name).exists():
            shutil.copy(work / name, out / name)
    return parts


def in_order(parts: list, chapter: dict) -> list:
    """The parts in the chapter's heading order (a part of no heading keeps its place at the end)."""
    from bie.brain import studio_script
    order = [h["number"] for h in studio_script.headings(chapter)]
    rank = {number: n for n, number in enumerate(order)}
    return sorted(parts, key=lambda p: rank.get(p.get("section"), len(order)))


def name_of(number: str) -> str:
    return number if number else '"" (the opening)'


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
        verdict = (getattr(args, "verdict", "") or "").strip()
        if verdict and (len(wanted) != 1 or not any(p.get("section") == wanted[0] for p in so_far.get("parts") or [])):
            raise SystemExit("verdict: one heading, written in the run it judges (from_run)")
        job = (VERDICT if verdict else WRITE).format(headings=", ".join(wanted), work=work, verdict=verdict)
        task = (TAUGHT if base else "") + TASK.format(course=args.course or "", language=args.language or "Hinglish",
                                                      job=job, work=work, python=sys.executable)
        model = model_of(env)
        cmd = command(task, work, binary=binary, base=base, model=model, env=env)
        summary["base_session"] = bool(cmd.count("--fork-session"))
        summary["model"] = f"{model}, effort {EFFORT}"
        try:
            result = call_writer(cmd, env, run)
        except Limit as stop:
            raise SystemExit("the writer stopped at the plan's limit: " + stop.text) from None
        summary.update(usage=usage_of(result), turns=result.get("num_turns"),
                       writer_reply=str(result.get("result") or "")[-1500:], notional_usd=result.get("total_cost_usd"))
        written = json.loads((work / "script.json").read_text(encoding="utf-8"))
        rounds, problems = bie_checks(written.get("parts") or [], chapter, wanted)
        parts = write_outputs(out, work, chapter, written.get("chapter_title") or title, written.get("parts") or [],
                              rounds, problems, summary["usage"])
        summary.update(status="ok" if not problems else "needs_fix", rewritten=wanted, problems=problems,
                       script=studio_script.counts(chapter, parts))
        if verdict:
            before = next(p for p in so_far["parts"] if p.get("section") == wanted[0])
            after = next((p for p in written.get("parts") or [] if p.get("section") == wanted[0]), {})
            summary["verdict"] = verdict
            summary["verdict_changes"] = changes(before, after)
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


IDENTITY = ("from_run", "chapter_map", "keep_from", "keep", "videos", "course", "language")


def start_chapter(folder: Path, args) -> dict:
    """A chapter job's first call: the work folder (chapter map, plan, the script so far with the chosen headings in
    it) and its state: the headings to write in the chapter's order and the ones Navin chose."""
    import vm_studio
    from bie.brain import studio_script
    source = args.chapter_map or args.from_run
    if not source:
        raise SystemExit("chapter: chapter_map (the naksha run) or from_run (a script run)")
    chapter = vm_studio.read_json(source, "chapter_map.json")
    plans = vm_studio.maybe_json(source, "naksha.json")
    old = vm_studio.maybe_json(args.from_run, "script.json") if args.from_run else None
    title = (chapter.get("map") or {}).get("chapter_title", "")
    so_far = old if isinstance(old, dict) and old.get("parts") else {"chapter_title": title, "parts": []}
    asked = [v for v in (getattr(args, "keep", "") or "").split(",") if v.strip()]
    kept = headings_of(",".join(asked), chapter) if asked else []
    if len(kept) != len(asked):
        raise SystemExit(f"keep: {getattr(args, 'keep', '')!r} names a heading the chapter does not have")
    if getattr(args, "keep_from", ""):                       # Navin's chosen headings, from the run that holds them
        other = vm_studio.read_json(args.keep_from, "script.json")
        chosen = {p.get("section"): p for p in other.get("parts") or [] if p.get("section") in kept}
        so_far["parts"] = [chosen.pop(p.get("section"), p) for p in so_far["parts"]] + list(chosen.values())
    have = {p.get("section") for p in so_far["parts"]}
    missing = [name_of(h) for h in kept if h not in have]
    if missing:
        raise SystemExit("keep: " + ", ".join(missing) + " is in neither from_run nor keep_from")
    todo = [h for h in headings_of(args.videos, chapter) if h not in kept]
    if not todo:
        raise SystemExit(f"videos: no heading to write ({args.videos!r}, kept {', '.join(map(name_of, kept))})")
    so_far["parts"] = in_order(so_far["parts"], chapter)
    shutil.rmtree(folder, ignore_errors=True)
    work = folder / "work"
    work.mkdir(parents=True)
    (work / "chapter_map.json").write_text(json.dumps(chapter, ensure_ascii=False), encoding="utf-8")
    if isinstance(plans, dict):
        (work / "naksha.json").write_text(json.dumps(plans, ensure_ascii=False), encoding="utf-8")
    (work / "script.json").write_text(studio_script.dump(so_far), encoding="utf-8")
    per = int(getattr(args, "per_window", 0) or PER_WINDOW)
    return {"schema": "bie.chapter-job/1", "job": {k: str(getattr(args, k, "") or "") for k in IDENTITY},
            "title": so_far.get("chapter_title") or title, "todo": todo, "kept": kept, "done": [], "current": None,
            "window": {"start": None, "count": 0}, "per_window": max(1, per), "headings": {}, "rounds": [],
            "usage": {"input_tokens": 0, "output_tokens": 0}, "turns": 0, "calls": 0, "started": time.time()}


def chapter(args, *, run=subprocess.run, binary: str = "", now=time.time) -> dict:
    """Stage ``chapter``: one call writes the next heading of the chapter (see the module text) and ends ``paused``
    with ``resume_at``, or ``ok`` / ``needs_fix`` when the last heading is written."""
    from bie.brain import studio_script
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    folder = out.parent / (out.name + ".work")
    started = now()
    summary = {"schema": "bie.studio-run/1", "section": "studio", "stage": "chapter", "status": "failed", "maker": MAKER,
               "model": f"{MODEL}, effort {EFFORT}", "cost": {"total_inr": 0.0}, "error": None}
    state, work = None, folder / "work"

    def save():
        (folder / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")

    def pause(when: float, why: str):
        state["resume_at"] = when
        save()
        summary.update(status="paused", resume_at=when, waiting_for=why,
                       resume_at_utc=datetime.fromtimestamp(when, timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    try:
        env = environment()
        binary = binary or shutil.which("claude") or "claude"
        base = base_session(env)
        if not base and not getattr(args, "fresh", False):
            raise SystemExit("the chat Navin taught is not on this machine yet (sudo bie-claude-setup, step 3); "
                             "a job without it needs \"fresh\": true")
        identity = {k: str(getattr(args, k, "") or "") for k in IDENTITY}
        if (folder / "state.json").exists():
            state = json.loads((folder / "state.json").read_text(encoding="utf-8"))
            if state.get("job") != identity:                 # the same id run again with other fields: start over
                state = None
        if state is None:
            state = start_chapter(folder, args)
            save()
        chapter_map = json.loads((work / "chapter_map.json").read_text(encoding="utf-8"))
        model = model_of(env)
        summary["model"] = f"{model}, effort {EFFORT}"
        t = now()
        window = state["window"]
        if window["start"] is not None and t - window["start"] >= WINDOW:
            window.update(start=None, count=0)
        if state["current"] is None and state["todo"] and window["count"] >= state["per_window"]:
            pause(window["start"] + WINDOW + 120, f"{state['per_window']} headings written in this window of the plan")
        elif state["todo"] or state["current"]:
            fresh_start = state["current"] is None or not state["current"].get("session")
            if state["current"] is None:
                state["current"] = {"heading": state["todo"][0], "session": "", "tries": 0}
                if window["start"] is None:
                    window["start"] = t
                window["count"] += 1
            current = state["current"]
            number = current["heading"]
            if fresh_start:                                  # a heading always starts from the script before it
                if (folder / "before.json").exists() and current.get("began"):
                    shutil.copy(folder / "before.json", work / "script.json")
                else:
                    shutil.copy(work / "script.json", folder / "before.json")
                current["began"] = t
            save()
            check = (f"{sys.executable} tools/script_writer_check.py --script {work}/script.json --chapter "
                     f"{work}/chapter_map.json --heading {shlex.quote(number)}")
            lines = ""
            if state["done"]:
                lines += CHAPTER_WRITTEN.format(names=", ".join(map(name_of, state["done"])))
            if state["kept"]:
                lines += CHAPTER_KEPT.format(names=", ".join(map(name_of, state["kept"])))
            if len(state["todo"]) > 1:
                lines += CHAPTER_OLD
            job = WRITE.format(headings=name_of(number), work=work) + "\n" + CHAPTER.format(
                heading=name_of(number), check=check, work=work, lines=lines)
            task = (TAUGHT if base else "") + TASK.format(course=args.course or "", language=args.language or "Hinglish",
                                                          job=job, work=work, python=sys.executable)
            if current.get("session"):
                cmd = command(CONTINUE.format(work=work) + task, work, binary=binary, base=current["session"],
                              model=model, env=env, fork=False)
            else:
                cmd = command(task, work, binary=binary, base=base, model=model, env=env)
            summary["base_session"] = bool(base)
            state["calls"] += 1
            call_started = now()
            result = stop = error = None
            try:
                result = call_writer(cmd, env, run)
            except Limit as exc:
                stop = exc
            except SystemExit as exc:
                error = exc
            current["spent"] = current.get("spent", 0) + now() - call_started
            if stop is not None:                             # the same fork goes on when the plan opens again
                current["session"] = stop.session or current.get("session") or ""
                pause(stop.reset, "the plan's limit: " + stop.text[:200])
            elif error is not None:
                current["tries"] += 1
                gone = current.get("session") and re.search(r"no conversation found|session.{0,40}not found",
                                                            str(error), re.IGNORECASE)
                current["session"] = ""                       # the next try starts the heading again from before it
                if current["tries"] > RETRIES and not gone:
                    save()
                    raise error
                pause(now() + (0 if gone else RETRY_WAIT), str(error)[:300])
            else:
                if finish_heading(state, folder, work, chapter_map, number, result, current["spent"]):
                    if state["todo"]:
                        pause(now(), "the next heading (other jobs on this machine go first)")
                else:
                    pause(now(), f"heading {name_of(number)} was not written; it is tried again")
        if summary["status"] != "paused":
            problems = {h: v["problems"] for h, v in state["headings"].items() if v.get("problems")}
            summary.update(status="ok" if not problems else "needs_fix", problems=problems)
    except SystemExit as exc:
        summary["error"] = str(exc)
    except Exception as exc:                        # the runner publishes the folder either way; the error says why
        summary["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    if state is not None and (work / "script.json").exists():
        try:                                        # what is written so far is published, whatever stopped the call
            chapter_map = json.loads((work / "chapter_map.json").read_text(encoding="utf-8"))
            parts = json.loads((work / "script.json").read_text(encoding="utf-8")).get("parts") or []
            problems = {h: v["problems"] for h, v in state["headings"].items() if v.get("problems")}
            write_outputs(out, work, chapter_map, state["title"], parts, state["rounds"], problems, state["usage"])
            summary.update(rewritten=state["done"], kept=state["kept"], usage=state["usage"], turns=state["turns"],
                           progress={"written": state["done"], "left": state["todo"], "kept": state["kept"],
                                     "now": (state["current"] or {}).get("heading"), "per_window": state["per_window"]},
                           headings=state["headings"], script=studio_script.counts(chapter_map, parts))
        except Exception as exc:
            summary["error"] = summary["error"] or f"publishing: {type(exc).__name__}: {str(exc)[:200]}"
            if summary["status"] != "paused":
                summary["status"] = "failed"
        if summary["status"] in ("ok", "needs_fix"):
            shutil.rmtree(folder, ignore_errors=True)        # the chapter is done: its state goes
        elif summary["status"] == "failed":
            summary["kept_state"] = ("the job's state stays on this machine; a new job can go on from this run folder "
                                     "(from_run, with the headings written here added to keep)")
    try:
        summary["forks_deleted"] = len(prune_forks(environment()))
    except Exception:                                   # tidying never decides a job
        pass
    summary["minutes"] = round((now() - started) / 60, 1)
    (out / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return summary


def finish_heading(state: dict, folder: Path, work: Path, chapter_map: dict, number: str, result: dict,
                   seconds: float) -> bool:
    """A heading the writer finished: only its own part is taken (any other heading it touched is put back as it was,
    so Navin's chosen headings and the ones written before stay), BIE's checks run, and the state moves on. False when
    the writer left the heading out (it is tried again from the script before it)."""
    before = json.loads((folder / "before.json").read_text(encoding="utf-8"))
    try:
        written = json.loads((work / "script.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        written = {}
    mine = next((p for p in written.get("parts") or [] if p.get("section") == number), None)
    if mine is None or mine == next((p for p in before.get("parts") or [] if p.get("section") == number), None):
        state["current"]["tries"] += 1
        state["current"]["session"] = ""
        shutil.copy(folder / "before.json", work / "script.json")
        if state["current"]["tries"] > RETRIES:
            raise SystemExit(f"the writer did not write heading {name_of(number)}")
        return False
    old = {p.get("section"): p for p in before.get("parts") or []}
    new = {p.get("section"): p for p in written.get("parts") or []}
    restored = sorted(s for s in old if s != number and new.get(s) != old[s])
    dropped = sorted(s for s in new if s != number and s not in old)
    parts = in_order([p for p in before.get("parts") or [] if p.get("section") != number] + [mine], chapter_map)
    from bie.brain import studio_script
    (work / "script.json").write_text(studio_script.dump(dict(before, parts=parts)), encoding="utf-8")
    rounds, problems = bie_checks(parts, chapter_map, [number])
    usage = usage_of(result)
    state["rounds"] = [r for r in state["rounds"] if r.get("section") != number] + rounds
    state["headings"][number] = {"problems": problems.get(number, []), "turns": result.get("num_turns"),
                                 "usage": usage, "minutes": round(seconds / 60, 1),
                                 "writer_reply": str(result.get("result") or "")[-800:],
                                 "put_back": restored + dropped, "tries": state["current"]["tries"] + 1}
    for key in usage:
        state["usage"][key] += usage[key]
    state["turns"] += int(result.get("num_turns") or 0)
    state["done"].append(number)
    state["todo"] = [h for h in state["todo"] if h != number]
    state["current"] = None
    (folder / "before.json").unlink(missing_ok=True)
    (folder / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return True


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
    parser.add_argument("stage", choices=["script", "copy", "chapter"])
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
    parser.add_argument("--verdict", default="")              # stage script: Navin's verdict on one heading of from_run
    parser.add_argument("--keep", default="")                 # stage chapter: the headings Navin chose, never rewritten
    parser.add_argument("--keep-from", default="")            # stage chapter: the run that holds them, when from_run does not
    parser.add_argument("--per-window", type=int, default=PER_WINDOW)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.stage == "copy":
        summary = install_copy(args)
        print(json.dumps({k: summary.get(k) for k in ("status", "error", "minutes", "tokens", "checks")}, ensure_ascii=False))
        return 0 if summary["status"] == "ok" else 1
    if args.stage == "chapter":
        summary = chapter(args)
        print(json.dumps({k: summary.get(k) for k in ("status", "error", "minutes", "rewritten", "resume_at_utc")},
                         ensure_ascii=False))
        return 0 if summary["status"] in ("ok", "needs_fix", "paused") else 1
    summary = script(args)
    print(json.dumps({k: summary.get(k) for k in ("status", "error", "minutes", "rewritten")}, ensure_ascii=False))
    return 0 if summary["status"] in ("ok", "needs_fix") else 1


if __name__ == "__main__":
    raise SystemExit(main())
