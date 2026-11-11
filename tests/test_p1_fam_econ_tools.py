"""Family econ_tools (Sloman economics book, 5 November 2026): the teaching tools its chapter workers asked for most.

formula, scaleBalance, causeChain, sorter, spectrum, padlocks, tugOfWar, oneVsAll, tAccount, choicePaths, incomeLine and
doorway are in the family manifest (saanche.d/econ_tools.json) with Hindi and English words and in the engine's registry;
they draw clean SVG at their defaults and in the states a scene plan uses, refuse parameters out of range, carry no words
of their own, and move as a pure function of _t and _s (the same parameters and times give the same SVG, so frames can be
drawn out of order). A few checks of meaning: the formula computes its result and levels its beam only when both sides
are equal, the balance tips to the heavier pan, the sorter crosses a wrong card before moving it, the ledger ticks
matching totals, the income line counts the people below it, and words keep to the box rule's 36 px (subscripts aside).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import saanche  # noqa: E402

ENGINE = ROOT / "bie" / "brain" / "video" / "engine"
FAMILY = ENGINE / "families" / "econ_tools.mjs"
MANIFEST = ENGINE / "saanche.d" / "econ_tools.json"
NAMES = ["formula", "scaleBalance", "causeChain", "sorter", "spectrum", "padlocks", "tugOfWar", "oneVsAll", "tAccount",
         "choicePaths", "incomeLine", "doorway"]
HAS_NODE = shutil.which("node") is not None

VARIANTS = (
    [(n, {}) for n in NAMES]
    + [("formula", {"terms": "Q|=|100|−|2P", "values": "P=10", "sub": "in", "result": "auto", "labels": "1:माँग की मात्रा;3:दाम", "_s": s})
       for s in (0, 0.3, 5)]
    + [("formula", {"terms": "P_e|=|a − c//d + b", "values": "a=120;c=10;d=5;b=15", "sub": "in", "lines": "= {110}//{20}", "result": "auto", "upto": u})
       for u in (0, 1, 2)]
    + [("formula", {"terms": "M|×|V|=|P|×|Y", "values": v, "sub": "under", "beam": True, "tiltFrom": "-0.5", "_s": 0.4})
       for v in ("M=1000;V=5;P=10;Y=500", "M=2000;V=5;P=10;Y=500", "M=2000;V=5;P=?;Y=500")]
    + [("formula", {"terms": "PV|=|Σ d^{t} U_t", "result": "80 + 192 + 102.4", "title": "भविष्य", "glow": "2", "unit": "₹"}),
       ("formula", {"terms": "", "upto": 3}), ("formula", {"terms": "a|+", "values": "x=", "sub": "in", "result": "auto"}),
       ("formula", {"terms": "AD|=|C|+|I|+|G|+|X|−|M", "upto": 4, "glow": "4", "w": 300})]
    + [("scaleBalance", {"left": "चाहतें=3;और=3;@coinStack:₹100;@moneyBag", "right": "ज़मीन;श्रम;पूंजी", "auto": True, "upto": u, "leftLabel": "चाहतें",
                         "rightLabel": "साधन", "gapLabel": "दुर्लभता", "levelTag": "MB = MC", "mark": "auto", "crack": "left", "title": "दुर्लभता", "_s": 0.3})
       for u in (0, 1, 5, 7)]
    + [("scaleBalance", {"mode": "seesaw", "weight": "कर ₹10", "share": sh, "shareFrom": "0.5", "split": True, "leftLabel": "ख़रीदार", "rightLabel": "दुकानदार", "_s": 0.4})
       for sh in (0, 0.7, 1)]
    + [("scaleBalance", {"mode": "seesaw", "leftValue": "10%", "rightValue": "₹100", "tilt": -0.6, "tiltFrom": "0.6", "pivotLabel": "₹10 हर साल", "crack": "right",
                         "left": "@nosuchthing;@scaleBalance", "mark": "right"})]
    + [("causeChain", {"links": "ब्याज दर|up;EMI|up;ख़रीदार|down;घरों के दाम|down", "at": a, "until": "जब तक D_g = S_g", "_s": 0.3}) for a in (0, 1, 3, 9)]
    + [("causeChain", {"links": "a|up;b|down;c|eq;d;e|x;f|up", "loop": True, "loopLabel": "फिर से", "run": True, "layout": lay, "ghost": g, "at": 3, "_t": 2.5})
       for lay in ("auto", "row", "snake", "ring") for g in (True, False)]
    + [("causeChain", {"links": "माँग|up;दाम|up;मुनाफ़ा|up", "links2": "मज़दूरी|up;रोज़गार|up", "join": j, "title": "दो बाज़ार", "until": "x"}) for j in (0, 2, 9)]
    + [("causeChain", {"links": ""})]
    + [("sorter", {"bins": "ज़मीन;श्रम;पूंजी", "cards": "खेत;मशीन;किसान;फ़ैक्टरी", "answers": "1,3,2,3", "wrong": "2:1", "at": a, "_s": s, "title": "साधन"})
       for a in (0, 1, 2, 4) for s in (0.3, 1.0, 1.6, 5)]
    + [("sorter", {"bins": "", "cards": "a|बहुत लंबा कथन जो दो पंक्तियों में आएगा", "answers": "9", "at": 1, "marks": False}),
       ("sorter", {"bins": "x;y", "cards": ";".join(f"c{i}" for i in range(16)), "answers": ",".join("1" for _ in range(16)), "at": 16})]
    + [("spectrum", {"left": "योजनाबद्ध", "right": "बाज़ार", "pins": "क्यूबा:0.05;चीन:0.15;पोलैंड:0.2;भारत:0.4;UK:0.75;USA:0.85;x:bad", "pins2": "चीन:0.5;पोलैंड:0.7",
                     "date": "1980", "date2": "2010", "state": st, "upto": u, "glow": "2", "title": "अर्थव्यवस्थाएँ", "_s": 0.3})
       for st in ("1", "2") for u in (0, 3)]
    + [("spectrum", {"look": "pendulum", "left": "बाज़ार", "right": "सरकार", "at": a, "atFrom": "0", "era": "1980", "leftNote": "संकट", "rightNote": "मंदी",
                     "pins": "कीन्स:0.8;फ्रीडमैन:-0.7", "title": "झूला", "_s": 0.5, "_t": 3}) for a in (-1, 0, 1)]
    + [("spectrum", {"min": 5, "max": 5, "pins": "a:5"})]
    + [("padlocks", {"labels": "आमदनी;पसंद;दूसरी चीज़ों के दाम;उम्मीदें;आबादी;मौसम;a;b;c;d", "open": o, "glow": g, "title": "बाकी सब स्थिर", "_s": 0.2})
       for o, g in (("", ""), ("2", "2"), ("1,2,3", "4"))] + [("padlocks", {"labels": "", "cols": 5})]
    + [("tugOfWar", {"left": "यूनियन", "right": "मालिक", "share": 0.55, "shareFrom": "0.5", "pull": pl, "rounds": r, "prices": "₹100;₹110;₹121", "tag": "दाम",
                     "shareLabel": "हिस्सा", "_s": 0.4, "_t": 2}) for pl in ("left", "right", "both", "") for r in (0, 2, 9)]
    + [("tugOfWar", {"share": 1}), ("tugOfWar", {"share": 0, "rounds": 3, "tag": "दाम"})]
    + [("oneVsAll", {"actor": "किसान", "action": "फसल आधी", "oneResult": "आमदनी घटी", "oneDir": "down", "allResult": "आमदनी बढ़ी", "allDir": "up",
                     "leftTitle": "एक किसान", "rightTitle": "सब किसान", "total": "कुल", "stage": st, "n": n, "_s": s, "title": "भ्रम"})
       for st in (0, 1, 2) for n in (2, 30) for s in (0.3, 1.6, 5)]
    + [("tAccount", {"title": "अपना बैंक", "unit": "₹ करोड़", "leftHead": "देनदारियाँ", "rightHead": "संपत्तियाँ", "left": "जमा:1,100;पूंजी:100",
                     "right": "रिज़र्व:200;कर्ज़:1,000", "was": "L1:1,000", "glow": "L1,R2", "upto": u, "_s": 0.2}) for u in (0, 1, 3, 9)]
    + [("tAccount", {"left": "होम लोन:30,00,000", "right": "फ़्लैट:50,00,000", "net": True, "netLabel": "हैसियत", "capital": c, "loss": l, "capitalLabel": "पूंजी",
                     "lossLabel": "घाटा", "_s": 0.3}) for c, l in ((10, 4), (10, 12), (0, 5))]
    + [("tAccount", {"left": "a;b:x", "right": "", "order": "L2,R9,L1", "upto": 2, "totals": False})]
    + [("choicePaths", {"options": "मुफ़्त लेक्चर;₹500 की शिफ़्ट;नींद;लाइब्रेरी", "chosen": c, "best": b, "tag": "अवसर लागत", "from": "सीता", "title": "चुनाव", "_s": 0.5})
       for c, b in ((0, 0), (1, 2), (2, 2), (4, 1))] + [("choicePaths", {"options": ""})]
    + [("incomeLine", {"values": "3;4;5;6;8;10;12;15;20;30", "mode": m, "share": 0.6, "rise": 2, "riseFrom": "1", "line": 7, "lineLabel": "गरीबी रेखा",
                       "showValue": True, "unit": "k", "countLabel": "{n} लोग", "meanLabel": "औसत", "title": "आय", "_s": s}) for m in ("absolute", "relative") for s in (0.5, 5)]
    + [("incomeLine", {"values": "", "max": 10}), ("incomeLine", {"values": "x;-3;0", "countLabel": ""})]
    + [("doorway", {"open": o, "openFrom": "0", "label": "दहलीज़", "beyond": "नई समझ", "_s": s}) for o in (0, 0.5, 1) for s in (0.2, 5)]
)


def node(js: str):
    """Runs a module script after the engine is loaded (draw.mjs first: it is the entry that loads the families)."""
    script = (f"const D = await import('{(ENGINE / 'draw.mjs').as_posix()}');"
              f"const F = await import('{FAMILY.as_posix()}');" + js)
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def draw_all(cases):
    return node(f"const cases = {json.dumps(cases, ensure_ascii=False)};"
                "console.log(JSON.stringify(cases.map(([n, p]) => D.drawSaancha(n, p))));")


def balanced(svg: str) -> bool:
    stack = []
    for close, tag, selfclose in re.findall(r"<(/?)([a-zA-Z]+)(?:\s[^<>]*?)?(/?)>", svg):
        if close:
            if not stack or stack.pop() != tag:
                return False
        elif not selfclose:
            stack.append(tag)
    return not stack


def rotation(svg: str) -> float:
    """The beam's angle: the first rotate(a cx cy) the balance draws."""
    return float(re.search(r"rotate\((-?[\d.]+) 0 ", svg).group(1))


