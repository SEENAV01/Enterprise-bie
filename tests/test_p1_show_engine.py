"""Phase 1, part A (agreement of 3 November 2026): the showing engine inside BIE and the Money v2 gold example.

Offline (the core lane runs without node's web packages): the engine is the v2 demo's renderer rebuilt inside bie/
(dist/*.js of the demo were never committed), on the same window API as the preview harness, so stills, MP4, the
chunked CI render and the text audit work unchanged. The render smoke tests are tests/test_p1_show_render.py, run
in the toolbox demos job.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import formats  # noqa: E402
from bie.brain.gold.money_v2 import ASSETS_USED, Timeline, build_script, gold_spec  # noqa: E402
from bie.brain.video import render, text_audit as ta  # noqa: E402

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="#c98850"/></svg>'


class GoldScript(unittest.TestCase):
    def test_the_narration_is_whole_and_every_english_term_speaks_in_devanagari(self):
        script = build_script()
        lines = [l for sc in script for l in sc["lines"]]
        self.assertEqual(len(lines), 67)
        covered = {i for l in lines for i in l["covers"]}
        self.assertEqual(len(covered), 32)                      # distinct book items named by the narration
        self.assertTrue(all(l["say_parts"] for l in lines))     # to_say() raises on untranslated English

    def test_the_timeline_places_words_in_order_and_names_a_missing_word(self):
        T = Timeline(build_script())
        self.assertLess(T.cue("l03", "दो किलो"), T.cue("l03", "एक मीटर"))
        self.assertLess(T.L("l02")["t1"], T.L("l03")["t0"])
        self.assertGreater(T.cue("l06", "सेवा", nth=2), T.cue("l06", "सेवा"))
        with self.assertRaises(KeyError):
            T.cue("l03", "no-such-word")
        self.assertEqual(T.estimated, len(T.parts))             # no voice durations: everything estimated
        real = Timeline(build_script(), {f"{l['id']}_{i}": 2.0 for sc in build_script() for l in sc["lines"] for i in range(len(l["say_parts"]))})
        self.assertEqual(real.estimated, 0)

    def test_the_gold_spec_is_deterministic_and_a_valid_show_spec(self):
        a, b = gold_spec(width=1920, height=1080), gold_spec(width=1920, height=1080)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertEqual(formats.problems("show_spec", a), [])
        self.assertEqual(len(a["scenes"]), 20)
        self.assertEqual(sum(len(s["els"]) for s in a["scenes"]), 477)
        self.assertGreater(a["duration"], 500)
        for s0, s1 in zip(a["scenes"], a["scenes"][1:]):        # scenes cover the video without gaps
            self.assertEqual(s0["t1"], s1["t0"])
        self.assertEqual(a["scenes"][0]["t0"], 0.0)
        kinds = {e.get("kind") or ("item" if (e.get("draw") or e.get("asset") or e.get("group")) else "text")
                 for s in a["scenes"] for e in s["els"]}
        self.assertLessEqual({"person", "item", "text", "mark", "arrow", "bubble", "rect", "glow", "map"}, kinds)


class EngineGlue(unittest.TestCase):
    def test_a_show_spec_takes_the_engine_page_and_the_old_spec_does_not(self):
        self.assertTrue(render.needs_engine({"schema": "bie.show-spec/1"}))
        self.assertTrue(render.needs_engine({"subs": [], "scenes": [{"els": []}]}))
        self.assertFalse(render.needs_engine({"schema": "bie.video-spec/1", "scenes": [{"layers": []}]}))
        self.assertEqual(render.total_frames({"duration": 10.5, "fps": 30}), 315)
        self.assertEqual(render.total_frames({"scenes": [{"duration": 60}, {"duration": 30}]}), 90)

    def test_the_audit_knows_a_show_specs_subtitles(self):
        spec = {"subs": [{"t0": 0, "t1": 1, "text": "  नीचे   की पट्टी  "}], "scenes": []}
        self.assertIn("नीचे की पट्टी", ta.caption_texts(spec))

    def test_the_engine_sources_carry_the_demo_vocabulary(self):
        draw = (ROOT / "bie" / "brain" / "video" / "engine" / "draw.mjs").read_text(encoding="utf-8")
        for name in ("sack", "clothRoll", "saltPacket", "note", "coin", "goldBar", "oilTin", "matka", "charpai", "saw",
                     "calendar", "bugs", "heap", "teaBrick", "tobacco", "cowries", "cheque", "accountCard", "bank",
                     "qrStand", "phone", "noteBundle", "coinStack", "sweat", "bowl", "veg", "wheat", "clothStack"):
            self.assertIn(f"{name}:", draw, name)
        people = (ROOT / "bie" / "brain" / "video" / "engine" / "people.mjs").read_text(encoding="utf-8")
        for pose in ("stand", "give", "receive", "hold", "think", "point", "wave", "carry", "write", "walk", "refuse", "shrug", "holdBoth"):
            self.assertIn(pose + ":", people, pose)
        for look in ("ramu", "mohan", "sita", "kamla", "raju", "villager", "oil", "salt", "herder", "shop"):
            self.assertIn(look + ":", people, look)
        land = json.loads((ROOT / "bie" / "brain" / "video" / "engine" / "map_land.json").read_text(encoding="utf-8"))
        self.assertEqual(set(land["pins"]), {"rome", "africa", "india", "china", "central_asia", "tibet", "colonial_america"})
        self.assertIn("public domain", land["note"])

    def test_every_asset_of_the_gold_plan_is_a_fluent_emoji_in_the_index(self):
        from gold_money_v2 import FLUENT
        from bie.toolbox import icons
        rows = icons.by_id()
        for name, icon_id in FLUENT.items():
            self.assertIn(icon_id, rows, name)
        self.assertEqual(set(FLUENT), set(ASSETS_USED))


class GoldTool(unittest.TestCase):
    def test_the_tool_writes_script_spec_and_credits_through_the_library(self):
        import gold_money_v2 as tool
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(tool, "resolve_assets",
                                                                        lambda out, opener=None: {n: f"assets/{n}.png" for n in ASSETS_USED}):
            out = Path(folder)
            self.assertEqual(tool.main(["--out", str(out), "--width", "1920", "--height", "1080"]), 0)
            spec = json.loads((out / "video_specs" / "v2_gold.json").read_text(encoding="utf-8"))
            self.assertEqual(formats.problems("show_spec", spec), [])
            self.assertIn("Claude's demo, not BIE output", (out / "GOLD.md").read_text(encoding="utf-8"))
            script = json.loads((out / "script.json").read_text(encoding="utf-8"))
            self.assertEqual(sum(len(s["lines"]) for s in script), 67)


if __name__ == "__main__":
    unittest.main()
