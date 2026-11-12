"""Readable words in BIE's drawings (Sloman notes and videos, Nov 2026): a saancha's own words never shrink under the
36 px floor at the drawing's w (a long name wraps instead), the graph keeps a line whose name has a ':' in it, the
said-must-be-shown check reads Hindi verbs, aliases and drawn ideas correctly, maths letters are not English, the
EconGraph draws a vertical curve, and the box rule measures loose captions and a world's zones only in its own time."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain.video import box_rules, boxes, shown_said, showplan  # noqa: E402
from bie.brain.video.econ_graph import EconGraph  # noqa: E402

FLOOR = box_rules.FLOOR_PX - 0.5


def words(draw, p):
    return [w for w in boxes.item(draw, p).get("texts") or [] if not box_rules.is_symbol(w["t"])]


def px_of(draw, p):
    return {w["t"]: w["px"] for w in words(draw, p)}


class GraphWords(unittest.TestCase):
    G = {"w": 1200, "xLabel": "मात्रा", "yLabel": "कीमत", "xTicks": "2:Q1;5:Q2;7:Qmax", "yTicks": "4:P1;6:P2",
         "lines": "D:1,9 5,5 9,1;S:1,1 5,5 9,9", "ticks": True}

    def test_tick_names_and_axis_numbers_reach_the_floor_at_w_1200(self):
        got = px_of("graph", self.G)
        for t in ("Q1", "Q2", "Qmax", "P1", "P2", "0", "10"):
            self.assertGreaterEqual(got[t], FLOOR, (t, got))

    def test_two_panel_graphs_keep_the_floor(self):
        for w in (600, 900):
            low = min(w_["px"] for w_ in words("graph", dict(self.G, w=w)))
            self.assertGreaterEqual(low, FLOOR, w)

    def test_a_long_line_name_wraps_instead_of_shrinking(self):
        got = px_of("graph", dict(self.G, lines="Demand curve:1,9 5,5 9,1;DAS (short run):1,2 9,8"))
        self.assertIn("Demand", got)
        self.assertIn("curve", got)
        self.assertNotIn("Demand curve", got)
        self.assertTrue(all(v >= FLOOR for v in got.values()), got)

    def test_a_colon_inside_a_line_name_keeps_the_whole_line(self):
        plain = boxes.item("graph", dict(self.G, lines="S:1,1 5,5 9,9", xTicks="", yTicks="", ticks=False))
        named = boxes.item("graph", dict(self.G, lines="S: supply:1,1 5,5 9,9", xTicks="", yTicks="", ticks=False))
        self.assertIn("S: supply", [w["t"] for w in named["texts"]])
        self.assertEqual(plain["body"], named["body"])             # the same line, from (1,1): not cut to its last points

    def test_a_short_y_label_is_drawn_upright_at_full_size(self):
        svg_free = boxes.item("graph", dict(self.G, yLabel="₹"))
        r = [w for w in svg_free["texts"] if w["t"] == "₹"][0]
        self.assertGreaterEqual(r["px"], FLOOR)
        self.assertLess(r["box"][2] - r["box"][0], 60)              # upright: as wide as one sign, not a sideways strip


class OtherDrawings(unittest.TestCase):
    def test_fork_words_reach_the_floor_at_its_default_w(self):
        p = {"from": "ब्याज दर (interest rate)", "up": "बढ़ाओ (raise)", "upNote": "जब महँगाई ऊँची हो", "upResult": "खर्च घटता है",
             "down": "घटाओ (cut)", "downNote": "जब मंदी हो", "downResult": "निवेश बढ़ता है"}
        self.assertTrue(all(w["px"] >= FLOOR for w in words("fork", p)), px_of("fork", p))

    def test_calendar_heading_and_podium_names_reach_the_floor(self):
        self.assertGreaterEqual(px_of("calendar", {"w": 200, "text": "मार्च"})["मार्च"], FLOOR)
        got = px_of("podium", {"labels": "Gold;Silver;Bronze"})
        self.assertTrue(all(got[k] >= FLOOR for k in ("Gold", "Silver", "Bronze")), got)

    def test_a_heading_that_cannot_fit_is_reported_by_the_readable_width(self):
        mw = box_rules.min_readable_w("calendar", {"w": 200, "text": "Day thirty of the month"})
        self.assertGreater(mw["w"], 200)

    def test_paper_takes_amount_and_footer(self):
        got = px_of("paper", {"w": 400, "kind": "report", "title": "RBI", "amount": "₹50 cr", "footer": "2024"})
        self.assertIn("₹50 cr", got)
        self.assertIn("2024", got)

    def test_ticket_slip_shows_its_rows(self):
        got = px_of("slip", {"kind": "ticket", "w": 600, "title": "Permit", "rows": "Price:€80;Year:2024"})
        for t in ("Price", "€80", "Year", "2024"):
            self.assertIn(t, got)

    def test_marginal_bars_read_comma_labels_one_per_bar(self):
        got = boxes.item("marginalBars", {"values": "7;4;2", "labels": "first,second,third"})
        self.assertTrue({"first", "second", "third"} <= {w["t"] for w in got["texts"]})

    def test_gap_bars_put_the_rupee_first_and_do_not_repeat_the_gap(self):
        t = [w["t"] for w in boxes.item("gapBars", {"a": "Spending:500", "b": "Revenue:300", "unit": "₹", "gap": "deficit ₹200"})["texts"]]
        self.assertIn("₹500", t)
        self.assertIn("deficit ₹200", t)
        self.assertFalse(any("200₹" in x for x in t), t)
        t2 = [w["t"] for w in boxes.item("gapBars", {"a": "A:500", "b": "B:300", "unit": "₹", "gap": "deficit"})["texts"]]
        self.assertIn("deficit ₹200", t2)

    def test_a_long_price_stays_inside_its_tag(self):
        got = boxes.item("priceTag", {"value": "₹1,20,000"})
        word = [w for w in got["texts"] if w["t"] == "₹1,20,000"][0]
        self.assertGreaterEqual(word["box"][0], got["body"][0])
        self.assertLessEqual(word["box"][2], got["body"][2])

    def test_note_bundle_band_leaves_the_value_clear(self):
        got = boxes.item("noteBundle", {"w": 500, "value": 2000})
        v = [w for w in got["texts"] if w["t"] == "2000"][0]
        self.assertGreater(v["box"][0], -500 * 0.355)               # the band ends at x = -0.355 w

    def test_agents_words_reach_the_floor(self):
        self.assertTrue(all(w["px"] >= FLOOR for w in words("agents", {"mode": "belief", "label": "prices rise", "w": 800})))


class SaidShown(unittest.TestCase):
    def setUp(self):
        self.lex = shown_said.lexicon()

    def tags(self, text):
        return [t for _, t, _ in shown_said.named_things(text, self.lex)]

    def test_hindi_verb_forms_are_not_things(self):
        for line in ("हम काम करते हैं", "इसे कर लें", "काम करो", "वह कर पाता है", "कर दो", "लोग खाना खाते हैं", "वह खाता है",
                     "ज़मीन सूखा है", "उत्पादन बढ़ा", "जोखिम बड़ा है"):
            self.assertNotIn("कर", self.tags(line), line)
            self.assertNotIn("खाता", self.tags(line), line)
            self.assertNotIn("उत्पादन", self.tags(line), line)
        self.assertIn("कर", self.tags("सरकार कर बढ़ाती है"))
        self.assertIn("खाता", self.tags("बैंक खाता खोलो"))

    def shown(self, els, tag, names):
        spec = {"scenes": [{"t0": 0, "t1": 2, "els": [dict(e, t0=0, t1=2) for e in els]}]}
        return shown_said._shown_seconds(spec, 0, 1, tag, names)

    def test_a_label_in_the_other_language_shows_the_thing(self):
        self.assertGreater(self.shown([{"draw": "building", "p": {"label": "कारखाना"}}], "factory", ["factory"]), 0)
        self.assertGreater(self.shown([{"draw": "priceTag", "p": {"value": "डीज़ल"}}], "diesel", ["oilTin"]), 0)
        self.assertEqual(self.shown([{"draw": "building", "p": {"label": "घर"}}], "factory", ["factory"]), 0)

    def test_a_label_on_any_drawing_shows_the_thing(self):
        self.assertGreater(self.shown([{"draw": "priceTag", "p": {"value": "बैंक"}}], "बैंक", ["bank"]), 0)
        self.assertEqual(self.shown([{"kind": "text", "text": "बैंक"}], "बैंक", ["bank"]), 0)   # plain words alone are not the thing

    def test_ideas_shown_by_a_drawing(self):
        self.assertGreater(self.shown([{"draw": "gapBars", "p": {"a": "x:1", "b": "y:2"}}], "shortage", ["queueLine"]), 0)
        self.assertGreater(self.shown([{"draw": "graph", "p": {"gaps": "3,7@4:कमी"}}], "कमी", ["queueLine"]), 0)
        self.assertGreater(self.shown([{"draw": "slip", "p": {"kind": "rationCard"}}], "rationing", ["queueLine"]), 0)
        self.assertEqual(self.shown([{"draw": "graph", "p": {}}], "shortage", ["queueLine"]), 0)


class MathsLetters(unittest.TestCase):
    def test_maths_letters_are_not_english(self):
        for t in ("a", "b", "Qd", "Ps", "Pe", "Qe", "d/dQ", "a-c", "MC = MR"):
            self.assertFalse(box_rules.english_label(t), t)
        for t in ("price", "is it", "demand curve"):
            self.assertTrue(box_rules.english_label(t), t)


class VerticalCurve(unittest.TestCase):
    def test_perfectly_inelastic_supply(self):
        g = EconGraph()
        D = g.linear("D", intercept=9, slope=-0.8)
        S = g.vertical("S", 5)
        E = g.cross(D, S, "E")
        self.assertAlmostEqual(E.x, 5.0)
        self.assertAlmostEqual(E.y, 5.0)
        self.assertEqual(g.at_price(S, 3), 5.0)
        g.shift(S, dx=2)
        lines = g.params()["lines"]
        self.assertIn("S:5,0 5,10", lines)
        self.assertIn("S2:7,0 7,10", lines)
        self.assertIn("vertical()", str(self._through_error()))

    def _through_error(self):
        try:
            EconGraph().through("S", (5, 0), (5, 10))
        except ValueError as exc:
            return exc
        return None


class BoxRuleTiming(unittest.TestCase):
    def spec(self):
        from tests.test_p1_box_rule import plan_of, timeline
        plan = plan_of({"op": "item", "id": "w", "thing": {"draw": "world", "p": {"kind": "bankHall"}}, "x": 960, "y": 540, "s": 0.5},
                       {"op": "item", "thing": {"draw": "coin", "p": {}}, "x": 1277, "y": 498})
        return showplan.compile_plan(json.loads(json.dumps(plan)), timeline(), width=1920, height=1080, box_rule=False,
                                     said_shown=False)

    def test_a_world_zone_counts_only_while_the_world_is_on_screen(self):
        spec = self.spec()
        hit = [p for p in box_rules.problems(copy.deepcopy(spec)) if "vault" in p]
        self.assertTrue(hit)                                         # the coin on the vault while the world shows
        sc = spec["scenes"][0]
        world = [e for e in sc["els"] if e.get("draw") == "world"][0]
        coin = [e for e in sc["els"] if e.get("draw") == "coin"][0]
        world["t0"], coin["t1"] = 5.0, 4.5                           # the world arrives after the coin has gone
        self.assertFalse([p for p in box_rules.problems(spec) if "vault" in p])

    def test_a_caption_outside_a_things_body_is_measured(self):
        loose = box_rules.loose_local({"draw": "crowd", "p": {"label": "Buyers"}}, 0)
        self.assertEqual([w[0] for w in loose], ["Buyers"])
        self.assertEqual(box_rules.loose_local({"draw": "sack", "p": {"label": "गेहूँ"}}, 0), [])


if __name__ == "__main__":
    unittest.main()
