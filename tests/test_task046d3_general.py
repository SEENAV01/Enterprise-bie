"""Task 046 Part D3: the general fixes from Navin's verdict on the D2 addendum proof (3 November 2026).

"fix only these general issues (minimum on-screen text size readable on a phone, no world for a place that is not that world,
label overlap in every mode)". Offline: no AI call, no browser (the render-time text audit is tested on measured frames).
"""
from __future__ import annotations

import copy
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import canvas, canvas_director as cd  # noqa: E402
from bie.brain.assets import AssetLibrary  # noqa: E402
from bie.brain.video import text_audit as ta, world  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "task046c"
SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M0 0h10v10H0z"/></svg>'


class NoWorldForAnotherPlace(unittest.TestCase):
    """v6: the shop world hosted mints, a British Act and a Mumbai bank."""

    def test_place_words_are_whole_words_and_a_banknote_names_no_bank(self):
        self.assertEqual(world.places_named("RBI prints banknotes"), set())
        self.assertEqual(world.places_named("the bank gives a loan"), {"bank"})
        self.assertEqual(world.places_named("coins are made in the mint"), {"mint"})
        self.assertEqual(world.places_named("Coinage Act, 2011 sets the limit"), {"government"})
        self.assertEqual(world.places_named("दुकान पर ग्राहक आया"), {"shop"})

    def test_the_people_of_a_place_open_its_scene(self):
        self.assertTrue(world.place_words("shop")("दुकानदार ने कहा"))
        self.assertTrue(world.place_words("bank")("the teller counts the notes"))
        self.assertFalse(world.place_words("shop")("he pays ₹50"))

    def test_a_beat_at_another_place_closes_the_scene_and_only_the_place_reopens_it(self):
        beats = [{"beat_id": "b1", "say": "Ravi goes to the shop"}, {"beat_id": "b2", "say": "he pays ₹50"},
                 {"beat_id": "b3", "say": "coins are made in a mint"}, {"beat_id": "b4", "say": "the price stays"},
                 {"beat_id": "b5", "say": "the shopkeeper smiles"}]
        self.assertEqual(cd.at_place(beats, "shop", []), [True, True, False, False, True])
        # the story's first beat opens the scene even when it names no place
        self.assertEqual(cd.at_place([{"beat_id": "s1", "say": "₹50 दिए"}, {"beat_id": "s2", "say": "फिर ₹10 लौटे"}], "shop", ["s1"]),
                         [True, True])

    def test_a_world_part_splits_into_world_runs_and_a_canvas_for_the_other_place(self):
        beats = [{"beat_id": "b1", "say": "Ravi goes to the shop"}, {"beat_id": "b2", "say": "he pays ₹50"},
                 {"beat_id": "b3", "say": "coins are made in a mint"}, {"beat_id": "b4", "say": "the price stays"},
                 {"beat_id": "b5", "say": "the shopkeeper smiles"}]
        stub = {"id": "v9_s1", "mode": {"mode": "C", "kit": "shop", "place": "shop"}, "beats": beats, "story_beats": ["b2"]}
        pieces = cd.world_split(stub, {})
        self.assertEqual([(p["id"], p["mode"]["mode"], [b["beat_id"] for b in p["beats"]]) for p in pieces],
                         [("v9_s11", "C", ["b1", "b2"]), ("v9_s12", "B", ["b3", "b4"]), ("v9_s13", "C", ["b5"])])
        self.assertIn("mint", pieces[1]["mode"]["note"])
        self.assertEqual(pieces[0]["story_beats"], ["b2"])
        self.assertEqual(pieces[1]["story_beats"], [])

    def test_a_story_run_at_another_place_with_a_kit_becomes_that_kit(self):
        beats = [{"beat_id": "b1", "say": "Ravi goes to the shop"}, {"beat_id": "b2", "say": "then he goes to the bank"},
                 {"beat_id": "b3", "say": "the bank keeps ₹500 in his account"}]
        stub = {"id": "v9_s2", "mode": {"mode": "C", "kit": "shop", "place": "shop"}, "beats": beats, "story_beats": ["b3"]}
        pieces = cd.world_split(stub, {})
        self.assertEqual([(p["mode"]["mode"], p["mode"]["kit"]) for p in pieces], [("C", "shop"), ("C", "bank")])

    def test_a_part_at_its_place_and_a_canvas_part_are_not_split(self):
        beats = [{"beat_id": "b1", "say": "दुकान पर ग्राहक आया"}, {"beat_id": "b2", "say": "उसने ₹20 दिए"}]
        stub = {"id": "v9_s3", "mode": {"mode": "C", "kit": "shop", "place": "shop"}, "beats": beats, "story_beats": ["b2"]}
        self.assertEqual(cd.world_split(stub, {}), [stub])
        canvas_stub = dict(stub, mode={"mode": "B", "kit": ""})
        self.assertEqual(cd.world_split(canvas_stub, {}), [canvas_stub])


