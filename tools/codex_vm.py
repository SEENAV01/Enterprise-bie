"""BIE job runner for Navin's private Codex machine (Task 044, deployment/codex-vm/).

The machine is signed in to Codex with Navin's ChatGPT Pro plan and holds the checker's Gemini keys. It
never runs this public repository's GitHub Actions (OpenAI: ChatGPT sign-in only on trusted private
machines, never for public repositories). Work reaches it as job files instead:

  python tools/codex_vm.py poll     run every queued job once (a systemd timer calls this every 2 minutes)
  python tools/codex_vm.py status   sign-in state, plan usage and the last jobs (for Navin and Claude)

A job is ``jobs/<id>.json`` on the ``codex-jobs`` branch (written by Claude through GitHub, later by the
one-button app). The runner checks every field against a fixed list, runs ``tools/run_brain.py`` from
``main`` without a shell (sections ``image`` and ``look``: ``tools/vm_image.py``, pictures through the plan, and
``tools/vm_look.py``, the LOOK-01 look check; Task 046), publishes the run folder to ``blindtest-results`` (``runs/vm-<id>-<section>/``)
and writes ``jobs/<id>.result.json`` next to the job. Keys never leave the machine: run_brain redacts them
and the auth file stays in CODEX_HOME. Only people with write access to the repository can add a job.

Environment (systemd sets it from /etc/bie/bie.env): BIE_HOME (default /var/lib/bie), BIE_REPO_URL (git
remote, default the repository over SSH with the deploy key), BIE_GIT_SSH (ssh command with the key),
CODEX_HOME, AICREDITS_GEMINI_API_KEY, GEMINI_API_KEY (Navin's free Google AI Studio key, added 25 October 2026;
sample content only, never student data), optional BIE_CODEX_MODEL. With both Gemini keys set the direct Google
key wins unless a job's ``routes`` says ``google=aicredits``; a job for the free key carries
``"routes": "google=direct", "models": "google=gemini-3.8-flash"`` (the free tier does not serve gemini-4-argon
or gemini-3.1-pro).
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOB_SCHEMA = "bie.vm-job/1"
JOBS_BRANCH = "codex-jobs"
RESULTS_BRANCH = "blindtest-results"
SECTIONS = ("understand", "lesson", "director", "notes", "game", "visual", "canvas", "chain", "image", "look")
# Task 046 one-shot test (Navin, 26 October 2026): "image" makes pictures with Codex's built-in image_gen tool through the
# ChatGPT plan (tools/vm_image.py, prompts written by BIE, at most 4 images) and returns the image files; "look" runs the
# LOOK-01 look check with the free Google reviewer (tools/vm_look.py). Both are fixed commands, like run_brain.
TOOL_SECTIONS = ("image", "look")
FRESH_ENV = "BIE_VM_FRESH"         # set on the one re-run of a poll after the checkout moved to a newer main
MAKERS = ("codex", "google", "openai")
REVIEWERS = ("google", "openai")
URL = re.compile(r"^https://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]{1,400}$")
FIELDS = {
    "id": re.compile(r"^[a-z0-9][a-z0-9-]{2,60}$"),
    "pages": re.compile(r"^[0-9][0-9,\- ]{0,59}$"),
    "videos": re.compile(r"^[A-Za-z0-9_,-]{1,60}$"),
    "course": re.compile(r"^[^\n\r\x00]{1,400}$"),
    "models": re.compile(r"^[a-z]+=[A-Za-z0-9/._:-]+(,[a-z]+=[A-Za-z0-9/._:-]+)*$"),
    "routes": re.compile(r"^[a-z]+=[a-z]+(,[a-z]+=[a-z]+)*$"),
    "reviewer_model": re.compile(r"^[A-Za-z0-9/._:-]{1,80}$"),
    "language": re.compile(r"^[A-Za-z ]{2,30}$"),
}
DEFAULTS = {"maker": "codex", "reviewer": "google", "max_inr": 300, "workers": 2, "max_rounds": 3}
RUN_TIMEOUT = 8 * 3600


class JobError(ValueError):
    pass


def validate(job: dict) -> dict:
    """The job with defaults, or JobError naming the first bad field. Unknown fields are refused."""
    if not isinstance(job, dict) or job.get("job") != JOB_SCHEMA:
        raise JobError(f"job: must be a {JOB_SCHEMA} object")
    allowed = {"job", "id", "section", "source", "chapter_map", "from_run", "resume_from", "pages", "videos", "course",
               "maker", "reviewer", "reviewer_model", "models", "routes", "max_inr", "workers", "max_rounds", "language",
               "with_visual", "render", "fake", "note", "prompts", "request", "max_images"}
    unknown = sorted(set(job) - allowed)
    if unknown:
        raise JobError("unknown fields: " + ", ".join(unknown))
    out = dict(DEFAULTS, **job)
    if out.get("section") not in SECTIONS:
        raise JobError("section: one of " + ", ".join(SECTIONS))
    if out["maker"] not in MAKERS or out["reviewer"] not in REVIEWERS:
        raise JobError("maker or reviewer: not allowed")
    for name in ("source", "chapter_map", "from_run", "resume_from", "prompts", "request"):
        if out.get(name) and not URL.match(str(out[name])):
            raise JobError(f"{name}: an https URL")
    if out["section"] == "image" and not out.get("prompts"):
        raise JobError("prompts: needed for image")
    if out["section"] == "look" and not out.get("request"):
        raise JobError("request: needed for look")
    if out["section"] not in TOOL_SECTIONS and (out.get("prompts") or out.get("request") or "max_images" in out):
        raise JobError("prompts, request and max_images: only for image and look")
    if "max_images" in out and (isinstance(out["max_images"], bool) or out["max_images"] not in (1, 2, 3, 4)):
        raise JobError("max_images: between 1 and 4")
    for name, pattern in FIELDS.items():
        if out.get(name) not in (None, "") and not pattern.match(str(out[name])):
            raise JobError(f"{name}: not allowed")
    if out["section"] in ("understand", "chain") and not out.get("source"):
        raise JobError("source: needed for understand and chain")
    if out["section"] in ("lesson", "notes", "game") and not out.get("chapter_map"):
        raise JobError("chapter_map: needed for lesson, notes and game")
    if out["section"] in ("director", "visual", "canvas") and not out.get("from_run"):
        raise JobError("from_run: needed for director, visual and canvas")
    for name, low, high in (("max_inr", 1, 1000), ("workers", 1, 4), ("max_rounds", 1, 3)):
        value = out[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
            raise JobError(f"{name}: between {low} and {high}")
    for name in ("with_visual", "render", "fake"):
        if name in out and not isinstance(out[name], bool):
            raise JobError(f"{name}: true or false")
    if out.get("fake") and os.environ.get("BIE_VM_ALLOW_FAKE") != "1":
        raise JobError("fake: only in tests")
    return out


def argv(job: dict, out: Path, python: str = sys.executable) -> list:
    """The command for a validated job (no shell, every value its own argument)."""
    if job["section"] == "image":
        return [python, "-B", str(ROOT / "tools" / "vm_image.py"), "--prompts", str(job["prompts"]), "--out", str(out),
                "--max-images", str(job.get("max_images", 4))]
    if job["section"] == "look":
        cmd = [python, "-B", str(ROOT / "tools" / "vm_look.py"), "--request", str(job["request"]), "--out", str(out),
               "--max-inr", str(job["max_inr"])]
        for name in ("models", "routes"):
            if job.get(name):
                cmd += ["--" + name, str(job[name])]
        return cmd
    cmd = [python, "-B", str(ROOT / "tools" / "run_brain.py"), "--section", job["section"], "--out", str(out),
           "--maker", job["maker"], "--reviewer", job["reviewer"], "--max-inr", str(job["max_inr"]),
           "--workers", str(job["workers"]), "--max-rounds", str(job["max_rounds"])]
    flags = {"source": "--source", "chapter_map": "--chapter-map", "from_run": "--from-run", "resume_from": "--resume-from",
             "pages": "--pages", "videos": "--videos", "course": "--course", "reviewer_model": "--reviewer-model",
             "models": "--models", "routes": "--routes", "language": "--language"}
    for name, flag in flags.items():
        if job.get(name):
            cmd += [flag, str(job[name])]
    for name in ("with_visual", "render", "fake"):
        if job.get(name):
            cmd.append("--" + name.replace("_", "-"))
    return cmd


class Repo:
    """The machine's clone; pushes go through the deploy key (BIE_GIT_SSH)."""

    def __init__(self, url: str, folder: Path):
        self.url, self.folder = url, folder

    def git(self, *args, cwd=None, check=True):
        env = dict(os.environ)
        if os.environ.get("BIE_GIT_SSH"):
            env["GIT_SSH_COMMAND"] = os.environ["BIE_GIT_SSH"]
        return subprocess.run(["git", "-c", "user.name=BIE Codex VM", "-c", "user.email=bie-vm@users.noreply.github.com", *args],
                              cwd=cwd or self.folder, env=env, capture_output=True, text=True, check=check)

    def fetch(self, *branches):
        if not (self.folder / ".git").exists():
            self.folder.mkdir(parents=True, exist_ok=True)
            self.git("init", "-q")
            self.git("remote", "add", "origin", self.url)
        for branch in branches:
            self.git("fetch", "-q", "origin", f"+refs/heads/{branch}:refs/remotes/origin/{branch}", check=False)

    def files(self, branch: str, folder: str) -> list:
        done = self.git("ls-tree", "--name-only", f"origin/{branch}", folder + "/", check=False)
        return sorted(line for line in done.stdout.splitlines() if line)

    def show(self, branch: str, path: str) -> str:
        return self.git("show", f"origin/{branch}:{path}").stdout

    def commit_files(self, branch: str, files: dict, message: str, attempts: int = 4):
        """Add or replace files on a branch and push, retrying when someone else pushed first."""
        for attempt in range(attempts):
            with tempfile.TemporaryDirectory(prefix="bie-push-") as work:
                work = Path(work)
                self.git("init", "-q", cwd=work)
                self.git("remote", "add", "origin", self.url, cwd=work)
                exists = self.git("fetch", "-q", "--depth=1", "origin", branch, cwd=work, check=False).returncode == 0
                self.git("checkout", "-q", "FETCH_HEAD" if exists else "--orphan", *([] if exists else [branch]), cwd=work)
                if exists:
                    self.git("checkout", "-q", "-B", branch, cwd=work)
                for relative, source in files.items():
                    target = work / relative
                    if isinstance(source, Path) and source.is_dir():
                        shutil.rmtree(target, ignore_errors=True)
                        shutil.copytree(source, target)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(source if isinstance(source, str) else source.read_text(encoding="utf-8"),
                                          encoding="utf-8")
                self.git("add", "-A", ".", cwd=work)
                self.git("commit", "-q", "-m", message, cwd=work)
                if self.git("push", "-q", "origin", f"HEAD:refs/heads/{branch}", cwd=work, check=False).returncode == 0:
                    return
            time.sleep(2 ** attempt)
        raise RuntimeError(f"could not push to {branch}")


