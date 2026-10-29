"""Task 046 Part C · the economy kit inside BIE: the build-up canvas compiler (``bie/brain/canvas.py``), the world compiler
(``bie/brain/video/world.py``), the cue-word fix in ``timing.py`` (a word just before a danda or comma is found), one
caption place (the core strip; no block draws its own subtitles), the icon index with its two CC BY 4.0 sets
(``bie/toolbox/icons.py``) and the registry entries, proof demos and blocks that carry them.

Offline, standard library, no network, no keys, no money. The fixtures in tests/fixtures/task046c/ are the kit's own
hand-written test plans (test inputs, not lesson content); the lesson plans come from the director.
"""
from __future__ import annotations

import copy
import dataclasses
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import canvas, director, shots  # noqa: E402
from bie.brain.assets import AssetLibrary  # noqa: E402
from bie.brain.video import render, timing, world  # noqa: E402
from bie.toolbox import demos, icons, licence, registry  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "task046c"
BLOCKS = ROOT / "bie" / "brain" / "video" / "blocks"


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


BASE = {
    "id": "t", "grid": [12, 8],
    "beats": [{"beat_id": "b1", "say": "दुकान पर दाम पचास रुपये है।"}, {"beat_id": "b2", "say": "फिर दाम पैंसठ हो जाता है, यही CPI।"}],
    "nodes": [
        {"id": "shop", "kind": "icon", "icon": "tw:1f3ea", "cell": [0, 2, 3, 3], "cue": ["b1", "दुकान"]},
        {"id": "p", "kind": "value", "cell": [4, 3, 3, 1], "steps": [{"text": "₹50", "cue": ["b1", "पचास"]},
                                                                  {"text": "₹65", "dir": "up", "cue": ["b2", "पैंसठ"]}]},
        {"id": "a", "kind": "arrow", "from": "shop", "to": "p", "cue": ["b1", "दाम"]},
    ],
}
SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path fill="currentColor" d="M0 0h10v10z"/></svg>'
TW_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36"><path fill="#DD2E44" d="M0 0h36v36z"/></svg>'


def elements(scene: dict) -> list:
    return scene["layers"][0]["data"]["elements"]


def element(scene: dict, el_id: str) -> dict:
    return next(e for e in elements(scene) if e["id"] == el_id)


class Timing(unittest.TestCase):
    """The danda bug: ``_norm`` stripped every non-word character into nothing, so "CPI।" never matched "CPI"."""

    def test_a_cue_word_before_a_danda_or_comma_is_found(self):
        self.assertTrue(timing.has_word("फिर दाम पैंसठ हो जाता है, यही CPI।", "CPI"))
        self.assertTrue(timing.has_word("फिर दाम पैंसठ हो जाता है, यही CPI।", "है"))
        self.assertTrue(timing.has_word("माँग ने दाम को ऊपर खींच लिया।", "खींच"))
        self.assertFalse(timing.has_word("फिर दाम पैंसठ हो जाता है।", "पचास"))
        self.assertGreater(timing.word_fraction("फिर दाम पैंसठ हो जाता है, यही CPI।", "CPI"), 0.7)

    def test_the_director_reads_words_through_the_same_code(self):
        self.assertTrue(director.word_in("CPI", "यही CPI।"))
        self.assertFalse(director.word_in("CPI", "यही CPIX।"))