class ReadableText(unittest.TestCase):
    """CV-17: no text under 36 px on the 1080p frame (a phone held sideways)."""

    def test_the_profile_carries_the_floor(self):
        self.assertEqual((canvas.MIN_FONT, canvas.MIN_ICON, canvas.CAPTION_CHARS), (36, 64, 150))
        profile = json.loads((ROOT / "bie" / "brain" / "rulebook" / "canvas_profile.json").read_text(encoding="utf-8"))
        self.assertIn("CV-17", json.dumps(profile, ensure_ascii=False))

    def test_a_long_caption_is_cut_into_pieces_of_two_lines_never_inside_a_word(self):
        text = "पहले लोग चीज़ों से चीज़ें बदलते थे। फिर सिक्के आए, जिनका वज़न और धातु तय थी। " * 4
        pieces = canvas.caption_pieces(text)
        self.assertGreater(len(pieces), 1)
        self.assertTrue(all(len(p) <= canvas.CAPTION_CHARS for p in pieces))
        self.assertEqual(" ".join(pieces).split(), text.split())
        self.assertEqual(canvas.caption_pieces("छोटा वाक्य।"), ["छोटा वाक्य।"])
        self.assertEqual(canvas.caption_pieces(""), [])

    def test_a_label_too_wide_for_its_cell_or_an_icon_too_small_is_refused(self):
        plan = json.loads((FIXTURES / "demand_pull_touches.plan.json").read_text(encoding="utf-8"))
        shop = next(n for n in plan["nodes"] if n["id"] == "shop")
        tight = copy.deepcopy(plan)
        next(n for n in tight["nodes"] if n["id"] == "shop")["cell"] = [shop["cell"][0], shop["cell"][1], shop["cell"][2], 1]
        with self.assertRaises(canvas.PlanError) as err:
            canvas.compile_plan(tight)
        self.assertIn("CV-17", str(err.exception))
        wide = copy.deepcopy(plan)
        next(n for n in wide["nodes"] if n["id"] == "shop")["label"] = "SUPPLY · दुकान · wholesale and retail trade together"
        with self.assertRaises(canvas.PlanError):
            canvas.compile_plan(wide)
        scene, _ = canvas.compile_plan(copy.deepcopy(plan))
        texts = [e for layer in scene["layers"] for e in (layer.get("data") or {}).get("elements", []) if e.get("kind") == "text"]
        self.assertTrue(texts and all(e["size"] >= canvas.MIN_FONT for e in texts))

    def test_a_long_book_table_shows_a_page_at_a_time_at_the_readable_size(self):
        rows = [{"cells": [f"Year {i}", f"₹{i}00"], "cue": ["b1", ""]} for i in range(1, 13)]
        nodes = [{"id": "tab", "kind": "picture", "cell": [0, 0, 12, 4], "cue": ["b1", ""],
                  "picture": {"type": "table", "columns": ["Year", "Price"], "rows": rows}}]
        out = canvas.expand_pictures(nodes, [12, 8])
        pages = [n for n in out if n["kind"] == "table"]
        self.assertGreater(len(pages), 1)
        self.assertEqual([p["id"] for p in pages], [f"tab_t{k}" for k in range(1, len(pages) + 1)])
        self.assertTrue(all(p["size"] >= canvas.MIN_FONT for p in pages))
        self.assertEqual(sum(len(p["rows"]) for p in pages), 12)

    def test_a_two_row_timeline_is_refused_with_the_reason(self):
        events = [{"when": "1500", "name": "Barter"}, {"when": "1600", "name": "Coins"}, {"when": "1900", "name": "Notes"}]
        nodes = [{"id": "hist", "kind": "picture", "cell": [0, 0, 12, 2], "cue": ["b1", ""], "picture": {"type": "timeline", "events": events}}]
        with self.assertRaises(canvas.PlanError) as err:
            canvas.expand_pictures(nodes, [12, 8])
        self.assertIn("3 rows", str(err.exception))
        nodes[0]["cell"] = [0, 0, 12, 3]
        self.assertEqual(len([n for n in canvas.expand_pictures(nodes, [12, 8]) if n["kind"] == "icon"]), 3)


