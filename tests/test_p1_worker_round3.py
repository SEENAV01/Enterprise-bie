"""Scene-plan worker fixes, round 3 (Sloman workers, Nov 2026): the said-shown check reads कर as a verb before any light
verb (punctuation too), लाइन as a queue only in a queue line, idioms and angles as no thing, Hindi aliases of economics
words, worlds and their signs as showing what they name; Roman cue words match whole words; drawings keep decimals as
given, write rupees with Indian commas, hide numbers nobody says and stand empty before their first part; the box rule
reads a wrapped "Hindi (English)" label as one label and lets a thing move in from off-screen; EconGraph draws Q = f(P)
curves, solid perfectly elastic/inelastic shifts, show=[] as no line and segments by number; timeline words keep 36 px."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain.video import box_rules, boxes, shown_said  # noqa: E402
from bie.brain.video.econ_graph import EconGraph  # noqa: E402
from bie.brain.video.narration import cue_positions  # noqa: E402

FLOOR = box_rules.FLOOR_PX - 0.5


def named(text):
    return [t for _, t, _ in shown_said.named_things(text)]


def texts(draw, p):
    return [w["t"] for w in boxes.item(draw, p)["texts"]]


def overlap(a, b):
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


class KarVerb(unittest.TestCase):
    def test_kar_before_any_light_verb_form_is_do(self):
        for line in ("सरकार ₹50 कम कर देंगी", "दाम कम कर दिए", "हम हिसाब कर लेंगे", "आप तुलना कर लीजिए", "अब फ़ैसला कर लें",
                     "इसे पूरा कर दो", "वे बचत कर सकते हैं", "लोग खरीदारी कर रहे थे", "आप यह कर दीजियेगा", "वह काम कर देगी",
                     "वह भुगतान कर देती है", "वे जमा कर देंगे", "वह पूरा कर चुका", "हम तय कर पाएँगे", "आप जाँच कर दीजिए"):
            self.assertNotIn("कर", named(line), line)

    def test_punctuation_after_the_helper_is_taken_off(self):
        for line in ("सरकार ₹50 कम कर दे।", "क्या आप कम कर देंगे?", "कम कर दो!", "कम कर लें, फिर देखें"):
            self.assertNotIn("कर", named(line), line)

    def test_real_tax_still_counts(self):
        for line in ("सरकार कर बढ़ाती है", "कर दर 10% है", "सरकार पेट्रोल पर कर लगाती है", "कर देय है", "कर दो प्रकार के होते हैं",
                     "यह कर।"):
            self.assertIn("कर", named(line), line)

    def test_khaata_as_eats_and_as_account(self):
        self.assertNotIn("खाता", named("वह रोज़ समोसा खाता है"))
        self.assertIn("खाता", named("बैंक में उसका खाता खुला"))


class ContextWords(unittest.TestCase):
    def test_line_of_text_is_not_a_queue(self):
        self.assertEqual(named("तीन लाइन में लिखिए"), [])
        self.assertIn("लाइन", named("लोग राशन की लाइन में खड़े हैं"))

    def test_idiom_demands_no_dice(self):
        self.assertNotIn("पासा", named("अब पासा पलटिए"))
        self.assertNotIn("पासा", named("और पासा पलट गया"))
        self.assertIn("पासा", named("वह पासा फेंकता है"))

    def test_degree_as_angle_is_no_certificate(self):
        for line in ("45 डिग्री की रेखा खींचिए", "45 degree line", "ग्राफ़ पर कोण 30 डिग्री है"):
            self.assertEqual([t for t in named(line) if t in ("डिग्री", "degree")], [], line)
        self.assertIn("डिग्री", named("उसने कॉलेज से डिग्री ली"))


class Aliases(unittest.TestCase):
    def test_economics_words_have_hindi_aliases(self):
        for eng, hin in (("marginal cost", "सीमांत लागत"), ("offer", "प्रस्ताव"), ("offer", "ऑफ़र"), ("account", "खाता"),
                         ("insurance", "बीमा"), ("demand", "माँग"), ("supply", "आपूर्ति"), ("subsidy", "सब्सिडी"),
                         ("tariff", "शुल्क"), ("profit", "मुनाफ़ा"), ("interest", "ब्याज")):
            self.assertIn(hin, shown_said.aliases(eng), (eng, hin))
            self.assertIn(eng, shown_said.aliases(hin), (eng, hin))

    def test_a_hindi_label_shows_the_english_word_said(self):
        spec = {"scenes": [{"t0": 0, "t1": 4, "els": [{"draw": "sack", "p": {"label": "बीमा"}}]}]}
        self.assertGreaterEqual(shown_said._shown_seconds(spec, 0, 4, "insurance", ["insurancePool"]), 3.5)
        spec = {"scenes": [{"t0": 0, "t1": 4, "els": [{"draw": "sack", "p": {"label": "बैंक खाते"}}]}]}
        self.assertGreaterEqual(shown_said._shown_seconds(spec, 0, 4, "account", ["accountCard"]), 3.5)


class WorldsShow(unittest.TestCase):
    def spec(self, kind, **p):
        return {"scenes": [{"t0": 0, "t1": 4, "bg": "paper", "els": [{"draw": "world", "p": dict(kind=kind, **p)}]}]}

    def test_a_world_kind_shows_its_own_name(self):
        self.assertGreater(shown_said._shown_seconds(self.spec("petrolPump"), 0, 4, "पंप", ["pump"]), 3)
        self.assertGreater(shown_said._shown_seconds(self.spec("petrolPump"), 0, 4, "petrol pump", ["pump"]), 3)
        self.assertGreater(shown_said._shown_seconds(self.spec("foodStreet"), 0, 4, "गली", ["street"]), 3)

    def test_its_signs_show_what_they_name(self):
        self.assertGreater(shown_said._shown_seconds(self.spec("market", signs="सब्ज़ी;चाय"), 0, 4, "चाय", ["tea"]), 3)

    def test_a_world_still_shows_no_object_it_does_not_draw_or_write(self):
        self.assertEqual(shown_said._shown_seconds(self.spec("bankHall"), 0, 4, "सिक्का", ["coin"]), 0)


class RomanCues(unittest.TestCase):
    def test_roman_cue_matches_whole_words_only(self):
        self.assertEqual(cue_positions("extra cost", "TR"), [])
        self.assertEqual(cue_positions("TR और MC", "TR"), [0])
        self.assertEqual(cue_positions("MCQ में MC", "MC"), [8])
        self.assertEqual(cue_positions("prices rise", "price"), [0])        # a plural still counts

    def test_devanagari_cue_keeps_the_stem_match(self):
        self.assertEqual(cue_positions("खरीदारों को", "खरीद"), [0])


class DrawnNumbers(unittest.TestCase):
    def test_gamble_tree_keeps_given_decimals(self):
        got = texts("gambleTree", {"branches": "जीत:1/2:100.50;हार:1/2:0", "unit": "₹", "sure": "पक्का:16.20"})
        for t in ("जीत ₹100.50", "पक्का ₹16.20", "EV ₹50.25", "0.5 × 100.50 = 50.25"):
            self.assertIn(t, got)
        self.assertIn("EV ₹50", texts("gambleTree", {"branches": "a:0.5:100;b:0.5:0", "unit": "₹"}))   # whole numbers stay whole

    def test_time_value_keeps_decimals_and_takes_a_factor_per_lane(self):
        self.assertIn("₹1.50", texts("timeValue", {"amounts": "1.50@1", "unit": "₹"}))
        got = texts("timeValue", {"amounts": "16.20@2", "unit": "₹", "travel": 1, "d": "0.9;0.8"})
        self.assertIn("d = 0.9", got)
        self.assertIn("d = 0.8", got)
        self.assertIn("₹13.12", got)                                    # 16.20 x 0.9^2
        self.assertIn("₹10.37", got)                                    # 16.20 x 0.8^2

    def test_rupees_get_indian_commas(self):
        got = texts("gapBars", {"a": "माँग:30000", "b": "आपूर्ति:100000", "unit": "₹"})
        self.assertIn("₹30,000", got)
        self.assertIn("₹1,00,000", got)
        self.assertIn("₹1,00,000", texts("pump", {"price": 100000}))

    def test_tug_of_war_can_hide_its_share_numbers(self):
        self.assertIn("60%", texts("tugOfWar", {"share": 0.6}))
        self.assertEqual([t for t in texts("tugOfWar", {"share": 0.6, "shareNumbers": False}) if "%" in t], [])

    def test_numbers_nobody_says_can_stay_off(self):
        self.assertEqual(texts("pump", {"price": 96.5, "priceBoard": False}), [])
        got = texts("marginalBars", {"values": "7;4;2", "numbers": False, "line": "3:मज़दूरी", "tower": "beside",
                                     "towerLabel": "कुल"})
        self.assertFalse([t for t in got if any(c.isdigit() for c in t) and t not in ("1", "2", "3")], got)

    def test_gap_tag_does_not_cover_the_other_bars_value(self):
        it = boxes.item("gapBars", {"w": 520, "a": "पूर्ति:90", "b": "माँग:100", "unit": "₹", "gap": "कमी"})
        words = {w["t"]: w["box"] for w in it["texts"]}
        self.assertEqual(overlap(words["कमी ₹10"], words["₹100"]), 0)


class EmptyFirst(unittest.TestCase):
    def test_upto_minus_one_stands_empty(self):
        self.assertEqual(texts("table", {"cols": "a;b", "cells": "1;2|3;4", "upto": -1}), ["a", "b"])
        self.assertEqual(texts("timeline", {"events": "1991:उदारीकरण;2016:नोटबंदी", "upto": -1}), [])
        self.assertNotIn("₹7", texts("barChart", {"bars": "a:7;b:4", "unit": "₹", "upto": -1}))
        self.assertIn("1;2", "1;2")                                      # upto 0 is still all:
        self.assertIn("3", texts("table", {"cols": "a;b", "cells": "1;2|3;4", "upto": 0}))

    def test_pie_slices_in_any_order(self):
        first = texts("pieChart", {"slices": "a:10;b:20;c:70", "upto": 1, "order": "3", "legend": False})
        self.assertIn("70%", first)
        self.assertNotIn("10%", first)


class BoxRuleWords(unittest.TestCase):
    def test_a_wrapped_bracket_half_is_judged_with_its_label(self):
        el = {"draw": "graph", "p": {"lines": "माँग (demand):1,9 9,1", "xTicks": "4:45 डिग्री (degree)"}}
        labels = box_rules.label_strings(el, 0)
        for half in ("(demand)", "(degree)"):
            self.assertTrue(box_rules.english_label(half))
            self.assertTrue(box_rules.wrapped_hindi(half, labels), half)
        self.assertFalse(box_rules.wrapped_hindi("Demand", box_rules.label_strings({"draw": "graph", "p": {"lines": "Demand:1,9 9,1"}}, 0)))

    def test_graph_bracket_labels_draw_their_halves(self):
        got = texts("graph", {"w": 1100, "lines": "माँग (demand):1,9 5,5 9,1", "xTicks": "5:संतुलन (equilibrium)"})
        self.assertTrue(any("(" in t for t in got))

    def test_a_thing_moving_in_is_not_cut_while_it_moves(self):
        el = {"draw": "sack", "x": -300, "y": 600, "keys": [{"t": 1.0, "x": 500, "d": 1.2}]}
        self.assertFalse(box_rules.moving_at(el, 0.5))
        self.assertTrue(box_rules.moving_at(el, 1.5))
        self.assertFalse(box_rules.moving_at(el, 2.5))
        self.assertFalse(box_rules.moving_at({"draw": "sack", "keys": [{"t": 1.0, "s": 2}]}, 1.2))   # a zoom is no entry


class EconGraphMore(unittest.TestCase):
    def test_backward_bending_supply_from_q_of_p(self):
        g = EconGraph(xmax=10, ymax=10)
        S = g.of_price("S", lambda p: 8 - 0.32 * (p - 5) ** 2 if p > 0 else 0, p0=0.5, p1=9.5)
        pts = [tuple(map(float, q.split(","))) for q in g._pts(S).split()]
        ps = [p for _, p in pts]
        self.assertEqual(ps, sorted(ps))                                 # ordered along the curve (by P), not by Q
        qs = [q for q, _ in pts]
        self.assertLess(qs.index(max(qs)), len(qs) - 1)                  # it bends back: Q rises then falls
        self.assertAlmostEqual(g.at_price(S, 5), 8.0)
        D = g.linear("D", intercept=10, slope=-1)
        E = g.cross(D, S, "E")
        self.assertAlmostEqual(E.x + E.y, 10, places=3)
        self.assertAlmostEqual(E.x, 8 - 0.32 * (E.y - 5) ** 2, places=3)
        S2 = g.shift(S, dx=1)
        self.assertAlmostEqual(g.at_price(S2, 5), 9.0)

    def test_flat_and_vertical_shifts_stay_solid(self):
        g = EconGraph()
        D = g.horizontal("D", 5)
        S = g.vertical("S", 4)
        L = g.linear("L", intercept=9, slope=-1)
        g.shift(D, dy=1)
        g.shift(S, dx=1)
        g.shift(L, dx=1)
        self.assertEqual(g.params()["dashed"], "6")                      # only the shifted slope
        h = EconGraph()
        h.shift(h.horizontal("D", 5), dy=2, dashed=True)
        self.assertEqual(h.params()["dashed"], "2")                      # a dash only when asked

    def test_show_empty_draws_no_line(self):
        g = EconGraph()
        g.linear("D", intercept=9, slope=-1)
        self.assertEqual(g.params(show=[])["show"], "none")
        named_all = texts("graph", g.params())
        self.assertIn("D", named_all)
        self.assertNotIn("D", texts("graph", g.params(show=[])))        # the line and its name are not drawn

    def test_segments_by_number(self):
        g = EconGraph()
        a = g.seg((1, 1), (2, 2), "a")
        b = g.seg((3, 3), (4, 4), "b")
        self.assertEqual((a, b), (1, 2))
        self.assertEqual(g.params(segs=[b])["segs"], "3,3>4,4:b")
        self.assertNotIn("segs", g.params(segs=[]))
        self.assertEqual(g.params()["segs"].count(";"), 1)


class ReadableTimeline(unittest.TestCase):
    def test_timeline_words_keep_the_floor_at_w_1900_and_1200(self):
        p = {"events": "आज:₹100 की बचत;1 साल:ब्याज जुड़ा;2 साल:फिर ब्याज जुड़ा;3 साल:पैसा दोगुना होने लगा;4 साल:नई कार खरीदी;"
                       "5 साल:घर का सपना;6 साल:सेवानिवृत्ति योजना;7 साल:अंत", "zones": "", "title": "बचत की कहानी"}
        for w in (1900, 1200):
            low = min(x["px"] for x in boxes.item("timeline", dict(p, w=w))["texts"])
            self.assertGreaterEqual(low, FLOOR, w)

    def test_graph_ticks_and_segments_keep_the_floor_at_w_1100(self):
        p = {"w": 1100, "xLabel": "मात्रा", "yLabel": "कीमत", "lines": "D:1,9 9,1;S:1,1 9,9", "xTicks": "2:कम घंटे;6:Q3",
             "yTicks": "8:ऊँची मज़दूरी", "segs": "2,8>8,2:सीमांत लागत रेखा", "ticks": True}
        low = min(x["px"] for x in boxes.item("graph", p)["texts"])
        self.assertGreaterEqual(low, FLOOR)


class Round3Extras(unittest.TestCase):
    def test_soviet_union_is_a_country_not_a_trade_union(self):
        for line in ("सोवियत संघ टूट गया", "the Soviet Union collapsed", "European Union rules"):
            self.assertFalse([t for t in named(line) if t in ("संघ", "union", "यूनियन")], line)
        self.assertIn("यूनियन", named("मज़दूर यूनियन ने हड़ताल की"))

    def test_cause_chain_chips_show_what_they_name(self):
        spec = {"scenes": [{"t0": 0, "t1": 4, "els": [{"draw": "causeChain", "p": {"links": "पेट्रोल|up;किराया|up"}}]}]}
        self.assertGreaterEqual(shown_said._shown_seconds(spec, 0, 4, "petrol", ["pump"]), 3.5)

    def test_subscripts_keep_the_floor(self):
        for draw, p in (("causeChain", {"w": 1600, "links": "D_g बढ़ी|up;कीमत बढ़ी|up;S_g बढ़ी|up", "until": "जब तक D_g = S_g"}),
                        ("formula", {"w": 1200, "terms": "D_g = C + I_p + G"})):
            low = min(x["px"] for x in boxes.item(draw, p)["texts"])
            self.assertGreaterEqual(low, FLOOR, draw)

    def test_compact_timeline_is_short_and_close_years_never_collide(self):
        it = boxes.item("timeline", {"w": 1600, "compact": True,
                                     "events": "1917:क्रांति;1921:नई आर्थिक नीति;1985:पेरेस्त्रोइका;1989:दीवार गिरी;1993:नया दौर"})
        self.assertLess(it["box"][3] - it["box"][1], 250)
        bs = [w["box"] for w in it["texts"]]
        self.assertTrue(all(w["px"] >= FLOOR for w in it["texts"]))
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                self.assertEqual(overlap(bs[i], bs[j]), 0, (it["texts"][i]["t"], it["texts"][j]["t"]))


if __name__ == "__main__":
    unittest.main()
