"""Phase 1, part B1: the saancha slot — the manifest, the parameter checks, the search and the still sheets.

Offline except the still-sheet render, which needs node like the rest of the toolbox lane.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import formats, saanche  # noqa: E402
from bie.brain.gold.money_v2 import gold_spec  # noqa: E402

ENGINE = ROOT / "bie" / "brain" / "video" / "engine"


def drawn_things(value):
    """Every {draw, p} anywhere in a spec: elements, held items, bubble contents, group members."""
    if isinstance(value, dict):
        if value.get("draw") and not str(value["draw"]).startswith("__"):   # __person__ is the engine's rig, not a saancha
            yield value["draw"], value.get("p") or {}
        for inner in value.values():
            yield from drawn_things(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from drawn_things(inner)


class Manifest(unittest.TestCase):
    def test_the_manifest_is_valid_and_every_entry_is_a_drawing_the_engine_has(self):
        data = saanche.manifest()
        self.assertEqual(formats.problems("saancha_manifest", data), [])
        self.assertIn("BIE original", data["licence"])
        draw = "".join(f.read_text(encoding="utf-8") for f in [ENGINE / "draw.mjs", *sorted((ENGINE / "families").glob("*.mjs"))])
        for name in saanche.names():
            self.assertIn(f"{name}:", draw, name)              # registered in DRAWS or a family's (the node test proves it draws)
            entry = saanche.get(name)
            self.assertTrue(any(not t.isascii() for t in entry["tags"]), f"{name}: no Hindi word")
            self.assertTrue(any(t.isascii() for t in entry["tags"]), f"{name}: no English word")
            self.assertEqual(saanche.problems(name, {k: v["default"] for k, v in entry["params"].items()
                                                     if v["type"] != "color" or v["default"]}), [], name)

    @unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
    def test_the_manifest_and_the_engine_registry_name_the_same_saanche(self):
        out = subprocess.run(["node", "--input-type=module", "-e",
                              f"import {{DRAWS}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                              "console.log(JSON.stringify(Object.keys(DRAWS)))"],
                             capture_output=True, text=True, check=True)
        self.assertEqual(sorted(json.loads(out.stdout)), saanche.names())

    def test_a_wrong_parameter_is_named_exactly(self):
        self.assertEqual(saanche.problems("sack", {"w": 220, "label": "गेहूँ", "content": "salt"}), [])
        self.assertIn("no saancha 'sock'", saanche.problems("sock", {})[0])
        self.assertIn("no parameter 'width'", saanche.problems("sack", {"width": 220})[0])
        self.assertIn("outside", saanche.problems("sack", {"w": 5000})[0])
        self.assertIn("not one of", saanche.problems("phone", {"screen": "video"})[0])
        self.assertIn("whole number", saanche.problems("coinStack", {"n": 2.5})[0])
        self.assertIn("true or false", saanche.problems("heap", {"wet": "yes"})[0])
        self.assertIn("#rrggbb", saanche.problems("clothRoll", {"color": "red"})[0])
        self.assertIn("a number is needed", saanche.problems("coin", {"r": "big"})[0])

    def test_every_drawing_of_the_gold_plan_passes_the_manifest(self):
        spec = gold_spec(width=1920, height=1080)
        seen = set()
        for name, p in drawn_things(spec):
            seen.add(name)
            self.assertEqual(saanche.problems(name, p), [], f"{name}: {p}")
        self.assertGreaterEqual(len(seen), 20)                  # the gold plan exercises most of the library


class Search(unittest.TestCase):
    def test_hindi_and_english_words_find_the_drawing_first_and_icons_after(self):
        rows = saanche.search("सिक्का")
        self.assertEqual(rows[0]["kind"], "draw")
        self.assertEqual(rows[0]["name"], "coin")
        rows = saanche.search("sack grain")
        self.assertIn("sack", [r["name"] for r in rows if r["kind"] == "draw"])
        rows = saanche.search("बैंक")
        self.assertEqual(rows[0]["name"], "bank")
        self.assertTrue(any(r["kind"] == "asset" for r in saanche.search("book", icons_limit=4)))
        self.assertEqual([r for r in saanche.search("qqqqzz", icons_limit=0)], [])


class StillSheetSpec(unittest.TestCase):
    def test_every_saancha_is_on_exactly_one_sheet_with_its_name(self):
        import saanche_stills as tool
        everything = saanche.names()
        pages = [everything[i:i + 12] for i in range(0, len(everything), 12)]
        spec = tool.sheet_spec(pages)
        from bie.brain import formats
        self.assertEqual(formats.problems("show_spec", spec), [])
        drawn = [e["draw"] for s in spec["scenes"] for e in s["els"] if e.get("draw")]
        named = [e["text"] for s in spec["scenes"] for e in s["els"] if e.get("text")]
        self.assertEqual(sorted(drawn), everything)
        self.assertEqual(sorted(named), everything)
        self.assertTrue(all(e.get("size", 36) >= 36 for s in spec["scenes"] for e in s["els"] if e.get("text")))


if __name__ == "__main__":
    unittest.main()
