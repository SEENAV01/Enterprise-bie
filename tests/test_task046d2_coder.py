"""Task 046 Part D2 addendum, point 1 (Navin, 2 November 2026): one general path for every thing a beat names.

"Drop the hand-picked list in F ... Whatever a beat names goes through the one general path: library -> icon index (incl.
Fluent Emoji) -> fetch -> if still missing, BIE's own coder makes a new SVG component from a short spec, tested and
licence-clean, and adds it to the library for every later book. The Money items appear only if the needs list asks for them."
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from bie.brain import coder, fake, formats, visual_thinking as vt  # noqa: E402
from bie.brain.assets import AssetLibrary  # noqa: E402
from bie.toolbox import icons, licence  # noqa: E402

GOOD = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!-- a note -->'
        '<defs><linearGradient id="g"><stop offset="0" stop-color="#ffd166"/><stop offset="1" stop-color="#f4a261"/></linearGradient></defs>'
        '<rect x="96" y="160" width="320" height="200" rx="24" fill="url(#g)" stroke="#2d3640" stroke-width="12"/>'
        '<circle cx="256" cy="260" r="48" fill="#2a9d8f" stroke="#2d3640" stroke-width="10"/>'
        '<path d="M140 200 L200 200" stroke="#2d3640" stroke-width="10"/></svg>')
NEEDS = {"schema": "bie.brain.needs/1", "missing_capabilities": [], "needs": [
    {"thing": "test tube rack", "beats": ["b1", "b4"], "kind": "icon", "sources_tried": ["icon-index"], "part": "v1_s1", "video": "v1"},
    {"thing": "bicycle bell", "beats": ["b2"], "kind": "image", "sources_tried": ["asset-library"], "part": "v1_s1", "video": "v1"},
    {"thing": "Sweden", "beats": ["b3"], "kind": "icon", "sources_tried": [], "part": "v1_s2", "video": "v1"},
    {"thing": "farmer with plough", "beats": ["b3"], "kind": "icon", "sources_tried": [], "part": "v1_s2", "video": "v1"},
    {"thing": "village map", "beats": ["b5"], "kind": "icon", "sources_tried": [], "part": "v1_s2", "video": "v1"},
    {"thing": "a bank kit", "beats": ["b6"], "kind": "world kit", "sources_tried": [], "part": "v1_s2", "video": "v1"},
    {"thing": "test tube rack", "beats": ["b7"], "kind": "icon", "sources_tried": [], "part": "v1_s3", "video": "v1"}]}


class SvgChecks(unittest.TestCase):
    def test_a_plain_drawing_passes_and_is_stored_clean(self):
        self.assertEqual(coder.svg_problems(GOOD), [])
        clean = coder.clean_svg(GOOD)
        self.assertNotIn("<!--", clean)
        self.assertIn('width="512"', clean)
        self.assertEqual(coder.svg_problems(clean), [])

    def test_scripts_links_images_styles_words_and_outside_references_are_refused(self):
        bad = {
            "script": GOOD.replace("</svg>", "<script>alert(1)</script></svg>"),
            "image": GOOD.replace("</svg>", '<image href="https://x.example/a.png" width="10" height="10"/></svg>'),
            "text": GOOD.replace("</svg>", '<text x="10" y="20">₹500</text></svg>'),
            "style": GOOD.replace('rx="24"', 'rx="24" style="fill:red"'),
            "event": GOOD.replace('rx="24"', 'rx="24" onload="x()"'),
            "outside url": GOOD.replace('fill="url(#g)"', 'fill="url(https://x.example/a.svg#g)"'),
            "xlink": GOOD.replace('<svg xmlns="http://www.w3.org/2000/svg"', '<svg xmlns="http://www.w3.org/2000/svg" '
                                  'xmlns:xlink="http://www.w3.org/1999/xlink"').replace('<circle ', '<circle xlink:href="#g" '),
            "entity": '<!DOCTYPE svg [<!ENTITY a "aaaa">]>' + GOOD,
            "missing id": GOOD.replace('fill="url(#g)"', 'fill="url(#nope)"'),
            "not square": GOOD.replace('viewBox="0 0 512 512"', 'viewBox="0 0 1024 256"'),
            "not svg": "<html><body/></html>",
            "too few shapes": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><circle cx="1" cy="1" r="1" fill="#000"/></svg>',
            "blank": ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect x="1" y="1" width="9" height="9" fill="none"/>'
                      '<circle cx="50" cy="50" r="9" fill="white"/><path d="M0 0 L9 9" fill="none" stroke="none"/></svg>'),
            "too big": GOOD.replace("</svg>", "<g>" + '<path d="M0 0 L1 1"/>' * 2000 + "</g></svg>"),
        }
        for name, text in bad.items():
            with self.subTest(name):
                self.assertNotEqual(coder.svg_problems(text), [], name)
        self.assertIn("no words", " ".join(coder.svg_problems(bad["text"])))

    def test_the_coder_draws_things_never_people_names_maps_or_kits(self):
        verdicts = {n["thing"]: coder.wants(n)[0] for n in NEEDS["needs"]}
        self.assertEqual(verdicts, {"test tube rack": True, "bicycle bell": True, "Sweden": False, "farmer with plough": True,
                                    "village map": False, "a bank kit": False})
        self.assertFalse(coder.wants({"thing": "portrait of a king", "kind": "image"})[0])
        self.assertFalse(coder.wants({"thing": "राजा", "kind": "icon"})[0])
        self.assertFalse(coder.wants({"thing": "2024 timeline marker", "kind": "icon"})[0])        # text on screen, not a picture
        self.assertFalse(coder.wants({"thing": "payment acceptance tick", "kind": "icon"})[0])     # a mark the blocks draw
        self.assertTrue(coder.wants({"thing": "10 kg grain sack", "kind": "icon"})[0])            # a sack; its number is text


class CoderRun(unittest.TestCase):
    def runner(self, tmp):
        import test_task046_canvas_director as T
        return T.runner(tmp)

    def test_the_coder_draws_each_missing_thing_once_checks_it_and_writes_its_provenance(self):
        tmp = Path(tempfile.mkdtemp())
        made = coder.run_coder(NEEDS, self.runner(tmp), tmp, course={"title": "Lab work", "subject": "Science", "learners": "class 8"})
        formats.check("coder_made", made, where="made.json")
        self.assertEqual(sorted(i["thing"] for i in made["items"]), ["bicycle bell", "farmer with plough", "test tube rack"])
        rack = next(i for i in made["items"] if i["thing"] == "test tube rack")
        self.assertEqual(rack["beats"], ["b1", "b4", "b7"])                       # the same thing once, with all its beats
        self.assertEqual(rack["status"], "passed")
        svg = (tmp / rack["file"]).read_text(encoding="utf-8")
        self.assertEqual(coder.svg_problems(svg), [])
        self.assertEqual(rack["sha256"], hashlib.sha256(svg.encode("utf-8")).hexdigest())
        self.assertTrue(rack["generated_by"] and rack["generated_on"] and "test tube rack" in rack["prompt"])
        self.assertIn("test tube rack", rack["tags"])
        self.assertEqual({s["thing"] for s in made["skipped"]}, {"Sweden", "village map", "a bank kit"})
        self.assertEqual(made["quality"]["made"], 3)
        self.assertTrue((tmp / "MADE.md").exists() and (tmp / "made.json").exists())

    def test_a_thing_the_library_holds_is_not_drawn_again(self):
        tmp = Path(tempfile.mkdtemp())
        lib = AssetLibrary(tmp / "lib")
        lib.add_bytes(GOOD.encode("utf-8"), mime="image/svg+xml", source="bie_coder", title="rack", page_url="", licence=coder.LICENCE,
                      licence_url=coder.LICENCE_URL, author=coder.AUTHOR, credit="", tags=["test tube rack", "test", "tube", "rack"],
                      generated_by="g", prompt="p", generated_on="2026-11-02")
        made = coder.run_coder(NEEDS, self.runner(tmp / "run"), tmp / "run", library=lib)
        self.assertEqual(made["in_library"], ["test tube rack"])
        self.assertNotIn("test tube rack", [i["thing"] for i in made["items"]])

    def test_a_refused_drawing_goes_back_with_its_problems_and_is_never_written(self):
        tmp = Path(tempfile.mkdtemp())
        r = self.runner(tmp)
        real = fake.coder_answer
        try:
            fake.coder_answer = lambda user: dict(real(user), svg=GOOD.replace("</svg>", "<text>x</text></svg>"))
            made = coder.run_coder({"schema": "bie.brain.needs/1", "missing_capabilities": [],
                                    "needs": [NEEDS["needs"][0]]}, r, tmp, max_rounds=2)
        finally:
            fake.coder_answer = real
        item = made["items"][0]
        self.assertEqual((item["status"], item["rounds"], item.get("file")), ("failed", 2, None))
        rec = json.loads((tmp / "records" / f"coder--{item['slug']}.json").read_text(encoding="utf-8"))
        self.assertIn("no words", json.dumps(rec["rounds"][0].get("code_problems"), ensure_ascii=False))
        self.assertEqual(list((tmp / "made").iterdir()), [])


class IntoTheLibrary(unittest.TestCase):
    def test_a_made_drawing_joins_the_library_licence_clean_with_its_provenance_for_every_later_book(self):
        tmp = Path(tempfile.mkdtemp())
        import test_task046_canvas_director as T
        made = coder.run_coder(NEEDS, T.runner(tmp / "run"), tmp / "run")
        lib = AssetLibrary(tmp / "lib")
        result = coder.add_made(made, tmp / "run", lib)
        self.assertEqual(len(result["added"]), 3)
        self.assertEqual(result["refused"], [])
        ids = [a["asset_id"] for a in result["added"]]
        self.assertEqual(lib.lesson_check(ids), [])                               # the licence gate a lesson calls
        asset = lib.assets[ids[0]]
        self.assertEqual(asset.source, "bie_coder")
        self.assertTrue(asset.generated_by and asset.prompt and asset.generated_on)
        self.assertEqual(licence.asset_verdict(asset).licence_class, "generated")
        # a later book's visual thinking finds the library picture for the same thing
        found = vt.resolve_needs({"beats": [{"beat_id": "b1", "things": ["test tube rack"]}]}, lib)
        self.assertTrue(found["images"].get("test tube rack"))
        self.assertEqual(found["needs"], [])
        # a file that changed after the coder made it is refused
        item = next(i for i in made["items"] if i.get("file"))
        (tmp / "run" / item["file"]).write_text(GOOD, encoding="utf-8")
        again = coder.add_made(made, tmp / "run", AssetLibrary(tmp / "lib2"))
        self.assertTrue(any("sha256" in r["why"] for r in again["refused"]))

    def test_the_fetch_tool_adds_a_coder_run_to_the_library(self):
        import task046d_fetch_needs as F
        tmp = Path(tempfile.mkdtemp())
        import test_task046_canvas_director as T
        coder.run_coder(NEEDS, T.runner(tmp / "run"), tmp / "run")
        self.assertEqual(F.main(["--made", str(tmp / "run" / "made.json"), "--library", str(tmp / "lib")]), 0)
        report = json.loads((tmp / "lib" / "made-added.json").read_text(encoding="utf-8"))
        self.assertEqual(report["counts"], {"added": 3, "refused": 0})


class GeneralPath(unittest.TestCase):
    def test_the_hand_made_money_drawings_are_retired(self):
        self.assertFalse((ROOT / "bie" / "toolbox" / "icons" / "bie").exists())
        self.assertFalse((ROOT / "tools" / "bie_objects.py").exists())
        self.assertEqual([r["id"] for r in icons.load()["icons"] if r["id"].startswith("bie:")], [])
        self.assertEqual(sorted(i for ids in icons.ALIASES.values() for i in ids if i.startswith("bie:")), [])
        self.assertEqual(icons.check_ids(["bie:cheque", "bie:salt-sack"]), ["bie:cheque", "bie:salt-sack"])

    def test_a_thing_no_icon_is_a_picture_of_is_a_need_not_a_near_word(self):
        ideas = {"beats": [{"beat_id": "b1", "things": ["bicycle", "sack of salt", "payment claim", "test tube rack"]}]}
        found = vt.resolve_needs(ideas, None)
        self.assertIn("bicycle", found["found"])
        self.assertEqual(sorted(n["thing"] for n in found["needs"]), ["payment claim", "sack of salt", "test tube rack"])

    def test_money_appears_only_when_the_needs_ask_for_it(self):
        # the coder's card names no thing of one chapter; a money thing is drawn only because a need named it
        card = coder.card().lower()
        for word in ("salt", "cattle", "cowrie", "cheque", "passbook", "upi", "qr"):
            self.assertNotIn(word, card)
        made = coder.run_coder({"schema": "bie.brain.needs/1", "missing_capabilities": [], "needs": [
            {"thing": "grain sack", "beats": ["b1"], "kind": "icon", "sources_tried": []}]},
            __import__("test_task046_canvas_director").runner(Path(tempfile.mkdtemp())), Path(tempfile.mkdtemp()))
        self.assertEqual([i["thing"] for i in made["items"]], ["grain sack"])


class ProofVideos(unittest.TestCase):
    def test_the_two_other_videos_are_chosen_by_code_never_v1_v2_v4_or_the_prerequisite(self):
        import task046d2_pick_videos as P
        beat = lambda say: {"beat_id": "b", "say": say}                                        # noqa: E731
        lesson = {"plan": {"videos": [{"video_id": "v0", "kind": "prerequisites"}] + [{"video_id": f"v{i}", "kind": "topic"} for i in range(1, 7)]},
                  "videos": [{"video_id": "v0", "status": "passed", "beats": [beat("telescope microscope prism lens mirror")]},
                             {"video_id": "v1", "status": "passed", "beats": [beat("salt cloth wheat")]},
                             {"video_id": "v2", "status": "passed", "beats": [beat("salt cattle shells")]},
                             {"video_id": "v3", "status": "passed", "beats": [beat("salt bicycle"), beat("bicycle")]},
                             {"video_id": "v4", "status": "passed", "beats": [beat("paper note")]},
                             {"video_id": "v5", "status": "passed", "beats": [beat("test tube beaker flask burner")]},
                             {"video_id": "v6", "status": "failed", "beats": [beat("rocket satellite orbit moon planet")]}]}
        out = P.pick(lesson)
        self.assertEqual(out["chosen"], ["v5", "v3"])            # most words v1, v2, v4 never say; failed and prerequisite videos left out
        self.assertEqual(P.pick(lesson), out)                    # the same answer every time


if __name__ == "__main__":
    unittest.main()
