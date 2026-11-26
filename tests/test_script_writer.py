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
open(log, "w").write(json.dumps({"args": args, "api_key": "ANTHROPIC_API_KEY" in os.environ,
                                 "config": os.environ.get("CLAUDE_CONFIG_DIR", "")}))
work = re.search(r"(\S+)/script\.json in place", task).group(1)
written = json.loads(open(os.environ["FAKE_PART"]).read())
script = json.load(open(work + "/script.json"))
script["parts"] = [written if p.get("section") == written["section"] else p for p in script["parts"]]
open(work + "/script.json", "w").write(json.dumps(script))
open(work + "/YAADEIN_NEW.md", "w").write("- 11.6: seekha ki ...\n")
print(json.dumps({"type": "result", "is_error": False, "result": "11.6: 10 sentences, 0 problems", "num_turns": 7,
                  "session_id": "s1", "total_cost_usd": 1.5,
                  "usage": {"input_tokens": 100, "cache_read_input_tokens": 50, "output_tokens": 20}}))
'''


class VmClaude(unittest.TestCase):
    """The script stage on the VM with Claude as the writer (tools/vm_claude.py) and its job (maker "claude")."""

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

    def args(self, **more):
        from types import SimpleNamespace
        return SimpleNamespace(**dict({"from_run": str(self.run_dir), "chapter_map": str(self.map_dir), "videos": "h11-6",
                                       "course": "Class 11", "language": "Hinglish",
                                       "out": str(Path(self.folder.name) / "out")}, **more))

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
        call = json.loads(Path(self.env["FAKE_LOG"]).read_text())
        self.assertFalse(call["api_key"])                       # never an Anthropic API key: Navin's plan only
        for flag in ("--model", "opus", "--effort", "xhigh", "--permission-mode", "dontAsk"):
            self.assertIn(flag, call["args"])
        allowed = call["args"][call["args"].index("--allowedTools") + 1:]
        self.assertTrue(any(a.startswith("Write(//") and a.endswith("/work/**)") for a in allowed))
        self.assertNotIn("Bash", allowed)                       # only the self-check may run
        self.assertNotIn("--fork-session", call["args"])
        self.assertIn("bie-script-writer", call["args"][call["args"].index("-p") + 1])

    def test_a_base_session_is_forked_for_every_job(self):
        (Path(self.env["CLAUDE_CONFIG_DIR"]) / "BASE_SESSION").write_text("session-taught\n")
        summary = self.vm_claude.script(self.args(), binary=str(self.fake))
        call = json.loads(Path(self.env["FAKE_LOG"]).read_text())
        self.assertTrue(summary["base_session"])
        self.assertEqual(call["args"][call["args"].index("--resume") + 1], "session-taught")
        self.assertIn("--fork-session", call["args"])

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
        for bad in ({"section": "studio", "stage": "films", "from_run": "https://x/r"},
                    {"section": "understand", "source": "https://x/b.pdf"}):
            with self.assertRaises(codex_vm.JobError):
                codex_vm.validate(dict({"job": codex_vm.JOB_SCHEMA, "id": "c2-bad-test", "maker": "claude"}, **bad))

    def test_the_setup_script_pins_the_writer_and_never_uses_a_key(self):
        text = (ROOT / "deployment" / "codex-vm" / "bie-claude-setup").read_text(encoding="utf-8")
        self.assertIn(f'CLAUDE_VERSION="{self.vm_claude.CLAUDE_VERSION}"', text)
        self.assertIn("env -u ANTHROPIC_API_KEY", text)
        self.assertIn("auth login", text)
        self.assertIn('TP="$CONF/teleport-repo"', text)              # never the checkout the running jobs use
        self.assertNotIn('cd "$BIE_HOME/repo"', text)
        self.assertIn('run_claude --teleport "$session")', text)                # on the screen: teleport is interactive
        self.assertIn('"cleanupPeriodDays"', text)                                # the taught chat is never swept away
        self.assertIn("bie-claude-setup", (ROOT / "deployment" / "codex-vm" / "setup.sh").read_text(encoding="utf-8"))
