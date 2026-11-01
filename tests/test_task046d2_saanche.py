"""Task 046 Part D2 (Navin's verdict of 1 November 2026): kriya ke saanche, story goods from the story, the stricter layout and
meaning checks, and LOOK-D2. Offline tests: no network, no renderer."""
from __future__ import annotations

import base64
import copy
import json
import tempfile
import unittest
from pathlib import Path

from bie.brain import canvas, canvas_director as cd, look, visual_thinking as vt
from bie.brain.canvas import PlanError
from bie.brain.video import saanche, world

ROOT = Path(__file__).resolve().parents[1]
SHOP_BEATS = [
    {"beat_id": "b1", "say": "राम नमक खरीदने दुकान पर जाता है।"},
    {"beat_id": "b2", "say": "नमक ₹300 का है, राम ₹500 का नोट देता है।"},
    {"beat_id": "b3", "say": "दुकानदार नमक देता है और ₹200 वापस करता है।"},
    {"beat_id": "b4", "say": "अगले दिन राम फ़ोन से QR स्कैन करता है और ₹300 देता है।"},
    {"beat_id": "b5", "say": "राम के फ़ोन पर paid आता है, दुकानदार के फ़ोन पर received आता है।"},
]
PAY = {"id": "pay", "kind": "action", "template": "pay_change", "x": 2600,
       "actors": [{"role": "buyer", "who": "main", "label": "राम"}, {"role": "seller", "who": "other", "label": "दुकानदार"}],
       "objects": [{"name": "goods", "icon": "tw:1f9c2", "label": "नमक"}],
       "amounts": [{"name": "paid", "text": "₹500"}, {"name": "change", "text": "₹200"}, {"name": "price", "text": "₹300"}],
       "steps": [{"name": "pay", "cue": ["b2", "नोट"]}, {"name": "goods", "cue": ["b3", "नमक"]}, {"name": "change", "cue": ["b3", "वापस"]}],
       "until_cue": ["b4", "अगले"]}
UPI = {"id": "upi", "kind": "action", "template": "upi", "x": 2600,
       "actors": [{"role": "buyer", "who": "main", "label": "राम"}, {"role": "seller", "who": "other", "label": "दुकानदार"}],
       "amounts": [{"name": "amount", "text": "₹300"}],
       "steps": [{"name": "scan", "cue": ["b4", "स्कैन"]}, {"name": "paid", "cue": ["b5", "paid"]}, {"name": "received", "cue": ["b5", "received"]}]}


def shop_plan(**extra):
    plan = {"id": "v9_s1", "kit": "shop", "world_width": 5200, "beats": copy.deepcopy(SHOP_BEATS), "elements": [
        {"id": "shop", "kind": "shop", "x": 2600, "sign": "किराना", "goods": [{"icon": "tw:1f9c2", "label": "नमक"}],
         "packets": [{"n": 3, "cue": ["b1", "नमक"]}]}, copy.deepcopy(PAY), copy.deepcopy(UPI)],
        "camera": [{"cue": ["b1", ""], "x": 2600, "y": 540, "zoom": 1.0, "frames": 30}]}
    plan.update(extra)
    return plan


class Saanche(unittest.TestCase):
    def says(self):
        return {b["beat_id"]: b["say"] for b in SHOP_BEATS}

    def test_every_template_has_its_steps_roles_and_a_close_up_from_its_steps(self):
        for name, t in saanche.TEMPLATES.items():
            self.assertTrue(t["steps"], name)
            self.assertTrue(set(t["close"]) <= set(t["steps"]), name)
        self.assertIn("upi: the buyer's phone scans", saanche.templates_text())

    def test_the_problems_name_what_is_missing_and_numbers_must_be_said(self):
        bad = dict(copy.deepcopy(PAY), actors=[{"role": "buyer"}], objects=[], amounts=[{"name": "paid", "text": "₹700"}])
        problems = saanche.problems_of(bad, self.says())
        self.assertTrue(any("needs the actor 'seller'" in p for p in problems))
        self.assertTrue(any("needs the object 'goods'" in p for p in problems))
        self.assertTrue(any("needs the amount 'change'" in p for p in problems))
        self.assertTrue(any("'₹700' is not said" in p for p in problems))
        self.assertIn("is not a saancha", saanche.problems_of({"id": "x", "template": "juggle"}, {})[0])
        self.assertEqual(saanche.problems_of(PAY, self.says()), [])

    def test_steps_are_timed_in_order_with_a_close_up_and_the_main_character_keeps_one_look(self):
        frames = {"b2": 100, "b3": 200, "b4": 300}
        frame_of = lambda cue: frames[cue[0]] + (20 if cue[1] in ("वापस",) else 0)
        a = saanche.compile_action(PAY, frame_of, self.says(), icon_paths={"tw:1f9c2": "assets/files/salt.svg"}, main_look=42)
        self.assertEqual(list(a["step_at"]), ["pay", "goods", "change"])
        self.assertEqual(a["objects"]["goods"]["src"], "assets/files/salt.svg")
        self.assertEqual(a["close_up"]["at"], a["step_at"]["pay"] - 10)
        self.assertEqual([x["look"] for x in a["actors"] if x["main"]], [42])
        self.assertEqual(saanche.main_look("v2"), saanche.main_look("v2"))
        backwards = copy.deepcopy(PAY)
        backwards["steps"][0]["cue"] = ["b4", "अगले"]     # steps out of order are put in order now; ₹300 is then said in none of its beats
        with self.assertRaises(PlanError):
            saanche.compile_action(backwards, frame_of, {**self.says(), "b4": "अगले ₹500 नोट"})

    def test_code_guesses_the_template_from_the_beat_words(self):
        self.assertEqual(saanche.guess_template("फ़ोन से QR स्कैन करता है"), "upi")
        self.assertEqual(saanche.guess_template("दुकानदार ₹200 वापस करता है"), "pay_change")
        self.assertEqual(saanche.guess_template("दुकानदार सिक्का लेने से मना करता है"), "refuse")
        self.assertEqual(saanche.guess_template("बाज़ार में भीड़ है"), "")