class Canvas(unittest.TestCase):
    def test_every_fixture_compiles_without_problems_and_carries_captions(self):
        for name in ("demand_pull_touches.plan.json", "phillips.plan.json", "price_chain.plan.json", "real_gdp.plan.json"):
            plan = fixture(name)
            scene, report = canvas.compile_plan(copy.deepcopy(plan))
            self.assertEqual(report["problems"], [], name)
            self.assertGreater(scene["duration"], 300, name)
            self.assertLessEqual(report["longest_still_s"], canvas.MAX_STILL_S, name)
            self.assertEqual(len(scene["captions"]), len(plan["beats"]), name)
            self.assertNotIn("subtitles", scene["layers"][0]["data"], name)
            self.assertIn(scene["layers"][0]["block"], ("canvas_build", "curve_story"), name)
            self.assertEqual(report["mode"], "B" if plan.get("touches") else "A", name)
            self.assertEqual(report["level"], "L2 + touches" if plan.get("touches") else "L2", name)

    def test_a_scene_camera_box_never_shows_the_backdrop(self):
        """The Money chapter's v1 (28 October 2026): a plan camera on cells gave the scene a 0.90 x 0.68 box; the core camera
        fits a box by its larger side, so a band of backdrop ran along the top of the canvas for 30 s. The box grows to a
        square in frame fractions around its centre and stays inside the frame."""
        box = canvas.fit_box({"x": 0.051, "y": 0.07, "w": 0.898, "h": 0.68})
        self.assertEqual((box["w"], box["h"]), (0.898, 0.898))
        self.assertEqual(box["y"], 0.0)                                           # clamped to the top edge
        self.assertAlmostEqual(box["x"], 0.051, places=3)
        self.assertEqual(canvas.fit_box({"x": 0, "y": 0, "w": 1, "h": 1}), {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0})
        small = canvas.fit_box({"x": 0.6, "y": 0.5, "w": 0.3, "h": 0.4})
        self.assertEqual((small["w"], small["h"]), (0.4, 0.4))
        self.assertAlmostEqual(small["x"] + small["w"] / 2, 0.75, places=3)       # the centre stays
        self.assertLessEqual(small["x"] + small["w"], 1.0)
        plan = fixture("demand_pull_touches.plan.json")
        plan = dict(plan, camera=[{"cells": [0, 0, 12, 8], "cue": [plan["beats"][0]["beat_id"], ""]},
                                  {"cells": [1, 1, 10, 6], "cue": [plan["beats"][1]["beat_id"], ""]}])
        scene, _ = canvas.compile_plan(copy.deepcopy(plan))
        for key in scene["camera"]:
            b = key["box"]
            self.assertAlmostEqual(b["w"], b["h"], places=4)
            self.assertGreaterEqual(min(b["x"], b["y"]), 0.0)
            self.assertLessEqual(max(b["x"] + b["w"], b["y"] + b["h"]), 1.0001)

    def test_touches_plan_gets_a_camera_and_flowing_goods(self):
        scene, report = canvas.compile_plan(fixture("demand_pull_touches.plan.json"))
        data = scene["layers"][0]["data"]
        self.assertTrue(data["touches"])
        self.assertEqual(data["cam"][-1]["box"], {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0})
        self.assertEqual(len([e for e in data["elements"] if e.get("flow")]), 2)
        self.assertEqual((report["mode"], report["level"]), ("B", "L2 + touches"))

    def test_cue_on_the_last_word_before_the_danda_lands_late_in_its_beat(self):
        plan = copy.deepcopy(BASE)
        plan["nodes"].append({"id": "t", "kind": "text", "text": "CPI", "cell": [8, 0, 3, 1], "cue": ["b2", "CPI"]})
        scene, _ = canvas.compile_plan(plan)
        self.assertGreater(element(scene, "t")["at"], element(scene, "p")["steps"][1]["at"])

    def test_unknown_cue_word_is_refused(self):
        plan = copy.deepcopy(BASE)
        plan["nodes"][0]["cue"] = ["b1", "बाज़ार"]
        with self.assertRaises(canvas.PlanError):
            canvas.compile_plan(plan)

    def test_shared_cells_on_screen_together_are_refused_but_one_after_another_pass(self):
        plan = copy.deepcopy(BASE)
        plan["nodes"].append({"id": "x", "kind": "icon", "icon": "tw:1f4b0", "cell": [1, 3, 2, 2], "cue": ["b2", "दाम"]})
        with self.assertRaises(canvas.PlanError):
            canvas.compile_plan(copy.deepcopy(plan))
        plan["nodes"][0]["until_cue"] = ["b2", "", 0.0]
        plan["nodes"] = [n for n in plan["nodes"] if n["id"] != "a"]
        canvas.compile_plan(plan)

    def test_text_that_cannot_fit_and_a_wide_tag_are_refused(self):
        for style, text in (("box", "बहुत लंबा वाक्य " * 30), ("tag", "Demand-pull inflation explained")):
            plan = copy.deepcopy(BASE)
            plan["nodes"].append({"id": "t", "kind": "text", "style": style, "text": text, "cell": [8, 0, 2, 1], "cue": ["b2", "दाम"]})
            with self.assertRaises(canvas.PlanError):
                canvas.compile_plan(plan)

    def test_missing_reference_and_unknown_kind_are_refused(self):
        plan = copy.deepcopy(BASE)
        plan["nodes"][2]["to"] = "nowhere"
        with self.assertRaises(canvas.PlanError):
            canvas.compile_plan(plan)
        plan = copy.deepcopy(BASE)
        plan["nodes"].append({"id": "d", "kind": "dragon", "cell": [8, 0, 2, 1], "cue": ["b2", "दाम"]})
        with self.assertRaises(canvas.PlanError):
            canvas.compile_plan(plan)

    def test_a_long_still_picture_is_a_problem_and_a_medium_one_an_advisory(self):
        plan = copy.deepcopy(BASE)
        plan["beats"].append({"beat_id": "b3", "say": "यह एक बहुत लंबा वाक्य है जिसमें कुछ नया नहीं दिखता " * 6})
        _, report = canvas.compile_plan(plan)
        self.assertTrue(any("stays the same" in p for p in report["problems"]))
        plan = copy.deepcopy(BASE)
        plan["beats"].append({"beat_id": "b3", "say": "यह एक लंबा वाक्य है जिसमें कुछ नया नहीं दिखता, बस बात चलती रहती है।"})
        _, report = canvas.compile_plan(plan)
        self.assertEqual(report["problems"], [])
        self.assertTrue(any("stays the same" in a for a in report["advisories"]))

    def test_elements_stay_inside_the_safe_area_above_the_caption_strip(self):
        scene, _ = canvas.compile_plan(fixture("demand_pull_touches.plan.json"))
        for e in elements(scene):
            if "x" in e:
                self.assertGreaterEqual(e["x"], canvas.SAFE["left"] - 1e-9, e["id"])
                self.assertLessEqual(e["x"] + e["w"], 1 - canvas.SAFE["right"] + 1e-9, e["id"])
                self.assertLessEqual(e["y"] + e["h"], 1 - canvas.SAFE["bottom"] + 1e-9, e["id"])

    def test_captions_follow_the_beats_and_are_drawn_once_by_the_core_strip(self):
        scene, _ = canvas.compile_plan(copy.deepcopy(BASE))
        subs = scene["captions"]
        self.assertEqual([s["text"] for s in subs], [b["say"] for b in BASE["beats"]])
        self.assertEqual(subs[0]["until"], subs[1]["at"])                 # held through the short pause between beats
        self.assertLess(subs[1]["until"], scene["duration"])              # the tail after the last beat has no caption
        plan = copy.deepcopy(BASE)
        plan["beats"][0]["say"] += " " + "और " * 2
        voice = {"b1": {"duration": 1.0}, "b2": {"duration": 1.0}}
        tl = timing.build(plan["beats"], [{"scene_id": "s", "beat_ids": ["b1", "b2"]}], voice=voice)
        self.assertEqual(canvas.captions_of(tl, "s", plan["beats"])[0]["until"], tl["s"]["beats"]["b2"][0])
        far = {"b1": {"duration": 1.0}, "b2": {"duration": 1.0}}
        tl2 = timing.build(plan["beats"], [{"scene_id": "s", "beat_ids": ["b1", "b2"]}], voice=far)
        tl2["s"]["beats"]["b2"] = (tl2["s"]["beats"]["b1"][0] + 30 + 45, 30)   # a 1.5 s pause: the caption does not hold
        self.assertEqual(canvas.captions_of(tl2, "s", plan["beats"])[0]["until"], tl2["s"]["beats"]["b1"][0] + 30)
        core = (BLOCKS / "index.tsx").read_text(encoding="utf-8")
        self.assertEqual(core.count("const Captions"), 1)
        for path in (BLOCKS / "toolbox").glob("*.tsx"):
            self.assertNotIn("const Subtitles", path.read_text(encoding="utf-8"), path.name)
        self.assertTrue(canvas.video_spec([scene])["captions"])

    def test_icon_paths_reach_the_elements_and_icons_in_lists_every_icon_once(self):
        plan = fixture("demand_pull_touches.plan.json")
        ids = canvas.icons_in(plan)
        self.assertEqual(ids, ["tw:1f3ea", "tw:1f4e6", "tw:1fa99", "tw:1f9cd", "tw:1f4b0"])
        scene, _ = canvas.compile_plan(plan, icon_paths={i: f"assets/icons/{icons.safe(i)}.svg" for i in ids})
        self.assertEqual(element(scene, "shop")["src"], "assets/icons/tw-1f3ea.svg")
        self.assertEqual(element(scene, "a2")["flow"]["src"], "assets/icons/tw-1fa99.svg")

    def test_the_video_spec_and_the_credits_card(self):
        scene, _ = canvas.compile_plan(copy.deepcopy(BASE))
        credits = canvas.credits_scene(["Twemoji graphics by Twitter, Inc and other contributors, CC BY 4.0"], 5.0)
        spec = canvas.video_spec([scene, credits])
        self.assertEqual((spec["fps"], spec["width"], spec["height"], spec["schema"]), (30, 1920, 1080, canvas.SCHEMA))
        self.assertTrue(render.needs_toolbox(spec))
        self.assertEqual(credits["duration"], 150)
        self.assertEqual([e["text"] for e in elements(credits)][1], "Twemoji graphics by Twitter, Inc and other contributors, CC BY 4.0")
        self.assertEqual(credits["captions"], [])

    def test_stubs_group_beats_exactly_as_the_shot_list_director_does(self):
        video = {"video_id": "v2", "beats": [
            {"beat_id": "h1", "say": "hook", "part_id": ""},
            {"beat_id": "b1", "say": "one", "part_id": "p1", "covers_item_ids": ["i2"], "on_screen": "a shop"},
            {"beat_id": "b2", "say": "two", "part_id": "p1", "covers_item_ids": ["i1"]},
            {"beat_id": "b3", "say": "three", "part_id": "p2"},
            {"beat_id": "c1", "say": "close", "part_id": ""}]}
        stubs = canvas.stubs(video)
        self.assertEqual([s["id"] for s in stubs], ["v2_" + sc["scene_id"] for sc in shots.scenes_of(video["beats"])])
        self.assertEqual([[b["beat_id"] for b in s["beats"]] for s in stubs], [["h1", "b1", "b2"], ["b3", "c1"]])
        self.assertEqual(stubs[0]["part_id"], "p1")
        self.assertEqual(stubs[0]["covers_item_ids"], ["i1", "i2"])
        self.assertEqual(stubs[0]["on_screen_hints"], ["a shop"])
        self.assertTrue(all(s["touches"] and s["nodes"] == [] for s in stubs))

    def test_trim_keeps_only_the_pieces_cued_inside_the_first_beats(self):
        plan = canvas.trim_plan(fixture("demand_pull_touches.plan.json"), 2)
        self.assertEqual([b["beat_id"] for b in plan["beats"]], ["b1", "b2"])
        ids = {n["id"] for n in plan["nodes"]}
        self.assertEqual(ids, {"tag", "shop", "goods", "a1", "price", "plabel", "a2", "buyers", "dlabel"})
        self.assertEqual(len(next(n for n in plan["nodes"] if n["id"] == "price")["steps"]), 1)
        self.assertEqual(len(next(n for n in plan["nodes"] if n["id"] == "buyers")["steps"]), 1)
        self.assertTrue(plan["touches"])
        graph = canvas.trim_plan(fixture("phillips.plan.json"), 2)["graph"]
        self.assertEqual([d["id"] for d in graph["dots"]], ["d"])
        self.assertEqual(len(graph["dots"][0]["steps"]), 1)
        self.assertEqual(graph["shades"], [])
        self.assertEqual(len(graph["notes"]), 1)
        gdp = canvas.trim_plan(fixture("real_gdp.plan.json"), 3)
        self.assertNotIn("x", {n["id"] for n in gdp["nodes"]})          # its target tr_0 still exists, but its cue is in b5
        self.assertEqual(len(next(n for n in gdp["nodes"] if n["id"] == "tab")["rows"]), 1)
        w = canvas.trim_plan(fixture("demand_pull_world.world.json"), 2)
        self.assertEqual(len(w["camera"]), 4)
        self.assertNotIn("lift", next(e for e in w["elements"] if e["kind"] == "price_tag"))
        self.assertNotIn("carry", next(e for e in w["elements"] if e["kind"] == "crowd"))

    def test_squeeze_fits_the_beats_into_the_clip(self):
        beats = fixture("price_chain.plan.json")["beats"][:3]
        voice = canvas.squeeze(beats, 4.8)
        tl = timing.build(beats, [{"scene_id": "s", "beat_ids": [b["beat_id"] for b in beats]}], voice=voice)
        self.assertAlmostEqual(tl["s"]["duration"] / timing.FPS, 4.8, delta=0.05)


