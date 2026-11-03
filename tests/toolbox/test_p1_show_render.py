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

    def test_the_gold_spec_first_frames_render(self):
        spec = gold_spec(width=1280, height=720, assets={n: f"assets/{n}.png" for n in ASSETS_USED})
        pngs = render.stills(spec, [60], dist=self.dist, assets=self.tmp / "assets")
        self.assertTrue(pngs[0][:8] == b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
