"""The econ_finance family of saanche (Sloman, Economics, 5 November 2026): the money and stock processes of the finance
and macro chapters. Every saancha in the family's manifest draws clean SVG at its defaults and in the variants a scene
plan will use, at every time (before, during and after a step); its words keep the 36 px floor at s = 1 and do not sit on
each other; the manifest and the engine registry agree; parameters out of range are refused; and a process is a pure
function of its times (the same params and times give the same SVG; time moves it)."""
from __future__ import annotations

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

ENGINE = ROOT / "bie" / "brain" / "video" / "engine"
FAMILY = ENGINE / "saanche.d" / "econ_finance.json"
NAMES = sorted(json.loads(FAMILY.read_text(encoding="utf-8"))["saanche"])
PROCESSES = ["circularFlow", "chainRounds", "tank", "balanceSheet", "timeValue", "gambleTree", "insurancePool", "queueLine",
             "contagion", "securitisation", "layers", "pricePath", "rateCorridor", "moneySplit", "tradeLedger", "road", "agents",
             "riskDial", "accountBar", "appliance", "usedCar", "certificate"]
VARIANTS = [
    ('circularFlow', {'households': 'परिवार', 'firms': 'कंपनियाँ', 'top': 'वस्तु बाज़ार', 'bottom': 'साधन बाज़ार', 'arrows': 'खर्च;माल;मज़दूरी;श्रम', 'realToken': 'labour', 'moneyToken': 'note', 'active': 'money', 'size': 2}),
    ('circularFlow', {'mode': 'income', 'households': 'परिवार', 'firms': 'कंपनियाँ', 'leaks': 'S:20;T:30;M:10', 'injections': 'I:25;G:30;X:15', 'sectors': 'बैंक;सरकार;विदेश', 'arrows': 'Cd;Y', 'income': 1000, 'incomeFrom': 900, 'unit': '₹', 'brackets': True, 'lit': 'S,I', 'outer': 'पर्यावरण', 'inputs': 'संसाधन', 'outputs': 'कचरा'}),
    ('circularFlow', {'mode': 'income', 'leaks': 'S:20', 'injections': 'I:20;G:x', 'brackets': True, 'active': 'none'}),
    ('chainRounds', {'start': 100, 'keep': 0.1, 'leak': 0.2, 'rounds': 4, 'unit': '₹', 'names': 'बैंक A;बैंक B;बैंक C;बैंक D', 'keepLabel': 'रिज़र्व', 'leakLabel': 'नकद', 'totalLabel': 'कुल जमा', 'upto': 3}),
    ('chainRounds', {'view': 'bars', 'start': 160, 'keep': 0, 'leak': 0.5, 'rounds': 5, 'unit': '₹ करोड़', 'leakLabel': 'बचत', 'passLabel': 'खर्च', 'totalLabel': 'कुल आय', 'final': True}),
    ('chainRounds', {'keep': 0, 'leak': 0, 'rounds': 1, 'node': 'person', 'total': False}),
    ('tank', {'ins': 'निवेश (J):0.6', 'outs': 'बचत (W):0.5', 'level': 0.7, 'from': 0.3, 'settle': True, 'label': 'राष्ट्रीय आय', 'marks': '0.7:Y₂;0.3:Y₁', 'value': 'Y', 'clock': 'flow'}),
    ('tank', {'ins': 'I:0.5;G:0.3;X:0.2', 'outs': 'S:0.4;T:0.3;M:0.2', 'level': 0.45, 'label': 'Y', 'clock': 'stock', 'grows': True, 'color': '#2a9d8f'}),
    ('tank', {'level': 0, 'from': 1}),
    ('balanceSheet', {'title': 'बैंक की बैलेंस शीट', 'leftHead': 'संपत्ति', 'rightHead': 'देनदारी', 'assets': 'नकद:10;कर्ज़:70<80;बॉन्ड:20', 'liabilities': 'जमा:90;पूंजी:10', 'unit': '₹', 'totalLabel': 'कुल', 'glow': 'a2', 'upto': 3}),
    ('balanceSheet', {'view': 'blocks', 'leftHead': 'संपत्ति', 'rightHead': 'देनदारी + पूंजी', 'assets': 'नकद:10;बॉन्ड:20;कर्ज़:70', 'liabilities': 'जमा:92;पूंजी:8', 'unit': '₹', 'loss': 12, 'lossLabel': 'घाटा', 'brokeLabel': 'दिवालिया'}),
    ('balanceSheet', {'assets': 'a:x', 'liabilities': '', 'cushion': False, 'totals': False}),
    ('timeValue', {'periods': 3, 'slots': 'आज;1 साल;2 साल;3 साल', 'amounts': '10000@1;30000@2;20000@3', 'rate': '0.1', 'travel': 3, 'sum': True, 'cost': 45000, 'unit': '₹', 'showFactor': 'number', 'title': 'वर्तमान मूल्य'}),
    ('timeValue', {'periods': 50, 'slots': 'आज', 'amounts': '100@50', 'rate': '0.01;0.05', 'travel': 1, 'unit': '₹'}),
    ('timeValue', {'periods': 4, 'amounts': '1000@0', 'rate': '0.1', 'travel': 1, 'dir': 'forward', 'unit': '₹', 'showFactor': 'symbol', 'sum': True}),
    ('timeValue', {'periods': 3, 'slots': '3pm;5pm;6pm;', 'now': 1, 'amounts': 'खर्च:-4@1;फ़ायदा:6@2', 'd': 0.9, 'b': 0.6, 'travel': 2, 'sum': True, 'net': True, 'cost': 1, 'sumLabel': 'NB'}),
    ('gambleTree', {'branches': 'जीत:1/10:1000;हार:9/10:0', 'sure': 'पक्का:80', 'unit': '₹', 'title': 'जुआ या पक्का?'}),
    ('gambleTree', {'branches': 'a:25%:400;b:0.5:100;c:0.25:-200;d:x:y', 'fly': True, 'unit': '₹', 'glow': 2, 'evLabel': 'औसत'}),
    ('insurancePool', {'n': 40, 'premium': 500, 'claim': 8000, 'share': 0.05, 'admin': 50, 'unit': '₹', 'phase': 'claim', 'labels': 'प्रीमियम;दावे;खर्च;बचत', 'pot': 'बीमा कोष', 'countLabel': 'दुर्घटना', 'title': 'साल 1'}),
    ('insurancePool', {'n': 100, 'types': 'कम जोखिम:0.01;ज़्यादा जोखिम:0.09', 'leave': 1, 'premium': 500, 'claim': 8000, 'unit': '₹', 'phase': 'premium', 'labels': 'प्रीमियम;दावे;खर्च;बचत', 'year': 3}),
    ('queueLine', {'n': 12, 'stock': 5, 'rate': 1, 'label': 'टिकट', 'stockLabel': 'बचे', 'cutLabel': 'खत्म', 'urgent': '9'}),
    ('queueLine', {'n': 12, 'stock': 5, 'rate': 1, 'label': 'अस्पताल', 'place': 'theatre', 'turnAway': 'wait', 'waiting': 4, 'waitLabel': 'प्रतीक्षा सूची', 'joinRate': 1}),
    ('queueLine', {'n': 20, 'stock': 20, 'served': 5, 'rate': 2, 'place': 'bank', 'label': 'बैंक', 'unit': '₹ लाख', 'vaultFull': 25}),
    ('queueLine', {'n': 6, 'stock': 2, 'place': 'gate', 'who': 'trucks', 'cut': False, 'showStock': False}),
    ('contagion', {'names': 'बैंक A;बैंक B;बैंक C;बैंक D;बैंक E', 'fail': '2,3,4', 'upto': 2, 'rescued': '4', 'rescuer': 'सरकार', 'sizes': '1,2,1,1,1', 'title': 'संकट'}),
    ('contagion', {'style': 'domino', 'n': 6, 'names': 'A;B;C;D;E;F', 'fail': '1,2,3,4,5,6', 'upto': 4, 'stop': '4', 'stopLabel': 'पूंजी'}),
    ('contagion', {'style': 'disc', 'layout': 'ring', 'names': 'A;B;C;D;E;F', 'links': '1>2;2>3;3>4;4>5;5>6;6>1;1>4;2>5;9>1;x', 'fail': '1,4', 'upto': 2}),
    ('securitisation', {'originator': 'बैंक', 'spv': 'SPV', 'tranches': 'सीनियर:70;मेज़नाइन:20;इक्विटी:10', 'holders': 'पेंशन फंड;बीमा कंपनी;विदेशी बैंक', 'stage': 4, 'default': 0.2, 'risk': True, 'riskLabel': 'जोखिम', 'cashLabel': 'EMI'}),
    ('securitisation', {'stage': 0, 'risk': True}),
    ('securitisation', {'stage': 2, 'loans': 24, 'holders': 'एक'}),
    ('layers', {'layers': 'Tier 2:2;AT1:1.5;CET1:4.5;संरक्षण:2.5;काउंटर-साइक्लिकल:2.5', 'marks': '8;10.5;13:13%', 'upto': 5, 'fillLayer': 5, 'fill': 0.4, 'title': 'Basel III', 'at': 3}),
    ('layers', {'mode': 'ladder', 'layers': 'नकद:0;बचत खाता:3;FD:6;बॉन्ड:7;होम लोन:9', 'cut': 2, 'cutLabel': 'तरल', 'cutBelow': 'कम तरल', 'at': 3, 'title': 'तरलता'}),
    ('pricePath', {'seed': 11, 'steps': 40, 'start': 100, 'vol': 3, 'ref': 100, 'refLabel': 'तय कीमत', 'aboveLabel': 'किसान', 'belowLabel': 'मिल', 'events': '10:अनुबंध;30:अप्रैल', 'dotLabel': '₹{y}', 'xLabel': 'समय', 'yLabel': 'कीमत', 'drawIn': 4}),
    ('pricePath', {'seed': 5, 'steps': 40, 'start': 50, 'vol': 1.5, 'bubble': '15,30', 'boom': 2.5, 'burst': 33, 'base': '0,50 40,58', 'baseName': 'असली मूल्य', 'gapLabel': 'बुलबुला', 'fromStep': True, 'drawIn': 2}),
    ('pricePath', {'points': '0,10 1,12 2,9 3,15', 'upto': 2, 'dot': False, 'smooth': True, 'ymin': 0, 'ymax': 20, 'title': 'शेयर'}),
    ('rateCorridor', {'ceiling': 6, 'policy': 5, 'floor': 4, 'labels': 'ऋण दर;बैंक दर;जमा दर', 'speed': 1.5, 'omo': True, 'omoLabel': 'OMO'}),
    ('rateCorridor', {'labels': 'ऋण दर;बैंक दर;जमा दर', 'mode': 'floor'}),
    ('rateCorridor', {'mode': 'broken', 'path': '0:5;3:5.4;6:6.8;10:7.5'}),
    ('moneySplit', {'parts': 'GST:10:कर दफ़्तर@government;आयात:10:बंदरगाह@warehouse;Cd:80:कारख़ाना@factory', 'unit': '₹', 'upto': 2, 'label': 'खर्च'}),
    ('moneySplit', {'total': 100, 'parts': 'a:60;b:40', 'split': False}),
    ('tradeLedger', {'left': 'कंपनी A', 'right': 'कंपनी B', 'items': 4, 'itemLabel': '10 परमिट', 'payLabel': '₹20,000', 'deal': True, 'leftRows': 'सफ़ाई:20000<40000;परमिट:-20000<0', 'rightRows': 'सफ़ाई:40000<20000;परमिट:20000<0', 'unit': '₹', 'totalLabel': 'कुल', 'cap': 20, 'capFrom': 24, 'capLabel': 'सीमा'}),
    ('tradeLedger', {'leftKind': 'house', 'rightKind': 'shop', 'itemKind': 'goods', 'items': 0, 'totals': False, 'leftRows': 'x:y'}),
    ('road', {'lanes': 2, 'cars': 0.8, 'speed': 0.2, 'busLane': True, 'gantry': '₹50', 'sideStreets': 2, 'sideCars': 0.6, 'houses': 5, 'fumes': True, 'parking': 'paid', 'label': 'MG रोड'}),
    ('road', {'lanes': 4, 'cars': 0.3, 'speed': 0.9, 'hovLane': True, 'parking': 'banned', 'houses': 1}),
    ('road', {'lanes': 1, 'pedestrian': True, 'parking': 'free', 'sideStreets': 3}),
    ('agents', {'mode': 'merge', 'n': 24, 'merge': 1, 'from': 0, 'label': 'प्रतिनिधि परिवार', 'shock': True}),
    ('agents', {'mode': 'merge', 'n': 12, 'merge': 0, 'vary': True, 'react': True, 'kinds': 'firms'}),
    ('agents', {'mode': 'belief', 'n': 24, 'share': 0.6, 'from': 0.1, 'belief': 'factory', 'label': 'महँगाई की उम्मीद'}),
    ('agents', {'mode': 'herd', 'n': 18, 'rate': 3, 'price': 100, 'priceStep': 5, 'label': 'शेयर', 'target': 'exchange'}),
    ('riskDial', {'kind': 'coin,spinner,fog', 'p': 0.5, 'outcome': 'heads', 'headsLabel': 'चित', 'labels': 'सिक्का;पहिया;शेयर'}),
    ('riskDial', {'kind': 'spinner', 'p': 1, 'win': False, 'pText': '1/2'}),
    ('riskDial', {'kind': 'x', 'outcome': 'tails', 'tailsLabel': 'पट'}),
    ('accountBar', {'balance': -300, 'from': 400, 'limit': 500, 'max': 1000, 'label': 'खाते में बाकी', 'limitLabel': 'ओवरड्राफ़्ट'}),
    ('accountBar', {'balance': 5000, 'limit': 0}),
    ('appliance', {'kind': 'fan', 'label': '₹1,500', 'on': False}),
    ('appliance', {'kind': 'fridge', 'open': 0.6, 'label': '₹20,000'}),
    ('appliance', {'kind': 'tanker', 'level': 0.6, 'label': '₹500', 'color': '#e5484d'}),
    ('appliance', {'kind': 'tv'}),
    ('appliance', {'kind': 'washer', 'label': '₹9,000'}),
    ('usedCar', {'kind': 'small', 'label': '₹3 लाख', 'moving': True}),
    ('usedCar', {'kind': 'luxury', 'color': '#2d3748', 'damage': 0.5}),
    ('usedCar', {'kind': 'suv', 'damage': 0.9, 'lemon': True, 'label': 'नींबू'}),
    ('usedCar', {'kind': 'bus'}),
    ('usedCar', {'kind': 'truck', 'label': 'माल'}),
    ('certificate', {'kind': 'policy', 'title': 'बीमा पॉलिसी', 'rows': 'कवर:₹5 लाख;प्रीमियम:₹500;एक्सेस:₹2,000', 'stamp': 'मंज़ूर'}),
    ('certificate', {'kind': 'form', 'title': 'फ़ॉर्म', 'rows': 'सिगरेट?;शराब?;बीमारी?', 'ticked': 2}),
    ('certificate', {'kind': 'degree', 'title': 'डिग्री', 'rows': 'नाम:सीता'}),
    ('certificate', {'kind': 'medical', 'title': 'मेडिकल', 'stamp': 'FIT', 'stampColor': '#2fa35b'})
] + [(n, {}) for n in NAMES]
TIMES = [[None, None], [0, 0], [0.7, 0.7], [2.5, 0.4], [9, 9]]

