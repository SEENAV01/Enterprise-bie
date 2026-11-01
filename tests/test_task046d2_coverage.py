"""Task 046 Part D2 addendum, point 4 (Navin, 2 November 2026): "jis cheej ka jikar hai wohi cheej dikhe".

Every thing the visual-idea step (the dikhane ki list) names for a beat must be on screen in that beat; the run reports the
mentioned-things coverage (%) per video. The check works for any thing (a bicycle, a test tube, a book), not one chapter's.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from bie.brain import canvas_director as cd
from bie.brain import visual_thinking as vt
from bie.toolbox import icons

BEATS = [{"beat_id": "b1", "say": "राम के पास एक साइकिल है।"}, {"beat_id": "b2", "say": "लैब में एक टेस्ट ट्यूब रखी है।"},
         {"beat_id": "b3", "say": "मेज़ पर एक किताब है।"}]
FOUND = {"bicycle": ["tw:1f6b2"], "test tube": ["tw:1f9ea"], "book": ["fl:closed-book"]}


def ideas(*rows):
    return {"beats": [{"beat_id": b, "things": list(t)} for b, t in rows]}


def canvas_plan(*nodes):
    return {"id": "x", "grid": [12, 8], "beats": copy.deepcopy(BEATS), "nodes": [dict(n) for n in nodes]}


def icon(nid, ref, cue, until=None, cell=(0, 0, 2, 2)):
    n = {"id": nid, "kind": "icon", "icon": ref, "cell": list(cell), "cue": cue}
    if until:
        n["until_cue"] = until
    return n


class Rows(unittest.TestCase):
    def test_a_thing_is_shown_only_while_its_picture_is_on_screen_in_its_beat(self):
        plan = canvas_plan(icon("n1", "tw:1f6b2", ["b1", ""], until=["b2", ""]), icon("n2", "tw:1f9ea", ["b3", ""]))
        rows = vt.coverage_rows(plan, "B", ideas(("b1", ["bicycle"]), ("b2", ["test tube", "bicycle"])), found=FOUND)
        got = {(r["beat_id"], r["thing"]): (r["shown"], r["by"]) for r in rows}
        self.assertEqual(got[("b1", "bicycle")], (True, ["n1"]))
        self.assertEqual(got[("b2", "bicycle")], (True, ["n1"]))           # until the start of b2 counts for b2 too (it is there)
        self.assertEqual(got[("b2", "test tube")], (False, []))            # the tube comes only in b3
        summary = vt.coverage_summary(rows)
        self.assertEqual((summary["mentioned"], summary["shown"], summary["coverage_pct"]), (3, 2, 66.7))
        self.assertEqual(summary["not_shown"], [{"beat_id": "b2", "thing": "test tube", "has_picture": True}])

    def test_the_refusal_names_the_thing_and_a_picture_of_it_never_a_near_word(self):
        plan = canvas_plan(icon("n1", "tw:1f6b2", ["b1", ""]))
        rows = vt.coverage_rows(plan, "B", ideas(("b3", ["book"]), ("b2", ["payment claim"])), found={"book": ["fl:closed-book"]})
        problems = vt.coverage_problems(rows)
        self.assertEqual(len(problems), 1)
        self.assertIn("'book'", problems[0])
        self.assertIn("fl:closed-book", problems[0])
        claim = next(r for r in rows if r["thing"] == "payment claim")
        self.assertEqual((claim["shown"], claim["has_picture"]), (False, False))   # a baggage claim is not a payment claim: a need

    def test_a_mark_a_number_and_a_label_are_shown_by_marks_and_words(self):
        plan = canvas_plan({"id": "m", "kind": "mark", "mark": "tick", "target": "n1", "cue": ["b1", ""]},
                           {"id": "t", "kind": "text", "text": "₹1,500", "cell": [4, 0, 3, 1], "cue": ["b2", ""]})
        rows = vt.coverage_rows(plan, "B", ideas(("b1", ["check mark"]), ("b2", ["₹1500 label", "cross"])), found={})
        got = {r["thing"]: r["shown"] for r in rows}
        self.assertEqual(got, {"check mark": True, "₹1500 label": True, "cross": False})

    def test_in_a_world_the_place_its_keeper_and_the_crowd_show_their_things_for_the_whole_part(self):
        plan = {"id": "w", "beats": copy.deepcopy(BEATS),
                "elements": [{"id": "shop", "kind": "shop", "x": 2600}, {"id": "keeper", "kind": "shopkeeper", "x": 2600},
                             {"id": "crowd", "kind": "crowd", "steps": [{"n": 3, "cue": ["b2", ""]}]},
                             {"id": "act", "kind": "action", "actors": [{"role": "giver", "who": "Ravi", "label": "मज़दूर"}],
                              "objects": [{"name": "bicycle", "icon": "tw:1f6b2"}], "parts": [{"part": "hold", "cue": ["b3", ""]}]}]}
        rows = vt.coverage_rows(plan, "C", ideas(("b1", ["दुकान", "दुकानदार", "लोग"]), ("b2", ["buyers"]), ("b3", ["मज़दूर", "bicycle"])),
                                found=FOUND)
        got = {(r["beat_id"], r["thing"]): r["shown"] for r in rows}
        self.assertEqual(got, {("b1", "दुकान"): True, ("b1", "दुकानदार"): True, ("b1", "लोग"): False,    # the crowd comes in b2
                               ("b2", "buyers"): True, ("b3", "मज़दूर"): True, ("b3", "bicycle"): True})


class CodeShowsWhatItCan(unittest.TestCase):
    def test_code_puts_a_missing_bicycle_test_tube_and_book_on_the_canvas_in_their_own_beats(self):
        plan = canvas_plan()
        idea = ideas(("b1", ["bicycle"]), ("b2", ["test tube"]), ("b3", ["book"]))
        fixes = vt.show_missing_things(plan, "B", idea, found=FOUND)
        self.assertEqual(len(fixes), 3)
        added = {n["cue"][0]: n for n in plan["nodes"]}
        self.assertEqual({b: n["icon"] for b, n in added.items()}, {"b1": "tw:1f6b2", "b2": "tw:1f9ea", "b3": "fl:closed-book"})
        self.assertEqual(added["b1"]["until_cue"], ["b2", ""])                 # it leaves when the next beat starts
        self.assertNotIn("until_cue", added["b3"])                             # the last beat: it stays to the end
        self.assertTrue(all(r["shown"] for r in vt.coverage_rows(plan, "B", idea, found=FOUND)))
        self.assertEqual(vt.show_missing_things(plan, "B", idea, found=FOUND), [])      # nothing left to do

    def test_only_given_things_are_drawn_never_a_near_word_and_never_in_a_world(self):
        plan = canvas_plan()
        self.assertEqual(vt.show_missing_things(plan, "B", ideas(("b1", ["payment claim", "net banking screen"])), found={}), [])
        self.assertEqual(plan["nodes"], [])
        world = {"id": "w", "beats": copy.deepcopy(BEATS), "elements": []}
        self.assertEqual(vt.show_missing_things(world, "C", ideas(("b1", ["bicycle"])), found=FOUND), [])

    def test_at_most_four_per_part_and_a_smaller_cell_when_the_grid_is_full(self):
        plan = canvas_plan()
        many = ideas(("b1", ["bicycle", "test tube", "book", "cow", "teacup", "scissors"]))
        self.assertEqual(len(vt.show_missing_things(plan, "B", many, found=FOUND)), vt.AUTO_THINGS_MAX)
        full = canvas_plan(*[icon(f"r{r}", "tw:1f6b2", ["b1", ""], cell=(0, r, 12, 1)) for r in range(8) if r != 3],
                           icon("half", "tw:1f6b2", ["b1", ""], cell=(2, 3, 10, 1)))
        vt.show_missing_things(full, "B", ideas(("b2", ["book"])), found=FOUND)
        self.assertEqual(full["nodes"][-1]["cell"], [0, 3, 2, 1])               # no 2 x 2 is free: a 2 x 1 cell
        self.assertEqual(vt._free_cell([[0, 0, 12, 8]], 12, 8), None)

    def test_code_never_puts_a_thing_under_the_subtitle_strip(self):
        # replay of run c: 9 parts had a thing code placed in the bottom rows, which the camera showed under the captions
        plan = canvas_plan(icon("top", "tw:1f6b2", ["b1", ""], cell=(0, 0, 12, 6)))
        fixes = vt.show_missing_things(plan, "B", ideas(("b2", ["book"])), found=FOUND)
        added = {n["id"] for n in plan["nodes"] if n["id"].startswith("auto_thing")}
        self.assertEqual(vt._under_the_strip(plan, added), set())
        self.assertEqual(len(fixes), len(added))

    def test_a_question_mark_code_shows_itself_a_tick_or_a_cross_only_the_maker_places(self):
        # replay of run c: a "?" text is refused by CV-13 (only symbols), so the question mark is the icon that fits the words
        plan = canvas_plan()
        fixes = vt.show_missing_things(plan, "B", ideas(("b1", ["question mark", "check mark", "cross"])), found={})
        self.assertEqual([(n["kind"], n.get("icon")) for n in plan["nodes"]], [("icon", icons.fitting("question mark")[0]["id"])])
        self.assertEqual(len(fixes), 1)
        rows = vt.coverage_rows(plan, "B", ideas(("b2", ["unequal grain measures", "equal signs"])), found={})
        self.assertEqual([r.get("mark") for r in rows], [None, "equal"])           # "unequal" is not an equal sign


class TheCheck(unittest.TestCase):
    def test_the_check_refuses_a_world_that_leaves_out_a_thing_bie_has_a_picture_of(self):
        world = {"id": "w", "beats": copy.deepcopy(BEATS), "elements": [{"id": "shop", "kind": "shop", "x": 2600}]}
        problems = cd._coverage(world, "C", ideas(("b1", ["bicycle", "दुकान"])), {"found": FOUND, "images": {}})
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("beat b1: 'bicycle'"))
        self.assertEqual(cd._coverage(world, "C", None, None), [])                # no dikhane ki list, nothing to hold it to

    def test_the_run_reports_coverage_per_part_and_per_video(self):
        import test_task046_canvas_director as T
        chapter, lesson = T.econ_lesson()
        tmp = Path(tempfile.mkdtemp())
        summary = cd.run_canvas(chapter, lesson, T.ECON, T.runner(tmp), tmp, workers=1)
        video = summary["videos"][0]
        self.assertTrue(all("coverage_pct" in p for p in video["parts"] if p["status"] == "passed"))
        rep = video["report"]
        self.assertGreater(rep["mentioned_things"], 0)
        self.assertEqual(rep["coverage_pct"], round(100.0 * rep["shown_things"] / rep["mentioned_things"], 1))
        self.assertTrue(all({"beat_id", "thing", "has_picture", "part"} <= set(t) for t in rep["things_not_shown"]))
        written = json.loads((tmp / "canvas.json").read_text(encoding="utf-8"))
        self.assertEqual(written["videos"][0]["report"]["coverage_pct"], rep["coverage_pct"])
        q = summary["quality"]
        self.assertEqual((q["mentioned_things"], q["shown_things"]), (rep["mentioned_things"], rep["shown_things"]))
        self.assertIn("Mentioned things on screen", (tmp / "CANVAS.md").read_text(encoding="utf-8"))


class Fits(unittest.TestCase):
    def test_an_icon_fits_when_it_is_a_picture_of_the_thing(self):
        by = icons.by_id()
        self.assertTrue(icons.fits("bicycle", by["tw:1f6b2"]))
        self.assertTrue(icons.fits("test tubes", by["tw:1f9ea"]))              # a plural finds the thing
        self.assertFalse(icons.fits("payment claim", by["tw:1f6c4"]))          # baggage claim
        self.assertEqual(icons.fitting("net banking screen"), [])
        self.assertEqual([r["id"] for r in icons.fitting("दुकान")][:1], ["tw:1f3ea"])     # a Hindi word through its alias


if __name__ == "__main__":
    unittest.main()
