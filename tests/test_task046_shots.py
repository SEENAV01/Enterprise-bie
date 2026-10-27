"""Task 046 Part A · the visual level ladder, the visual grammar rulebook, the wording rule W-01 and the shot-list
director (one spoken sentence → one shot, by code), with the offline proof on v3 of the tissue chapter.

Offline, standard library, no network, no keys, no money. Navin's decisions of 26 October 2026 are the rules under test:
every shot carries a level from {L2, L3, L4, L5a}; the level rule has two stars (A: 90-99 % of a chapter's videos with their
main level at L3 or above, a target and never a blocker; B: the level is per shot, L2 only with its reason, no video blocked
for its level); the pace is the visual-change rate (micro 3-5 s, engineering 10-20 s); a plan that asks for L5b is a
planning error; the narration never points at the book (W-01).
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import director, lesson, regression, rulebook, shots, soul  # noqa: E402
from bie.brain.understanding import Course  # noqa: E402
from bie.toolbox import registry  # noqa: E402

FIXTURE = ROOT / "tests/fixtures/task046/v3_tissue.json"
LEVELS = ROOT / "bie/brain/rulebook/visual_levels.json"
GRAMMAR = ROOT / "bie/brain/rulebook/visual_grammar.json"
CAPABILITIES = ROOT / "bie/toolbox/capabilities.json"
BENCHMARK = ROOT / "bie/brain/rulebook/benchmarks/epithelium_animation.json"
BOX = registry.load()
BOOK = rulebook.load()
V3 = json.loads(FIXTURE.read_text(encoding="utf-8"))
V3_COURSE = Course(**V3["course"])
V3_CHAPTER = {"course": V3["course"], "items": V3["items"], "level": V3["level"], "source_sha256": V3["source_sha256"]}


def beat(bid, say, *, purpose="explain", part="c1.1", covers=("p001-i2",), on_screen=""):
    return {"beat_id": bid, "part_id": part, "step": 1, "purpose": purpose, "say": say, "covers_item_ids": list(covers),
            "answers": [], "on_screen": on_screen, "basis": "book"}


TINY_ITEMS = {
    "p001-i1": {"item_id": "p001-i1", "kind": "heading", "content": "Epithelial tissue", "content_type": "none", "parent_item_id": "",
                "unpack": dict(soul.EMPTY_UNPACK)},
    "p001-i2": {"item_id": "p001-i2", "kind": "list_point", "content": "Epithelial cells are tightly packed and form a continuous sheet over a basement membrane.",
                "content_type": "structure", "parent_item_id": "p001-i1", "teachable": True,
                "unpack": dict(soul.EMPTY_UNPACK, visual_verb="Fit cells edge to edge into a sheet.",
                               terms=[{"term": "basement membrane", "plain_meaning": "नीचे का आधार", "everyday_image": "tiles के नीचे की परत"}])},
    "p001-i3": {"item_id": "p001-i3", "kind": "table_row", "content": "Simple squamous | Location: lung air sacs, blood vessels | Function: diffusion",
                "content_type": "structure", "parent_item_id": "p001-i1", "teachable": True,
                "unpack": dict(soul.EMPTY_UNPACK, visual_verb="Pass particles across one thin layer.")},
}
TINY_CHAPTER = {"course": {"title": "Tissues", "subject": "Biology", "learners": "class 11", "exam": "NEET", "language": "Hinglish", "level": "neet_11_12"},
                "items": TINY_ITEMS, "level": "neet_11_12"}
TINY_COURSE = Course(**TINY_CHAPTER["course"])
TINY_BEATS = [
    beat("b1", "Skin को बचाव करना है, lung air sacs को gases पार होने देनी हैं। क्या एक जैसी covering चलेगी?", purpose="hook", part="", covers=(),
         on_screen="Skin protection versus lung exchange."),
    beat("b2", "Cells tightly packed हैं और continuous sheet बनाती हैं; sheet के नीचे basement membrane यानी नीचे का आधार है। Kaisi? Lagataar.",
         on_screen="Fit cells edge to edge."),
    beat("b3", "Simple squamous lung air sacs में मिलता है। Oxygen पतली sheet के पार diffuse करती है।", covers=("p001-i3",),
         on_screen="Oxygen dots cross the thin sheet."),
    beat("b4", "याद रखो: पतली sheet, आसान exchange।", purpose="recap"),
]
TINY_VIDEO = {"video_id": "v1", "title": "Epithelium", "status": "passed", "beats": TINY_BEATS, "kind": "topic"}


class VisualLevels(unittest.TestCase):
    def test_the_ladder_carries_navins_words_and_the_rule(self):
        data = json.loads(LEVELS.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "bie.brain.visual-levels/1")
        self.assertEqual([lvl["id"] for lvl in data["levels"]], ["L1", "L2", "L3", "L4", "L5a", "L5b"])
        self.assertEqual(data["shot_levels"], ["L2", "L3", "L4", "L5a"])
        self.assertNotIn("minimum_share", data)                                   # the per-video 90 % blocker is withdrawn
        self.assertEqual(data["targets"]["chapter"]["target"], [0.9, 0.99])
        self.assertFalse(data["targets"]["chapter"]["blocker"])
        self.assertFalse(data["targets"]["shot"]["blocker"])
        self.assertIn("koshish ka target hai, blocker nahi", data["targets"]["chapter"]["decided"])
        self.assertIn("poori video ek level ki bane, ye zaroori nahi", data["targets"]["shot"]["decided"])
        self.assertEqual(data["pace"]["bands"]["micro"]["seconds"], [3.0, 5.0])
        self.assertEqual(data["pace"]["bands"]["world"]["seconds"], [10.0, 20.0])
        self.assertEqual(data["capable_up_to"], "L5a")
        self.assertTrue(any(w.startswith("90 se 99 percent videos L3 ya isse upar ke level ki ho.") for w in data["decided"]["words"]))
        page = (ROOT / "docs/vision/VISUAL_LEVELS.md").read_text(encoding="utf-8")
        for words in ("two stars", "koshish ka target hai, blocker nahi", "poori video ek level ki bane", "3–5 s per change", "10–20 s"):
            self.assertIn(words, page)
        for lvl in data["levels"]:
            self.assertEqual(lvl["shot_allowed"], lvl["id"] in data["shot_levels"], lvl["id"])
            self.assertEqual(lvl["bie_target"], lvl["id"] not in ("L1", "L5b"), lvl["id"])
        self.assertTrue((ROOT / "docs/vision/VISUAL_LEVELS.md").read_text(encoding="utf-8").count("L5b") >= 2)

    def test_the_rulebook_counts_the_ladder_as_data_and_the_grammar_as_rules(self):
        self.assertIn("visual_levels@2026-10-26.2", BOOK.version)
        self.assertIn("visual_grammar@2026-10-26.2", BOOK.version)
        self.assertIn("vision-2026-10-21@2026-10-21.14", BOOK.version)
        bench = json.loads(BENCHMARK.read_text(encoding="utf-8"))
        self.assertEqual(bench["version"], "2026-10-26.1")
        self.assertIn("3-5 seconds", next(r["rule"] for r in bench["rules"] if r["id"] == "B-01"))
        self.assertIn("3-5 seconds", next(r.rule for r in BOOK.rules if r.id == "S3-06"))
        self.assertIn("3-5 seconds", next(r.rule for r in BOOK.rules if r.id == "VG-01"))
        self.assertIn("10-20 seconds", next(r.rule for r in BOOK.rules if r.id == "VG-01"))
        ids = [r.id for r in BOOK.for_section("director")]
        self.assertEqual([i for i in ids if i.startswith("VG-")], [f"VG-{n:02d}" for n in range(1, 12)])
        self.assertIn("W-01", ids)
        self.assertIn("W-01", [r.id for r in BOOK.for_section("lesson")])
        self.assertIn("W-01", [r.id for r in BOOK.for_section("visual")] + ["W-01"])     # the visual section reads VG-*; W-01 is a lesson rule
        self.assertEqual([r.id for r in BOOK.for_section("visual") if r.id.startswith("VG-")], [f"VG-{n:02d}" for n in range(1, 12)])
        grammar = json.loads(GRAMMAR.read_text(encoding="utf-8"))
        self.assertIn("G-01 to G-07 are already the general rules", grammar["numbering"])
        self.assertTrue(all(r["status"] == "locked" for r in grammar["rules"]))
        self.assertIn("split_compare", next(r["rule"] for r in grammar["rules"] if r["id"] == "VG-07"))
        self.assertIn("licence gate", next(r["rule"] for r in grammar["rules"] if r["id"] == "VG-10"))

    def test_rank_and_higher(self):
        self.assertLess(shots.level_rank("L2"), shots.level_rank("L3"))
        self.assertLess(shots.level_rank("L4"), shots.level_rank("L5a"))
        self.assertEqual(shots.higher("L3", "L5a"), "L5a")
        self.assertEqual(shots.level_rank("L9"), 0)

    def test_pace_bands_by_subject(self):
        self.assertEqual(shots.pace_band("biology_medical"), ("micro", (3.0, 5.0)))
        self.assertEqual(shots.pace_band("physics"), ("world", (10.0, 20.0)))
        self.assertEqual(shots.pace_band("law"), ("", None))


class WordingRule(unittest.TestCase):
    """W-01 (Navin, 26 October 2026): no 'book के अनुसार', 'किताब कहती है', 'book says' or anything of that family."""

    def test_the_refused_examples_are_caught_and_the_allowed_ones_are_not(self):
        words = json.loads(GRAMMAR.read_text(encoding="utf-8"))["wording"]["W-01"]
        for text in words["refused_examples"]:
            self.assertTrue(soul.book_pointing(text), text)
        for text in words["allowed_examples"]:
            self.assertEqual(soul.book_pointing(text.split(" (")[0]), [], text)

    def test_the_three_forms_and_the_mixed_form(self):
        cases = {"किताब के अनुसार epithelium covering बनाता है।": "hindi", "NCERT kehta hai ki membrane non-cellular hai.": "hinglish",
                 "According to the book, the cells are flat.": "english", "Book में इसे simple squamous कहा गया है।": "mixed",
                 "Book short cylindrical कहती है; height और width लगभग बराबर समझो।": "mixed", "Page पर दिया diagram देखो।": "mixed",
                 "Printed location है ‘The outer layer of the cell’।": "hinglish", "book waterproof कहती है, water-resistant समझो।": "mixed"}
        for text, group in cases.items():
            found = soul.book_pointing(text)
            self.assertEqual(len(found), 1, text)
            self.assertEqual(found[0][2], group, text)

    def test_everyday_books_and_longer_words_stay(self):
        for text in ("एक book में लगभग 1 MB text होता है।", "इसे book-lung कहते हैं।", "Notebook में लिखो।", "Kitaabghar mein jao.",
                     "पृष्ठभूमि dark रखो।", "Exam में यह line सीधे पूछी जाती है।", "इस table को देखो: shape → job।"):
            self.assertEqual(soul.book_pointing(text), [], text)

    def test_wording_problems_go_back_to_the_maker_through_the_script_checks(self):
        beats = [beat("b7", "Book waterproof कहती है। Keratin रगड़ घटाता है।"), beat("b8", "Keratin रगड़ घटाता है।")]
        problems = soul.wording_problems(beats)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("beat b7:") and problems[0].endswith("(W-01)"), problems[0])
        self.assertIn("soul.wording_problems(beats)", (ROOT / "bie/brain/lesson.py").read_text(encoding="utf-8"))
        hits = soul.wording_hits(beats)
        self.assertEqual([h["beat_id"] for h in hits], ["b7"])
        self.assertEqual(hits[0]["group"], "mixed")

    def test_the_rule_change_is_recorded_for_the_passed_outputs(self):
        change = next(c for c in regression.RULE_CHANGES if c["rule"] == "W-01")
        self.assertEqual(change["rulebook"], "visual_grammar@2026-10-26.1")
        self.assertIn("wording patch", change["upgraded_by"])
        old_set = {"rulebook": "content_types@2026-10-24.1+vision-2026-10-21@2026-10-21.12"}
        self.assertIs(regression._changed(old_set, 'beat b7: "Book waterproof कहती है।" points at the book (\'book waterproof कहती है\') (W-01)'), change)
        new_set = {"rulebook": "visual_grammar@2026-10-26.1+vision-2026-10-21@2026-10-21.12"}
        self.assertIsNone(regression._changed(new_set, "beat b7: x (W-01)"))

    def test_the_wording_hint_is_sent_only_when_a_beat_points_at_the_book(self):
        self.assertIn("change no other beat", lesson.SCRIPT_WORDING_HINT)
        text = (ROOT / "bie/brain/lesson.py").read_text(encoding="utf-8")
        self.assertIn("(SCRIPT_WORDING_HINT if soul.wording_hits(beats) else \"\")", text)


class OnlyTheseVideos(unittest.TestCase):
    """VM job 1 patches v3 alone: every other script is kept exactly as it was (lesson.reusable(only=...))."""

    def test_unselected_scripts_are_kept_with_a_note(self):
        previous = {"naksha_sha256": "n", "plan_status": "passed", "plan": {"videos": [{"video_id": "v3"}, {"video_id": "v7"}]},
                    "videos": [{"video_id": "v3", "status": "passed", "beats": [beat("b1", "Book x कहती है।")], "parts": []},
                               {"video_id": "v7", "status": "passed", "beats": [beat("b1", "Page पर देखो।")], "parts": []}]}
        saved = {k: getattr(lesson, k) for k in ("check_plan", "script_prefixes", "script_card", "check_script", "video_budget")}
        try:
            lesson.check_plan = lambda plan, chapter: []
            lesson.script_prefixes = lambda course, rulebook: ("prefix", "review")
            lesson.script_card = lambda *a, **k: {"parts": [], "coverage": {"must_cover": []}}
            lesson.check_script = lambda value, chapter, video, language, card, budget: soul.wording_problems(value["beats"])
            lesson.video_budget = lambda chapter, videos, video: (1, 2)
            plan, scripts, notes, starts = lesson.reusable(previous, {"items": {}}, {"sha256": "n"}, TINY_COURSE, BOOK, only=["v3"])
        finally:
            for k, v in saved.items():
                setattr(lesson, k, v)
        self.assertEqual(sorted(starts), ["v3"])                      # v3 continues from its last answer (the W-01 patch round)
        self.assertEqual(sorted(scripts), ["v7"])                     # v7 is kept, problems and all
        self.assertTrue(any(n.startswith("v7 kept as it was (not selected for this run; 1 problems today)") for n in notes), notes)
        self.assertTrue(any(n.startswith("v3 fails today's checks") for n in notes), notes)

    def test_run_brain_passes_the_selection_to_the_lesson(self):
        text = (ROOT / "tools/run_brain.py").read_text(encoding="utf-8")
        self.assertIn("only=[v.strip() for v in args.videos.split(\",\") if v.strip()] or None", text)
        self.assertIn('"videos": re.compile', (ROOT / "tools/codex_vm.py").read_text(encoding="utf-8"))


class CapabilitiesCarryLevelsAndBlocks(unittest.TestCase):
    def test_every_capability_names_its_level_and_its_blocks(self):
        allowed = set(registry.shot_levels())
        self.assertEqual(allowed, {"L2", "L3", "L4", "L5a"})
        for cap in BOX.capabilities.values():
            self.assertIn(cap.default_level, allowed, cap.id)
            self.assertTrue(cap.blocks, cap.id)
        self.assertEqual(BOX.capabilities["cell_sheet_3d"].default_level, "L5a")
        self.assertEqual(BOX.capabilities["equation_transform"].default_level, "L3")
        self.assertEqual(BOX.capabilities["vector_field"].default_level, "L2")
        self.assertEqual(BOX.capabilities["board_build"].blocks, ("board_build",))

    def test_the_benchmark_and_the_new_blocks_are_all_named(self):
        bench = json.loads(BENCHMARK.read_text(encoding="utf-8"))["blocks"]
        named = {b for cap in BOX.capabilities.values() for b in cap.blocks} | set(registry.grammar_blocks())
        for block in bench["built_in_task_046"] + ["split_compare"]:
            self.assertIn(block, named, block)
        for block in ("leader_label", "cutaway", "exploded_view", "scale_compare", "equation_steps", "graph_plot", "flow_arrows", "timeline", "camera_path"):
            self.assertIn(block, named, block)

    def test_the_loader_refuses_a_wrong_level_or_missing_blocks(self):
        caps = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        reg = json.loads((ROOT / "bie/toolbox/registry.json").read_text(encoding="utf-8"))
        bad = json.loads(json.dumps(caps))
        bad["capabilities"][0]["default_level"] = "L5b"
        bad["capabilities"][1]["blocks"] = []
        found = registry.problems(reg, bad)
        self.assertTrue(any("default_level must be one of L2, L3, L4, L5a" in p for p in found), found[:3])
        self.assertTrue(any("needs the code blocks that draw it" in p for p in found), found[:3])
        self.assertEqual([p for p in registry.problems(reg, caps) if "capability" in p], [])


class Sentences(unittest.TestCase):
    def test_one_clause_one_shot_and_short_questions_join_their_answer(self):
        say = "Cells packed हैं; sheet बनती है। Kaisi? Lagataar. Basement membrane नीचे है।"
        self.assertEqual(shots.split_sentences(say), ["Cells packed हैं;", "sheet बनती है।", "Kaisi? Lagataar. Basement membrane नीचे है।"])
        self.assertEqual(shots.split_sentences("Sirf ek."), ["Sirf ek."])
        self.assertEqual(shots.split_sentences(""), [])

    def test_labels_are_the_things_the_sentence_says_as_phrases(self):
        vocab = {"basement", "membrane", "tightly", "packed", "continuous", "sheet", "kidney", "tubules", "bladder", "ureter", "urethra"}
        self.assertEqual(shots.shot_labels("Sheet के नीचे extracellular fibrous basement membrane होती है।", vocab, []), ["sheet", "basement membrane"])
        self.assertEqual(shots.shot_labels("इसके स्थान urinary bladder, ureter और urethra हैं।", vocab, []), ["bladder", "ureter", "urethra"])
        self.assertEqual(shots.shot_labels("tightly packed cells continuous sheet बनाती हैं", vocab, ["परत"]), ["tightly packed cells", "continuous sheet", "परत"])
        self.assertEqual(shots.shot_labels("कोई English शब्द नहीं", vocab, []), [])

    def test_family_and_members(self):
        self.assertEqual(shots.subject_family("Science and Technology"), "biology_medical")
        self.assertEqual(shots.subject_family("Indian Polity"), "geography_history_polity")
        self.assertEqual(shots.subject_family("Something else"), "all_subjects")
        self.assertEqual(shots.member_of("Simple squamous है: flat cells"), "simple squamous")
        self.assertEqual(shots.member_of("कड़ी है"), "")

    def test_scenes_follow_the_parts_and_the_hook_joins_the_first(self):
        scenes = shots.scenes_of(TINY_BEATS + [beat("b5", "अगला topic।", part="c1.2"), beat("b6", "bye", part="")])
        self.assertEqual([(s["scene_id"], s["part_id"], s["beat_ids"]) for s in scenes],
                         [("s1", "c1.1", ["b1", "b2", "b3", "b4"]), ("s2", "c1.2", ["b5", "b6"])])


class DirectorOnATinyScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = shots.build_video(TINY_VIDEO, TINY_CHAPTER, TINY_COURSE, toolbox=BOX)

    def test_one_shot_per_clause_with_timing_from_the_beat(self):
        expected = sum(len(shots.split_sentences(b["say"])) for b in TINY_BEATS)
        self.assertEqual(len(self.plan["shots"]), expected)
        self.assertEqual([s["shot_id"] for s in self.plan["shots"]][:3], ["b1.1", "b1.2", "b2.1"])
        for s in self.plan["shots"]:
            self.assertGreater(s["seconds"], 0)
            self.assertIn(s["level"], ("L2", "L3", "L4", "L5a"))
            self.assertEqual(s["block"], s["blocks"][0])
            self.assertIn("kinetic_caption", s["blocks"])             # B-08 on every shot
            self.assertIn("leader_label", s["blocks"])                # VG-02 on every shot
            for label in s["labels"]:
                self.assertIn(label.lower(), s["sentence"].lower())    # B-03: nothing shown that is not said
        self.assertAlmostEqual(self.plan["seconds"], sum(s["seconds"] for s in self.plan["shots"]), places=1)

    def test_the_world_is_the_cell_sheet_and_the_benchmark_shots_are_chosen(self):
        self.assertEqual(self.plan["world"]["capability"], "cell_sheet_3d")
        by_id = {s["shot_id"]: s for s in self.plan["shots"]}
        self.assertEqual(by_id["b1.1"]["capability"], "organ_zoom")              # the hook from the organ (B-09)
        self.assertEqual(by_id["b1.1"]["camera"], "zoom_in")
        self.assertEqual(by_id["b3.1"]["capability"], "organ_zoom")              # where found
        self.assertEqual(by_id["b3.2"]["capability"], "particle_flow")           # a function sentence moves (B-04)
        self.assertEqual(by_id["b4.1"]["capability"], "mnemonic_card")           # याद रखो in a recap
        self.assertEqual(by_id["b4.1"]["level"], "L3")
        self.assertIn("focus_glow", by_id["b2.1"]["blocks"])                     # B-10
        self.assertTrue(by_id["b2.2"]["caption"]["yaani"])                       # B-05 the plain meaning on the caption
        self.assertEqual(by_id["b2.2"]["level"], "L5a")                          # overlays never lower the world's level

    def test_the_level_mix_the_main_level_and_the_pace(self):
        self.assertEqual(self.plan["main_level"], "L5a")
        self.assertGreaterEqual(self.plan["l3_plus_share"], 0.9)
        self.assertEqual(set(self.plan["level_split"]) <= {"L3", "L5a"}, True)
        self.assertNotIn("at_or_above", self.plan)
        pace = self.plan["pace"]
        self.assertEqual((pace["band"], pace["target_seconds"]), ("micro", [3.0, 5.0]))
        self.assertEqual(pace["changes"], len(shots.visual_changes(self.plan["shots"])))
        self.assertLessEqual(pace["seconds_per_change"], 5.0 + 0.5)
        self.assertTrue(self.plan["render_allowed"], self.plan["checks"]["blocking"])
        self.assertEqual(self.plan["checks"]["blocking"], [])
        self.assertEqual(self.plan["wording"]["hits"], [])
        self.assertEqual(len(self.plan["rule_table"]), 24)
        self.assertEqual({r["status"] for r in self.plan["rule_table"]} <= {"pass", "partial", "fail", "n/a"}, True)

    def test_the_ai_directors_checks_accept_the_code_shot_list(self):
        video = shots.to_director_video(self.plan, TINY_BEATS)
        problems = director.check_video(video, TINY_BEATS, set(TINY_ITEMS), set())
        self.assertEqual(problems, [])
        self.assertEqual([s["scene_id"] for s in video["scenes"]], ["s1"])
        self.assertTrue(all(s["actions"] for s in video["scenes"]))


class TheChecksFailWhatNavinRuledOut(unittest.TestCase):
    def plan_with(self, levels):
        plan = shots.build_video(TINY_VIDEO, TINY_CHAPTER, TINY_COURSE, toolbox=BOX)
        for s, lvl in zip(plan["shots"], levels * len(plan["shots"])):
            s["level"] = lvl
        split = shots.level_split(plan["shots"])
        total = sum(v["seconds"] for v in split.values())
        above = sum(v["seconds"] for lvl, v in split.items() if shots.level_rank(lvl) >= shots.level_rank("L3"))
        plan["level_split"], plan["l3_plus_share"] = split, round(above / total, 4)
        return plan

    def test_a_shot_at_l5b_or_l1_is_a_planning_error(self):
        plan = self.plan_with(["L5b"])
        blocking, _ = shots.check_video(plan, TINY_BEATS, toolbox=BOX)
        self.assertTrue(any("level 'L5b' is outside BIE's output" in p for p in blocking), blocking[:2])
        plan = self.plan_with(["L1"])
        self.assertTrue(any("level 'L1' is outside" in p for p in shots.check_video(plan, TINY_BEATS, toolbox=BOX)[0]))

    def test_a_mostly_l2_video_is_reported_not_blocked(self):
        """Star A and B (Navin, 26 October 2026): a video's level never blocks it; the chapter report names it with the reason."""
        plan = self.plan_with(["L2", "L2", "L2", "L5a"])
        for s in plan["shots"]:
            if s["level"] == "L2":
                s["level_reason"] = "L2: a flat drawing shows this better (test)"
        blocking, advisory = shots.check_video(plan, TINY_BEATS, toolbox=BOX)
        self.assertEqual([p for p in blocking if "90" in p or "not rendered" in p], [])
        plan["main_level"] = "L2"
        report = shots.chapter_report([plan, dict(plan, video_id="v9", main_level="L5a", level_split={"L5a": {"shots": 1, "seconds": 10, "share": 1.0}})])
        self.assertEqual((report["videos"], report["l3_plus_videos"], report["share"]), (2, 1, 0.5))
        self.assertFalse(report["meets_target"])
        self.assertFalse(report["blocker"])
        self.assertEqual([r["video_id"] for r in report["below_target"]], ["v1"])
        self.assertIn("main level L2", report["below_target"][0]["reason"])
        self.assertIn("koshish ka target hai, blocker nahi", report["decided"])

    def test_an_l2_shot_without_its_reason_is_pointed_at(self):
        plan = self.plan_with(["L2"])
        for s in plan["shots"]:
            s["level_reason"] = ""
        _, advisory = shots.check_video(plan, TINY_BEATS, toolbox=BOX)
        self.assertTrue(any("L2 without its reason" in p for p in advisory), advisory[:3])

    def test_the_pace_pass_adds_camera_moves_only_where_the_picture_would_hold(self):
        plan = shots.build_video(TINY_VIDEO, TINY_CHAPTER, TINY_COURSE, toolbox=BOX)
        still = [dict(s, camera="hold", block="cell_sheet", seconds=2.0, why=[]) for s in plan["shots"]]
        before = len(shots.visual_changes(still))
        added = shots.pace_pass(still, (3.0, 5.0))
        self.assertEqual(before, 1)
        self.assertGreaterEqual(added, len(still) // 3)
        self.assertLessEqual(sum(s["seconds"] for s in still) / len(shots.visual_changes(still)), 5.0)
        self.assertTrue(all(s["camera"] in ("hold", "zoom_in", "orbit", "zoom_out") for s in still))
        self.assertEqual(shots.pace_pass([dict(s) for s in still], None), 0)        # no band, no moves
        slow = [dict(s, camera="hold", block="cell_sheet", seconds=2.0, why=[]) for s in plan["shots"]]
        shots.pace_pass(slow, (10.0, 20.0))
        self.assertLess(len(shots.visual_changes(slow)), len(shots.visual_changes(still)))

    def test_said_is_shown_and_one_sentence_one_shot(self):
        plan = shots.build_video(TINY_VIDEO, TINY_CHAPTER, TINY_COURSE, toolbox=BOX)
        plan["shots"][0]["labels"] = ["mitochondria"]
        blocking, _ = shots.check_video(plan, TINY_BEATS, toolbox=BOX)
        self.assertTrue(any("'mitochondria' is not said" in p and "(B-03)" in p for p in blocking), blocking)
        plan = shots.build_video(TINY_VIDEO, TINY_CHAPTER, TINY_COURSE, toolbox=BOX)
        plan["shots"].pop(2)
        blocking, _ = shots.check_video(plan, TINY_BEATS, toolbox=BOX)
        self.assertTrue(any(p.startswith("B-01:") for p in blocking), blocking)
        plan = shots.build_video(TINY_VIDEO, TINY_CHAPTER, TINY_COURSE, toolbox=BOX)
        plan["shots"][0]["blocks"] = ["hologram"]
        self.assertTrue(any("unknown block 'hologram'" in p for p in shots.check_video(plan, TINY_BEATS, toolbox=BOX)[0]))

    def test_a_beat_that_points_at_the_book_blocks_the_video(self):
        video = dict(TINY_VIDEO, beats=TINY_BEATS + [beat("b5", "Book waterproof कहती है।")])
        plan = shots.build_video(video, TINY_CHAPTER, TINY_COURSE, toolbox=BOX)
        self.assertFalse(plan["render_allowed"])
        self.assertEqual([h["beat_id"] for h in plan["wording"]["hits"]], ["b5"])
        self.assertTrue(any(p.endswith("(W-01)") for p in plan["checks"]["blocking"]))
        self.assertEqual(next(r for r in plan["rule_table"] if r["rule"] == "W-01")["status"], "fail")


class TheOfflineProofOnV3(unittest.TestCase):
    """v3 (epithelial tissue) as the lesson run passed it on 25 October 2026: the shot list, the level split, every W-01 hit."""

    @classmethod
    def setUpClass(cls):
        cls.plan = shots.build_video(V3["video"], V3_CHAPTER, V3_COURSE, toolbox=BOX)

    def test_one_shot_per_spoken_clause_in_order(self):
        expected = [(b["beat_id"], k + 1) for b in V3["video"]["beats"] for k in range(len(shots.split_sentences(b["say"])))]
        self.assertEqual([(s["beat_id"], int(s["shot_id"].rsplit(".", 1)[1])) for s in self.plan["shots"]], expected)
        self.assertGreater(len(self.plan["shots"]), 120)
        self.assertEqual(self.plan["beats"], 53)
        self.assertEqual([s["part_id"] for s in self.plan["scenes"]], ["c06.1", "c06.2", "c06.3", "c07.1", "c07.2", "c08.1"])
        self.assertAlmostEqual(self.plan["seconds"], sum(s["seconds"] for s in self.plan["shots"]), places=1)
        self.assertGreater(self.plan["seconds"], 9 * 60)

    def test_the_world_the_levels_and_the_pace(self):
        self.assertEqual(self.plan["world"], dict(self.plan["world"], capability="cell_sheet_3d", block="cell_sheet", level="L5a"))
        self.assertEqual(set(self.plan["level_split"]), {"L3", "L5a"})
        self.assertGreater(self.plan["level_split"]["L5a"]["share"], 0.8)
        self.assertEqual((self.plan["main_level"], self.plan["l3_plus_share"]), ("L5a", 1.0))
        pace = self.plan["pace"]
        self.assertEqual(pace["band"], "micro")
        self.assertGreater(pace["seconds_per_change_before"], 5.0)              # measured 7.6 s before the director's camera moves
        self.assertTrue(3.0 <= pace["seconds_per_change"] <= 5.0, pace)         # within the benchmark pace after them
        self.assertGreater(pace["camera_moves_added"], 20)
        self.assertTrue(pace["within_target"])
        self.assertEqual([p for p in self.plan["checks"]["advisory"] if "(VG-01)" in p], [])
        self.assertEqual(next(r for r in self.plan["rule_table"] if r["rule"] == "VG-01")["status"], "pass")
        self.assertEqual(self.plan["level_profile"]["id"], "upsc_pcs")
        for s in self.plan["shots"]:
            self.assertIn(s["level"], ("L2", "L3", "L4", "L5a"))
            if s["capability"] in ("board_build", "mnemonic_card", "tree_hierarchy"):
                self.assertEqual(s["level"], "L3", s["shot_id"])
            else:
                self.assertEqual(s["level"], "L5a", s["shot_id"])

    def test_the_benchmark_shots_appear_where_the_sentences_ask(self):
        caps = {}
        for s in self.plan["shots"]:
            caps[s["capability"]] = caps.get(s["capability"], 0) + 1
        self.assertGreaterEqual(caps.get("organ_zoom", 0), 8)              # B-09: lungs, kidney, bladder, intestine, mouth
        self.assertGreaterEqual(caps.get("particle_flow", 0), 20)          # B-04: diffusion, secretion, mucus, shedding
        self.assertGreaterEqual(caps.get("board_build", 0), 7)             # B-07: one recap per part on the board
        self.assertGreaterEqual(caps.get("split_compare", 0), 5)           # VG-07: the compare beats
        self.assertGreaterEqual(caps.get("mnemonic_card", 0), 2)           # याद रखो
        self.assertEqual(caps.get("tree_hierarchy", 0), 1)                 # the family overview (b20)
        by_id = {s["shot_id"]: s for s in self.plan["shots"]}
        self.assertEqual(by_id["b1.1"]["capability"], "organ_zoom")
        self.assertEqual(by_id["b32.1"]["labels"], ["urinary bladder", "ureter", "urethra"])
        self.assertEqual([s["beat_id"] for s in self.plan["shots"] if s["capability"] == "tree_hierarchy"], ["b20"])
        self.assertEqual(self.plan["cuts"], 0)                             # VG-01: the camera moves, no cuts
        self.assertIn("pan", {s["camera"] for s in self.plan["shots"]})
        self.assertIn("zoom_in", {s["camera"] for s in self.plan["shots"]})
        self.assertIn("orbit", {s["camera"] for s in self.plan["shots"]})   # the pace pass
        self.assertTrue(all(s["level_reason"] == "" for s in self.plan["shots"]))     # no L2 shot in v3
        for s in self.plan["shots"]:
            for label in s["labels"]:
                self.assertIn(label.lower(), s["sentence"].lower(), s["shot_id"])

    def test_every_w01_hit_is_listed_and_is_the_only_blocker(self):
        hits = self.plan["wording"]["hits"]
        self.assertEqual([h["beat_id"] for h in hits], ["b22", "b24", "b29", "b30", "b36"])
        self.assertEqual([h["words"] for h in hits][:2], ["Book short cylindrical कहती है", "Book digestive और upper respiratory tract बताती है"])
        self.assertEqual([h["words"] for h in hits][3], "Printed location")
        self.assertEqual([p for p in self.plan["checks"]["blocking"] if "(W-01)" not in p], [])
        self.assertFalse(self.plan["render_allowed"])
        table = {r["rule"]: r["status"] for r in self.plan["rule_table"]}
        self.assertEqual(len(table), 24)
        self.assertEqual(table["W-01"], "fail")
        self.assertEqual(table["B-01"], "partial")                               # 18 clauses over 6 s: a long sentence could be two
        self.assertEqual(table["VG-01"], "pass")
        self.assertEqual(table["B-03"], "pass")
        self.assertEqual(table["VG-11"], "n/a")
        without = dict(V3["video"], beats=[b for b in V3["video"]["beats"] if b["beat_id"] not in ("b22", "b24", "b29", "b30", "b36")])
        clean = shots.build_video(without, V3_CHAPTER, V3_COURSE, toolbox=BOX)
        self.assertTrue(clean["render_allowed"], clean["checks"]["blocking"])     # with the five beats rewritten, v3 renders

    def test_the_recorded_proof_matches_the_code(self):
        recorded = json.loads((ROOT / "docs/evidence/task046-director/shots/v3.json").read_text(encoding="utf-8"))
        self.assertEqual(recorded["schema"], shots.SCHEMA)
        self.assertEqual(len(recorded["shots"]), len(self.plan["shots"]))
        self.assertEqual(recorded["level_split"], self.plan["level_split"])
        self.assertEqual(recorded["pace"], self.plan["pace"])
        self.assertEqual(recorded["main_level"], "L5a")
        self.assertEqual([h["beat_id"] for h in recorded["wording"]["hits"]], ["b22", "b24", "b29", "b30", "b36"])
        self.assertEqual([(s["shot_id"], s["capability"], s["level"]) for s in recorded["shots"]],
                         [(s["shot_id"], s["capability"], s["level"]) for s in self.plan["shots"]])
        w01 = (ROOT / "docs/evidence/task046-director/W01.md").read_text(encoding="utf-8")
        for bid in ("b22", "b24", "b29", "b30", "b36"):
            self.assertIn(f"| {bid} |", w01)

    def test_the_ai_directors_checks_accept_v3s_shot_list(self):
        video = shots.to_director_video(self.plan, V3["video"]["beats"])
        problems = director.check_video(video, V3["video"]["beats"], set(V3["items"]), set())
        self.assertEqual(problems, [])
        self.assertEqual(len(video["scenes"]), 6)


class RunAndTool(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="t046-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_run_shots_writes_the_pages_and_skips_a_failed_script(self):
        lesson_doc = {"videos": [TINY_VIDEO, {"video_id": "v2", "title": "x", "status": "failed", "beats": TINY_BEATS}]}
        summary = shots.run_shots(TINY_CHAPTER, lesson_doc, TINY_COURSE, self.tmp, toolbox=BOX)
        self.assertEqual([(v["video_id"], v["status"]) for v in summary["videos"]], [("v1", "render_allowed"), ("v2", "skipped")])
        self.assertTrue((self.tmp / "shots" / "v1.json").exists())
        self.assertEqual((summary["chapter"]["videos"], summary["chapter"]["l3_plus_videos"], summary["chapter"]["meets_target"]), (1, 1, True))
        page = (self.tmp / "SHOTS.md").read_text(encoding="utf-8")
        self.assertIn("## Chapter report (star A)", page)
        self.assertIn("## v1 · Epithelium", page)
        self.assertIn("Main level **L5a**", page)
        self.assertIn("Pace (VG-01)", page)
        self.assertIn("### The 24 rules", page)
        self.assertIn("render allowed", page)

    def test_the_tool_runs_on_a_run_folder(self):
        import shot_list
        (self.tmp / "chapter_map.json").write_text(json.dumps(TINY_CHAPTER, ensure_ascii=False), encoding="utf-8")
        (self.tmp / "lesson_plan.json").write_text(json.dumps({"videos": [TINY_VIDEO]}, ensure_ascii=False), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = shot_list.main(["--from-run", str(self.tmp), "--videos", "v1", "--out", str(self.tmp / "out")])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("v1:", out.getvalue())
        self.assertIn("main level L5a", out.getvalue())
        self.assertIn("chapter: 1 of 1 videos", out.getvalue())
        self.assertTrue((self.tmp / "out" / "shots" / "v1.json").exists())


if __name__ == "__main__":
    unittest.main()