NODE = """
import { drawSaancha, boxOf, DRAWS } from %s;
const [cases, times] = JSON.parse(process.argv[1]);
const isSym = (t) => !/[\\p{L}\\p{N}]/u.test(t);
const out = cases.map(([n, p]) => times.map(([t, s]) => {
  const q = { ...p, _t: t ?? undefined, _s: s ?? undefined }, svg = drawSaancha(n, q), b = boxOf(n, q);
  const small = b.texts.filter((w) => !isSym(w.t) && w.px < 35.5).map((w) => w.t + " " + w.px);
  const over = [];
  for (let i = 0; i < b.texts.length; i++) for (let j = i + 1; j < b.texts.length; j++) {
    const a = b.texts[i].box, c = b.texts[j].box, ox = Math.min(a[2], c[2]) - Math.max(a[0], c[0]), oy = Math.min(a[3], c[3]) - Math.max(a[1], c[1]);
    if (ox > 4 && oy > 4 && (ox * oy) / Math.min((a[2] - a[0]) * (a[3] - a[1]), (c[2] - c[0]) * (c[3] - c[1])) > 0.15) over.push(b.texts[i].t + " | " + b.texts[j].t);
  }
  return { svg, small, over };
}));
console.log(JSON.stringify({ out, keys: Object.keys(DRAWS) }));
"""


