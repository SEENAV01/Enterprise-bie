"""The econ_charts family (Sloman economics book, 5 November 2026): data charts and counted pictures built at the voice's
speed - barChart, marginalBars, waterfall, pieChart, shareBar, pictogram, iconArray, timeSeries, scatterFit, cycleWave,
dayHours, roundBars, weightBars, pumpJack and bargainTable.

Every name in the family manifest is in the engine's registry and the other way round; every one draws clean SVG at its
defaults and in the variants a scene plan will use; every manifest parameter is one the drawing reads; parameters out of
range are refused; the words inside a drawing never sit on each other; and a process is a pure function of its times
(_t since it appeared, _s since its last step) whose end state is what a measurement without times sees.
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
FAMILY = ENGINE / "families" / "econ_charts.mjs"
MANIFEST = ENGINE / "saanche.d" / "econ_charts.json"
NAMES = ["barChart", "marginalBars", "waterfall", "pieChart", "shareBar", "pictogram", "iconArray", "timeSeries", "scatterFit",
         "cycleWave", "dayHours", "roundBars", "weightBars", "pumpJack", "bargainTable"]
ICONS = ["cup", "tea", "scooter", "sack", "seat", "person", "packet", "share", "barrel", "block", "coin", "note", "house", "car", "plate"]
GINI = "आइसलैंड:0.246;डेनमार्क:0.254;OECD:0.318;ब्रिटेन:0.351;अमेरिका:0.39;भारत:0.495;द. अफ्रीका:0.62"
SERIES = ("बेरोज़गारी:1900=3 4 5 4 3 4 5 6 8 7 5 3 2 2 3 2 1 1 2 3 4 10 12 9 8 7 8 10 11 16 20 21 18 16 13 11 10 8 5 2;"
          "महँगाई@2:1900=2 3 1 0 -1 2 3 4 2 1 1 2 5 10 20 22 18 12 -10 -5 -2 -3 -1 0 1 -2 -4 -6 -5 -2 0 1 3 4 5 5 3 2 4 6")
LAMB = "1,160 2,155 3,150 4,152 5,140 6,138 7,130 8,128 9,122 10,118 11,112 12,110"
TS = {"series": SERIES, "bands": "1914-1918:युद्ध;1929-1938:महामंदी", "events": "1931:सोना छोड़ा", "xLabel": "साल", "yLabel": "बेरोज़गारी",
      "y2Label": "महँगाई", "unit": "%", "unit2": "%", "title": "ब्रिटेन"}

# the variants a scene plan will use; CLEAN ones must also keep their words apart (the box rule inside a drawing)
CLEAN = (
    [("barChart", {"bars": GINI, "glow": "3", "refLine": "0.318:OECD औसत", "title": "गिनी"}),
     ("barChart", {"bars": "क्विंटाइल 1:6.8;2:8.7;3:10.0;4:11.8;5:11.6", "dir": "vertical", "unit": "%", "glow": "5", "title": "हरित कर"}),
     ("barChart", {"bars": "चीनी:99;तंबाकू:99;मिठाई:81;गैस:70;बीयर:50;दवा:30;कपड़ा:12;निर्माण:5", "group": "4:ऊँचा:कम", "groupGlow": 1, "unit": "%"}),
     ("barChart", {"bars": "क:30:22;ख:45:38;ग:80:60", "names": "सकल;खर्च योग्य", "dir": "vertical", "unit": "₹"}),
     ("barChart", {"bars": "क:-2.5;ख:4;ग:1.2", "unit": "%", "sort": "desc"}),
     ("marginalBars", {"values": "800;700;600;500;400;300", "line": "400:मज़दूरी ₹400", "unit": "₹", "stop": True, "stopLabel": "रुको", "title": "MRP"}),
     ("marginalBars", {"values": "60000;60000", "costs": "50000;65000", "labels": "पहला;दूसरा", "names": "लाभ;लागत", "unit": "₹", "stop": True, "stopLabel": "रुको"}),
     ("marginalBars", {"values": "7;4;2;1;0;-1", "tower": "beside", "towerLabel": "कुल"}),
     ("marginalBars", {"values": "65;50;45;40", "line": "40:कीमत ₹40", "unit": "₹", "gather": True, "gatherLabel": "बचत", "marks": False}),
     ("marginalBars", {"values": "7;4;2;1", "tower": "only", "towerLabel": "कुल"}),
     ("waterfall", {"parts": "PSNCR:+100;बिक्री:-40;बैंक कर्ज़:+150;बाहर:-10", "total": "ΔM4", "unit": "₹", "glow": "3", "title": "M4"}),
     ("waterfall", {"parts": "PSNCR:+120;बैंक कर्ज़:-200;बाहर:+20", "total": "ΔM4", "start": "पहले:50", "unit": "₹"}),
     ("pieChart", {"slices": "सबसे गरीब:4.1;दूसरे:7.6;बीच के:12.8;चौथे:22.6;सबसे अमीर:52.9", "glow": "5", "tower": "5:ऊपरी 1%", "title": "आय"}),
     ("pieChart", {"slices": "मज़दूरी:60;मुनाफ़ा:25;किराया:15", "donut": True, "center": "आय", "legend": False}),
     ("shareBar", {"parts": "आयकर:20;NI:12;खोया क्रेडिट:41;बचा:27", "unit": "p", "running": True, "label": "एक पाउंड"}),
     ("shareBar", {"parts": "कर:20;NI:12;क्रेडिट:73", "unit": "p", "overflow": True, "running": True, "wholeLabel": "£1"}),
     ("shareBar", {"parts": "कार:60;बस:20;रेल:12;पैदल:8|कार:70;बस:14;रेल:9;पैदल:7", "bars": "1990;2010", "label": "यात्रा", "glow": "1"}),
     ("pictogram", {"icon": "cup", "n": 6, "on": 4, "label": "सीता के कप", "count": "{n} कप"}),
     ("pictogram", {"icon": "block", "n": 40, "on": 20, "cols": 8, "rowLabels": "सोम;मंगल;बुध;गुरु;शुक्र", "label": "हफ़्ते के घंटे"}),
     ("iconArray", {"n": 200, "groups": "बीमार:100;स्वस्थ:9900", "split": "99;99", "marks": True, "splitLabel": "पॉज़िटिव", "per": "1 = 50 लोग", "title": "10,000 लोग"}),
     ("iconArray", {"n": 200, "groups": "बीमार:100:#e5484d;स्वस्थ:9900:#2a9d8f", "split": "99;99", "marks": True, "gather": True,
                    "gatherLabel": "पॉज़िटिव {n}: बीमार {1} ({p1}%)", "shape": "dot", "mark": "dot"}),
     ("timeSeries", dict(TS, window="1929-1938", marks="1@max;2@min", pointer="1@1935<1@1925")),
     ("timeSeries", {"series": "निवेश:1990=5 8 -3 12 26.4 4 -20.7 6;GDP:1990=2 3 1 4 9.8 2 -6.1 3", "marks": "1@max;1@min;2@max", "unit": "%"}),
     ("scatterFit", {"points": LAMB, "residuals": True, "r2": 0.908, "xLabel": "कीमत", "yLabel": "खपत", "title": "मेमना"}),
     ("scatterFit", {"points": LAMB, "fit2": "159 155 151 150 141 137 131 127 122 118 113 110", "model": 2, "r2": 0.908, "r2b": 0.958, "residuals": True}),
     ("cycleWave", {"ceiling": "पूर्ण रोज़गार", "floor": "न्यूनतम", "trendLabel": "संभावित", "xLabel": "समय", "yLabel": "उत्पादन", "title": "चक्र"}),
     ("cycleWave", {"at": 2, "dot": False, "cycles": 3}),
     ("dayHours", {"hours": 16, "work": 10, "wage": 200, "tax": 0.2, "taxAbove": 1200, "unitH": " घंटे", "earn": "कमाई ₹{v}", "title": "मोहन"}),
     ("dayHours", {"hours": 16, "work": 2, "unitH": " घंटे"}),
     ("dayHours", {"shape": "dial", "hours": 12, "work": 8, "highlight": 9, "unitH": " घं", "wage": 100, "title": "दिन"}),
     ("roundBars", {"first": 100, "keep": 0.8, "rounds": 5, "totalLabel": "कुल", "title": "गुणक"}),
     ("roundBars", {"first": 100, "keep": 0.8, "rounds": 4, "dir": "down", "jars": False}),
     ("weightBars", {"assets": "नकद:100:0;सरकारी बॉन्ड:200:0.2;होम लोन:400:0.35;कारोबारी कर्ज़:300:1", "applied": 4, "stack": True, "capital": 60, "title": "RWA"}),
     ("weightBars", {"applied": 0, "capital": 30, "threshold": 3, "unweighted": True, "ratioLabel": "लीवरेज"}),
     ("pumpJack", {"running": True, "label": "चालू", "_t": 1.3}),
     ("bargainTable", {"left": "यूनियन", "right": "प्रबंधन", "cards": "L:हड़ताल;L:नियम से काम;R:छँटनी:torn;R:बोनस:agreed;L:धरना;R:मशीन", "mood": 0.7,
                       "mediator": True, "mediatorLabel": "मध्यस्थ", "title": "मोलभाव", "_t": 2})]
)
EDGES = (
    [(n, {}) for n in NAMES]
    + [("pictogram", {"icon": i, "n": 7, "on": 3, "off": o}) for i in ICONS for o in ("fade", "cross")]
    + [("pictogram", {"icon": "cup", "n": 130, "on": 130, "from": 100, "each": 0.02, "_t": 2, "_s": 0.4}), ("pictogram", {"n": 1, "on": 0, "off": "hide"}),
       ("pictogram", {"icon": "moon", "n": 120, "cols": 1, "order": "start", "on": 7, "from": 12, "_s": 0.5})]
    + [("barChart", {"bars": ""}), ("barChart", {"bars": "a:x;b"}), ("barChart", {"bars": "क:0;ख:0", "refLine": "x"}),
       ("barChart", {"bars": GINI, "upto": 3, "from": "0.2;0.2;0.2", "_t": 2, "_s": 0.3, "dim": True, "glow": "2"}),
       ("barChart", {"bars": GINI, "dir": "vertical", "upto": 9, "group": "3:a:b", "groupGlow": 2, "max": 1, "_s": 0.1})]
    + [("marginalBars", {"values": ""}), ("marginalBars", {"values": "5", "line": "x:y", "costs": "a"}),
       ("marginalBars", {"values": "800;700;600;500", "line": "600:मज़दूरी", "lineFrom": "400", "upto": 3, "_t": 3, "_s": 0.35}),
       ("marginalBars", {"values": "7;4;2;1;0;-1", "tower": "beside", "upto": 6, "_t": 3, "_s": 0.5}),
       ("marginalBars", {"values": "65;50;45;40", "line": "40", "gather": True, "_t": 3, "_s": 0.5}),
       ("marginalBars", {"values": "-3;-1", "line": "-2:x", "tower": "only", "upto": 1, "max": 5})]
    + [("waterfall", {"parts": ""}), ("waterfall", {"parts": "a:x;b:5", "start": "x"}), ("waterfall", {"parts": "a:+5;b:-5", "total": "t", "upto": 1, "_s": 0.2}),
       ("waterfall", {"parts": "a:+5;b:-5", "total": "t", "upto": 3, "running": False})]
    + [("pieChart", {"slices": ""}), ("pieChart", {"slices": "a:0;b:0"}), ("pieChart", {"slices": "a:100"}), ("pieChart", {"slices": "a:1:#ff0000;b:2:bad", "tower": "9:x"}),
       ("pieChart", {"slices": "a:6.9;b:10.9;c:43", "from": "4.1;7.6;48", "upto": 2, "_t": 1, "_s": 0.4, "donut": True})]
    + [("shareBar", {"parts": ""}), ("shareBar", {"parts": "a:0"}), ("shareBar", {"parts": "a:5;b:2", "whole": 0.001}),
       ("shareBar", {"parts": "कर:20;NI:12;क्रेडिट:73", "overflow": True, "running": True, "upto": 3, "_s": 0.3, "from": "1;1;1"}),
       ("shareBar", {"parts": "a:1|b:2|", "bars": "x", "upto": 2, "_s": 0.2})]
    + [("iconArray", {"groups": "", "n": 1}), ("iconArray", {"n": 1000, "groups": "a:1;b:999", "split": "1;10", "marks": True, "gather": True, "_s": 0.7}),
       ("iconArray", {"n": 30, "groups": "a:10;b:10;c:10", "upto": 2, "highlight": 1, "shape": "square", "mark": "cross", "split": "5", "marks": True})]
    + [("timeSeries", {"series": ""}), ("timeSeries", {"series": "a:1990=x y;b:"}), ("timeSeries", {"series": "a:5,5"}),
       ("timeSeries", dict(TS, drawIn=4, _t=1, window="1929-1938", windowFrom="1914-1918", _s=0.5, pointer="2@1930<2@1910", show="1,2", grow="2")),
       ("timeSeries", dict(TS, xmin=1910, xmax=1920, ymin=-5, ymax=30, y2min=-20, y2max=40, step=2, zero=False, legend=False, marks="1@1915:{x} {y};9@max;1@x"))]
    + [("scatterFit", {"points": ""}), ("scatterFit", {"points": "1,1"}), ("scatterFit", {"points": "1,1 1,2", "fit": "none"}),
       ("scatterFit", {"points": LAMB, "fit": "170,-5", "settle": True, "_s": 0.5, "upto": 5, "gauge": False}),
       ("scatterFit", {"points": LAMB, "fit2": "159 155", "model": 2, "modelFrom": 1, "_s": 0.7, "residuals": True})]
    + [("cycleWave", {"phases": ""}), ("cycleWave", {"phases": "a;b", "cycles": 4, "ride": 0, "pos": 1}),
       ("cycleWave", {"phases": "a;b;c;d;e;f", "ceiling": "c", "floor": "f", "_t": 1.5, "ride": 6}), ("cycleWave", {"ceiling": "छत", "_t": 0.5, "ride": 4, "cycles": 1})]
    + [("dayHours", {"work": 0}), ("dayHours", {"work": 24, "hours": 24}), ("dayHours", {"work": 9, "from": 8, "_s": 0.4, "wage": 100}),
       ("dayHours", {"shape": "dial", "hours": 1, "work": 0.5, "labels": "", "_t": 1}), ("dayHours", {"hours": 4, "work": 3, "labels": "a"})]
    + [("roundBars", {"rounds": 1}), ("roundBars", {"rounds": 12, "keep": 0.99, "leaks": "", "total": False, "limit": False}),
       ("roundBars", {"rounds": 3, "first": 0, "leakShares": "3;1;x"}), ("roundBars", {"rounds": 5, "_t": 3, "_s": 0.9})]
    + [("weightBars", {"assets": ""}), ("weightBars", {"assets": "a:x:y"}), ("weightBars", {"capital": 60, "applied": 2, "_s": 0.4, "from": "100;200;200;500", "stack": True}),
       ("weightBars", {"capital": 1, "threshold": 50, "tags": False, "ratio": True})]
    + [("pumpJack", {"w": 60}), ("pumpJack", {"running": True, "rate": 3, "_t": 0.7}), ("pumpJack", {"running": False, "_t": 5})]
    + [("bargainTable", {"cards": ""}), ("bargainTable", {"cards": "R:x;R:y;R:z;R:a;R:b;L:c:agreed;L:d:torn;L:e", "upto": 8, "_s": 0.3, "_t": 4}),
       ("bargainTable", {"cards": "x", "mood": 1, "_t": 0.2})]
)


def node(script: str) -> str:
    return subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout


def draw_all(cases) -> list:
    script = (f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
              f"const cases = {json.dumps(cases, ensure_ascii=False)};"
              "console.log(JSON.stringify(cases.map(([n, p]) => drawSaancha(n, p))));")
    return json.loads(node(script))


def balanced(svg: str) -> bool:
    stack = []
    for close, tag, selfclose in re.findall(r"<(/?)([a-zA-Z]+)(?:\s[^<>]*?)?(/?)>", svg):
        if close:
            if not stack or stack.pop() != tag:
                return False
        elif not selfclose:
            stack.append(tag)
    return not stack


class Manifest(unittest.TestCase):
    def test_manifest_and_registry_agree(self):
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(man["schema"], "bie.saancha-manifest/1")
        self.assertEqual(sorted(man["saanche"]), sorted(NAMES))
        for name in NAMES:
            entry = saanche.get(name)
            self.assertIsNotNone(entry, name)
            self.assertEqual(entry["since"], "2026-11-05")
            self.assertTrue(any(not t.isascii() for t in entry["tags"]), name)
            self.assertTrue(any(t.isascii() for t in entry["tags"]), name)

    @unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
    def test_the_engine_registry_has_every_family_drawing_with_its_anchor(self):
        got = json.loads(node(f"import {{DRAWS}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                              f"import {{DRAWS as F}} from '{FAMILY.as_posix()}';"
                              "console.log(JSON.stringify({fam: Object.fromEntries(Object.entries(F).map(([k, v]) => [k, v.anchor])),"
                              " reg: Object.keys(DRAWS)}));"))
        self.assertEqual(sorted(got["fam"]), sorted(NAMES))
        for name, anchor in got["fam"].items():
            self.assertIn(name, got["reg"])
            self.assertEqual(saanche.get(name)["anchor"], anchor, name)

    def test_every_manifest_parameter_is_read_by_its_drawing(self):
        src = FAMILY.read_text(encoding="utf-8")
        starts = sorted((src.index(f"function {n}(p)"), n) for n in NAMES)
        end = src.index("export const DRAWS")
        for k, (at, name) in enumerate(starts):
            body = src[at:starts[k + 1][0] if k + 1 < len(starts) else end]
            for pname in saanche.get(name)["params"]:
                self.assertRegex(body, rf"\bp\.{pname}\b", f"{name}.{pname} is in the manifest but the drawing never reads it")

    def test_defaults_obey_their_own_limits(self):
        for name in NAMES:
            for pname, spec in saanche.get(name)["params"].items():
                if spec["type"] == "color" and spec["default"] == "":
                    continue
                self.assertEqual(saanche.problems(name, {pname: spec["default"]}), [], f"{name}.{pname}")

    def test_parameters_out_of_range_are_refused(self):
        for name in NAMES:
            self.assertTrue(saanche.problems(name, {"w": 5000}), name)
            self.assertTrue(saanche.problems(name, {"nonsense": 1}), name)
        for name, p in [("pictogram", {"n": 500}), ("pictogram", {"icon": "moon"}), ("pictogram", {"on": -2}), ("iconArray", {"n": 5000}),
                        ("iconArray", {"mark": "star"}), ("roundBars", {"keep": 1.5}), ("roundBars", {"rounds": 40}), ("barChart", {"dir": "diagonal"}),
                        ("barChart", {"upto": 2.5}), ("marginalBars", {"tower": "yes"}), ("marginalBars", {"stop": "yes"}), ("dayHours", {"hours": 30}),
                        ("dayHours", {"shape": "pie"}), ("scatterFit", {"model": 3}), ("scatterFit", {"r2": 2}), ("cycleWave", {"cycles": 9}),
                        ("weightBars", {"applied": 20}), ("pumpJack", {"rate": 9}), ("bargainTable", {"mood": 2}), ("shareBar", {"whole": 0}),
                        ("timeSeries", {"drawIn": 99}), ("pieChart", {"towerSize": 3}), ("barChart", {"color": "red"})]:
            self.assertTrue(saanche.problems(name, p), (name, p))

    def test_a_director_finds_them_in_hindi_and_english(self):
        for word, name in [("पाई", "pieChart"), ("वॉटरफॉल", "waterfall"), ("सीमांत", "marginalBars"), ("गिनती", "pictogram"), ("आवृत्ति", "iconArray"),
                           ("समय श्रृंखला", "timeSeries"), ("प्रतिगमन", "scatterFit"), ("व्यापार चक्र", "cycleWave"), ("घंटे", "dayHours"),
                           ("गुणक", "roundBars"), ("जोखिम भार", "weightBars"), ("शेल", "pumpJack"), ("मोलभाव", "bargainTable"), ("रैंकिंग", "barChart"),
                           ("waterfall", "waterfall"), ("regression", "scatterFit"), ("multiplier", "roundBars"), ("pictogram", "pictogram")]:
            found = [r.get("name") for r in saanche.search(word, limit=12) if r.get("kind") == "draw"]
            self.assertIn(name, found, word)


@unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
class Drawing(unittest.TestCase):
    def test_every_variant_draws_clean_svg(self):
        cases = CLEAN + EDGES
        for (name, params), svg in zip(cases, draw_all(cases)):
            with self.subTest(name=name, params=params):
                self.assertTrue(svg.strip())
                self.assertNotRegex(svg, r"NaN|undefined|Infinity")
                self.assertTrue(balanced(svg))
                self.assertNotIn('stroke-width="-', svg)
                self.assertNotRegex(svg, r'(width|height)="-')

    def test_words_inside_a_drawing_never_sit_on_each_other(self):
        """The box rule inside one drawing: in the clean variants no word's box covers a quarter of another's."""
        script = (f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                  f"import {{svgBounds}} from '{(ENGINE / 'boxes.mjs').as_posix()}';"
                  f"const cases = {json.dumps(CLEAN, ensure_ascii=False)};"
                  "console.log(JSON.stringify(cases.map(([n, p]) => svgBounds(drawSaancha(n, p)).texts)));")
        for (name, params), texts in zip(CLEAN, json.loads(node(script))):
            for i, a in enumerate(texts):
                for b in texts[i + 1:]:
                    ax, bx = a["box"], b["box"]
                    ix = max(0, min(ax[2], bx[2]) - max(ax[0], bx[0]))
                    iy = max(0, min(ax[3], bx[3]) - max(ax[1], bx[1]))
                    small = min((ax[2] - ax[0]) * (ax[3] - ax[1]), (bx[2] - bx[0]) * (bx[3] - bx[1]))
                    self.assertLessEqual(ix * iy, 0.25 * small, f"{name} {params}: '{a['t']}' sits on '{b['t']}'")

    def test_words_are_large_at_scale_one(self):
        """At its defaults every family drawing writes its words at 36 px or more (the box rule's floor at s = 1)."""
        script = (f"import {{boxOf}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                  f"const cases = {json.dumps([(n, {}) for n in NAMES] + CLEAN[:4], ensure_ascii=False)};"
                  "console.log(JSON.stringify(cases.map(([n, p]) => boxOf(n, p).texts.map((t) => t.px))));")
        for name, sizes in zip(NAMES + [c[0] for c in CLEAN[:4]], json.loads(node(script))):
            self.assertTrue(all(px >= 35.5 for px in sizes), (name, sorted(sizes)[:3]))

    def test_a_process_is_a_pure_function_of_its_times(self):
        procs = [("pumpJack", {"running": True}), ("cycleWave", {"ride": 6}), ("timeSeries", dict(TS, drawIn=4)),
                 ("roundBars", {"rounds": 4}), ("iconArray", {"n": 50, "groups": "a:1;b:9", "split": "1;1", "marks": True, "gather": True}),
                 ("pictogram", {"n": 6, "on": 2, "from": 6}), ("barChart", {"bars": GINI, "upto": 4}),
                 ("marginalBars", {"values": "7;4;2", "tower": "beside", "upto": 3}), ("waterfall", {"parts": "a:+5;b:-2", "upto": 2}),
                 ("pieChart", {"slices": "a:1;b:2;c:3", "upto": 3}), ("shareBar", {"parts": "a:1;b:2", "upto": 2, "running": True}),
                 ("dayHours", {"work": 10, "from": 6}), ("weightBars", {"applied": 3, "capital": 50}), ("scatterFit", {"settle": True}),
                 ("bargainTable", {"cards": "L:a;R:b", "upto": 2, "mood": 0.5})]
        cases = []
        for name, p in procs:
            cases += [(name, dict(p, _t=0.3, _s=0.3)), (name, dict(p, _t=0.3, _s=0.3)), (name, dict(p, _t=4.4, _s=0.9)),
                      (name, dict(p, _t=100, _s=100)), (name, p)]
        svgs = draw_all(cases)
        for k, (name, p) in enumerate(procs):
            a, b, c, end, timeless = svgs[k * 5:k * 5 + 5]
            with self.subTest(name=name):
                self.assertEqual(a, b)                       # the same times give the same picture (frames rendered out of order)
                self.assertNotEqual(a, c)                    # and it moves as the video plays
                if name not in ("pumpJack", "cycleWave", "bargainTable", "dayHours"):   # running loops have no end state
                    self.assertEqual(end, timeless)          # a measurement without times sees the end state
        self.assertNotIn("Math.random", FAMILY.read_text(encoding="utf-8"))
        self.assertNotIn("Date.now", FAMILY.read_text(encoding="utf-8"))

    def test_steps_change_what_is_shown(self):
        pairs = [(("barChart", {"bars": GINI, "upto": 2}), ("barChart", {"bars": GINI, "upto": 3})),
                 (("marginalBars", {"values": "7;4", "line": "3"}), ("marginalBars", {"values": "7;4", "line": "3", "stop": True, "stopLabel": "रुको", "tower": "beside"})),
                 (("pictogram", {"n": 6, "on": 6}), ("pictogram", {"n": 6, "on": 4})),
                 (("iconArray", {"groups": "a:1;b:9", "split": "1;1"}), ("iconArray", {"groups": "a:1;b:9", "split": "1;1", "marks": True})),
                 (("timeSeries", {"series": SERIES}), ("timeSeries", {"series": SERIES, "window": "1929-1938"})),
                 (("scatterFit", {"points": LAMB}), ("scatterFit", {"points": LAMB, "fit2": "150 150", "model": 2})),
                 (("weightBars", {"applied": 1}), ("weightBars", {"applied": 2})),
                 (("shareBar", {"parts": "a:50;b:70"}), ("shareBar", {"parts": "a:50;b:70", "overflow": True}))]
        flat = [x for pr in pairs for x in pr]
        svgs = draw_all(flat)
        for k in range(len(pairs)):
            self.assertNotEqual(svgs[2 * k], svgs[2 * k + 1], pairs[k])

    def test_the_counts_follow_the_numbers(self):
        """A pictogram's live count, a waterfall's total and the multiplier's limit are the numbers the narration says."""
        svgs = draw_all([("pictogram", {"n": 6, "on": 4, "count": "{n} कप"}), ("pictogram", {"n": 6, "on": 4, "from": 6, "count": "{n} कप", "_t": 1, "_s": 0.05}),
                         ("waterfall", {"parts": "a:+100;b:-40;c:+150;d:-10", "total": "ΔM4", "unit": "₹"}),
                         ("roundBars", {"first": 100, "keep": 0.8, "unit": "₹"}),
                         ("weightBars", {"assets": "a:100:0;b:200:0.2;c:400:0.35;d:300:1", "applied": 4, "stack": True, "capital": 60}),
                         ("iconArray", {"n": 200, "groups": "a:100;b:9900", "split": "99;99", "marks": True, "gather": True, "gatherLabel": "{n} = {1} + {2}, {p1}%"})])
        self.assertIn(">4 कप<", svgs[0])
        self.assertIn(">6 कप<", svgs[1])
        self.assertIn("= ₹200", svgs[2])
        self.assertIn("₹500", svgs[3])
        self.assertIn("RWA ₹480", svgs[4])
        self.assertIn("CAR 12.5%", svgs[4])
        self.assertIn("198 = 99 + 99, 50%", svgs[5])


if __name__ == "__main__":
    unittest.main()


class PilotNeeds(unittest.TestCase):
    """Pilot ch02 v1 (Sloman): two small pies side by side were left unlabelled; a table column had to be rewritten
    cell by cell through ``cells`` on every step."""

    @classmethod
    def setUpClass(cls):
        if not shutil.which("node"):
            raise unittest.SkipTest("node is needed to measure the drawings")
        from bie.brain.video import boxes
        cls.boxes = boxes

    def test_a_small_pie_with_a_big_legend_reads_at_36px_and_the_default_is_unchanged(self):
        p = {"w": 500, "slices": "कॉफ़ी:30;बाकी:70"}
        small = self.boxes.item("pieChart", p)
        self.assertTrue(all(t["px"] < 36 for t in small["texts"]))
        big = self.boxes.item("pieChart", dict(p, legendSize=0.08))
        self.assertEqual(sorted(t["t"] for t in big["texts"]), ["कॉफ़ी 30%", "बाकी 70%"])   # values move into the legend
        self.assertTrue(all(t["px"] >= 36 for t in big["texts"]), big["texts"])
        self.assertEqual(self.boxes.item("pieChart", dict(p, legendSize=0.036)), small)
        self.assertEqual(saanche.problems("pieChart", {"legendSize": 0.2}), ["pieChart.legendSize: 0.2 is outside 0.02..0.09"])

    def test_a_table_column_fills_cell_by_cell(self):
        p = {"w": 900, "cols": "भाव;कुल", "cells": "₹50;700|₹40;500|₹30;350"}
        words = lambda q: [t["t"] for t in self.boxes.item("table", q)["texts"]]   # noqa: E731
        self.assertIn("350", words(p))
        one = words(dict(p, fill="2:1"))
        self.assertIn("700", one)
        self.assertNotIn("500", one)
        self.assertIn("₹30", one)                                                   # other columns stay whole
        self.assertNotIn("700", words(dict(p, fill="2:0")))
        self.assertEqual(saanche.problems("table", {"fill": "2:1"}), [])
