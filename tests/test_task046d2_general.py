"""Task 046 Part D2 addendum (Navin, 2 November 2026): examples are illustrations, not a list.

"maine salt aur kapde ka example diya ... aise to kal kisi aur cheej ka jikar aayega to salt aur kapda hi dikhaoge, jabki mera
kehna hai jis cheej ka jikar hai wohi cheej dikhe."

1. No chapter noun is a fixed value anywhere in the director, world, canvas or template code (string constants and identifiers
   are read; comments and docstrings, which record history, are not).
2. Every recipe, a composed process and a world run with different objects (a bicycle, a test tube, a book) draw only the
   objects they were given: no other picture, and no drawing of any object of the block's own.
"""
from __future__ import annotations

import ast
import copy
import io
import re
import tokenize
import unittest
from pathlib import Path

from bie.brain import canvas
from bie.brain.video import saanche, world

ROOT = Path(__file__).resolve().parents[1]
CODE = ["bie/brain/canvas_director.py", "bie/brain/canvas.py", "bie/brain/visual_thinking.py", "bie/brain/video/world.py",
        "bie/brain/video/saanche.py"]
BLOCKS = ["bie/brain/video/blocks/toolbox/saanche.tsx", "bie/brain/video/blocks/toolbox/world.tsx",
          "bie/brain/video/blocks/toolbox/canvas.tsx"]
# The Money chapter's own things (the examples Navin gave and the objects D2 first drew by hand). None may be a fixed value.
CHAPTER_NOUNS = ["नमक", "salt", "कपड़", "cloth", "गेहूँ", "गेहूं", "wheat", "अनाज", "grain", "मवेशी", "cattle", "कौड़ी", "cowrie",
                 "चीनी", "sugar", "cheque", "चेक", "upi", "qr", "passbook", "पासबुक", "सिक्क", "coin", "banknote", "नोट", "rupee",
                 "रुपय", "रुपए", "₹", "phone", "फ़ोन", "pos machine", "किराना", "बैंक", "barter", "gold", "सोना"]
# a Latin word whole (so "sqrt" is not "qr", "CoinRain" is read as a name), any Devanagari stem or sign as it stands
WORD = re.compile("|".join(sorted(((rf"(?<![A-Za-z]){re.escape(n)}(?![A-Za-z])" if n.isascii() else re.escape(n)) for n in CHAPTER_NOUNS),
                                  key=len, reverse=True)), re.IGNORECASE)
# kind and key names of the block API (renamed only with the plan schema, Task 046 Part D CONTRACTS): read as names, not as
# things to draw
API_NAMES = {"coin_rain"}


def python_values(path: Path) -> list:
    """The string constants of a Python file that are not docstrings, with their line numbers, and its identifiers."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                docs.add(id(first.value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            out.append((node.lineno, node.value))
        elif isinstance(node, ast.Name):
            out.append((node.lineno, node.id))
        elif isinstance(node, ast.Attribute):
            out.append((node.lineno, node.attr))
    return out


def tsx_values(path: Path) -> list:
    """The code of a TSX file without its comments, line by line."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"\{/\*.*?\*/\}", "", text)
    return list(enumerate(text.split("\n"), start=1))


def hits(values: list) -> list:
    out = []
    for line, value in values:
        for m in WORD.finditer(str(value)):
            if any(api in str(value) for api in API_NAMES) and m.group(0).lower() == "coin":
                continue
            out.append((line, m.group(0), str(value)[:80]))
    return out


class NoChapterNouns(unittest.TestCase):
    def test_no_chapter_noun_is_a_fixed_value_in_the_director_world_canvas_or_template_code(self):
        found = {}
        for rel in CODE:
            h = hits(python_values(ROOT / rel))
            if h:
                found[rel] = h
        for rel in BLOCKS:
            h = hits(tsx_values(ROOT / rel))
            if h:
                found[rel] = h
        self.assertEqual(found, {}, "\n".join(f"{f}:{l}: {w!r} in {v!r}" for f, hs in found.items() for l, w, v in hs))

    def test_the_block_draws_no_object_of_its_own(self):
        tsx = (ROOT / "bie/brain/video/blocks/toolbox/saanche.tsx").read_text(encoding="utf-8")
        for name in ("Note", "Coin", "QRStand", "Phone", "PhoneCard", "POS", "Card", "Cheque", "Passbook"):
            self.assertNotRegex(tsx, rf"const {name}\b", name)
        self.assertEqual(re.findall(r"<image\b[^>]*href=\{([^}]*)\}", tsx), ["assetUrl(obj.src)"])   # pictures only from the plan


