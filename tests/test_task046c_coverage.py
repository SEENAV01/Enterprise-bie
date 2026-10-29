"""Task 046 Part C · work B (Navin, 29 October 2026): "which lines of the book did this video teach", by code.

Offline, on a four-item chapter map and a two-video lesson: the coverage record of a video (assigned lines from the map's
concepts, the beats covering each line, their times from the spec's captions, how they teach, the teacher questions
answered), the uncovered lines and outside-basis beats, the chapter record (every teachable line → its video), the caption
beat ids the canvas writes, and the two page tools (table B on the review page, red when a line is not covered; the chapter
page with its numbers).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import canvas, coverage  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


page_tool = _load("task046c_page")
chapter_tool = _load("task046c_chapter_page")


def _item(iid, page, content, kind="list_point", questions=1, teachable=True):
    return {"item_id": iid, "kind": kind, "content": content, "teachable": teachable, "page": page, "exam_importance": "high",
            "teacher_understanding": [{"depth": 1, "ask": "what", "question": f"q{n}?", "answer": "a", "basis": "book"} for n in range(questions)]}


CHAPTER = {"schema": "bie.brain.understanding/1", "course": {"title": "3. Money", "subject": "Indian Economy", "learners": "UPSC aspirants"},
           "items": {"p001-i1": _item("p001-i1", 1, "3. Money", kind="heading", questions=0, teachable=False),
                     "p001-i3": _item("p001-i3", 1, "Definition: Money is anything accepted as a medium of exchange.", kind="definition", questions=2),
                     "p001-i4": _item("p001-i4", 1, "Money is not just currency notes and coins."),
                     "p002-i2": _item("p002-i2", 2, "Barter needs a double coincidence of wants."),
                     "p002-i5": _item("p002-i5", 2, "Metallic money came later.")},
           "map": {"chapter_title": "3. Money",
                   "concepts": [{"concept_id": "c01", "name": "What money is", "item_ids": ["p001-i3", "p001-i4"], "content_type": "definition"},
                                {"concept_id": "c02", "name": "Barter", "item_ids": ["p002-i2"], "content_type": "cause_effect"},
                                {"concept_id": "c03", "name": "Metal", "item_ids": ["p002-i5"], "content_type": "facts_numbers"}],
                   "prerequisites_to_teach": [{"name": "Purchases and debts", "why_needed": "x", "needed_for": ["c01"], "basis": "outside"}]}}


def _beat(bid, part, purpose, say, covers, basis="mixed", answers=()):
    return {"beat_id": bid, "part_id": part, "step": 1, "purpose": purpose, "say": say, "covers_item_ids": list(covers), "answers": list(answers),
            "on_screen": "", "basis": basis}


LESSON = {"schema": "bie.brain.lesson/1",
          "plan": {"videos": [{"video_id": "v0", "title": "पहले यह जान लो", "kind": "prerequisites", "concept_ids": [], "prerequisites_taught": ["Purchases and debts"]},
                              {"video_id": "v1", "title": "Money क्या है?", "kind": "topic", "concept_ids": ["c01"]},
                              {"video_id": "v2", "title": "Barter", "kind": "topic", "concept_ids": ["c02", "c03"]}]},
          "videos": [{"video_id": "v0", "status": "passed", "card_parts": [{"part_id": "pre1", "type": "none", "item_ids": ["pre1"]}],
                      "beats": [_beat("b1", "pre1", "prerequisite", "उधार क्या है?", ["pre1"], basis="outside")]},
                     {"video_id": "v1", "status": "passed",
                      "card_parts": [{"part_id": "c01.1", "type": "definition", "item_ids": ["p001-i3", "p001-i4"]}],
                      "beats": [_beat("b1", "", "hook", "कीमती चीज़ money है?", [], basis="outside"),
                                _beat("b2", "c01.1", "example", "चाय ₹10 की है।", ["p001-i3"], answers=["p001-i3#q1"]),
                                _beat("b3", "c01.1", "explain", "Money वह है जो payment में लिया जाए।", ["p001-i3", "p001-i4"], basis="book", answers=["p001-i3#q2"]),
                                _beat("b4", "c01.1", "recap", "दोहराव।", ["p001-i4"])]},
                     {"video_id": "v2", "status": "failed",
                      "card_parts": [{"part_id": "c02.1", "type": "cause_effect", "item_ids": ["p002-i2"]}, {"part_id": "c03.1", "type": "facts_numbers", "item_ids": ["p002-i5"]}],
                      "beats": [_beat("b1", "c02.1", "explain", "Barter में दोनों को एक-दूसरे की चीज़ चाहिए।", ["p002-i2"]),
                                _beat("b2", "c02.1", "example", "एक और बात।", ["p009-i9"], basis="outside")]}]}

PLANS = {"v1_s1": {"id": "v1_s1", "beats": [{"beat_id": "b1", "say": "कीमती चीज़ money है?"}]},
         "v1_s2": {"id": "v1_s2", "beats": [{"beat_id": "b2", "say": "चाय ₹10 की है।"}, {"beat_id": "b3", "say": "Money वह है जो payment में लिया जाए।"},
                                            {"beat_id": "b4", "say": "दोहराव।"}]}}
SPEC = {"schema": "bie.render-spec/1", "fps": 30, "width": 1920, "height": 1080, "captions": True,
        "scenes": [{"id": "v1_s1", "duration": 300, "layers": [], "captions": [{"at": 12, "until": 290, "text": "कीमती चीज़ money है?", "beat_id": "b1"}]},
                   {"id": "v1_s2", "duration": 900, "layers": [],
                    "captions": [{"at": 10, "until": 300, "text": "चाय ₹10 की है।", "beat_id": "b2"},
                                 {"at": 300, "until": 600, "text": "Money वह है जो payment में लिया जाए।", "beat_id": "b3"},
                                 {"at": 600, "until": 870, "text": "दोहराव।", "beat_id": "b4"}]}]}


class VideoCoverage(unittest.TestCase):
    def test_the_assigned_lines_come_from_the_maps_concepts_and_each_shows_its_beats_times_and_how(self):
        cov = coverage.video_coverage(CHAPTER, LESSON, "v1", spec=SPEC, plans=PLANS)
        self.assertEqual(cov["schema"], coverage.SCHEMA)
        self.assertEqual([r["item_id"] for r in cov["rows"]], ["p001-i3", "p001-i4"])
        self.assertEqual((cov["assigned"], cov["covered"], cov["beats"], cov["beats_timed"]), (2, 2, 4, 4))
        i3 = cov["rows"][0]
        self.assertEqual([b["beat_id"] for b in i3["beats"]], ["b2", "b3"])
        self.assertEqual(i3["beats"][0]["time"], "0:10–0:20")                   # scene 1 (300 frames) before it: 310/30 → 320/30... held caption
        self.assertEqual(i3["beats"][1]["time"], "0:20–0:30")
        self.assertEqual(i3["how"], "example se, samjhaya")
        self.assertEqual((i3["questions_answered"], i3["questions"]), (2, 2))
        self.assertEqual(cov["rows"][1]["how"], "samjhaya, dohraav")
        self.assertEqual(cov["uncovered"], [])
        self.assertEqual([b["beat_id"] for b in cov["outside_beats"]], ["b1"])
        self.assertEqual(cov["outside_beats"][0]["time"], "0:00–0:10")
        self.assertEqual(cov["beats_beyond_scope"], [])
        self.assertEqual(cov["basis"], {"outside": 1, "mixed": 2, "book": 1})

    def test_an_assigned_line_no_beat_covers_is_listed_and_a_beat_beyond_the_scope_too(self):
        cov = coverage.video_coverage(CHAPTER, LESSON, "v2")
        self.assertEqual([r["item_id"] for r in cov["rows"]], ["p002-i2", "p002-i5"])
        self.assertEqual([u["item_id"] for u in cov["uncovered"]], ["p002-i5"])
        self.assertFalse(cov["rows"][1]["covered"])
        self.assertEqual(cov["rows"][1]["beats"], [])
        self.assertEqual([(b["beat_id"], b["covers"]) for b in cov["beats_beyond_scope"]], [("b2", ["p009-i9"])])
        self.assertEqual(cov["rows"][0]["beats"][0]["time"], "")             # no spec: no times, no crash

    def test_the_prerequisite_video_is_measured_against_the_maps_prerequisites_by_name(self):
        cov = coverage.video_coverage(CHAPTER, LESSON, "v0")
        self.assertEqual([(r["item_id"], r["content"]) for r in cov["rows"]], [("pre1", "Purchases and debts")])
        self.assertEqual(cov["rows"][0]["how"], "pehle yeh jaan lo")
        self.assertEqual(cov["uncovered"], [])

    def test_a_script_resumed_without_a_plan_entry_falls_back_to_its_card_parts(self):
        lesson = {"videos": LESSON["videos"]}                                  # no plan at all
        cov = coverage.video_coverage(CHAPTER, lesson, "v1")
        self.assertEqual([r["item_id"] for r in cov["rows"]], ["p001-i3", "p001-i4"])
        self.assertEqual(cov["rows"][0]["content"], CHAPTER["items"]["p001-i3"]["content"])


class BeatTimes(unittest.TestCase):
    def test_captions_carry_their_beat_id_and_times_run_across_the_joined_scenes(self):
        tl = {"s": {"fps": 30, "duration": 300, "beats": {"b1": (0, 100), "b2": (120, 150)}}}
        caps = canvas.captions_of(tl, "s", [{"beat_id": "b1", "say": "एक"}, {"beat_id": "b2", "say": "दो"}])
        self.assertEqual([c["beat_id"] for c in caps], ["b1", "b2"])
        self.assertEqual(coverage.beat_times(SPEC)["b3"], {"scene": "v1_s2", "start_s": 20.0, "end_s": 30.0})

    def test_an_older_spec_without_beat_ids_is_matched_to_the_plans_beats_in_order_else_by_text(self):
        old = json.loads(json.dumps(SPEC))
        for scene in old["scenes"]:
            for cap in scene["captions"]:
                cap.pop("beat_id")
        self.assertEqual(coverage.beat_times(old, PLANS)["b4"], {"scene": "v1_s2", "start_s": 30.0, "end_s": 39.0})
        self.assertEqual(coverage.beat_times(old), {})                       # neither ids nor plans: nothing to match
        plans = {"v1_s2": {"id": "v1_s2", "beats": PLANS["v1_s2"]["beats"] + [{"beat_id": "b9", "say": "extra"}]}}   # counts differ: by text
        self.assertEqual(coverage.beat_times(old, plans)["b2"]["start_s"], 10.3)
        self.assertNotIn("b9", coverage.beat_times(old, plans))


class ChapterCoverage(unittest.TestCase):
    def test_every_teachable_line_names_its_video_and_the_unassigned_lines_are_listed(self):
        rec = coverage.chapter_coverage(CHAPTER, LESSON)
        self.assertEqual(rec["schema"], coverage.CHAPTER_SCHEMA)
        self.assertEqual((rec["teachable"], rec["assigned"], rec["taught_by_a_passed_video"]), (4, 4, 2))
        rows = {r["item_id"]: r for r in rec["rows"]}
        self.assertEqual(rows["p001-i3"]["videos"], [{"video_id": "v1", "status": "passed", "covered": True}])
        self.assertEqual(rows["p002-i5"]["videos"], [{"video_id": "v2", "status": "failed", "covered": False}])
        self.assertEqual(rec["unassigned"], [])
        v2 = next(v for v in rec["videos"] if v["video_id"] == "v2")
        self.assertEqual((v2["assigned"], v2["covered"], v2["uncovered"], v2["status"]), (2, 1, ["p002-i5"], "failed"))
        chapter = json.loads(json.dumps(CHAPTER))
        chapter["items"]["p003-i1"] = _item("p003-i1", 3, "An orphan line.")
        rec = coverage.chapter_coverage(chapter, LESSON)
        self.assertEqual([u["item_id"] for u in rec["unassigned"]], ["p003-i1"])
        self.assertEqual(rec["rows"][-1]["item_id"], "p003-i1")              # pages in order


class Pages(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="t046c-cov-"))
        self.canvas = self.tmp / "canvas"
        (self.canvas / "plans").mkdir(parents=True)
        (self.canvas / "video_specs").mkdir()
        canvas_json = {"schema": "bie.brain.canvas/1", "course": CHAPTER["course"], "maker_route": "codex", "missing_kits": [], "quality": {},
                       "videos": [{"video_id": "v1", "title": "Money क्या है?", "parts": [{"id": "v1_s1", "part_id": "", "mode": "B", "status": "passed", "seconds": 10.0},
                                                                                        {"id": "v1_s2", "part_id": "c01.1", "mode": "C", "place": "shop", "status": "passed", "seconds": 30.0}],
                                   "parts_passed": 2, "first_try_passes": 2, "rounds": 2, "modes": {"B": 1, "C": 1}, "seconds": 40.0}]}
        (self.canvas / "canvas.json").write_text(json.dumps(canvas_json, ensure_ascii=False), encoding="utf-8")
        (self.canvas / "video_specs" / "v1.json").write_text(json.dumps(SPEC, ensure_ascii=False), encoding="utf-8")
        for pid, plan in PLANS.items():
            (self.canvas / "plans" / f"{pid}.plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        self.render = self.tmp / "render"
        self.render.mkdir()
        (self.render / "summary.json").write_text(json.dumps({"schema": "bie.render-spec.summary/1", "cost": {}, "join": {}}), encoding="utf-8")
        self.lesson = self.tmp / "lesson"
        self.lesson.mkdir()
        (self.lesson / "lesson_plan.json").write_text(json.dumps(LESSON, ensure_ascii=False), encoding="utf-8")
        self.map = self.tmp / "chapter_map.json"
        self.map.write_text(json.dumps(CHAPTER, ensure_ascii=False), encoding="utf-8")

    def test_the_review_page_carries_table_b_and_writes_the_coverage_record(self):
        out = self.tmp / "v1.html"
        page_tool.main(["--canvas", str(self.canvas), "--render", str(self.render), "--html", str(out), "--lesson", str(self.lesson),
                        "--chapter-map", str(self.map)])
        html = out.read_text(encoding="utf-8")
        self.assertIn("Kitaab ki kaun-si lines is video ne padhaayi", html)
        self.assertIn("2 of 2 assigned lines padhaayi gayi, 4 beats mein", html)
        self.assertIn("Cover na hui line: 0 ✅", html)
        self.assertIn("0:10–0:20", html)                                      # b2's time from the captions
        self.assertIn("example se, samjhaya", html)
        self.assertIn("Beats jinka basis kitaab ke bahar hai (outside): 1 of 4", html)
        record = json.loads(out.with_suffix(".coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(record["v1"]["covered"], 2)
        self.assertNotIn('class="bad-box"', html)

    def test_an_uncovered_line_is_shown_in_red(self):
        lesson = json.loads(json.dumps(LESSON))
        lesson["videos"][1]["beats"] = [b for b in lesson["videos"][1]["beats"] if "p001-i4" not in b["covers_item_ids"]]
        (self.lesson / "lesson_plan.json").write_text(json.dumps(lesson, ensure_ascii=False), encoding="utf-8")
        html = page_tool.build(self.canvas, self.render, lesson_dir=self.lesson, chapter_map=self.map)
        self.assertIn("Cover na hui lines: 1 ❌", html)
        self.assertIn('class="bad-box"', html)
        self.assertIn("Money is not just currency notes and coins.", html)
        self.assertIn("koi beat nahi ❌", html)

    def test_without_the_lesson_or_the_map_the_page_has_no_table_b(self):
        html = page_tool.build(self.canvas, self.render, lesson_dir=self.lesson)
        self.assertNotIn("table B", html)

    def test_the_chapter_page_names_every_line_its_video_and_the_numbers(self):
        out = self.tmp / "chapter.html"
        chapter_tool.main(["--chapter-map", str(self.map), "--lesson", str(self.lesson), "--html", str(out), "--page", "v1=https://example.test/v1"])
        html = out.read_text(encoding="utf-8")
        self.assertIn("kitaab ki har line kis video mein padhaayi gayi", html)
        self.assertIn('<p class="big">4</p>', html)                           # teachable
        self.assertIn('<p class="big ok">2</p>', html)                        # taught by a passed video
        self.assertIn("v2, v4, v10, v11, v12".split(", ")[0], html)
        self.assertIn('href="https://example.test/v1"', html)
        self.assertIn("Barter needs a double coincidence of wants.", html)
        self.assertIn("❌ failed", html)
        self.assertIn("beat nahi", html)                                      # p002-i5 in the failed v2 has no beat
        record = json.loads(out.with_suffix(".coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(record["teachable"], 4)


if __name__ == "__main__":
    unittest.main()
