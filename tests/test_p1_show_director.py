"""Phase 1, part C (first slice): BIE's director writes scene plans in the plan language; the compiler judges.

Offline: the maker is the brain's fake client, whose plan must pass the real compiler and all its checks —
the same gate a live Codex plan passes on the VM.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import formats, rulebook  # noqa: E402
from bie.brain.fake import BrainFakeClient, showplan_answer  # noqa: E402
from bie.brain.runner import SectionRunner  # noqa: E402
from bie.brain.show_director import check_plan, gold_example, run_show_director, video_step  # noqa: E402
from bie.brain.understanding import Course  # noqa: E402
from bie.brain.video import narration, showplan  # noqa: E402
from bie.model_gateway.claude_adapter import ClaudeAdapter  # noqa: E402
from bie.model_gateway.live.gateway import LiveGateway  # noqa: E402

BOOK = rulebook.load()
COURSE = Course(title="पैसा", subject="Economics", learners="class 9", language="Hinglish", exam="board", level="basic")


def beat(bid, part, say, covers=("p002-i2",), sub=""):
    return {"beat_id": bid, "part_id": part, "step": 1, "purpose": "teach", "say": say,
            "covers_item_ids": list(covers), "answers": [], "on_screen": "", "basis": "book",
            "source": "p2", "subtitle": sub or say}


LESSON = {"videos": [{"video_id": "v9", "title": "Barter", "status": "passed",
                      "card_parts": [{"part_id": "p1", "type": "", "item_ids": []}],
                      "beats": [beat("l1", "p1", "रामू के पास गेहूँ है।"),
                                beat("l2", "p1", "मोहन के पास कपड़ा है।"),
                                beat("l3", "p2", "दोनों बदल लेते हैं।", covers=("p002-i3",))]}]}


def runner_of():
    gateway = LiveGateway({"anthropic": ClaudeAdapter(BrainFakeClient("anthropic"), "fake-claude")}, sleep=lambda s: None)
    return SectionRunner(gateway, maker="anthropic", reviewer=None, rulebook=BOOK)


class Narration(unittest.TestCase):
    def test_a_lessons_beats_become_the_script_and_the_timeline_speaks_it(self):
        script = narration.script_of(LESSON["videos"][0])
        self.assertEqual([sc["id"] for sc in script], ["p1", "p2"])
        self.assertEqual([l["id"] for sc in script for l in sc["lines"]], ["l1", "l2", "l3"])
        T = narration.Timeline(script)
        self.assertLess(T.cue("l1", "गेहूँ"), T.cue("l2", "कपड़ा"))
        self.assertEqual(T.line_ids(), ["l1", "l2", "l3"])
        self.assertTrue(T.subs())
        from bie.brain.gold.money_v2 import Timeline as GoldTimeline   # the gold example speaks the same Timeline
        self.assertIs(GoldTimeline, narration.Timeline)


class DirectorStep(unittest.TestCase):
    def test_the_step_carries_the_vocabulary_the_saanche_and_the_gold_example(self):
        video = LESSON["videos"][0]
        T = narration.Timeline(narration.script_of(video))
        step = video_step(COURSE, video, T, rulebook=BOOK)
        self.assertEqual(step.section, "showplan")
        self.assertIn("bie.scene-plan/1", step.system)
        self.assertIn("sack", step.system)                       # the saancha library is in the prompt
        self.assertIn('"lines"', step.user)
        self.assertIn("36px", step.system)
        self.assertIn('"id": "B"', gold_example())               # the haat trade scene of the gold plan

    def test_the_check_is_the_compiler_and_names_problems_exactly(self):
        video = LESSON["videos"][0]
        T = narration.Timeline(narration.script_of(video))
        plan = showplan_answer(json.dumps({"video_id": "v9", "title": "Barter",
                                           "lines": [{"id": l, "scene": "p1" if l != "l3" else "p2"} for l in ("l1", "l2", "l3")]}))
        self.assertEqual(check_plan(plan, T), [])
        broken = json.loads(json.dumps(plan))
        broken["scenes"][0]["steps"][2]["t0"] = {"line": "l1", "word": "सोना"}
        problems = check_plan(broken, T)
        self.assertTrue(any("l1" in p and "सोना" in p for p in problems), problems)

    def test_the_director_writes_plans_the_compiler_accepts_and_the_specs_land(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            summary = run_show_director(LESSON, COURSE, runner_of(), out)
            self.assertEqual(summary["passed"], 1)
            self.assertEqual(summary["first_try"], 1)
            plan = json.loads((out / "plans" / "v9.plan.json").read_text(encoding="utf-8"))
            self.assertEqual(formats.problems("scene_plan", plan), [])
            spec = json.loads((out / "video_specs" / "v9.json").read_text(encoding="utf-8"))
            self.assertEqual(formats.problems("show_spec", spec), [])
            self.assertEqual(len(spec["scenes"]), 2)
            self.assertTrue(spec["subs"])
            self.assertIn("v9: passed", (out / "SHOWPLAN.md").read_text(encoding="utf-8"))


class Writers(unittest.TestCase):
    CHAPTER = {"items": {"i1": {"item_id": "i1", "content": "रामू गेहूँ देता है", "teachable": True,
                                "kind": "paragraph", "content_type": "story"},
                         "i2": {"item_id": "i2", "content": "पैसे का सफ़र", "teachable": True,
                                "kind": "paragraph", "content_type": "process"}},
               "map": {"chapter_title": "पैसा", "concepts": [
                   {"concept_id": "c1", "name": "Barter", "item_ids": ["i1"]},
                   {"concept_id": "c2", "name": "Money", "item_ids": ["i2"]}]}}

    def test_the_ai_writes_notes_pages_the_slot_accepts_and_the_deck_lands(self):
        from bie.brain.show_writers import run_notes_pages
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            summary = run_notes_pages(self.CHAPTER, COURSE, runner_of(), out)
            self.assertEqual(summary["status"], "passed")
            self.assertEqual(summary["pages"], 2)
            self.assertEqual(summary["pictures"], 1)
            page = json.loads((out / "notes" / "pages" / "pg-c1.json").read_text(encoding="utf-8"))
            self.assertEqual(formats.problems("notes_page", page), [])
            html = (out / "notes" / "NOTES_PAGES.html").read_text(encoding="utf-8")
            self.assertIn("Barter kya hai?", html)
            self.assertIn("pages/pg-c1.png", html)              # the engine's still slots in at render time

    def test_the_ai_writes_game_levels_the_slot_accepts_and_the_game_lands(self):
        from bie.brain.show_writers import run_game_levels
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            summary = run_game_levels(self.CHAPTER, COURSE, runner_of(), out)
            self.assertEqual(summary["status"], "passed")
            self.assertEqual(summary["levels"], 2)
            self.assertEqual(summary["mechanics"], ["find_partner", "run_process"])
            level = json.loads((out / "game" / "levels" / "lv-process.json").read_text(encoding="utf-8"))
            self.assertEqual(formats.problems("game_level", level), [])
            html = (out / "game" / "GAME.html").read_text(encoding="utf-8")
            self.assertIn("__bot", html)
            self.assertIn("Sahi saathi se milao.", html)

    def test_a_wrong_write_is_sent_back_with_the_slot_problems(self):
        from bie.brain.show_writers import check_levels, check_pages
        bad = {"pages": [{"schema": "bie.notes-page/1", "page_id": "p", "ask": "what", "question": "q",
                          "essence": "e", "answer": "a", "item_ids": ["nahi"],
                          "visual": {"kind": "flow", "steps": [{"label": "x"}, {"label": "y"}]}}]}
        problems = check_pages(bad, self.CHAPTER)
        self.assertTrue(any("item 'nahi' is not in the chapter" in p for p in problems))
        self.assertTrue(any("has no page" in p for p in problems))
        problems = check_levels({"levels": []}, self.CHAPTER)
        self.assertIn("at least 2 levels are needed", problems)


class VmJobs(unittest.TestCase):
    def test_the_vm_takes_the_new_sections_and_the_with_show_chain(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import codex_vm
        job = codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "t", "section": "showplan",
                                 "from_run": "https://raw.example/runs/x", "maker": "codex", "reviewer": "google",
                                 "max_inr": 50, "workers": 2, "max_rounds": 4})
        self.assertIn("--section", codex_vm.argv(job, Path("/tmp/o")))
        chain = codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "t2", "section": "chain", "source": "https://x/b.pdf",
                                   "maker": "codex", "reviewer": "google", "max_inr": 50, "workers": 2,
                                   "max_rounds": 4, "with_show": True})
        self.assertIn("--with-show", codex_vm.argv(chain, Path("/tmp/o")))
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "t3", "section": "showplan",
                               "maker": "codex", "reviewer": "google", "max_inr": 50, "workers": 2, "max_rounds": 4})


if __name__ == "__main__":
    unittest.main()