class Credits(unittest.TestCase):
    def test_a_video_credits_what_it_shows_not_the_whole_library(self):
        lib = AssetLibrary(Path(tempfile.mkdtemp()) / "assets")
        a = lib.add_bytes(SVG.encode(), mime="image/svg+xml", source="twemoji", title="coin", page_url="https://example.org/a",
                          licence="CC BY 4.0", licence_url="https://creativecommons.org/licenses/by/4.0/", author="A", credit="A, CC BY 4.0")
        b = lib.add_bytes(SVG.replace("10v10", "10v9").encode(), mime="image/svg+xml", source="twemoji", title="bank",
                          page_url="https://example.org/b", licence="CC BY 4.0", licence_url="https://creativecommons.org/licenses/by/4.0/",
                          author="B", credit="B, CC BY 4.0")
        scenes = [{"id": "s1", "layers": [{"data": {"elements": [{"kind": "icon", "src": "assets/" + a.path}]}}]}]
        self.assertEqual(lib.used_in(scenes), [a.asset_id])
        self.assertEqual(lib.used_in({"src": "/assets/" + b.path}), [b.asset_id])
        self.assertEqual(lib.used_in([]), [])

    def test_the_credit_card_pages_seven_readable_lines_at_a_time(self):
        lines = [f"Icon {i} by Someone, CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), https://example.org/{i}" for i in range(10)]
        scene = canvas.credits_scene(lines, 5.0, scene_id="v9_credits")
        self.assertEqual(scene["duration"], 2 * 150)
        els = scene["layers"][0]["data"]["elements"]
        body = [e for e in els if e["id"] != "title"]
        self.assertEqual(len(body), 10)
        self.assertTrue(all(e["size"] >= canvas.MIN_FONT for e in els))
        self.assertTrue(all(e.get("until") == 150 for e in body if e["id"].startswith("c0_")))
        self.assertTrue(all(e["at"] >= 150 and "until" not in e for e in body if e["id"].startswith("c1_")))
        self.assertTrue(all(e["y"] + e["h"] <= 1.0 for e in els))


def frame(n, *texts):
    return {"frame": n, "texts": [dict(t) for t in texts]}