def home() -> Path:
    return Path(os.environ.get("BIE_HOME") or "/var/lib/bie")


def head() -> str:
    run = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return run.stdout.strip()


def repo() -> Repo:
    url = os.environ.get("BIE_REPO_URL") or "git@github.com:SEENAV01/Enterprise-bie.git"
    return Repo(url, home() / "state-repo")


def queued(rep: Repo) -> list:
    names = rep.files(JOBS_BRANCH, "jobs")
    finished = {n[:-len(".result.json")] for n in names if n.endswith(".result.json")}
    done_dir = home() / "done"
    local = {p.name for p in done_dir.iterdir()} if done_dir.exists() else set()
    return [n for n in names if n.endswith(".json") and not n.endswith(".result.json")
            and n[:-len(".json")] not in finished and Path(n).stem not in local]


def run_one(rep: Repo, name: str, *, python: str = sys.executable) -> dict:
    started = time.time()
    result = {"job": Path(name).stem, "started_at": started}
    try:
        job = validate(json.loads(rep.show(JOBS_BRANCH, name)))
        if job["id"] != Path(name).stem:
            raise JobError("id: must match the file name")
    except (JobError, ValueError) as exc:
        result.update(status="refused", error=str(exc)[:300], finished_at=time.time())
        return result
    out = home() / "runs" / job["id"]
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    try:
        done = subprocess.run(argv(job, out, python), cwd=ROOT, capture_output=True, text=True, timeout=RUN_TIMEOUT)
        result["exit_code"] = done.returncode
        (out / "RUN_LOG.txt").write_text(done.stdout[-200000:], encoding="utf-8")     # annotations only; keys redacted
    except subprocess.TimeoutExpired:
        result["exit_code"] = None
        result["error"] = f"the job did not finish within {RUN_TIMEOUT // 3600} hours"
    summary = json.loads((out / "SUMMARY.json").read_text(encoding="utf-8")) if (out / "SUMMARY.json").exists() else {}
    folder = f"runs/vm-{job['id']}-brain-{job['section']}"
    try:
        rep.commit_files(RESULTS_BRANCH, {folder: out}, f"VM job {job['id']} ({job['section']})")
        published = f"{RESULTS_BRANCH}:{folder}"
    except (RuntimeError, subprocess.CalledProcessError):
        published = f"not published; kept on the machine in {out}"
    result.update(status=summary.get("status", "failed"), results=published, finished_at=time.time(),
                  minutes=round((time.time() - started) / 60, 1),
                  cost_inr=(summary.get("cost") or {}).get("total_inr"),
                  plan_usage_after=summary.get("plan_usage_after"),
                  quality=summary.get("quality"), map_status=summary.get("map_status"),
                  stop_reason=summary.get("stop_reason"), error=summary.get("error") or result.get("error"))
    if job["section"] == "image":
        result.update(images_made=sum(1 for r in summary.get("images") or [] if r.get("status") == "made"),
                      plan_usage_before=summary.get("plan_usage_before"))
    if job["section"] == "look":
        result.update(look=summary.get("table"), reference=summary.get("reference"))
    return result