class WorldGoodsAndLayout(unittest.TestCase):
    def test_no_hard_coded_good_is_left_and_the_shop_names_the_story_goods(self):
        tsx = (ROOT / "bie/brain/video/blocks/toolbox/world.tsx").read_text(encoding="utf-8")
        self.assertNotIn("SugarBag", tsx)
        self.assertNotIn("चीनी", tsx)
        plan = shop_plan()
        self.assertEqual(world.goods_problems(plan), [])
        plan["elements"][0].pop("goods")
        self.assertIn("the story's goods", world.goods_problems(plan)[0])
        self.assertEqual(world.icons_in(shop_plan()), ["tw:1f9c2"])

    def test_an_action_compiles_beside_its_place_and_the_camera_moves_in_and_back(self):
        scene, report = world.compile_world(shop_plan(), icon_paths={"tw:1f9c2": "assets/files/salt.svg"})
        self.assertEqual(report["actions"], ["pay_change", "upi"])
        data = scene["layers"][0]["data"]
        acts = [e for e in data["elements"] if e["kind"] == "action"]
        self.assertTrue(all(a["on_place"] for a in acts))
        self.assertEqual(data["elements"][0]["goods"][0]["src"], "assets/files/salt.svg")
        close = [k for k in data["camera"] if k.get("close_up")]
        self.assertEqual([k["close_up"] for k in close], ["pay", "upi"])
        self.assertTrue(all(k["zoom"] == world.CLOSE_ZOOM for k in close))
        self.assertGreater(data["camera"][-1]["at"], close[-1]["at"])            # and back out
        self.assertEqual(world.layout_problems(scene), [])

    def test_the_layout_check_names_overlaps_texts_numbers_the_strip_small_people_and_empty_frames(self):
        plan = shop_plan()
        plan["elements"] += [{"id": "b", "kind": "board", "x": 2600, "y": 500, "text": "खाता", "steps": [{"text": "नमक", "cue": ["b1", ""]}]},
                             {"id": "l", "kind": "label", "x": 2600, "y": 470, "text": "₹300 नमक", "cue": ["b1", "नमक"]},
                             {"id": "low", "kind": "label", "x": 3600, "y": 1010, "text": "नीचे", "cue": ["b1", ""]}]
        plan["camera"] += [{"cue": ["b2", ""], "x": 2600, "y": 540, "zoom": 0.6}, {"cue": ["b5", "received"], "x": 600, "y": 540, "zoom": 1.2}]
        problems = world.layout_problems(world.compile_world(plan)[0])
        self.assertTrue(any("b and l overlap" in p for p in problems), problems)
        self.assertTrue(any("at most one board, label or title" in p for p in problems))
        self.assertTrue(any("l: a label has no number" in p for p in problems))
        _, report = world.compile_world(plan)               # a label low in the frame is raised above the strip by code
        self.assertTrue(any(f.startswith("low raised") for f in report["auto_fixes"]), report["auto_fixes"])
        self.assertFalse(any("low reaches into the subtitle strip" in p for p in problems))
        self.assertTrue(any("camera key added on pay" in f for f in report["auto_fixes"]), report["auto_fixes"])   # code frames it
        scene, _ = world.compile_world(plan)
        for k in scene["layers"][0]["data"]["camera"]:          # the check itself still names people too small to see
            k["zoom"] = 0.6
        scene["layers"][0]["data"]["camera"][-1]["x"] = 200      # and a key that looks at no one (code moves the plan's keys to the action)
        checked = world.layout_problems(scene)
        self.assertTrue(any("of the frame tall" in p for p in checked))
        self.assertTrue(any("shows an empty street" in p for p in checked))

    def test_the_director_check_refuses_a_world_without_its_goods_and_passes_a_world_with_saanche(self):
        stub = {"id": "v9_s1", "beats": copy.deepcopy(SHOP_BEATS)}
        empty = {"x": 0, "y": 0, "sign": "", "text": "", "fill": "", "string": 0, "steps": [], "packets": [], "cue": [], "until_cue": [],
                 "tilt_cue": [], "tilt": 0, "x0": 0, "x1": 0, "y0": 0, "y1": 0, "spacing": 0, "enter_x": 0, "exit_x": 0, "face": 0,
                 "seed": 0, "count": 0, "lift_cue": [], "lift_dy": 0, "carry_cue": [], "carry_n": 0, "carry_icon": "", "goods": [],
                 "left_icon": "", "left_label": "", "right_icon": "", "right_label": "",
                 "action": {"template": "", "actors": [], "objects": [], "amounts": [], "steps": [], "close_up": False}}
        self.assertEqual(set(empty) | {"id", "kind"}, set(cd.WELEMENT["properties"]))
        act = lambda a: {k: a.get(k, []) for k in ("template", "actors", "objects", "amounts", "steps")} | {"close_up": True}
        value = {"notes": "", "camera": [{"cue": ["b1", ""], "x": 2600, "y": 540, "zoom": 1.0, "frames": 30}], "elements": [
            dict(empty, id="shop", kind="shop", x=2600, sign="किराना", goods=[{"icon": "tw:1f9c2", "label": "नमक"}], packets=[{"n": 3, "cue": ["b1", "नमक"]}]),
            dict(empty, id="pay", kind="action", x=2600, action=act(PAY)), dict(empty, id="upi", kind="action", x=2600, action=act(UPI))]}
        value["elements"][1]["until_cue"] = ["b4", "अगले"]
        mode = {"mode": "C", "kit": "shop"}
        self.assertEqual(cd.check_plan(stub, value, mode), [])
        plan = cd.world_from(stub, value, kit="shop")
        self.assertEqual(plan["elements"][1]["steps"][2], {"name": "change", "cue": ["b3", "वापस"]})
        no_goods = json.loads(json.dumps(value))
        no_goods["elements"][0]["goods"] = []
        self.assertIn("the story's goods", cd.check_plan(stub, no_goods, mode)[0])


