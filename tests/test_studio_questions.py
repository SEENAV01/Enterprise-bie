"""The film-first course studio, stage 1 (Navin, 18 November 2026): the chapter's student questions, checked by code,
and the VM job section ``studio`` that runs it. Offline: a fake maker client and fake pages."""
from __future__ import annotations

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
from bie.brain import studio  # noqa: E402
from bie.brain.pages import Block, Page  # noqa: E402
from bie.model_gateway.live.messages import strict_ready  # noqa: E402

LONG = "Moist south-west winds rise over the Western Ghats, cool, and drop heavy rain on the windward slopes. "


def pages():
    return [Page(1, (Block("p0001-b0001", "The Monsoon", (0, 0, 1, 0.1)),
                     Block("p0001-b0002", LONG, (0, 0.1, 1, 0.3)),
                     Block("p0001-b0003", "Land heats faster than the sea, so a low pressure area forms over the north-west in May.",
                           (0, 0.3, 1, 0.5)))),
            Page(2, (Block("p0002-b0001", "The winds cross the equator and turn to the right, becoming south-westerly winds.",
                           (0, 0, 1, 0.2)),
                     Block("p0002-b0002", "The monsoon reaches Kerala around the first of June and covers India by early July.",
                           (0, 0.2, 1, 0.4))))]


def question(qid, pillar, ids, kind="process"):
    return {"id": qid, "pillar": pillar, "question": "Ek hi hawa kahin baadh aur kahin sookha kyun laati hai?",
            "hook": "Mumbai mein baadh hai, aur Pune mein dhoop. Aisa kyun?",
            "points": [{"block_ids": ids, "point": "Hawa pahaad par chadhkar thandi hoti hai aur barasti hai.", "kind": kind}],
            "film": {"length": "long", "showing_moment": "Hawa ka gola Ghat par chadhta hai aur baarish shuru hoti hai"},
            "game_stage": {"mechanic": "drag_to_target", "idea": "Gole ko Ghat par kheencho, baadal ban kar baarish ho"}}


def answer(all_covered=True):
    qs = [question("q01", "p1", ["p0001-b0003"]), question("q02", "p2", ["p0002-b0001"]),
          question("q03", "p2", ["p0001-b0002"]), question("q04", "p3", ["p0002-b0002"], "timeline")]
    if not all_covered:
        qs[3]["points"][0]["block_ids"] = ["p0001-b0002"]
    return {"chapter_title": "Monsoon", "big_question": "Ek hi hawa poore Bharat ko kaise bhigoti hai?",
            "pillars": [{"id": "p1", "title": "Garmi", "line": "Zameen tapti hai"},
                        {"id": "p2", "title": "Safar", "line": "Hawa samudra se aati hai"},
                        {"id": "p3", "title": "Calendar", "line": "Monsoon kab aata hai"}],
            "questions": qs}


class FakeClient:
    def __init__(self, answers):
        self.answers, self.calls = list(answers), []

    def chat(self, *, model, messages, schema=None):
        self.calls.append(messages)
        return {"content": json.dumps(self.answers.pop(0), ensure_ascii=False), "usage": {"input_tokens": 100, "output_tokens": 50}}

    def plan_usage(self):
        return {"codex.primary.usedPercent": 10}