class TextAudit(unittest.TestCase):
    """The render-time check: sizes after every camera and scale, and texts that cover each other."""

    def test_a_text_is_small_only_when_its_settled_size_stays_under_the_floor(self):
        pop = [frame(0, {"t": "price", "px": 12, "box": [0, 0, 50, 12]}), frame(30, {"t": "price", "px": 40, "box": [0, 0, 160, 40]})]
        self.assertEqual(ta.summarize(pop, every=30)["small_count"], 0)
        tiny = [frame(f, {"t": "tiny label", "px": 22, "box": [0, 0, 90, 22]}) for f in (0, 30, 60)]
        rec = ta.summarize(tiny, every=30)
        self.assertEqual((rec["small_count"], rec["lasting_small_count"], rec["min_px"]), (1, 1, 22))
        self.assertEqual(rec["small"][0]["samples"], 3)
        self.assertEqual(ta.summarize([frame(0, {"t": "₹", "px": 20, "box": [0, 0, 20, 20]})], every=30)["small_count"], 0)

    def test_texts_that_cover_each_other_are_counted_and_a_halo_is_not(self):
        a = {"t": "₹1,500", "px": 40, "box": [100, 100, 120, 40]}
        b = {"t": "₹1,000", "px": 40, "box": [110, 105, 120, 40]}
        halo = dict(a)
        rec = ta.summarize([frame(0, a, b, halo), frame(30, a, b)], every=30)
        self.assertEqual((rec["overlap_count"], rec["lasting_overlap_count"]), (1, 1))
        self.assertEqual(rec["overlaps"][0]["longest_run"], 2)
        apart = {"t": "far", "px": 40, "box": [600, 600, 80, 40]}
        self.assertEqual(ta.summarize([frame(0, a, apart)], every=30)["overlap_count"], 0)

    def test_the_caption_strip_is_counted_apart(self):
        spec = {"scenes": [{"captions": [{"at": 0, "until": 30, "text": "नीचे   की   पट्टी"}]}]}
        cap = {"t": "नीचे की पट्टी", "px": 36, "box": [100, 1000, 400, 50]}
        label = {"t": "label", "px": 36, "box": [120, 1005, 100, 40]}
        rec = ta.summarize([frame(0, cap, label), frame(30, cap, label)], every=30, captions=ta.caption_texts(spec))
        self.assertEqual((rec["overlap_count"], rec["caption_overlap_count"]), (0, 1))

    def test_the_tool_reads_measurements_written_before(self):
        tmp = Path(tempfile.mkdtemp())
        spec = {"fps": 30, "scenes": [{"captions": []}]}
        (tmp / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        (tmp / "f.jsonl").write_text("\n".join(json.dumps(f) for f in [frame(0, {"t": "x y", "px": 20, "box": [0, 0, 40, 20]}),
                                                                     frame(30, {"t": "x y", "px": 20, "box": [0, 0, 40, 20]})]) + "\n")
        import text_audit as tool
        with mock.patch("sys.stdout", new=io.StringIO()):
            tool.main(["--spec", str(tmp / "spec.json"), "--frames", str(tmp / "f.jsonl"), "--out", str(tmp / "audit.json")])
        rec = json.loads((tmp / "audit.json").read_text(encoding="utf-8"))
        self.assertEqual((rec["schema"], rec["lasting_small_count"]), ("bie.text_audit/1", 1))


class Respec(unittest.TestCase):
    """tools/respec_video.py: a canvas run's plans compiled again with the current code, at ₹0."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        env = mock.patch.dict(os.environ, {"BIE_ASSET_CACHE": str(self.tmp / "cache"), "BIE_TWEMOJI_SVG": "", "BIE_FONTAWESOME_SVGS": ""})
        env.start()
        self.addCleanup(env.stop)

    @staticmethod
    def opener(request, timeout=None):
        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False
        return Response(SVG.encode("utf-8"))

    def test_the_plans_compile_again_and_a_missing_plan_is_listed(self):
        import respec_video
        run = self.tmp / "run"
        (run / "plans").mkdir(parents=True)
        plan = json.loads((FIXTURES / "demand_pull_touches.plan.json").read_text(encoding="utf-8"))
        (run / "plans" / "v9_s1.plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        (run / "canvas.json").write_text(json.dumps({"videos": [{"video_id": "v9", "parts": [
            {"id": "v9_s1", "mode": "B", "status": "passed"}, {"id": "v9_s2", "mode": "C", "status": "failed"}]}]}), encoding="utf-8")
        out = self.tmp / "out"
        result = respec_video.respec(run, "v9", out, opener=self.opener)
        self.assertEqual((result["status"], result["compiled"], result["refused"]), ("spec_written", 1, 0))
        self.assertEqual([p["status"] for p in result["parts"]], ["compiled", "no_plan"])
        spec = json.loads((out / "video_specs" / "v9.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["scenes"][-1]["id"], "v9_credits")
        credit_lines = [e for e in spec["scenes"][-1]["layers"][0]["data"]["elements"] if e["id"] != "title"]
        self.assertEqual(len(credit_lines), len(AssetLibrary(out / "assets").used_in(spec["scenes"][:-1])))

    def test_a_plan_the_current_code_refuses_is_named_with_its_reason(self):
        import respec_video
        run = self.tmp / "run"
        (run / "plans").mkdir(parents=True)
        plan = json.loads((FIXTURES / "demand_pull_touches.plan.json").read_text(encoding="utf-8"))
        next(n for n in plan["nodes"] if n["id"] == "shop")["cell"][3] = 1          # an icon with a label in one row: under CV-17
        (run / "plans" / "v9_s1.plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        (run / "canvas.json").write_text(json.dumps({"videos": [{"video_id": "v9", "parts": [{"id": "v9_s1", "mode": "B", "status": "passed"}]}]}),
                                         encoding="utf-8")
        result = respec_video.respec(run, "v9", self.tmp / "out", opener=self.opener)
        self.assertEqual((result["status"], result["refused"]), ("no_scene", 1))
        self.assertIn("CV-17", result["parts"][0]["problem"])


if __name__ == "__main__":
    unittest.main()
