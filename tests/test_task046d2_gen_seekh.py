"""Seekh -> BIE from the addendum proof's run a (Task 046 Part D2, 2 November 2026): 18 of 61 parts refused after three
rounds, most on things code can read itself.

- a composed process's fields code can settle: a style the part has no use for, a meter's own styles (bar, number, refused
  before as show_text styles), a place word for a spot ("up", "offstage"), a count out of range, a missing only actor or
  object, a move without a target, a meter without its value;
- a canvas node the camera shows under the subtitle strip goes up while the cells above are free;
- a thing named by a text or mark head noun ("₹ symbol", "₹100 amount") is shown by the words on screen, never asked for as a
  picture (run a asked for an anger symbol icon).
"""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import canvas, visual_thinking as vt  # noqa: E402
from bie.brain.video import saanche  # noqa: E402

SAYS = {"b1": "राम ने साइकिल ₹500 में बेची और पैसे ऊपर रख दिए।", "b2": "फिर उसने ₹200 की घंटी खरीदी।"}


def composed(*parts, objects=(("bicycle", "tw:1f6b2"),), actors=("seller",)):
    return {"id": "a1", "kind": "action", "template": "compose",
            "actors": [{"role": r, "who": "main" if i == 0 else "other"} for i, r in enumerate(actors)],
            "objects": [{"name": n, "icon": i, "label": ""} for n, i in objects],
            "amounts": [{"name": "price", "text": "₹500"}], "steps": [], "parts": [dict(p) for p in parts]}


class ComposedParts(unittest.TestCase):
    def test_code_settles_what_run_a_refused_three_times(self):
        action = composed({"part": "show_text", "cue": ["b1", "बेची"], "on": "bicycle", "text": "₹500", "style": "particles"},
                          {"part": "move", "cue": ["b1", "ऊपर"], "object": "bicycle", "to": "up"},
                          {"part": "move", "cue": ["b1", "रख"], "to": "offstage"},
                          {"part": "meter", "cue": ["b2", "खरीदी"], "style": "red_limit"},
                          {"part": "appear", "cue": ["b2", "घंटी"], "object": "bicycle", "style": "grid", "n": 40},
                          {"part": "hold", "cue": ["b2", "फिर"]})
        self.assertNotEqual(saanche.problems_of(copy.deepcopy(action), SAYS), [])        # refused as the maker sent it
        fixes = saanche.complete_action(action, SAYS)
        self.assertEqual(saanche.problems_of(action, SAYS), [])
        parts = action["parts"]
        self.assertEqual(parts[0]["style"], "tag")
        self.assertEqual((parts[1]["to"], parts[2]["to"], parts[2]["object"]), ("far", "far", "bicycle"))
        self.assertEqual((parts[3].get("style"), parts[3]["to"]), (None, "{price}"))
        self.assertEqual((parts[4].get("style"), parts[4]["layout"], parts[4]["n"]), (None, "grid", saanche.COUNT_MAX))
        self.assertEqual((parts[5]["actor"], parts[5]["object"]), ("seller", "bicycle"))
        self.assertGreaterEqual(len(fixes), 8)

    def test_a_meter_keeps_its_own_style_and_a_word_no_spot_means_is_still_refused(self):
        ok = composed({"part": "meter", "cue": ["b1", "बेची"], "to": "{price}", "style": "number"})
        self.assertEqual(saanche.problems_of(ok, SAYS), [])                               # refused before as a show_text style
        bad = composed({"part": "move", "cue": ["b1", "ऊपर"], "object": "bicycle", "to": "the moon"})
        saanche.complete_action(bad, SAYS)
        self.assertTrue(any("not an actor, an object or a spot" in p for p in saanche.problems_of(bad, SAYS)))

    def test_two_actors_or_two_objects_are_never_guessed(self):
        action = composed({"part": "hold", "cue": ["b2", "फिर"]}, actors=("seller", "buyer"),
                          objects=(("bicycle", "tw:1f6b2"), ("bell", "tw:1f514")))
        saanche.complete_action(action, SAYS)
        self.assertTrue(any("needs actor" in p for p in saanche.problems_of(action, SAYS)))


class ComposedNamings(unittest.TestCase):
    def test_a_thing_named_as_from_a_target_named_as_spot_a_value_given_as_text_and_an_object_without_its_icon(self):
        action = composed({"part": "move", "cue": ["b1", "बेची"], "from": "bicycle", "to": "bell"},
                          {"part": "move", "cue": ["b1", "रख"], "object": "bicycle", "spot": "offstage"},
                          {"part": "meter", "cue": ["b2", "खरीदी"], "on": "bell", "text": "₹200"},
                          {"part": "compare", "cue": ["b2", "घंटी"], "left_text": "₹500", "right_text": "₹200"},
                          objects=(("bicycle", "tw:1f6b2"), ("bell", "")))
        action["objects"] = action["objects"][:1] + [{"name": "bell", "icon": "", "label": ""}]
        saanche.complete_action(action, SAYS)
        parts, icons_of = action["parts"], {o["name"]: o["icon"] for o in action["objects"]}
        self.assertTrue(icons_of["bell"])                                                # a picture OF a bell
        self.assertEqual((parts[0]["object"], parts[0].get("from")), ("bicycle", None))
        self.assertEqual(parts[1]["to"], "far")
        self.assertEqual(parts[2]["to"], "₹200")
        self.assertEqual((parts[3]["left"], parts[3]["right"]), ("bicycle", "bell"))
        self.assertEqual(saanche.problems_of(action, SAYS), [])


