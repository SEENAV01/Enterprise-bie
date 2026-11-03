"""Phase 1, part B3: the game-level slot — five mechanics as code on the existing phone runtime.

Offline. The example levels here are test data (Claude's demo, not BIE output; BIE's AI writes real levels in
part C), never passed outputs.
"""
from __future__ import annotations

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
    def test_every_mechanic_has_a_valid_level_that_lowers_to_a_playable_stage(self):
        for mech in gl.MECHANICS:
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


if __name__ == "__main__":
    unittest.main()
