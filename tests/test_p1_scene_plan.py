"""Phase 1, part B2: the scene-plan language, its compiler and its checks (agreement of 3 November 2026).

Offline. The Money v2 gold plan is the language's gold example: it must compile clean through every check, and a
wrong plan must be refused with the exact step and reason named.
"""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import formats  # noqa: E402
from bie.brain.gold.money_v2 import Timeline, build_script, gold_plan, gold_spec  # noqa: E402
from bie.brain.video import showplan as sp  # noqa: E402


def tiny_plan(**scene_extra):
    """One scene over l01 with a person, a thing and a text, all on cue words of l01."""
    scene = {"id": "A", "lines": ["l01"], "bg": "village",
             "cam": [{"t": {"line": "l01", "frac": 0.5}, "d": 0.8, "x": 900, "y": 500, "z": 1.2}],
             "steps": [
                 {"op": "person", "id": "ramu", "look": "ramu", "x": 700},
                 {"op": "item", "thing": {"draw": "sack", "p": {"w": 220, "label": "गेहूँ"}}, "x": 1200, "y": 885},
                 {"op": "text", "text": "Barter", "x": 960, "y": 200, "size": 64, "style": "title",
                  "t0": {"line": "l01", "word": "गेहूँ"}},
                 {"op": "pose", "who": "ramu", "t": {"line": "l01", "word": "गेहूँ", "plus": 0.2}, "pose": "point"},
             ]}
    scene.update(scene_extra)
    return {"schema": "bie.scene-plan/1", "scenes": [scene]}


class GoldPlan(unittest.TestCase):
    def test_the_gold_plan_is_a_valid_plan_and_compiles_clean_through_every_check(self):
        plan, T = gold_plan()
        self.assertEqual(formats.problems("scene_plan", plan), [])
        self.assertEqual(json.loads(json.dumps(plan)), plan)                 # pure JSON: what the director will write
        spec = sp.compile_plan(plan, T, width=1920, height=1080)
        self.assertEqual(formats.problems("show_spec", spec), [])
        self.assertEqual(len(spec["scenes"]), 20)
        self.assertEqual(sum(len(s["els"]) for s in spec["scenes"]), 477)
        lines_planned = [l for sc in plan["scenes"] for l in sc["lines"]]
        self.assertEqual(sorted(lines_planned), sorted(T.line_ids()))        # every line in exactly one scene
        self.assertEqual(len(lines_planned), len(set(lines_planned)))

    def test_the_gold_plan_round_trips_and_times_are_cues_not_seconds_mostly(self):
        plan, T = gold_plan()
        again = json.loads(json.dumps(plan))
        a = sp.compile_plan(copy.deepcopy(again), T, width=1920, height=1080)
        b = gold_spec(width=1920, height=1080)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        times = {"cue": 0, "number": 0}
        for sc in plan["scenes"]:
            for st in sc["steps"]:
                for key in ("t0", "t1", "t"):
                    v = st.get(key)
                    if isinstance(v, dict):
                        times["cue"] += 1
                    elif isinstance(v, (int, float)):
                        times["number"] += 1
        self.assertGreater(times["cue"], times["number"])                    # the language speaks in cue words

    def test_the_vocabulary_names_what_the_engine_and_compiler_really_have(self):
        vocab = sp.vocab()
        people = (ROOT / "bie" / "brain" / "video" / "engine" / "people.mjs").read_text(encoding="utf-8")
        bgs = (ROOT / "bie" / "brain" / "video" / "engine" / "backgrounds.mjs").read_text(encoding="utf-8")
        for look in vocab["looks"]:
            self.assertIn(f"{look}:", people, look)
        for pose in vocab["poses"]:
            self.assertIn(pose, sp.POSES, pose)
        self.assertEqual(sorted(vocab["poses"]), sorted(sp.POSES))
        for bg in vocab["backgrounds"]:
            self.assertIn(f"{bg}:", bgs, bg)
        ops = {name[3:] for name in dir(sp._Executor) if name.startswith("op_")}
        self.assertEqual(set(vocab["steps"]), ops)                           # the vocabulary is exactly the compiler