class Manifest(unittest.TestCase):
    def test_the_family_manifest_names_its_drawings_with_hindi_and_english_words(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "bie.saancha-manifest/1")
        self.assertEqual(data["licence"], "MIT (BIE)")
        self.assertEqual(sorted(data["saanche"]), sorted(NAMES))
        for name in NAMES:
            entry = saanche.get(name)
            self.assertIsNotNone(entry, name)
            self.assertEqual(entry["since"], "2026-11-05")
            self.assertTrue(any(not t.isascii() for t in entry["tags"]), name)
            self.assertTrue(any(t.isascii() for t in entry["tags"]), name)
            defaults = {k: v["default"] for k, v in entry["params"].items() if v["type"] != "color" or v["default"]}
            self.assertEqual(saanche.problems(name, defaults), [], name)

    def test_parameters_out_of_range_are_refused(self):
        for name, p in [("formula", {"upto": 31}), ("formula", {"sub": "over"}), ("formula", {"beam": "yes"}), ("formula", {"w": 5000}),
                        ("scaleBalance", {"tilt": 1.5}), ("scaleBalance", {"mode": "lever"}), ("scaleBalance", {"share": -0.1}),
                        ("scaleBalance", {"mark": "middle"}), ("causeChain", {"at": 2.5}), ("causeChain", {"layout": "tree"}),
                        ("sorter", {"at": 17}), ("spectrum", {"look": "dial"}), ("spectrum", {"at": -2}), ("spectrum", {"state": "3"}),
                        ("padlocks", {"cols": 6}), ("tugOfWar", {"pull": "up"}), ("tugOfWar", {"rounds": 13}), ("oneVsAll", {"stage": 3}),
                        ("oneVsAll", {"n": 1}), ("oneVsAll", {"oneDir": "left"}), ("tAccount", {"loss": -1}), ("tAccount", {"color": "orange"}),
                        ("choicePaths", {"chosen": 5}), ("incomeLine", {"mode": "both"}), ("incomeLine", {"rise": -1}), ("doorway", {"open": 2}),
                        ("formula", {"tilt": 0}), ("doorway", {"angle": 3})]:
            with self.subTest(name=name, p=p):
                self.assertTrue(saanche.problems(name, p))

    def test_a_search_in_hindi_finds_them(self):
        for word, name in [("सूत्र", "formula"), ("समीकरण", "formula"), ("तराज़ू", "scaleBalance"), ("झूला", "scaleBalance"), ("श्रृंखला", "causeChain"),
                           ("छाँटो", "sorter"), ("स्पेक्ट्रम", "spectrum"), ("पेंडुलम", "spectrum"), ("ताला", "padlocks"), ("रस्साकशी", "tugOfWar"),
                           ("भ्रम", "oneVsAll"), ("बैलेंस", "tAccount"), ("अवसर", "choicePaths"), ("गरीबी", "incomeLine"), ("दहलीज़", "doorway")]:
            found = [r.get("name") for r in saanche.search(word) if r.get("kind") == "draw"]
            self.assertIn(name, found, word)

    def test_no_words_are_baked_into_the_drawings(self):
        source = FAMILY.read_text(encoding="utf-8")
        self.assertIsNone(re.search("[ऀ-ॿ]", source))          # Hindi words come only from parameters
        self.assertNotIn("Math.random", source)
        self.assertNotIn("Date.now", source)

    @unittest.skipUnless(HAS_NODE, "needs node (the toolbox lane has it)")
    def test_the_registry_and_the_manifest_agree(self):
        got = node("console.log(JSON.stringify(Object.fromEntries(Object.entries(F.DRAWS).map(([k, v]) => [k, v.anchor]))));")
        self.assertEqual(sorted(got), sorted(NAMES))
        for name, anchor in got.items():
            self.assertEqual(saanche.get(name)["anchor"], anchor, name)
        registry = node("console.log(JSON.stringify(Object.keys(D.DRAWS)));")
        self.assertTrue(set(NAMES) <= set(registry))


