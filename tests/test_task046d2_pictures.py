"""Task 046 Part D2 item F · better pictures: Microsoft Fluent Emoji's 3D icons (``fl:``, MIT, pinned commit) in the icon index
(``bie/toolbox/icons.py``), the words of the icon search, and the licence gate that lets MIT in for the Fluent source only
(Navin's brief of 1 November 2026). BIE's own money drawings (``bie:``) of item F are retired by Navin's addendum of 2 November
2026 (``tests/test_task046d2_coder.py`` holds the general path that replaces them).

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
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain.assets import AssetLibrary  # noqa: E402
from bie.toolbox import icons, licence, registry  # noqa: E402
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
        paths = icons.add_to_library(["fl:coin", "tw:1f3ea"], library, opener=Opener())
        self.assertTrue(paths["fl:coin"].endswith(".png"))
        self.assertTrue(paths["tw:1f3ea"].endswith(".svg"))
        assets = {a.source: a for a in library.assets.values()}
        fl = assets["fluentui-emoji"]
        self.assertEqual((fl.mime, fl.licence, fl.author), ("image/png", "MIT", "Microsoft"))
        self.assertIn(icons.FLUENT_COMMIT, fl.licence_url)
        self.assertEqual(licence.lesson_licence_check(list(library.assets.values())), [])
        lines = licence.lesson_credits(list(library.assets.values()))
        self.assertEqual(len(lines), 2)
        self.assertTrue(any("Microsoft" in line and "MIT" in line and "fluentui-emoji" in line for line in lines))
        out = icons.copy(["fl:coin", "tw:1f3ea"], self.tmp / "dest", opener=Opener())
        self.assertEqual(out, {"fl:coin": "icons/fl-coin.png", "tw:1f3ea": "icons/tw-1f3ea.svg"})
        self.assertEqual((self.tmp / "dest" / "icons" / "fl-coin.png").read_bytes(), PNG)
        credits = json.loads((self.tmp / "dest" / "icons" / "credits.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(c["licence"] for c in credits), ["CC BY 4.0", "MIT"])

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

    def test_the_money_words_find_the_icon_index_s_own_pictures(self):
        # the retired bie: drawings no longer answer: a word finds the icon sets' pictures, and a thing none of them is a picture
        # of is a need (BIE's coder draws it when a needs list asks for it)
        cases = {"cheque": "fa:solid/money-check", "₹500 का नोट": "fa:solid/money-bill-1", "salt": "tw:1f9c2", "नमक": "tw:1f9c2",
                 "cattle": "tw:1f404", "गाय": "tw:1f404", "cowrie shells": "tw:1f41a", "grain": "tw:1f33e", "ledger": "tw:1f4d2",
                 "qr code": "fa:solid/qrcode", "upi scanner": "fa:solid/qrcode"}
        for query, wanted in cases.items():
            self.assertEqual(self.first(query), wanted, query)
        self.assertFalse(any(r["id"].startswith("bie:") for q in cases for r in icons.search(q)))
        self.assertEqual(icons.fitting("sack of salt"), [])
        self.assertEqual(icons.fitting("payment claim"), [])

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

    def test_check_ids_knows_the_sets_and_names_the_retired_ones(self):
        self.assertEqual(icons.check_ids(["fl:coin", "fl:thumbs-up", "tw:1f3ea"]), [])
        self.assertEqual(icons.check_ids(["bie:cheque", "bie:nope", "fl:Bad_Id", "fl:no-such-emoji", "bi:cheque"]),
                         ["bie:cheque", "bie:nope", "fl:Bad_Id", "fl:no-such-emoji", "bi:cheque"])


class LicenceGate(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_fluent_is_approved_by_name_only(self):
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
        self.assertEqual([a["asset_id"] for a in once], ["fluentui-emoji", "twemoji"])          # a retired id is not in the index
        self.assertEqual(licence.lesson_licence_check(once), [])

    def test_the_policy_and_the_registry_record_navins_words(self):
        policy = json.loads(licence.POLICY.read_text(encoding="utf-8"))
        self.assertEqual(licence.policy_problems(policy), [])
        approved = {a["id"]: a for a in policy["sources"]["approved_by_navin"]}
        self.assertEqual(approved["fluentui-emoji"]["approved_on"], "2026-11-01")
        self.assertIn("add Microsoft Fluent Emoji (MIT", approved["fluentui-emoji"]["words"])
        self.assertIn(icons.FLUENT_COMMIT, approved["fluentui-emoji"]["condition"])
        self.assertNotIn("bie-objects", policy["own_work"]["asset_sources"])                     # retired, 2 November 2026
        self.assertIn("bie_coder", policy["generated_images"]["asset_sources"])
        allowed = {c["id"] for c in policy["classes"] if c["verdict"] == "allowed"}
        self.assertEqual(allowed, {"public-domain", "cc-by", "font", "own-work"})                    # no licence class loosened
        box = registry.load()
        tool = box.tool("fluentui-emoji")
        self.assertEqual((tool.status, tool.adapter, tool.kind), ("wrapped", "bie.toolbox.icons", "asset_source"))
        self.assertEqual((licence.tool_verdict(tool).verdict, licence.tool_verdict(tool).licence_class), ("allowed", "approved"))
        self.assertEqual(box.tool("bie-objects").status, "blocked_with_reason")
        self.assertIn("2 November 2026", box.tool("bie-objects").blocked_reason)
        self.assertEqual((box.tool("bie-coder").status, box.tool("bie-coder").adapter), ("wrapped", "bie.brain.coder"))
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
        self.assertEqual({icons.set_of(i) for i in ids}, {"tw", "fa", "fl"})
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "index.json.gz"
            icons.add_sets(icons.DEFAULT_INDEX, out)                      # fl rows kept
            self.assertEqual(out.read_bytes(), icons.DEFAULT_INDEX.read_bytes())
            self.assertEqual(json.loads(gzip.open(out, "rt", encoding="utf-8").read())["icons"][:5], data["icons"][:5])


if __name__ == "__main__":
    unittest.main()
