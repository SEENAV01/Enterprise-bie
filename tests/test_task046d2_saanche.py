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
        backwards["steps"][0]["cue"] = ["b4", "अगले"]
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
        self.assertTrue(any("low reaches into the subtitle strip" in p for p in problems))
        self.assertTrue(any("of the frame tall" in p for p in problems))
        self.assertTrue(any("shows an empty street" in p for p in problems))

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
