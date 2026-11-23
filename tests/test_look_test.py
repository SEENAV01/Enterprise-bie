"""The look test (tools/look_test.py, studio_film.CUTAWAY_STYLES; Navin, 22 November 2026, on the 11.6 films: "visuals
asli banane the ... ab cheezen zyada banawati lag rahi hain ... abhi alag se dekhein")."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from bie.brain import studio_film

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import look_test  # noqa: E402
import vm_image  # noqa: E402

SHOT = {"id": "s2", "visual": {"type": "cutaway", "image_prompt": "16:9 realistic cutaway of a thylakoid membrane with "
                                                                  "PS II on the left and ATP synthase on the right"}}
PHOTO = {"id": "s1", "visual": {"type": "photo", "image_prompt": "a green leaf in morning sunlight on a farm"}}


class Styles(unittest.TestCase):
    def test_the_glossy_look_is_the_films_default_and_mixed_stays_one_word_away(self):
        # Navin, 23 November 2026, after the first heading film: "Is baar matte with controlled roshni nhi pehale wale
        # chamakdaar tarike se hi banao video"; his 22 November "mixed" look (structure close-ups, matte overviews, a light
        # controlled sheen) stays one word away
        self.assertEqual(studio_film.FILM_STYLE, "glossy")
        self.assertTrue(studio_film.image_prompt(SHOT).endswith(studio_film.CUTAWAY_SUFFIX))
        self.assertIn("glossy cells, soft volumetric light", studio_film.CUTAWAY_SUFFIX)
        self.assertIn("glossy cells, soft\n  volumetric light", studio_film.INSTRUCTIONS)
        self.assertTrue(studio_film.image_prompt(SHOT, "", "mixed").endswith(studio_film.CUTAWAY_STYLES["close_up"]))
        overview = {"visual": {"type": "cutaway", "image_prompt": "a whole chloroplast with its grana stacks; no proteins at "
                                                                   "this scale"}}
        self.assertTrue(studio_film.image_prompt(overview, "", "mixed").endswith(studio_film.CUTAWAY_STYLES["overview"]))
        self.assertIn("controlled satin sheen", studio_film.CUTAWAY_STYLES["close_up"])
        self.assertIn("never gritty", studio_film.CUTAWAY_STYLES["close_up"])
        self.assertTrue(studio_film.image_prompt(SHOT, "", "glossy").endswith(studio_film.CUTAWAY_SUFFIX))
        self.assertEqual(studio_film.CUTAWAY_STYLES["glossy"], studio_film.CUTAWAY_SUFFIX)

    def test_a_style_replaces_only_how_the_cutaway_is_rendered(self):
        matte = studio_film.image_prompt(SHOT, "", "matte")
        self.assertIn("PS II on the left and ATP synthase on the right", matte)      # what the shot shows is kept
        self.assertIn("matte non-reflective", matte)
        self.assertNotIn("glossy cells", matte)
        self.assertIn("no labels", matte)
        self.assertTrue(studio_film.image_prompt(PHOTO, "", "matte").endswith(studio_film.IMAGE_SUFFIX))   # photos untouched


class LookTest(unittest.TestCase):
    def run_dir(self, folder):
        films = Path(folder) / "films"
        films.mkdir()
        (films / "a15.json").write_text(json.dumps({"film": {"look": "teal world; PS II: emerald", "shots": [PHOTO, SHOT]}}),
                                        encoding="utf-8")
        return str(folder)

    def test_it_writes_a_prompt_file_the_vm_image_section_accepts(self):
        with tempfile.TemporaryDirectory() as folder:
            data = look_test.prompts(self.run_dir(folder), [("a15", "s2")], "structure")
            checked = vm_image.load_prompts(json.dumps(data))
            self.assertEqual([p["id"] for p in checked["prompts"]], ["a15-s2-structure"])
            self.assertIn("atomic-surface model", checked["prompts"][0]["prompt"])

    def test_it_refuses_what_it_cannot_test(self):
        with tempfile.TemporaryDirectory() as folder:
            run = self.run_dir(folder)
            with self.assertRaises(ValueError):
                look_test.prompts(run, [("a15", "s1")], "matte")                    # a photo, not a cutaway
            with self.assertRaises(ValueError):
                look_test.prompts(run, [("a15", "s2")], "neon")                     # no such style
            self.assertEqual(look_test.prompts(run, [("a15", "s2")], "mixed")["prompts"][0]["id"], "a15-s2-mixed")
            with self.assertRaises(ValueError):
                look_test.prompts(run, [("a15", "s2")] * 5, "matte")                # the image section takes 4
