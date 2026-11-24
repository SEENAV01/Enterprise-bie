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
    def test_the_hybrid_look_is_the_films_default_and_glossy_stays_one_word_away(self):
        # Navin, 23 November 2026, after the first heading film: "Is baar matte with controlled roshni nhi pehale wale
        # chamakdaar tarike se hi banao video"; then, 24 November 2026, after r3 of 11.6.3b in his 22 November "mixed" look
        # (structure close-ups, matte overviews, a light controlled sheen): "Behtar laga achha bana hai". Glossy stays one
        # word away
        self.assertEqual(studio_film.FILM_STYLE, "mixed")
        self.assertTrue(studio_film.image_prompt(SHOT).endswith(studio_film.CUTAWAY_STYLES["close_up"]))
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


class AsliLooks(unittest.TestCase):
    """Navin, 24 November 2026, after the real electron micrographs and the trial pictures: r4 of 11.6.3b is made three
    ways, "mixed" (the hybrid), "asli" (as electron micrographs show the chloroplast) and "asli_mixed" (protein close-ups
    clean, the rest asli), and he decides from the three."""

    def test_asli_draws_the_chloroplast_as_electron_micrographs_show_it(self):
        made = studio_film.image_prompt(SHOT, "", "asli")
        self.assertTrue(made.endswith(studio_film.CUTAWAY_STYLES["asli"]))
        self.assertIn("stacked like coins into grana", made)
        self.assertIn("never an empty smooth background", made)
        self.assertNotIn("glossy cells", made)
        self.assertIn("electron micrographs", studio_film.look_rule("asli"))
        self.assertIn("drawn large, in front", studio_film.look_rule("asli"))

    def test_asli_mixed_keeps_protein_close_ups_clean(self):
        close = {"visual": {"type": "cutaway", "image_prompt": "Closer section inside the ATP synthase head, CF1 lobes"}}
        wide = {"visual": {"type": "cutaway", "image_prompt": "A closed thylakoid sac with ATP synthase on its membrane"}}
        self.assertTrue(studio_film.image_prompt(close, "", "asli_mixed").endswith(studio_film.CUTAWAY_STYLES["close_up"]))
        self.assertTrue(studio_film.image_prompt(wide, "", "asli_mixed").endswith(studio_film.CUTAWAY_STYLES["asli"]))
        self.assertIn("Close-ups of proteins", studio_film.look_rule("asli_mixed"))

    def test_a_job_can_choose_either(self):
        import codex_vm
        for look in ("asli", "asli_mixed"):
            job = codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": f"r4-{look.replace('_', '-')}-test",
                                     "section": "studio", "stage": "films", "from_run": "https://example.org/runs/x",
                                     "look": look})
            self.assertEqual(job["look"], look)
        self.assertEqual(studio_film.FILM_STYLE, "mixed")          # not the films' rule until Navin decides
