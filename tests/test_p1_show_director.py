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


if __name__ == "__main__":
    unittest.main()