class CanvasActions(unittest.TestCase):
    BEATS = [{"beat_id": "b1", "say": "राम दुकानदार को 25 पैसे का सिक्का देता है।"},
             {"beat_id": "b2", "say": "दुकानदार मना कर देता है, क्योंकि अब यह सिक्का चलन में नहीं है।"}]
    REFUSE = {"id": "act", "kind": "action", "cell": [1, 1, 10, 6], "template": "refuse",
              "actors": [{"role": "who", "who": "other", "label": "दुकानदार"}], "objects": [{"name": "thing", "icon": "tw:1fa99", "label": "सिक्का"}],
              "amounts": [], "steps": [{"name": "show", "cue": ["b1", "सिक्का"]}, {"name": "refuse", "cue": ["b2", "मना"]}]}

    def plan(self, node):
        return {"id": "v9_s2", "grid": [12, 8], "touches": True, "beats": copy.deepcopy(self.BEATS), "nodes": [node]}

    def test_an_action_fits_its_cells_at_the_stage_shape_and_the_camera_closes_in_above_the_strip(self):
        scene, report = canvas.compile_plan(self.plan(copy.deepcopy(self.REFUSE)))
        el = scene["layers"][0]["data"]["elements"][0]
        self.assertAlmostEqual(el["w"] * 1920 / (el["h"] * 1080), saanche.STAGE_W / saanche.STAGE_H, places=2)
        cam = scene["layers"][0]["data"]["cam"]
        close = [k for k in cam if k.get("close_up") == "act"]
        self.assertEqual(len(close), 1)
        box = close[0]["box"]
        self.assertLessEqual((el["y"] + el["h"] - box["y"]) / box["h"], canvas.SUBTITLE_TOP)
        self.assertEqual(canvas.subtitle_problems(scene), [])
        self.assertIn("tw:1fa99", canvas.icons_in(self.plan(self.REFUSE)))
        small = dict(copy.deepcopy(self.REFUSE), cell=[1, 1, 10, 2])
        with self.assertRaises(PlanError):
            canvas.compile_plan(self.plan(small))

    def test_a_camera_box_keeps_the_cells_it_shows_above_the_subtitle_strip(self):
        want = canvas.cell_box([0, 0, 12, 8], [12, 8])
        box = canvas.above_strip(canvas.fit_box(canvas.pad_box(want)), want)
        self.assertLessEqual((want["y"] + want["h"] - box["y"]) / box["h"], canvas.SUBTITLE_TOP + 1e-6)

    def test_the_strict_canvas_answer_carries_the_action(self):
        stub = {"id": "v9_s2", "beats": copy.deepcopy(self.BEATS)}
        node = {k: "" for k in cd.NODE["properties"]}
        node.update(id="act", kind="action", cell=[1, 1, 10, 6], cue=[], until_cue=[], steps=[], children=[], columns=[], rows=[],
                    highlights=[], marks=[], cue_fraction=0, until_fraction=0, size=0, cols=0, dashed=False, curve=False,
                    flow={"icon": "", "count": 0, "period": 0, "size": 0, "reverse": False, "cue": []},
                    picture={"type": "", "title": "", "items": [], "arrows": False},
                    action={k: self.REFUSE[k] for k in ("template", "actors", "objects", "amounts", "steps")} | {"close_up": True})
        value = {"notes": "", "nodes": [node], "camera": [], "focus": [], "graph_used": False, "graph": {}}
        plan = cd.plan_from(stub, value)
        self.assertEqual(plan["nodes"][0]["template"], "refuse")
        ideas = {"beats": [{"beat_id": "b1", "relation": "other"}, {"beat_id": "b2", "relation": "reject"}]}
        self.assertEqual(cd.check_plan(stub, value, "B", ideas=ideas), [])


class Meaning(unittest.TestCase):
    def test_a_refusal_needs_its_cross_and_change_given_back_is_the_change_template(self):
        beats = [{"beat_id": "b1", "say": "दुकानदार 25 पैसे का सिक्का लेने से मना करता है।"},
                 {"beat_id": "b2", "say": "दुकानदार ₹200 वापस करता है।"}]
        icon = {"id": "coin", "kind": "icon", "icon": "tw:1fa99", "cell": [0, 0, 2, 2], "cue": ["b1", "सिक्का"]}
        value = {"id": "price", "kind": "value", "cell": [4, 0, 4, 1], "steps": [{"text": "₹500", "cue": ["b2", ""]}, {"text": "₹200", "cue": ["b2", "वापस"], "dir": "down"}]}
        plan = {"beats": beats, "nodes": [icon, value]}
        ideas = {"beats": [{"beat_id": "b1", "relation": "reject"}, {"beat_id": "b2", "relation": "other"}]}
        problems = vt.meaning_problems(plan, "B", ideas)
        self.assertTrue(any("beat b1 is 'reject'" in p and "cross" in p for p in problems), problems)
        self.assertTrue(any("pay_change saancha" in p for p in problems), problems)
        plan["nodes"].append({"id": "x", "kind": "mark", "mark": "cross", "target": "coin", "cue": ["b1", "मना"]})
        plan["beats"].append({"beat_id": "b3", "say": "नमक ₹500 का है और 2 kg नमक मिलता है।"})
        plan["nodes"][1] = dict(value, steps=[{"text": "₹500", "cue": ["b3", ""]}, {"text": "2 kg", "cue": ["b3", "2"]}])
        problems = vt.meaning_problems(plan, "B", ideas)
        self.assertFalse(any("beat b1" in p for p in problems))
        self.assertTrue(any("two different quantities" in p for p in problems), problems)
        rows = vt.relation_rows(plan, "B", ideas)
        self.assertEqual(rows, [{"beat_id": "b1", "relation": "reject", "realised": True, "by": ["x"]}])

    def test_a_modern_icon_in_a_barter_beat_is_reported(self):
        plan = {"beats": [{"beat_id": "b1", "say": "पुराने ज़माने में barter होता था।"}],
                "nodes": [{"id": "p", "kind": "icon", "icon": "tw:1f4f1", "cue": ["b1", ""]}]}
        self.assertEqual(vt.icon_misfits(plan, "B")[0]["name"], "mobile phone")

    def test_the_ideas_name_a_template_per_beat_and_other_needs_its_note(self):
        stub = {"id": "s", "beats": [{"beat_id": "b1", "say": "राम फ़ोन से QR स्कैन करता है।"}]}
        row = {"beat_id": "b1", "idea": "upi", "relation": "sequence", "relation_note": "", "things": ["phone"], "people": [], "places": [],
               "shows": "phone scans the QR stand", "on_word": "", "image_wanted": ""}
        answer = {"beats": [dict(row, template="none")], "picture_type": "things"}
        self.assertIn("pick the template 'upi'", vt.check_ideas(stub, answer)[0])
        answer["beats"][0]["template"] = "other"
        self.assertIn("needs template_note", vt.check_ideas(stub, answer)[0])
        answer["beats"][0].update(template="upi")
        self.assertEqual(vt.check_ideas(stub, answer), [])
        self.assertIn("template", vt.IDEA["properties"])


