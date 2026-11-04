"""Phase 1, part E (first slice): one chain from the book to the new slots, and the chapter review page.

Offline: the chain runs with the brain's fake maker; the review page is built from the run folder it leaves.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from bie.brain import cost  # noqa: E402

from test_p1_show_director import COURSE, LESSON, Writers, runner_of  # noqa: E402


class ChainWithShow(unittest.TestCase):
    def test_the_estimate_counts_the_new_sections_only_with_show(self):
        plain = cost.estimate("chain", 10, rate=90.0)
        with_show = cost.estimate("chain", 10, rate=90.0, with_show=True)
        self.assertNotIn("showplan", plain["sections"])
        for name in ("showplan", "notespages", "gamelevels"):
            self.assertIn(name, with_show["sections"])
        self.assertGreater(with_show["total_inr"], plain["total_inr"])

    def test_run_brain_offers_the_flag(self):
        text = (ROOT / "tools" / "run_brain.py").read_text(encoding="utf-8")
        self.assertIn("--with-show", text)
        self.assertIn("run_show_director(lesson, course, runner, out", text)
        self.assertIn("run_notes_pages(chapter, course, runner, out", text)
        self.assertIn("run_game_levels(chapter, course, runner, out", text)


class ReviewPage(unittest.TestCase):
    def test_the_page_shows_what_exists_and_says_what_does_not(self):
        import p1_review_page as tool
        from bie.brain.show_director import run_show_director
        from bie.brain.show_writers import run_game_levels, run_notes_pages
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            run_show_director(LESSON, COURSE, runner_of(), run)
            run_notes_pages(Writers.CHAPTER, COURSE, runner_of(), run)
            run_game_levels(Writers.CHAPTER, COURSE, runner_of(), run)
            self.assertEqual(tool.main(["--run", str(run), "--title", "पैसा"]), 0)
            page = (run / "REVIEW.html").read_text(encoding="utf-8")
            self.assertIn("पैसा", page)
            self.assertIn("v9 · passed", page)
            self.assertIn("video abhi render nahi hua", page)     # honest: the render has not run
            self.assertIn("notes/NOTES_PAGES.html", page)
            self.assertIn("game/GAME.html", page)
            self.assertIn("1/1 pass", page)
            self.assertIn("2 (find_partner, run_process)", page)
            self.assertIn("viewport", page)

    def test_an_empty_run_still_makes_an_honest_page(self):
        import p1_review_page as tool
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            self.assertEqual(tool.main(["--run", str(run)]), 0)
            page = (run / "REVIEW.html").read_text(encoding="utf-8")
            self.assertIn("Koi scene plan nahi bana", page)
            self.assertIn("abhi nahi bana", page)


class OneButtonWorkflow(unittest.TestCase):
    def test_the_workflow_fans_out_the_existing_render_and_publishes_one_page(self):
        text = (ROOT / ".github" / "workflows" / "p1-one-button.yml").read_text(encoding="utf-8")
        self.assertIn("gh workflow run task046c-render.yml", text)       # the existing render path, not a new one
        self.assertIn("showplan.json", text)
        self.assertIn("tools/p1_review_page.py", text)
        self.assertIn("REVIEW.html", text)
        self.assertIn("actions: write", text)
        self.assertIn("contents: write", text)
        self.assertNotIn("video.mp4\n", text)                            # only review copies travel to the branch
        self.assertIn("already rendered", text)                          # a re-run never renders a landed video again

    def test_the_render_workflow_counts_frames_of_either_spec_kind(self):
        # The first one-button run died in the render's prepare step on KeyError 'duration': the inline frame
        # count assumed the old per-scene shape, while a show-spec carries seconds. It must use render.total_frames.
        text = (ROOT / ".github" / "workflows" / "task046c-render.yml").read_text(encoding="utf-8")
        self.assertIn("render.total_frames(spec)", text)
        self.assertNotIn('sum(s["duration"] for s in spec["scenes"])', text)


class TrimMap(unittest.TestCase):
    def test_the_trim_keeps_only_what_the_videos_teach_and_still_validates(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import trim_chapter_map as tool
        from bie.brain import formats
        chapter = {"schema": "bie.brain.chapter-map/2", "course": {"title": "t", "subject": "s", "learners": "l"},
                   "source_sha256": "a" * 64, "pages": [{"page": 2}, {"page": 9}],
                   "items": {"i1": {"item_id": "i1", "content": "a", "teachable": True, "page": 2},
                             "i2": {"item_id": "i2", "content": "b", "teachable": True, "page": 9}},
                   "map": {"chapter_title": "t", "concepts": [
                       {"concept_id": "c1", "name": "one", "item_ids": ["i1"]},
                       {"concept_id": "c2", "name": "two", "item_ids": ["i2"]}]},
                   "map_status": "passed"}
        lesson = {"videos": [{"video_id": "v4", "beats": [{"covers_item_ids": ["i1"]}]},
                             {"video_id": "v9", "beats": [{"covers_item_ids": ["i2"]}]}]}
        out = tool.trim(chapter, lesson, ["v4"])
        self.assertEqual(sorted(out["items"]), ["i1"])
        self.assertEqual([c["concept_id"] for c in out["map"]["concepts"]], ["c1"])
        self.assertEqual(formats.problems("chapter_map", out), [])
        with self.assertRaises(SystemExit):
            tool.trim(chapter, lesson, ["v99"])


if __name__ == "__main__":
    unittest.main()