class World(unittest.TestCase):
    def test_the_world_fixture_compiles_as_level_c(self):
        plan = fixture("demand_pull_world.world.json")
        scene, report = world.compile_world(copy.deepcopy(plan))
        self.assertEqual(report["problems"], [])
        self.assertEqual((report["mode"], report["level"]), ("C", "L3"))
        data = scene["layers"][0]["data"]
        self.assertEqual(scene["layers"][0]["block"], "world_scene")
        self.assertTrue(all("at" in k for k in data["camera"]))
        crowd = next(e for e in data["elements"] if e["kind"] == "crowd")
        self.assertEqual([s["n"] for s in crowd["steps"]], [2, 12, 3])
        self.assertEqual(len(scene["captions"]), len(plan["beats"]))
        self.assertNotIn("subtitles", data)

    def test_bad_world_plans_are_refused(self):
        plan = fixture("demand_pull_world.world.json")
        bad = copy.deepcopy(plan)
        bad["elements"].append({"id": "x", "kind": "dragon", "cue": ["b1", "दुकान"]})
        with self.assertRaises(canvas.PlanError):
            world.compile_world(bad)
        bad = copy.deepcopy(plan)
        bad["camera"][1], bad["camera"][2] = bad["camera"][2], bad["camera"][1]
        with self.assertRaises(canvas.PlanError):
            world.compile_world(bad)
        bad = copy.deepcopy(plan)
        bad["elements"] = [e for e in bad["elements"] if e["kind"] != "shop"]
        with self.assertRaises(canvas.PlanError):
            world.compile_world(bad)
        bad = copy.deepcopy(plan)
        next(e for e in bad["elements"] if e["kind"] == "crowd")["steps"][0]["n"] = 2.5
        with self.assertRaises(canvas.PlanError):
            world.compile_world(bad)

    def test_a_story_part_finds_its_kit_by_the_place_words(self):
        self.assertEqual(world.kit_for("मान लीजिए एक दुकान पर चीनी के तीन पैकेट हैं"), "shop")
        self.assertEqual(world.kit_for("The shopkeeper raises the price"), "shop")
        self.assertEqual(world.kit_for("GDP दो तरह से नापी जाती है"), "")
        # PR 3 (the Money chapter's v1): a tea stall, a market stall and the English "bazaar" are shops; a bank story has its kit
        self.assertEqual(world.kit_for("Tea stall; illustrative outside example"), "shop")
        self.assertEqual(world.kit_for("चायवाले ने दो दस के सिक्के लिए"), "shop")
        self.assertEqual(world.kit_for("Hypothetical village bazaar"), "shop")
        self.assertEqual(world.kit_for("Bank account; illustrative outside amounts"), "bank")
        self.assertEqual(world.kit_for("खाते में पाँच सौ रुपये जमा किए, पासबुक में balance बढ़ा"), "bank")
        self.assertEqual(world.kit_for("A factory and its workers"), "")               # a place without a kit yet
        self.assertEqual(world.place_of("A factory and its workers"), "factory")

    def test_the_bank_fixture_compiles_as_a_level_c_world_with_the_bank_kit(self):
        plan = fixture("store_of_value_world.world.json")
        scene, report = world.compile_world(copy.deepcopy(plan))
        self.assertEqual(report["problems"], [])
        self.assertEqual((report["mode"], report["level"], report["kit"]), ("C", "L3", "bank"))
        data = scene["layers"][0]["data"]
        kinds = [e["kind"] for e in data["elements"]]
        self.assertIn("bank", kinds)
        self.assertIn("teller", kinds)
        board = next(e for e in data["elements"] if e["kind"] == "board")
        self.assertEqual([s["text"] for s in board["steps"]], ["₹0", "₹500", "₹0"])
        self.assertTrue(all("at" in s for s in board["steps"]))
        self.assertEqual(board["steps"][1]["dir"], "up")
        self.assertLess(report["longest_still_s"], 15)
        self.assertEqual(len(scene["captions"]), len(plan["beats"]))

    def test_a_board_holds_three_wrapped_lines_and_a_price_tag_a_price(self):
        """The Money chapter's v1 (28 October 2026): the director wrote sentences into boards (63 of 98 values over 16
        characters) and they ran out of the box. Code wraps a long line at spaces, keeps the maker's own line breaks and
        refuses more than three lines; a price tag shows a price; the title stays short."""
        self.assertEqual(world.wrap_value("₹500"), ["₹500"])
        self.assertEqual(world.wrap_value("Exchange · Account\nStore · Deferred"), ["Exchange · Account", "Store · Deferred"])
        self.assertEqual(world.wrap_value("Digital balances = digitally recorded पैसे"), ["Digital balances = digitally recorded", "पैसे"])   # 40 since 29 Oct
        self.assertEqual(len(world.wrap_value("Savings = आपके resources\nFuture instalment = obligation")), 2)     # 40 a line since 29 Oct
        plan = fixture("store_of_value_world.world.json")
        board = next(e for e in plan["elements"] if e["kind"] == "board")
        board["steps"][1]["text"] = "Bank deposits = खाते में जमा पैसे"
        scene, report = world.compile_world(copy.deepcopy(plan))
        self.assertEqual(report["problems"], [])
        compiled = next(e for e in scene["layers"][0]["data"]["elements"] if e["kind"] == "board")
        self.assertEqual(compiled["steps"][1]["lines"], ["Bank deposits = खाते में जमा पैसे"])      # one line of 40 since 29 Oct
        self.assertEqual(compiled["steps"][0]["lines"], ["₹0"])
        too_long = copy.deepcopy(plan)
        next(e for e in too_long["elements"] if e["kind"] == "board")["steps"][1]["text"] = "Savings = आपके resources\nFuture instalment = obligation\nEMI amount तय\nचौथी line नहीं"   # 4 lines
        with self.assertRaises(canvas.PlanError) as ctx:
            world.compile_world(too_long)
        self.assertIn("a board holds at most 3 lines of 40 characters", str(ctx.exception))
        self.assertIn("say the rest in the narration", str(ctx.exception))
        unbroken = copy.deepcopy(plan)
        next(e for e in unbroken["elements"] if e["kind"] == "board")["steps"][1]["text"] = "x" * 41      # one unbreakable word over 40
        with self.assertRaises(canvas.PlanError):
            world.compile_world(unbroken)
        tag = copy.deepcopy(fixture("demand_pull_world.world.json"))
        next(e for e in tag["elements"] if e["kind"] == "price_tag")["steps"][0]["text"] = "₹100 / basket"
        with self.assertRaises(canvas.PlanError) as ctx:
            world.compile_world(tag)
        self.assertIn("a price tag shows a price", str(ctx.exception))
        title = copy.deepcopy(fixture("demand_pull_world.world.json"))
        next(e for e in title["elements"] if e["kind"] == "title")["text"] = "Money: value → Limited supply → Purchasing power"
        with self.assertRaises(canvas.PlanError) as ctx:
            world.compile_world(title)
        self.assertIn("the title is at most 30 characters", str(ctx.exception))
        card = (ROOT / "bie" / "brain" / "rulebook" / "world_director_card.md").read_text(encoding="utf-8")
        self.assertIn("at most 3 lines of 40 characters", card)
        self.assertIn("at most 9 characters", card)
        self.assertIn("at most 30 characters", card)

    def test_a_bank_story_is_refused_until_it_has_its_bank(self):
        plan = fixture("store_of_value_world.world.json")
        shop_only = copy.deepcopy(plan)
        shop_only["elements"] = [dict(e, kind="shop") if e["kind"] == "bank" else e for e in shop_only["elements"] if e["kind"] != "teller"]
        with self.assertRaises(canvas.PlanError) as ctx:
            world.compile_world(shop_only)                                            # plan["kit"] == "bank"
        self.assertIn("a world in bank needs its place: add a bank element", str(ctx.exception))
        del shop_only["kit"]
        self.assertEqual(world.compile_world(shop_only)[1]["kit"], "shop")              # without a kit named, the shop is a world
        nothing = copy.deepcopy(plan)
        nothing["elements"] = [e for e in nothing["elements"] if e["kind"] not in ("bank", "teller")]
        del nothing["kit"]
        with self.assertRaises(canvas.PlanError) as ctx:
            world.compile_world(nothing)
        self.assertIn("add a shop or a bank element", str(ctx.exception))
        self.assertEqual(world.compile_world(copy.deepcopy(fixture("demand_pull_world.world.json")), kit="shop")[1]["kit"], "shop")
        self.assertEqual(world.KITS["bank"]["label"], "a bank with its customers at the counter")
        self.assertEqual(world.PLACE_KINDS, {"shop": "shop", "bank": "bank"})


