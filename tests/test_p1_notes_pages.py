"""Phase 1, part B4: the notes-page slot — one question per page, the picture drawn by the showing engine.

Offline. The example pages here are test data (Claude's demo, not BIE output; BIE's AI writes real pages in
part C), never passed outputs.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import formats, notes_pages as np  # noqa: E402
from bie.brain.notes_render import render_notes_html  # noqa: E402
from bie.brain.video import render  # noqa: E402


def page(kind="picture", **extra):
    base = {"schema": "bie.notes-page/1", "page_id": f"money-{kind}", "ask": "what",
            "question": "Barter kya hai?", "essence": "चीज़ के बदले चीज़।",
            "answer": "रामू गेहूँ देता है, मोहन कपड़ा: बिना पैसे का सौदा।", "item_ids": ["p002-i2"]}
    if kind == "picture":
        base["visual"] = {"kind": "picture", "bg": "village", "caption": "गेहूँ ↔ कपड़ा",
                          "els": [
                              {"draw": "__person__", "look": "ramu", "h": 300, "pose": "give", "facing": 1, "x": 700, "y": 700},
                              {"draw": "__person__", "look": "mohan", "h": 300, "pose": "give", "facing": -1, "x": 1200, "y": 700},
                              {"draw": "sack", "p": {"w": 180, "label": "गेहूँ"}, "x": 560, "y": 860},
                              {"draw": "clothRoll", "p": {"w": 160}, "x": 1350, "y": 820},
                              {"text": "Barter: चीज़ ↔ चीज़", "size": 48, "style": "pill", "bg": "#2fb463",
                               "fill": "#fff", "x": 960, "y": 200},
                          ]}
    elif kind == "flow":
        base["visual"] = {"kind": "flow", "title": "सौदे के कदम",
                          "steps": [{"label": "मिलो", "detail": "जिसके पास चाहिए वाली चीज़ हो"},
                                    {"label": "भाव तय", "detail": "कितना गेहूँ, कितना कपड़ा"},
                                    {"label": "अदला-बदली", "detail": "दोनों की ज़रूरत पूरी"}]}
    elif kind == "compare":
        base["visual"] = {"kind": "compare", "title": "Barter बनाम पैसा", "columns": ["Barter", "पैसा"],
                          "rows": [{"label": "ज़रूरत", "cells": ["दोनों की एक साथ", "किसी एक की"]},
                                   {"label": "नाप", "cells": ["कोई एक नाप नहीं", "एक ही नाप"]}]}
    else:
        base["visual"] = {"kind": "table", "title": "कौन क्या लाया",
                          "rows": [{"label": "रामू", "cells": ["गेहूँ"]}, {"label": "मोहन", "cells": ["कपड़ा"]}]}
    base.update(extra)
    return base


class PageSlot(unittest.TestCase):
    def test_every_kind_is_a_valid_page(self):
        for kind in np.KINDS:
            pg = page(kind)
            self.assertEqual(formats.problems("notes_page", pg), [], kind)
            self.assertEqual(np.problems(pg), [], kind)

    def test_a_picture_page_is_a_show_spec_the_engine_draws(self):
        spec = np.still_spec(page("picture"))
        self.assertEqual(formats.problems("show_spec", spec), [])
        self.assertTrue(render.needs_engine(spec))              # the same engine as the video draws the page
        self.assertEqual(render.total_frames(spec), 30)
        self.assertEqual(spec["scenes"][0]["bg"], "village")

    def test_a_wrong_page_is_named_exactly(self):
        pg = page("picture")
        pg["visual"]["els"][2]["p"] = {"w": 180, "colour": "red"}
        self.assertTrue(any("no parameter 'colour'" in p for p in np.problems(pg)))
        pg = page("picture")
        pg["visual"]["els"][4]["size"] = 24
        self.assertTrue(any("under the 36px floor" in p for p in np.problems(pg)))
        pg = page("picture")
        pg["visual"]["els"][0]["x"] = 5000
        self.assertTrue(any("off the 1920x1080 stage" in p for p in np.problems(pg)))
        pg = page("compare")
        pg["visual"]["rows"][0]["cells"] = ["x"]
        self.assertTrue(any("has 1 cells for 2 columns" in p for p in np.problems(pg)))
        pg = page("flow")
        pg["visual"]["steps"] = pg["visual"]["steps"][:1]
        self.assertTrue(any("at least 2 steps" in p for p in np.problems(pg)))
        pg = page("table")
        pg["ask"] = "quiz"
        self.assertTrue(any("no ask 'quiz'" in p for p in np.problems(pg)))

    def test_pages_become_the_existing_notes_deck_with_the_rendered_picture(self):
        pages = [page(k) for k in np.KINDS]
        deck = np.deck_of(pages, course={"title": "पैसा", "subject": "Economics", "learners": "class 9",
                                         "language": "Hinglish"},
                          chapter_name="पैसे की कहानी", images={"money-picture": "pages/money-picture.png"})
        html = render_notes_html(deck)
        self.assertIn("Barter kya hai?", html)
        self.assertIn("pages/money-picture.png", html)
        self.assertIn('"type": "image"', html.replace('","', '", "').replace('":"', '": "'))
        self.assertIn("difference_table", html)
        with self.assertRaises(ValueError) as ctx:
            np.deck_of([page("flow", essence="")], course={}, chapter_name="x")
        self.assertIn("'essence' is needed", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
