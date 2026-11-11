"""Phase 1, part A: the showing engine draws — render smoke tests.

In tests/toolbox/ like the wrappers, so the canonical gate (which fails a file that runs no test) never sees it:
these need node, esbuild and Chromium, which the toolbox demos job has. Run there as the 'show' lane, and locally with
NODE_PATH pointing at the web packages.
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bie.brain.gold.money_v2 import ASSETS_USED, gold_spec  # noqa: E402
from bie.brain.video import render, text_audit as ta  # noqa: E402


@unittest.skipUnless(shutil.which("node"), "needs node (the toolbox demos job has it)")
class EngineRender(unittest.TestCase):
    """The engine draws: built once, frames rendered, the text audit runs on them."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        try:
            cls.dist = render.build_preview(cls.tmp / "dist", engine=True)
        except render.RenderError as exc:                        # the canonical gate has node but not the web packages
            raise unittest.SkipTest(f"engine build needs esbuild on NODE_PATH: {exc}")
        (cls.tmp / "assets").mkdir()
        for name in ASSETS_USED:
            (cls.tmp / "assets" / f"{name}.png").write_bytes(b"")          # never fetched: the spec uses drawn things only

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def small_spec(self):
        return {"schema": "bie.show-spec/1", "fps": 30, "width": 640, "height": 360, "duration": 4.0,
                "subs": [{"t0": 0.2, "t1": 3.6, "text": "रामू दो किलो गेहूँ देता है।"}],
                "scenes": [{"id": "s1", "t0": 0.0, "t1": 4.0, "bg": "village", "kicker": "Barter",
                            "cam": [{"t": 2.0, "d": 0.8, "x": 760, "y": 540, "z": 1.4}],
                            "els": [
                                {"id": "ramu", "kind": "person", "look": "ramu", "x": 700, "y": 885, "h": 440, "facing": 1,
                                 "pose": "stand", "expr": "smile", "t0": 0.0, "t1": None, "z": 10, "poses": [{"t": 1.0, "pose": "give"}],
                                 "exprs": [{"t": 2.0, "expr": "happy"}], "holds": [{"t": 0.5, "item": {"draw": "saltPacket", "p": {"w": 90}, "y": 60}}],
                                 "facings": [], "walks": [{"t": 2.4, "d": 1.0}], "shakes": [], "nods": [], "keys": [{"t": 2.4, "d": 1.0, "x": 1000}]},
                                {"draw": "sack", "p": {"w": 220, "label": "गेहूँ"}, "x": 1100, "y": 885, "s": 1, "z": 20, "t0": 0.0, "t1": None, "enter": "pop", "keys": []},
                                {"text": "Barter system", "size": 64, "style": "title", "x": 960, "y": 200, "t0": 0.4, "t1": None, "z": 40},
                                {"kind": "mark", "mark": "cross", "x": 1400, "y": 400, "w": 140, "t0": 1.0, "t1": None, "z": 45, "enter": "none"},
                                {"kind": "arrow", "x1": 500, "y1": 300, "x2": 900, "y2": 300, "x": 0, "y": 0, "t0": 1.2, "t1": None, "z": 30, "enter": "none", "bend": -0.2, "color": "#2fb463"},
                                {"kind": "bubble", "of": "ramu", "content": {"draw": "clothRoll", "p": {"w": 150}}, "w": 260, "kind2": "think", "t0": 0.8, "t1": None, "dx": 200, "dy": -560, "z": 48, "tail": -1, "x": 0, "y": 0},
                            ]}]}

    def test_the_engine_renders_frames_and_the_audit_reads_them(self):
        spec = self.small_spec()
        pngs = render.stills(spec, [15, 75, 105], dist=self.dist, assets=self.tmp / "assets")
        self.assertEqual(len(pngs), 3)
        self.assertTrue(all(p[:8] == b"\x89PNG\r\n\x1a\n" for p in pngs))
        self.assertGreater(len(pngs[1]), 12000)                      # a drawn frame, not an empty page
        frames = render.audit(spec, dist=self.dist, assets=self.tmp / "assets", every=30)
        rec = ta.summarize(frames, every=30, captions=ta.caption_texts(spec))
        self.assertGreaterEqual(rec["frames_sampled"], 4)
        self.assertGreater(rec["texts_seen"], 2)
        self.assertEqual(rec["caption_overlap_count"], 0)
        # the plan's own words carry the engine's bie-plan mark (the text-audit gate), a saancha's label does not
        marked = {t["t"] for f in frames for t in f["texts"] if t.get("plan")}
        self.assertIn("Barter system", marked)
        self.assertIn("Barter", marked)                              # the kicker
        self.assertNotIn("गेहूँ", marked)                             # the sack's label
        self.assertTrue(rec["plan_marked"])

    def test_the_gold_spec_first_frames_render(self):
        spec = gold_spec(width=1280, height=720, assets={n: f"assets/{n}.png" for n in ASSETS_USED})
        pngs = render.stills(spec, [60], dist=self.dist, assets=self.tmp / "assets")
        self.assertTrue(pngs[0][:8] == b"\x89PNG\r\n\x1a\n")

    def test_a_notes_picture_page_draws_through_the_same_engine(self):
        sys.path.insert(0, str(ROOT / "tests"))
        from test_p1_notes_pages import page
        from bie.brain import notes_pages
        spec = notes_pages.still_spec(page("picture"))
        png = render.stills(spec, [15], dist=self.dist)[0]
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertGreater(len(png), 20000)                      # a drawn page, not an empty frame

    def test_the_saancha_still_sheets_draw_every_entry(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import saanche_stills as tool
        from bie.brain import saanche
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            self.assertEqual(tool.main(["--out", str(out), "--dist", str(self.dist)]), 0)
            sheets = sorted(out.glob("saanche-*.png"))
            self.assertEqual(len(sheets), (len(saanche.names()) + 11) // 12)
            for sheet in sheets:
                png = sheet.read_bytes()
                self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
                self.assertGreater(len(png), 20000, sheet.name)  # a drawn grid, not an empty page
            index = (out / "INDEX.md").read_text(encoding="utf-8")
            for name in saanche.names():
                self.assertIn(name, index)


@unittest.skipUnless(shutil.which("node"), "needs node (the toolbox demos job has it)")
class Engine3DRender(unittest.TestCase):
    """The 3D layer draws (three.js on SwiftShader): a compiled plan with a 3D place and a 3D model renders, the same frame
    twice is the same bytes, and every 3D model's still sheet draws. Only here, where three.js is installed."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        try:
            cls.dist = render.build_preview(cls.tmp / "dist", engine=True, three=True)
        except render.RenderError as exc:                        # the canonical gate has node but not three.js
            raise unittest.SkipTest(f"engine3d build needs three.js and esbuild on NODE_PATH: {exc}")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def spec(self):
        sys.path.insert(0, str(ROOT / "tests"))
        from test_p1_models3d import FACTORY, HILL, RAMU, compiled, scene
        plan = scene(RAMU, {"op": "text", "text": "मशीनें", "at": {"spot": "machine2", "dy": -70}, "size": 44},
                     world3d=dict(FACTORY, steps=[{"t": {"line": "l2", "edge": "start"}, "p": {"running": 4, "output": 14}}],
                                  cam3d=[{"t": {"line": "l2", "edge": "start"}, "d": 1.5, "angle": -15}]), lines=("l1", "l2"))
        plan["scenes"].append({"id": "B", "lines": ["l3"], "bg": "paper", "cam": [], "steps": [
            dict(HILL, steps=[{"t": {"line": "l3", "edge": "start"}, "p": {"drop": 1, "flatten": 1}, "d": 1.0}],
                 cam3d=[{"t": {"line": "l3", "edge": "start"}, "d": 1.0, "angle": 0, "height": 18, "dist": 0, "ty": 0}])]})
        return compiled(plan)

    def test_a_3d_place_and_a_3d_model_render_under_the_svg_and_the_same_frame_is_the_same_bytes(self):
        spec = self.spec()
        self.assertTrue(render.needs_3d(spec))
        a = render.stills(spec, [30, 120, 230], dist=self.dist)
        b = render.stills(spec, [30, 120, 230], dist=self.dist)
        for png in a:
            self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
            self.assertGreater(len(png), 30000)                  # a drawn 3D frame, not an empty page
        self.assertEqual(a, b)                                    # same params and time -> same pixels
        self.assertNotEqual(a[0], a[1])                           # the step and the camera changed the frame
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(a[0])).convert("RGB")
        colours = len(set(im.resize((160, 90)).getdata()))
        self.assertGreater(colours, 200)                          # many colours: the 3D world is drawn, not one fill
        frames = render.audit(spec, dist=self.dist, every=30)
        self.assertIn("मशीनें", {t["t"] for f in frames for t in f["texts"]})   # the SVG words sit over the 3D layer

    def test_every_3d_model_still_draws(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import models3d_stills as tool
        from bie.brain.video import models3d
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            self.assertEqual(tool.main(["--out", str(out), "--dist", str(self.dist), "--width", "640"]), 0)
            frames = sorted(out.glob("models3d-*-[0-9].png"))
            self.assertEqual(len(frames), len(tool.states()))
            self.assertEqual({f.name.split("-")[1] for f in frames}, set(models3d.names()))
            for f in frames:
                self.assertGreater(len(f.read_bytes()), 8000, f.name)


@unittest.skipUnless(shutil.which("node"), "needs node (the toolbox demos job has it)")
class GameBotPlays(unittest.TestCase):
    """BIE's bot plays the allocate engine on a phone in Chromium: one wrong split (every box out of range reddens with
    its reason), then the right one (4 Nov 2026)."""

    def test_the_bot_plays_a_wrong_split_then_the_right_one(self):
        import json
        sys.path.insert(0, str(ROOT / "tests"))
        from test_p1_game_levels import allocate_level
        from bie.brain import game_levels as gl
        from bie.brain.game_build import bot_screenshots
        mission = gl.mission_of([allocate_level()], title="बैंक बनो")
        shots, info = bot_screenshots({"id": "a", "title": "बैंक", "world": "", "missions": [mission], "credits": []})
        self.assertTrue(shots, info)
        result = json.loads(info)
        self.assertEqual((result["won"], result["wrong_moves"], result["errors"]), (1, 1, []))


if __name__ == "__main__":
    unittest.main()
