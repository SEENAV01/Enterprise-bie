"""Dikhaya-bola, the shown-said check (Navin, 5 November 2026: "Boli cheez usi line mein"): every thing a line names is
on screen during that line, or the compiler returns the plan naming the line and the word.

Offline (the box rule's Node measure runs in the same compile, as on the VM and the runners).
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain.show_director import payload_of, run_show_director, video_step  # noqa: E402
from bie.brain.video import narration, showplan, shown_said as ss  # noqa: E402

from tests.test_p1_show_director import BOOK, COURSE, LESSON, runner_of  # noqa: E402

VIDEO = LESSON["videos"][0]          # l1 "रामू के पास गेहूँ है।", l2 "मोहन के पास कपड़ा है।", l3 "दोनों बदल लेते हैं।"


def timeline():
    return narration.Timeline(narration.script_of(VIDEO))


def plan_of(*steps):
    base = [{"op": "person", "id": "ramu", "look": "ramu", "x": 420},
            {"op": "item", "thing": {"draw": "sack", "p": {"w": 230, "label": "गेहूँ"}}, "x": 1300, "y": 885}]
    return {"schema": "bie.scene-plan/1", "video": "v9",
            "scenes": [{"id": "A", "lines": ["l1", "l2", "l3"], "bg": "paper", "cam": [], "steps": base + list(steps)}]}


def said_problems(plan):
    try:
        showplan.compile_plan(json.loads(json.dumps(plan)), timeline(), width=1920, height=1080, language="Hinglish")
    except showplan.PlanProblems as exc:
        return [p for p in exc.problems if "dikhaya-bola" in p]
    return []


L2 = {"t0": {"line": "l2", "edge": "start"}, "t1": {"line": "l2", "edge": "end"}}


class Words(unittest.TestCase):
    def test_the_lexicon_holds_things_not_ideas_or_diagrams(self):
        lex = ss.lexicon()
        for word in ("गेहूँ", "कपड़ा", "डॉलर", "बैंक", "सिक्का", "तिजोरी", "dollar", "gold"):
            self.assertIn(word, lex, word)
        for word in ("पैसा", "सही", "माँग", "दाम", "बचत", "भुगतान", "money"):
            self.assertNotIn(word, lex, word)
        named = {n for names in lex.values() for n in names}
        for diagram in ("timeline", "graph", "mark", "fork", "gauge", "world"):
            self.assertNotIn(diagram, named)

    def test_hindi_endings_and_english_plurals_match_but_a_different_word_does_not(self):
        tags = lambda text: [tag for _, tag, _ in ss.named_things(text)]     # noqa: E731
        self.assertIn("नोट", tags("दस नोटों का बंडल"))
        self.assertIn("रुपया", tags("सौ रुपये"))
        self.assertIn("बैंक", tags("दोनों बैंकों में"))
        self.assertIn("dollar", tags("Dollars की माँग"))
        self.assertEqual(tags("नोट जारी हुए"), ["नोट"])                       # जारी (issued) is not जार (a jar)
        self.assertEqual(tags("नोटों की गड्डी आई")[0], "नोटों की गड्डी")       # the phrase before its words


class CompilerRefuses(unittest.TestCase):
    def test_a_named_thing_missing_from_its_line_is_named_with_the_line_and_the_word(self):
        problems = said_problems(plan_of())
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("line l2", problems[0])
        self.assertIn("'कपड़ा'", problems[0])
        self.assertIn("clothRoll", problems[0])

    def test_the_thing_on_screen_during_its_line_passes(self):
        plan = plan_of({"op": "item", "thing": {"draw": "clothRoll", "p": {}}, "x": 960, "y": 640, **L2})
        self.assertEqual(said_problems(plan), [])

    def test_a_thing_held_by_a_person_shows_it(self):
        plan = plan_of({"op": "hold", "who": "ramu", "t": {"line": "l2", "edge": "start"},
                        "thing": {"draw": "clothRoll", "p": {"w": 120}, "y": 37.5}})
        self.assertEqual(said_problems(plan), [])

    def test_a_thing_whose_own_label_carries_the_word_shows_it(self):
        plan = plan_of({"op": "item", "thing": {"draw": "sack", "p": {"w": 230, "label": "कपड़ा"}}, "x": 960, "y": 885, **L2})
        self.assertEqual(said_problems(plan), [])

    def test_the_word_as_text_alone_is_not_the_thing(self):
        plan = plan_of({"op": "text", "text": "कपड़ा", "x": 960, "y": 300, "size": 56, "style": "pill", **L2})
        self.assertEqual(len(said_problems(plan)), 1)

    def test_a_thing_shown_only_on_another_line_does_not_count(self):
        plan = plan_of({"op": "item", "thing": {"draw": "clothRoll", "p": {}}, "x": 960, "y": 640,
                        "t0": {"line": "l3", "edge": "start"}})
        self.assertEqual(len(said_problems(plan)), 1)

    def test_the_switch_freezes_the_demo_only(self):
        spec = showplan.compile_plan(json.loads(json.dumps(plan_of())), timeline(), width=1920, height=1080,
                                     said_shown=False)
        self.assertTrue(spec["scenes"])


class FairerWords(unittest.TestCase):
    """Pilot ch02 v1 (Sloman): ~60% of 82 said-not-shown hits were word-matching false positives."""

    def tags(self, text):
        return [tag for _, tag, _ in ss.named_things(text)]

    def test_whole_words_only_so_a_function_word_is_not_a_thing(self):
        self.assertNotIn("बस", self.tags("बस इतना ही चाहिए"))          # बस = only, not a bus
        self.assertIn("bus", self.tags("एक bus आई"))                    # the English word still names the bus
        self.assertNotIn("आग", self.tags("आगे के चित्र"))                # आगे is not आग + े
        self.assertIn("आग", self.tags("घर में आग लगी"))
        self.assertFalse(ss.has_word("bus stand", "बस"))
        self.assertFalse(ss.has_word("आगे", "आग"))
        self.assertTrue(ss.has_word("नोटों की गड्डी", "नोट"))
        self.assertFalse(ss.has_word("नोटबंदी", "नोट"))                 # inside another word is not the word

    def test_ordinary_and_idea_words_create_no_obligation(self):
        lex = ss.lexicon()
        for word in ("बीच", "दिन", "काम", "कमाई", "गिनी", "बिंदु", "चित्र", "रेखा", "समय", "साल", "income", "effect", "table"):
            self.assertNotIn(word, lex, word)
        self.assertEqual(self.tags("दिन भर का काम, कुल कमाई और income effect"), [])
        for word in ("आलू", "कॉफ़ी", "घड़ी", "laptop", "बोरी"):            # real things stay obliged
            self.assertIn(word, lex, word)

    def test_a_phrase_tag_needs_its_whole_words(self):
        self.assertEqual(self.tags("नोटों की गड्डी आई")[0], "नोटों की गड्डी")
        self.assertNotIn("नोटों की गड्डी", self.tags("नोटों की गड्डियाँनुमा"))


class StepsShowToo(unittest.TestCase):
    """The gold Money v2 craft: a thing's label changes on the cue word; that change shows the word from then on."""

    def test_a_label_changed_by_a_step_on_its_line_shows_the_word(self):
        plan = plan_of({"op": "item", "thing": {"draw": "sack", "p": {"w": 230, "label": "नमक"}}, "x": 960, "y": 885,
                        "steps": [{"t": {"line": "l2", "edge": "start"}, "p": {"label": "कपड़ा"}}]})
        self.assertEqual(said_problems(plan), [])

    def test_a_label_step_after_the_line_does_not_count(self):
        plan = plan_of({"op": "item", "thing": {"draw": "sack", "p": {"w": 230, "label": "नमक"}}, "x": 960, "y": 885,
                        "steps": [{"t": {"line": "l3", "edge": "start"}, "p": {"label": "कपड़ा"}}]})
        self.assertEqual(len(said_problems(plan)), 1)

    def test_a_graph_title_set_by_a_step_is_read(self):
        graph = {"draw": "graph", "p": {"w": 900, "title": ""}}
        step = {"t": {"line": "l2", "edge": "start"}, "p": {"title": "कपड़ा का भाव"}}
        plan = plan_of({"op": "item", "thing": graph, "x": 1000, "y": 480, "steps": [step]})
        self.assertEqual(said_problems(plan), [])
        self.assertIn("कपड़ा", ss._labels({"draw": "graph", "p": {"title": ""}, "steps": [dict(step, t=1.0)]}, 2.0))
        self.assertNotIn("कपड़ा", ss._labels({"draw": "graph", "p": {"title": ""}, "steps": [dict(step, t=1.0)]}, 0.5))


