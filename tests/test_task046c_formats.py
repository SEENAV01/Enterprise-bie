"""Task 046 Part C · work D: the video path's formats locked (``bie/brain/formats.py``).

Offline: every hand-over has one definition with an id and a version; a validator at every section boundary refuses the
wrong shape naming the file, the format and the field; an older file is migrated, never hand-edited; the voice fields are
reserved for Task 047 and ``timing.build`` reads them when present; the fields the game and the notes read are named and
exist in the schemas; the passed outputs in ``tests/fixtures/passed_outputs/`` still validate after migration; CONTRACTS.md
names every format at its current version.
"""
from __future__ import annotations

import gzip
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import canvas, formats  # noqa: E402
from bie.brain.video import timing  # noqa: E402

from tests.test_task046c_coverage import CHAPTER, LESSON, PLANS, SPEC  # noqa: E402


def _chapter():
    value = json.loads(json.dumps(CHAPTER))
    value.update(schema="bie.brain.chapter-map/2", source_sha256="a" * 64, pages=[{"page": 1}, {"page": 2}], map_status="passed")
    return value


def _lesson():
    value = json.loads(json.dumps(LESSON))
    value.update(schema="bie.brain.lesson/2", course=CHAPTER["course"], rulebook_version="t", plan_status="passed", quality={})
    for v in value["videos"]:
        v.setdefault("title", "t")
    return value