class Icons(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.rows = icons.by_id()
        self.used = sorted({i for name in ("demand_pull_touches.plan.json", "price_chain.plan.json", "real_gdp.plan.json")
                            for i in canvas.icons_in(fixture(name))})
        tw, fa = self.tmp / "tw", self.tmp / "fa"
        for i in self.used:
            root = tw if i.startswith("tw:") else fa
            path = root / self.rows[i]["file"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((TW_SVG if i.startswith("tw:") else SVG).replace("<path ", f"<!-- {i} --><path "), encoding="utf-8")
        self.env = mock.patch.dict(os.environ, {"BIE_TWEMOJI_SVG": str(tw), "BIE_FONTAWESOME_SVGS": str(fa),
                                                "BIE_ASSET_CACHE": str(self.tmp / "cache")})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_the_index_is_two_cc_by_sets_without_brands_or_skin_tones(self):
        data = icons.load()
        self.assertEqual(data["schema"], icons.SCHEMA)
        self.assertEqual(data["count"], len(data["icons"]))
        self.assertGreater(data["count"], 4000)
        sets = {r["id"][:2] for r in data["icons"]}
        self.assertEqual(sets, {"tw", "fa"})
        for r in data["icons"]:
            self.assertTrue(icons.ID.match(r["id"]), r["id"])
            self.assertEqual(r["licence"], "CC BY 4.0")
            for key in icons.CREDIT_FIELDS + ("name", "terms", "style", "file"):
                self.assertTrue(r.get(key), (r["id"], key))
            self.assertFalse(icons.SKIN.search(r["id"]), r["id"])
            self.assertNotIn("brands", r["file"])
        self.assertEqual(icons.tw_name("1f3ea"), "convenience store")
        self.assertEqual(icons.tw_name("1f1ee-1f1f3"), "regional indicator symbol letter i + regional indicator symbol letter n")

    def test_search_check_and_safe_names(self):
        self.assertIn("tw:1f3e6", [r["id"] for r in icons.search("bank")][:3])
        self.assertEqual(icons.search("warehouse")[0]["id"], "fa:solid/warehouse")
        self.assertEqual(icons.search("qqqqzz"), [])
        self.assertEqual(icons.check_ids(["tw:1f3ea", "tw:zzz", "fa:brands/x", 7]), ["tw:zzz", "fa:brands/x", 7])
        self.assertEqual(icons.safe("fa:solid/building-columns"), "fa-solid-building-columns")

    def test_copy_colours_line_icons_and_writes_the_credits(self):
        out = icons.copy(self.used, self.tmp / "dest")
        self.assertEqual(out["tw:1f3ea"], "icons/tw-1f3ea.svg")
        self.assertTrue((self.tmp / "dest" / "icons" / "tw-1f3ea.svg").exists())
        fa = (self.tmp / "dest" / "icons" / "fa-solid-warehouse.svg").read_text(encoding="utf-8")
        self.assertIn('fill="#2b3a4a"', fa)
        self.assertNotIn("currentColor", fa)
        credits = json.loads((self.tmp / "dest" / "icons" / "credits.json").read_text(encoding="utf-8"))
        self.assertEqual([c["credit"] for c in credits], ["Font Awesome Free by Fonticons, Inc.",
                                                          "Twemoji graphics by Twitter, Inc and other contributors"])
        with self.assertRaises(icons.IconError):
            icons.copy(["tw:nope"], self.tmp / "dest")

    def test_icons_join_the_asset_library_and_pass_the_licence_gate_with_credit_lines(self):
        library = AssetLibrary(self.tmp / "assets")
        paths = icons.add_to_library(self.used, library)
        self.assertTrue(all(p.startswith("assets/") and p.endswith(".svg") for p in paths.values()))
        assets = list(library.assets.values())
        self.assertEqual(len(assets), len(self.used))
        self.assertEqual(licence.lesson_licence_check(assets), [])
        lines = licence.lesson_credits(assets)
        self.assertEqual(len(lines), len(self.used))
        self.assertTrue(all("CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)" in line for line in lines))
        self.assertTrue(any("Fonticons, Inc." in line and "https://fontawesome.com" in line for line in lines))
        once = icons.credit_assets(self.used)
        self.assertEqual(sorted(a["asset_id"] for a in once), ["fontawesome-free", "twemoji"])
        self.assertEqual(licence.lesson_licence_check(once), [])
        self.assertEqual(len(licence.lesson_credits(once)), 2)

    def test_a_missing_local_file_is_named_and_the_fetch_path_uses_the_pinned_tag(self):
        (Path(os.environ["BIE_TWEMOJI_SVG"]) / self.rows["tw:1f3ea"]["file"]).unlink()
        with self.assertRaises(icons.IconError):
            icons.icon_file("tw:1f3ea")
        with mock.patch.dict(os.environ, {"BIE_TWEMOJI_SVG": "", "BIE_FONTAWESOME_SVGS": ""}):
            urls = []

            class Response(io.BytesIO):
                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    return False

            def opener(request, timeout=None):
                urls.append(request.full_url)
                return Response(SVG.encode("utf-8"))

            path = icons.icon_file("fa:solid/warehouse", opener=opener)
            self.assertEqual(urls, ["https://raw.githubusercontent.com/FortAwesome/Font-Awesome/7.3.1/svgs/solid/warehouse.svg"])
            self.assertTrue(str(path).startswith(str(self.tmp / "cache")))
            icons.icon_file("fa:solid/warehouse", opener=opener)            # cached: no second fetch
            self.assertEqual(len(urls), 1)
            path = icons.icon_file("tw:1f4bb", opener=opener)
            self.assertEqual(urls[-1], "https://raw.githubusercontent.com/jdecked/twemoji/v16.0.1/assets/svg/1f4bb.svg")


class Registry(unittest.TestCase):
    def test_the_icon_sets_and_the_econ_blocks_are_registered_with_proofs_in_batch_3(self):
        box = registry.load()
        for tid, licence_name in (("twemoji", "CC BY 4.0"), ("fontawesome-free", "CC BY 4.0"), ("bie-econ-blocks", "BIE's own code")):
            tool = box.tool(tid)
            self.assertEqual((tool.batch, tool.status, tool.licence), (3, "demo_proven", licence_name), tid)
            self.assertTrue(tool.proof["demos"], tid)
            for demo_id in tool.proof["demos"]:
                self.assertIn(tid, demos.by_id(demo_id).tools)
        self.assertEqual(box.tool("twemoji").adapter, "bie.toolbox.icons")
        self.assertEqual(box.tool("bie-econ-blocks").block, "canvas_build, curve_story, world_scene")
        self.assertEqual(licence.tool_verdict(box.tool("twemoji")).verdict, "allowed")
        self.assertEqual(licence.tool_verdict(box.tool("fontawesome-free")).verdict, "allowed")

    def test_the_blocks_are_registered_and_imported_in_the_toolbox_bundle(self):
        canvas_tsx = (BLOCKS / "toolbox" / "canvas.tsx").read_text(encoding="utf-8")
        world_tsx = (BLOCKS / "toolbox" / "world.tsx").read_text(encoding="utf-8")
        self.assertEqual(set(re.findall(r'registerBlock\("([a-z_]+)"', canvas_tsx)), {"canvas_build", "curve_story"})
        self.assertEqual(set(re.findall(r'registerBlock\("([a-z_]+)"', world_tsx)), {"world_scene"})
        index = (BLOCKS / "toolbox" / "index.ts").read_text(encoding="utf-8")
        self.assertIn('import "./canvas";', index)
        self.assertIn('import "./world";', index)
        for text in (canvas_tsx, world_tsx):
            self.assertIn('from "../registry"', text)
            self.assertIn('from "./common"', text)


class Demos(unittest.TestCase):
    def test_the_econ_proof_clips_compile_offline_into_3_to_5_second_specs(self):
        tmp = Path(tempfile.mkdtemp())
        rows = icons.by_id()
        tw, fa = tmp / "tw", tmp / "fa"
        for name in ("demand_pull_touches.plan.json", "price_chain.plan.json", "real_gdp.plan.json"):
            for i in canvas.icons_in(fixture(name)):
                path = (tw if i.startswith("tw:") else fa) / rows[i]["file"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(SVG.replace("<path ", f"<!-- {i} --><path "), encoding="utf-8")
        with mock.patch.dict(os.environ, {"BIE_TWEMOJI_SVG": str(tw), "BIE_FONTAWESOME_SVGS": str(fa)}):
            econ = [d for d in demos.DEMOS if d.id.startswith("econ-") and d.tools[0] == "bie-econ-blocks"]
            self.assertEqual(len(econ), 6)
            self.assertIn("econ-world-bank-saving", [d.id for d in econ])
            for d in econ:
                work = demos.Work(folder=tmp / d.id, library=AssetLibrary(tmp / d.id / "assets"))
                spec = d.build(work)
                seconds = sum(s["duration"] for s in spec["scenes"]) / spec["fps"]
                self.assertAlmostEqual(seconds, d.seconds, delta=0.1, msg=d.id)
                self.assertTrue(3.0 <= seconds <= 5.0, d.id)
                self.assertTrue(render.needs_toolbox(spec), d.id)
                self.assertTrue(spec["captions"], d.id)
                self.assertTrue(spec["scenes"][0]["captions"], d.id)
                self.assertEqual(d.batch, 3)
                report = next(iter(work.notes.values()))
                self.assertEqual(report["problems"], [], d.id)
                self.assertIn(report["mode"], ("A", "B", "C"), d.id)
                for asset in work.library.assets.values():
                    self.assertEqual(asset.licence, "CC BY 4.0")
                    self.assertIn(asset.source, ("twemoji", "fontawesome-free"))
            receipts = [dataclasses.asdict(a) for a in AssetLibrary(tmp / "econ-price-chain" / "assets").assets.values()]
            self.assertEqual(len(receipts), 4)
            self.assertEqual(demos.lesson_use(demos.by_id("econ-price-chain").tools, receipts)["use"], "lessons")


if __name__ == "__main__":
    unittest.main()
