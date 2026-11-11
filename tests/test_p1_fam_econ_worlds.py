"""The worlds family (Sloman economics book, 5 November 2026): the places of the book's stories as world kinds whose
state changes on the word.

Nineteen new kinds join the world saancha (grain mandi, food street, labour chowk, factory floor, farm, river town,
mohalla, canteen, home, tea estate, bus stand, petrol pump, venue, godown, island, two-sector economy, dealing room,
hospital, food shop / dhaba) and five old ones learn state (market: prices, stock, shutters, queues, festival lights;
bank hall: a queue and the vault's money; exchange floor: ticker rows and an index line; factory: emission, filter,
limit, counter, belt; city: traffic and smog). Their state is parameters a step sets on its cue word; `was` holds the
values just before the step, so a board strikes the old value and counts, levels and shutters move from it over glide
seconds. Every kind is a plain background too, names its spots exactly as bie/brain/game_levels.py does, and writes no
words of its own.
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

from bie.brain import game_levels as gl  # noqa: E402
from bie.brain import saanche  # noqa: E402
from bie.brain.video import showplan as sp  # noqa: E402

ENGINE = ROOT / "bie" / "brain" / "video" / "engine"
OLD = ["market", "bankHall", "centralBank", "exchangeFloor", "port", "factory", "village", "office", "court", "city", "assembly",
       "twoCountries", "forexCounter"]
NEW = ["mandi", "foodStreet", "labourChowk", "factoryFloor", "farm", "riverTown", "mohalla", "canteen", "home", "teaEstate",
       "busStand", "petrolPump", "venue", "godown", "island", "twoSector", "dealingRoom", "hospital", "foodShop"]
ALL = OLD + NEW

# The states a scene plan will use (test data: Claude's own examples, not BIE output).
STATES = [
    ("mandi", {"prices": "₹1,800", "was": "prices:₹2,100|people:16", "trend": "down", "people": 5, "counts": "20;28;9", "glow": "2",
               "notice": "MSP ₹2,000", "taken": 6, "vehicles": 2, "signs": "रामू;श्याम;गीता"}),
    ("foodStreet", {"count": 12, "signs": "रवि;गीता", "prices": "₹30;₹35", "was": "prices:₹30;₹30|shut:", "shut": "3,7", "levels": "1;0.5",
                    "counts": "3;0;5", "seats": 4, "glow": "1,seats", "festive": "wedding", "light": "night", "people": 6}),
    ("labourChowk", {"prices": "₹400", "was": "prices:₹500|taken:2|people:12", "people": 8, "taken": 30, "vehicles": 3, "shut": "road", "light": "dawn"}),
    ("factoryFloor", {"count": 8, "running": 5, "people": 9, "value": "1,548", "was": "value:1,200|running:2", "notice": "लक्ष्य", "goods": 60, "level": 0.9,
                      "signs": "A;B", "item": "glass"}),
    ("factoryFloor", {"item": "shirt", "count": 1, "running": 0, "people": 0, "goods": 0}),
    ("factoryFloor", {"item": "cloth", "running": 3}),
    ("farm", {"count": 6, "levels": "1;0.5;0;1;0.2;1", "people": 8, "was": "people:7", "goods": 60, "glow": "fence,3", "crop": "cotton",
              "weather": "pests", "season": "harvest", "signs": "घाटी;पहाड़ी"}),
    ("farm", {"weather": "flood", "crop": "none", "level": 0}),
    ("riverTown", {"level": 1, "goods": 0, "part": 9, "rate": 1, "value": "25", "was": "value:12|level:0", "filter": True, "vehicles": 3, "people": 12}),
    ("mohalla", {"count": 8, "levels": "0;0.2;0.4;0.6;0.8;1;0.5;0.5", "was": "levels:1;1;1;1;1;1;1;1", "counts": "0;0;0;1;2;3;0;1",
                 "signs": "शर्मा;खान", "glow": "4", "festive": "diwali", "light": "evening"}),
    ("canteen", {"signs": "समोसा;चाय;सैंडविच;पोहा;जलेबी;लस्सी", "prices": "₹20;₹10;₹20;₹25;₹15;₹30", "was": "prices:₹15", "levels": "0;1;0.5;0.2",
                 "people": 20, "notice": "शनिवार"}),
    ("home", {"on": True, "goods": 30, "level": 0, "glow": "stove,fridge,tv,door", "notice": "टिफ़िन ₹80", "light": "night"}),
    ("teaEstate", {"prices": "₹350", "was": "prices:₹232|shut:", "shut": "gate", "people": 30, "notice": "यूनियन"}),
    ("busStand", {"count": 4, "signs": "लाल;नीली;हरी;पीली", "prices": "₹40;₹50;₹45;₹50", "was": "prices:₹50|shut:", "shut": "2",
                  "counts": "8;0;3;1", "levels": "1;0;0.5;0.2", "value": "₹4,000"}),
    ("petrolPump", {"count": 4, "signs": "A;B;C;D", "prices": "₹110;₹102", "was": "prices:₹100;₹102|value:1000", "value": "1,250",
                    "counts": "0;5;9;1", "shut": "4", "light": "night"}),
    ("venue", {"seats": 600, "taken": 600, "part": 250, "people": 20, "notice": "हाउसफुल", "shut": "door", "signs": "बच्चे;बड़े",
               "prices": "₹80;₹150", "was": "prices:₹50;₹100|taken:300", "on": False}),
    ("venue", {"seats": 1, "taken": 0}),
    ("godown", {"prices": "₹28/किलो", "was": "prices:₹20/किलो|level:0.8", "level": 1, "flow": "out", "trend": "up", "notice": "अक्टूबर", "value": "₹500"}),
    ("godown", {"level": 0, "flow": "in", "shut": "door"}),
    ("island", {"count": 6, "neighbour": "hostile", "level": 0.1, "was": "level:0.9", "goods": 5, "weather": "drought", "crop": "wheat"}),
    ("island", {"neighbour": "friendly", "crop": "none"}),
    ("twoSector", {"signs": "खेत;कपड़ा", "people": 30, "taken": 12, "part": 6, "was": "taken:5", "counts": "60;0", "weather": "rain"}),
    ("dealingRoom", {"count": 6, "signs": "A;B;C;D;E;F", "prices": "6.8%;7.5%", "links": "1-2;5-6;x-y;1-9;3-3", "level": 0.2,
                     "value": "6.8%", "was": "value:5.2%|links:1-2;2-3", "trend": "up"}),
    ("hospital", {"count": 4, "signs": "डॉ. A;डॉ. B", "people": 40, "seats": 8, "taken": 8}),
    ("foodShop", {"item": "roti", "prices": "रोटी ₹10;दाल ₹60", "was": "prices:रोटी ₹8;दाल ₹60|value:₹3,000", "people": 6, "count": 4,
                  "counts": "12;9;6;3", "notice": "किराया ₹20,000", "value": "₹3,400", "taken": 3, "glow": "oven,till,counter", "shut": "shutter"}),
    ("foodShop", {"item": "bread"}), ("foodShop", {"item": "tea"}), ("foodShop", {"item": "jalebi", "goods": 60}), ("foodShop", {"item": "mithai"}),
    ("market", {"signs": "सब्ज़ी;फल;कपड़े;बर्तन", "prices": "₹40;₹60", "was": "prices:₹30|shut:|people:12", "shut": "2,4", "levels": "0;0.5;1;1",
                "counts": "2;0;9;0", "people": 3, "glow": "1", "festive": "diwali", "light": "evening"}),
    ("bankHall", {"signs": "जमा;निकासी", "people": 60, "open": True, "level": 0.2, "was": "level:0.9|people:10"}),
    ("exchangeFloor", {"signs": "कंपनी A:98;कंपनी B:70;bad", "was": "signs:कंपनी A:120|points:", "points": "116;110;104;95;90",
                       "value": "22,800", "trend": "down", "people": 10}),
    ("exchangeFloor", {"points": "5"}),
    ("factory", {"level": 0.9, "filter": True, "notice": "सीमा", "value": "500", "rate": 1}),
    ("factory", {"level": 0.9, "notice": "सीमा"}),
    ("city", {"level": 0.8, "vehicles": 12}),
    ("village", {"weather": "rain"}), ("port", {"weather": "flood"}), ("twoCountries", {"weather": "drought"}),
]
TIMES = [(None, None), (0.0, 0.0), (2.0, 0.4), (9.0, 9.0)]


def node(script: str):
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def draw_all(cases):
    """cases: [[p, t, s]] -> the SVGs of the world drawn by drawSaancha (the way the engine draws it)."""
    script = (f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
              f"const cases = {json.dumps(cases, ensure_ascii=False)};"
              "console.log(JSON.stringify(cases.map(([p, t, s]) => drawSaancha('world', t === null ? p : {...p, _t: t, _s: s}))));")
    return node(script)


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
    def test_every_new_kind_is_in_the_manifest_the_engine_the_backgrounds_and_the_zones(self):
        kinds = saanche.get("world")["params"]["kind"]["choices"]
        self.assertEqual(kinds, ALL)
        engine = (ENGINE / "worlds.mjs").read_text(encoding="utf-8")
        bgs = (ENGINE / "backgrounds.mjs").read_text(encoding="utf-8")
        vocab = sp.vocab()["backgrounds"]
        zones = re.search(r"export const WORLD_ZONES = \{(.*?)\n\};", bgs, re.S).group(1)
        for k in NEW:
            self.assertIn(f"  {k}(W, H, p)", engine, k)
            self.assertIn(f'{k}: () => worldBg("{k}")', bgs, k)
            self.assertIn(k, vocab, k)
            self.assertRegex(zones, rf"\b{k}: \{{", k)
            self.assertIn(k, gl._FIXED_SPOTS, k)

    def test_the_world_engine_stays_one_self_contained_file(self):
        engine = (ENGINE / "worlds.mjs").read_text(encoding="utf-8")
        self.assertNotRegex(engine, r"^import ", "the game page embeds worlds.mjs as it is: no imports")
        self.assertNotRegex(engine, r"[ऀ-ॿ]")              # no Hindi baked in: words come from the plan
        for name in ("NIFTY", "SENSEX", "RBI", "SBI", "LIBOR", "Indian Oil", "HPCL"):
            self.assertNotIn(name, engine)

    def test_wrong_states_are_refused_with_the_field_named(self):
        good = {"kind": "mandi", "prices": "₹1,800", "was": "prices:₹2,100", "people": 5, "taken": 0, "level": 0.5, "glide": 2,
                "light": "dawn", "weather": "rain", "crop": "onion", "item": "shirt", "festive": "diwali", "neighbour": "hostile",
                "on": True, "flow": "in", "filter": True, "running": 3, "seats": 500, "vehicles": 2, "rate": 0.3}
        self.assertEqual(saanche.problems("world", good), [])
        for key, bad in [("people", 99), ("people", -2), ("level", 2), ("light", "noon"), ("crop", "moon"), ("running", 13),
                         ("glide", 0), ("seats", 700), ("weather", "snow"), ("on", "yes"), ("taken", 1.5), ("kind", "moon")]:
            with self.subTest(key=key, value=bad):
                probs = saanche.problems("world", {"kind": "mandi", key: bad})
                self.assertTrue(probs and all(f"world.{key}" in q for q in probs), probs)

    def test_a_search_in_hindi_finds_the_places(self):
        for word in ("मंडी", "लेबर चौक", "ढाबा", "मोहल्ला", "गोदाम", "पेट्रोल पंप", "टापू", "चाय बागान", "dealing room"):
            found = [r.get("name") for r in saanche.search(word) if r.get("kind") == "draw"]
            self.assertIn("world", found, word)


@unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
class Drawing(unittest.TestCase):
    def test_every_kind_draws_clean_svg_at_defaults_small_and_in_its_states(self):
        cases = ([[{"kind": k}, t, s] for k in ALL for t, s in TIMES] + [[{"kind": k, "w": 400, "count": 12}, 1.0, 0.2] for k in ALL]
                 + [[dict(p, kind=k), t, s] for k, p in STATES for t, s in TIMES])
        for (p, t, s), svg in zip(cases, draw_all(cases)):
            with self.subTest(p=p, t=t, s=s):
                self.assertTrue(svg.strip())
                self.assertNotRegex(svg, r"NaN|undefined|Infinity")
                self.assertTrue(balanced(svg))
                self.assertNotIn('stroke-width="-', svg)
                self.assertNotRegex(svg, r'(?:width|height|r|rx|ry)="-')

    def test_a_new_place_writes_no_words_of_its_own(self):
        svgs = draw_all([[{"kind": k}, 2.0, None] for k in NEW])
        for k, svg in zip(NEW, svgs):
            self.assertNotIn("<text", svg, k)

    def test_a_board_strikes_the_old_value_beside_the_new(self):
        plain, struck, chowk = draw_all([[{"kind": "mandi", "prices": "₹1,800"}, 1.0, None],
                                         [{"kind": "mandi", "prices": "₹1,800", "was": "prices:₹2,100"}, 1.0, 0.2],
                                         [{"kind": "labourChowk", "prices": "₹400", "was": "prices:₹500"}, 1.0, None]])
        self.assertIn("₹1,800", plain)
        self.assertNotIn("₹2,100", plain)
        self.assertIn("₹1,800", struck)
        self.assertIn("₹2,100", struck)
        self.assertIn('stroke="#e5484d"', struck)                    # the strike line
        self.assertIn("₹500", chowk)
        rows = draw_all([[{"kind": "canteen", "signs": "समोसा;चाय", "prices": "₹20;₹10", "was": "prices:₹15;₹10"}, 1.0, None]])[0]
        self.assertIn("₹15", rows)                                   # the changed row is struck
        self.assertEqual(rows.count("₹10"), 1)                       # an unchanged row is not

    def test_counts_and_levels_move_from_was_over_glide_seconds(self):
        p = {"kind": "labourChowk", "people": 8, "taken": 6, "was": "taken:2|people:12"}
        at0, mid, end, later, timeless, nowas = draw_all([[p, 3.0, 0.0], [p, 3.0, 0.75], [p, 3.0, 1.5], [p, 3.0, 40.0], [p, None, None],
                                                          [{"kind": "labourChowk", "people": 8, "taken": 6}, None, None]])
        self.assertNotEqual(at0, mid)                                # workers walk to the truck after the step
        self.assertNotEqual(mid, end)
        self.assertEqual(end, later)                                 # once glide has passed it is the new state
        self.assertEqual(timeless, nowas)                            # and was only says where things came from
        gl2 = dict(p, glide=4)
        slow, fast = draw_all([[gl2, 3.0, 1.5], [p, 3.0, 1.5]])
        self.assertNotEqual(slow, fast)                              # glide sets how long the move takes
        shut0, shut1 = draw_all([[{"kind": "market", "shut": "2", "was": "shut:"}, 1.0, 0.0], [{"kind": "market", "shut": "2", "was": "shut:"}, 1.0, 5.0]])
        self.assertNotEqual(shut0, shut1)                            # a shutter rolls down on its word

    def test_a_step_changes_the_place(self):
        pairs = [({"kind": "mandi", "goods": 10}, {"kind": "mandi", "goods": 40}), ({"kind": "factoryFloor", "running": 1}, {"kind": "factoryFloor", "running": 4}),
                 ({"kind": "mohalla", "levels": "0.1"}, {"kind": "mohalla", "levels": "0.95"}), ({"kind": "farm", "weather": "none"}, {"kind": "farm", "weather": "drought"}),
                 ({"kind": "venue", "taken": 0}, {"kind": "venue", "taken": 80}), ({"kind": "riverTown", "level": 0}, {"kind": "riverTown", "level": 0.9}),
                 ({"kind": "teaEstate"}, {"kind": "teaEstate", "shut": "gate"}), ({"kind": "home"}, {"kind": "home", "on": True}),
                 ({"kind": "dealingRoom", "links": "1-2"}, {"kind": "dealingRoom", "links": "1-2", "level": 0.1}),
                 ({"kind": "island"}, {"kind": "island", "neighbour": "hostile"}), ({"kind": "bankHall", "people": 0}, {"kind": "bankHall", "people": 30}),
                 ({"kind": "city"}, {"kind": "city", "level": 0.7})]
        svgs = draw_all([[q, 1.0, None] for a, b in pairs for q in (a, b)])
        for i, (a, b) in enumerate(pairs):
            self.assertNotEqual(svgs[2 * i], svgs[2 * i + 1], (a, b))

    def test_a_process_is_a_pure_function_of_its_time(self):
        for p in ({"kind": "factoryFloor"}, {"kind": "riverTown"}, {"kind": "farm", "weather": "pests"}, {"kind": "village", "weather": "rain"},
                  {"kind": "godown", "flow": "in"}, {"kind": "city", "vehicles": 4}, {"kind": "foodStreet", "light": "night"}):
            with self.subTest(p=p):
                a, b, c = draw_all([[p, 1.3, 1.3], [p, 1.3, 1.3], [p, 2.9, 2.9]])
                self.assertEqual(a, b)
                self.assertNotEqual(a, c)


@unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
class Spots(unittest.TestCase):
    def test_python_and_the_drawing_name_the_same_spots(self):
        worlds = [{"kind": k} for k in NEW] + [{"kind": k, "count": 12} for k in NEW] + [
            {"kind": "mandi", "signs": "रामू;श्याम"}, {"kind": "foodStreet", "signs": "a;b;c;d;e;f;g"}, {"kind": "factoryFloor", "signs": "x;y;z"},
            {"kind": "farm", "signs": "घाटी;पहाड़ी;field"}, {"kind": "mohalla", "signs": "शर्मा;खान;सिंह"}, {"kind": "canteen", "signs": "समोसा;चाय"},
            {"kind": "busStand", "signs": "लाल;नीली;हरी"}, {"kind": "petrolPump", "signs": "A"}, {"kind": "dealingRoom", "signs": "a"},
            {"kind": "hospital", "signs": "डॉ. A;डॉ. B"}, {"kind": "foodShop", "signs": "रामू"}, {"kind": "twoSector", "signs": "खेत;कपड़ा;x"},
            {"kind": "twoSector", "signs": "shed;खेत"}, {"kind": "venue", "signs": "बच्चे;बड़े"}, {"kind": "home", "count": 3}]
        engine = ENGINE / "worlds.mjs"
        out = node(f"import {{worldSpots}} from '{engine.as_posix()}';const ws = {json.dumps(worlds, ensure_ascii=False)};"
                   "console.log(JSON.stringify(ws.map((w) => worldSpots(w))));")
        for w, spots in zip(worlds, out):
            with self.subTest(world=w):
                self.assertEqual(list(spots), gl.world_spot_names(w))
                for box in spots.values():
                    self.assertTrue(0 <= box["x"] <= 1 and 0 <= box["y"] <= 1 and box["w"] > 0 and box["h"] > 0, box)
                    self.assertLessEqual(box["x"] + box["w"], 1.0001)
                    self.assertLessEqual(box["y"] + box["h"], 1.0001)

    def test_a_game_level_can_happen_in_a_new_place(self):
        level = {"world": {"kind": "labourChowk", "prices": "₹500"}, "places": [{"id": "a", "label": "x", "spot": "truck"}]}
        self.assertEqual(gl._world_problems(level, "L1"), [])
        level["places"][0]["spot"] = "vault"
        self.assertTrue(any("spot 'vault' is not in the labourChowk world" in q for q in gl._world_problems(level, "L1")))
        self.assertIn("labourChowk: crowd, truck", gl.world_spots_text())


if __name__ == "__main__":
    unittest.main()