class Measure(unittest.TestCase):
    def test_the_summary_counts_lines_that_name_things(self):
        spec = showplan.compile_plan(json.loads(json.dumps(plan_of())), timeline(), width=1920, height=1080,
                                     said_shown=False)
        summary = ss.summary(ss.rows(spec, timeline()))
        self.assertEqual((summary["lines"], summary["lines_naming_things"], summary["lines_shown"]), (3, 2, 1))
        self.assertEqual(summary["said_shown_pct"], 50.0)
        self.assertEqual(summary["missing"][0]["line"], "l2")


class DirectorKnows(unittest.TestCase):
    def test_each_line_of_the_payload_names_its_things_and_the_prompt_carries_the_rule(self):
        T = timeline()
        lines = {line["id"]: line for line in payload_of(VIDEO, T, None)["lines"]}
        self.assertEqual(lines["l2"]["names"][0]["word"], "कपड़ा")
        self.assertIn("clothRoll", lines["l2"]["names"][0]["show_one_of"])
        self.assertEqual(lines["l3"]["names"], [])
        self.assertIn("DIKHAYA-BOLA", video_step(COURSE, VIDEO, T, rulebook=BOOK).system)

    def test_the_run_reports_said_shown_for_each_video(self):
        with tempfile.TemporaryDirectory() as folder:
            summary = run_show_director(LESSON, COURSE, runner_of(), Path(folder))
            row = summary["videos"][0]
            self.assertEqual((row["status"], row["said_shown_pct"], row["lines_naming_things"]), ("passed", 100.0, 2))
            self.assertIn("said = shown 100.0%", (Path(folder) / "SHOWPLAN.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
