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
       "coinJar", "pillars", "briefcase", "podium", "staircase", "desk", "chair", "rope", "world", "flow"]
WORLDS = ["market", "bankHall", "centralBank", "exchangeFloor", "port", "factory", "village", "office", "court", "city", "assembly"]
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
                           ("मेज़", "desk"), ("कुर्सी", "chair"), ("रस्सी", "rope"), ("बंदरगाह", "world"), ("अदालत", "building"), ("प्रवाह", "flow")]:
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
        self.assertEqual(kinds, WORLDS)
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
        spec = sp.compile_plan(self._plan([world, sack, words], T), T, width=1920, height=1080)
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
        self.assertIn("if (t >= s.t && s.p) p = { ...p, ...s.p }", engine)
        self.assertIn("_t: Math.max(0, t - (el.t0 ?? 0))", engine)


if __name__ == "__main__":
    unittest.main()
