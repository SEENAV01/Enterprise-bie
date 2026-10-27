"""Task 046 Part C addition (Navin, 27 October 2026), the offline Money chapter end to end: the fake maker fills the
real-world slot and speaks the example first, so Sections 1 and 2 pass on the first try and the reports carry Navin's
per-concept table; and check_script catches a term named before its example on the real card. This file needs pypdf and
pypdfium2 (the Task 045 lane); the dependency-free checks are in tests/test_task046c_real_world.py (both lanes).
Test input only, never lesson content."""
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

import test_task045_cards as t045  # noqa: E402
from bie.brain import content_types as ct, lesson, rulebook  # noqa: E402
from bie.brain.understanding import Course  # noqa: E402

ECON = "economics_commerce_management"
TYPES = ct.load()
BOOK = rulebook.load()
COURSE = Course(title="3. Money", subject="Indian Economy", learners="UPSC / State PCS aspirants", exam="UPSC / State PCS",
                language="Hinglish", level="upsc_pcs")


class FakeChain(unittest.TestCase):
    """The offline economics chapter: the fake maker fills the slot and speaks the example first, so Sections 1 and 2 pass
    on the first try, and the reports carry Navin's per-concept table."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        lines = [["Demand-pull inflation is a rise in prices because demand exceeds supply.",
                  "Money is anything accepted as a medium of exchange for goods and services.",
                  "The RBI controls the money supply through the repo rate."],
                 ["Inflation is measured by the consumer price index every month."]]
        self.pdf = Path(self.tmp.name, "money.pdf")
        self.pdf.write_bytes(t045.positioned_text_pdf([[(72, 720 - i * 20, t) for i, t in enumerate(page)] for page in lines]))

    def args(self, out):
        return ["--fake", "--section", "chain", "--source", str(self.pdf), "--out", str(Path(self.tmp.name, out)), "--workers", "1",
                "--course", "title=3. Money;subject=Indian Economy;learners=UPSC / State PCS aspirants;exam=UPSC / State PCS;language=Hinglish",
                "--max-inr", "100000"]

    def read(self, out, name):
        return json.loads(Path(self.tmp.name, out, name).read_text(encoding="utf-8"))

    def test_the_offline_economics_chapter_applies_every_concept_first_and_passes_first_try(self):
        code, _ = t045.run(self.args("econ"))
        self.assertEqual(code, 0)
        summary = self.read("econ", "SUMMARY.json")
        self.assertEqual(summary["status"], "ok")
        chapter = self.read("econ", "chapter_map.json")
        q = chapter["quality"]
        self.assertGreater(q["real_world_needed"], 0)
        self.assertEqual((q["real_world_filled"], q["real_world_ok"]), (q["real_world_needed"], q["real_world_needed"]))
        self.assertTrue(all(p["status"] == "passed" and p["rounds"] == 1 for p in chapter["pages"]))      # first try
        needing = [i for i in chapter["items"].values() if i.get("teachable") and TYPES.needs_real_world(ECON, i["content_type"])]
        self.assertTrue(all(i["unpack"]["real_world_example"]["place"] == "kirana shop" for i in needing))
        others = [i for i in chapter["items"].values() if i.get("teachable") and not TYPES.needs_real_world(ECON, i["content_type"])]
        self.assertTrue(all(i["unpack"]["real_world_example"]["place"] == "" for i in others))
        self.assertIn("## Real-world examples (S1-16", Path(self.tmp.name, "econ", "MAP.md").read_text(encoding="utf-8"))
        self.assertIn("real world (run it first", Path(self.tmp.name, "econ", "PAGES.md").read_text(encoding="utf-8"))
        lesson_ = self.read("econ", "lesson_plan.json")
        lq = lesson_["quality"]
        self.assertGreater(lq["real_world"]["items"], 0)
        self.assertEqual(lq["real_world"]["run_first"], lq["real_world"]["items"])
        self.assertEqual(lq["videos_passed"], lq["videos"])
        self.assertTrue(all(v["rounds"] == 1 for v in lesson_["videos"]))
        script = Path(self.tmp.name, "econ", "SCRIPT.md").read_text(encoding="utf-8")
        self.assertIn("## Real-world examples (S2-08", script)
        topic = next(v for v in lesson_["videos"] if v["kind"] == "topic" and v["real_world"])
        story_beats = [b for b in topic["beats"] if b["purpose"] == "story"]
        self.assertTrue(story_beats and all("₹50" in b["say"] and "12" in b["say"] for b in story_beats))

    def test_check_script_catches_a_term_named_before_its_example_on_the_real_card(self):
        code, _ = t045.run(self.args("econ2"))
        self.assertEqual(code, 0)
        chapter = self.read("econ2", "chapter_map.json")
        lesson_ = self.read("econ2", "lesson_plan.json")
        plan = lesson_["plan"]
        topic = next(v for v in lesson_["videos"] if v["kind"] == "topic" and v["real_world"])
        video = next(v for v in plan["videos"] if v["video_id"] == topic["video_id"])
        naksha = lesson.chapter_naksha(chapter)
        prefix = lesson.script_prefixes(COURSE, BOOK)[0]
        card = lesson.script_card(COURSE, chapter, naksha, plan, video, rulebook=BOOK, prefix=prefix)
        value = {"notes": {}, "title": topic["title"], "parts": topic["parts"],
                 "beats": [{k: b[k] for k in ("beat_id", "part_id", "step", "purpose", "say", "covers_item_ids", "answers", "on_screen", "basis")}
                           for b in topic["beats"]]}
        self.assertEqual([p for p in lesson.check_script(value, chapter, video, "Hinglish", card) if "S2-08" in p], [])
        row = topic["real_world"][0]
        story = next(i for i, b in enumerate(value["beats"]) if b["beat_id"] == row["example_beats"][0])
        term = chapter["items"][row["item_id"]]["unpack"]["terms"][0]["term"]
        explain = value["beats"][story + 1]
        explain["say"] = f"ये सामने क्या दिख रहा है? इसे {term} कहते हैं। " + explain["say"]
        value["beats"][story], value["beats"][story + 1] = explain, value["beats"][story]
        problems = [p for p in lesson.check_script(value, chapter, video, "Hinglish", card) if "S2-08" in p]
        self.assertEqual(len(problems), 1)
        self.assertIn(f"names '{term}' before its real-world example runs", problems[0])


if __name__ == "__main__":
    unittest.main()
