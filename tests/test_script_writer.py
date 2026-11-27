"""The script writer's skill and self-check (Navin, 26 November 2026: script writing moves from Codex to Claude, "mujhe
hubahu tumhare jaisi script chahiye"; `.claude/skills/bie-script-writer`, `tools/script_writer_check.py`)."""
from __future__ import annotations

import copy
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import script_writer_check  # noqa: E402
from bie.brain import studio_script  # noqa: E402
from tests.test_studio_naksha import chapter  # noqa: E402
from tests.test_studio_script import parts  # noqa: E402

SKILL = ROOT / ".claude" / "skills" / "bie-script-writer"


class Skill(unittest.TestCase):
    def test_the_skill_names_itself_and_says_when_to_use_it(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        head = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", text)
        self.assertIsNotNone(head)
        self.assertEqual(head.group(1), "bie-script-writer")
        self.assertIn("script", head.group(2))

    def test_every_file_and_command_the_skill_names_exists(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for name in re.findall(r"`references/([\w.-]+)`", text):
            self.assertTrue((SKILL / "references" / name).exists(), name)
        for path in ("bie/brain/namuna/script_11.6.3.json", "tools/script_writer_check.py", "CLAUDE.md",
                     "docs/roadmap/STATUS.md"):
            self.assertIn(path, text)
            self.assertTrue((ROOT / path).exists(), path)

    def test_the_skill_keeps_navins_settled_rules_and_the_gold_standard_withheld(self):
        words = " ".join((SKILL / "references" / "navin-ki-baatein.md").read_text(encoding="utf-8").split())
        for rule in ("A4", "B3", "B4", "B7", "B8", "C2", "C3", "H3", "N1"):
            self.assertIn(f"**{rule}", words)
        self.assertIn("bilkul passed hai meri taraf se", words)
        skill = " ".join((SKILL / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("Never open it while you write heading 11.6.3", skill)
        self.assertIn("ek aise teacher ki bhanti padhaya hai jise us concept ki poori knowledge hai", skill)
        self.assertNotIn("to a Class 11 NEET learner", skill)        # the learner is the course's, not a fixed class
        self.assertIn("not by adding lines", skill)

    def test_the_pairs_never_quote_six_words_of_the_withheld_example_as_text_to_copy(self):
        # jode.md quotes the gold standard on purpose (its reader is the writer); the scripts BIE's rules show Codex must
        # not (tests/test_studio_script.py checks that). Here: the skill says the pairs are never text to copy.
        self.assertIn("never as text to copy", (SKILL / "references" / "jode.md").read_text(encoding="utf-8"))


class SelfCheck(unittest.TestCase):
    def test_bies_problems_and_the_voice_measures_for_one_heading(self):
        result = script_writer_check.check({"parts": parts()}, chapter(), "11.6")
        self.assertEqual(result["heading"], "11.6")
        self.assertIsInstance(result["problems"], list)
        voice = result["voice"]
        self.assertEqual(voice["sentences"], sum(len(studio_script.sentences(p)) for p in parts()[1]["points"]))
        self.assertGreater(voice["words_per_sentence"], 0)
        self.assertTrue(0 <= voice["talk_share"] <= 1)

    def test_a_heading_that_grew_a_lot_is_called_patching(self):
        now = parts()
        before = copy.deepcopy(now)
        before[1]["points"] = before[1]["points"][:1]
        grown = script_writer_check.check({"parts": now}, chapter(), "11.6", {"parts": before})["growth"]
        self.assertTrue(grown["patching"] and grown["now"] > grown["before"])
        same = script_writer_check.check({"parts": now}, chapter(), "11.6", {"parts": now})["growth"]
        self.assertFalse(same["patching"])

    def test_the_command_prints_and_saves_the_result(self):
        with tempfile.TemporaryDirectory() as folder:
            script, chap, out = (Path(folder) / name for name in ("script.json", "chapter.json", "out.json"))
            script.write_text(json.dumps({"parts": parts()}), encoding="utf-8")
            chap.write_text(json.dumps(chapter()), encoding="utf-8")
            printed = io.StringIO()
            with redirect_stdout(printed):
                script_writer_check.main(["--script", str(script), "--chapter", str(chap), "--heading", "11.6",
                                          "--json", str(out)])
            self.assertIn("words each", printed.getvalue())
            self.assertEqual(json.loads(out.read_text())["heading"], "11.6")
            with self.assertRaises(SystemExit):
                script_writer_check.check({"parts": parts()}, chapter(), "9.9")


if __name__ == "__main__":
    unittest.main()


FAKE_CLAUDE = r'''
import json, os, re, sys
args = sys.argv[1:]
if args[:2] == ["auth", "status"]:
    print(json.dumps({"loggedIn": True, "authMethod": os.environ.get("FAKE_AUTH", "claude.ai"), "email": "secret@x"}))
    sys.exit(0)
task = args[args.index("-p") + 1]
log = os.environ["FAKE_LOG"]
open(log, "a").write(json.dumps({"args": args, "api_key": "ANTHROPIC_API_KEY" in os.environ,
                                 "config": os.environ.get("CLAUDE_CONFIG_DIR", "")}) + "\n")
if task.startswith("Teen chhote jawab do"):                     # the copy's test
    model = args[args.index("--model") + 1]
    if os.environ.get("FAKE_COPY_ONLY_1M") and model == "opus":
        print(json.dumps({"type": "result", "is_error": True, "result": "Prompt is too long", "usage": {}}))
        sys.exit(1)
    if os.environ.get("FAKE_FORK_DIR"):
        open(os.environ["FAKE_FORK_DIR"] + "/fork-test.jsonl", "w").write("{}")
    print(json.dumps({"type": "result", "is_error": False, "session_id": "fork-test",
                      "result": "(1) 11.6.3 ka c2-c3; Navin: bilkul passed (2) B8: film script ki lines hubahu (3) Navin ki",
                      "usage": {"input_tokens": 10, "cache_read_input_tokens": int(os.environ.get("FAKE_COPY_TOKENS", "300000"))}}))
    sys.exit(0)
work = re.search(r"(\S+)/script\.json(?: in place| \(you wrote)", task).group(1)
written = json.loads(open(os.environ["FAKE_PART"]).read())
script = json.load(open(work + "/script.json"))
script["parts"] = [written if p.get("section") == written["section"] else p for p in script["parts"]]
open(work + "/script.json", "w").write(json.dumps(script))
open(work + "/YAADEIN_NEW.md", "w").write("- 11.6: seekha ki ...\n")
print(json.dumps({"type": "result", "is_error": False, "result": "11.6: 10 sentences, 0 problems", "num_turns": 7,
                  "session_id": "s1", "total_cost_usd": 1.5,
                  "usage": {"input_tokens": 100, "cache_read_input_tokens": 50, "output_tokens": 20}}))
'''


class WriterBase(unittest.TestCase):
    """A run folder, a chapter map, a fake Claude Code and its config folder for the writer's tests."""

    def setUp(self):
        import os
        import vm_claude
        self.vm_claude = vm_claude
        self.folder = tempfile.TemporaryDirectory()
        root = Path(self.folder.name)
        self.run_dir, self.map_dir = root / "srun", root / "nrun"
        self.run_dir.mkdir()
        self.map_dir.mkdir()
        (self.run_dir / "script.json").write_text(json.dumps({"chapter_title": "Ch", "parts": parts()}), encoding="utf-8")
        (self.map_dir / "chapter_map.json").write_text(json.dumps(chapter()), encoding="utf-8")
        self.fake = root / "claude"
        self.fake.write_text(f"#!{sys.executable}\n" + FAKE_CLAUDE, encoding="utf-8")
        self.fake.chmod(0o755)
        part = copy.deepcopy(parts()[1])
        part["points"][0]["says"] = ["Yeh nayi line hai jo teacher ki tarah samjhati hai."] + part["points"][0]["says"]
        (root / "part.json").write_text(json.dumps(part), encoding="utf-8")
        self.env = {"FAKE_LOG": str(root / "log.json"), "FAKE_PART": str(root / "part.json"),
                    "CLAUDE_CONFIG_DIR": str(root / "conf"), "ANTHROPIC_API_KEY": "sk-never"}
        self.old = {k: os.environ.get(k) for k in self.env}
        os.environ.update(self.env)
        (root / "conf").mkdir()

    def tearDown(self):
        import os
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.folder.cleanup()

    def call(self, n=-1):
        return [json.loads(line) for line in Path(self.env["FAKE_LOG"]).read_text().splitlines()][n]

    def args(self, **more):
        from types import SimpleNamespace
        return SimpleNamespace(**dict({"from_run": str(self.run_dir), "chapter_map": str(self.map_dir), "videos": "h11-6",
                                       "course": "Class 11", "language": "Hinglish",
                                       "out": str(Path(self.folder.name) / "out")}, **more))


class VmClaude(WriterBase):
    """The script stage on the VM with Claude as the writer (tools/vm_claude.py) and its job (maker "claude")."""

    def test_the_writer_writes_one_heading_and_bie_checks_it(self):
        summary = self.vm_claude.script(self.args(fresh=True), binary=str(self.fake))
        out = Path(self.folder.name) / "out"
        self.assertIn(summary["status"], ("ok", "needs_fix"), summary.get("error"))
        self.assertEqual(summary["rewritten"], ["11.6"])
        script = json.loads((out / "script.json").read_text(encoding="utf-8"))
        written = next(p for p in script["parts"] if p["section"] == "11.6")
        self.assertEqual(written["points"][0]["says"][0], "Yeh nayi line hai jo teacher ki tarah samjhati hai.")
        self.assertEqual([p["section"] for p in script["parts"]], [p["section"] for p in parts()])   # the rest kept
        for name in ("record.json", "SCRIPT.md", "SCRIPT.html", "chapter_map.json", "YAADEIN_NEW.md", "SUMMARY.json"):
            self.assertTrue((out / name).exists(), name)
        self.assertFalse((out / "work").exists())
        self.assertEqual(summary["usage"], {"input_tokens": 150, "output_tokens": 20})
        self.assertEqual(summary["cost"], {"total_inr": 0.0})
        call = self.call()
        self.assertFalse(call["api_key"])                       # never an Anthropic API key: Navin's plan only
        for flag in ("--model", "opus", "--effort", "xhigh", "--permission-mode", "dontAsk"):
            self.assertIn(flag, call["args"])
        allowed = call["args"][call["args"].index("--allowedTools") + 1:]
        self.assertTrue(any(a.startswith("Write(//") and a.endswith("/work/**)") for a in allowed))
        self.assertNotIn("Bash", allowed)                       # only the self-check may run
        allowed = allowed[:allowed.index("--disallowedTools")]
        self.assertNotIn("Read", allowed)                       # plan point 5: reading only the repository and the work
        self.assertIn(f"Read(/{ROOT}/**)", allowed)
        refused = call["args"][call["args"].index("--disallowedTools") + 1:]
        conf = self.env["CLAUDE_CONFIG_DIR"]
        for place in (conf, "/var/lib/bie/codex", "/var/lib/bie/deploy_key", "/etc"):
            self.assertIn(f"Read(/{place}/**)", refused)        # sign-ins, the chat's copy and key, the deploy key
        self.assertNotIn("--fork-session", call["args"])
        self.assertIn("bie-script-writer", call["args"][call["args"].index("-p") + 1])
        self.assertNotIn("You are the chat Navin taught", call["args"][call["args"].index("-p") + 1])

    def test_a_base_session_is_forked_for_every_job(self):
        (Path(self.env["CLAUDE_CONFIG_DIR"]) / "BASE_SESSION").write_text("session-taught\n")
        summary = self.vm_claude.script(self.args(), binary=str(self.fake))
        call = self.call()
        self.assertTrue(summary["base_session"])
        self.assertEqual(call["args"][call["args"].index("--resume") + 1], "session-taught")
        self.assertIn("--fork-session", call["args"])
        task = call["args"][call["args"].index("-p") + 1]
        self.assertTrue(task.startswith("You are the chat Navin taught"))       # its memory first, the skill a reminder
        self.assertIn("follow his latest word", task)

    def test_a_verdict_is_applied_to_the_heading_and_the_change_is_recorded(self):
        # Navin, 27 November 2026: c3 is the golden benchmark once its start and end follow B3; the writer applies it
        (Path(self.env["CLAUDE_CONFIG_DIR"]) / "BASE_SESSION").write_text("session-taught\n")
        words = "Navin: shuruaat mein recap ke saath 'yaad rakhein'; baaki har line jaisi hai waisi."
        summary = self.vm_claude.script(self.args(verdict=words), binary=str(self.fake))
        self.assertIn(summary["status"], ("ok", "needs_fix"), summary.get("error"))
        task = self.call()["args"][self.call()["args"].index("-p") + 1]
        self.assertTrue(task.startswith("You are the chat Navin taught"))
        self.assertIn("Navin gave his verdict on heading 11.6", task)
        self.assertIn(words, task)
        self.assertIn("word for word", task)
        self.assertNotIn("Write the script of heading", task)
        changed = summary["verdict_changes"]
        self.assertEqual([p["id"] for p in changed["points_changed"]], [parts()[1]["points"][0]["id"]])
        self.assertEqual(changed["points_changed"][0]["lines_added"],
                         ["Yeh nayi line hai jo teacher ki tarah samjhati hai."])
        self.assertEqual(changed["points_changed"][0]["lines_removed"], [])
        self.assertEqual(changed["points_same"], len(parts()[1]["points"]) - 1)
        self.assertEqual(summary["verdict"], words)

    def test_a_verdict_needs_the_heading_it_judges(self):
        (Path(self.env["CLAUDE_CONFIG_DIR"]) / "BASE_SESSION").write_text("session-taught\n")
        (self.run_dir / "script.json").write_text(json.dumps({"chapter_title": "Ch", "parts": parts()[:1]}),
                                                  encoding="utf-8")
        summary = self.vm_claude.script(self.args(verdict="Navin ka verdict, lambi si baat yahan."),
                                        binary=str(self.fake))
        self.assertEqual(summary["status"], "failed")
        self.assertIn("verdict: one heading", summary["error"])
        self.assertFalse(Path(self.env["FAKE_LOG"]).exists())

    def test_the_writer_gets_no_packet(self):
        # Navin, 27 November 2026: "packet needs wala option bhi hata do" (the c5 test, kept out)
        self.vm_claude.script(self.args(fresh=True), binary=str(self.fake))
        task = self.call()["args"][self.call()["args"].index("-p") + 1]
        self.assertNotIn("packet", task)

    def test_without_the_taught_chat_a_job_stops_unless_it_says_fresh(self):
        summary = self.vm_claude.script(self.args(), binary=str(self.fake))       # Navin, 26 November: the writer is that chat
        self.assertEqual(summary["status"], "failed")
        self.assertIn("step 3", summary["error"])
        self.assertFalse(Path(self.env["FAKE_LOG"]).exists())                    # Claude was never started

    def test_a_missing_writer_or_heading_fails_with_the_fix(self):
        summary = self.vm_claude.script(self.args(fresh=True), binary=str(Path(self.folder.name) / "nothing"))
        self.assertEqual(summary["status"], "failed")
        self.assertIn("bie-claude-setup", summary["error"])
        summary = self.vm_claude.script(self.args(videos="h99", fresh=True), binary=str(self.fake))
        self.assertIn("no heading", summary["error"])

    def test_the_login_is_reported_without_account_details(self):
        status = self.vm_claude.login_status(binary=str(self.fake))
        self.assertEqual(status, {"installed": True, "logged_in": True, "method": "claude.ai", "base_session": False})
        import os
        os.environ["FAKE_AUTH"] = "api_key"
        try:
            self.assertFalse(self.vm_claude.login_status(binary=str(self.fake))["logged_in"])   # a key is not the plan
        finally:
            os.environ.pop("FAKE_AUTH")

    def test_a_job_may_name_claude_only_for_the_script(self):
        import codex_vm
        job = codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "c1-script-test", "section": "studio", "stage": "script",
                                 "maker": "claude", "from_run": "https://x/run", "chapter_map": "https://x/map",
                                 "videos": "h11-6-3"})
        cmd = codex_vm.argv(job, Path("/tmp/o"))
        self.assertTrue(cmd[2].endswith("vm_claude.py") and cmd[3] == "script")
        self.assertEqual(cmd[cmd.index("--videos") + 1], "h11-6-3")
        self.assertNotIn("--fresh", cmd)
        self.assertIn("--fresh", codex_vm.argv(dict(job, fresh=True), Path("/tmp/o")))
        with self.assertRaises(codex_vm.JobError):                               # fresh belongs to the Claude writer only
            codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "c3-bad-test", "section": "studio", "stage": "script",
                               "from_run": "https://x/run", "fresh": True})
        words = "Navin: c3 hi rakho; shuruaat mein yaad rakhein, ant mein khula sawaal."
        cmd = codex_vm.argv(codex_vm.validate(dict(job, id="c6-verdict-test", verdict=words)), Path("/tmp/o"))
        self.assertEqual(cmd[cmd.index("--verdict") + 1], words)
        for bad in (dict(job, verdict="short"), dict(job, verdict=words, videos="h11-6-3,h11-7-2"),
                    {"section": "studio", "stage": "films", "from_run": "https://x/r", "verdict": words},
                    {"section": "studio", "stage": "script", "from_run": "https://x/r", "verdict": words}):
            bad = dict(bad, job=codex_vm.JOB_SCHEMA, id="c7-bad-verdict")
            with self.assertRaises(codex_vm.JobError):                           # a verdict: Claude's script, one heading
                codex_vm.validate(bad)
        for bad in ({"section": "studio", "stage": "films", "from_run": "https://x/r"},
                    {"section": "understand", "source": "https://x/b.pdf"}):
            with self.assertRaises(codex_vm.JobError):
                codex_vm.validate(dict({"job": codex_vm.JOB_SCHEMA, "id": "c2-bad-test", "maker": "claude"}, **bad))

    def test_the_setup_script_pins_the_writer_and_never_uses_a_key(self):
        text = (ROOT / "deployment" / "codex-vm" / "bie-claude-setup").read_text(encoding="utf-8")
        self.assertIn(f'CLAUDE_VERSION="{self.vm_claude.CLAUDE_VERSION}"', text)
        self.assertIn("env -u ANTHROPIC_API_KEY", text)
        self.assertIn("auth login", text)
        self.assertNotIn("--teleport", text)                    # 27 November: teleport cannot bring a Claude app chat
        self.assertIn('"$CONF/chat.key"', text)                 # the copy's key, kept only on the machine
        self.assertIn('chmod 600 "$CONF/chat.key"', text)
        self.assertIn('read -rsp', text)                        # pasted unseen
        self.assertIn('"cleanupPeriodDays"', text)              # the copies are never swept away
        self.assertIn('"hasTrustDialogAccepted"', text)         # a job never stops at the folder question
        self.assertIn("bie-claude-setup", (ROOT / "deployment" / "codex-vm" / "setup.sh").read_text(encoding="utf-8"))


