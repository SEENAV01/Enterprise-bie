"""The chapter file and the chapter's teaching naksha (bie/brain/chapter_file.py, bie/brain/studio_naksha.py; Navin,
21 November 2026: "Naksha pehle", the naksha on the book's own headings in two shapes, and "codex ko ek output file do
jisse wo asani se content ko samjh paaye").

A small chapter map (two headings, one with a sub-heading, a summary and an exercise) stands in for Section 1's output.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from bie.brain import chapter_file, studio_film, studio_naksha
from bie.model_gateway.live.messages import strict_ready


def item(page, n, content, *, section, role="teach", zone="body", kind="paragraph", terms=(), teachable=True, blocks=None):
    return {f"p{page:03d}-i{n}": {"item_id": f"i{n}", "page": page, "kind": kind, "role": role, "content": content,
                                  "content_type": "process", "teachable": teachable, "exam_importance": "high",
                                  "exam_note": "asked often", "teach_depth": "normal", "deep_why": "",
                                  "block_ids": blocks if blocks is not None else [f"p{page:04d}-b{n:04d}"],
                                  "prerequisites": ["light is energy"],
                                  "teacher_understanding": [{"depth": 2, "ask": "why", "question": "Why?", "answer": "Because.",
                                                             "basis": "book"}],
                                  "unpack": {"terms": [{"term": t, "plain_meaning": f"{t} ka matlab", "everyday_image": ""}
                                                       for t in terms],
                                             "why_chain": [{"step": "need", "basis": "book"}, {"step": "answer", "basis": "book"}],
                                             "example_or_place": "a leaf in sun", "consequence": "sugar is made",
                                             "visual_verb": "light falls on the leaf", "level_extra": ""},
                                  "ncert_section": section, "zone": zone}}


def chapter():
    items = {}
    items.update(item(1, 1, "Plants make their own food.", section=""))
    items.update(item(1, 2, "11.6 THE ELECTRON TRANSPORT", section="11.6", role="heading", kind="heading", teachable=False))
    items.update(item(1, 3, "Electrons move from PS II to PS I.", section="11.6", terms=("PS II",)))
    items.update(item(1, 4, "Let us see how this happens.", section="11.6", role="reader_talk"))
    items.update(item(2, 1, "Water is split to replace the electrons.", section="11.6.1", terms=("PS II", "lumen")))
    items.update(item(2, 2, "Where are the protons released?", section="11.6.1", role="in_text_question"))
    items.update(item(2, 3, "Light reactions make ATP and NADPH.", section="11.6.1", role="summary", zone="summary"))
    items.update(item(2, 4, "1. Explain the Z scheme.", section="11.6.1", role="exercise", zone="exercise"))
    items.update(item(2, 5, "Z scheme figure", section="11.6.1", kind="diagram", blocks=[]))
    items.update(item(2, 6, "Photosystem II", section="11.6.1", kind="diagram_label", blocks=[]))
    items["p002-i6"]["parent_item_id"] = "i5"
    return {"course": {"title": "11. Photosynthesis", "subject": "Biology", "learners": "Class 11", "exam": "NEET",
                       "language": "Hinglish"}, "level": "neet_11_12", "items": items,
            "ncert_sections": [{"block_id": "p0001-b0002", "page": 1, "number": "11.6", "title": "THE ELECTRON TRANSPORT",
                                "level": 1, "zone": "body"},
                               {"block_id": "p0002-b0000", "page": 2, "number": "11.6.1", "title": "Splitting of Water",
                                "level": 2, "zone": "body"},
                               {"block_id": "p0002-b0003", "page": 2, "number": "", "title": "Summary", "level": 0,
                                "zone": "summary"}],
            "map": {"chapter_title": "Photosynthesis in Higher Plants", "chapter_summary": "Plants make food in light.",
                    "concepts": [{"concept_id": "c01", "name": "Electron transport", "content_type": "process",
                                  "core_explanation": "Electrons flow downhill.", "item_ids": ["p001-i3"]}],
                    "relations": [], "prerequisites_to_teach": [], "exam_focus": [], "teaching_order": ["c01"]}}


OPENINGS = {"01": "a thali of rice and dal on a kitchen table", "02": "the thylakoid membrane with its two photosystems",
            "03": "a water molecule breaking apart beside the membrane", "04": "protons crowding inside the lumen"}


def film(fid, section, teaches, *, recalls=(), builds_on=(), analogy="", opening="", reuse=""):
    return {"id": fid, "section": section, "title": f"Film {fid}", "question": "Kyun?", "teaches": list(teaches),
            "recalls": list(recalls), "builds_on": list(builds_on), "prerequisite": "", "opens_with": "Ek sawaal se",
            "story": ["pehle yeh", "phir woh"], "analogy": {"for": "flow", "picture": analogy, "why_it_fits": "fits"},
            "examples": ["a leaf"], "real_world": ["greenhouse"], "terms": ["PS II"], "outside_book": [],
            "saman": [{"id": "s1", "shows": opening or OPENINGS[fid[1:]], "kind": "cutaway",
                       "for_items": list(teaches[:1]), "why": "shows it", "reuse_of": reuse}],
            "minutes": 4}


def good(shape):
    p = shape.lower()
    films = [film(f"{p}01", "", ["p001-i1"], analogy="a kitchen"),
             film(f"{p}02", "11.6", ["p001-i3", "p001-i4"], builds_on=[f"{p}01"], analogy="water down a hill"),
             film(f"{p}03", "11.6.1", ["p002-i1", "p002-i2", "p002-i5"], recalls=["p001-i3"], builds_on=[f"{p}02"])]
    return {"shape": shape, "chapter_flow": "food, then electrons, then water", "films": films,
            "practice": [{"item": "p002-i4", "films": [f"{p}02", f"{p}03"]}], "recap": [{"item": "p002-i3", "film": f"{p}03"}]}


class ChapterFile(unittest.TestCase):
    def test_the_file_keeps_the_books_sections_and_order(self):
        data = chapter_file.build(chapter())
        self.assertEqual([(s["number"], s["zone"]) for s in data["sections"]],
                         [("", "body"), ("11.6", "body"), ("11.6.1", "body"), ("", "summary"), ("", "exercise")])
        water = data["sections"][2]["items"]
        self.assertEqual([r["id"] for r in water], ["p002-i1", "p002-i2", "p002-i5"])      # the label is folded in
        self.assertEqual(water[2]["parts"][0]["content"], "Photosystem II")
        firsts = {t["term"]: t["first_here"] for r in water for t in r["terms"]}
        self.assertEqual(firsts, {"PS II": False, "lumen": True})          # PS II was opened in 11.6

    def test_the_markdown_marks_first_terms_and_names_every_item(self):
        text = chapter_file.markdown(chapter())
        self.assertIn("## 11.6.1 Splitting of Water", text)
        self.assertIn("★ lumen = lumen ka matlab", text)
        self.assertNotIn("★ PS II = PS II ka matlab\n  why: need → answer\n  leads to: sugar is made\n  example: a leaf in sun\n"
                         "  show: light falls on the leaf\n  exam: asked often\n- [p002-i2", text)
        for iid in ("p001-i1", "p001-i3", "p002-i1", "p002-i3", "p002-i4"):
            self.assertIn(f"[{iid} ·", text)

    def test_the_page_for_navin_is_one_html_page(self):
        page = chapter_file.html(chapter())
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("Kitaab ke hisse, kram se", page)
        self.assertIn("kitaab ka sawaal", page)
        self.assertIn("review page", page)


class Naksha(unittest.TestCase):
    def test_schema_is_strict_ready(self):
        self.assertTrue(strict_ready(studio_naksha.SCHEMA))

    def test_a_good_naksha_of_either_shape_passes(self):
        for shape in studio_naksha.SHAPES:
            self.assertEqual(studio_naksha.problems(good(shape), chapter(), shape), [], shape)

    def test_coverage_is_line_by_line_once(self):
        answer = good("A")
        answer["films"][2]["teaches"] = ["p002-i1", "p001-i3"]
        found = " | ".join(studio_naksha.problems(answer, chapter(), "A"))
        self.assertIn("p001-i3 is taught twice", found)
        self.assertIn("items are in no film's teaches: p002-i2", found)
        self.assertIn("belongs to section '11.6'", found)

    def test_exercises_and_summary_are_not_taught_as_lines(self):
        answer = good("B")
        answer["films"][2]["teaches"].append("p002-i4")
        answer["practice"], answer["recap"] = [], []
        found = " | ".join(studio_naksha.problems(answer, chapter(), "B"))
        self.assertIn("p002-i4 is a exercise item: put it in practice", found)
        self.assertIn("1 exercise items are in no practice row", found)
        self.assertIn("1 summary items are in no recap row", found)

    def test_progression_recalls_only_what_was_taught_before(self):
        answer = good("A")
        answer["films"][1]["recalls"] = ["p002-i1"]
        answer["films"][1]["builds_on"] = ["a03"]
        found = " | ".join(studio_naksha.problems(answer, chapter(), "A"))
        self.assertIn("a02: recalls 'p002-i1', which no earlier film teaches", found)
        self.assertIn("a02: builds_on 'a03', which is not an earlier film", found)

    def test_the_books_order_is_kept(self):
        answer = good("A")
        answer["films"][1], answer["films"][2] = answer["films"][2], answer["films"][1]
        answer["films"][1]["id"], answer["films"][2]["id"] = "a02", "a03"
        found = " | ".join(studio_naksha.problems(answer, chapter(), "A"))
        self.assertIn("follow the book's order", found)

    def test_an_analogy_and_an_opening_picture_are_used_once(self):
        answer = good("A")
        answer["films"][2]["analogy"]["picture"] = "water down a hill"
        answer["films"][2]["saman"][0]["shows"] = answer["films"][1]["saman"][0]["shows"]
        found = " | ".join(studio_naksha.problems(answer, chapter(), "A"))
        self.assertIn("a03: its analogy ('water down a hill') repeats a02's", found)
        self.assertIn("a03 opens on the same picture as a02", found)
        answer = good("A")
        answer["films"][2]["saman"][0]["reuse_of"] = "a02 s1"
        self.assertIn("a03: its opening picture reuses 'a02 s1'; open on a picture of its own",
                      studio_naksha.problems(answer, chapter(), "A"))

    def test_shape_b_makes_one_film_per_heading(self):
        answer = good("B")
        answer["films"].append(film("b04", "11.6.1", ["p002-i2"], analogy=""))
        answer["films"][2]["teaches"] = ["p002-i1", "p002-i5"]
        found = " | ".join(studio_naksha.problems(answer, chapter(), "B"))
        self.assertIn("b04 and b03 share section '11.6.1'", found)

    def test_the_films_carry_their_naksha_to_the_film_writer(self):
        rows = studio_naksha.questions(chapter(), good("A"))
        self.assertEqual([r["id"] for r in rows], ["a01", "a02", "a03"])
        third = rows[2]
        self.assertEqual([p["block_ids"] for p in third["points"]], [["p0002-b0001"], ["p0002-b0002"], []])
        self.assertEqual([b["id"] for b in third["naksha"]["before"]], ["a01", "a02"])
        self.assertEqual(third["naksha"]["before"][1]["taught"][0], "Electrons move from PS II to PS I.")
        user = studio_film.messages(third, course="NEET", language="Hinglish")[1]["content"]
        self.assertIn("THE CHAPTER'S NAKSHA", user)
        self.assertIn("a02 (Film a02): Electrons move from PS II to PS I.", user)
        self.assertIn("water down a hill", user)          # what the film before it used, so this one does not repeat it
        self.assertIn("(this is the last film)", user)

    def test_the_maker_gets_the_whole_chapter_file_and_the_rules(self):
        convo = studio_naksha.messages(chapter(), "B", course=chapter()["course"])
        self.assertIn("one heading, one film", convo[0]["content"])
        self.assertIn("b01, b02", convo[0]["content"])
        self.assertIn("## 11.6.1 Splitting of Water", convo[1]["content"])


class Stage(unittest.TestCase):
    def test_the_vm_stage_writes_both_shapes_and_the_chapter_file(self):
        import tools.vm_studio as vm_studio

        class Client:
            def __init__(self):
                self.answers = [good("A"), good("B")]

            def chat(self, *, model, messages, schema=None):
                return {"content": json.dumps(self.answers.pop(0)), "usage": {"input_tokens": 10, "output_tokens": 5}}

            def plan_usage(self):
                return None

        with tempfile.TemporaryDirectory() as folder:
            run_dir = Path(folder) / "understand"
            run_dir.mkdir()
            (run_dir / "chapter_map.json").write_text(json.dumps(chapter()), encoding="utf-8")
            args = SimpleNamespace(stage="naksha", source="", from_run=str(run_dir), videos="", out=str(Path(folder) / "out"),
                                   pages="", course="", language="Hinglish", model="", max_rounds=2, pyqs="")
            summary = vm_studio.run(args, client=Client(), load=None)
            out = Path(folder) / "out"
            self.assertEqual(summary["status"], "ok", summary)
            self.assertEqual({k: v["films"] for k, v in summary["shapes"].items()}, {"A": 3, "B": 3})
            plan = json.loads((out / "questions.json").read_text(encoding="utf-8"))
            self.assertTrue(plan["naksha"])
            self.assertEqual([q["id"] for q in plan["questions"]], ["a01", "a02", "a03", "b01", "b02", "b03"])
            for name in ("CHAPTER.md", "SAMAJH.html", "NAKSHA.md", "naksha.json", "chapter_file.json"):
                self.assertTrue((out / name).exists(), name)

    def test_the_vm_runner_accepts_the_naksha_stage(self):
        import tools.codex_vm as codex_vm
        job = {"job": codex_vm.JOB_SCHEMA, "id": "naksha-test", "section": "studio", "stage": "naksha", "maker": "codex",
               "reviewer": "codex", "from_run": "https://raw.githubusercontent.com/x/y/z"}
        checked = codex_vm.validate(job)
        self.assertIn("--stage", codex_vm.argv(checked, Path("/tmp/out")))
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate(dict(job, from_run=""))


if __name__ == "__main__":
    unittest.main()
