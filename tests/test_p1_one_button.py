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


if __name__ == "__main__":
    unittest.main()
