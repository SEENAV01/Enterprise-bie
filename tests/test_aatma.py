"""Aatma ki almaari (Navin, 23 November 2026): a passed film's ways of teaching and showing, found by code, kept as forms
with blanks that each subject fills with its own words, locked only after Navin's yes, and used in every subject's next
film (its prompt and its check)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import aatma, studio_film  # noqa: E402
import lock_aatma  # noqa: E402


def line(roman, **kw):
    base = {"roman": roman, "voice": roman, "pins": [], "arrows": [], "effects": [], "focus": [],
            "zoom": {"x": 50, "y": 50, "scale": 1.0}, "moves": [], "grows": [], "fuses": [], "reacts": [], "cycles": [],
            "acts": [], "step": 0, "count": {}, "teaches": [], "beyond": "", "part": "concept"}
    base.update(kw)
    return base


def film():
    """A small film with each way once: a whole place, a dive into a machine, a thing that moves through it as it is
    named after the two sides are shown, three steps on one picture, a part that acts, a question then its answer, and an
    everyday aside with its mapping."""
    pump = {"label": "CF0", "x": 50, "y": 50}
    move = {"what": "H+", "label": "H⁺", "points": [[50, 90], [50, 52], [50, 10]], "count": 2}
    return {"title": "Gradient se ATP", "shots": [
        {"id": "s1", "title": "Thylakoid", "visual": {"type": "cutaway", "image_prompt": "a thylakoid"}, "dive": {"x": -1, "y": -1},
         "sentences": [line("Lumen mein H⁺ zyada hain aur stroma mein kam."), line("Yeh hai poori thylakoid.")]},
        {"id": "s2", "title": "ATP synthase", "dive": {"x": 60, "y": 40},
         "visual": {"type": "cutaway", "image_prompt": "ATP synthase", "parts": [{"id": "lobe", "name": "CF1", "looks": "a lobe"}]},
         "sentences": [line("Lumen mein H⁺ ki bheed hai, stroma khaali.", step=1, pins=[pump]),
                       line("Ab H⁺ CF0 se guzarta hai.", step=2, moves=[move]),
                       line("Return ke liye energy kyun nahi lagani?"),
                       line("Kyunki gradient pehle se energy rakhta hai, isliye CF1 kasta hai.", step=3,
                            acts=[{"part": "lobe", "do": "tight", "toward": [60, 30]}])]},
        {"id": "s3", "title": "Baandh", "aside": True, "dive": {"x": -1, "y": -1}, "visual": {"type": "photo", "image_prompt": "a dam"},
         "sentences": [line("Socho ek baandh.", pins=[{"label": "baandh = membrane", "x": 30, "y": 30}])]}]}


class Forms(unittest.TestCase):
    def test_the_ways_are_found_by_code(self):
        got = {f["id"]: f for f in aatma.forms(film())}
        for fid in ("naam_par_chale", "andar_se_raasta", "pehle_zyada_kam", "ek_ek_step", "hissa_hile",
                    "sawaal_phir_jawab", "poora_phir_zoom", "rozmarra_misaal"):
            self.assertIn(fid, got)
        self.assertEqual(got["andar_se_raasta"]["filled"], {"chalti cheez": "H⁺", "machine": "CF0"})
        self.assertEqual(got["hissa_hile"]["filled"], {"hissa": "CF1", "kaam": "kasta hai"})
        self.assertEqual(got["rozmarra_misaal"]["filled"]["mapping"], "baandh = membrane")
        self.assertEqual({f["kind"] for f in got.values()} - set(aatma.KINDS), set())

    def test_a_form_carries_no_subject_word(self):
        for f in aatma.forms(film()):
            for value in (f.get("filled") or {}).values():
                if value and len(str(value)) > 2:
                    self.assertNotIn(str(value), f["form"], f["id"])
            self.assertRegex(f["form"], r"\[|Ek hi tasveer|Camera")              # blanks, or a way with no blank

    def test_measures_carry_no_subject(self):
        m = aatma.measures(film())
        self.assertEqual((m["lines"], m["shots"], m["asides"]), (7, 3, 1))
        self.assertAlmostEqual(m["questions"], round(1 / 7, 2))
        self.assertTrue(all(isinstance(v, (int, float)) for v in m.values()))

    def test_the_review_page_shows_each_drawer(self):
        page = aatma.page(film(), question={"question": "Gradient kyun?"}, chapter="Photosynthesis")
        for said in ("Is film ki aatma", "Process / mechanism", "Kaaran (kyun)", "[chalti cheez] khud chale",
                     "Is film mein: chalti cheez: <b>H⁺</b>", "learner ko nahi dikhta", "Film ka naap"):
            self.assertIn(said, page)


class Almaari(unittest.TestCase):
    def test_empty_until_navin_says_yes(self):
        book = json.loads(aatma.PATH.read_text(encoding="utf-8"))
        self.assertEqual((book["schema"], book["films"]), (aatma.SCHEMA, []))
        self.assertEqual(aatma.prompt_part("NEET Biology", book), "")
        self.assertEqual(aatma.aatma_problems(film(), book), [])
        with mock.patch.object(aatma, "almaari", return_value=book):
            text = studio_film.messages({"id": "q", "question": "?", "points": []}, course="Biology", language="Hinglish")[0]["content"]
        self.assertNotIn("aatma ki almaari", text)

    def test_a_locked_film_teaches_every_subject_with_its_own_words(self):
        book = aatma.lock({"schema": aatma.SCHEMA, "version": 0, "films": [], "kits": {}}, film(), qid="h11-6-3b",
                          run="runs/x", by="Navin, 24 November 2026", words="bolte huye wahi step dikhta hai")
        self.assertEqual(book["version"], 1)
        entry = book["films"][0]
        self.assertEqual((entry["by"], entry["words"]), ("Navin, 24 November 2026", "bolte huye wahi step dikhta hai"))
        self.assertIn({"chalti cheez": "H⁺", "machine": "CF0"}, [f["example"] for f in entry["forms"]])
        economics = aatma.prompt_part("Class 11 Economics: Money", book)
        self.assertIn("aatma ki almaari", economics)
        self.assertIn("[chalti cheez] khud chale", economics)
        self.assertIn("This subject's own things (economics)", economics)
        self.assertIn("Kirana shop", economics)                                 # from the examples Navin locked
        for biology in ("H⁺", "CF0", "CF1", "thylakoid", "baandh"):
            self.assertNotIn(biology, economics)                                # no other subject's words
        again = aatma.lock(book, film(), qid="h11-6-3b", run="runs/x", by="Navin", only=["ek_ek_step"])
        self.assertEqual((len(again["films"]), [f["id"] for f in again["films"][0]["forms"]]), (1, ["ek_ek_step"]))

    def test_a_new_film_is_measured_against_the_passed_ones(self):
        book = {"films": [{"qid": "p", "measures": {"camera_moves": 0.38, "movers_per_line": 2.5, "questions": 0.21}}]}
        busy = film()
        for shot in busy["shots"]:
            for k, s in enumerate(shot["sentences"]):
                s["zoom"] = {"x": 20 + 30 * (k % 2), "y": 50, "scale": 1.0 + 0.4 * (k % 2)}
                s["pins"] = s["pins"] or [{"label": f"p{k}", "x": 10, "y": 10}]
                s["roman"] = s["roman"].rstrip("?") + "."
        said = " ".join(aatma.aatma_problems(busy, book))
        self.assertIn("the camera moves on", said)
        self.assertIn("ask before the answer", said)

    def test_kits_come_from_bies_own_resources(self):
        kits = aatma.kits({"kits": {"economics": {"hissa": ["dukaan ka shutter"]}}})
        self.assertIn("Kirana shop", kits["economics"]["jagah"])
        self.assertIn("shopkeeper", kits["economics"]["kirdaar"])
        self.assertIn("dukaan ka shutter", kits["economics"]["hissa"])
        self.assertTrue(kits["biology"]["chalti cheez"])
        self.assertEqual((aatma.subject_of("NEET + Class 11 Biology"), aatma.subject_of("Indian Economy")),
                         ("biology", "economics"))


class LockTool(unittest.TestCase):
    def test_the_page_and_the_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder) / "run"
            (run / "films").mkdir(parents=True)
            (run / "films" / "q1.json").write_text(json.dumps({"film": film()}), encoding="utf-8")
            (run / "questions.json").write_text(json.dumps({"chapter_title": "Photosynthesis",
                                                             "questions": [{"id": "q1", "question": "Gradient kyun?"}]}),
                                                encoding="utf-8")
            page = Path(folder) / "aatma.html"
            lock_aatma.main(["--run", str(run), "--qid", "q1", "--page", "--out", str(page)])
            self.assertIn("Gradient kyun?", page.read_text(encoding="utf-8"))
            book = Path(folder) / "aatma.json"
            book.write_text(json.dumps({"schema": aatma.SCHEMA, "version": 0, "films": [], "kits": {}}), encoding="utf-8")
            with self.assertRaises(SystemExit):                                  # no lock without Navin's yes
                lock_aatma.main(["--run", str(run), "--qid", "q1", "--book", str(book)])
            lock_aatma.main(["--run", str(run), "--qid", "q1", "--book", str(book), "--by", "Navin, 24 November 2026"])
            self.assertEqual(json.loads(book.read_text(encoding="utf-8"))["version"], 1)


if __name__ == "__main__":
    unittest.main()