def poll(*, python: str = sys.executable, update_main: bool = True) -> list:
    lock_path = home() / "poll.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return []                                           # the previous poll is still running a job
        if update_main:
            before = head()
            subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin", "main"], check=False)
            subprocess.run(["git", "-C", str(ROOT), "checkout", "-q", "--detach", "origin/main"], check=False)
            if head() != before and os.environ.get(FRESH_ENV) != "1":
                # This process loaded the runner before the checkout moved, so it would check jobs with the old rules
                # (26 October 2026: the first image job after PR #77 was refused as "unknown fields"). Poll again,
                # once, with the code just checked out; the lock is released by closing it.
                lock.close()
                os.execve(python, [python, "-B", str(Path(__file__).resolve()), "poll"], dict(os.environ, **{FRESH_ENV: "1"}))
            installed = home() / "pyproject.sha256"
            current = hashlib.sha256((ROOT / "pyproject.toml").read_bytes()).hexdigest()
            if not installed.exists() or installed.read_text() != current:      # dependencies changed on main
                subprocess.run([python, "-m", "pip", "install", "-q", "-e",
                                f"{ROOT}[document-intelligence,document-intelligence-layout]"], check=True)
                installed.write_text(current)
        rep = repo()
        rep.fetch(JOBS_BRANCH)
        results = []
        for name in queued(rep):
            result = run_one(rep, name, python=python)
            (home() / "done").mkdir(parents=True, exist_ok=True)            # never run a job twice, even if reporting fails
            (home() / "done" / Path(name).stem).write_text(result["status"], encoding="utf-8")
            try:
                rep.commit_files(JOBS_BRANCH, {f"jobs/{Path(name).stem}.result.json":
                                               json.dumps(result, indent=1, sort_keys=True) + "\n"},
                                 f"VM job {Path(name).stem}: {result['status']}")
            except (RuntimeError, subprocess.CalledProcessError):
                print(json.dumps({"job": result["job"], "warning": "result not pushed"}), flush=True)
            results.append(result)
            print(json.dumps({k: result.get(k) for k in ("job", "status", "minutes", "cost_inr", "results")}), flush=True)
        return results