@unittest.skipUnless(HAS_NODE, "needs node (the toolbox lane has it)")
class Drawing(unittest.TestCase):
    def test_every_variant_draws_clean_svg(self):
        svgs = draw_all(VARIANTS)
        self.assertEqual(len(svgs), len(VARIANTS))
        for (name, params), svg in zip(VARIANTS, svgs):
            with self.subTest(name=name, params=params):
                self.assertTrue(svg.strip().startswith("<"))
                self.assertNotRegex(svg, r"NaN|undefined|Infinity")
                self.assertTrue(balanced(svg))
                self.assertNotIn('stroke-width="-', svg)
                self.assertNotIn('font-size="-', svg)

    def test_a_process_is_a_pure_function_of_its_times(self):
        cases = [("formula", {"terms": "Q|=|100|−|2P", "values": "P=10", "sub": "in"}), ("scaleBalance", {"left": "a", "right": "b;c", "auto": True, "upto": 3}),
                 ("causeChain", {"links": "a|up;b|down;c", "at": 2, "run": True, "loop": True}), ("sorter", {"bins": "x;y", "cards": "p;q", "answers": "1,2", "at": 1}),
                 ("spectrum", {"pins": "a:0.1", "pins2": "a:0.9", "state": "2"}), ("spectrum", {"look": "pendulum", "at": 1, "atFrom": "-1"}),
                 ("padlocks", {"labels": "a;b", "open": "1", "glow": "1"}), ("tugOfWar", {"share": 0.7, "shareFrom": "0.5", "pull": "left", "rounds": 2}),
                 ("oneVsAll", {"oneResult": "x", "oneDir": "down", "allResult": "y", "allDir": "up", "stage": 2}),
                 ("tAccount", {"left": "a:1;b:2", "right": "c:3", "upto": 2, "capital": 5, "loss": 2}), ("choicePaths", {"chosen": 1, "best": 2, "tag": "t"}),
                 ("incomeLine", {"rise": 2, "riseFrom": "1", "mode": "relative"}), ("doorway", {"open": 1})]
        times = [(0.0, 0.0), (0.25, 0.25), (1.5, 0.6), (9.0, 9.0)]
        runs = [(n, {**p, "_t": t, "_s": s}) for n, p in cases for t, s in times]
        first, second = draw_all(runs), draw_all(list(reversed(runs)))[::-1]
        self.assertEqual(first, second)                                        # same params and times, same SVG, any order
        for k, (name, _) in enumerate(cases):
            frames = first[k * len(times):(k + 1) * len(times)]
            with self.subTest(name=name):
                self.assertGreater(len(set(frames)), 1)                        # it moves
        stills = draw_all([(n, p) for n, p in cases])
        settled = draw_all([(n, {**p, "_s": 10000}) for n, p in cases])
        self.assertEqual(stills, settled)                                      # a still shows the settled state

    def test_the_formula_computes_and_its_beam_levels_only_when_both_sides_are_equal(self):
        auto, worked, balanced_, unbalanced, unknown = draw_all([
            ("formula", {"terms": "Q|=|100|−|2P", "values": "P=10", "sub": "in", "result": "auto"}),
            ("formula", {"terms": "P_e|=|a − c//d + b", "values": "a=120;c=10;d=5;b=15", "sub": "in", "result": "auto", "unit": "₹"}),
            ("formula", {"terms": "M|×|V|=|P|×|Y", "values": "M=1000;V=5;P=10;Y=500", "sub": "under", "beam": True}),
            ("formula", {"terms": "M|×|V|=|P|×|Y", "values": "M=2000;V=5;P=10;Y=500", "sub": "under", "beam": True}),
            ("formula", {"terms": "M|×|V|=|P|×|Y", "values": "M=2000;V=5;P=?;Y=500", "sub": "under", "beam": True})])
        self.assertIn(">80<", auto)
        self.assertIn(">₹5.5<", worked)
        self.assertNotIn("≠", balanced_)
        self.assertAlmostEqual(rotation(balanced_), 0, places=2)
        self.assertIn("≠", unbalanced)
        self.assertLess(rotation(unbalanced), 0)                               # the heavier left side goes down
        self.assertAlmostEqual(rotation(unknown), 0, places=2)                 # an unknown side does not tip the beam
        ev = node("const {evaluate} = F._test; console.log(JSON.stringify(['{120 − 10 − 10}//{15}', '£100 × 0.8% × 30', '2^3 + 1', 'a + 1', '−10//5']"
                  ".map((x) => evaluate(x))));")
        self.assertAlmostEqual(ev[0], 100 / 15)
        self.assertAlmostEqual(ev[1], 24)
        self.assertEqual(ev[2], 9)
        self.assertIsNone(ev[3])                                               # NaN: a letter is left
        self.assertEqual(ev[4], -2)

    def test_the_balance_tips_to_the_heavier_side(self):
        left, right, level, burden = draw_all([
            ("scaleBalance", {"left": "a=3;b=3", "right": "c", "auto": True}), ("scaleBalance", {"leftValue": "₹100", "rightValue": "₹250", "auto": True}),
            ("scaleBalance", {"left": "a", "right": "b", "auto": True, "levelTag": "MB = MC"}),
            ("scaleBalance", {"mode": "seesaw", "weight": "₹10", "share": 0.7, "split": True})])
        self.assertLess(rotation(left), 0)
        self.assertGreater(rotation(right), 0)
        self.assertAlmostEqual(rotation(level), 0, places=2)
        self.assertIn("MB = MC", level)
        self.assertLess(rotation(burden), 0)
        self.assertIn(">₹7<", burden)
        self.assertIn(">₹3<", burden)

    def test_the_sorter_crosses_a_wrong_card_before_moving_it(self):
        p = {"bins": "a;b", "cards": "x;y", "answers": "1,2", "wrong": "2:1", "at": 2}
        flying, crossed, settled = draw_all([("sorter", {**p, "_s": 0.3}), ("sorter", {**p, "_s": 1.0}), ("sorter", {**p, "_s": 5})])
        cross = 'stroke="#e5484d" stroke-width'
        self.assertNotIn(cross, flying)
        self.assertIn(cross, crossed)
        self.assertNotIn(cross, settled)
        self.assertGreaterEqual(settled.count("#2fa35b"), 2)                   # both cards ticked in their bins

    def test_the_ledger_ticks_matching_totals_and_the_line_counts_who_is_below(self):
        match, mismatch, indian, below = draw_all([
            ("tAccount", {"left": "जमा:1,100;पूंजी:100", "right": "रिज़र्व:200;कर्ज़:1,000"}), ("tAccount", {"left": "जमा:1,100", "right": "कर्ज़:1,000"}),
            ("tAccount", {"left": "लोन:30,00,000", "right": "फ़्लैट:50,00,000", "net": True}),
            ("incomeLine", {"values": "1;2;3;10", "line": 2.5, "countLabel": "{n} नीचे"})])
        self.assertIn(">1,200<", match)
        self.assertIn("#2fa35b", match)
        self.assertNotIn("≠", match)
        self.assertIn("≠", mismatch)
        self.assertIn(">20,00,000<", indian)                                   # net worth in the rows' own grouping
        self.assertIn(">50,00,000<", indian)
        self.assertIn("2 नीचे", below)

    def test_words_keep_to_the_box_rule(self):
        cases = [(n, p) for n, p in VARIANTS if not p.get("w") and any(not str(v).isascii() for v in p.values())]
        boxes = node(f"const cases = {json.dumps(cases, ensure_ascii=False)};"
                     "console.log(JSON.stringify(cases.map(([n, p]) => D.boxOf(n, {...p, _s: 10000}))));")
        sizes = [t["px"] for b in boxes for t in b["texts"]]
        self.assertGreater(len(sizes), 200)
        self.assertGreaterEqual(min(sizes), 26)                                # subscripts and powers (0.62 of their term)
        self.assertGreaterEqual(sum(s >= 36 for s in sizes) / len(sizes), 0.95)


if __name__ == "__main__":
    unittest.main()