class Refusals(unittest.TestCase):
    def setUp(self):
        self.T = Timeline(build_script())

    def refuse(self, plan):
        with self.assertRaises(sp.PlanProblems) as ctx:
            sp.compile_plan(plan, self.T, width=1920, height=1080)
        return ctx.exception.problems

    def test_a_good_tiny_plan_fails_only_on_uncovered_lines(self):
        problems = self.refuse(tiny_plan())
        self.assertEqual(len(problems), 1)
        self.assertIn("lines not in any scene: l02, l03", problems[0])

    def test_a_missing_cue_word_names_the_line_and_word(self):
        plan = tiny_plan()
        plan["scenes"][0]["steps"][2]["t0"] = {"line": "l01", "word": "no-such-word"}
        self.assertTrue(any("l01" in p and "no-such-word" in p for p in self.refuse(plan)))

    def test_a_wrong_step_person_pose_or_saancha_parameter_is_named(self):
        plan = tiny_plan()
        plan["scenes"][0]["steps"][0]["op"] = "persn"
        self.assertTrue(any("no step 'persn'" in p for p in self.refuse(plan)))
        plan = tiny_plan()
        plan["scenes"][0]["steps"][3]["who"] = "mohan"
        self.assertTrue(any("no person 'mohan'" in p for p in self.refuse(plan)))
        plan = tiny_plan()
        plan["scenes"][0]["steps"][3]["pose"] = "fly"
        self.assertTrue(any("no pose 'fly'" in p for p in self.refuse(plan)))
        plan = tiny_plan()
        plan["scenes"][0]["steps"][1]["thing"] = {"draw": "sack", "p": {"w": 220, "colour": "red"}}
        self.assertTrue(any("no parameter 'colour'" in p for p in self.refuse(plan)))

    def test_the_cv17_checks_refuse_small_text_overlap_strip_and_text_alone(self):
        plan = tiny_plan()
        plan["scenes"][0]["steps"][2]["size"] = 24
        self.assertTrue(any("under the 36px floor" in p for p in self.refuse(plan)))
        plan = tiny_plan()
        plan["scenes"][0]["steps"].append({"op": "text", "text": "Barter bhi", "x": 965, "y": 205, "size": 64,
                                           "t0": {"line": "l01", "word": "गेहूँ"}})
        self.assertTrue(any("cover each other" in p for p in self.refuse(plan)))
        plan = tiny_plan()
        plan["scenes"][0]["steps"][2]["y"] = 1020
        self.assertTrue(any("subtitle strip" in p for p in self.refuse(plan)))
        plan = tiny_plan()
        plan["scenes"][0]["steps"] = [plan["scenes"][0]["steps"][2]]          # the text alone, nothing shown
        self.assertTrue(any("only text on screen" in p for p in self.refuse(plan)))

    def test_a_wrong_scene_line_and_a_duplicate_person_are_named(self):
        plan = tiny_plan(lines=["l99"])
        self.assertTrue(any("no narration line l99" in p for p in self.refuse(plan)))
        plan = tiny_plan()
        plan["scenes"][0]["steps"].append(dict(plan["scenes"][0]["steps"][0]))
        self.assertTrue(any("two persons named 'ramu'" in p for p in self.refuse(plan)))

    def test_a_text_behind_an_opaque_panel_is_not_on_screen(self):
        plan = tiny_plan()
        plan["scenes"][0]["steps"][2]["size"] = 24                            # small, but hidden behind a panel
        plan["scenes"][0]["steps"].append({"op": "rect", "x": 960, "y": 200, "w": 800, "h": 300,
                                           "fill": "#fdf6e3", "z": 50})
        problems = self.refuse(plan)
        self.assertFalse(any("under the 36px floor" in p for p in problems), problems)


class Cues(unittest.TestCase):
    def test_cue_arithmetic_keeps_the_symbol_and_the_seconds(self):
        T = Timeline(build_script())
        C, start, end = sp.cues(T)
        c = C("l03", "दो किलो") + 0.4
        self.assertEqual(c.to_json(), {"line": "l03", "word": "दो किलो", "plus": 0.4})
        self.assertAlmostEqual(float(c), T.cue("l03", "दो किलो") + 0.4, places=6)
        self.assertEqual((end("l02") - 0.2).to_json(), {"line": "l02", "edge": "end", "plus": -0.2})
        problems = []
        t = sp.resolve_time(c.to_json(), T, "here", problems)
        self.assertAlmostEqual(t, float(c), places=6)
        self.assertEqual(problems, [])
        sp.resolve_time({"line": "l03", "word": "nahi"}, T, "here", problems)
        self.assertIn("here", problems[0])


if __name__ == "__main__":
    unittest.main()
