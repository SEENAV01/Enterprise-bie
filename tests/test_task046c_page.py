"""Task 046 Part C · the review page tool (``tools/task046c_page.py``) builds Navin's page from BIE's own run folders.

Offline: a two-part canvas.json, a spec with two scenes, a render summary; no video, no ffmpeg needed. The page must carry the
review-copy link, every part with its mode and place, the render numbers, each scene's start time and the plans' spoken lines.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SPEC = importlib.util.spec_from_file_location("task046c_page", ROOT / "tools" / "task046c_page.py")
page = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(page)

CANVAS = {"schema": "bie.brain.canvas/1", "course": {"title": "3. Money", "subject": "Indian Economy", "learners": "UPSC aspirants"},
          "maker_route": "codex", "missing_kits": [],
          "videos": [{"video_id": "v1", "title": "Money क्या है?", "parts_passed": 2, "first_try_passes": 1, "rounds": 3, "cost_usd": 0.0,
                      "modes": {"B": 1, "C": 1}, "credits": ["basket (tw:1f9fa) · CC BY 4.0"], "seconds": 21.0, "status": "spec_written",
                      "parts": [{"id": "v1_s1s", "part_id": "c01.1", "beats": 1, "mode": "C", "place": "shop", "story": True, "status": "passed",
                                 "rounds": 1, "first_try": True, "cost_usd": 0.0, "last_problems": [], "level": "L3", "seconds": 10.0,
                                 "elements": 5, "longest_still_s": 2.0, "advisories": []},
                                {"id": "v1_s1b", "part_id": "c01.1", "beats": 1, "mode": "B", "place": "", "story": False, "status": "passed",
                                 "rounds": 2, "first_try": False, "cost_usd": 0.0, "last_problems": [], "level": "L2 + touches", "seconds": 11.0,
                                 "elements": 8, "longest_still_s": 2.3, "advisories": ["one still of 2.3 s"]}]}],
          "quality": {"videos": 1, "videos_written": 1, "parts": 2, "parts_passed": 2, "first_try_passes": 1, "first_try_rate": 0.5, "rounds": 3,
                      "modes": {"B": 1, "C": 1}, "story_parts": 1, "story_parts_in_a_world": 1, "missing_kits": [], "seconds": 21.0, "cost_usd": 0.0}}
SPEC_JSON = {"schema": "bie.render-spec/1", "fps": 30, "width": 1920, "height": 1080, "captions": True,
             "scenes": [{"id": "v1_s1s", "duration": 300, "layers": []}, {"id": "v1_s1b", "duration": 330, "layers": []}, {"id": "v1_credits", "duration": 150, "layers": []}]}
RENDER = {"schema": "bie.render-spec.summary/1", "run_id": "123", "sha": "abcdef0123456789", "run_url": "https://github.com/x/y/actions/runs/123",
          "cost": {"chunks": 8, "frames": 780, "video_minutes": 0.43, "seconds_per_video_second": 3.78, "wall_clock_minutes_parallel": 0.4,
                   "machine_minutes": 1.6, "inr_at_list_price": 1.07},
          "join": {"review": "/tmp/out/review-720p.mp4", "review_bytes": 1_500_000, "seconds": 26.0, "chunks": 8}}


class ReviewPage(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="t046c-page-"))
        canvas = self.tmp / "canvas"
        (canvas / "plans").mkdir(parents=True)
        (canvas / "video_specs").mkdir()
        (canvas / "canvas.json").write_text(json.dumps(CANVAS, ensure_ascii=False), encoding="utf-8")
        (canvas / "video_specs" / "v1.json").write_text(json.dumps(SPEC_JSON), encoding="utf-8")
        (canvas / "plans" / "v1_s1s.plan.json").write_text(json.dumps({"id": "v1_s1s", "kit": "shop", "beats": [{"beat_id": "b2", "say": "चाय ₹10 की है।"}]}, ensure_ascii=False), encoding="utf-8")
        (canvas / "plans" / "v1_s1b.plan.json").write_text(json.dumps({"id": "v1_s1b", "beats": [{"beat_id": "b11", "say": "आगे functions में यही आधार रखिए।"}]}, ensure_ascii=False), encoding="utf-8")
        render = self.tmp / "render"
        render.mkdir()
        (render / "summary.json").write_text(json.dumps(RENDER), encoding="utf-8")
        self.canvas, self.render = canvas, render

    def test_only_one_video_of_a_run_that_planned_several(self):
        two = json.loads(json.dumps(CANVAS))
        v2 = json.loads(json.dumps(two["videos"][0])); v2.update(video_id="v2", title="Barter से commodity money", parts=[])
        two["videos"].append(v2)
        (self.canvas / "canvas.json").write_text(json.dumps(two, ensure_ascii=False), encoding="utf-8")
        both = page.build(self.canvas, self.render)
        self.assertEqual(both.count("<h1>"), 2)
        one = page.build(self.canvas, self.render, only="v1")
        self.assertEqual(one.count("<h1>"), 1)
        self.assertIn("Money क्या है?", one)
        self.assertNotIn("Barter से commodity money", one)
        with self.assertRaises(SystemExit):
            page.build(self.canvas, self.render, only="v9")

    def test_scene_times_come_from_the_spec_durations(self):
        times = page.scene_times(SPEC_JSON)
        self.assertEqual([t["id"] for t in times], ["v1_s1s", "v1_s1b", "v1_credits"])
        self.assertEqual(times[1]["start_s"], 10.0)
        self.assertEqual(times[1]["mid_s"], 15.5)
        self.assertEqual(times[2]["start_s"], 21.0)

    def test_the_page_carries_the_link_the_parts_the_render_numbers_and_the_script(self):
        html = page.build(self.canvas, self.render, base_url="https://example.invalid/runs/t046c-money-v1c")
        self.assertIn('href="https://example.invalid/runs/t046c-money-v1c/review-720p.mp4"', html)
        self.assertIn("<title>3. Money · review</title>", html)
        for needle in ("v1_s1s", "v1_s1b", "C · L3 world", "B · build-up canvas + L3 touches", "shop", "story", "first try",
                       "3.78", "1.6", "₹1.07", "0:10 · 11.0 s", "चाय ₹10 की है।", "आगे functions में यही आधार रखिए।", "basket (tw:1f9fa)",
                       "one still of 2.3 s", "Navin ke faisle", "task046c_page.py"):
            self.assertIn(needle, html, needle)
        self.assertNotIn("Ek still har scene", html, "no video and no stills folder: no stills section")

    def test_stills_from_a_folder_are_embedded_per_scene(self):
        from PIL import Image
        stills = self.tmp / "stills"
        stills.mkdir()
        Image.new("RGB", (64, 36), (200, 120, 40)).save(stills / "v1_s1s.png")
        html = page.build(self.canvas, self.render, stills_dir=stills)
        self.assertIn("Ek still har scene", html)
        self.assertIn('alt="v1_s1s"', html)
        self.assertNotIn('alt="v1_s1b"', html)
        self.assertIn("data:image/jpeg;base64,", html)
        self.assertIn("v1_s1s · 0:05 · C · L3 world · shop", html)

    def test_the_tool_writes_the_file(self):
        out = self.tmp / "page.html"
        self.assertEqual(page.main(["--canvas", str(self.canvas), "--render", str(self.render), "--html", str(out), "--note", "pehla render"]), 0)
        text = out.read_text(encoding="utf-8")
        self.assertIn("pehla render", text)
        self.assertLess(len(text.encode("utf-8")), 16_000_000)


if __name__ == "__main__":
    unittest.main()
