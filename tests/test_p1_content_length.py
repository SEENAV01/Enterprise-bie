"""S2-11, the content rule (Navin, 5 November 2026, his "Mix" choice for the Sloman economics book): with the course's
length_rule "content" a topic video's minutes come from what its items need (normal 0.25, deep 0.75, a practice question
0.10 spoken minutes; the video 0.8-1.4 times that), not from 6-8 minutes per book page. S2-01 stays the default."""
import copy
import unittest

from bie.brain import lesson, rulebook
from bie.brain.understanding import Course, DEEP_WHYS, ITEM_SCHEMA, TEACH_DEPTHS


def item(iid, page, depth="normal", why="", kind="paragraph", teachable=True, legacy=False):
    out = {"item_id": iid, "page": page, "kind": kind, "parent_item_id": "", "source": "text", "block_ids": [],
           "content": "Demand falls as the price rises.", "content_type": "definition", "teachable": teachable,
           "tests_item_ids": [],
           "teacher_understanding": [
               {"depth": 1, "ask": "what", "question": "What?", "answer": "The quantity bought falls.", "basis": "book"},
               {"depth": 2, "ask": "why", "question": "Why?", "answer": "Buyers switch to substitutes.", "basis": "outside"}]}
    if legacy:                                   # the Sloman run's kit wrote "depth" on the item itself
        out["depth"], out["deep_why"] = depth, why
    else:
        out["teach_depth"], out["deep_why"] = depth, why
    return out


def dense_chapter(rule="content", legacy=False):
    """One dense book page: c1 = 20 normal + 4 deep items (8 minutes), c2 = 10 deep items + 5 practice questions
    (8 minutes), c3 = 2 normal items (0.5 minutes). Under S2-01 the whole page is 6-8 minutes."""
    items, concepts = {}, []
    groups = {"c1": [("normal", "")] * 20 + [("deep", "graph")] * 4,
              "c2": [("deep", "numerical")] * 10 + [("question", "")] * 5,
              "c3": [("normal", "")] * 2}
    n = 0
    for cid, rows in groups.items():
        ids = []
        for depth, why in rows:
            n += 1
            iid = f"p001-i{n:02d}"
            if depth == "question":
                items[iid] = item(iid, 1, kind="question", legacy=legacy)
            else:
                items[iid] = item(iid, 1, depth, why, legacy=legacy)
            ids.append(iid)
        concepts.append({"concept_id": cid, "name": cid, "item_ids": ids, "content_type": "definition", "core_explanation": "x"})
    pre = [{"name": "Price", "why_needed": "x", "needed_for": ["c1"], "basis": "outside"}]
    course = {"title": "Demand", "subject": "Economics", "learners": "BA and UPSC", "exam": "UPSC", "language": "Hinglish"}
    if rule:
        course["length_rule"] = rule
    return {"course": course, "items": items,
            "map": {"concepts": concepts, "prerequisites_to_teach": pre, "teaching_order": ["c1", "c2", "c3"], "relations": [],
                    "exam_focus": []}}


def video(vid, cids, minutes, kind="topic", taught=()):
    return {"video_id": vid, "title": vid, "goal": "", "kind": kind, "concept_ids": list(cids), "prerequisites_taught": list(taught),
            "opening_hook": "", "story_or_analogy": "", "estimated_minutes": minutes, "length_note": "", "why_this_unit": ""}


PRE = video("v0", [], 6, "prerequisites", ["Price"])


