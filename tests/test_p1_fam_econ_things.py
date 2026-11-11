"""Family "econ_things" (Sloman economics book, 5 November 2026): the everyday things, vehicles, buildings, papers and
machines of the book's stories as parametric saanche, and the people looks for its roles.

Every saancha of the family's manifest draws clean SVG (no NaN or undefined, balanced tags) at its defaults and in the
states a scene plan will use; the manifest and the engine registry agree; a parameter out of range is refused by the
library; a moving part is a pure function of its times and settles without them. Every look of the vocabulary is in the
rig, draws in every pose, and the ten looks the Money v2 gold uses still draw byte for byte as before.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import saanche  # noqa: E402
from bie.brain.video import showplan as sp  # noqa: E402

ENGINE = ROOT / "bie" / "brain" / "video" / "engine"
FAMILY = json.loads((ENGINE / "saanche.d" / "econ_things.json").read_text(encoding="utf-8"))
NAMES = sorted(FAMILY["saanche"])
STUFF = FAMILY["saanche"]["produce"]["params"]["content"]["choices"]
GOODS = FAMILY["saanche"]["goods"]["params"]["kind"]["choices"]

VARIANTS = (
    [("produce", {"kind": k, "content": c, "fill": f, "label": "आलू 50kg"}) for k in ("sack", "heap", "basket", "crate", "packet", "bag")
     for c, f in (("potato", 1), ("rice", 0.4), ("onion", 0))]
    + [("produce", {"kind": "basket", "content": "pear", "n": 30, "content2": "orange", "n2": 6, "label": "नाशपाती 30"}),
       ("produce", {"kind": "crate", "stack": 5, "content": "tomato"}), ("produce", {"kind": "heap", "content": "sugar", "fill": 0.1})]
    + [("produce", {"content": c}) for c in STUFF]
    + [("vehicle", {"kind": k, "label": "DL 01", "riders": 3, "fuel": fu, "state": st, "smoke": 0.7, "speed": 0.8, "tag": "₹5 लाख",
                    "old": "₹6 लाख", "sticker": "किराये की", "pedal": pd, "facing": fc, "box": True, "load": 0.5, "_t": 1.3})
       for k in ("car", "scooter", "bike", "cycle", "bus", "metro", "train", "auto", "erickshaw", "truck", "tanker", "van", "tractor", "plane")
       for fu, st, pd, fc in (("cng", "new", "none", "right"), ("electric", "writeoff", "brake", "left"))]
    + [("vehicle", {"kind": "car", "class": c, "state": s}) for c in ("small", "mid", "luxury") for s in ("scratched", "crashed")]
    + [("houses", {"n": 4, "grades": "hut,small,mid,big", "board": "बिकाऊ", "boards": "2,3", "value": "₹30 लाख", "loan": "₹40 लाख",
                   "old": "₹45 लाख", "buyers": 3, "fire": "1", "spread": True, "flood": 0.4, "_t": 2, "_s": s}) for s in (0.2, 1.5, None)]
    + [("houses", {"grade": g, "layout": "scattered", "n": 3, "fire": "2"}) for g in ("hut", "small", "mid", "big", "flat")]
    + [("campus", {"kind": k, "label": "नाम", "queue": 3, "open": o, "_t": 1}) for k in ("school", "college", "hospital", "clinic", "police", "rationShop") for o in (True, False)]
    + [("pump", {"price": 96.5, "fuel": "पेट्रोल", "tax": 45, "taxLabel": "टैक्स ₹45", "split": sp_, "litres": 1200, "count": True, "nozzles": 4,
                 "busy": "1,3", "queue": 3, "closed": cl, "closedLabel": "बंद", "coins": True, "govt": "सरकार", "label": "पंप", "_t": 1, "_s": 0.5})
       for sp_, cl in ((-1, False), (0.6, True))]
    + [("pump", {"tax": 200, "price": 0})]
    + [("godown", {"kind": k, "content": c, "fill": f, "inflow": 1, "outflow": 2, "inLabel": "आवक", "outLabel": "जावक", "open": o, "label": "गोदाम", "_t": 1.5})
       for k, c, f, o in (("godown", "sack", 0.7, True), ("godown", "box", 0, False), ("shelf", "crate", 1, True))]
    + [("headlines", {"medium": m, "title": "आज की ख़बर", "items": "प्याज़ के दाम दोगुने;पेट्रोल पर टैक्स;घर सस्ते", "upto": 2, "at": 1,
                      "marks": "up;down;!", "ticker": "बाज़ार ऊपर", "lit": True, "_t": 2, "_s": 0.2}) for m in ("newspaper", "tv", "phone", "billboard")]
    + [("headlines", {"items": ""}), ("headlines", {"medium": "tv"})]
    + [("slip", {"kind": k, "title": "शीर्षक", "rows": "मूल वेतन:₹20,000;भत्ता:₹5,000;कुल", "upto": 2, "glow": "2", "count": 3, "face": "₹500",
                 "resale": "₹2,000", "seat": "B-12", "sealed": False, "amount": "₹40 लाख", "stamp": "मंज़ूर", "stamps": 3, "weeks": 8, "owner": "कंपनी A", "_s": 0.3})
       for k in ("form", "policy", "payslip", "rationCard", "ticket", "fine", "permit", "envelope", "certificate")]
    + [("slip", {"kind": "ticket", "paperless": True}), ("slip", {"kind": "envelope"})]
    + [("clock", {"hour": 3, "to": "5:00", "glide": 2, "_s": s}) for s in (0, 1, None)]
    + [("clock", {"hour": 8, "minute": 15, "bands": "7-9:₹3;9-10:₹2;17-20:₹4;x", "dial": d, "digital": True, "running": True, "speed": 30, "_s": 1, "label": "ERP"}) for d in ("12", "24")]
    + [("clock", {"stopped": True, "label": "स्टॉक"})]
    + [("chance", {"kind": k, "flip": True, "face": "tails", "history": "H,T,चित", "sectors": "जीत:1;हार:3", "land": 2, "spin": True,
                   "prize": "इनाम", "price": "₹50", "result": "₹0", "scratch": True, "roll": True, "slips": 8, "drawn": 5, "label": "लॉटरी", "_t": 1, "_s": s})
       for k in ("coin", "spinner", "scratch", "dice", "ballot") for s in (0.4, None)]
    + [("chance", {"kind": "spinner", "sectors": ""}), ("chance", {"kind": "spinner", "sectors": "a:0;b:0"})]
    + [("press", {"running": True, "rate": 3, "notes": 4, "label": "छपाई", "amount": "₹500 करोड़", "_t": t}) for t in (0, 3, 100)]
    + [("press", {"mode": "screen", "amount": "₹1,000 करोड़", "count": True, "label": "RBI", "_s": 0.5}), ("press", {"mode": "screen", "count": True})]
    + [("chimney", {"smoke": s, "filter": f, "base": b, "cloud": "CO₂ 50 t", "cloudSize": 0.8, "label": "कारख़ाना", "_t": 2}) for s, f, b in ((1, False, True), (0.9, True, False), (0, False, True))]
    + [("food", {"kind": k, "n": 2, "steam": True, "level": 0.5, "stack": 3, "label": "नाम", "price": "₹15", "old": "₹10", "_t": 1})
       for k in ("samosa", "paniPuri", "thali", "kulhad", "chaiGlass", "coffeeCup", "lassi", "jalebi", "laddoo", "momo", "chutney", "bread",
                 "iceCream", "iceCup", "paneer", "tiffin", "plate", "ghee", "toffeeJar", "biscuit", "milkPacket", "sweetBox")]
    + [("food", {"kind": "laddoo", "n": 0}), ("food", {"kind": "plate", "portion": 0})]
    + [("machine", {"kind": k, "on": True, "screen": s, "text": "₹200", "title": "रेट", "old": "₹180", "level": 0.3, "rows": "A;B;C;D",
                    "label": "नाम", "price": "₹40,000", "size": "big", "shield": True, "state": st, "_t": 1.2, "_s": 0.2})
       for k in ("laptop", "phone", "tv", "cylinder", "cooker", "fan", "fridge", "washer", "sewing", "loom", "tandoor", "bhatti", "oven",
                 "kadhai", "till", "pos", "meter", "iu", "printer", "console", "camera")
       for s, st in (("normal", "tap"), ("cracked", "approved"))]
    + [("machine", {"kind": "laptop", "screen": s}) for s in ("loading", "frozen", "off")]
    + [("goods", {"kind": k, "label": "नाम", "price": "₹200", "old": "₹150", "count": 3, "open": True, "opener": True, "warning": 0.7,
                  "tools": "हथौड़ा;पेचकस;रिंच", "upto": 2, "band": "#e5484d", "lit": "green", "on": True, "angle": 30, "at": 2, "_t": 1, "_s": 0.2})
       for k in GOODS]
    + [("stall", {"kind": k, "label": "चाय की टपरी", "items": "चाय:₹10;समोसा:₹15", "strike": 1, "new": "₹12", "cost": "पेंट ₹50", "count": 4,
                  "size": "big", "open": o, "queue": 2, "_t": 1, "_s": 0.3}) for k in ("tea", "samosa", "momo", "sweets", "dhaba", "icecream", "kiln") for o in (True, False)]
    + [("natureSign", {"kind": k, "sign": "−", "label": "झटका", "level": 0.4, "_t": 1, "_s": 0.1})
       for k in ("sun", "rain", "cloud", "storm", "frost", "drought", "crop", "flood", "fire", "bolt", "sheep", "buffalo", "heart", "ozone")]
    + [("cityMap", {"detail": d, "stations": "क;ख;ग;घ", "label": "शहर"}) for d in (0, 0.5, 1)]
)

# Processes: the same params and times give the same SVG, a later time moves it, and no times give the settled state.
PROCESSES = [
    ("vehicle", {"kind": "truck", "speed": 1, "smoke": 0.8}), ("houses", {"n": 4, "fire": "1", "spread": True, "flood": 0.3}),
    ("pump", {"coins": True, "litres": 900, "count": True}), ("godown", {"inflow": 1, "outflow": 1}),
    ("headlines", {"medium": "tv", "items": "ख़बर", "ticker": "चलती पट्टी"}), ("clock", {"hour": 3, "to": "5:00"}),
    ("chance", {"kind": "coin", "flip": True}), ("chance", {"kind": "spinner", "spin": True, "land": 1, "sectors": "a:1;b:2"}),
    ("press", {"running": True}), ("chimney", {"smoke": 0.8}), ("machine", {"kind": "fan", "on": True}),
    ("machine", {"kind": "sewing", "on": True}), ("machine", {"kind": "loom", "on": True}), ("food", {"kind": "kulhad", "steam": True}),
    ("stall", {"kind": "tea"}), ("natureSign", {"kind": "rain"}), ("goods", {"kind": "wheel", "on": True}),
]

LOOKS_NEW = ["officer", "doctor", "patient", "police", "student", "teacher", "rider", "clerk", "banker", "trader", "economist", "landlord",
             "tout", "mason", "contractor", "tailor", "teaPicker", "weaver", "oldMan", "oldWoman", "child", "girl", "farmWoman", "worker",
             "executive", "judge", "engineer", "unionLeader", "halwai", "foreignMan", "foreignWoman"]
LOOKS_OLD = ["ramu", "mohan", "sita", "kamla", "raju", "villager", "oil", "salt", "herder", "shop"]
POSES_OLD = ["stand", "give", "receive", "hold", "holdBoth", "think", "point", "shrug", "wave", "carry", "write", "walk", "refuse"]
OLD_LOOKS_SHA = "226693961aa1e4f807df1b6e91aa2f61e3743790579df68cd0e74a661f869ae7"   # the rig's output for the ten looks before this family


def balanced(svg: str) -> bool:
    stack = []
    for close, tag, selfclose in re.findall(r"<(/?)([a-zA-Z]+)(?:\s[^<>]*?)?(/?)>", svg):
        if close:
            if not stack or stack.pop() != tag:
                return False
        elif not selfclose:
            stack.append(tag)
    return not stack


def node(script: str):
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


class Manifest(unittest.TestCase):
    def test_the_family_is_in_the_library_with_hindi_and_english_words(self):
        self.assertEqual(FAMILY["schema"], "bie.saancha-manifest/1")
        for name in NAMES:
            entry = saanche.get(name)
            self.assertIsNotNone(entry, name)
            self.assertEqual(entry["since"], "2026-11-05")
            self.assertTrue(any(not t.isascii() for t in entry["tags"]), name)
            self.assertTrue(any(t.isascii() for t in entry["tags"]), name)
            defaults = {k: v["default"] for k, v in entry["params"].items() if v["type"] != "color" or v["default"]}
            self.assertEqual(saanche.problems(name, defaults), [], name)

    def test_every_variant_fits_the_manifest(self):
        for name, p in VARIANTS:
            with self.subTest(name=name, p=p):
                self.assertEqual(saanche.problems(name, {k: v for k, v in p.items() if not k.startswith("_")}), [])

    def test_out_of_range_parameters_are_refused(self):
        self.assertIn("outside", saanche.problems("produce", {"fill": 1.5})[0])
        self.assertIn("not one of", saanche.problems("produce", {"content": "gold"})[0])
        self.assertIn("not one of", saanche.problems("vehicle", {"kind": "rocket"})[0])
        self.assertIn("whole number", saanche.problems("houses", {"n": 2.5})[0])
        self.assertIn("outside", saanche.problems("houses", {"n": 20})[0])
        self.assertIn("true or false", saanche.problems("pump", {"closed": "yes"})[0])
        self.assertIn("outside", saanche.problems("clock", {"hour": 25})[0])
        self.assertIn("#rrggbb", saanche.problems("goods", {"color": "red"})[0])
        self.assertIn("no parameter", saanche.problems("slip", {"colour": "#ffffff"})[0])
        self.assertIn("a number is needed", saanche.problems("chimney", {"smoke": "high"})[0])

    def test_a_search_in_hindi_finds_them(self):
        for word, name in [("बोरी", "produce"), ("स्कूटर", "vehicle"), ("बिकाऊ", "houses"), ("अस्पताल", "campus"), ("पेट्रोल पंप", "pump"),
                           ("गोदाम", "godown"), ("अख़बार", "headlines"), ("राशन कार्ड", "slip"), ("घड़ी", "clock"), ("स्क्रैच कार्ड", "chance"),
                           ("छपाई", "press"), ("चिमनी", "chimney"), ("समोसा", "food"), ("सिलाई मशीन", "machine"), ("हथकड़ी", "goods"),
                           ("टपरी", "stall"), ("सूखा", "natureSign"), ("नक़्शा", "cityMap")]:
            found = [r.get("name") for r in saanche.search(word, limit=12, icons_limit=0) if r.get("kind") == "draw"]
            self.assertIn(name, found, word)

    def test_no_words_baked_into_the_drawings(self):
        src = (ENGINE / "families" / "econ_things.mjs").read_text(encoding="utf-8")
        self.assertNotRegex(src, r"[ऀ-ॿ]")          # Hindi words come only from parameters
        for name in ("RBI", "SBI", "NIFTY", "Indian Oil", "Amul"):
            self.assertNotIn(name, src)


@unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
class Drawings(unittest.TestCase):
    def test_the_registry_has_the_family(self):
        keys = node(f"import {{DRAWS}} from '{(ENGINE / 'draw.mjs').as_posix()}'; console.log(JSON.stringify(Object.keys(DRAWS)));")
        for name in NAMES:
            self.assertIn(name, keys)
        fam = node(f"import '{(ENGINE / 'draw.mjs').as_posix()}'; import {{DRAWS}} from '{(ENGINE / 'families' / 'econ_things.mjs').as_posix()}';"
                   "console.log(JSON.stringify(Object.fromEntries(Object.entries(DRAWS).map(([k, v]) => [k, v.anchor]))));")
        self.assertEqual(sorted(fam), NAMES)
        for name, anchor in fam.items():
            self.assertEqual(anchor, FAMILY["saanche"][name]["anchor"], name)

    def test_every_saancha_draws_clean_svg_at_defaults_and_in_its_states(self):
        cases = [(n, {}) for n in NAMES] + VARIANTS
        svgs = node(f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                    f"const cases = {json.dumps(cases, ensure_ascii=False)};"
                    "console.log(JSON.stringify(cases.map(([n, p]) => drawSaancha(n, p))));")
        self.assertEqual(len(svgs), len(cases))
        for (name, p), svg in zip(cases, svgs):
            with self.subTest(name=name, p=p):
                self.assertTrue(svg.strip())
                self.assertNotRegex(svg, r"NaN|undefined|Infinity")
                self.assertTrue(balanced(svg))
                self.assertNotIn('stroke-width="-', svg)
                self.assertNotRegex(svg, r'(width|height|r)="-')

    def test_every_saancha_has_a_box_and_scales_with_w(self):
        boxes = node(f"import {{boxOf}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                     f"const names = {json.dumps(NAMES)};"
                     "console.log(JSON.stringify(names.map((n) => [boxOf(n, {w: 300}).box, boxOf(n, {w: 600}).box])));")
        for name, (a, b) in zip(NAMES, boxes):
            with self.subTest(name=name):
                self.assertIsNotNone(a)
                wa, wb = a[2] - a[0], b[2] - b[0]
                self.assertAlmostEqual(wb / wa, 2, delta=0.25)

    def test_a_process_is_a_pure_function_of_its_time_and_settles_without_it(self):
        script = (f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                  f"const cases = {json.dumps(PROCESSES, ensure_ascii=False)};"
                  "console.log(JSON.stringify(cases.map(([n, p]) => [drawSaancha(n, {...p, _t: 0.7, _s: 0.35}), drawSaancha(n, {...p, _t: 0.7, _s: 0.35}),"
                  " drawSaancha(n, {...p, _t: 2.45, _s: 2.1}), drawSaancha(n, p), drawSaancha(n, p)])));")
        for (name, p), (a, b, c, d, e) in zip(PROCESSES, node(script)):
            with self.subTest(name=name, p=p):
                self.assertEqual(a, b)                  # pure: the same times give the same frame
                self.assertNotEqual(a, c)               # and it moves as the video plays
                self.assertEqual(d, e)                  # no times: one settled drawing for the box measurement

    def test_states_change_on_their_parameters(self):
        pairs = [("produce", {"fill": 1}, {"fill": 0.2}), ("vehicle", {"state": "new"}, {"state": "writeoff"}),
                 ("houses", {"value": "₹50"}, {"value": "₹30", "loan": "₹40"}), ("slip", {"kind": "envelope"}, {"kind": "envelope", "sealed": False}),
                 ("machine", {"kind": "phone", "text": "₹200"}, {"kind": "phone", "text": "₹200", "screen": "cracked"}),
                 ("goods", {"kind": "padlock"}, {"kind": "padlock", "open": True}), ("cityMap", {"detail": 1}, {"detail": 0})]
        out = node(f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                   f"const cases = {json.dumps(pairs, ensure_ascii=False)};"
                   "console.log(JSON.stringify(cases.map(([n, a, b]) => [drawSaancha(n, a), drawSaancha(n, b)])));")
        for (name, a, b), (sa, sb) in zip(pairs, out):
            self.assertNotEqual(sa, sb, name)
        neg = node(f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                   "console.log(JSON.stringify([drawSaancha('houses', {value: '₹30 लाख', loan: '₹40 लाख'}), drawSaancha('houses', {value: '₹50 लाख', loan: '₹40 लाख'})]));")
        self.assertIn("#e5484d", neg[0])               # the value tag turns red under the loan (negative equity)
        self.assertNotIn('fill="#e5484d"', neg[1].split("₹50")[0][-400:])


@unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
class People(unittest.TestCase):
    def test_every_look_of_the_vocabulary_is_in_the_rig_and_draws_in_every_pose(self):
        vocab = sp.vocab()
        for look in LOOKS_NEW:
            self.assertIn(look, vocab["looks"])
        self.assertEqual(sorted(vocab["poses"]), sorted(sp.POSES))
        script = (f"import {{drawPerson, personBoxes, LOOKS, POSES}} from '{(ENGINE / 'people.mjs').as_posix()}';"
                  f"const looks = {json.dumps(vocab['looks'])}, poses = {json.dumps(vocab['poses'])};"
                  "const out = {missing: looks.filter((l) => !LOOKS[l]), poses: Object.keys(POSES), bad: [], boxes: {}};"
                  "for (const l of looks) { for (const p of poses) for (const f of [1, -1]) for (const w of [null, 0.4]) {"
                  "  const s = drawPerson({look: l, arms: p, facing: f, walkPhase: w, expr: 'happy', h: 440});"
                  "  if (!s || /NaN|undefined/.test(s)) out.bad.push(l + ':' + p); }"
                  "  out.boxes[l] = personBoxes({look: l, h: 440}); }"
                  "console.log(JSON.stringify(out));")
        out = node(script)
        self.assertEqual(out["missing"], [])
        self.assertEqual(sorted(out["poses"]), sorted(sp.POSES))
        self.assertEqual(out["bad"], [])
        for look, b in out["boxes"].items():
            with self.subTest(look=look):
                x0, y0, x1, y1 = b["face"]
                self.assertLess(y1 - y0, 0.4 * 440)       # the face box stays a face (head-wear included)
                self.assertGreater(b["box"][3] - b["box"][1], 0.9 * 440)

    def test_the_new_looks_differ_from_each_other(self):
        svgs = node(f"import {{drawPerson}} from '{(ENGINE / 'people.mjs').as_posix()}';"
                    f"console.log(JSON.stringify({json.dumps(LOOKS_NEW)}.map((l) => drawPerson({{look: l}}))));")
        self.assertEqual(len(set(svgs)), len(LOOKS_NEW))

    def test_the_old_looks_draw_exactly_as_before(self):
        script = (f"import {{drawPerson, personBoxes}} from '{(ENGINE / 'people.mjs').as_posix()}';"
                  f"const OLD = {json.dumps(LOOKS_OLD)}, P = {json.dumps(POSES_OLD)}; let all = '';"
                  "for (const look of OLD) for (const pose of P) for (const facing of [1, -1]) for (const expr of ['smile','happy','frown','sad','surprised'])"
                  "  for (const wp of [null, 0.3]) all += drawPerson({look, arms: pose, facing, expr, walkPhase: wp, h: 440, headDx: 3, headDy: 2});"
                  "for (const look of OLD) all += JSON.stringify(personBoxes({look, h: 440}));"
                  "console.log(JSON.stringify(all));")
        self.assertEqual(hashlib.sha256(node(script).encode("utf-8")).hexdigest(), OLD_LOOKS_SHA)

    def test_the_new_poses_are_known_to_the_compiler_and_the_rig(self):
        for pose in ("pull", "raise"):
            self.assertIn(pose, sp.POSES)
            self.assertIn(pose, sp.vocab()["poses"])
        rig = node(f"import {{POSES}} from '{(ENGINE / 'people.mjs').as_posix()}'; console.log(JSON.stringify(POSES));")
        for name, angles in sp.POSES.items():
            self.assertEqual(list(angles), rig[name], name)


if __name__ == "__main__":
    unittest.main()