B, T, K = "tw:1f6b2", "tw:1f9ea", "tw:1f4d6"
GIVEN = {B, T, K}
BEATS = [{"beat_id": f"b{i}", "say": s} for i, s in enumerate([
    "रीना साइकिल देती है और अमन लेता है।",
    "अमन 12 रुपये देता है, किताब लेता है और 2 रुपये वापस मिलते हैं।",
    "रीना की test tube और अमन की किताब की अदला बदली होती है, दोनों पूछते हैं फिर बदलते हैं।",
    "अमन स्कैन करता है, 40 रुपये paid, received होता है।",
    "test tube लिए अमन मना करता है।",
    "रीना किताब स्वीकार करती है।",
    "तीन किताबें एक एक करके आती हैं।",
    "test tube किताब में बदल जाती है और साइकिल आगे जाती है।",
    "अमन कार्ड से 15 रुपये देता है और मशीन approved दिखाती है।",
    "रीना 50 का लिखती है, वह आगे जाता है और खाते बदलते हैं।",
    "एक एक करके 5 के टुकड़े आते हैं, 20 तक ही।",
], start=1)]
TWO = lambda r1, r2: [{"role": r1, "who": "main", "label": "रीना"}, {"role": r2, "who": "other", "label": "अमन"}]
RECIPES = {
    "hand_over": (TWO("giver", "taker"), [{"name": "thing", "icon": B}], [("give", "b1", "देती"), ("take", "b1", "लेता")], []),
    "pay_change": (TWO("buyer", "seller"), [{"name": "goods", "icon": K}, {"name": "money", "icon": T}],
                   [("pay", "b2", "देता"), ("goods", "b2", "किताब"), ("change", "b2", "वापस")],
                   [{"name": "paid", "text": "12 रुपये"}, {"name": "change", "text": "2 रुपये"}]),
    "barter_swap": (TWO("a", "b"), [{"name": "a_thing", "icon": T}, {"name": "b_thing", "icon": K}],
                    [("offer", "b3", "अदला"), ("ask", "b3", "पूछते"), ("swap", "b3", "बदलते")], []),
    "upi": (TWO("buyer", "seller"), [{"name": "device", "icon": B}, {"name": "sign", "icon": K}],
            [("scan", "b4", "स्कैन"), ("paid", "b4", "paid,"), ("received", "b4", "received")], [{"name": "amount", "text": "40 रुपये"}]),
    "card_tap": (TWO("buyer", "seller"), [{"name": "card", "icon": K}, {"name": "machine", "icon": T}],
                 [("tap", "b9", "कार्ड"), ("approved", "b9", "approved")], [{"name": "amount", "text": "15 रुपये"}]),
    "cheque": (TWO("payer", "payee"), [{"name": "cheque", "icon": K}, {"name": "place", "icon": B}],
               [("write", "b10", "लिखती"), ("hand", "b10", "आगे"), ("balances", "b10", "बदलते")], [{"name": "amount", "text": "50"}]),
    "coin_count": ([], [{"name": "coin", "icon": T}], [("count", "b11", "एक"), ("limit", "b11", "तक")],
                   [{"name": "each", "text": "5"}, {"name": "limit", "text": "20"}]),
    "refuse": ([{"role": "who", "who": "other", "label": "अमन"}], [{"name": "thing", "icon": T}], [("show", "b5", "test"), ("refuse", "b5", "मना")], []),
    "accept": ([{"role": "who", "who": "main", "label": "रीना"}], [{"name": "thing", "icon": K}], [("show", "b6", "किताब"), ("accept", "b6", "स्वीकार")], []),
    "count_stack": ([], [{"name": "thing", "icon": K}], [("count", "b7", "एक")], [{"name": "n", "text": "3"}]),
}
COMPOSED = {"template": "compose", "actors": [{"role": "left", "who": "main", "label": "रीना"}],
            "objects": [{"name": "tube", "icon": T}, {"name": "book", "icon": K}, {"name": "cycle", "icon": B}], "amounts": [], "steps": [],
            "parts": [{"part": "hold", "cue": ["b8", "test"], "actor": "left", "object": "tube"},
                      {"part": "transform", "cue": ["b8", "बदल"], "object": "tube", "into": "book"},
                      {"part": "appear", "cue": ["b8", "साइकिल"], "object": "cycle", "spot": "right"},
                      {"part": "move", "cue": ["b8", "आगे"], "object": "cycle", "to": "far"}]}