class SubtitleStrip(unittest.TestCase):
    def test_run_a_v2_s3_two_zooms_together_no_longer_push_the_action_under_the_captions(self):
        # the maker's scene camera framed the action while the block camera zoomed in too: each kept it above the strip,
        # together they did not (run a, part v2_s3, refused three times). One camera zooms at a time now.
        plan = json.loads((ROOT / "tests" / "fixtures" / "task046d2" / "run_a_v2_s3.plan.json").read_text(encoding="utf-8"))
        scene, _ = canvas.compile_plan(copy.deepcopy(plan))
        self.assertEqual(canvas.subtitle_problems(scene), [])
        inner, outer = scene["layers"][0]["data"]["cam"], scene["camera"]
        for k in inner:
            if float(k["box"]["w"]) < 1:
                nxt = min([j["at"] for j in inner if j["at"] > k["at"]] or [10 ** 9])
                self.assertFalse(canvas._zoomed_during(outer, k["at"], nxt), k)

    def test_one_camera_at_a_time_and_no_close_up_inside_a_scene_zoom(self):
        scene_keys = [{"at": 0, "box": {"x": 0, "y": 0, "w": 0.97, "h": 0.97}}, {"at": 100, "box": {"x": 0.1, "y": 0.2, "w": 0.6, "h": 0.6}},
                      {"at": 200, "box": {"x": 0, "y": 0, "w": 0.97, "h": 0.97}}]
        inner = [{"at": 0, "box": {"x": 0, "y": 0, "w": 0.8, "h": 0.8}}, {"at": 120, "box": {"x": 0.1, "y": 0.1, "w": 0.7, "h": 0.7}},
                 {"at": 250, "box": {"x": 0.1, "y": 0.1, "w": 0.7, "h": 0.7}}]
        calm = canvas.one_camera_at_a_time(inner, scene_keys)
        self.assertEqual([k["box"]["w"] for k in calm], [1.0, 1.0, 0.7])            # zoomed only where the scene camera is wide
        el = {"id": "act", "x": 0.1, "y": 0.2, "w": 0.4, "h": 0.4, "until": 300, "close_up": {"at": 130, "until": 180}}
        self.assertFalse(any(k.get("close_up") for k in canvas.action_close_ups([], [el], scene_keys)))
        self.assertTrue(any(k.get("close_up") for k in canvas.action_close_ups([], [el], None)))

    def test_a_node_under_the_strip_goes_up_only_into_free_cells(self):
        beats = [{"beat_id": "b1", "say": "राम के पास एक साइकिल है।"}]
        nodes = [{"id": f"r{r}", "kind": "icon", "icon": "tw:1f6b2", "cell": [0, r, 12, 1], "cue": ["b1", ""]} for r in range(8)]
        plan = {"id": "x", "grid": [12, 8], "beats": beats, "nodes": nodes}
        cells = [list(n["cell"]) for n in nodes]
        vt.lift_from_strip(plan)
        self.assertEqual([n["cell"] for n in plan["nodes"]][:7], cells[:7])                # the rows above were all taken


class TextThings(unittest.TestCase):
    def test_a_sign_or_an_amount_is_shown_by_words_never_asked_for_as_a_picture(self):
        beats = [{"beat_id": "b1", "say": "₹ का निशान 2010 में आया और ₹100 का नोट।"}]
        plan = {"id": "x", "grid": [12, 8], "beats": beats,
                "nodes": [{"id": "t", "kind": "text", "text": "₹100", "cell": [0, 0, 3, 1], "cue": ["b1", ""]}]}
        ideas = {"beats": [{"beat_id": "b1", "things": ["₹ symbol", "₹100 amount", "2010 timeline marker"]}]}
        rows = {r["thing"]: r for r in vt.coverage_rows(plan, "B", ideas, found={})}
        self.assertEqual((rows["₹ symbol"]["shown"], rows["₹100 amount"]["shown"]), (True, True))
        self.assertFalse(rows["2010 timeline marker"]["shown"])
        self.assertTrue(all(not r["has_picture"] for r in rows.values() if not r["shown"]))
        self.assertEqual(vt.coverage_problems(list(rows.values())), [])                  # nothing asked for as a picture
        self.assertTrue(vt.is_text_thing("₹ symbol") and not vt.is_text_thing("bicycle"))


if __name__ == "__main__":
    unittest.main()
