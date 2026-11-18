"""The course studio, stage 4 (Navin, 18 November 2026): the Living Book notes per question, checked by code (coverage,
the class moment, the check question, no source or caution lines) and built into the chapter's phone notes with the
film's own picture and pins. Offline: fake maker."""
from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import codex_vm  # noqa: E402
import vm_studio  # noqa: E402
from bie.brain import studio_book  # noqa: E402
from bie.model_gateway.live.messages import strict_ready  # noqa: E402

QUESTION = {"id": "q01", "pillar": "p1", "question": "Ek hi hawa kahin baadh aur kahin sookha kyun laati hai?",
            "hook": "Mumbai bheega, Pune sookha.",
            "points": [{"block_ids": ["p0001-b0002"], "point": "Hawa pahaad par chadhkar barasti hai", "kind": "process"},
                       {"block_ids": ["p0001-b0003"], "point": "Doosri taraf vrishti chhaya", "kind": "cause_effect"}]}
PLAN = {"chapter_title": "Monsoon", "big_question": "Ek hi hawa poore Bharat ko kaise bhigoti hai?",
        "pillars": [{"id": "p1", "title": "Ghat", "line": "Pahaad aur baarish"}], "questions": [QUESTION]}
FILM = {"title": "Ghat", "shots": [
    {"id": "s1", "key": "Hawa chadhti hai, baarish hoti hai", "visual": {"type": "photo", "image_prompt": "x", "svg": ""},
     "sentences": [{"roman": "Dekhiye, yeh Ghat hai.", "pins": [{"label": "Ghat", "x": 40, "y": 30}]},
                   {"roman": "Baadal yahan barasta hai.", "pins": [{"label": "baadal", "x": 55, "y": 20}]}]},
    {"id": "s2", "key": "Peeche sookha", "visual": {"type": "diagram", "image_prompt": "",
                                                   "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>'},
     "sentences": [{"roman": "Doosri taraf hawa sookhi hai.", "pins": []}]}]}


def notes():
    return {"cards": [
        {"label": "Orographic baarish", "text": "Geeli hawa Ghat ki dhalaan par chadhti hai, thandi hoti hai aur barasti hai.",
         "covers": [0]},
        {"label": "Vrishti chhaya", "text": "Pahaad ke peeche utarti hawa garam aur sookhi hoti hai, isliye Pune mein kam baarish.",
         "covers": [1]},
        {"label": "Numbers yaad rakho", "text": "Mahabaleshwar mein 5000 mm se zyada, Pune mein lagbhag 700 mm baarish hoti hai.",
         "covers": [0, 1]}],
        "scene": [{"who": "Asha", "line": "Pune to paas hai, phir wahan baarish kam kyun?"},
                  {"who": "Dev", "line": "Shayad wahan baadal hi nahi aate."},
                  {"who": "Teacher", "line": "Baadal aate hain, par Ghat par baras chuke hote hain. Utarti hawa sookhi hoti hai."}],
        "remember": "Hawa ki taraf wali dhalaan bheegti hai, peeche wali sookhi rehti hai.",
        "check": {"question": "Agar Ghat aadhe unche hote, to Pune ki baarish par kya asar hota?",
                  "choices": ["Zyada baarish hoti", "Koi farq nahi", "Aur kam baarish"], "correct": 0,
                  "explanation": "Kam unchai par hawa kam barasti, to zyada nami Pune tak pahunchti."}}


class FakeClient:
    def __init__(self, answers):
        self.answers, self.calls = list(answers), []

    def chat(self, *, model, messages, schema=None):
        self.calls.append(messages)
        return {"content": json.dumps(self.answers.pop(0), ensure_ascii=False), "usage": {"input_tokens": 10, "output_tokens": 5}}


class BookChecks(unittest.TestCase):
    def test_schema_strict_and_good_notes_pass(self):
        self.assertTrue(strict_ready(studio_book.SCHEMA))
        self.assertEqual(studio_book.problems(notes(), QUESTION), [])

    def test_problems_are_named(self):
        bad = notes()
        bad["cards"] = bad["cards"][:2]
        bad["cards"][1]["covers"] = [0]
        bad["scene"] = [line for line in bad["scene"] if line["who"] != "Teacher"]
        bad["check"]["correct"] = 7
        bad["check"]["choices"][2] = "Zyada baarish hoti"
        bad["remember"] = "NCERT ke hisaab se illustrative line yaad rakho"
        found = " | ".join(studio_book.problems(bad, QUESTION))
        for text in ("2 cards", "points 1", "needs the Teacher", "3 or 4 different choices", "index of a choice",
                     "names the source", "caution line"):
            self.assertIn(text, found)

    def test_problems_go_back_and_are_fixed(self):
        broken = copy.deepcopy(notes())
        broken["scene"] = broken["scene"][:1]
        client = FakeClient([broken, notes()])
        record = studio_book.write(client, "fake", QUESTION, course="Class 9 Geography")
        self.assertEqual(record["problems"], [])
        self.assertIn("scene has 1 lines", client.calls[1][-1]["content"])

    def test_film_figures(self):
        figures = studio_book.film_figures(FILM, {"s1": "data:image/webp;base64,AAAA"})
        self.assertEqual([p["t"] for p in figures["photo"]["pins"]], ["Ghat", "baadal"])
        self.assertEqual(figures["photo"]["caption"], "Hawa chadhti hai, baarish hoti hai")
        self.assertIn("viewBox", figures["diagram"]["svg"])
        self.assertEqual(figures["keys"], ["Hawa chadhti hai, baarish hoti hai", "Peeche sookha"])


class BookRun(unittest.TestCase):
    def test_book_stage_writes_the_living_book(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            films = Path(folder) / "films_run"
            (films / "films" / "img").mkdir(parents=True)
            (films / "questions.json").write_text(json.dumps(PLAN, ensure_ascii=False), encoding="utf-8")
            (films / "films" / "q01.json").write_text(json.dumps({"film": FILM, "images": {"s1": "q01-s1.png"}}),
                                                      encoding="utf-8")
            buffer = io.BytesIO()
            Image.new("RGB", (64, 36), (40, 120, 60)).save(buffer, "PNG")
            (films / "films" / "img" / "q01-s1.png").write_bytes(buffer.getvalue())
            client = FakeClient([notes()])
            args = SimpleNamespace(stage="book", source="", from_run=str(films), videos="", out=str(Path(folder) / "out"),
                                   pages="", course="Class 9 Geography", language="Hinglish", model="", max_rounds=2)
            summary = vm_studio.run(args, client=client, load=None)
            out = Path(folder) / "out"
            self.assertEqual(summary["status"], "ok", summary.get("error"))
            self.assertIn("Baadal yahan barasta hai.", client.calls[0][1]["content"])
            page = (out / "BOOK.html").read_text(encoding="utf-8")
            self.assertNotIn("/*__BOOK__*/null", page)
            for text in ("films/q01.html", "GAME.html#q01", "data:image/webp;base64,", "Vrishti chhaya"):
                self.assertIn(text, page)
            for name in ("BOOK.md", "book/q01.json", "questions.json", "SUMMARY.json"):
                self.assertTrue((out / name).exists(), name)

    def test_book_job(self):
        job = {"job": "bie.vm-job/1", "id": "studio-b-test", "section": "studio", "stage": "book",
               "from_run": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/x"}
        cmd = codex_vm.argv(codex_vm.validate(dict(job)), Path("/tmp/out"), "python")
        self.assertEqual(cmd[cmd.index("--stage") + 1], "book")
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate({k: v for k, v in job.items() if k != "from_run"})


class Course(unittest.TestCase):
    def test_course_folder_links_film_game_and_notes(self):
        import studio_course
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            for run in ("films", "games", "book"):
                (base / run).mkdir()
                (base / run / "questions.json").write_text(json.dumps(PLAN, ensure_ascii=False), encoding="utf-8")
            (base / "films" / "films").mkdir()
            (base / "films" / "films" / "q01.html").write_text("<html>film</html>", encoding="utf-8")
            (base / "games" / "GAME.html").write_text("<html>game</html>", encoding="utf-8")
            (base / "book" / "BOOK.html").write_text("<html>book</html>", encoding="utf-8")
            made = studio_course.assemble(films=base / "films", games=base / "games", book=base / "book",
                                          out=base / "course", course="Class 9 Geography")
            self.assertEqual(made, {"films": ["q01"], "game": True, "book": True, "questions": 1})
            index = (base / "course" / "index.html").read_text(encoding="utf-8")
            for text in ('href="films/q01.html"', 'href="GAME.html#q01"', 'href="BOOK.html#q01"', "Ek hi hawa poore Bharat"):
                self.assertIn(text, index)
            for name in ("films/q01.html", "GAME.html", "BOOK.html", "questions.json"):
                self.assertTrue((base / "course" / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
