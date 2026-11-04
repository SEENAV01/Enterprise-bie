"""Phase 1, part B3: the game-level slot — five mechanics as code on the existing phone runtime.

Offline. The example levels here are test data (Claude's demo, not BIE output; BIE's AI writes real levels in
part C), never passed outputs.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import formats, game_levels as gl  # noqa: E402
from bie.brain.game_build import STAGE_SCHEMA  # noqa: E402
from bie.brain.game_runtime import render_game_html  # noqa: E402
from bie.model_gateway.schema_validation import validate  # noqa: E402


def level(mechanic, **extra):
    """A playable Money-chapter example of each mechanic (test data: Claude's demo, not BIE output)."""
    base = {"schema": "bie.game-level/1", "level_id": f"money-{mechanic}", "title": "Money", "win": "काम चल पड़ा!",
            "item_ids": ["p002-i2"], "mechanic": mechanic}
    if mechanic == "run_process":
        base.update(instruction="बैंक में पैसा जमा करने के कदम सही क्रम में चलाओ।",
                    pieces=[{"id": "fill", "label": "पर्ची भरो", "right": "पर्ची तैयार।"},
                            {"id": "give", "label": "पैसे दो", "right": "कैशियर ने गिने।"},
                            {"id": "entry", "label": "खाते में entry", "right": "खाता बढ़ गया।"}],
                    order_why="जमा इसी क्रम में होती है।")
    elif mechanic == "place_right":
        base.update(instruction="हर चीज़ उसकी सही जगह रखो।",
                    pieces=[{"id": "note", "label": "₹500 का नोट", "fits": "purse", "right": "नोट बटुए में सही।",
                             "wrong": "नोट मटके में भीग जाएगा।"},
                            {"id": "wheat", "label": "गेहूँ", "fits": "sack", "right": "अनाज बोरी में सुरक्षित।",
                             "wrong": "गेहूँ बटुए में नहीं समाता।"}],
                    places=[{"id": "purse", "label": "बटुआ"}, {"id": "sack", "label": "बोरी"}])
    elif mechanic == "build_timeline":
        base.update(instruction="पैसे का सफ़र: जो पहले आया, उसे पहले रखो।",
                    pieces=[{"id": "barter", "label": "Barter", "right": "सबसे पहले अदला-बदली।"},
                            {"id": "coin", "label": "सिक्के", "right": "फिर धातु के सिक्के।"},
                            {"id": "note", "label": "नोट", "right": "फिर काग़ज़ के नोट।"},
                            {"id": "upi", "label": "UPI", "right": "आज digital।"},
                            {"id": "card9", "label": "Credit card से पहले UPI", "decoy": True,
                             "wrong": "ग़लत: UPI card के बाद आया; timeline टूट गई।"}])
    elif mechanic == "find_partner":
        base.update(instruction="रामू के पास गेहूँ है, उसे कपड़ा चाहिए। सही साथी से मिलाओ।",
                    pieces=[{"id": "ramu", "label": "रामू: गेहूँ है, कपड़ा चाहिए", "fits": "mohan",
                             "right": "दोनों की ज़रूरत मिल गई!", "wrong": "इसे गेहूँ नहीं चाहिए: सौदा नहीं होगा।"},
                            {"id": "sita", "label": "सीता: मटका है, नमक चाहिए", "fits": "salt",
                             "right": "मटका ↔ नमक, सौदा पक्का।", "wrong": "यह नमक नहीं देता।"}],
                    places=[{"id": "mohan", "label": "मोहन: कपड़ा है, गेहूँ चाहिए"},
                            {"id": "salt", "label": "नमक वाला: नमक है, मटका चाहिए"}])
    else:
        base.update(instruction="बारिश से अनाज-पैसे पर क्या-क्या होता है? कारण से असर तक जोड़ो।",
                    pieces=[{"id": "rain", "label": "बारिश हुई", "right": "यही शुरुआत है।"},
                            {"id": "wet", "label": "अनाज भीगा", "right": "भीगा अनाज ख़राब।"},
                            {"id": "value", "label": "क़ीमत गिरी", "right": "ख़राब अनाज कोई नहीं लेता।"}],
                    order_why="असर कारण के बाद आता है।")
    base.update(extra)
    return base


class LevelSlot(unittest.TestCase):
    def test_a_hostile_shape_is_a_named_problem_never_a_crash(self):
        # The first live writers' run died on a shape like these ("'str' object has no attribute 'get'").
        self.assertIn("must be a JSON object", gl.problems("not a level")[0])
        with_str_piece = level("run_process")
        with_str_piece["pieces"] = list(with_str_piece["pieces"]) + ["a string piece"]
        self.assertIn("must be a JSON object", " ".join(gl.problems(with_str_piece)))
        with_dict_pieces = level("run_process") | {"pieces": {"p1": "x"}}
        self.assertIn("'pieces' must be a list", " ".join(gl.problems(with_dict_pieces)))

    def test_every_mechanic_has_a_valid_level_that_lowers_to_a_playable_stage(self):
        for mech in gl.DRAG:
            lv = level(mech)
            self.assertEqual(formats.problems("game_level", lv), [], mech)
            self.assertEqual(gl.problems(lv), [], mech)
            stage = gl.stage_of(lv)
            validate(stage, STAGE_SCHEMA)                       # the existing runtime's stage shape, exactly
            self.assertEqual(stage["kind"], "drag")
            self.assertEqual(stage["ordered"], mech in ("run_process", "build_timeline", "cause_effect"))
            tokens = {t["id"] for t in stage["tokens"]}
            for rule in stage["rules"]:
                self.assertIn(rule["token"], tokens)
                self.assertTrue(rule["feedback"], f"{mech}: a move without its what-and-why")
            rights = [r for r in stage["rules"] if r["correct"]]
            wrongs = [r for r in stage["rules"] if not r["correct"]]
            self.assertGreaterEqual(len(rights), 2, mech)
            self.assertGreaterEqual(len(wrongs), 1, mech)        # every level teaches through a wrong move

    def test_a_wrong_level_is_named_exactly(self):
        lv = level("run_process")
        lv["mechanic"] = "quiz"
        self.assertIn("no mechanic 'quiz'", gl.problems(lv)[0])
        lv = level("place_right")
        lv["pieces"][0]["fits"] = "shelf"
        self.assertTrue(any("fits 'shelf', which is no place" in p for p in gl.problems(lv)))
        lv = level("find_partner")
        del lv["pieces"][0]["wrong"]
        self.assertTrue(any("needs 'wrong'" in p for p in gl.problems(lv)))
        lv = level("build_timeline")
        lv["pieces"] = lv["pieces"][:1]
        self.assertTrue(any("at least 2" in p for p in gl.problems(lv)))
        lv = level("run_process")
        lv["pieces"] = [{"id": f"s{i}", "label": "x" * 50, "right": "ok"} for i in range(9)]
        problems = gl.problems(lv)
        self.assertTrue(any("2..7 pieces" in p for p in problems))
        self.assertTrue(any(f"over {gl.MAX_LABEL} characters" in p for p in problems))
        lv = level("cause_effect")
        lv["item_ids"] = []
        self.assertTrue(any("'item_ids' is needed" in p for p in gl.problems(lv)))

    def test_levels_become_one_mission_the_phone_runtime_plays(self):
        levels = [level(m) for m in ("find_partner", "build_timeline")]
        mission = gl.mission_of(levels, title="पैसा: खेल कर सीखो", intro="रामू के गाँव का बाज़ार।")
        self.assertEqual(len(mission["stages"]), 2)
        self.assertEqual(mission["replay_twist"], "shuffle_tokens")
        self.assertEqual(mission["item_ids"], ["p002-i2"])
        html = render_game_html({"id": "money-p1", "title": "पैसा", "world": "रामू का गाँव",
                                 "missions": [mission], "credits": []})
        self.assertIn("viewport", html)                          # phone-first page
        self.assertIn("__bot", html)                             # BIE's bot can play it
        self.assertIn("मोहन: कपड़ा है, गेहूँ चाहिए", html)
        self.assertIn("timeline टूट गई", html)
        with self.assertRaises(ValueError) as ctx:
            gl.mission_of([level("run_process", win="")], title="x")
        self.assertIn("'win' is needed", str(ctx.exception))


def bank_level(**extra):
    """place_right in the bank hall: each need goes to its counter (test data: Claude's demo, not BIE output)."""
    lv = level("place_right", instruction="हर ग्राहक की ज़रूरत सही काउंटर पर ले जाओ।",
               world={"kind": "bankHall", "signs": "जमा;निकासी;कर्ज़", "label": "बैंक"},
               pieces=[{"id": "save", "label": "₹5,000 बचाने हैं", "fits": "dep", "right": "जमा काउंटर: खाता बढ़ा।",
                        "wrong": "यहाँ पैसा जमा नहीं होता।"},
                       {"id": "cash", "label": "₹2,000 चाहिए अभी", "fits": "wd", "right": "निकासी: खाते से पैसा मिला।",
                        "wrong": "यहाँ से पैसा नहीं निकलता।"},
                       {"id": "loan", "label": "दुकान के लिए ₹1 लाख", "fits": "ln", "right": "कर्ज़ काउंटर: ब्याज पर पैसा।",
                        "wrong": "कर्ज़ यहाँ नहीं मिलता।"}],
               places=[{"id": "dep", "label": "जमा", "spot": "जमा"}, {"id": "wd", "label": "निकासी", "spot": "counter2"},
                       {"id": "ln", "label": "कर्ज़", "spot": "कर्ज़"}])
    lv.update(extra)
    return lv


class WorldLevels(unittest.TestCase):
    def test_a_level_in_a_world_puts_its_places_on_the_world_spots(self):
        lv = bank_level()
        self.assertEqual(formats.problems("game_level", lv), [])
        self.assertEqual(gl.problems(lv), [])
        stage = gl.stage_of(lv)
        self.assertEqual(stage["world"]["kind"], "bankHall")
        self.assertEqual([t.get("spot") for t in stage["targets"]], ["जमा", "counter2", "कर्ज़"])
        plain = dict(stage, targets=[{k: v for k, v in t.items() if k != "spot"} for t in stage["targets"]])
        plain.pop("world")
        validate(plain, STAGE_SCHEMA)                       # beyond world and spot, the runtime's stage shape exactly
        html = render_game_html({"id": "bank", "title": "बैंक", "world": "", "missions": [gl.mission_of([lv], title="बैंक")], "credits": []})
        self.assertIn("window.BIEWorld = (", html)         # the videos' world drawing, inside the phone page
        self.assertIn("worldSpots", html)
        plain_html = render_game_html({"id": "m", "title": "m", "world": "", "missions": [gl.mission_of([level("place_right")], title="m")], "credits": []})
        self.assertFalse("window.BIEWorld = (" in plain_html, "a page without a world stays small")

    def test_a_wrong_world_or_spot_is_named_exactly(self):
        bad = bank_level()
        bad["places"][1]["spot"] = "counter9"
        self.assertTrue(any("spot 'counter9' is not in the bankHall world" in p for p in gl.problems(bad)), gl.problems(bad))
        bad = bank_level(world={"kind": "moon"})
        self.assertTrue(any("world: world.kind" in p for p in gl.problems(bad)), gl.problems(bad))
        bad = bank_level()
        bad.pop("world")
        self.assertTrue(any("has a spot but the level has no world" in p for p in gl.problems(bad)))
        bad = bank_level(world="bank")
        self.assertTrue(any("'world' must be a JSON object" in p for p in gl.problems(bad)))

    @unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
    def test_python_and_the_drawing_name_the_same_spots(self):
        worlds = [{"kind": k} for k in gl._FIXED_SPOTS] + [
            {"kind": "bankHall", "signs": "जमा;निकासी;कर्ज़;vault;जमा"}, {"kind": "market", "count": 6}, {"kind": "market", "signs": "a"},
            {"kind": "office", "signs": "a;b;c;d;e;f;g;h"}, {"kind": "factory", "signs": "x;y"}, {"kind": "city", "signs": "दुकान;बैंक;होटल;x"},
            {"kind": "bankHall", "count": 5, "signs": "a;b"}, {"kind": "nowhere"}]
        engine = ROOT / "bie" / "brain" / "video" / "engine" / "worlds.mjs"
        script = (f"import {{worldSpots}} from '{engine.as_posix()}';"
                  f"const ws = {json.dumps(worlds, ensure_ascii=False)};"
                  "console.log(JSON.stringify(ws.map((w) => worldSpots(w))));")
        out = json.loads(subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout)
        for w, spots in zip(worlds, out):
            with self.subTest(world=w):
                self.assertEqual(list(spots), gl.world_spot_names(w))
                for box in spots.values():
                    self.assertTrue(0 <= box["x"] <= 1 and 0 <= box["y"] <= 1 and box["w"] > 0 and box["h"] > 0, box)
                    self.assertLessEqual(box["x"] + box["w"], 1.0001)
                    self.assertLessEqual(box["y"] + box["h"], 1.0001)


if __name__ == "__main__":
    unittest.main()


class ActAsAndPredict(unittest.TestCase):
    """The two mechanics learned from the economy reference videos (4 Nov 2026), on the branch and slider engines."""

    def act_as(self, **extra):
        lv = {"schema": "bie.game-level/1", "level_id": "repo-act", "title": "RBI", "mechanic": "act_as",
              "instruction": "Aap RBI ho: mehngai badh rahi hai. Kya karoge?", "role": "RBI",
              "situation": "Mehngai 7% par, lakshya 4%.", "win": "Mehngai kaabu mein.", "item_ids": ["p004-i1"],
              "choices": [{"label": "Repo rate badhao", "correct": True, "feedback": "Karz mehnga, maang ghati."},
                          {"label": "Repo rate ghatao", "correct": False, "feedback": "Karz sasta, maang aur badhi: mehngai badhi."}]}
        lv.update(extra)
        return lv

    def predict(self, **extra):
        lv = {"schema": "bie.game-level/1", "level_id": "crr-predict", "title": "CRR", "mechanic": "predict",
              "instruction": "Rs 100 jama hue. CRR 3% hai: RBI ki tijori mein kitna jayega?", "win": "Sahi andaaza.",
              "item_ids": ["p005-i2"], "feedback_close": "Haan: 3% of 100 = 3.", "feedback_far": "CRR jama ka chhota hissa hai.",
              "slider": {"label": "Tijori mein", "unit": "Rs", "min": 0, "max": 50, "step": 1, "answer": 3, "tolerance": 1,
                         "predict_prompt": "Andaaza lagao", "reveal_label": "Sahi jawab"}}
        lv.update(extra)
        return lv

    def test_valid_levels_have_no_problems_and_lower_to_the_runtime_engines(self):
        self.assertEqual(gl.problems(self.act_as()), [])
        self.assertEqual(gl.problems(self.predict()), [])
        branch, slider = gl.stage_of(self.act_as()), gl.stage_of(self.predict())
        self.assertEqual((branch["kind"], slider["kind"]), ("branch", "slider"))
        self.assertTrue(branch["situation"].startswith("RBI: "))
        self.assertEqual(slider["slider"]["answer"], 3.0)
        for stage in (branch, slider):
            self.assertTrue(validate(stage, STAGE_SCHEMA), stage["kind"])
        for lv in (self.act_as(), self.predict()):
            self.assertEqual(formats.problems("game_level", lv), [], lv["mechanic"])
        mission = gl.mission_of([self.act_as(), self.predict(), level("run_process")], title="Paisa")
        self.assertEqual([s["kind"] for s in mission["stages"]], ["branch", "slider", "drag"])

    def test_wrong_levels_are_named_exactly(self):
        self.assertIn("at least one choice must be wrong", " ".join(gl.problems(self.act_as(choices=[
            {"label": "a", "correct": True, "feedback": "x"}, {"label": "b", "correct": True, "feedback": "y"}]))))
        self.assertIn("'role' is needed", " ".join(gl.problems(self.act_as(role=""))))
        self.assertIn("choice 2 needs 'feedback'", " ".join(gl.problems(self.act_as(choices=[
            {"label": "a", "correct": True, "feedback": "x"}, {"label": "b", "correct": False}]))))
        self.assertIn("answer inside the range", " ".join(gl.problems(self.predict(slider={**self.predict()["slider"], "answer": 99}))))
        self.assertIn("'feedback_far' is needed", " ".join(gl.problems(self.predict(feedback_far=""))))
        self.assertIn("'slider' is needed", " ".join(gl.problems(self.predict(slider=None))))
