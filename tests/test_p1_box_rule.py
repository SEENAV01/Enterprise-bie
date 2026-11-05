"""The box rule (dabba-niyam, Navin 5 November 2026): every drawing knows its box and the boxes of its words, every
background its reserved zones, and the scene-plan compiler refuses a plan whose things collide, naming them.

Offline (Node measures the engine's own drawings, as on the VM and the runners).
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import saanche  # noqa: E402
from bie.brain.gold.money_v2 import gold_plan  # noqa: E402
from bie.brain.show_director import language_rule, size_text, video_step, zones_text  # noqa: E402
from bie.brain.understanding import Course  # noqa: E402
from bie.brain.video import box_rules, boxes, narration, showplan  # noqa: E402

from tests.test_p1_show_director import BOOK, COURSE, LESSON  # noqa: E402

VIDEO = LESSON["videos"][0]


def timeline():
    return narration.Timeline(narration.script_of(VIDEO))


def plan_of(*steps, bg="paper", cam=None):
    """One scene over all three lines: a person at the left and the given steps."""
    base = [{"op": "person", "id": "ramu", "look": "ramu", "x": 420}]
    return {"schema": "bie.scene-plan/1", "video": "v9",
            "scenes": [{"id": "A", "lines": ["l1", "l2", "l3"], "bg": bg, "cam": cam or [], "steps": base + list(steps)}]}


def refusal(plan, language="Hinglish"):
    try:
        showplan.compile_plan(json.loads(json.dumps(plan)), timeline(), width=1920, height=1080, language=language)
    except showplan.PlanProblems as exc:
        return [p for p in exc.problems if "box rule" in p or "Hindi" in p or "caution" in p]
    return []


SACK = {"op": "item", "thing": {"draw": "sack", "p": {"w": 230, "label": "गेहूँ"}}, "x": 1300, "y": 885}


class EngineBoxes(unittest.TestCase):
    def test_every_saancha_of_the_library_is_measured_from_its_own_drawing(self):
        names = saanche.names()
        boxes.measure(items=[{"draw": n, "p": {}} for n in names])
        for name in names:
            got = boxes.item(name, {})
            self.assertNotIn("error", got, name)
            b = got["box"]
            self.assertIsNotNone(b, name)
            self.assertLess(b[0], b[2], name)
            self.assertLess(b[1], b[3], name)

    def test_a_label_is_a_word_box_inside_the_thing(self):
        got = boxes.item("sack", {"w": 230, "label": "गेहूँ"})
        words = [w for w in got["texts"] if w["t"] == "गेहूँ"]
        self.assertEqual(len(words), 1)
        wb, b = words[0]["box"], got["box"]
        self.assertTrue(b[0] <= wb[0] < wb[2] <= b[2] and b[1] <= wb[1] < wb[3] <= b[3], (wb, b))
        self.assertGreater(words[0]["px"], 0)

    def test_the_bank_label_is_drawn_at_a_real_size_now(self):
        # before the box rule the bank's label had font-size 0: it was never visible
        got = boxes.item("bank", {"label": "SBI"})
        words = [w for w in got["texts"] if w["t"] == "SBI"]
        self.assertTrue(words and words[0]["px"] > 10, got["texts"])

    def test_miniature_notes_inside_a_vault_carry_no_unreadable_words(self):
        bare = boxes.item("noteBundle", {"value": 500, "bare": True})
        self.assertEqual([w["t"] for w in bare["texts"]], [])
        full = boxes.item("noteBundle", {"value": 500})
        self.assertTrue(full["texts"])

    def test_a_person_knows_its_face(self):
        got = boxes.person(440, "ramu")
        b, f = got["box"], got["face"]
        self.assertTrue(b[0] <= f[0] < f[2] <= b[2], (f, b))
        self.assertAlmostEqual(f[1], b[1], delta=5)                 # the head is the top of the person
        self.assertLess(f[3], -0.6 * 440)                            # and the face ends above the shoulders

    def test_backgrounds_name_their_reserved_zones(self):
        shop = {z["name"]: z for z in boxes.zones("shop")}
        self.assertEqual(shop["board"]["keep"], "all")
        self.assertEqual(shop["shelf"]["keep"], "all")
        store = {z["name"]: z for z in boxes.zones("store")}
        self.assertEqual(store["almari"]["keep"], "all")
        self.assertEqual(boxes.zones("paper"), [])
        hall = {z["name"]: z for z in boxes.world_zones({"kind": "bankHall"})}
        self.assertEqual(hall["vault"]["keep"], "all")


class CompilerRefuses(unittest.TestCase):
    def test_a_clean_plan_passes(self):
        plan = plan_of(SACK, {"op": "text", "text": "रामू का गेहूँ", "x": 960, "y": 300, "size": 56, "style": "pill"})
        self.assertEqual(refusal(plan), [])

    def test_a_text_on_a_thing_is_named_with_both_and_the_second(self):
        plan = plan_of(SACK, {"op": "text", "text": "दस किलो", "x": 1300, "y": 780, "size": 48, "style": "pill"})
        problems = refusal(plan)
        self.assertTrue(any("'दस किलो' sits on 'sack' (गेहूँ)" in p and " from 0.5s for " in p for p in problems), problems)

    def test_a_thing_on_a_face(self):
        plan = plan_of({"op": "item", "thing": {"draw": "coin", "p": {}}, "x": 430, "y": 470, "s": 1.2})
        problems = refusal(plan)
        self.assertTrue(any("covers the face of person 'ramu'" in p for p in problems), problems)

    def test_nothing_on_a_reserved_zone_of_the_background(self):
        plan = plan_of({"op": "item", "thing": {"draw": "coin", "p": {}}, "x": 1540, "y": 200}, bg="shop")
        problems = refusal(plan)
        self.assertTrue(any("sits on the background's board (shop)" in p and "x 1280-1800" in p for p in problems), problems)

    def test_words_stay_inside_the_frame(self):
        plan = plan_of({"op": "text", "text": "बहुत लंबी पंक्ति यहाँ है", "x": 1880, "y": 300, "size": 56})
        problems = refusal(plan)
        self.assertTrue(any("cut by the frame's right edge" in p for p in problems), problems)

    def test_words_inside_a_small_thing_must_reach_the_floor_and_the_way_out_is_named(self):
        plan = plan_of({"op": "item", "thing": {"draw": "sack", "p": {"w": 230, "label": "गेहूँ"}}, "x": 1300, "y": 885,
                        "s": 0.6})
        problems = refusal(plan)
        self.assertTrue(any("'गेहूँ' inside 'sack'" in p and "36px floor" in p and "s at least" in p for p in problems),
                        problems)

    def test_a_text_that_flashes_before_the_cut_is_refused(self):
        spec = showplan.compile_plan(json.loads(json.dumps(plan_of())), timeline(), width=1920, height=1080, box_rule=False,
                                     said_shown=False)
        end = spec["scenes"][0]["t1"]                     # the scene's own end (its last line plus the tail)
        flash = plan_of({"op": "text", "text": "दावा बाकी", "x": 960, "y": 300, "size": 56, "t0": round(end - 0.7, 2)})
        problems = refusal(flash)
        self.assertTrue(any("on screen for only 0.7s" in p and "the scene ends" in p for p in problems), problems)
        held = plan_of({"op": "text", "text": "दावा बाकी", "x": 960, "y": 300, "size": 56, "t0": {"line": "l2", "edge": "start"}})
        self.assertFalse(any("on screen for only" in p for p in refusal(held)))

    def test_a_caution_line_never_reaches_the_screen(self):
        plan = plan_of({"op": "text", "text": "मान लीजिए दाम", "x": 960, "y": 300, "size": 56})
        problems = refusal(plan)
        self.assertTrue(any("caution" in p and "D1-06" in p for p in problems), problems)

    def test_a_hindi_video_writes_its_screen_labels_in_hindi(self):
        english = plan_of({"op": "text", "text": "Barter system", "x": 960, "y": 300, "size": 56})
        self.assertTrue(any("English on a Hindi video" in p for p in refusal(english)))
        self.assertEqual(refusal(english, language="English"), [])
        bracket = plan_of({"op": "text", "text": "वस्तु विनिमय (Barter system)", "x": 960, "y": 300, "size": 56})
        self.assertEqual(refusal(bracket), [])
        codes = plan_of({"op": "text", "text": "RBI ₹500 10 kg", "x": 960, "y": 300, "size": 56})
        self.assertEqual(refusal(codes), [])

    def test_without_node_the_box_rule_fails_closed(self):
        plan = plan_of({"op": "item", "thing": {"draw": "sack", "p": {"w": 230, "label": "बिना नोड"}}, "x": 1300, "y": 885})
        with mock.patch.dict(os.environ, {"BIE_NODE": str(ROOT / "no-such-node")}):
            problems = refusal(plan)
        self.assertTrue(any("box rule not checked" in p for p in problems), problems)

    def test_the_check_switch_freezes_only_the_demo(self):
        plan = plan_of(SACK, {"op": "text", "text": "दस किलो", "x": 1300, "y": 780, "size": 48, "style": "pill"})
        spec = showplan.compile_plan(json.loads(json.dumps(plan)), timeline(), width=1920, height=1080, box_rule=False,
                                     said_shown=False)
        self.assertTrue(spec["scenes"])


class GoldExample(unittest.TestCase):
    def test_the_directors_example_scene_keeps_the_box_rule(self):
        plan, T = gold_plan()
        try:
            showplan.compile_plan(json.loads(json.dumps(plan)), T, width=1920, height=1080, language="Hinglish")
            problems = []
        except showplan.PlanProblems as exc:
            problems = exc.problems
        self.assertEqual([p for p in problems if p.startswith("scene B:")], [])


class DirectorKnows(unittest.TestCase):
    def test_the_prompt_carries_the_rule_the_sizes_the_zones_and_the_language(self):
        step = video_step(COURSE, VIDEO, timeline(), rulebook=BOOK)
        self.assertIn("THE BOX RULE", step.system)
        self.assertIn("shop: board all x1280-1800", step.system)
        self.assertIn("Hindi video", step.system)
        self.assertIn("size ", size_text("sack"))
        self.assertIn("board all", zones_text())
        english = Course(title="Money", subject="Economics", learners="class 9", language="English", exam="board", level="basic")
        self.assertNotIn("Devanagari", language_rule(english.language))

    def test_a_long_list_of_problems_reaches_the_director_from_every_scene(self):
        from bie.brain.show_director import spread
        problems = [f"scene A: a{i}" for i in range(60)] + ["scene B: b0", "scene B: b1"]
        got = spread(problems)
        self.assertEqual(len(got), 40)
        self.assertIn("scene B: b1", got)                            # not buried under scene A's sixty
        self.assertIn("23 more problems of the same kinds, not listed: scene A 23", got[-1])
        self.assertEqual(spread(problems[:5]), problems[:5])

    def test_the_language_test_is_the_courses(self):
        self.assertTrue(box_rules.is_hindi("Hinglish"))
        self.assertTrue(box_rules.is_hindi("hi"))
        self.assertFalse(box_rules.is_hindi("English"))
        self.assertTrue(box_rules.english_label("Commodity money"))
        self.assertFalse(box_rules.english_label("वस्तु विनिमय (Barter)"))
        self.assertFalse(box_rules.english_label("UPI"))
        self.assertFalse(box_rules.english_label("10 kg"))


def frames_of(rows, n):
    """n sampled frames (1 a second), each with the given texts: rows = [(text, px, box, plan, first, last)]."""
    out = []
    for k in range(n):
        texts = [{"t": t, "px": px, "box": list(box), "boxes": [list(box)], **({"plan": True} if plan else {})}
                 for t, px, box, plan, first, last in rows if first <= k <= last]
        out.append({"frame": k * 30, "texts": texts})
    return out


class AuditGate(unittest.TestCase):
    """Navin: "2 s se lamba overlap ya 36 px se chhota plan-text mile to run fail, Navin ko nahi dikhana"."""

    def record(self, rows, n=8):
        from bie.brain.video import text_audit as ta
        return ta.summarize(frames_of(rows, n), every=30)

    def test_an_overlap_of_two_seconds_passes_and_three_fails(self):
        from bie.brain.video import text_audit as ta
        two = self.record([("गेहूँ", 48, (100, 100, 200, 60), True, 0, 7), ("कपड़ा", 48, (120, 110, 200, 60), True, 2, 3)])
        self.assertEqual((two["overlap_seconds"], two["longest_overlap_s"]), (2.0, 2.0))
        self.assertTrue(ta.gate(two)["passed"], ta.gate(two))
        three = self.record([("गेहूँ", 48, (100, 100, 200, 60), True, 0, 7), ("कपड़ा", 48, (120, 110, 200, 60), True, 2, 4)])
        g = ta.gate(three)
        self.assertFalse(g["passed"])
        self.assertEqual(g["long_overlaps"], 1)
        self.assertTrue(any("cover each other for 3 s" in p for p in g["problems"]), g)

    def test_a_small_plan_text_fails_and_a_small_saancha_word_is_the_compilers(self):
        from bie.brain.video import text_audit as ta
        rec = self.record([("नमक", 20, (700, 700, 60, 24), False, 0, 7), ("पैसा", 56, (100, 100, 200, 70), True, 0, 7)])
        self.assertTrue(ta.gate(rec)["passed"])                      # the saancha's word: the compiler's floor rule
        self.assertFalse(ta.gate(rec, plan_marks=False)["passed"])   # an unmarked (older) page: every small text counts
        small = self.record([("पैसा", 30, (100, 100, 120, 40), True, 0, 7)])
        g = ta.gate(small)
        self.assertFalse(g["passed"])
        self.assertTrue(any("'पैसा' is 30" in p for p in g["problems"]), g)

    def test_the_render_workflow_shows_nothing_that_fails_the_gate(self):
        render = (ROOT / ".github" / "workflows" / "task046c-render.yml").read_text(encoding="utf-8")
        self.assertIn("The text-audit gate", render)
        self.assertIn('if [ "$GATE" = "true" ]; then', render)
        self.assertIn('cp "$RUNNER_TEMP/out/gate.json" "$dest/GATE_FAILED.json"', render)
        self.assertIn("if: steps.gate.outputs.passed != 'true'", render)
        one = (ROOT / ".github" / "workflows" / "p1-one-button.yml").read_text(encoding="utf-8")
        self.assertIn("GATE_FAILED.json", one)
        self.assertIn("failed the text-audit gate (no review page)", one)
        engine = (ROOT / "bie" / "brain" / "video" / "engine" / "engine.mjs").read_text(encoding="utf-8")
        self.assertEqual(engine.count('class="bie-plan"'), 2)         # the plan's texts and the kicker
        audit = (ROOT / "bie" / "brain" / "video" / "preview" / "audit.mjs").read_text(encoding="utf-8")
        self.assertIn('el.closest(".bie-plan")', audit)


if __name__ == "__main__":
    unittest.main()
