"""Task 046 Part D2 item F · better pictures: BIE's own money drawings (``bie:``, ``tools/bie_objects.py``) and Microsoft Fluent
Emoji's 3D icons (``fl:``, MIT, pinned commit) in the icon index (``bie/toolbox/icons.py``), the money words of the icon search,
and the licence gate that lets MIT in for the Fluent source only (Navin's brief of 1 November 2026).

Offline, standard library, no network (a fake opener stands in for raw.githubusercontent.com), no keys, no money.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain.assets import AssetLibrary  # noqa: E402
from bie.toolbox import icons, licence, registry  # noqa: E402
import bie_objects  # noqa: E402

SVG_NS = "{http://www.w3.org/2000/svg}"
COINS = ["coin-1", "coin-2", "coin-5", "coin-10", "coin-20", "coin-50p", "coin-25p"]
NOTES = ["note-10", "note-20", "note-50", "note-100", "note-200", "note-500", "note-2000"]
OBJECTS = ["cheque", "passbook", "qr-stand", "pos-machine", "phone", "salt-sack", "cowrie-shells", "cattle", "grain-sack",
           "cloth-roll", "gold-bar", "ledger"]
BIE_IDS = ["bie:" + k for k in COINS + NOTES + OBJECTS]
# words a picture of money may never carry (docs/bie/BIE_MONEY_OBJECTS.md): the issuer, the state, the promise, the signature
FORBIDDEN = ("Reserve Bank", "भारतीय रिज़र्व", "रिज़र्व बैंक", "रिजर्व बैंक", "RBI", "Government of India", "भारत सरकार", "गवर्नर",
             "Governor", "promise to pay", "वचन देता", "सत्यमेव जयते", "Satyamev", "legal tender")
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Opener:
    def __init__(self, data: bytes = PNG):
        self.urls, self.data = [], data

    def __call__(self, request, timeout=None):
        self.urls.append(request.full_url)
        if request.full_url.endswith(".svg"):                           # a different file for every SVG asked for
            return Response(f'<svg xmlns="http://www.w3.org/2000/svg"><!-- {request.full_url} --><path d="M0 0h1v1z"/></svg>'.encode())
        return Response(self.data)


def texts(svg: str) -> list:
    """The words a drawing shows (every <text>, tspans included)."""
    root = ET.fromstring(svg)
    return ["".join(t.itertext()).strip() for t in root.iter(SVG_NS + "text")]


class BieDrawings(unittest.TestCase):
    def test_every_bie_id_is_an_svg_in_the_repository(self):
        rows = icons.by_id()
        found = sorted(i for i in rows if i.startswith("bie:"))
        self.assertEqual(found, sorted(BIE_IDS))
        for i in BIE_IDS:
            path = icons.icon_file(i)                                     # no opener: never the network
            self.assertTrue(path.is_file(), i)
            self.assertEqual(path.parent, icons.BIE_DIR)
            self.assertEqual(path.suffix, ".svg")
            r = rows[i]
            self.assertEqual((r["licence"], r["credit"], r["style"]), ("CC0 1.0", "BIE's own drawings (Book Intelligence Engine)", "colour"))
            self.assertEqual(r["licence_url"], "https://creativecommons.org/publicdomain/zero/1.0/")
            self.assertIn("bie/toolbox/icons/bie", r["source_url"])
            self.assertRegex(r["name"], r"[a-zA-Z]")                      # English and Hindi names and terms
            self.assertRegex(r["name"], "[ऀ-ॿ]")
            self.assertTrue(any(re.search("[ऀ-ॿ]", t) for t in r["terms"]), i)
            self.assertTrue(any(re.fullmatch(r"[a-z0-9 ₹]+", t) for t in r["terms"]), i)

    def test_the_drawings_are_small_self_contained_svgs_without_issuer_words(self):
        for i in BIE_IDS:
            svg = icons.icon_file(i).read_text(encoding="utf-8")
            root = ET.fromstring(svg)
            self.assertEqual(root.get("viewBox"), "0 0 512 512", i)
            self.assertLess(len(svg.encode("utf-8")), 6 * 1024, i)
            for word in FORBIDDEN:
                self.assertNotIn(word.lower(), svg.lower(), (i, word))
            self.assertNotIn("href", svg, i)                              # no external files, images or fonts
            self.assertNotIn("<image", svg, i)
            self.assertNotIn("@import", svg, i)
            self.assertEqual(re.findall(r"url\((?!#)", svg), [], i)
            self.assertEqual([u for u in re.findall(r"https?://[^\"' ]+", svg) if u != "http://www.w3.org/2000/svg"], [], i)

    def test_each_coin_and_note_shows_its_denomination_and_the_notes_say_not_money(self):
        for cid in COINS:
            words = texts(icons.icon_file("bie:" + cid).read_text(encoding="utf-8"))
            if cid.endswith("p"):
                self.assertIn(cid[5:-1], words, cid)
                self.assertIn("पैसे", words, cid)
            else:
                self.assertIn("₹" + cid[5:], words, cid)
        for nid in NOTES:
            svg = icons.icon_file("bie:" + nid).read_text(encoding="utf-8")
            words = texts(svg)
            self.assertIn("₹" + nid[5:], words, nid)
            self.assertIn("BIE", words, nid)
            self.assertIn(bie_objects.NOT_MONEY, words, nid)
            # not the shape of a real note: BIE's note is about 1.6 : 1 with round corners (real notes: 1.95 to 2.5 : 1)
            body = next(r for r in ET.fromstring(svg).iter(SVG_NS + "rect") if r.get("stroke") == bie_objects.INK)
            ratio = float(body.get("width")) / float(body.get("height"))
            self.assertLess(ratio, 1.8, nid)
            self.assertGreaterEqual(float(body.get("rx")), 20, nid)
        colours = {bie_objects.NOTES[d][0] for d in bie_objects.NOTES}
        self.assertEqual(len(colours), 7)                                 # each note its own colour
        # 50 and 25 paise are visibly different coins (the D1 stills drew both as the same coin)
        self.assertNotEqual(bie_objects.COINS["coin-50p"][2:6], bie_objects.COINS["coin-25p"][2:6])

    def test_the_qr_pattern_is_decorative_and_the_phone_screen_is_plain(self):
        modules = bie_objects.qr_modules()
        self.assertEqual(max(max(r, c) for r, c in modules), 18)           # 19 x 19: no QR version has that size
        self.assertIn((0, 0), modules)
        svg = icons.icon_file("bie:phone").read_text(encoding="utf-8")
        self.assertEqual(texts(svg), [])                                  # nothing on the screen: the video writes on it

    def test_the_committed_drawings_are_what_the_script_draws(self):
        self.assertEqual(bie_objects.check(), [])
        with tempfile.TemporaryDirectory() as folder:
            ids = bie_objects.write(Path(folder))
            self.assertEqual(["bie:" + i for i in sorted(ids)], sorted(BIE_IDS))
            self.assertEqual(bie_objects.check(Path(folder)), [])
            (Path(folder) / "phone.svg").write_text("<svg/>", encoding="utf-8")
            self.assertEqual(bie_objects.check(Path(folder)), ["phone.svg"])

    def test_the_money_rules_are_written_down(self):
        doc = (ROOT / "docs" / "bie" / "BIE_MONEY_OBJECTS.md").read_text(encoding="utf-8")
        for needed in ("Bharatiya Nyaya Sanhita", "178", "182", "State Emblem", "Coinage Act", "BS_PressReleaseDisplay.aspx?prid=3803",
                       icons.FLUENT_COMMIT, "MIT", "CC0"):
            self.assertIn(needed, doc)


class FluentEmoji(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.env = mock.patch.dict(os.environ, {"BIE_FLUENT_EMOJI": "", "BIE_ASSET_CACHE": str(self.tmp / "cache")})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_the_fluent_rows_are_3d_pngs_at_the_pinned_commit_without_skin_tones(self):
        self.assertRegex(icons.FLUENT_COMMIT, r"^[0-9a-f]{40}$")
        s = icons.SETS["fl"]
        self.assertEqual(s["tag"], icons.FLUENT_COMMIT)
        self.assertIn(icons.FLUENT_COMMIT, s["raw"])
        rows = [r for r in icons.load()["icons"] if r["id"].startswith("fl:")]
        self.assertGreater(len(rows), 1500)
        for r in rows:
            self.assertTrue(icons.ID.match(r["id"]), r["id"])
            self.assertEqual((r["style"], r["licence"], r["credit"]), ("3d", "MIT", "Fluent Emoji by Microsoft"))
            self.assertEqual(r["licence_url"], f"https://github.com/microsoft/fluentui-emoji/blob/{icons.FLUENT_COMMIT}/LICENSE")
            self.assertEqual(r["source_url"], "https://github.com/microsoft/fluentui-emoji")
            self.assertRegex(r["file"], r"^assets/[^/]+/(Default/)?3D/[^/]+\.png$")
            self.assertNotRegex(r["file"], r"_(dark|light|medium|medium-dark|medium-light)\.png$")
            self.assertFalse(r["name"].lower().startswith("flag:"), r["id"])
        ids = {r["id"] for r in rows}
        self.assertTrue({"fl:coin", "fl:money-bag", "fl:bank", "fl:thumbs-up", "fl:sheaf-of-rice"} <= ids)

    def test_a_fluent_icon_is_fetched_once_from_the_pinned_commit_as_a_png(self):
        opener = Opener()
        path = icons.icon_file("fl:coin", opener=opener)
        self.assertEqual(opener.urls, [f"https://raw.githubusercontent.com/microsoft/fluentui-emoji/{icons.FLUENT_COMMIT}/assets/Coin/3D/coin_3d.png"])
        self.assertEqual(path.suffix, ".png")
        self.assertTrue(str(path).startswith(str(self.tmp / "cache")))
        icons.icon_file("fl:coin", opener=opener)                        # cached: no second fetch
        self.assertEqual(len(opener.urls), 1)
        icons.icon_file("fl:thumbs-up", opener=opener)                   # spaces are quoted; the default skin tone
        self.assertEqual(opener.urls[-1], f"https://raw.githubusercontent.com/microsoft/fluentui-emoji/{icons.FLUENT_COMMIT}/"
                                          "assets/Thumbs%20up/Default/3D/thumbs_up_3d_default.png")

    def test_a_local_checkout_is_read_when_it_is_set(self):
        row = icons.by_id()["fl:coin"]
        path = self.tmp / "fluent" / row["file"]
        path.parent.mkdir(parents=True)
        path.write_bytes(PNG)
        with mock.patch.dict(os.environ, {"BIE_FLUENT_EMOJI": str(self.tmp / "fluent")}):
            self.assertEqual(icons.icon_file("fl:coin"), path)
            with self.assertRaises(icons.IconError):
                icons.icon_file("fl:bank")

    def test_fluent_icons_join_the_library_and_copies_as_png_and_pass_the_gate_with_their_credit(self):
        library = AssetLibrary(self.tmp / "assets")
        paths = icons.add_to_library(["fl:coin", "bie:coin-50p", "tw:1f3ea"], library, opener=Opener())
        self.assertTrue(paths["fl:coin"].endswith(".png"))
        self.assertTrue(paths["bie:coin-50p"].endswith(".svg"))
        assets = {a.source: a for a in library.assets.values()}
        fl = assets["fluentui-emoji"]
        self.assertEqual((fl.mime, fl.licence, fl.author), ("image/png", "MIT", "Microsoft"))
        self.assertIn(icons.FLUENT_COMMIT, fl.licence_url)
        self.assertEqual(assets["bie-objects"].mime, "image/svg+xml")
        self.assertEqual(licence.lesson_licence_check(list(library.assets.values())), [])
        lines = licence.lesson_credits(list(library.assets.values()))
        self.assertEqual(len(lines), 2)                                  # BIE's own drawing needs no credit line
        self.assertTrue(any("Microsoft" in line and "MIT" in line and "fluentui-emoji" in line for line in lines))
        out = icons.copy(["fl:coin", "bie:cheque"], self.tmp / "dest", opener=Opener())
        self.assertEqual(out, {"fl:coin": "icons/fl-coin.png", "bie:cheque": "icons/bie-cheque.svg"})
        self.assertEqual((self.tmp / "dest" / "icons" / "fl-coin.png").read_bytes(), PNG)
        credits = json.loads((self.tmp / "dest" / "icons" / "credits.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(c["licence"] for c in credits), ["CC0 1.0", "MIT"])

    def test_the_rows_are_built_from_a_checkout_and_a_clone_at_another_commit_is_refused(self):
        root = self.tmp / "fl"
        for folder, files, meta in (("Coin", ["3D/coin_3d.png", "Color/coin_color.svg"], {"cldr": "coin", "keywords": ["coin", "Money"]}),
                                    ("Thumbs up", ["Default/3D/thumbs_up_3d_default.png", "Dark/3D/thumbs_up_3d_dark.png"],
                                     {"cldr": "thumbs up", "keywords": ["+1", "hand"], "unicodeSkintones": ["1f44d"]}),
                                    ("Piñata", ["3D/piñata_3d.png"], {"cldr": "piñata", "keywords": ["party"]})):
            for f in files:
                (root / "assets" / folder / f).parent.mkdir(parents=True, exist_ok=True)
                (root / "assets" / folder / f).write_bytes(PNG)
            (root / "assets" / folder / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        rows = icons.fluent_rows(root)
        self.assertEqual([r["id"] for r in rows], ["fl:coin", "fl:pinata", "fl:thumbs-up"])
        self.assertEqual(rows[0]["terms"], ["coin", "money"])
        self.assertEqual(rows[2]["file"], "assets/Thumbs up/Default/3D/thumbs_up_3d_default.png")
        self.assertEqual(set(rows[0]), set(icons.load()["icons"][0]))
        git = ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(git + ["add", "-A"], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "x"], check=True)
        with self.assertRaises(icons.IconError) as ctx:
            icons.fluent_rows(root)
        self.assertIn(icons.FLUENT_COMMIT, str(ctx.exception))


class MoneySearch(unittest.TestCase):
    def first(self, query: str) -> str:
        return icons.search(query)[0]["id"]

    def test_the_money_words_find_bies_own_drawings_first(self):
        self.assertEqual(self.first("cheque"), "bie:cheque")
        self.assertEqual([r["id"] for r in icons.search("Cheques and deposits")][:2], ["bie:cheque", "fa:solid/money-check"])
        self.assertEqual(self.first("50 paise"), "bie:coin-50p")
        self.assertEqual(self.first("25 paise"), "bie:coin-25p")
        self.assertNotEqual(self.first("50 paise"), self.first("25 paise"))
        cases = {"50 पैसे": "bie:coin-50p", "चवन्नी": "bie:coin-25p", "50p coin": "bie:coin-50p", "₹500 का नोट": "bie:note-500",
                 "500 notes": "bie:note-500", "Rs 2000 note": "bie:note-2000", "दो हज़ार का नोट": "bie:note-2000", "₹10 coin": "bie:coin-10",
                 "10 का सिक्का": "bie:coin-10", "₹10": "bie:note-10", "₹100": "bie:note-100", "a 5 rupee coin": "bie:coin-5",
                 "salt": "bie:salt-sack", "Salt, cattle, shells": "bie:salt-sack", "नमक": "bie:salt-sack", "cowrie shells": "bie:cowrie-shells",
                 "कौड़ी": "bie:cowrie-shells", "cattle": "bie:cattle", "गाय": "bie:cattle", "grain": "bie:grain-sack", "अनाज": "bie:grain-sack",
                 "cloth": "bie:cloth-roll", "कपड़ा": "bie:cloth-roll", "qr code": "bie:qr-stand", "upi scanner": "bie:qr-stand",
                 "card machine": "bie:pos-machine", "POS": "bie:pos-machine", "passbook": "bie:passbook", "पासबुक": "bie:passbook",
                 "UPI payment": "bie:phone", "gold bar": "bie:gold-bar", "ledger": "bie:ledger", "बही-खाता": "bie:ledger"}
        for query, wanted in cases.items():
            self.assertEqual(self.first(query), wanted, query)
        self.assertEqual([r["id"] for r in icons.search("₹10")][:2], ["bie:note-10", "bie:coin-10"])
        self.assertNotIn("bie:note-10", [r["id"] for r in icons.search("₹100")])        # whole numbers: ₹100 is not ₹10

    def test_the_earlier_words_keep_their_icons(self):
        for query, wanted in {"cross": "tw:274c", "tick": "tw:2705", "question": "tw:2753", "wheat": "tw:1f33e", "गेहूँ के बदले कपड़ा": "tw:1f33e",
                              "coins": "tw:1fa99", "coin": "tw:1fa99", "सिक्का": "tw:1fa99", "bank": "tw:1f3e6", "warehouse": "fa:solid/warehouse",
                              "lender": "fa:solid/user-tie", "किसान": "tw:1f9d1-200d-1f33e"}.items():
            self.assertEqual(self.first(query), wanted, query)
        self.assertNotIn("fl:latin-cross", [r["id"] for r in icons.search("cross")])     # no religious cross unasked, in any set
        self.assertEqual(icons.check_ids(sorted({i for ids in icons.ALIASES.values() for i in ids})), [])

    def test_fluent_3d_ranks_a_little_above_twemoji_for_objects(self):
        apple = [r["id"] for r in icons.search("apple")]
        self.assertTrue(apple[0].startswith("fl:"), apple)
        self.assertIn("tw:1f34e", apple)
        self.assertLess(icons.STYLE_BONUS["fl"] - 0.5, 1)              # a little: a better word match still wins
        self.assertGreater(icons.STYLE_BONUS["fl"], 0.5)

    def test_check_ids_knows_the_new_sets(self):
        self.assertEqual(icons.check_ids(["bie:cheque", "bie:coin-25p", "fl:coin", "fl:thumbs-up", "tw:1f3ea"]), [])
        self.assertEqual(icons.check_ids(["bie:nope", "fl:Bad_Id", "fl:no-such-emoji", "bi:cheque"]),
                         ["bie:nope", "fl:Bad_Id", "fl:no-such-emoji", "bi:cheque"])


class LicenceGate(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_bie_drawings_are_own_work_and_fluent_is_approved_by_name_only(self):
        library = AssetLibrary(self.tmp / "assets")
        icons.add_to_library(["bie:note-500", "bie:cheque"], library)
        bie = list(library.assets.values())
        self.assertEqual({(a.source, a.licence) for a in bie}, {("bie-objects", "CC0 1.0")})
        self.assertEqual(licence.lesson_licence_check(bie), [])
        self.assertEqual(licence.lesson_credits(bie), [])
        self.assertEqual(licence.asset_verdict(bie[0]).licence_class, "own-work")
        fl = {"asset_id": "a1", "title": "coin (fl:coin)", "source": "fluentui-emoji", "licence": "MIT", "author": "Microsoft",
              "licence_url": icons.SETS["fl"]["licence_url"], "page_url": icons.SETS["fl"]["source_url"]}
        verdict = licence.asset_verdict(fl)
        self.assertTrue(verdict.allowed)
        self.assertIn("approved by Navin on 2026-11-01", verdict.reason)
        self.assertIn("missing: author", licence.asset_verdict(dict(fl, author="")).reason)          # the credit is a condition
        self.assertEqual(licence.asset_verdict(dict(fl, source="openverse")).verdict, "needs_navin")   # MIT elsewhere: still Navin's
        self.assertEqual(licence.classify("MIT").verdict, "needs_navin")
        for bad, cls in (("CC BY-SA 4.0", "share-alike"), ("CC BY-NC 4.0", "non-commercial")):   # still refused
            for source in ("openverse", "", "twemoji"):
                v = licence.asset_verdict(dict(fl, source=source, licence=bad))
                self.assertEqual((v.verdict, v.licence_class), ("refused", cls), (source, bad))
        once = icons.credit_assets(["bie:cheque", "fl:coin", "tw:1f3ea", "fl:bank"])
        self.assertEqual([a["asset_id"] for a in once], ["bie-objects", "fluentui-emoji", "twemoji"])
        self.assertEqual(licence.lesson_licence_check(once), [])

    def test_the_policy_and_the_registry_record_navins_words(self):
        policy = json.loads(licence.POLICY.read_text(encoding="utf-8"))
        self.assertEqual(licence.policy_problems(policy), [])
        approved = {a["id"]: a for a in policy["sources"]["approved_by_navin"]}
        self.assertEqual(approved["fluentui-emoji"]["approved_on"], "2026-11-01")
        self.assertIn("add Microsoft Fluent Emoji (MIT", approved["fluentui-emoji"]["words"])
        self.assertIn(icons.FLUENT_COMMIT, approved["fluentui-emoji"]["condition"])
        self.assertIn("bie-objects", policy["own_work"]["asset_sources"])
        allowed = {c["id"] for c in policy["classes"] if c["verdict"] == "allowed"}
        self.assertEqual(allowed, {"public-domain", "cc-by", "font", "own-work"})                    # no licence class loosened
        box = registry.load()
        for tid, kind in (("fluentui-emoji", "approved"), ("bie-objects", "own-work")):
            tool = box.tool(tid)
            self.assertEqual((tool.status, tool.adapter, tool.kind), ("wrapped", "bie.toolbox.icons", "asset_source"), tid)
            self.assertEqual((licence.tool_verdict(tool).verdict, licence.tool_verdict(tool).licence_class), ("allowed", kind), tid)
        self.assertEqual(box.tool("fluentui-emoji").version, icons.FLUENT_COMMIT)
        self.assertEqual(licence.registry_problems(box.tools), [])


class Index(unittest.TestCase):
    def test_the_index_schema_is_unchanged_and_the_new_rows_rebuild_to_the_same_bytes(self):
        data = icons.load()
        self.assertEqual(data["schema"], "bie.icons/1")
        self.assertEqual(data["count"], len(data["icons"]))
        fields = {"id", "name", "terms", "style", "file", "licence", "credit", "licence_url", "source_url"}
        ids = [r["id"] for r in data["icons"]]
        self.assertEqual(len(ids), len(set(ids)))
        for r in data["icons"]:
            self.assertEqual(set(r), fields, r["id"])
            self.assertTrue(icons.ID.match(r["id"]), r["id"])
        self.assertEqual({icons.set_of(i) for i in ids}, {"tw", "fa", "fl", "bie"})
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "index.json.gz"
            icons.add_sets(icons.DEFAULT_INDEX, out)                      # fl rows kept, bie rows from the catalogue
            self.assertEqual(out.read_bytes(), icons.DEFAULT_INDEX.read_bytes())
            self.assertEqual(json.loads(gzip.open(out, "rt", encoding="utf-8").read())["icons"][:5], data["icons"][:5])


if __name__ == "__main__":
    unittest.main()
