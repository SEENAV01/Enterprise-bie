"""Economy kit, batches 3 to 5 (4 Nov 2026): the saanche learned from the economy reference videos.

institutionBadge, paper, disc, vault, crowd, centralBank, committee and moneyBag are in the manifest with Hindi and
English words, and draw clean SVG (no NaN or undefined, balanced tags) at their defaults and in the variants a scene
plan will use (every badge kind and paper kind, open and closed vaults, shaded crowds, labels in Hindi). Batch 5 adds
the worlds (whole places behind the lesson that a scene plan can change in its steps), the same places as plain
backgrounds, the last recurring things (coin jar, pillars, briefcase, podium, staircase, desk, chair, rope, court) and
the flow saancha: a process world whose coins, notes or goods keep travelling along its arrows as the video plays.
A world never counts as the thing being shown: a scene of a world and a text alone is refused like text alone.
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
from bie.brain.gold.money_v2 import Timeline, build_script  # noqa: E402
from bie.brain.video import showplan as sp  # noqa: E402

ENGINE = ROOT / "bie" / "brain" / "video" / "engine"
NEW = ["institutionBadge", "paper", "disc", "vault", "crowd", "centralBank", "committee", "moneyBag",
       "building", "priceTag", "gauge", "foreignNote", "barrier", "segmentedBar", "cart", "piggyBank", "ruler", "hands",
       "coinJar", "pillars", "briefcase", "podium", "staircase", "desk", "chair", "rope", "world", "flow", "bands", "fork", "gapBars",
       "timeline", "table", "graph", "funnel", "roadmap", "plant"]
WORLDS = ["market", "bankHall", "centralBank", "exchangeFloor", "port", "factory", "village", "office", "court", "city", "assembly",
          "twoCountries", "forexCounter"]
VARIANTS = (
    [("institutionBadge", {"kind": k, "name": n, "sub": "उप"}) for k, n in
     [("central_bank", "RBI"), ("bank", "SBI"), ("government", "सरकार"), ("regulator", "SEBI"), ("international", "IMF"),
      ("cooperative", "PACS"), ("committee", "MPC"), ("market", "NSE"), ("company", "XYZ")]]
    + [("paper", {"kind": k, "title": "शीर्षक", "year": "1934", "value": "₹1,000", "note": "6% हर साल", "stamp": "AMENDED"})
       for k in ("law", "bond", "licence", "contract", "bill", "report")]
    + [("paper", {"lines": 0}), ("paper", {"lines": 8, "title": ""})]
    + [("vault", {"door": d, "fill": f, "locked": lk, "label": "CRR", "tag": "0% ब्याज", "metal": m})
       for d, f, lk, m in [(0, 0, True, "gold"), (0.3, 0.12, True, "gold"), (0.7, 0.5, False, "steel"), (1, 1, False, "steel")]]
    + [("crowd", {"n": 140, "cols": 20, "share": 0.6, "shareLabel": "पहुँच", "restColor": "#e5484d", "restLabel": "बाहर",
                  "label": "140 करोड़ लोग", "dimRest": True}), ("crowd", {"n": 1, "cols": 1, "share": 1})]
    + [("committee", {"n": n, "name": "मौद्रिक नीति समिति", "sub": "6 सदस्य"}) for n in (1, 6, 12)]
    + [("moneyBag", {"w": 40, "sign": ""}), ("moneyBag", {"w": 400, "label": "विदेशी मुद्रा"})]
    + [("disc", {"text": "4.5%"}), ("disc", {"text": "FIXED", "color": "#2459a6"})]
    + [("centralBank", {"label": ""}), ("centralBank", {"label": "भारतीय रिज़र्व बैंक"})]
    + [("building", {"kind": k, "label": "नाम"}) for k in ("office", "government", "exchange", "house", "tower", "shop", "warehouse", "hut")]
    + [("paper", {"kind": k, "title": "Share", "value": "₹10"}) for k in ("share", "unit")]
    + [("priceTag", {"value": "₹65", "old": "₹50", "trend": "up"}), ("priceTag", {"value": "₹40", "trend": "down"}), ("priceTag", {"trend": "none"})]
    + [("gauge", {"value": v, "text": "0.64", "label": "HDI", "reverse": r}) for v, r in ((0, False), (0.5, True), (1, False))]
    + [("foreignNote", {"sign": s, "value": "50"}) for s in ("$", "€", "£", "¥", "¤")]
    + [("barrier", {"label": "रोक"}), ("barrier", {"w": 60})]
    + [("segmentedBar", {"parts": "Food:46;Fuel:7;Core:47", "cross": "1,2", "label": "CPI"}), ("segmentedBar", {"parts": "Food:46;Fuel:7;Core:47", "hide": "1,2", "label": "Core"}),
       ("segmentedBar", {"parts": "CRR:3;SLR:18;कर्ज़:79", "unit": "", "glow": "1"}), ("segmentedBar", {"parts": "", "shrink": False}), ("segmentedBar", {"parts": "a:0;b:0"})]
    + [("cart", {"content": c, "label": "म्यूचुअल फंड"}) for c in ("veg", "notes", "goods", "empty")]
    + [("piggyBank", {"label": "NBFC"}), ("ruler", {"min": 100, "max": 75000, "value": 6590, "text": "$6,590", "minLabel": "$100", "maxLabel": "$75,000"}),
       ("ruler", {"min": 20, "max": 85, "value": 90}), ("ruler", {"min": 5, "max": 5, "value": 5})]
    + [("paper", {"kind": k, "title": "IDR"}) for k in ("receipt", "invoice")]
    + [("hands", {"item": it, "from": "पैसा ज़्यादा", "to": "पैसे की ज़रूरत"}) for it in ("notes", "coin", "paper", "none")]
    + [("building", {"kind": "court", "label": "अदालत"})]
    + [("coinJar", {"fill": f, "label": "बचत"}) for f in (0, 0.5, 1)]
    + [("pillars", {"labels": "पूंजी;निगरानी;खुलासा", "title": "Basel III", "broken": "2", "glow": "1"}), ("pillars", {"n": 6}), ("pillars", {"n": 1, "labels": "", "broken": "x,0"})]
    + [("briefcase", {"label": "बजट", "open": o}) for o in (False, True)]
    + [("podium", {"labels": "अमेरिका;चीन;भारत"}), ("podium", {"labels": "एक"})]
    + [("staircase", {"labels": "M0;M1;M2;M3;M4", "at": 3}), ("staircase", {"n": 8, "dir": "down", "at": 8}), ("staircase", {"labels": "a", "n": 2})]
    + [("desk", {"label": "साहूकार", "chair": c}) for c in (True, False)]
    + [("chair", {"kind": k, "label": "पद"}) for k in ("plain", "office", "big")]
    + [("rope", {"kind": k, "sag": sg, "angle": a, "label": "पेग"}) for k, sg, a in (("rope", 0.3, 0), ("rod", 0.5, 30), ("chain", 0, -45), ("chain", 1, 180))]
    + [("world", {"kind": k, "label": "नाम", "signs": "जमा;निकासी;कर्ज़", "crowd": True, "open": True, "trend": "down",
                  "smoke": False, "season": "harvest", "light": lt, "color": "#e8e1d3"}) for k in WORLDS for lt in ("day", "night")]
    + [("world", {"kind": k, "w": 400, "count": 12}) for k in WORLDS] + [("world", {"kind": k}) for k in WORLDS]
    + [("flow", {"nodes": "परिवार:house;कंपनी:warehouse;सरकार:government;बैंक:bank;RBI:centralBank;लोग:people;दुनिया:globe;डिब्बा:box",
                 "edges": "1>2:खर्च;2>1:मज़दूरी;1>4;4>2:कर्ज़;5>4;8>7;x>y;1>1;1>9", "layout": lay, "token": tok, "active": act, "_t": tt})
       for lay, tok, act, tt in (("ring", "coin", "", 0), ("row", "note", "1,3", 2.5), ("hub", "goods", "2", 7), ("ring", "dot", "9", None))]
    + [("flow", {"nodes": "एक:house", "edges": "1>2"}), ("flow", {"nodes": "a:box;b:box", "edges": "1>2:x;2>1:y", "bend": -1, "speed": 0})]
    + [("flow", {"nodes": "भारत:box;अमेरिका:globe", "edges": "1>2:माल@goods;2>1:डॉलर@note;1>2:@dot;2>1:x@moon", "layout": "row", "_t": 1.5})]
    + [("bands", {"zones": "Creeping:0-3;Walking:3-10;Running:10-50;Hyper:50+", "value": v, "unit": "%", "glow": "2", "title": "महँगाई"}) for v in ("7", "0", "75", "-4", "")]
    + [("bands", {"zones": "कम;मध्यम;ज़्यादा", "reverse": True}), ("bands", {"zones": "a:x-y", "value": "3"})]
    + [("fork", {"from": "CRR", "up": "कम", "upNote": "बैंक ज़्यादा कर्ज़ दें", "upResult": "महँगाई ↑", "down": "ज़्यादा", "downNote": "कर्ज़ कम",
                 "downResult": "महँगाई ↓", "glow": g}) for g in ("", "up", "down")]
    + [("gapBars", {"a": a, "b": b, "gap": "घाटा", "unit": " लाख करोड़"}) for a, b in (("खर्च:45", "कमाई:30"), ("आयात:30", "निर्यात:45"), ("a:0", "b:0"), ("x", ""))]
    + [("timeline", {"events": "1935:RBI Act;1949:राष्ट्रीयकरण;1969:14 बैंक;1991:सुधार;2016:MPC", "zones": "1935-1969:निजी;1969-1991:सरकारी;x-y:z;1991-1950:उल्टा",
                     "at": a, "upto": u, "title": "बैंकिंग"}) for a, u in ((0, 0), (3, 3), (12, 12))]
    + [("timeline", {"events": "पहले:बार्टर;फिर:सिक्के;अब:UPI"}), ("timeline", {"events": "2020:एक"}), ("timeline", {"events": "1991:a;1991:b", "even": True})]
    + [("table", {"cols": "M1;M2;M3;M4", "rows": "नकद;माँग जमा;डाक बचत;समय जमा", "cells": "✓;✓;✓;✓|✓;✓;✓;✓|;✓;;✓|;;✓;✓", "glowCol": "3", "glowRow": "9", "upto": u})
       for u in (0, 2)]
    + [("table", {"cells": "a;b;c|x;✗;tick|1"}), ("table", {"cols": "only"}), ("table", {"rows": "a;b", "cells": "|"})]
    + [("graph", {"lines": "D:1,9 5,5 9,1;S:1,1 5,5 9,9;S2:2,1 6,5 10,9", "dashed": "3", "dots": "5,5:E;x,y:bad", "xLabel": "मात्रा", "yLabel": "कीमत",
                  "drawIn": d, "_t": t, "ticks": True, "title": "माँग-पूर्ति"}) for d, t in ((0, None), (2, 0.5), (2, 9))]
    + [("graph", {"lines": "J:0,5 2,3 4,3 10,8", "ymin": -5, "ymax": 10, "smooth": False, "drop": False, "dots": "3,3"}),
       ("graph", {"lines": "a:1,1;b:x", "xmin": 5, "xmax": 5}), ("graph", {"lines": "1,1 2,2"})]
    + [("graph", {"lines": "D:1,9 9,1;S:1,1 9,9;D2:3,9 10,3", "show": sh, "grow": gr, "drawIn": 2, "_t": t, "_s": s,
                  "colors": "3:#e76f51;x:bad", "bold": "2", "areas": "बचत:0,9 5,5 0,5@#f4a261;bad:1,1;राजस्व:0,5 4,5 4,3 0,3",
                  "hlines": "3:अधिकतम मूल्य;x:bad", "vlines": "4:कोटा", "arrows": "5,6>6.5,6:माँग बढ़ी;1,1>bad", "gaps": "3,7@3:कमी;x@1",
                  "xTicks": "5:Q1;x:Q9", "yTicks": "5:P1", "dots": "6,6<5,5:E2;5,5:E;bad<1,1", "glide": 1.5})
       for sh, gr, t, s in (("", "", 3, 3), ("1", "", 1, 1), ("1,2", "2", 4, 0.5), ("1,2,3", "3,a1", 9, None))]
    + [("graph", {"lines": "D:1,9 9,1;S:1,1 9,9;D2:3,9 10,3.4", "slide": "3:-2,0;x:1;9:1,1", "morph": "2:1,5 9,5;3:bad",
                  "along": "1@0.5<1@0.1:P={y};9@0.5;1@x", "segs": "3,6.6>7,3.4:स्पर्श;bad", "path": "5,5:a;6,6:b;bad:c;7,5.5:c",
                  "pathUpto": u, "glide": 2, "_t": t, "_s": s})
       for u, t, s in ((0, 1, 0.1), (2, 3, 1), (99, 9, None))]
    + [("funnel", {"label": "40%", "top": "₹1000", "bottom": "₹2500", "flip": f}) for f in (False, True)]
    + [("roadmap", {"items": "M0;M1;M2;M3;M4", "at": a, "done": d, "title": "आज"}) for a, d in ((0, ""), (3, ""), (5, "5"), (9, "x"))]
    + [("plant", {"stage": g, "fruit": f, "label": "वेंचर फंड"}) for g in (0, 0.3, 0.7, 1) for f in ("coin", "note", "none")]
    + [("building", {"kind": "factory", "label": "SIDBI", "sick": s}) for s in (False, True)]
    + [(n, {}) for n in NEW]
)


def balanced(svg: str) -> bool:
    stack = []
    for close, tag, selfclose in re.findall(r"<(/?)([a-zA-Z]+)(?:\s[^<>]*?)?(/?)>", svg):
        if close:
            if not stack or stack.pop() != tag:
                return False
        elif not selfclose:
            stack.append(tag)
    return not stack


class EconSaanche(unittest.TestCase):
    def test_they_are_in_the_manifest_with_hindi_and_english_words(self):
        for name in NEW:
            entry = saanche.get(name)
            self.assertIsNotNone(entry, name)
            self.assertEqual(entry["since"], "2026-11-04")
            self.assertTrue(any(not t.isascii() for t in entry["tags"]), name)
            self.assertTrue(any(t.isascii() for t in entry["tags"]), name)

    def test_a_search_in_hindi_finds_them(self):
        for word, name in [("तिजोरी", "vault"), ("समिति", "committee"), ("कानून", "paper"), ("भीड़", "crowd"), ("थैली", "moneyBag"),
                           ("गोदाम", "building"), ("दाम", "priceTag"), ("मीटर", "gauge"), ("डॉलर", "foreignNote"), ("दीवार", "barrier"), ("बँटवारा", "segmentedBar"), ("ठेला", "cart"), ("गुल्लक", "piggyBank"), ("पैमाना", "ruler"), ("उधार", "hands"),
                           ("जार", "coinJar"), ("स्तंभ", "pillars"), ("अटैची", "briefcase"), ("मंच", "podium"), ("सीढ़ी", "staircase"),
                           ("मेज़", "desk"), ("कुर्सी", "chair"), ("रस्सी", "rope"), ("बंदरगाह", "world"), ("अदालत", "building"), ("प्रवाह", "flow"), ("घाटा", "gapBars"), ("दोराहा", "fork"), ("दायरा", "bands"), ("सीमा", "world"), ("समयरेखा", "timeline"), ("तालिका", "table"), ("ग्राफ़", "graph"), ("कीप", "funnel"), ("एजेंडा", "roadmap"), ("पौधा", "plant"), ("कारख़ाना", "building")]:
            found = [r.get("name") for r in saanche.search(word) if r.get("kind") == "draw"]
            self.assertIn(name, found, word)

    @unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
    def test_every_variant_draws_clean_svg(self):
        script = (f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                  f"const cases = {json.dumps(VARIANTS, ensure_ascii=False)};"
                  "console.log(JSON.stringify(cases.map(([n, p]) => drawSaancha(n, p))));")
        out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True)
        svgs = json.loads(out.stdout)
        self.assertEqual(len(svgs), len(VARIANTS))
        for (name, params), svg in zip(VARIANTS, svgs):
            with self.subTest(name=name, params=params):
                self.assertTrue(svg.strip())
                self.assertNotRegex(svg, r"NaN|undefined")
                self.assertTrue(balanced(svg))
                self.assertNotIn("stroke-width=\"-", svg)


class Worlds(unittest.TestCase):
    def test_every_world_kind_is_in_the_manifest_and_a_plain_background_too(self):
        kinds = saanche.get("world")["params"]["kind"]["choices"]
        self.assertEqual(kinds[:len(WORLDS)], WORLDS)               # the Sloman places follow (tests/test_p1_fam_econ_worlds.py)
        engine = (ENGINE / "worlds.mjs").read_text(encoding="utf-8")
        bgs = (ENGINE / "backgrounds.mjs").read_text(encoding="utf-8")
        vocab = sp.vocab()["backgrounds"]
        for k in kinds:
            self.assertIn(f"  {k}(W, H, p)", engine, k)
            if k != "village":                                   # the Money v2 village background keeps its name
                self.assertIn(f'{k}: () => worldBg("{k}")', bgs, k)
                self.assertIn(k, vocab, k)

    def test_no_world_writes_words_of_its_own(self):
        engine = (ENGINE / "worlds.mjs").read_text(encoding="utf-8")
        self.assertNotRegex(engine, r"[\u0900-\u097F]")          # no Hindi baked in: words come from the plan
        for name in ("NIFTY", "SENSEX", "RBI", "SBI"):           # no real index or institution names
            self.assertNotIn(name, engine)

    def _plan(self, steps, T):
        return {"schema": "bie.scene-plan/1", "scenes": [
            {"id": "A", "lines": T.line_ids(), "bg": "bankHall", "cam": [], "steps": steps}]}

    def test_a_world_is_the_place_not_the_thing_shown(self):
        T = Timeline(build_script())
        world = {"op": "item", "thing": {"draw": "world", "p": {"kind": "bankHall", "signs": "जमा;निकासी", "open": False}},
                 "x": 960, "y": 540, "z": 1, "enter": "none",
                 "steps": [{"t": {"line": "l01", "frac": 0.5}, "p": {"open": True}}]}
        words = {"op": "text", "text": "Barter", "x": 960, "y": 200, "size": 64, "style": "title"}
        with self.assertRaises(sp.PlanProblems) as ctx:
            sp.compile_plan(self._plan([world, words], T), T, width=1920, height=1080)
        self.assertTrue(any("only text on screen" in p for p in ctx.exception.problems), ctx.exception.problems)
        sack = {"op": "item", "thing": {"draw": "sack", "p": {"w": 220}}, "x": 1200, "y": 885}
        spec = sp.compile_plan(self._plan([world, sack, words], T), T, width=1920, height=1080,
                               said_shown=False)          # the world's mechanics; dikhaya-bola has its own tests
        els = spec["scenes"][0]["els"]
        self.assertEqual(els[0]["draw"], "world")
        self.assertEqual(spec["scenes"][0]["bg"], "bankHall")
        self.assertEqual(els[0]["steps"][0]["p"], {"open": True})
        bad = json.loads(json.dumps(world))
        bad["steps"][0]["p"] = {"open": "yes", "kind": "moon"}                # a content change obeys the manifest too
        with self.assertRaises(sp.PlanProblems) as ctx:
            sp.compile_plan(self._plan([bad, sack, words], T), T, width=1920, height=1080)
        self.assertTrue(any("step at" in p and "world.kind" in p for p in ctx.exception.problems), ctx.exception.problems)

    @unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
    def test_a_step_changes_a_drawn_thing_from_its_time_on(self):
        script = (f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                  "console.log(JSON.stringify([drawSaancha('world', {kind: 'bankHall'}), drawSaancha('world', {kind: 'bankHall', open: true})]));")
        closed, opened = json.loads(subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout)
        self.assertNotEqual(closed, opened)
        script = (f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                  "const p = {nodes: 'a:house;b:bank', edges: '1>2:x'};"
                  "console.log(JSON.stringify([0, 0, 0.7].map((t) => drawSaancha('flow', {...p, _t: t}))));")
        a, b, c = json.loads(subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(a, b)                                        # a process is a pure function of its time
        self.assertNotEqual(a, c)                                     # and its tokens travel as the video plays
        engine = (ENGINE / "engine.mjs").read_text(encoding="utf-8")
        self.assertIn("p = { ...p, ...s.p }; last = s.t;", engine)
        self.assertIn("_t: Math.max(0, t - (el.t0 ?? 0)), _s: Math.max(0, t - last)", engine)

    def test_a_step_may_glide_its_numbers(self):
        """A step with d makes the numbers glide from their old values over d seconds (a bar grows, a level rises)."""
        engine = (ENGINE / "engine.mjs").read_text(encoding="utf-8")
        self.assertIn("const d = Number(s.d) || 0;", engine)
        self.assertIn("p[k] = prev[k] + (s.p[k] - prev[k]) * e;", engine)
        from bie.brain.video import narration, showplan
        from bie.brain.video.showplan import Recorder, plan_of
        T = narration.Timeline([{"id": "A", "lines": [{"id": "l01", "sub": "जार भरता है।", "say_parts": ["जार भरता है।"]}]}])
        def plan(d):
            s = Recorder("A", ["l01"], "paper")
            s.item({"draw": "coinJar", "p": {"w": 300}}, 960, 700, t0=0.2, steps=[{"t": 0.5, "p": {"w": 400}, "d": d}])
            return plan_of([s])
        showplan.compile_plan(plan(1.5), T, width=1920, height=1080)
        with self.assertRaises(showplan.PlanProblems) as bad:
            showplan.compile_plan(plan(99), T, width=1920, height=1080)
        self.assertIn("d must be 0-30 seconds", "\n".join(bad.exception.problems))

    @unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
    def test_the_graph_is_built_at_the_voice_speed(self):
        """A line shown on a step draws over drawIn seconds after that step (_s), a dot glides to its new place, and the
        whole drawing is a pure function of its times (the Sloman book's graphs, 5 November 2026)."""
        script = (f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                  "const p = {lines: 'D:1,9 9,1;S:1,1 9,9', show: '1,2', grow: '2', drawIn: 2, dots: '6,6<5,5:E2', glide: 1};"
                  "console.log(JSON.stringify([[0.2, 0.2], [0.2, 0.2], [5, 1], [9, 3], [9, null]].map(([t, s]) => drawSaancha('graph', {...p, _t: t, _s: s}))));")
        a, b, c, d, e = json.loads(subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True,
                                                  check=True).stdout)
        self.assertEqual(a, b)                                        # pure
        self.assertNotEqual(a, c)                                     # line 2 grows and the dot glides after the step
        self.assertIn('stroke-dasharray="0.1 1"', a)                  # line 2 is a tenth drawn 0.2 s after its step
        self.assertIn('stroke-dasharray="1 1"', d)                    # and whole once drawIn has passed
        self.assertEqual(d, e)                                        # a measurement without times sees the end state
        hidden = subprocess.run(["node", "--input-type=module", "-e",
                                 f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                                 "console.log(drawSaancha('graph', {lines: 'D:1,9 9,1;S:1,1 9,9', show: '1'}).split('<path').length);"],
                                capture_output=True, text=True, check=True).stdout
        both = subprocess.run(["node", "--input-type=module", "-e",
                               f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                               "console.log(drawSaancha('graph', {lines: 'D:1,9 9,1;S:1,1 9,9'}).split('<path').length);"],
                              capture_output=True, text=True, check=True).stdout
        self.assertEqual(int(both) - int(hidden), 1)                  # show hides the lines not yet spoken of


if __name__ == "__main__":
    unittest.main()