class StudioQuestions(unittest.TestCase):
    def test_schema_is_strict_ready(self):
        self.assertTrue(strict_ready(studio.SCHEMA))

    def test_teachable_skips_short_headings(self):
        self.assertNotIn("p0001-b0001", studio.teachable(pages()))
        self.assertEqual(len(studio.teachable(pages())), 4)

    def test_good_answer_passes_with_full_coverage(self):
        record = studio.plan(FakeClient([answer()]), "fake", pages())
        self.assertEqual(record["problems"], [])
        self.assertEqual(len(record["rounds"]), 1)
        self.assertEqual(record["coverage"]["percent"], 100.0)

    def test_missing_block_goes_back_and_is_fixed(self):
        client = FakeClient([answer(all_covered=False), answer()])
        record = studio.plan(client, "fake", pages())
        self.assertEqual(len(record["rounds"]), 2)
        self.assertIn("p0002-b0002", record["rounds"][0]["problems"][0])
        self.assertIn("p0002-b0002", client.calls[1][-1]["content"])
        self.assertEqual(record["problems"], [])

    def test_problems_name_ids_pillars_and_source_words(self):
        bad = answer()
        bad["pillars"] = bad["pillars"][:2]
        bad["questions"][0]["points"][0]["block_ids"] = ["p9999-b0001"]
        bad["questions"][1]["question"] = "NCERT ke hisaab se hawa kyun mudti hai?"
        found = " | ".join(studio.problems(bad, studio.all_blocks(pages()), list(studio.teachable(pages()))))
        self.assertIn("2 pillars", found)
        self.assertIn("unknown block ids p9999-b0001", found)
        self.assertIn("name the source", found)

    def test_markdown_lists_questions_for_navin(self):
        record = studio.plan(FakeClient([answer()]), "fake", pages())
        text = studio.markdown(record)
        self.assertIn("Sawaal-list", text)
        self.assertIn("Mumbai mein baadh", text)
        self.assertIn("4 / 4", text)


class StudioRun(unittest.TestCase):
    def test_run_writes_files_and_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            pdf = Path(folder) / "c.pdf"
            pdf.write_bytes(b"%PDF-1.4 fake")
            args = SimpleNamespace(stage="questions", source=str(pdf), out=str(Path(folder) / "out"), pages="", course="Class 9",
                                   language="Hinglish", model="", max_rounds=3)
            summary = vm_studio.run(args, client=FakeClient([answer()]),
                                    load=lambda data, spec, with_images=False: ("abc", 2, pages()))
            out = Path(folder) / "out"
            self.assertEqual(summary["status"], "ok")
            self.assertEqual(summary["questions"], 4)
            for name in ("questions.json", "QUESTIONS.md", "record.json", "SUMMARY.json"):
                self.assertTrue((out / name).exists(), name)

    def test_not_a_pdf_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "c.pdf"
            src.write_bytes(b"hello")
            args = SimpleNamespace(stage="questions", source=str(src), out=str(Path(folder) / "out"), pages="", course="",
                                   language="Hinglish", model="", max_rounds=1)
            summary = vm_studio.run(args, client=FakeClient([]), load=lambda *a, **k: ("x", 0, []))
            self.assertEqual(summary["status"], "failed")
            self.assertIn("not a PDF", summary["error"])


class StudioJob(unittest.TestCase):
    JOB = {"job": "bie.vm-job/1", "id": "studio-q-test", "section": "studio", "stage": "questions",
           "source": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-inputs/chapters/x.pdf",
           "pages": "1-30", "course": "Class 11 Geography", "language": "Hinglish"}

    def test_valid_job_and_command(self):
        job = codex_vm.validate(dict(self.JOB))
        cmd = codex_vm.argv(job, Path("/tmp/out"), "python")
        self.assertIn(str(ROOT / "tools" / "vm_studio.py"), cmd)
        self.assertEqual(cmd[cmd.index("--stage") + 1], "questions")
        self.assertEqual(cmd[cmd.index("--pages") + 1], "1-30")
        self.assertEqual(cmd[cmd.index("--course") + 1], "Class 11 Geography")

    def test_refusals(self):
        for change, word in (({"source": None}, "source"), ({"stage": "films"}, "stage"), ({"stage": "bad stage"}, "stage")):
            job = {k: v for k, v in dict(self.JOB, **change).items() if v is not None}
            with self.assertRaises(codex_vm.JobError) as caught:
                codex_vm.validate(job)
            self.assertIn(word, str(caught.exception))
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate({"job": "bie.vm-job/1", "id": "understand-x", "section": "understand", "stage": "questions",
                               "source": self.JOB["source"]})


if __name__ == "__main__":
    unittest.main()