def locked_copy(folder: Path, key: Path, sid: str = "aaaaaaaa-1111-2222-3333-444444444444", lines: int = 3):
    """A locked copy as Claude makes it: the chat's lines, gzip, then openssl AES-256-CBC with PBKDF2."""
    import gzip
    import hashlib
    import subprocess
    text = "".join(json.dumps({"type": "user", "sessionId": sid, "n": n}) + "\n" for n in range(lines))
    path = folder / f"copy-{sid[:4]}-{lines}.enc"
    done = subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt", "-pass",
                           f"file:{key}"], input=gzip.compress(text.encode()), capture_output=True, check=True)
    path.write_bytes(done.stdout)
    return path, hashlib.sha256(done.stdout).hexdigest(), text


class WriterCopy(WriterBase):
    """Stage copy (Navin, 27 November 2026, "Raasta 1"): a newer locked copy of the taught chat is installed only when
    it passes its test, the copy before is kept, and job copies beyond five are deleted."""

    def setUp(self):
        super().setUp()
        import os
        self.conf = Path(self.env["CLAUDE_CONFIG_DIR"])
        self.key = self.conf / "chat.key"
        self.key.write_text("k3y-for-tests\n")
        self.project = self.vm_claude.project_dir(self.vm_claude.environment())
        self.project.mkdir(parents=True)
        os.environ["FAKE_FORK_DIR"] = str(self.project)

    def tearDown(self):
        import os
        for name in ("FAKE_FORK_DIR", "FAKE_COPY_TOKENS", "FAKE_COPY_ONLY_1M"):
            os.environ.pop(name, None)
        super().tearDown()

    def copy_args(self, path, sha, tokens=300000):
        from types import SimpleNamespace
        return SimpleNamespace(url=str(path), sha256=sha, tokens=tokens, out=str(Path(self.folder.name) / "cout"))

    def test_a_good_copy_is_installed_and_the_one_before_kept(self):
        old = "bbbbbbbb-1111-2222-3333-444444444444"
        (self.project / f"{old}.jsonl").write_text("old chat\n")
        (self.conf / "BASE_SESSION").write_text(old + "\n")
        path, sha, text = locked_copy(Path(self.folder.name), self.key)
        summary = self.vm_claude.install_copy(self.copy_args(path, sha), binary=str(self.fake))
        self.assertEqual(summary["status"], "ok", summary.get("error"))
        sid = "aaaaaaaa-1111-2222-3333-444444444444"
        self.assertEqual((self.conf / "BASE_SESSION").read_text().strip(), sid)
        self.assertEqual((self.project / f"{sid}.jsonl").read_text(), text)
        kept = list((self.conf / "archive").glob("*.jsonl"))
        self.assertEqual([p.read_text() for p in kept], ["old chat\n"])          # never deleted
        self.assertEqual((self.conf / "MODEL").read_text().strip(), "opus")
        self.assertFalse((self.project / "fork-test.jsonl").exists())            # the test's own copy goes at once
        self.assertEqual(summary["checks"], {"answered": True, "knows_the_gold": True, "memory_whole": True})
        published = (Path(self.folder.name) / "cout" / "SUMMARY.json").read_text()
        self.assertNotIn("bilkul passed", published)                            # the chat's words stay on the machine
        self.assertIn("bilkul passed", (self.conf / "copy-test.txt").read_text())
        call = self.call()
        self.assertEqual(call["args"][call["args"].index("--resume") + 1], sid)
        self.assertIn("--fork-session", call["args"])
        self.assertFalse(call["api_key"])

    def test_a_copy_whose_memory_is_not_whole_is_refused_and_the_old_one_comes_back(self):
        import os
        old = "bbbbbbbb-1111-2222-3333-444444444444"
        (self.project / f"{old}.jsonl").write_text("old chat\n")
        (self.conf / "BASE_SESSION").write_text(old + "\n")
        os.environ["FAKE_COPY_TOKENS"] = "150000"                                 # a summary, not the whole memory
        path, sha, _ = locked_copy(Path(self.folder.name), self.key)
        summary = self.vm_claude.install_copy(self.copy_args(path, sha, tokens=320000), binary=str(self.fake))
        self.assertEqual(summary["status"], "failed")
        self.assertIn("memory_whole", summary["error"])
        self.assertTrue(summary["restored"])
        self.assertEqual((self.conf / "BASE_SESSION").read_text().strip(), old)
        self.assertEqual((self.project / f"{old}.jsonl").read_text(), "old chat\n")
        self.assertFalse((self.project / "aaaaaaaa-1111-2222-3333-444444444444.jsonl").exists())
        self.assertFalse((self.conf / "MODEL").exists())

    def test_only_the_bigger_window_holds_it_then_that_setting_stays(self):
        import os
        os.environ["FAKE_COPY_ONLY_1M"] = "1"
        path, sha, _ = locked_copy(Path(self.folder.name), self.key)
        summary = self.vm_claude.install_copy(self.copy_args(path, sha), binary=str(self.fake))
        self.assertEqual(summary["status"], "ok", summary.get("error"))
        self.assertEqual([t["model"] for t in summary["tries"]], ["opus", "opus[1m]"])
        self.assertEqual((self.conf / "MODEL").read_text().strip(), "opus[1m]")
        self.assertEqual(self.vm_claude.model_of(self.vm_claude.environment()), "opus[1m]")

    def test_a_copy_that_is_not_the_named_one_changes_nothing(self):
        path, sha, _ = locked_copy(Path(self.folder.name), self.key)
        summary = self.vm_claude.install_copy(self.copy_args(path, "0" * 64), binary=str(self.fake))
        self.assertEqual(summary["status"], "failed")
        self.assertIn("sha256", summary["error"])
        self.assertFalse((self.conf / "BASE_SESSION").exists())
        self.assertFalse(Path(self.env["FAKE_LOG"]).exists())                   # Claude never asked
        self.key.write_text("another key\n")
        summary = self.vm_claude.install_copy(self.copy_args(path, sha), binary=str(self.fake))
        self.assertIn("did not unlock", summary["error"])

    def test_job_copies_beyond_five_are_deleted_never_the_copy_in_use(self):
        import os
        import time
        base = "aaaaaaaa-1111-2222-3333-444444444444"
        (self.conf / "BASE_SESSION").write_text(base + "\n")
        (self.project / f"{base}.jsonl").write_text("chat\n")
        now = time.time()
        for n in range(8):
            fork = self.project / f"fork-{n}.jsonl"
            fork.write_text("{}")
            os.utime(fork, (now - 100 + n, now - 100 + n))
        (self.project / "fork-0").mkdir()
        gone = self.vm_claude.prune_forks(self.vm_claude.environment())
        self.assertEqual(sorted(gone), ["fork-0", "fork-1", "fork-2"])
        left = sorted(p.stem for p in self.project.glob("*.jsonl"))
        self.assertEqual(left, [base] + [f"fork-{n}" for n in range(3, 8)])
        self.assertFalse((self.project / "fork-0").exists())

    def test_the_copy_job_is_checked_and_routed(self):
        import codex_vm
        sha = "a" * 64
        job = codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "b1-writer-copy", "section": "studio", "stage": "copy",
                                 "maker": "claude", "url": codex_vm.COPY_URL + "writer-chat-1/chat.enc", "sha256": sha,
                                 "tokens": 320000})
        cmd = codex_vm.argv(job, Path("/tmp/o"))
        self.assertEqual(cmd[3], "copy")
        self.assertEqual(cmd[cmd.index("--sha256") + 1], sha)
        self.assertEqual(cmd[cmd.index("--tokens") + 1], "320000")
        for bad in ({"url": "https://example.com/chat.enc", "sha256": sha},          # only this repository's files
                    {"url": codex_vm.COPY_URL + "x/chat.enc", "sha256": "xyz"},
                    {"url": codex_vm.COPY_URL + "x/chat.enc", "sha256": sha, "maker": "codex"}):
            with self.assertRaises(codex_vm.JobError):
                codex_vm.validate(dict({"job": codex_vm.JOB_SCHEMA, "id": "b2-bad-copy", "section": "studio",
                                        "stage": "copy", "maker": "claude"}, **bad))
        with self.assertRaises(codex_vm.JobError):                                   # url belongs to the copy job only
            codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "c9-bad", "section": "studio", "stage": "script",
                               "maker": "claude", "from_run": "https://x/r", "url": codex_vm.COPY_URL + "a"})

