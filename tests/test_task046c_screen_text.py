"""Task 046 Part C · Navin's verdict on Money v1 (29 October 2026): on-screen text that reads complete and is explained
(CV-13 … CV-16, ``bie/brain/video/screen_text.py`` in the director's plan check) and narration that speaks like a teacher
(S2-09, ``soul.state_report_problems`` in the script check). Offline: fixtures, no network, no keys, no money.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import canvas_director, regression, rulebook, soul  # noqa: E402
from bie.brain.video import screen_text as st, world  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "task046c"
BEATS = [{"beat_id": "b2", "say": "किराना दुकान में आपके पास पहले 500 रुपये थे, चावल के 100 दिए, अब 400 बचे। दुकानदार ने payment ली।"},
         {"beat_id": "b7", "say": "Money की पहली खूबी acceptability है: दुकानदार payment में लेता है। दूसरी durability: सिक्का खराब नहीं होता।"}]


def say(beat_id):
    return next(b["say"] for b in BEATS if b["beat_id"] == beat_id)


class ScreenText(unittest.TestCase):
    def test_symbol_codes_unfinished_lines_and_code_lists_are_refused(self):
        p = st.text_problems("Exchange ✓ · Account ✓\nStore · Deferred", say("b7"), where="board.step1", beat_id="b7")
        self.assertTrue(any("symbol code" in x and "(CV-13)" in x for x in p), p)
        p = st.text_problems("1–3 ✓, 4 Future payment →", say("b7"), where="x", beat_id="b7")
        self.assertTrue(any("unfinished" in x for x in p), p)
        p = st.text_problems("EMI amount agreed\n≠\nActual payment", say("b7"), where="x", beat_id="b7")
        self.assertTrue(any("symbol code" in x for x in p) and any("unfinished" in x for x in p), p)
        p = st.text_problems("Exchange · Account · Store · Deferred", say("b7"), where="x", beat_id="b7")
        self.assertTrue(any("list of codes" in x for x in p), p)
        self.assertFalse(st.code_list("PPI · Producer Price Index"))                 # two parts: a label, not a list

    def test_a_text_the_narration_does_not_say_is_refused_and_a_spoken_one_passes(self):
        p = st.text_problems("Money = balance\nDevice ≠ money", say("b2"), where="board.step2", beat_id="b2")
        self.assertTrue(any("(CV-14)" in x and "not explained" in x for x in p), p)
        self.assertEqual(st.text_problems("Money की खूबी: acceptability", say("b7"), where="board.step1", beat_id="b7"), [])
        self.assertEqual(st.text_problems("सिक्का खराब नहीं होता", say("b7"), where="x", beat_id="b7"), [])
        self.assertEqual(st.text_problems("दुकान", say("b2"), where="shop.label", role="label", beat_id="b2"), [])   # a label is exempt

    def test_numbers_on_screen_are_the_narrations_numbers(self):
        self.assertEqual(st.text_problems("पहले ₹500, अब ₹400 बचे", say("b2"), where="board.step1", beat_id="b2"), [])
        p = st.text_problems("Payments: 0 → Payments: 2", say("b2"), where="board.step3", beat_id="b2")
        self.assertTrue(any("(CV-16)" in x and "0, 2" in x for x in p), p)
        p = st.text_problems("₹10,000", say("b2"), where="tag.step1", role="label", beat_id="b2")
        self.assertTrue(any("10000" in x and "(CV-16)" in x for x in p), p)

    def test_a_caveat_is_shown_once_per_part(self):
        texts = [{"id": "l1", "cue": ["b2", "पहले"], "text": "काल्पनिक बाज़ार, असली data नहीं", "role": "label"},
                 {"id": "l2", "cue": ["b7", "Money"], "text": "Illustrative numbers, not a forecast", "role": "label"}]
        p = st.problems(texts, BEATS)
        self.assertTrue(any("(CV-15)" in x and "l1, l2" in x for x in p), p)

    def test_the_rows_of_a_world_and_a_canvas_plan_are_found(self):
        plan = json.loads((FIXTURES / "store_of_value_world.world.json").read_text(encoding="utf-8"))
        rows = st.world_texts(plan)
        self.assertTrue(any(r["id"].startswith("khata.step") for r in rows))
        self.assertTrue(all(set(r) >= {"id", "cue", "text", "role"} for r in rows))
        plan = json.loads((FIXTURES / "real_gdp.plan.json").read_text(encoding="utf-8"))
        rows = st.canvas_texts(plan)
        self.assertTrue(any(r["id"] == "tab.columns" and r["role"] == "label" for r in rows))
        self.assertTrue(any(r["id"].startswith("tab.row") and r["role"] == "text" for r in rows))

    def test_the_director_refuses_a_code_board_and_accepts_a_spoken_sentence(self):
        plan = json.loads((FIXTURES / "store_of_value_world.world.json").read_text(encoding="utf-8"))
        stub = {"id": plan["id"], "part_id": plan.get("part_id", "c01.1"), "beats": plan["beats"]}
        value = {"notes": {}, "elements": plan["elements"], "camera": plan["camera"]}
        board = next(e for e in value["elements"] if e["kind"] == "board")
        board["steps"][0]["text"] = "Savings ✓ · Future due ≠"
        problems = canvas_director.check_plan(stub, value, {"mode": "C", "kit": "bank"})
        self.assertTrue(any("(CV-13)" in p for p in problems), problems)
        # the same board with a sentence the beat says, and its number
        b = plan["beats"][1]
        board["steps"][0]["text"] = "खाते में ₹500 बचे"
        board["steps"][0]["cue"] = [b["beat_id"], b["say"].split()[0]]
        b["say"] = b["say"] + " खाते में 500 रुपये बचे।"
        problems = canvas_director.check_plan(stub, value, {"mode": "C", "kit": "bank"})
        self.assertEqual([p for p in problems if "(CV-1" in p and "khata.step1" in p], [], problems)

    def test_a_board_holds_a_complete_sentence_now(self):
        self.assertEqual((world.BOARD_LINES, world.BOARD_CHARS), (3, 40))
        lines = world.wrap_value("Payment में notes और coins के अलावा खाते का पैसा भी चलता है")
        self.assertLessEqual(len(lines), 3)
        self.assertTrue(all(len(line) <= 40 for line in lines))
        card = canvas_director.card_text(canvas_director.WORLD_CARD_PATH)
        self.assertIn("3 lines of 40 characters", card)
        self.assertIn("CV-13", card)
        self.assertIn("CV-13", canvas_director.card_text())


class TeacherNarration(unittest.TestCase):
    def test_a_state_report_is_sent_back_with_navins_sentence(self):
        beats = [{"beat_id": "b2", "say": "किराना दुकान में क्या हुआ? ₹100 देकर चावल लिए; cash ₹500 से ₹400 हुआ। बाकी debt ₹50 से ₹0 हुआ।"},
                 {"beat_id": "b24", "say": "Worker ने account में ₹500 बचाए; savings ₹0 से ₹500 हुईं।"},
                 {"beat_id": "b3", "say": "पहले आपके पास 500 रुपये थे, किराने के 100 दिए, अब 400 बचे।"}]
        problems = soul.state_report_problems(beats)
        self.assertEqual([p.split(":")[0] for p in problems], ["beat b2", "beat b24"])
        self.assertIn(soul.TEACHER_NUMBERS, problems[0])
        self.assertTrue(all(p.endswith("(S2-09)") for p in problems))

    def test_the_rulebook_carries_s2_09_and_the_teacher_example(self):
        book = rulebook.load()
        self.assertIn("vision-2026-10-21@2026-10-21.16", book.version)
        self.assertIn("canvas_profile@2026-10-29.1", book.version)
        self.assertIn("teacher_examples@2026-10-29.1", book.version)
        rules = {r.id: r for r in book.rules}
        self.assertIn("S2-09", rules)
        self.assertIn("banawati na lage", rules["S2-09"].rule)
        for rid in ("CV-13", "CV-14", "CV-15", "CV-16"):
            self.assertEqual(rules[rid].status, "locked", rid)
        method = next(m for m in soul.load_teacher()["methods"] if m["id"] == "real_world_application")
        self.assertEqual(method["good_narration"], soul.TEACHER_NUMBERS)
        self.assertTrue(any(c["rule"] == "S2-09" for c in regression.RULE_CHANGES))


if __name__ == "__main__":
    unittest.main()