def node(aid, template, actors, objects, steps, amounts, **extra):
    n = {"id": aid, "kind": "action", "cell": [0, 0, 12, 6], "template": template, "actors": copy.deepcopy(actors),
         "objects": copy.deepcopy(objects), "amounts": copy.deepcopy(amounts), "steps": [{"name": s, "cue": [b, w]} for s, b, w in steps]}
    n.update(extra)
    return n


def drawn(element: dict) -> set:
    """Every picture a compiled action would draw: its objects' sources (a chip has none)."""
    return {o["src"] for o in element["objects"].values() if o.get("src")}


class OnlyTheGivenObjects(unittest.TestCase):
    def compile(self, n):
        scene, _ = canvas.compile_plan({"id": "gen_s1", "grid": [12, 8], "touches": True, "beats": copy.deepcopy(BEATS), "nodes": [n]})
        return scene["layers"][0]["data"]["elements"][0]

    def test_every_recipe_draws_only_the_bicycle_the_test_tube_and_the_book_it_was_given(self):
        self.assertEqual(set(RECIPES), set(saanche.TEMPLATES))                 # every recipe of the rulebook is run here
        for name, (actors, objects, steps, amounts) in RECIPES.items():
            with self.subTest(name):
                el = self.compile(node(name, name, actors, objects, steps, amounts))
                given = {o["icon"] for o in objects}
                self.assertEqual(drawn(el), given)
                self.assertTrue(el["parts"])
                self.assertTrue(set(p["part"] for p in el["parts"]) <= set(saanche.PARTS))

    def test_without_its_optional_objects_a_recipe_draws_chips_with_text_or_skips_them(self):
        actors, objects, steps, amounts = RECIPES["pay_change"]
        el = self.compile(node("p", "pay_change", actors, [o for o in objects if o["name"] == "goods"], steps, amounts))
        self.assertEqual(drawn(el), {K})
        self.assertEqual(sorted(o["chip"] for o in el["objects"].values() if "chip" in o), ["12 रुपये", "2 रुपये"])
        actors, objects, steps, amounts = RECIPES["upi"]
        el = self.compile(node("u", "upi", actors, [], steps, amounts))
        self.assertEqual(drawn(el), set())
        self.assertEqual([p["part"] for p in el["parts"]], ["show_text", "show_text"])

    def test_a_composed_process_draws_only_its_own_objects_and_names_a_missing_part(self):
        el = self.compile(dict(copy.deepcopy(COMPOSED), id="c", kind="action", cell=[0, 0, 12, 6]))
        self.assertEqual(drawn(el), GIVEN)
        self.assertEqual([p["part"] for p in el["parts"]], ["hold", "transform", "appear", "move"])
        bad = dict(copy.deepcopy(COMPOSED), id="c")
        bad["parts"][1]["part"] = "melt"
        problems = saanche.problems_of(bad, {b["beat_id"]: b["say"] for b in BEATS})
        self.assertTrue(any("'melt' is not a motion part" in p and "missing-capability log" in p for p in problems), problems)

    def test_a_world_draws_only_the_given_goods_and_objects(self):
        plan = {"id": "gen_s1", "kit": "shop", "world_width": 5200, "beats": copy.deepcopy(BEATS[:2]), "elements": [
            {"id": "shop", "kind": "shop", "x": 2600, "sign": "", "goods": [{"icon": B, "label": ""}, {"icon": T, "label": ""}],
             "packets": [{"n": 2, "cue": ["b1", "रीना"]}]},
            dict(node("give", "hand_over", *RECIPES["hand_over"]), x=3300)],
            "camera": [{"cue": ["b1", ""], "x": 2900, "y": 540, "zoom": 1.0, "frames": 30}]}
        plan["elements"][1].pop("cell")
        self.assertEqual(set(world.icons_in(plan)), {B, T})
        scene, _ = world.compile_world(plan, icon_paths={B: "assets/b.svg", T: "assets/t.svg"})
        data = scene["layers"][0]["data"]
        pictures = {g.get("src") for e in data["elements"] for g in e.get("goods") or []}
        pictures |= {o.get("src") for e in data["elements"] if e["kind"] == "action" for o in e["objects"].values() if o.get("src")}
        self.assertEqual(pictures, {"assets/b.svg", "assets/t.svg"})
        tsx = (ROOT / "bie/brain/video/blocks/toolbox/world.tsx").read_text(encoding="utf-8")
        self.assertNotRegex(tsx, r'el\.sign \?\? "[^"]+"')                    # no default sign words on a place


if __name__ == "__main__":
    unittest.main()
