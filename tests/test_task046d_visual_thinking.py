"""Task 046 Part D1 · dikhane ki soch, the needs list, the world choice and the D1 checks (Navin's verdict on the Money videos,
30 October 2026: "ek hi setup ... bank 4 admi aur screen par ubharta text"; "jo bola ja rha hai screen ke visuals se wo baat
clear ho"; "background mein ek check hai, visuals par to yeh cheejen na dikhe").

Offline: fixtures shaped like the Money chapter map's book pictures (the Evolution-of-Money panel, the page-4 timelines, the
coin-limit table, a payment flow; test inputs, not lesson content), the fake maker, fake sources and a fake reviewer. No
network, no keys, no money.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from bie.brain import assets, canvas, canvas_director as cd, formats, look, rulebook, visual_thinking as vt  # noqa: E402
from bie.brain.video import screen_text, world  # noqa: E402
from bie.toolbox import icons  # noqa: E402


def _tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def item(iid, kind, content, *, parent="", page=2, ct="timeline", where=""):
    return {"item_id": iid, "kind": kind, "content": content, "content_type": ct, "page": page, "teachable": True,
            "parent_item_id": parent, "where_on_page": where, "teacher_understanding": []}


ITEMS = {i["item_id"]: i for i in [
    item("p002-i12", "diagram", "EVOLUTION OF MONEY. Six numbered illustrations connected by right-pointing arrows: 1. BARTER → 2. COMMODITY MONEY"),
    item("p002-i13", "diagram_label", "1. BARTER | Wheat exchanged for cloth. Points to two people exchanging wheat and cloth.", parent="p002-i12"),
    item("p002-i14", "diagram_label", "2. COMMODITY MONEY | Salt, cattle, shells. Points to a bag of salt.", parent="p002-i12"),
    item("p002-i15", "diagram_label", "3. METALLIC MONEY | Gold and silver coins. Points to coins.", parent="p002-i12"),
    item("p002-i17", "diagram_label", "5. BANK MONEY | Cheques and deposits. Points to a bank and a cheque.", parent="p002-i12"),
    item("p004-i3", "diagram", "A horizontal timeline connects four dots: 1661—Sweden, First banknotes; 1816—Britain, Gold Standard.", page=4),
    item("p004-i4", "diagram_label", "1661 | Sweden | First banknotes", parent="p004-i3", page=4),
    item("p004-i5", "diagram_label", "1816 | Britain | Gold Standard", parent="p004-i3", page=4),
    item("p004-i17", "diagram", "A horizontal line links chronological dots: 7th c.—Tang, Receipts; 1275—Yuan, Compulsory.", page=4),
    item("p004-i18", "diagram_label", "7th c. | Tang | Receipts", parent="p004-i17", page=4),
    item("p004-i20", "diagram_label", "1275 | Yuan | Compulsory", parent="p004-i17", page=4),
    item("p005-i7", "table", "Current legal limits for coins (Coinage Act, 2011). Columns: Coin | Legal Tender Limit. Rows follow.", page=5, ct="figure"),
    item("p005-i9", "table_row", "Coin: ₹1, ₹2, ₹5, ₹10, ₹20 coins | Legal Tender Limit: Up to ₹1,000", parent="p005-i7", page=5, ct="facts_numbers"),
    item("p005-i10", "table_row", "Coin: 50 paise coin | Legal Tender Limit: Up to ₹10", parent="p005-i7", page=5, ct="facts_numbers"),
    item("p013-i7", "diagram", "Four rounded boxes joined by rightward arrows: Rahul / UPI App → Rahul's Bank → NPCI / UPI Switch → Merchant's Bank. Below: a caption.",
         page=13, ct="process"),
    item("p013-i8", "diagram_label", "Rahul / UPI App — the payer's app", parent="p013-i7", page=13, ct="process"),
]}


def beat(bid, say, covers=()):
    return {"beat_id": bid, "say": say, "covers_item_ids": list(covers)}


class Verbs(unittest.TestCase):
    def test_the_rulebook_of_visual_verbs_names_how_each_relation_is_shown(self):
        verbs = vt.load_verbs()
        self.assertEqual(verbs["version"], "2026-10-31.1")
        ids = vt.relations()
        for r in ("reject", "accept", "compulsory", "limit", "more_less", "count", "sequence", "cause_effect", "compare", "part_whole",
                  "place", "change", "promise", "question", "other"):
            self.assertIn(r, ids)
        self.assertIn("cross", vt.relation_entry("reject")["show"])
        self.assertEqual(vt.guess_relation("पुराना सिक्का अब नहीं चलता, reject हो गया"), "reject")
        self.assertEqual(vt.guess_relation("₹1,000 तक की सीमा है"), "limit")
        book = rulebook.load()
        self.assertIn("visual_verbs@2026-10-31.1", book.version)
        canvas_rules = {r.id for r in book.for_section("canvas")}
        self.assertTrue({"D1-01", "D1-02", "D1-03", "D1-04", "D1-05", "D1-06", "VG-07", "VG-10"} <= canvas_rules)


class IconSearch(unittest.TestCase):
    def test_the_cross_is_the_cross_mark_and_wheat_finds_the_sheaf(self):
        self.assertEqual(icons.search("cross")[0]["id"], "tw:274c")
        self.assertNotIn("tw:2626", [r["id"] for r in icons.search("cross")])                 # never a religious cross unasked
        self.assertIn("tw:2626", [r["id"] for r in icons.search("orthodox cross religious symbol")])
        self.assertEqual(icons.search("wheat")[0]["id"], "tw:1f33e")
        self.assertEqual(icons.search("गेहूँ के बदले कपड़ा")[0]["id"], "tw:1f33e")
        self.assertEqual(icons.search("Cheques and deposits")[0]["id"], "fa:solid/money-check")
        self.assertEqual(icons.search("किसान")[0]["id"], "tw:1f9d1-200d-1f33e")
        self.assertEqual(icons.search("warehouse")[0]["id"], "fa:solid/warehouse")                  # whole words: not a house
        self.assertEqual(icons.check_ids(sorted({i for ids in icons.ALIASES.values() for i in ids})), [])
        self.assertEqual(icons.search_nouns(["salt", "zorblatt"]), {"salt": icons.search("salt", limit=3), "zorblatt": []})


class BookPictures(unittest.TestCase):
    def test_code_draws_the_book_picture_a_part_covers_as_itself(self):
        gallery = vt.picture_of(ITEMS, ["p002-i13", "p002-i14"], "timeline")
        self.assertEqual((gallery["type"], gallery["by"]), ("gallery", "book"))
        panels = gallery["pictures"][0]["data"]["panels"]
        self.assertEqual([p["name"] for p in panels], ["BARTER", "COMMODITY MONEY", "METALLIC MONEY", "BANK MONEY"])
        self.assertEqual(vt.panel_icon(panels[0]), "tw:1f33e")                                    # wheat exchanged for cloth → the sheaf
        timeline = vt.picture_of(ITEMS, ["p004-i4"])
        self.assertEqual(timeline["type"], "timeline")
        events = timeline["pictures"][0]["data"]["events"]
        self.assertEqual([(e["when"], e["name"], e["detail"]) for e in events], [("1661", "Sweden", "First banknotes"), ("1816", "Britain", "Gold Standard")])
        table = vt.picture_of(ITEMS, ["p005-i9"])
        self.assertEqual(table["type"], "table")
        self.assertEqual(table["pictures"][0]["data"]["columns"], ["Coin", "Legal Tender Limit"])
        self.assertEqual(table["pictures"][0]["data"]["rows"][0]["cells"], ["₹1, ₹2, ₹5, ₹10, ₹20 coins", "Up to ₹1,000"])
        flow = vt.picture_of(ITEMS, ["p013-i8"])
        self.assertEqual(flow["type"], "flow")
        self.assertEqual([n["label"] for n in flow["pictures"][0]["data"]["nodes"]], ["Rahul / UPI App", "Rahul's Bank", "NPCI / UPI Switch", "Merchant's Bank"])
        none = vt.picture_of(ITEMS, [], "comparison")
        self.assertEqual((none["type"], none["by"]), ("table", "card"))

    def test_two_book_pictures_in_one_part_take_turns_and_every_one_compiles(self):
        beats = [beat("b1", "पहले Tang के receipts आए।", ["p004-i18"]), beat("b2", "1275 में Yuan ने compulsory किया।", ["p004-i20"]),
                 beat("b3", "1661 में Sweden में पहले banknotes आए।", ["p004-i4"]), beat("b4", "1816 में Britain ने Gold Standard अपनाया।", ["p004-i5"])]
        picture, nodes = vt.place_pictures(ITEMS, beats, "timeline")
        self.assertEqual([n["picture"]["item_id"] for n in nodes], ["p004-i17", "p004-i3"])
        self.assertEqual(nodes[0]["until_cue"], ["b3", ""])                                        # the first leaves as the second arrives
        self.assertEqual([e["cue"][0] for e in nodes[1]["picture"]["events"]], ["b3", "b4"])
        plan = {"id": "v4_s3", "part_id": "c09.3", "theme": "paper", "grid": [12, 8], "touches": True,
                "beats": [{"beat_id": b["beat_id"], "say": b["say"]} for b in beats], "nodes": nodes}
        scene, report = canvas.compile_plan(plan)
        self.assertEqual(report["peak_visible"], 1)                                                # one anchor picture, counted once
        texts = [e.get("text") for e in scene["layers"][0]["data"]["elements"] if e["kind"] == "text"]
        self.assertIn("7th c. Tang", texts)
        self.assertIn("1661 Sweden", texts)
        self.assertEqual(vt.book_picture_problems(plan, picture), [])
        self.assertEqual(len(vt.book_picture_problems(dict(plan, nodes=nodes[:1]), picture)), 1)
        for pid in ("p002-i13", "p005-i9", "p013-i8"):
            pic, nodes = vt.place_pictures(ITEMS, [beat("b1", "यहाँ कुछ बात।", [pid]), beat("b2", "आगे की बात।")])
            canvas.compile_plan(dict(plan, beats=[{"beat_id": "b1", "say": "यहाँ कुछ बात।"}, {"beat_id": "b2", "say": "आगे की बात।"}], nodes=nodes))


class Checks(unittest.TestCase):
    def setUp(self):
        self.beats = [{"beat_id": "b1", "say": "पुराना सिक्का अब नहीं चलता।"}, {"beat_id": "b2", "say": "नया नोट चलता है।"}]

    def plan(self, nodes):
        return {"id": "p", "part_id": "c1", "theme": "paper", "grid": [12, 8], "touches": True, "beats": self.beats, "nodes": nodes}

    def test_every_beat_shows_a_thing_and_text_alone_is_refused(self):
        only_text = self.plan([{"id": "t1", "kind": "text", "style": "box", "text": "पुराना सिक्का", "cell": [0, 0, 6, 1], "cue": ["b1", "पुराना"]},
                               {"id": "t2", "kind": "text", "style": "box", "text": "नया नोट", "cell": [6, 0, 6, 1], "cue": ["b2", "नया"]}])
        self.assertIn("b1, b2 show nothing but text", vt.beat_cover_problems(only_text, self.beats, "B")[0])
        shown = self.plan([{"id": "c", "kind": "icon", "icon": "tw:1fa99", "label": "सिक्का", "cell": [0, 0, 3, 3], "cue": ["b1", "सिक्का"]},
                           {"id": "x", "kind": "mark", "mark": "cross", "target": "c", "cue": ["b1", "नहीं"]},
                           {"id": "n", "kind": "icon", "icon": "fa:solid/money-bill-1", "label": "नोट", "cell": [6, 0, 3, 3], "cue": ["b2", "नोट"]}])
        self.assertEqual(vt.beat_cover_problems(shown, self.beats, "B"), [])
        scene, _ = canvas.compile_plan(shown)
        self.assertEqual(vt.text_only_problems(scene, 30)[0], [])
        long = [{"beat_id": "b1", "say": " ".join(["शब्द"] * 60)}]
        scene, _ = canvas.compile_plan({**self.plan([{"id": "t", "kind": "text", "style": "box", "text": "शब्द", "cell": [0, 0, 6, 1], "cue": ["b1", "शब्द"]}]),
                                        "beats": long})
        problems, seconds = vt.text_only_problems(scene, 30)
        self.assertIn("only text", problems[0])
        self.assertGreater(seconds, 10)

    def test_a_sentence_and_a_caution_line_never_reach_the_screen(self):
        texts = [{"id": "a", "text": "Legal tender एक कानूनी अनिवार्यता है जिसे मना नहीं किया जा सकता।", "role": "text"},
                 {"id": "b", "text": "सीमा ₹1,000", "role": "text"},
                 {"id": "c", "text": "Illustrative numbers", "role": "label"},
                 {"id": "d", "text": "Coins below 50 paise are no longer legal tender in India today.", "role": "book"}]
        self.assertEqual([p.split(":")[0] for p in vt.phrase_problems(texts)], ["a"])
        self.assertEqual([p.split(":")[0] for p in vt.caution_problems(texts)], ["c"])
        self.assertEqual(screen_text.text_problems("Up to ₹1,000", "", where="x", role="book"), [])   # the book's words: code placed them
        self.assertEqual((world.BOARD_LINES, world.BOARD_CHARS), (2, 28))

    def test_the_same_world_kit_never_twice_in_a_row(self):
        parts = [{"id": "a", "mode": "C", "kit": "bank"}, {"id": "b", "mode": "C", "kit": "bank"}, {"id": "c", "mode": "C", "kit": "shop"}]
        self.assertEqual(len(vt.kit_sequence_problems(parts)), 1)


class Ideas(unittest.TestCase):
    def test_the_ideas_check_reads_relations_nouns_and_words(self):
        stub = {"id": "v4_s3", "beats": [{"beat_id": "b1", "say": "Yuan ने यह compulsory किया।"}]}
        good = {"beats": [{"beat_id": "b1", "idea": "Yuan made notes compulsory", "relation": "compulsory", "relation_note": "",
                           "things": ["paper note"], "people": [], "places": ["China"], "shows": "a law scroll stamped on a note",
                           "on_word": "compulsory", "image_wanted": ""}], "picture_type": "timeline", "picture_note": ""}
        self.assertEqual(vt.check_ideas(stub, good), [])
        bad = copy.deepcopy(good)
        bad["beats"][0].update(relation="obliged", on_word="nowhere", things=[], places=[])
        problems = vt.check_ideas(stub, bad)
        self.assertEqual(len(problems), 3, problems)
        other = copy.deepcopy(good)
        other["beats"][0].update(relation="other")
        self.assertIn("relation_note", vt.check_ideas(stub, other)[0])
        self.assertIn("missing: b1", vt.check_ideas(stub, {"beats": []})[0])
        book = {"type": "timeline", "by": "book", "pictures": []}
        self.assertIn("set picture_type to 'timeline'", vt.check_ideas(stub, dict(good, picture_type="table"), picture=book)[0])

    def test_the_needs_list_names_what_no_source_had_and_never_a_portrait(self):
        ideas = {"beats": [{"beat_id": "b1", "things": ["salt", "zorblatt"], "people": [], "places": [], "image_wanted": "punch-marked silver coin"},
                           {"beat_id": "b2", "things": ["coin"], "people": [], "places": [], "image_wanted": "portrait of Sher Shah Suri"}]}
        tmp = Path(tempfile.mkdtemp())
        found = vt.resolve_needs(ideas, assets.AssetLibrary(tmp / "lib"))
        self.assertIn("salt", found["found"])
        needs = {n["thing"]: n for n in found["needs"]}
        self.assertEqual(needs["zorblatt"]["kind"], "icon")
        self.assertEqual(needs["punch-marked silver coin"]["kind"], "image")
        self.assertNotIn("portrait of Sher Shah Suri", needs)                                        # card rule 8 stays

    def test_a_word_that_is_only_grammar_is_not_a_thing(self):
        # the Money dry run of 31 October 2026: fillers such as "मानिए", "यहाँ", "कितना" reached the needs list as things
        ideas = {"beats": [{"beat_id": "b1", "things": ["मानिए", "यहाँ", "silver coin"], "people": ["कितना"], "places": []}]}
        self.assertEqual(vt.nouns_of(ideas), ["silver coin"])
        stub = {"id": "v2_s1", "beats": [{"beat_id": "b1", "say": "मानिए यहाँ एक दुकान है।"}]}
        answer = {"beats": [{"beat_id": "b1", "idea": "a shop", "relation": "place", "relation_note": "", "things": ["मानिए"],
                             "people": [], "places": [], "shows": "a shop", "on_word": "दुकान", "image_wanted": ""}],
                  "picture_type": "things", "picture_note": ""}
        problems = vt.check_ideas(stub, answer)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("only grammar", problems[0])


class Director(unittest.TestCase):
    def test_a_world_only_for_the_examples_story_and_never_by_keyword(self):
        import test_task046_canvas_director as T
        bank = [{"beat_id": "b1", "say": "बैंक से कर्ज़ लेने वाले borrowers को ब्याज देना पड़ता है।"}]
        self.assertEqual(cd.mode_of(T.ECON, bank)["mode"], "B")
        story = [{"item_id": "i1", "real_world_example": dict(T.EXAMPLE, place="bank")}]
        self.assertEqual(cd.mode_of(T.ECON, bank, story, story=True)["kit"], "bank")

    def test_the_run_thinks_first_writes_the_dikhane_ki_list_and_the_needs_and_reports(self):
        import test_task046_canvas_director as T
        chapter, lesson = T.econ_lesson()
        tmp = Path(tempfile.mkdtemp())
        summary = cd.run_canvas(chapter, lesson, T.ECON, T.runner(tmp), tmp, workers=1)
        q = summary["quality"]
        self.assertEqual((q["parts"], q["parts_passed"]), (2, 2))
        for key in ("distinct_icons", "text_only_seconds", "book_pictures", "book_pictures_drawn", "world_share", "ideas_first_try", "needs"):
            self.assertIn(key, q)
        ideas = json.loads((tmp / "visual_ideas" / "v1.json").read_text(encoding="utf-8"))
        formats.check("visual_ideas", ideas)
        self.assertTrue(all(b["relation"] in vt.relations() for p in ideas["parts"] for b in p["beats"]))
        formats.check("needs", json.loads((tmp / "needs.json").read_text(encoding="utf-8")))
        self.assertTrue(list((tmp / "records").rglob("canvas--v1_s1-ideas.json")))
        page = _tool("task046d_ideas_page").build(tmp, "v1", lesson=lesson, before=tmp)
        self.assertIn("dikhane ki list", page)
        self.assertIn("Pehle aur ab", page)

    def test_a_story_world_that_covers_a_book_picture_keeps_its_world_only_when_a_canvas_part_draws_it(self):
        # the Money dry run of 31 October 2026: a world part never draws the book's picture, so a picture covered only by a world
        # part was never shown (D1-04); and the same picture in three pieces counted three times
        import test_task046_canvas_director as T

        def run(also_on_canvas):
            chapter, lesson = T.econ_lesson()
            chapter["items"].update({k: dict(ITEMS[k], teachable=True, teacher_understanding=[]) for k in ("p004-i3", "p004-i4", "p004-i5")})
            beats = lesson["videos"][0]["beats"]
            beats[0]["covers_item_ids"] = list(beats[0].get("covers_item_ids") or []) + ["p004-i4"]
            if also_on_canvas:
                curve = [b for b in beats if b["part_id"] == "p2"]
                curve[0]["covers_item_ids"] = list(curve[0].get("covers_item_ids") or []) + ["p004-i4"]
            tmp = Path(tempfile.mkdtemp())
            summary = cd.run_canvas(chapter, lesson, T.ECON, T.runner(tmp), tmp, workers=1)
            return summary["videos"][0]

        alone = run(False)
        self.assertEqual(alone["parts"][0]["mode"], "B")
        self.assertIn("D1-04", alone["parts"][0].get("note", ""))
        self.assertEqual((alone["report"]["book_pictures"], alone["report"]["book_pictures_drawn"]), (1, 1))
        shared = run(True)
        self.assertEqual((shared["parts"][0]["mode"], shared["parts"][0]["kit"]), ("C", "shop"))       # the story keeps its world
        self.assertEqual(shared["parts"][1]["mode"], "B")
        self.assertEqual((shared["report"]["book_pictures"], shared["report"]["book_pictures_drawn"]), (1, 1))   # counted once

    def test_two_story_parts_in_the_same_kit_one_after_the_other_the_second_is_a_canvas(self):
        import test_task046_canvas_director as T
        chapter, lesson = T.econ_lesson()
        video = lesson["videos"][0]
        for b in video["beats"]:
            if b["part_id"] == "p2":                                                                 # p2 becomes a second shop story
                b.update(covers_item_ids=["i1"], say=b["say"] + " दाम ₹50 से ₹65।")
        tmp = Path(tempfile.mkdtemp())
        summary = cd.run_canvas(chapter, lesson, T.ECON, T.runner(tmp), tmp, workers=1)
        modes = [(p["mode"], p.get("kit")) for p in summary["videos"][0]["parts"]]
        self.assertEqual(modes[0], ("C", "shop"))
        self.assertEqual(modes[1][0], "B")
        self.assertIn("D1-05", summary["videos"][0]["parts"][1].get("note", ""))

    def test_a_library_image_is_a_valid_asset_id_and_an_unknown_one_is_refused(self):
        tmp = Path(tempfile.mkdtemp())
        lib = assets.AssetLibrary(tmp / "lib")
        a = lib.add_bytes(b"\xff\xd8\xff\xe0jpeg", mime="image/jpeg", source="met_open_access", title="Silver coin", page_url="https://x",
                          licence="CC0 1.0", licence_url="https://creativecommons.org/publicdomain/zero/1.0/", author="The Met",
                          credit="Silver coin, The Met, CC0", tags=["silver", "coin"])
        plan = {"nodes": [{"id": "i", "kind": "icon", "icon": f"asset:{a.asset_id}"}, {"id": "j", "kind": "icon", "icon": "asset:a-0000"}]}
        self.assertEqual(cd._icon_problems(plan, lib), ["image 'asset:a-0000' is not in this lesson's asset library"])


class FetchNeeds(unittest.TestCase):
    def cand(self, title, licence, source="met_open_access"):
        return assets.Candidate(source=source, title=title, page_url="https://example.invalid/obj", file_url="https://example.invalid/f.jpg",
                                thumb_url="", width=0, height=0, mime="image/jpeg", licence=licence,
                                licence_url="https://creativecommons.org/publicdomain/zero/1.0/", author="A museum", credit=f"{title}, CC0")

    def test_the_fetch_adds_licensed_images_to_the_library_and_skips_what_it_must(self):
        fetch = _tool("task046d_fetch_needs")
        needs = {"schema": formats.tag("needs"), "missing_capabilities": [{"what": "world kit for a farm", "kind": "world kit", "parts": ["v2_s5s"], "beats": []}],
                 "needs": [{"thing": "punch-marked silver coin", "beats": ["b3"], "kind": "image", "sources_tried": []},
                           {"thing": "portrait of a king", "beats": ["b4"], "kind": "image", "sources_tried": []},
                           {"thing": "RBI vault", "beats": ["b5"], "kind": "world kit", "sources_tried": []}]}
        formats.check("needs", needs)
        sources = {"met": lambda q, limit, opener=None: [self.cand("Punch-marked coin, silver", "CC BY-SA 4.0"), self.cand("Punch-marked coin, silver", "CC0 1.0")],
                   "openverse": lambda q, limit, opener=None: [], "commons": lambda q, limit, opener=None: []}
        tmp = Path(tempfile.mkdtemp())
        lib = assets.AssetLibrary(tmp / "lib")
        with mock.patch.dict(fetch.SOURCES, sources), mock.patch.object(assets, "_open", lambda url, **kw: b"\xff\xd8\xff\xe0jpeg"):
            report = fetch.fetch(needs, lib, sources=("met", "openverse", "commons"))
        rows = {r["thing"]: r for r in report["needs"]}
        self.assertEqual(rows["punch-marked silver coin"]["status"], "fetched")
        self.assertEqual(rows["punch-marked silver coin"]["assets"][0]["licence"], "CC0 1.0")              # BY-SA refused by the policy
        self.assertIn("errors", rows["punch-marked silver coin"])
        self.assertEqual(rows["portrait of a king"]["status"], "skipped")
        self.assertEqual(rows["RBI vault"]["status"], "skipped")
        self.assertEqual(report["counts"], {"fetched": 1, "in_library": 0, "not_found": 0, "skipped": 2, "not_tried": 0})
        with mock.patch.dict(fetch.SOURCES, sources), mock.patch.object(assets, "_open", lambda url, **kw: b"\xff\xd8\xff\xe0jpeg"):
            again = fetch.fetch(needs, lib)
        self.assertEqual({r["thing"]: r["status"] for r in again["needs"]}["punch-marked silver coin"], "in_library")
        run_lib = assets.AssetLibrary(tmp / "run")
        self.assertEqual(assets.seed_library(run_lib, tmp / "lib"), 1)                                   # the next run looks here first
        found = vt.resolve_needs({"beats": [{"beat_id": "b1", "things": [], "people": [], "places": [], "image_wanted": "punch-marked silver coin"}]}, run_lib)
        self.assertEqual(len(found["images"]["punch-marked silver coin"]), 1)
        self.assertEqual(found["needs"], [])

    def test_a_slow_fetch_stops_at_its_time_budget_keeps_what_it_found_and_asks_the_museum_only_for_objects(self):
        # the first live fetch (31 October 2026) ran out of its 30-minute job with nothing saved
        fetch = _tool("task046d_fetch_needs")
        needs = {"schema": formats.tag("needs"), "missing_capabilities": [],
                 "needs": [{"thing": "silver coin", "beats": ["b1"], "kind": "image", "sources_tried": []},
                           {"thing": "payer", "beats": ["b2"], "kind": "icon", "sources_tried": []},
                           {"thing": "cowrie shells", "beats": ["b3"], "kind": "image", "sources_tried": []},
                           {"thing": "salt bag", "beats": ["b4"], "kind": "image", "sources_tried": []}]}
        asked = []
        now = [0.0]

        def met(q, limit, opener=None):
            asked.append(("met", q)); now[0] += 400
            cand = self.cand(f"{q}, CC0 object", "CC0 1.0")
            return [assets.Candidate(**{**cand.__dict__, "file_url": f"https://example.invalid/{q.replace(' ', '-')}.jpg"})]

        def openverse(q, limit, opener=None):
            asked.append(("openverse", q)); now[0] += 400
            return []

        tmp = Path(tempfile.mkdtemp())
        lib = assets.AssetLibrary(tmp / "lib")
        with mock.patch.dict(fetch.SOURCES, {"met": met, "openverse": openverse, "commons": openverse}), \
                mock.patch.object(assets, "_open", lambda url, **kw: b"\xff\xd8\xff\xe0" + url.encode()):
            report = fetch.fetch(needs, lib, deadline_s=700, clock=lambda: now[0])
        status = {r["thing"]: r["status"] for r in report["needs"]}
        self.assertEqual(status, {"silver coin": "fetched", "payer": "skipped", "cowrie shells": "fetched", "salt bag": "not_tried"})
        self.assertNotIn(("met", "payer"), asked)                                   # an icon is never a photo search
        self.assertNotIn(("openverse", "payer"), asked)
        self.assertEqual(report["counts"]["not_tried"], 1)
        self.assertEqual(len(assets.AssetLibrary(tmp / "lib").assets), 2)          # saved, not lost

    def test_a_fetched_picture_must_name_its_need_never_shows_people_and_old_mistakes_are_pruned(self):
        # the second live fetch (31 October 2026): galaxies for the years "1275" and "1023", a protest rally for "payer"
        fetch = _tool("task046d_fetch_needs")
        self.assertTrue(fetch.acceptable("punch-marked silver coin", "Punch-marked coin, silver"))
        self.assertFalse(fetch.acceptable("payer", "Counter protest for single payer health care at a Tea Party rally"))
        self.assertFalse(fetch.acceptable("1275", "NGC 1275 Hubble"))
        self.assertFalse(fetch.acceptable("cowrie shells in open palm", "Kikuyu Flag (Cowrie on Ochre)"))
        self.assertTrue(fetch.acceptable("Tibet", "Between Shigatse and Lhasa, Tibet"))
        tmp = Path(tempfile.mkdtemp())
        lib = assets.AssetLibrary(tmp / "lib")
        with mock.patch.object(assets, "_open", lambda url, **kw: b"\xff\xd8\xff\xe0" + url.encode()):
            for title, thing in (("Counter protest for single payer health care", "payer"), ("NGC 1275 Hubble", "1275"),
                                 ("Mountain of Fire - Porter Ridge Park", "porter"), ("Punch-marked coin, silver", "punch-marked silver coin")):
                cand = self.cand(title, "CC0 1.0")
                cand = assets.Candidate(**{**cand.__dict__, "file_url": f"https://example.invalid/{len(title)}.jpg"})
                lib.add_candidate(cand, tags=["fetched", "d1-need"], description=f"for '{thing}' (needs.json of run a)")
        lib.save()
        removed = {r["thing"]: r["why"] for r in fetch.prune(lib)}
        self.assertEqual(set(removed), {"payer", "1275", "porter"})
        self.assertEqual(removed["payer"], "names people")
        self.assertIn("icon", removed["porter"])
        self.assertEqual([a.title for a in assets.AssetLibrary(tmp / "lib").assets.values()], ["Punch-marked coin, silver"])

    def test_the_met_reads_only_public_domain_objects(self):
        pd = {"objectID": 1, "isPublicDomain": True, "primaryImageSmall": "https://images.metmuseum.org/x.jpg", "title": "Coin", "objectURL": "https://met/1"}
        self.assertEqual(assets._met_candidate(pd).licence, "CC0 1.0")
        self.assertIsNone(assets._met_candidate(dict(pd, isPublicDomain=False)))


class Look(unittest.TestCase):
    def test_the_look_d1_request_is_validated_and_judged_part_by_part(self):
        vm_look = _tool("vm_look")
        frame = "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/t046d-money-v4/stills/v4_s3.jpg"
        req = {"schema": "bie.look-request/1", "rule": "LOOK-D1", "reviewer": "codex",
               "parts": [{"id": "v4_s3", "point": "Yuan made notes compulsory", "frame": frame}]}
        self.assertEqual(vm_look.load_request(json.dumps(req))["rule"], "LOOK-D1")
        with self.assertRaises(ValueError):
            vm_look.load_request(json.dumps(dict(req, parts=[dict(req["parts"][0], frame="https://example.com/x.jpg")])))

        class Response:
            content = {"hints_point": 7, "text_only": False, "what_it_shows": "a timeline with four dated markers", "missing": ""}

        class Gateway:
            ledger = guard = None

            def model_of(self, route):
                return "fake"

            def complete(self, route, request, **kw):
                assert route == "codex" and request.messages[1]["content"][1]["type"] == "image"
                return Response()

        png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
        with mock.patch.object(vm_look, "fetch", lambda url, opener=None: png):
            summary = vm_look.run_d1(req, Path(tempfile.mkdtemp()), max_inr=1, gateway=Gateway())
        self.assertEqual(summary["table"], {"parts": 1, "mean_hints_point": 7.0, "text_only": 0, "low": []})
        self.assertEqual(look.d1_problems({"what_it_shows": "x"}), ["what_it_shows: say what the frame shows in a few words"])

    def test_the_request_builder_reads_the_points_from_the_dikhane_ki_list(self):
        import test_task046_canvas_director as T
        chapter, lesson = T.econ_lesson()
        tmp = Path(tempfile.mkdtemp())
        cd.run_canvas(chapter, lesson, T.ECON, T.runner(tmp), tmp, workers=1)
        req = _tool("task046d_look_request").build(tmp, "v1", "t046d-test")
        self.assertEqual([p["id"] for p in req["parts"]], ["v1_s1", "v1_s2"])
        self.assertTrue(all(p["frame"].endswith(f"/t046d-test/stills/{p['id']}.jpg") and p["point"] for p in req["parts"]))
        self.assertEqual(_tool("vm_look").load_request(json.dumps(req))["reviewer"], "codex")

    def test_the_render_writes_no_stills_without_a_spec(self):
        render_spec = _tool("render_spec")
        self.assertEqual(render_spec.write_stills(Path(tempfile.mkdtemp()), Path("review.mp4")), 0)


if __name__ == "__main__":
    unittest.main()


class ProofRunFixes(unittest.TestCase):
    """What the live proof run on Money v2 and v4 (vm-t046d-money-canvas-a, 31 October 2026) taught: two v4 parts failed three
    rounds each on BIE's own code, not on the maker's thinking."""

    def test_a_currency_sign_is_a_word_a_cue_can_wait_for_and_earlier_cues_resolve_as_before(self):
        from bie.brain.video import timing
        say = "Foreign price tags में codes क्यों देखें? $ वाला United States Dollar, USD, सबसे ज़्यादा; € Euro; ¥ Japan या China।"
        for sign in ("$", "€", "¥"):
            self.assertTrue(timing.has_word(say, sign), sign)
        self.assertFalse(timing.has_word(say, "£"))
        self.assertLess(timing.word_fraction(say, "$"), timing.word_fraction(say, "€"))
        self.assertGreater(timing.word_fraction(say, "€"), 0.0)
        self.assertTrue(timing.has_word("एक ₹100 का note", "100"))                   # a cue with digits: the plain form, as before
        self.assertTrue(timing.has_word("100 रुपये का note", "₹100"))
        self.assertFalse(timing.has_word("Euro", "$"))

    def test_a_reference_to_a_picture_node_means_the_picture_and_a_missing_id_names_the_ids(self):
        beats = [{"beat_id": "b1", "say": "पहले commemorative coins देखिए।"}, {"beat_id": "b2", "say": "अब उनका status समझिए।"}]
        gallery = {"id": "status", "kind": "picture", "cell": [0, 0, 12, 3], "cue": ["b1", ""],
                   "picture": {"type": "gallery", "title": "", "panels": [{"name": "Proof set", "icon": "fa:solid/coins", "cue": ["b1", ""]},
                                                                         {"name": "UNC set", "icon": "fa:solid/coins", "cue": ["b2", ""]}],
                               "arrows": False, "numbered": False}}
        mint = {"id": "mint", "kind": "icon", "cell": [0, 5, 4, 2], "cue": ["b2", "status"], "icon": "fa:solid/landmark", "label": "Mint"}
        arrow = {"id": "sale", "kind": "arrow", "cue": ["b2", "status"], "from": {"id": "mint", "side": "top"}, "to": {"id": "status", "side": "bottom"}}
        plan = {"id": "v4_s7a", "part_id": "c11.2", "theme": "paper", "grid": [12, 8], "touches": True, "beats": beats,
                "nodes": [gallery, mint, arrow], "focus": [{"cue": ["b2", "status"], "ids": ["status"]}]}
        scene, report = canvas.compile_plan(copy.deepcopy(plan))
        focus = scene["layers"][0]["data"]["focus"][0]["ids"]
        self.assertGreaterEqual(len(focus), 2)                                         # the picture's own elements
        self.assertNotIn("status", focus)
        with self.assertRaises(canvas.PlanError) as err:
            canvas.compile_plan(dict(copy.deepcopy(plan), focus=[{"cue": ["b2", ""], "ids": ["sets"]}]))
        self.assertIn("focus names a missing element 'sets'", str(err.exception))
        self.assertIn("status", str(err.exception).split("ids are:")[1])               # the ids the maker can use

    def test_the_ideas_step_reads_a_card_type_as_its_picture_and_names_found_by_role(self):
        # 21 of 36 ideas answers wrote the card part's type as picture_type; the needs list held years, roles and "lender"→blender
        stub = {"id": "v2_s1", "beats": [{"beat_id": "b1", "say": "Barter यानी सीधा लेन-देन।"}]}
        answer = {"beats": [{"beat_id": "b1", "idea": "barter", "relation": "accept", "relation_note": "", "things": ["wheat"],
                             "people": [], "places": [], "shows": "wheat for cloth", "on_word": "Barter", "image_wanted": ""}],
                  "picture_type": "definition", "picture_note": ""}
        self.assertEqual(vt.check_ideas(stub, answer), [])
        self.assertEqual(vt.IDEAS_SCHEMA["properties"]["picture_type"]["enum"], list(vt.PICTURE_TYPES))
        self.assertFalse(vt._is_thing("1023"))
        self.assertTrue(vt._is_thing("1661 Sweden"))
        self.assertEqual(icons.search("lender")[0]["id"], "fa:solid/user-tie")
        self.assertNotIn("fa:solid/blender", [r["id"] for r in icons.search("lender")])
        self.assertEqual(icons.search("porter")[0]["id"], "fa:solid/person-walking-luggage")
        self.assertEqual(icons.search("coins")[0]["id"], "tw:1fa99")

    def test_the_render_keeps_the_edges_in_view_bends_arrows_gently_and_tags_readable(self):
        # the v2 render of 31 October 2026: the book's table lost its first letters at the frame edge, a curve=True arrow swung
        # a whole arrow-length across the book's gallery, and a tag had blue words on its pink fill
        full = canvas.fit_box(canvas.pad_box(canvas.cell_box([0, 0, 12, 8], [12, 8])))
        table = canvas.cell_box([0, 0, 12, 7], [12, 8])
        self.assertGreaterEqual(table["x"] - full["x"], 0.03)                         # the table's edge is well inside the view
        self.assertLessEqual(full["x"] + full["w"], 1.0)
        self.assertEqual((canvas.arrow_bend(True), canvas.arrow_bend(False), canvas.arrow_bend(5)), (canvas.ARROW_BEND, 0.0, 0.35))
        beats = [{"beat_id": "b1", "say": "पहला पड़ाव barter है: गेहूँ के बदले कपड़ा।"}]
        plan = {"id": "v2_s5a", "part_id": "c04.1", "theme": "paper", "grid": [12, 8], "touches": True, "beats": beats,
                "nodes": [{"id": "wheat", "kind": "icon", "cell": [1, 4, 2, 2], "cue": ["b1", ""], "icon": "tw:1f33e", "label": "गेहूँ"},
                          {"id": "cloth", "kind": "icon", "cell": [9, 4, 2, 2], "cue": ["b1", ""], "icon": "tw:1f455", "label": "कपड़ा"},
                          {"id": "swap", "kind": "arrow", "cue": ["b1", "बदले"], "from": {"id": "wheat"}, "to": {"id": "cloth"}, "curve": True},
                          {"id": "tag", "kind": "text", "cell": [4, 6, 4, 1], "cue": ["b1", "barter"], "text": "पहला पड़ाव barter",
                           "style": "tag", "tone": "accent"}],
                "camera": [{"cells": [0, 0, 12, 8], "cue": ["b1", ""]}]}
        scene, _ = canvas.compile_plan(plan)
        els = {e["id"]: e for e in scene["layers"][0]["data"]["elements"]}
        self.assertEqual(els["swap"]["curve"], canvas.ARROW_BEND)
        self.assertNotIn("tone", els["tag"])
        cam = scene["camera"][0]["box"]
        self.assertLess(cam["x"], table["x"] - 0.03)