class ContentRule(unittest.TestCase):
    def test_minutes_come_from_the_items_depth(self):
        chapter = dense_chapter()
        self.assertEqual(lesson.length_rule(chapter), "content")
        self.assertEqual({k: round(v, 2) for k, v in lesson.concept_minutes(chapter).items()}, {"c1": 8.0, "c2": 8.0, "c3": 0.5})
        videos = [PRE, video("v1", ["c1"], 9), video("v2", ["c2", "c3"], 10)]
        self.assertEqual([lesson.video_budget(chapter, videos, v) for v in videos], [(5.0, 8.0), (6.4, 11.2), (6.8, 11.9)])
        self.assertEqual(lesson.chapter_budget(chapter, videos), (13.2, 23.1))
        self.assertEqual(lesson.check_plan({"videos": videos}, chapter), [])

    def test_the_same_page_under_the_page_rule_gets_its_6_to_8_minutes(self):
        chapter = dense_chapter(rule=None)              # no length_rule: S2-01, unchanged
        self.assertEqual(lesson.length_rule(chapter), "pages")
        videos = [PRE, video("v1", ["c1", "c2", "c3"], 7)]
        self.assertEqual(lesson.check_plan({"videos": videos}, chapter), [])
        self.assertEqual(lesson.chapter_budget(chapter, videos), (6.0, 8.0))

    def test_a_video_out_of_its_items_minutes_is_named_with_the_rule(self):
        chapter = dense_chapter()
        short = [PRE, video("v1", ["c1"], 4), video("v2", ["c2", "c3"], 10)]
        problems = lesson.time_problems({"videos": short}, chapter)
        self.assertTrue(any("v1: 4 minutes is outside its narration budget of 6.4-11.2" in p and "S2-11" in p for p in problems),
                        problems)

    def test_a_video_too_heavy_is_split_and_a_light_one_merged(self):
        chapter = dense_chapter()
        heavy = copy.deepcopy(chapter)
        extra = [f"p002-i{k:02d}" for k in range(1, 21)]
        for iid in extra:
            heavy["items"][iid] = item(iid, 2, "deep", "misconception")
        heavy["map"]["concepts"][1]["item_ids"] += extra   # c2 now needs 23 minutes
        problems = lesson.time_problems({"videos": [PRE, video("v1", ["c1"], 9), video("v2", ["c2", "c3"], 30)]}, heavy)
        self.assertTrue(any("v2: its items need 23.5 minutes" in p and "split it" in p for p in problems), problems)
        light = lesson.time_problems({"videos": [PRE, video("v1", ["c1", "c2"], 18), video("v2", ["c3"], 5)]}, chapter)
        self.assertTrue(any("v2: its items need only 0.5 minutes: merge it" in p for p in light), light)

    def test_a_map_from_the_sloman_kit_is_read_too(self):
        chapter = dense_chapter(legacy=True)
        self.assertEqual({k: round(v, 2) for k, v in lesson.concept_minutes(chapter).items()}, {"c1": 8.0, "c2": 8.0, "c3": 0.5})
        self.assertEqual(lesson.teach_depth({"depth": 2}), "normal")      # an integer depth is a teacher question's, not this

    def test_the_plan_source_gives_the_content_minutes(self):
        chapter = dense_chapter()
        text = lesson._plan_source(chapter, lesson.chapter_naksha(chapter))
        self.assertIn("S2-11, the content rule", text)
        self.assertIn("14 deep items here", text)
        self.assertIn("c2 8.0", text)
        self.assertNotIn("6-8 minutes per book page", text)
        old = lesson._plan_source(dense_chapter(rule=None), lesson.chapter_naksha(dense_chapter(rule=None)))
        self.assertIn("Narration time (S2-01)", old)

    def test_an_unknown_rule_is_refused(self):
        chapter = dense_chapter(rule="words")
        with self.assertRaises(ValueError):
            lesson.length_rule(chapter)


class UnderstandingMarksTheDepth(unittest.TestCase):
    def test_the_item_schema_asks_for_the_depth_and_its_reason(self):
        self.assertEqual(ITEM_SCHEMA["properties"]["teach_depth"]["enum"], TEACH_DEPTHS)
        self.assertEqual(ITEM_SCHEMA["properties"]["deep_why"]["enum"], DEEP_WHYS)
        self.assertIn("teach_depth", ITEM_SCHEMA["required"])
        self.assertEqual(Course("t", "s", "l", "e", "Hinglish").length_rule, "pages")

    def test_a_deep_item_says_why_and_a_normal_one_does_not(self):
        from bie.brain.understanding import check_page
        from tests.test_task039_brain import item as page_item, page_value, page_with
        page = page_with((("p0001-b0001", "Cells form tissues."), ("p0001-b0002", "88")))

        def problems(**extra):
            value = page_value([page_item("i1", block_ids=["p0001-b0001"], **extra)], boilerplate=["p0001-b0002"])
            return [p for p in check_page(value, page) if "S2-11" in p]

        self.assertEqual(problems(teach_depth="deep", deep_why="graph"), [])
        self.assertEqual(problems(teach_depth="normal", deep_why=""), [])
        self.assertEqual(problems(), [])                               # a page read before S2-11: normal
        self.assertTrue(any("a deep item says why it is deep" in p for p in problems(teach_depth="deep", deep_why="")))
        self.assertTrue(any("teach_depth is not" in p for p in problems(teach_depth="normal", deep_why="story")))

    def test_the_rulebook_carries_s2_11(self):
        book = rulebook.load()
        lesson_rules = {r.id for r in book.for_section("lesson")}
        self.assertIn("S2-11", lesson_rules)
        self.assertIn("S2-11", {r.id for r in book.for_section("understand")})
        self.assertIn("vision-2026-10-21@2026-10-21.18", book.version)


if __name__ == "__main__":
    unittest.main()