class LookD2(unittest.TestCase):
    BEAT = {"beat_id": "b2", "nouns": ["coin", "shopkeeper"], "relation": "reject", "shows": "a cross on the coin", "template": "refuse"}

    def test_items_come_from_the_dikhane_ki_list_and_code_scores_the_answers(self):
        items = look.d2_items(self.BEAT)
        self.assertEqual([i["name"] for i in items], ["coin", "shopkeeper", "relation: reject", "process: refuse"])
        part = {"id": "v9_s2", "beats": [dict(self.BEAT, say="मना", items=items, frame="x")]}
        answer = {"beats": [{"beat_id": "b2", "text_only": False, "what_it_shows": "a man and a coin",
                             "items": [{"name": i["name"], "visible": True, "happening": i["name"].startswith(("relation", "process"))} for i in items]}],
                  "missing": ""}
        self.assertEqual(look.d2_problems(answer, part), [])
        self.assertEqual(look.d2_score(answer), {"items": 4, "visible": 4, "happening": 2, "text_only_beats": 0, "score": 7.5})
        self.assertIn("answer every item", look.d2_problems({"beats": [{"beat_id": "b2", "items": []}]}, part)[0])
        table = look.d2_summary({"v9_s2": dict(answer, numbers=look.d2_score(answer))})
        self.assertEqual((table["mean_score"], table["visible_pct"], table["happening_pct"]), (7.5, 100.0, 50.0))
        messages = look.d2_messages(part, [("b2", "image/jpeg", "AAAA")])
        self.assertEqual([c["type"] for c in messages[1]["content"]], ["text", "text", "image"])

    def test_the_vm_reads_a_d2_request_and_refuses_frames_outside_our_runs(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import vm_look
        frame = "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/t046d2-money-v4/stills/v4_s1/b1.jpg"
        req = {"schema": vm_look.SCHEMA, "rule": look.D2_RULE, "reviewer": "codex",
               "parts": [{"id": "v4_s1", "beats": [{"beat_id": "b1", "say": "x", "shows": "y", "frame": frame, "items": [{"name": "coin"}]}]}]}
        self.assertEqual(vm_look.load_request(json.dumps(req))["rule"], look.D2_RULE)
        bad = json.loads(json.dumps(req))
        bad["parts"][0]["beats"][0]["frame"] = "https://example.com/a.jpg"
        with self.assertRaises(ValueError):
            vm_look.load_request(json.dumps(bad))

    def test_the_request_builder_reads_each_beat_and_its_still(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import task046d_look_request as req
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / "video_specs").mkdir()
            (run / "visual_ideas").mkdir()
            spec = {"scenes": [{"id": "v4_s1", "captions": [{"beat_id": "b1", "text": "सिक्का", "at": 0, "until": 60}]}, {"id": "v4_credits"}]}
            (run / "video_specs" / "v4.json").write_text(json.dumps(spec), encoding="utf-8")
            ideas = {"parts": [{"id": "v4_s1", "beats": [dict(self.BEAT, beat_id="b1")]}]}
            (run / "visual_ideas" / "v4.json").write_text(json.dumps(ideas), encoding="utf-8")
            out = req.build_d2(run, "v4", "t046d2-money-v4")
        self.assertEqual(out["rule"], look.D2_RULE)
        self.assertTrue(out["parts"][0]["beats"][0]["frame"].endswith("/t046d2-money-v4/stills/v4_s1/b1.jpg"))


if __name__ == "__main__":
    unittest.main()


def element(scene, eid):
    return next(e for e in scene["layers"][0]["data"]["elements"] if e["id"] == eid)


def act(aid, x, at, template="hand_over", **extra):
    """A compiled world action (the shape ``saanche.compile_action`` returns), for the settle tests."""
    steps = saanche.TEMPLATES[template]["steps"]
    out = {"id": aid, "kind": "action", "template": template, "x": x, "at": at,
           "step_at": {s: at + 18 + 20 * i for i, s in enumerate(steps)}, "actors": [], "objects": {}, "amounts": {}}
    out.update(extra)
    return out


def world_scene(els, cam, duration=300):
    return {"id": "s", "duration": duration, "layers": [{"data": {"elements": els, "camera": cam}}]}


class AutoFixes(unittest.TestCase):
    """Seekh -> BIE from the first Part D2 run (1 November 2026, 88 rounds for 36 parts): what code settles itself."""

    def says(self):
        return {b["beat_id"]: b["say"] for b in SHOP_BEATS}

    def test_an_action_is_completed_from_the_narration(self):
        upi = copy.deepcopy(UPI)
        upi["amounts"] = [{"name": "price", "text": "₹300"}]            # an amount upi does not have, and its own one missing
        upi["steps"] = upi["steps"][:2] + [{"name": "wave", "cue": ["b5", "paid"]}]
        fixes = saanche.complete_action(upi, self.says())
        self.assertEqual(upi["amounts"], [{"name": "amount", "text": "₹300"}])
        self.assertEqual([s["name"] for s in upi["steps"]], ["scan", "paid", "received"])
        self.assertEqual(upi["steps"][-1]["cue"], ["b5", "paid"])          # the last step takes the cue of the one before
        self.assertEqual(len(fixes), 4, fixes)
        self.assertEqual(saanche.problems_of(upi, self.says()), [])
        stack = {"id": "c", "template": "count_stack", "actors": [], "objects": [{"name": "thing", "icon": "tw:1fa99"}],
                 "steps": [{"name": "count", "cue": ["b1", "राम"]}]}
        saanche.complete_action(stack, {"b1": "राम तीन सिक्के गिनता है।"})
        self.assertEqual(stack["amounts"], [{"name": "n", "text": "3"}])
        coins = {"id": "m", "template": "coin_count", "steps": []}
        saanche.complete_action(coins, {})
        self.assertNotIn("amounts", coins)                                  # nothing said: nothing made up

    def test_steps_said_in_another_order_follow_the_template_on_their_words(self):
        give = {"id": "g", "kind": "action", "template": "hand_over", "objects": [{"name": "thing", "icon": "tw:1f9c2", "label": "नमक"}],
                "actors": [{"role": "giver", "who": "other"}, {"role": "taker", "who": "main"}],
                "steps": [{"name": "give", "cue": ["b3", "नमक"]}, {"name": "take", "cue": ["b2", "नोट"]}]}
        frames = {"b2": 100, "b3": 200}
        a = saanche.compile_action(give, lambda cue: frames[cue[0]], self.says())
        self.assertEqual(a["step_at"], {"give": 100, "take": 200})
        self.assertTrue(any("follow the template" in f for f in a["auto_fixes"]))

    def test_an_action_stays_until_its_last_step_has_played(self):
        give = {"id": "g", "kind": "action", "template": "hand_over", "objects": [{"name": "thing", "icon": "tw:1f9c2", "label": "नमक"}],
                "actors": [{"role": "giver", "who": "other"}, {"role": "taker", "who": "main"}],
                "steps": [{"name": "give", "cue": ["b2", "नोट"]}, {"name": "take", "cue": ["b3", "नमक"]}], "until_cue": ["b3", "नमक"]}
        frames = {"b2": 100, "b3": 200}
        a = saanche.compile_action(give, lambda cue: frames[cue[0]], self.says())
        self.assertEqual(a["until"], 200 + saanche.PLAYED)
        self.assertTrue(any("stays until its last step has played" in f for f in a["auto_fixes"]))
        first = act("first", 2600, 40, "refuse")                   # its refuse step at 78
        second = act("second", 2600, 70, "accept")                 # its show step at 88: they meet on one spot
        fixes = world.settle_places([first, second], 300)
        self.assertEqual(first["until"], 88)                       # the refusal plays 10 frames, then the acceptance comes on
        self.assertEqual(second["at"], 88)
        self.assertIn("first plays its last step, then second comes on in its place", fixes)

    def test_a_counted_stack_finishes_its_count_before_it_leaves(self):
        stack = act("stack", 2600, 30, "count_stack", items=[48 + 18 * i for i in range(10)])     # code spread 10 over the beat
        nxt = act("next", 2600, 150, "accept")
        world.settle_places([stack, nxt], 400)
        self.assertEqual(len(stack["items"]), 10)
        self.assertLessEqual(stack["items"][-1] + saanche.PLAYED, stack["until"])                # all ten appear before it goes
        crowded = act("stack", 2600, 30, "count_stack", items=[48 + 18 * i for i in range(10)])
        self.assertFalse(saanche.fit_items(crowded, 70))                                         # 10 items in 10 frames: no
        self.assertEqual(crowded["items"][0], 48)

    def test_places_and_times_code_settles(self):
        label = {"id": "l", "kind": "label", "x": 600, "y": 300, "text": "नमक", "at": 50, "until": 40}
        a, b = act("a", 2600, 40), act("b", 2600, 45)
        fixes = world.settle_places([label, a, b], 300)
        self.assertNotIn("until", label)                                    # an until before its cue would hide it for good
        self.assertEqual(b["x"], 2600 + saanche.STAGE_W)                    # two actions starting together stand side by side
        self.assertEqual(len(fixes), 2, fixes)
        first, second = act("first", 2600, 40, "refuse", until=100), act("second", 2600, 130, "accept")
        fixes = world.settle_places([first, second], 300)
        self.assertEqual(first["until"], 130)                               # no empty stage between them
        self.assertIn("the stage was empty for 1.0 s", fixes[0])
        first, second = act("first", 2600, 40, "refuse", until=100), act("second", 2600, 130, "accept")
        board = {"id": "bd", "kind": "board", "x": 2600, "y": 500, "steps": [{"text": "खाता", "at": 105}], "until": 125}
        world.settle_places([first, second, board], 300)
        self.assertEqual(first["until"], 100)                               # something else is shown there meanwhile
        playing = act("p", 2600, 40, "pay_change")
        board = {"id": "bd", "kind": "board", "x": 2600, "y": 500, "steps": [{"text": "खाता", "at": 60}]}
        world.settle_places([playing, board], 300)
        self.assertNotIn("until", playing)                                  # an action never leaves before it has played

    def test_a_close_up_ends_when_its_action_leaves_or_the_next_one_starts(self):
        cam = [{"at": 0, "x": 2600, "y": 540, "zoom": 1.0, "frames": 30}]
        a = act("a", 2600, 10, "refuse", until=120, close_up={"at": 50, "until": 200, "step": "refuse"})
        fixes = []
        keys = world._close_ups(cam, [a], fixes)
        self.assertEqual([(k["at"], k.get("close_up")) for k in keys], [(0, None), (50, "a"), (120, None)])
        self.assertIn("the close-up on a ends at 120, when a leaves", fixes)
        a = act("a", 2600, 10, "refuse", close_up={"at": 50, "until": 200, "step": "refuse"})
        cam2 = cam + [{"at": 90, "x": 3600, "y": 540, "zoom": 1.0, "frames": 24, "frame": "b"}]
        keys = world._close_ups(cam2, [a, act("b", 3600, 90)], [])
        self.assertEqual([(k["at"], k["x"]) for k in keys], [(0, 2600), (50, 2600), (90, 3600)])
        self.assertFalse(any("frame" in k for k in keys))
        short = act("s", 2600, 10, "refuse", until=60, close_up={"at": 50, "until": 200, "step": "refuse"})
        self.assertEqual(world._close_ups(cam, [short], []), cam)          # too short to move in: the camera stays

    def test_the_camera_frames_and_widens_for_the_actions_and_looks_low_enough(self):
        a, b = act("a", 2600, 10), act("b", 3600, 20)
        keys, fixes = world._frame_actions([{"at": 0, "x": 2600, "y": 540, "zoom": 1.0, "frames": 30}], [a, b], [])
        self.assertIn("camera key added on b at its start (x 3600)", fixes)
        self.assertTrue(any("widened to hold a, b" in f for f in fixes), fixes)
        self.assertEqual(keys[-1]["x"], 3100)
        self.assertGreaterEqual(keys[-1]["zoom"], 0.9)
        cam = [{"at": 0, "x": 2600, "y": 540, "zoom": 1.3, "frames": 30}]
        fixes = world.settle_layout([act("a", 2600, 10)], cam, 300)
        self.assertEqual(cam[0]["y"], 553)                                   # the feet stay above the subtitle strip
        self.assertTrue(fixes)

    def test_an_empty_street_over_time_is_named(self):
        shop = {"id": "shop", "kind": "shop", "x": 2600}
        away = [{"at": 0, "x": 2600, "y": 540, "zoom": 1.0, "frames": 30}, {"at": 100, "x": 600, "y": 540, "zoom": 1.0, "frames": 10},
                {"at": 200, "x": 2600, "y": 540, "zoom": 1.0, "frames": 10}]
        problems = world.empty_frames(world_scene([shop], away))
        self.assertEqual(len(problems), 1)
        self.assertIn("empty street from 3.", problems[0])
        glide = [dict(k) for k in away]
        glide[2]["at"] = 115                                                 # a glide past the empty street is fine
        self.assertEqual(world.empty_frames(world_scene([shop], glide)), [])
        gone = world_scene([shop, act("a", 4400, 10, until=60)], [{"at": 0, "x": 4400, "y": 540, "zoom": 1.0, "frames": 30}])
        self.assertIn("(the camera at x 4400)", world.empty_frames(gone)[0])  # the camera stays where the people have gone
        close = world_scene([shop, act("a", 2600, 10, until=60)], [{"at": 0, "x": 2600, "y": 540, "zoom": 1.0, "frames": 30},
                            {"at": 40, "x": 2600, "y": world.CLOSE_Y, "zoom": world.CLOSE_ZOOM, "frames": 22, "close_up": "a"}])
        self.assertIn("from 2.0 s", world.empty_frames(close)[0])            # close on people who have gone, the shop behind

    def test_code_draws_an_unshown_sequence_and_counts_highlights_and_playing_processes(self):
        beats = [{"beat_id": "b1", "say": "राम गेहूँ लाता है।"}, {"beat_id": "b2", "say": "फिर गेहूँ से कपड़ा मिलता है।"}]
        wheat = {"id": "wheat", "kind": "icon", "icon": "tw:1f33e", "cell": [0, 0, 2, 2], "cue": ["b1", "गेहूँ"]}
        cloth = {"id": "cloth", "kind": "icon", "icon": "tw:1f9f5", "cell": [4, 0, 2, 2], "cue": ["b2", "कपड़ा"]}
        plan = {"beats": beats, "nodes": [wheat, cloth]}
        ideas = {"beats": [{"beat_id": "b1", "relation": "other"}, {"beat_id": "b2", "relation": "sequence"}]}
        self.assertFalse(vt.relation_rows(plan, "B", ideas)[0]["realised"])
        fixes = vt.realise_relations(plan, "B", ideas)
        self.assertEqual(plan["nodes"][-1], {"id": "auto_arrow_b2", "kind": "arrow", "from": "wheat", "to": "cloth", "cue": ["b2", "कपड़ा"]})
        self.assertEqual(fixes, ["arrow wheat → cloth drawn on beat b2 (sequence)"])
        self.assertTrue(vt.relation_rows(plan, "B", ideas)[0]["realised"])
        self.assertEqual(vt.realise_relations(plan, "C", ideas), [])           # a world shows it with a saancha, not an arrow
        line = {"id": "tl", "kind": "picture", "cell": [0, 3, 12, 3], "cue": ["b1", ""], "picture": {"type": "timeline"}}
        mark = {"id": "h", "kind": "highlight", "target": "tl.2", "cue": ["b2", "फिर"]}
        rows = vt.relation_rows({"beats": beats, "nodes": [line, mark]}, "B", ideas)
        self.assertEqual(rows[0]["by"], ["h"])
        three = beats + [{"beat_id": "b3", "say": "कपड़ा राम के पास।"}]
        give = {"id": "give", "kind": "action", "template": "hand_over", "steps": [{"name": "give", "cue": ["b1", ""]}, {"name": "take", "cue": ["b3", ""]}]}
        rows = vt.relation_rows({"beats": three, "nodes": [give]}, "B", ideas)
        self.assertEqual(rows[0]["by"], ["give"])

    def test_a_canvas_element_leaves_its_cells_only_when_it_has_nothing_left_to_show(self):
        beats = [{"beat_id": "b1", "say": "राम ₹500 देता है।"}, {"beat_id": "b2", "say": "दुकानदार नमक देता है।"},
                 {"beat_id": "b3", "say": "राम के पास ₹200 बचते हैं।"}]
        value = {"id": "v", "kind": "value", "cell": [0, 0, 4, 2], "steps": [{"text": "₹500", "cue": ["b1", "देता"]}]}
        salt = {"id": "salt", "kind": "icon", "icon": "tw:1f9c2", "cell": [0, 0, 4, 2], "cue": ["b2", "नमक"]}
        for order in ((value, salt), (salt, value)):              # either order in the plan
            plan = {"id": "s", "grid": [12, 8], "touches": True, "beats": copy.deepcopy(beats), "nodes": copy.deepcopy(list(order))}
            _, report = canvas.compile_plan(plan)
            self.assertIn("v leaves when salt comes (its cells)", report["auto_fixes"])
            busy = copy.deepcopy(list(order))
            next(n for n in busy if n["id"] == "v")["steps"].append({"text": "₹200", "cue": ["b3", "बचते"]})
            with self.assertRaises(PlanError):                     # its ₹200 is still to come: the maker moves one
                canvas.compile_plan({"id": "s", "grid": [12, 8], "touches": True, "beats": copy.deepcopy(beats), "nodes": busy})

    def test_two_processes_on_one_place_hand_over_after_the_first_ones_last_step(self):
        beats = [{"beat_id": "b1", "say": "किसान ने नमक दिया और कपड़ा लिया। इसलिए अब वह आगे नमक देता है और गेहूँ लेता है।"}]
        def give(aid, g, t, thing):
            return {"id": aid, "kind": "action", "template": "hand_over", "cell": [0, 2, 12, 4],
                    "actors": [{"role": "giver", "who": "main"}, {"role": "taker", "who": "other"}],
                    "objects": [{"name": "thing", "icon": "tw:1f9c2", "label": thing}],
                    "steps": [{"name": "give", "cue": ["b1", g]}, {"name": "take", "cue": ["b1", t]}]}
        first, second = give("one", "दिया", "लिया।", "नमक"), give("two", "इसलिए", "लेता", "नमक")
        first["until_cue"] = ["b1", "लेता"]                      # the maker kept the first on too long
        scene, report = canvas.compile_plan({"id": "s", "grid": [12, 8], "touches": True, "beats": beats, "nodes": [first, second]})
        one, two = (element(scene, i) for i in ("one", "two"))
        self.assertGreaterEqual(one["until"], one["step_at"]["take"] + 8)        # it plays its take
        self.assertGreaterEqual(two["at"], one["until"])
        self.assertLessEqual(two["at"], two["step_at"]["give"])
        close = copy.deepcopy(second)
        close["steps"][0]["cue"] = ["b1", "लिया।"]                               # the second gives on the first's take: refused
        with self.assertRaises(PlanError):
            canvas.compile_plan({"id": "s", "grid": [12, 8], "touches": True, "beats": beats, "nodes": [copy.deepcopy(first), close]})
        self.assertTrue(any("two comes on" in f for f in report["auto_fixes"]), report["auto_fixes"])
        cam = scene["layers"][0]["data"]["cam"]
        for k in cam:                                                            # no close-up outlives its action
            if k.get("close_up") == "one":
                nxt = min(x["at"] for x in cam if x["at"] > k["at"])
                self.assertLessEqual(nxt, one["until"])

    def test_a_tree_leaves_on_its_until_and_an_action_comes_on_as_a_book_picture_leaves(self):
        beats = [{"beat_id": "b1", "say": "barter की कमियाँ: बराबर नहीं, बाँट नहीं सकते।"}, {"beat_id": "b2", "say": "अब सिक्के आए।"},
                 {"beat_id": "b3", "say": "फिर सीधा लेन देन हुआ, राम ने गेहूँ दिया और कपड़ा लिया।"}]
        tree = {"id": "lim", "kind": "tree", "cell": [3, 0, 9, 3], "root": "कमियाँ", "cue": ["b1", "कमियाँ:"], "until_cue": ["b2", "अब"],
                "children": [{"text": "बराबर नहीं", "cue": ["b1", "बराबर"]}, {"text": "बाँट नहीं", "cue": ["b1", "बाँट"]}]}
        coins = {"id": "coins", "kind": "icon", "icon": "tw:1fa99", "cell": [3, 0, 9, 3], "cue": ["b2", "सिक्के"]}
        scene, _ = canvas.compile_plan({"id": "s", "grid": [12, 8], "touches": True, "beats": copy.deepcopy(beats), "nodes": [tree, coins]})
        kids = [e for e in scene["layers"][0]["data"]["elements"] if e["id"].startswith("lim_")]
        self.assertTrue(kids and all(e["until"] == kids[0]["until"] for e in kids))
        swap = {"id": "swap", "kind": "action", "template": "hand_over", "cell": [0, 2, 12, 5],
                "actors": [{"role": "giver", "who": "main"}, {"role": "taker", "who": "other"}],
                "objects": [{"name": "thing", "icon": "tw:1f33e", "label": "गेहूँ"}],
                "steps": [{"name": "give", "cue": ["b3", "दिया"]}, {"name": "take", "cue": ["b3", "लिया।"]}]}
        shelf = {"id": "shelf", "kind": "icon", "icon": "tw:1f9fa", "cell": [0, 2, 12, 4], "cue": ["b1", ""], "until_cue": ["b3", "दिया"],
                 "group": "book_gallery"}
        scene, report = canvas.compile_plan({"id": "s", "grid": [12, 8], "touches": True, "beats": copy.deepcopy(beats), "nodes": [shelf, swap]})
        self.assertEqual(element(scene, "swap")["at"], element(scene, "shelf")["until"])     # the book picture is never moved
        self.assertIn("swap comes on when shelf leaves (its lead-in shortened) (same place)", report["auto_fixes"])

    def test_a_zoom_into_a_close_up_never_dips_the_feet_into_the_strip(self):
        limit = world.SUBTITLE_TOP * world.FRAME_H - world.FRAME_H / 2 - 2
        def worst(cam, frames):
            return max(world.cam_at(cam, f)["zoom"] * (world.GROUND - 10 - world.cam_at(cam, f)["y"]) for f in frames)
        cam = [{"at": 0, "x": 2600, "y": 443, "zoom": 0.95, "frames": 30},
               {"at": 100, "x": 2600, "y": world.CLOSE_Y, "zoom": world.CLOSE_ZOOM, "frames": 22, "close_up": "a"}]
        self.assertGreater(worst(cam, range(100, 123)), limit)             # run b's v2_s4s: the feet dip at 41.0 s
        fixes = world._split_dips(cam, [act("a", 2600, 50)], 300)
        self.assertEqual(len(cam), 3)
        self.assertEqual((cam[1]["at"], cam[1]["zoom"], cam[1]["y"]), (100, 0.95, world.CLOSE_Y))   # pan first, then zoom
        self.assertEqual((cam[2]["at"], cam[2]["close_up"]), (111, "a"))
        self.assertLessEqual(worst(cam, range(100, 140)), limit + 0.5)
        self.assertTrue(fixes)
        quiet = [dict(k) for k in cam[:1]] + [{"at": 100, "x": 2600, "y": world.CLOSE_Y, "zoom": world.CLOSE_ZOOM, "frames": 22}]
        self.assertEqual(world._split_dips(quiet, [act("a", 2600, 400)], 600), [])   # nobody on the stage: nothing to lift

    def test_after_the_camera_nothing_moves_only_who_leaves_when(self):
        board = {"id": "bd", "kind": "board", "x": 2600, "y": 300, "steps": [{"text": "2 metres", "at": 100}]}
        pans = {"id": "bal", "kind": "balance", "x": 2600, "y": 480, "at": 300, "left": {"icon": "a"}, "right": {"icon": "b"}}
        a, b = act("a", 3600, 40), act("b", 3600, 45)
        fixes = world.settle_places([board, pans, a, b], 600, place=False)
        self.assertEqual(board["until"], 300)
        self.assertEqual(b["x"], 3600)                                     # no action moves once the camera is framed
        self.assertIn("bd leaves when bal comes (same place)", fixes)

    def test_change_given_back_needs_money_and_a_plural_is_one_unit(self):
        self.assertFalse(vt.gives_change_back("लौटाया 10 kg ही, लेकिन उससे तब 1 metre कपड़ा मिलता है।"))   # grain repaid
        self.assertTrue(vt.gives_change_back("दुकानदार ₹200 वापस करता है।"))
        self.assertTrue(vt.gives_change_back("उसके पास चिल्लर नहीं है।"))
        self.assertEqual(vt._unit("2 metres कपड़ा"), vt._unit("1 metre कपड़ा"))
        self.assertEqual(vt._unit("3 सिक्के"), vt._unit("1 सिक्का"))
        self.assertNotEqual(vt._unit("₹500"), vt._unit("2 kg"))
        plan = {"beats": [{"beat_id": "b20", "say": "अब 2 metres कपड़ा लेकर 10 kg अनाज बाद में देना माना। लौटाया 10 kg ही, लेकिन उससे तब 1 metre कपड़ा मिलता है।"}],
                "elements": [{"id": "cloth", "kind": "board", "steps": [{"text": "2 metres कपड़ा", "cue": ["b20", "2"]},
                                                                         {"text": "1 metre कपड़ा", "cue": ["b20", "1"]}]}]}
        self.assertEqual(vt.struck_problems(plan, "C"), [])

    def test_the_lists_own_saancha_and_a_refusal_beside_an_acceptance_realise_their_beats(self):
        beats = [{"beat_id": "b32", "say": "आप ₹100 देते हैं; दुकानदार पूरा उधार चुका मानता है।"},
                 {"beat_id": "b43", "say": "दुकानदार पुराने coins लेने से मना करे; valid ₹1 coin दें तो बकाया ₹0 होता है।"}]
        pay = {"id": "pay", "kind": "action", "template": "hand_over", "steps": [{"name": "give", "cue": ["b32", "देते"]}, {"name": "take", "cue": ["b32", "मानता"]}]}
        no = {"id": "no", "kind": "action", "template": "refuse", "steps": [{"name": "show", "cue": ["b43", "पुराने"]}, {"name": "refuse", "cue": ["b43", "मना"]}]}
        yes = {"id": "yes", "kind": "action", "template": "accept", "steps": [{"name": "show", "cue": ["b43", "valid"]}, {"name": "accept", "cue": ["b43", "बकाया"]}]}
        ideas = {"beats": [{"beat_id": "b32", "relation": "accept", "template": "hand_over"}, {"beat_id": "b43", "relation": "compare", "template": "other"}]}
        rows = vt.relation_rows({"beats": beats, "elements": [pay, no, yes]}, "C", ideas)
        self.assertEqual([(r["beat_id"], r["realised"], r["by"]) for r in rows], [("b32", True, ["pay"]), ("b43", True, ["no", "yes"])])
        ideas["beats"][0]["template"] = "none"                              # the list chose no saancha: a tick is still needed
        self.assertFalse(vt.relation_rows({"beats": beats, "elements": [pay, no]}, "C", ideas)[0]["realised"])
        self.assertFalse(vt.relation_rows({"beats": beats, "elements": [pay, no]}, "C", ideas)[1]["realised"])   # a refusal alone

    def test_a_currency_sign_alone_names_a_coin_on_a_label(self):
        from bie.brain.video import screen_text
        problems = screen_text.text_problems("¥", "यह ¥ का सिक्का है।", where="l", role="label")
        self.assertFalse(any("unfinished" in p for p in problems), problems)
        self.assertTrue(any("unfinished" in p for p in screen_text.text_problems("→", "आगे", where="l", role="label")))


class MoneyDrawingRules(unittest.TestCase):
    def test_the_animated_note_coin_and_qr_keep_bies_money_rules(self):
        # docs/bie/BIE_MONEY_OBJECTS.md: the same rules as the bie: drawings (no RBI marks, 1.6 : 1 notes, "not money", no UPI mark)
        from tests.test_task046d2_pictures import FORBIDDEN
        tsx = (ROOT / "bie/brain/video/blocks/toolbox/saanche.tsx").read_text(encoding="utf-8")
        body = tsx.split("export const Note", 1)[1]
        for word in FORBIDDEN:
            self.assertNotIn(word, body, word)
        self.assertIn("const h = w / 1.6", body)
        self.assertIn("नमूना · not money", body)
        self.assertIn("SCAN · PAY", tsx)
        self.assertNotIn("UPI</text>", tsx)