def status() -> dict:
    sys.path.insert(0, str(ROOT))
    from bie.model_gateway.live.codex_client import CodexExecClient
    client = CodexExecClient()
    from bie.model_gateway.live.config import RESELLER_PROVIDER_KEY_ENV, key_for, route_for
    keys = {"direct": bool(key_for("google")),
            "aicredits": bool((os.environ.get(RESELLER_PROVIDER_KEY_ENV["aicredits"]["google"]) or "").strip())}
    try:
        via = route_for("google")[0] or "none"
    except ValueError as exc:                            # a wrong BIE_GEMINI_VIA in bie.env
        via = "invalid: " + str(exc)[:80]
    # Presence only, never a key or a piece of one. The default route is what a job without "routes" gets.
    out = {"login": client.login_status(), "gemini_key_set": keys["direct"] or keys["aicredits"], "gemini_keys": keys,
           "gemini_default_route": via}
    out["plan_usage"] = client.plan_usage() if out["login"]["logged_in"] else {"unavailable": "not signed in"}
    done = home() / "done"
    out["last_jobs"] = {p.name: p.read_text() for p in sorted(done.iterdir())[-5:]} if done.exists() else {}
    return out


def main(argv_=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("poll", "status"))
    parser.add_argument("--no-update", action="store_true", help="tests: do not move this checkout to origin/main")
    args = parser.parse_args(argv_)
    if args.command == "status":
        print(json.dumps(status(), indent=1))
        return 0
    poll(update_main=not args.no_update)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