def balanced(svg: str) -> bool:
    stack = []
    for close, tag, selfclose in re.findall(r"<(/?)([a-zA-Z]+)(?:\s[^<>]*?)?(/?)>", svg):
        if close:
            if not stack or stack.pop() != tag:
                return False
        elif not selfclose:
            stack.append(tag)
    return not stack


def run_node(cases, times):
    script = NODE % json.dumps((ENGINE / "draw.mjs").as_posix())
    res = subprocess.run(["node", "--input-type=module", "-e", script, json.dumps([cases, times], ensure_ascii=False)],
                         capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


class Manifest(unittest.TestCase):
    def test_the_family_is_in_the_library_with_hindi_and_english_words(self):
        self.assertEqual(sorted(PROCESSES), NAMES)
        data = json.loads(FAMILY.read_text(encoding="utf-8"))
        self.assertEqual(data["licence"], "MIT (BIE)")
        for name in NAMES:
            entry = saanche.get(name)
            self.assertIsNotNone(entry, name)
            self.assertEqual(entry["since"], "2026-11-05")
            self.assertTrue(any(not t.isascii() for t in entry["tags"]), name)
            self.assertTrue(any(t.isascii() for t in entry["tags"]), name)
            defaults = {k: v["default"] for k, v in entry["params"].items() if v["type"] != "color" or v["default"]}
            self.assertEqual(saanche.problems(name, defaults), [], name)

    def test_every_variant_passes_the_manifest(self):
        for name, p in VARIANTS:
            with self.subTest(name=name, p=p):
                self.assertEqual(saanche.problems(name, p), [])

    def test_out_of_range_parameters_are_refused(self):
        bad = [("chainRounds", {"keep": 2}), ("chainRounds", {"rounds": 9}), ("tank", {"level": 1.5}), ("tank", {"clock": "sundial"}),
               ("timeValue", {"periods": 2.5}), ("queueLine", {"n": 400}), ("contagion", {"style": "jenga"}), ("securitisation", {"stage": 7}),
               ("road", {"lanes": 9}), ("agents", {"mode": "dance"}), ("riskDial", {"p": -1}), ("usedCar", {"damage": "lots"}),
               ("balanceSheet", {"cushion": "yes"}), ("circularFlow", {"widht": 900}), ("layers", {"fill": 3}), ("tank", {"color": "blue"})]
        for name, p in bad:
            with self.subTest(name=name, p=p):
                self.assertTrue(saanche.problems(name, p))

    def test_a_search_in_hindi_finds_them(self):
        for word, name in [("चक्रीय", "circularFlow"), ("गुणक", "chainRounds"), ("टंकी", "tank"), ("बैलेंस", "balanceSheet"),
                           ("वर्तमान", "timeValue"), ("जुआ", "gambleTree"), ("बीमा", "insurancePool"), ("कतार", "queueLine"),
                           ("डोमिनो", "contagion"), ("प्रतिभूतिकरण", "securitisation"), ("बेसल", "layers"), ("बुलबुला", "pricePath"),
                           ("रेपो", "rateCorridor"), ("बँटवारा", "moneySplit"), ("परमिट", "tradeLedger"), ("जाम", "road"),
                           ("उम्मीदें", "agents"), ("अनिश्चितता", "riskDial"), ("ओवरड्राफ़्ट", "accountBar"), ("पंखा", "appliance"),
                           ("कार", "usedCar"), ("पॉलिसी", "certificate")]:
            found = [r.get("name") for r in saanche.search(word, limit=20, icons_limit=0) if r.get("kind") == "draw"]
            self.assertIn(name, found, word)


@unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
class Drawing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = run_node(VARIANTS, TIMES)

    def test_manifest_and_registry_agree(self):
        keys = set(self.res["keys"])
        for name in NAMES:
            self.assertIn(name, keys)
        self.assertEqual(sorted(json.loads(subprocess.run(["node", "--input-type=module", "-e",
            f"import '{(ENGINE / 'draw.mjs').as_posix()}'; import {{DRAWS}} from '{(ENGINE / 'families' / 'econ_finance.mjs').as_posix()}';"
            "console.log(JSON.stringify(Object.keys(DRAWS)))"], capture_output=True, text=True, check=True).stdout)), NAMES)

    def test_every_variant_draws_clean_svg_at_every_time(self):
        for (name, p), runs in zip(VARIANTS, self.res["out"]):
            for (t, s), r in zip(TIMES, runs):
                with self.subTest(name=name, p=p, t=t):
                    svg = r["svg"]
                    self.assertTrue(svg.strip())
                    self.assertNotRegex(svg, r"NaN|undefined|Infinity")
                    self.assertTrue(balanced(svg))
                    self.assertNotRegex(svg, r'(stroke-width|width|height|r|rx|ry)="-')

    def test_words_keep_the_floor_and_do_not_sit_on_each_other(self):
        for (name, p), runs in zip(VARIANTS, self.res["out"]):
            if not p:
                continue
            for (t, s), r in zip(TIMES, runs):
                with self.subTest(name=name, p=p, t=t):
                    self.assertEqual(r["small"], [])
                    self.assertEqual(r["over"], [])

    def test_a_process_is_a_pure_function_of_its_times(self):
        cases = [(n, p) for n, p in VARIANTS if p][::2]
        a, b = run_node(cases, TIMES)["out"], run_node(cases, TIMES)["out"]
        self.assertEqual(a, b)                                       # the same params and times give the same SVG
        moving = {"circularFlow": {}, "chainRounds": {"upto": 2}, "tank": {"from": 0.1, "level": 0.9}, "timeValue": {"amounts": "100@2", "travel": 1},
                  "gambleTree": {"fly": True}, "insurancePool": {"phase": "premium"}, "queueLine": {"rate": 1, "stock": 9},
                  "contagion": {"upto": 1}, "securitisation": {"stage": 1}, "pricePath": {"drawIn": 4}, "rateCorridor": {},
                  "moneySplit": {"upto": 1}, "tradeLedger": {"deal": True}, "road": {"cars": 0.5}, "agents": {"from": 0}, "riskDial": {},
                  "accountBar": {"from": 500, "balance": -200}, "balanceSheet": {"assets": "a:10<20", "liabilities": "b:10"},
                  "layers": {"layers": "a:1;b:2", "upto": 2}, "appliance": {"kind": "fan"}, "usedCar": {"moving": True},
                  "certificate": {"stamp": "OK"}}
        self.assertEqual(sorted(moving), NAMES)
        res = run_node(list(moving.items()), [[0.3, 0.3], [1.1, 1.1]])["out"]
        for (name, _), (early, late) in zip(moving.items(), res):
            with self.subTest(name=name):
                self.assertNotEqual(early["svg"], late["svg"])       # time moves it


class SharedFiles(unittest.TestCase):
    def test_the_family_is_registered_in_the_index(self):
        idx = (ENGINE / "families" / "index.mjs").read_text(encoding="utf-8")
        self.assertIn('import { DRAWS as econ_finance } from "./econ_finance.mjs";', idx)
        self.assertIn("...econ_finance,", idx)
        src = (ENGINE / "families" / "econ_finance.mjs").read_text(encoding="utf-8")
        self.assertNotRegex(src, r"Math\.random|Date\.now")      # no randomness without a seed, no clock


if __name__ == "__main__":
    unittest.main()