class EveryFormat(unittest.TestCase):
    def test_every_hand_over_has_an_id_a_version_a_file_a_writer_and_readers(self):
        for name, fmt in formats.FORMATS.items():
            self.assertRegex(fmt.tag, r"^bie\.[a-z.-]+/\d+$", name)
            self.assertTrue(fmt.file and fmt.written_by and fmt.read_by and fmt.since, name)
            self.assertEqual(formats.tag(name), fmt.tag)
        self.assertEqual(formats.tag("lesson_plan"), "bie.brain.lesson/3")
        self.assertEqual(formats.tag("video_spec"), "bie.video-spec/1")
        self.assertEqual(canvas.SCHEMA, "bie.video-spec/1")

    def test_the_wrong_shape_stops_the_run_naming_the_file_the_format_and_the_field(self):
        chapter = _chapter()
        self.assertEqual(formats.problems("chapter_map", chapter), [])
        chapter["items"]["p001-i3"]["teachable"] = "yes"
        with self.assertRaises(formats.FormatError) as caught:
            formats.check("chapter_map", chapter, where="runs/x/chapter_map.json")
        self.assertEqual(str(caught.exception), "runs/x/chapter_map.json (bie.brain.chapter-map/2): $.items.p001-i3.teachable: boolean required")
        chapter["items"]["p001-i3"]["teachable"] = True
        chapter["map"]["concepts"] = []
        self.assertEqual(formats.problems("chapter_map", chapter), ["$.map.concepts: missing (map_status is passed)"])
        chapter["map_status"] = "failed"
        self.assertEqual(formats.problems("chapter_map", chapter), [])                     # a failed map is written too
        lesson = formats.migrate("lesson_plan", _lesson())
        self.assertEqual(formats.problems("lesson_plan", lesson), [])
        lesson["videos"][1]["beats"][2]["basis"] = "guess"
        self.assertEqual(formats.problems("lesson_plan", lesson), ["$.videos[1].beats[2].basis: enum"])
        lesson["videos"][1]["beats"][2]["basis"] = "book"
        lesson["videos"][1]["beats"][2]["part_id"] = "c09.9"
        self.assertEqual(formats.problems("lesson_plan", lesson), ["$.videos[1].beats[2].part_id: 'c09.9' is not a card part of v1"])
        spec = json.loads(json.dumps(SPEC))
        spec["scenes"][1]["captions"][0]["until"] = 5000
        self.assertIn("outside the scene's 900 frames", formats.problems("video_spec", formats.migrate("video_spec", spec))[0])
        self.assertEqual(formats.problems("render_join", {"video": "a.mp4"}), ["$: missing review"])

    def test_an_older_file_is_migrated_never_edited_by_hand_and_an_unknown_version_is_refused(self):
        lesson = _lesson()                                                     # bie.brain.lesson/2: beats without source
        self.assertNotIn("source", lesson["videos"][1]["beats"][0])
        accepted = formats.accept("lesson_plan", lesson)
        self.assertEqual(accepted["schema"], "bie.brain.lesson/3")
        self.assertEqual(accepted["videos"][1]["beats"][0]["source"], "")
        spec = formats.accept("video_spec", json.loads(json.dumps(SPEC)))     # bie.render-spec/1 → bie.video-spec/1
        self.assertEqual(spec["schema"], "bie.video-spec/1")
        old = {"schema": "bie.brain.canvas-plan/1", "fps": 30, "width": 1920, "height": 1080, "captions": True, "scenes": []}
        self.assertEqual(formats.accept("video_spec", old)["schema"], "bie.video-spec/1")
        plan = json.loads(json.dumps(PLANS["v1_s2"]))                           # a plan file before 29 October 2026: no schema
        plan.update(part_id="c01.1", nodes=[{"id": "n1", "kind": "box", "cue": ["b2", "", 0.0]}])
        self.assertEqual(formats.accept("canvas_b_plan", plan)["schema"], "bie.brain.canvas-b-plan/1")
        with self.assertRaises(formats.FormatError) as caught:
            formats.accept("lesson_plan", {"schema": "bie.brain.lesson/9", "videos": []})
        self.assertIn("is not a version this BIE can migrate", str(caught.exception))
        with self.assertRaises(formats.FormatError):
            formats.check("lesson_plan", _lesson())                              # a writer must write the current version

    def test_the_voice_fields_are_reserved_and_timing_reads_them_when_present(self):
        beats = [{"beat_id": "b1", "say": "एक दो तीन चार", "audio": {"file": "b1.wav", "duration": 2.0,
                                                                   "words": [{"w": "एक", "start": 0.0, "end": 0.4}, {"w": "तीन", "start": 1.0, "end": 1.4}]}},
                 {"beat_id": "b2", "say": "पाँच छह"}]
        voice = formats.voice_of(beats)
        self.assertEqual(list(voice), ["b1"])
        self.assertEqual(voice["b1"]["duration"], 2.0)
        self.assertEqual(voice["b1"]["words"][1], {"w": "तीन", "start": 1.0, "end": 1.4})
        self.assertEqual(formats.voice_of([{"beat_id": "b3", "say": "x", "audio": {"file": "", "duration": 0, "words": []}}]), {})
        tl = timing.build(beats, [{"scene_id": "s", "beat_ids": ["b1", "b2"]}], voice=voice)
        self.assertEqual(tl["s"]["beats"]["b1"][1], int(round(2.0 * timing.FPS)))   # the beat lasts as long as its audio
        self.assertEqual(formats.problems("lesson_plan", formats.migrate("lesson_plan", _lesson())), [])
        lesson = formats.migrate("lesson_plan", _lesson())
        lesson["videos"][1]["beats"][0]["audio"] = {"file": "b1.wav", "duration": 2.0, "words": [{"w": "x", "start": 0, "end": "soon"}]}
        self.assertEqual(formats.problems("lesson_plan", lesson), ["$.videos[1].beats[0].audio.words[0].end: number required"])
        for module in ("bie/brain/canvas.py", "bie/brain/video/world.py"):
            self.assertIn("formats.voice_of(beats)", (ROOT / module).read_text(encoding="utf-8"), module)

    def test_the_fields_the_game_and_the_notes_read_exist_in_the_formats(self):
        def known(schema, path):
            node = schema
            if ".<id>." in path:                                                # the items map: the item shape
                return known(formats.ITEM, path.split(".<id>.", 1)[1])
            for part in path.split("."):
                key = part.replace("[*]", "")
                props = node.get("properties") or {}
                if key not in props:
                    return node.get("type") == "object" and not props          # a free object (the items map): fine
                node = props[key]
                if part.endswith("[*]"):
                    if "items" not in node:
                        return node.get("type") == "object"                    # the items map, read item by item
                    node = node["items"]
            return True
        for reader, wants in formats.READERS.items():
            for name, paths in wants.items():
                for path in paths:
                    self.assertTrue(known(formats.FORMATS[name].schema, path), f"{reader}: {name} {path}")

    def test_the_validators_sit_at_every_section_boundary(self):
        wiring = {
            "bie/brain/understanding.py": ['formats.check("chapter_map", chapter'],
            "bie/brain/lesson.py": ['formats.accept("chapter_map", chapter', 'formats.check("lesson_plan", lesson'],
            "bie/brain/canvas_director.py": ['formats.accept("chapter_map", chapter', 'formats.accept("lesson_plan", lesson',
                                             'formats.check("video_spec", spec', 'formats.check("canvas_summary", summary'],
            "tools/run_brain.py": ['formats.accept("chapter_map"', 'formats.accept("lesson_plan"', 'formats.accept("video_spec"'],
            "tools/render_spec.py": ['formats.accept("video_spec"', 'formats.check("render_join"', 'formats.check("render_cost"',
                                     'formats.check("render_summary"'],
            "tools/task046c_page.py": ['formats.check("review_record"'],
            "tools/task046c_chapter_page.py": ['formats.check("chapter_review_record"'],
        }
        for path, needles in wiring.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            for needle in needles:
                self.assertIn(needle, text, f"{path}: {needle}")

    def test_the_passed_outputs_still_validate_after_migration(self):
        folder = ROOT / "tests" / "fixtures" / "passed_outputs"
        for path in sorted(folder.glob("*.json.gz")):
            passed = json.loads(gzip.open(path).read())
            if passed.get("map"):
                for iid, item in passed["map"]["items"].items():
                    self.assertEqual(formats.problems("chapter_map", {"schema": "bie.brain.chapter-map/2", "course": passed["course"],
                                                                      "source_sha256": passed.get("source_sha256") or "", "pages": [],
                                                                      "items": {iid: item}, "map": passed["map"]["map"], "map_status": "passed"}),
                                     [], f"{path.name}: {iid}")
            if passed.get("lesson"):
                for video in passed["lesson"]["videos"]:
                    beats = [dict(b) for b in video["beats"]]
                    lesson = formats.migrate("lesson_plan", {"schema": "bie.brain.lesson/2", "course": passed["course"], "rulebook_version": "x",
                                                             "plan_status": "passed", "plan": passed["lesson"]["plan"], "quality": {},
                                                             "videos": [{"video_id": video["video_id"], "title": video["title"], "status": "passed",
                                                                         "card_parts": [{"part_id": p, "type": "", "item_ids": []}
                                                                                        for p in sorted({b["part_id"] for b in beats if b["part_id"]})],
                                                                         "beats": beats}]})
                    self.assertEqual(formats.problems("lesson_plan", lesson), [], f"{path.name}: {video['video_id']}")

    def test_contracts_names_every_format_at_its_version_and_the_change_rule(self):
        text = (ROOT / "docs" / "bie" / "CONTRACTS.md").read_text(encoding="utf-8")
        for name, fmt in formats.FORMATS.items():
            self.assertIn(f"`{fmt.tag}`", text, name)
        self.assertIn("bump", text.lower())
        self.assertIn("tests/fixtures/passed_outputs", text)
        for reader in formats.READERS:
            self.assertIn(reader.split(" (")[0], text)
        table = formats.describe()
        self.assertTrue(table.startswith("| Hand-over | Schema |"))
        self.assertEqual(len(re.findall(r"^\| \w", table, flags=re.M)) - 1, len(formats.FORMATS))


if __name__ == "__main__":
    unittest.main()
