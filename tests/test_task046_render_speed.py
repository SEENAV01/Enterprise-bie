"""Task 046 Part C, PR 4 · render speed: a video spec rendered in parallel chunks on several runners and joined into one
MP4 (tools/render_spec.py, the task046c-render workflow), frames [first, last) through the preview renderer
(``render.mp4_range``), and the blocks' per-frame cost cut: no per-frame SVG blur or drop-shadow filters, static layers
cached by the compositor (will-change) and vignettes as static gradients.

Offline: the arithmetic, the tool's commands on fixtures, the renderer's arguments (subprocess mocked), the block source
and the workflow text. The before/after timings are measured by ``render_spec.py bench`` on the same frames (STATUS).
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import render_spec  # noqa: E402
from bie.brain.video import render  # noqa: E402

BLOCKS = ROOT / "bie" / "brain" / "video" / "blocks" / "toolbox"
WORKFLOW = ROOT / ".github" / "workflows" / "task046c-render.yml"
SPEC = {"fps": 30, "width": 1920, "height": 1080, "captions": True,
        "scenes": [{"id": "a", "duration": 100, "layers": [{"id": "x", "type": "block", "block": "canvas_build", "at": 0, "box": {}, "data": {}}], "camera": [{"at": 0}]},
                   {"id": "b", "duration": 50, "layers": [{"id": "y", "type": "block", "block": "world_scene", "at": 0, "box": {}, "data": {}}], "camera": [{"at": 0}]}]}


class Chunks(unittest.TestCase):
    def test_every_frame_is_rendered_once_and_the_last_chunk_is_shorter(self):
        for total, chunks in ((150, 4), (1, 3), (10800, 8), (100, 100), (7, 8)):
            ranges = [render_spec.chunk_range(total, i, chunks) for i in range(chunks)]
            frames = [f for a, b in ranges for f in range(a, b)]
            self.assertEqual(frames, list(range(total)), (total, chunks))
            self.assertTrue(all(b - a <= ranges[0][1] - ranges[0][0] for a, b in ranges))

    def test_the_timing_row_and_the_cost_table(self):
        rows = [render_spec.timing_row(SPEC, 0, 300, 150.0, chunk=0, chunks=2), render_spec.timing_row(SPEC, 300, 600, 120.0, chunk=1, chunks=2)]
        self.assertEqual((rows[0]["video_seconds"], rows[0]["seconds_per_frame"], rows[0]["seconds_per_video_second"]), (10.0, 0.5, 15.0))
        cost = render_spec.measure(rows)
        self.assertEqual((cost["frames"], cost["video_seconds"], cost["seconds_per_frame"]), (600, 20.0, 0.45))
        self.assertEqual((cost["wall_clock_minutes_parallel"], cost["machine_minutes"]), (2.5, 4.5))
        self.assertAlmostEqual(cost["inr_at_list_price"], 4.5 * render_spec.LIST_PRICE_USD_PER_MINUTE * render_spec.USD_TO_INR, places=2)
        self.assertIn("bills Rs 0", cost["note"])

    def test_trim_keeps_whole_scenes_up_to_the_frame_limit(self):
        self.assertEqual([s["duration"] for s in render_spec.trim_spec(SPEC, 60)["scenes"]], [60])
        self.assertEqual([s["duration"] for s in render_spec.trim_spec(SPEC, 120)["scenes"]], [100, 20])
        self.assertEqual(render_spec.total_frames(render_spec.trim_spec(SPEC, 1000)), 150)
        self.assertEqual(render_spec.total_frames(SPEC), 150)             # the original is untouched

    def test_a_chunk_asks_the_renderer_for_its_frame_range(self):
        calls = []

        def fake_run(args, **kwargs):
            calls.append(args)
            return mock.Mock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as folder:
            dist = Path(folder, "dist")
            dist.mkdir()
            for name in ("bundle.js", "toolbox.js", "index.html", "toolbox.html", "toolbox.css"):
                (dist / name).write_text("", encoding="utf-8")
            with mock.patch.object(render.subprocess, "run", fake_run):
                render.mp4_range(SPEC, Path(folder, "part.mp4"), 50, 100, dist=dist, toolbox=True)
        args = calls[-1]
        self.assertEqual(args[:2], ["node", str(render.PREVIEW / "stills.mjs")])
        for flag, value in (("--from", "50"), ("--to", "100"), ("--page", "toolbox.html")):
            self.assertEqual(args[args.index(flag) + 1], value, flag)
        self.assertIn("--mp4", args)
        script = (render.PREVIEW / "stills.mjs").read_text(encoding="utf-8")
        self.assertIn("args.from", script)
        self.assertIn("for (let f = first; f < last; f++)", script)

    def test_the_tool_measures_summarises_and_refuses_a_missing_part(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            for i, seconds in enumerate((150.0, 120.0)):
                row = render_spec.timing_row(SPEC, i * 75, (i + 1) * 75, seconds, chunk=i, chunks=2)
                (out / f"part-{i:02d}.json").write_text(json.dumps(row), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(render_spec.main(["measure", "--out", str(out)]), 0)
            cost = json.loads((out / "cost.json").read_text(encoding="utf-8"))
            self.assertEqual((cost["chunks"], cost["frames"], cost["video_seconds"]), (2, 150, 5.0))
            (out / "join.json").write_text(json.dumps({"video_bytes": 12_000_000, "review_bytes": 3_000_000, "seconds": 5.0}), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(render_spec.main(["summary", "--out", str(out), "--run-id", "7", "--sha", "abc"]), 0)
            report = (out / "REPORT.md").read_text(encoding="utf-8")
            self.assertIn("0.08 minutes of video in 2 chunks", report)
            self.assertIn("billed ₹0", report)
            self.assertEqual(json.loads((out / "summary.json").read_text(encoding="utf-8"))["run_id"], "7")
            with self.assertRaises(SystemExit):
                render_spec.cmd_join(mock.Mock(out=str(out), chunks=2, review=720, audio=""))

    def test_the_fixture_spec_is_the_kits_two_parts_and_the_credits(self):
        from bie.brain import canvas
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(render_spec, "fixture_spec", wraps=render_spec.fixture_spec) as spy:
            icons_dir = Path(folder, "icons")
            rows = __import__("bie.toolbox.icons", fromlist=["by_id"]).by_id()
            plan = json.loads((ROOT / "tests/fixtures/task046c/demand_pull_touches.plan.json").read_text(encoding="utf-8"))
            for i in canvas.icons_in(plan):
                path = icons_dir / rows[i]["file"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg"><!-- {i} --></svg>', encoding="utf-8")
            with mock.patch.dict("os.environ", {"BIE_TWEMOJI_SVG": str(icons_dir), "BIE_FONTAWESOME_SVGS": str(icons_dir)}):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(render_spec.main(["fixture", "--out", str(Path(folder, "in"))]), 0)
            self.assertTrue(spy.called)
            spec = json.loads(Path(folder, "in", "video_spec.json").read_text(encoding="utf-8"))
            self.assertEqual([s["layers"][0]["block"] for s in spec["scenes"]], ["canvas_build", "world_scene", "canvas_build"])
            self.assertTrue(60 < render_spec.total_frames(spec) / spec["fps"] < 90)
            self.assertTrue(Path(folder, "in", "assets", "assets.json").exists() or any(Path(folder, "in", "assets").iterdir()))


class Blocks(unittest.TestCase):
    def test_no_per_frame_filters_and_the_static_layers_are_cached(self):
        canvas_tsx = (BLOCKS / "canvas.tsx").read_text(encoding="utf-8")
        world_tsx = (BLOCKS / "world.tsx").read_text(encoding="utf-8")
        for text, name in ((canvas_tsx, "canvas.tsx"), (world_tsx, "world.tsx")):
            self.assertNotIn("feGaussianBlur", text, name)
            self.assertNotIn("drop-shadow(", text, name)
            self.assertNotIn('boxShadow: "inset', text, name)
            self.assertNotIn("filter=\"url(", text, name)
        self.assertIn('willChange: "transform"', canvas_tsx)                   # the camera layer
        self.assertIn("React.memo", world_tsx)                                # static layers drawn once
        self.assertGreaterEqual(world_tsx.count("<Layer "), 6)
        self.assertIn("radial-gradient(ellipse at 50% 50%", world_tsx)         # the vignette as a static gradient
        self.assertIn("radial-gradient(ellipse at 50% 50%", canvas_tsx)


class Workflow(unittest.TestCase):
    def test_the_render_workflow_chunks_joins_measures_and_publishes_only_the_review_copy(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("render_spec.py chunk", text)
        self.assertIn("render_spec.py join", text)
        self.assertIn("render_spec.py measure", text)
        self.assertIn("render_spec.py fixture", text)
        self.assertIn("fromJSON(needs.prepare.outputs.matrix)", text)
        self.assertIn("max-parallel: 16", text)
        self.assertIn("name: t046c-video", text)                              # the full MP4 is a CI artifact
        self.assertIn("review-720p.mp4", text)
        publish = text.split("Publish the review copy", 1)[1]
        self.assertNotIn("video.mp4", publish)                                # never the full MP4 on the public branch
        self.assertIn("apt_prefetch", text)                                   # F-11: bounded apt downloads
        self.assertIn("persist-credentials: false", text)
        self.assertNotIn("/../", text)                                        # F-13d: actions/cache refuses a path with ".."
        paths = (ROOT / ".github" / "workflows" / "toolbox.yml").read_text(encoding="utf-8")
        self.assertIn("'tools/render_spec.py'", paths)


if __name__ == "__main__":
    unittest.main()
