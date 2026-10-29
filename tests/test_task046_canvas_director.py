"""Task 046 Part C, PR 2 · the canvas director: for a canvas subject (economics, polity, history, geography concepts) every
script part becomes one build-up canvas (Navin's B, L2 + L3 touches) by default, a story part with actors in a place
becomes an L3 world (C) when a kit exists for the place, else a canvas plus a missing-kit line; the maker writes the plan
on the director card through the SectionRunner, code places, times and checks it, a refused plan goes back with the
exact code error (no reviewer round for layout), and first-try passes and rounds are counted per part.

Offline: the fake maker (bie/brain/fake.py) answers every plan; no network, no keys, no money.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import canvas, canvas_director as cd, fake, rulebook  # noqa: E402
from bie.brain.runner import SectionRunner  # noqa: E402
from bie.brain.understanding import Course  # noqa: E402
from bie.brain.video import world  # noqa: E402
from bie.model_gateway.live.gateway import LiveGateway  # noqa: E402
from bie.model_gateway.gpt_adapter import GPTAdapter  # noqa: E402
from bie.model_gateway.gemini_adapter import GeminiAdapter  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "task046c"
ECON = Course(title="Inflation", subject="Economics", learners="UPSC aspirants", exam="UPSC", language="Hinglish", level="upsc_pcs")
BIO = Course(title="Tissues", subject="Biology", learners="class 11", exam="NEET", language="Hinglish", level="neet_11_12")


def gateway():
    routes = {"openai": GPTAdapter(fake.BrainFakeClient("openai"), "fake-o"), "google": GeminiAdapter(fake.BrainFakeClient("google"), "fake-g")}
    return LiveGateway(routes, sleep=lambda s: None)


def runner(folder):
    return SectionRunner(gateway(), maker="openai", reviewer="google", rulebook=rulebook.load(), records_dir=Path(folder, "records"))


def beats_of(name: str, part: str, *, covers=("i1",)):
    plan = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return [{"beat_id": b["beat_id"], "part_id": part, "step": 1, "purpose": "explain", "say": b["say"], "covers_item_ids": list(covers),
             "answers": [], "on_screen": "", "basis": "book"} for b in plan["beats"]]


def econ_lesson():
    """A tiny economy lesson (test input, not lesson content): part p1 is the shop story, part p2 the Phillips curve."""
    shop = beats_of("demand_pull_touches.plan.json", "p1")
    curve = beats_of("phillips.plan.json", "p2", covers=("i2",))
    for n, b in enumerate(curve):
        b["beat_id"] = f"c{n + 1}"
    chapter = {"schema": "bie.brain.chapter-map/2", "source_sha256": "b" * 64, "pages": [{"page": 1}], "map_status": "passed",
               "course": {"title": "Inflation", "subject": "Economics", "learners": "UPSC aspirants", "exam": "UPSC", "language": "Hinglish",
                          "level": "upsc_pcs"}, "level": "upsc_pcs",
               "items": {"i1": {"item_id": "i1", "kind": "paragraph", "content": "Demand-pull inflation: demand exceeds supply.",
                                "content_type": "cause_effect", "teachable": True, "teacher_understanding": []},
                         "i2": {"item_id": "i2", "kind": "paragraph", "content": "Phillips curve: inflation against unemployment.",
                                "content_type": "cause_effect", "teachable": True, "teacher_understanding": []}},
               "map": {"concepts": [{"concept_id": "c1", "name": "Inflation", "item_ids": ["i1", "i2"]}]}}
    parts = sorted({b["part_id"] for b in shop + curve if b.get("part_id")})
    lesson = {"schema": "bie.brain.lesson/3", "course": chapter["course"], "rulebook_version": "test", "plan_status": "passed",
              "plan": {"videos": [{"video_id": "v1", "title": "Demand-pull and the Phillips curve", "concept_ids": ["c1"], "kind": "topic", "goal": "inflation"}]},
              "videos": [{"video_id": "v1", "title": "Demand-pull and the Phillips curve", "status": "passed", "kind": "topic",
                          "card_parts": [{"part_id": p, "type": "cause_effect", "item_ids": ["i1", "i2"]} for p in parts],
                          "beats": [dict(b, source=b.get("source", "")) for b in shop + curve]}],
              "quality": {}}
    return chapter, lesson


class Mode(unittest.TestCase):
    def test_a_canvas_subject_defaults_to_b_and_a_story_in_a_place_with_a_kit_goes_to_c(self):
        shop = beats_of("demand_pull_touches.plan.json", "p1")
        self.assertEqual(cd.mode_of(ECON, shop), {"mode": "C", "place": "shop", "kit": "shop", "missing": "", "story": False})
        gdp = beats_of("real_gdp.plan.json", "p2")
        self.assertEqual(cd.mode_of(ECON, gdp), {"mode": "B", "place": "", "kit": "", "missing": "", "story": False})
        bank = [{"beat_id": "b1", "say": "बैंक से कर्ज़ लेने वाले borrowers को ब्याज देना पड़ता है।"}]
        self.assertEqual(cd.mode_of(ECON, bank), {"mode": "C", "place": "bank", "kit": "bank", "missing": "", "story": False})   # PR 3
        factory = [{"beat_id": "b1", "say": "फैक्ट्री में मज़दूर दिन में सौ जूते बनाते हैं।"}]
        self.assertEqual(cd.mode_of(ECON, factory), {"mode": "B", "place": "factory", "kit": "", "missing": "world kit for a factory", "story": False})
        self.assertEqual(cd.mode_of(BIO, shop)["mode"], "")
        for subject, fits in (("Indian Economy", True), ("Polity and Constitution", True), ("Commerce", True), ("Physics", False), ("History", True)):
            self.assertEqual(cd.profile_fits(Course(title="x", subject=subject, learners="", exam="", language="Hinglish")), fits, subject)

    def test_places_are_found_by_their_words_and_the_busiest_place_wins(self):
        self.assertEqual(world.place_of("factory के workers को वेतन मिला, फिर वे दुकान गए"), "factory")
        self.assertEqual(world.place_of("Ships at the port carry exports"), "port")
        self.assertEqual(world.place_of("किसान खेत में फसल काटता है"), "farm")
        self.assertEqual(world.kit_for("किसान खेत में फसल काटता है"), "")


class Plans(unittest.TestCase):
    def setUp(self):
        self.stub = {"id": "v1_s1", "part_id": "p1", "theme": "paper", "grid": [12, 8], "touches": True,
                     "beats": [{"beat_id": b["beat_id"], "say": b["say"]} for b in beats_of("demand_pull_touches.plan.json", "p1")]}
        self.user = "The part (JSON):\n" + json.dumps({"part": {"id": "v1_s1", "part_id": "p1"}, "beats": self.stub["beats"]}, ensure_ascii=False)

    def test_the_strict_answer_becomes_a_kit_plan_without_unset_fields(self):
        value = fake.canvas_answer(self.user)
        self.assertEqual(set(value), {"notes", "nodes", "camera", "focus", "graph_used", "graph"})
        self.assertTrue(all(set(n) == set(cd.NODE["properties"]) for n in value["nodes"]))
        plan = cd.plan_from(self.stub, value)
        self.assertEqual(plan["beats"], self.stub["beats"])
        self.assertTrue(plan["touches"])
        self.assertNotIn("graph", plan)
        tag = plan["nodes"][0]
        self.assertEqual(tag["cue"], ["b1", "", 0.0])
        self.assertEqual(set(tag), {"id", "kind", "cell", "cue", "style", "text"})
        scene, report = canvas.compile_plan(plan)
        self.assertEqual(report["problems"], [])
        self.assertEqual((report["mode"], report["level"]), ("B", "L2 + touches"))

    def test_a_refused_plan_carries_the_exact_code_error(self):
        value = fake.canvas_answer(self.user)
        bad = json.loads(json.dumps(value))
        bad["nodes"][1]["cue"] = ["b1", "nowhere"]
        self.assertEqual(cd.check_plan(self.stub, bad, "B"), ["cue word 'nowhere' is not in beat b1: " + repr(self.stub["beats"][0]["say"][:80])])
        bad = json.loads(json.dumps(value))
        bad["nodes"].append(dict(bad["nodes"][1], id="ic", kind="icon", icon="tw:bank", cell=[6, 7, 2, 1]))
        problems = cd.check_plan(self.stub, bad, "B")
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("icon 'tw:bank' is not in the icon index; nearest: tw:1f3e6 (bank)"), problems)
        bad = json.loads(json.dumps(value))
        bad["nodes"][2]["cell"] = bad["nodes"][1]["cell"]
        self.assertTrue(any("share grid cells" in p for p in cd.check_plan(self.stub, bad, "B")))
        self.assertEqual(cd.check_plan(self.stub, {"nodes": [{"id": "x", "kind": "text", "cell": "no"}]}, "B")[0][:11], "plan shape:")
        self.assertEqual(cd.check_plan(self.stub, value, "B"), [])

    def test_the_world_answer_becomes_a_world_plan(self):
        value = fake.world_answer(self.user)
        plan = cd.world_from(self.stub, value)
        self.assertEqual([e["kind"] for e in plan["elements"]][:2], ["shop", "lamp"])
        self.assertNotIn("y", plan["elements"][1])
        self.assertEqual(plan["camera"][0]["cue"], ["b1", "", 0.0])
        scene, report = world.compile_world(plan)
        self.assertEqual((report["mode"], report["level"], report["problems"]), ("C", "L3", []))
        bad = json.loads(json.dumps(value))
        bad["camera"][1], bad["camera"][2] = bad["camera"][2], bad["camera"][1]
        self.assertEqual(cd.check_plan(self.stub, bad, "C"), ["camera keys must be in time order"])

    def test_a_long_part_is_split_into_near_equal_canvases(self):
        long = dict(self.stub, beats=[{"beat_id": f"b{n}", "say": f"beat {n} कहता है।"} for n in range(1, 20)])
        pieces = cd.split_stub(long)
        self.assertEqual([p["id"] for p in pieces], ["v1_s1a", "v1_s1b"])
        self.assertEqual([len(p["beats"]) for p in pieces], [10, 9])
        self.assertEqual(cd.split_stub(self.stub), [self.stub])

    def test_the_step_carries_the_card_the_rules_and_the_icon_menu(self):
        step = cd.part_step(ECON, self.stub, [{"item_id": "i1", "content_type": "cause_effect", "content": "x"}],
                            {"mode": "B", "place": "", "kit": "", "missing": ""}, rulebook=rulebook.load(), max_rounds=2)
        self.assertEqual((step.section, step.unit, step.max_rounds), ("canvas", "v1_s1", 2))
        self.assertIsNone(step.review_system)                                   # no reviewer round for layout
        self.assertIn("[CV-01]", step.system)
        self.assertIn("## Element vocabulary", step.system)
        self.assertNotIn("## Examples", step.system)
        self.assertIn("tw:1f3ea · convenience store", step.system)
        self.assertIn('"items": [{"item_id": "i1"', step.user)
        self.assertEqual(step.schema, cd.PLAN_SCHEMA)
        wstep = cd.part_step(ECON, self.stub, [], {"mode": "C", "place": "shop", "kit": "shop", "missing": ""}, rulebook=rulebook.load())
        self.assertEqual(wstep.schema, cd.WORLD_SCHEMA)
        self.assertIn("a shop with buyers on a street", wstep.system)
        self.assertIn("price_tag", wstep.system)


class Run(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_the_run_writes_plans_specs_and_counts_first_try_passes(self):
        chapter, lesson = econ_lesson()
        summary = cd.run_canvas(chapter, lesson, ECON, runner(self.tmp), self.tmp, workers=1)
        q = summary["quality"]
        self.assertEqual((q["parts"], q["parts_passed"], q["first_try_passes"], q["rounds"]), (2, 2, 2, 2))
        self.assertEqual(q["modes"], {"B": 1, "C": 1})
        self.assertEqual(q["missing_kits"], [])
        video = summary["videos"][0]
        self.assertEqual(video["status"], "spec_written")
        self.assertEqual([(p["id"], p["mode"], p["level"]) for p in video["parts"]], [("v1_s1", "C", "L3"), ("v1_s2", "B", "L2 + touches")])
        spec = json.loads(Path(self.tmp, "video_specs", "v1.json").read_text(encoding="utf-8"))
        self.assertEqual([s["layers"][0]["block"] for s in spec["scenes"]], ["world_scene", "canvas_build"])
        self.assertTrue(spec["captions"] and all(s["captions"] for s in spec["scenes"]))
        self.assertTrue(Path(self.tmp, "plans", "v1_s1.plan.json").exists() and Path(self.tmp, "plans", "v1_s2.plan.json").exists())
        page = Path(self.tmp, "CANVAS.md").read_text(encoding="utf-8")
        self.assertIn("2 of 2 parts passed, 2 on the first try (100%)", page)
        self.assertIn("mode C L3", page)
        self.assertIn("· first try", page)
        self.assertEqual(json.loads(Path(self.tmp, "canvas.json").read_text(encoding="utf-8"))["profile_version"], canvas.PROFILE["version"])

    def test_a_refused_first_answer_costs_a_round_and_the_record_keeps_the_exact_error(self):
        chapter, lesson = econ_lesson()
        good = fake.canvas_answer
        calls = []

        def flaky(user_text):
            value = good(user_text)
            calls.append(1)
            if len(calls) == 1:
                value["nodes"][1]["cue"] = ["c1", "nowhere"]
            return value

        with mock.patch.object(fake, "canvas_answer", flaky):
            summary = cd.run_canvas(chapter, lesson, ECON, runner(self.tmp), self.tmp, workers=1)
        q = summary["quality"]
        self.assertEqual((q["parts_passed"], q["first_try_passes"], q["rounds"]), (2, 1, 3))
        part = next(p for p in summary["videos"][0]["parts"] if p["mode"] == "B")
        self.assertEqual((part["rounds"], part["first_try"], part["status"]), (2, False, "passed"))
        records = list(Path(self.tmp, "records").rglob("*.json"))
        text = "\n".join(r.read_text(encoding="utf-8") for r in records)
        self.assertIn("[code] cue word 'nowhere' is not in beat c1", text)
        self.assertNotIn("review_problems\": [\"", text)                       # no reviewer round for layout

    def test_a_bank_story_gets_the_bank_kit_and_a_factory_story_falls_back_to_the_canvas(self):
        chapter, lesson = econ_lesson()
        for b in lesson["videos"][0]["beats"]:
            if b["part_id"] == "p1":
                b["say"] = b["say"].replace("दुकान", "बैंक").replace("खरीदार", "borrower").replace("दुकानदार", "banker")
        summary = cd.run_canvas(chapter, lesson, ECON, runner(self.tmp), self.tmp, workers=1)
        self.assertEqual(summary["quality"]["modes"], {"B": 1, "C": 1})                   # PR 3: the bank has its kit
        self.assertEqual(summary["quality"]["missing_kits"], [])
        plans = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(Path(self.tmp, "plans").glob("*.plan.json"))]
        plan = next(p for p in plans if p.get("kit") == "bank")
        self.assertEqual({e["kind"] for e in plan["elements"]} & {"bank", "teller", "board"}, {"bank", "teller", "board"})
        self.assertNotIn("Missing world kits", Path(self.tmp, "CANVAS.md").read_text(encoding="utf-8"))

    def test_a_factory_story_falls_back_to_the_canvas_and_logs_the_missing_kit(self):
        chapter, lesson = econ_lesson()
        for b in lesson["videos"][0]["beats"]:
            if b["part_id"] == "p1":
                b["say"] = b["say"].replace("दुकान", "फैक्ट्री").replace("खरीदार", "worker").replace("दुकानदार", "मज़दूर")
        summary = cd.run_canvas(chapter, lesson, ECON, runner(self.tmp), self.tmp, workers=1)
        self.assertEqual(summary["quality"]["modes"], {"B": 2, "C": 0})
        self.assertEqual(summary["quality"]["missing_kits"], ["world kit for a factory"])
        self.assertIn("Missing world kits", Path(self.tmp, "CANVAS.md").read_text(encoding="utf-8"))

    def test_a_bank_plan_drawn_as_a_shop_is_refused_with_the_kit_named(self):
        stub = {"id": "p1s", "part_id": "p1", "beats": beats_of("demand_pull_touches.plan.json", "p1")}
        value = fake.world_answer(json.dumps({"beats": stub["beats"]}))                   # the beats are set in a shop → shop world
        self.assertEqual(cd.check_plan(stub, value, {"mode": "C", "kit": "shop"}), [])
        self.assertEqual(cd.check_plan(stub, value, {"mode": "C", "kit": "bank"}), ["a world in bank needs its place: add a bank element"])
        self.assertEqual(cd.check_plan(stub, value, "C"), [])                              # the letter alone: no kit required

    def test_a_long_part_becomes_two_canvases_and_a_non_canvas_subject_is_left_to_the_shot_list_director(self):
        chapter, lesson = econ_lesson()
        beats = lesson["videos"][0]["beats"]
        extra = [dict(beats[-1], beat_id=f"x{n}", say=f"बात {n} और है।") for n in range(1, 12)]
        lesson["videos"][0]["beats"] = beats + extra                                # p2 now has 6 + 11 = 17 beats
        summary = cd.run_canvas(chapter, lesson, ECON, runner(self.tmp), self.tmp, workers=1)
        self.assertEqual([p["id"] for p in summary["videos"][0]["parts"]], ["v1_s1", "v1_s2a", "v1_s2b"])
        chapter["course"]["subject"] = "Biology"
        other = cd.run_canvas(chapter, lesson, BIO, runner(self.tmp), Path(self.tmp, "bio"), workers=1)
        self.assertEqual(other["quality"]["parts"], 0)
        self.assertIn("not a canvas subject", other["note"])


class Tool(unittest.TestCase):
    def test_run_brain_runs_the_canvas_section_on_a_run_folder(self):
        import run_brain
        chapter, lesson = econ_lesson()
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder, "run")
            run.mkdir()
            (run / "chapter_map.json").write_text(json.dumps(chapter, ensure_ascii=False), encoding="utf-8")
            (run / "lesson_plan.json").write_text(json.dumps(lesson, ensure_ascii=False), encoding="utf-8")
            out = Path(folder, "out")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = run_brain.main(["--fake", "--section", "canvas", "--from-run", str(run), "--out", str(out), "--workers", "1",
                                       "--max-inr", "100000", "--videos", "v1"])
            self.assertEqual(code, 0)
            summary = json.loads((out / "SUMMARY.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "ok")
            self.assertEqual(summary["canvas_quality"]["parts_passed"], 2)
            self.assertIn("canvas", summary["estimate"]["sections"])
            self.assertTrue((out / "video_specs" / "v1.json").exists())
            # a lesson run folder has no chapter_map.json (the Money lesson read its map from a URL): --chapter-map names it
            lesson_only = Path(folder, "lesson_run")
            lesson_only.mkdir()
            (lesson_only / "lesson_plan.json").write_text(json.dumps(lesson, ensure_ascii=False), encoding="utf-8")
            out2 = Path(folder, "out2")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = run_brain.main(["--fake", "--section", "canvas", "--from-run", str(lesson_only), "--chapter-map", str(run / "chapter_map.json"),
                                       "--out", str(out2), "--workers", "1", "--max-inr", "100000", "--videos", "v1"])
            self.assertEqual(code, 0)
            self.assertTrue((out2 / "video_specs" / "v1.json").exists())
            # the canvas section has no reviewer round: its preflight checks the maker's route only (a job without a reviewer
            # route stopped on the VM's default Google reviewer on 28 October 2026)
            self.assertEqual(list(summary["preflight"]["routes"]), [summary["maker"]])

    def test_the_vm_accepts_a_canvas_job(self):
        import codex_vm
        job = codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "t046c-canvas", "section": "canvas",
                                 "from_run": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/x/", "videos": "v1"})
        self.assertEqual(job["section"], "canvas")
        argv = codex_vm.argv(job, Path("/tmp/out"))
        self.assertIn("canvas", argv)
        self.assertIn("--videos", argv)
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "x", "section": "canvas"})


if __name__ == "__main__":
    unittest.main()
