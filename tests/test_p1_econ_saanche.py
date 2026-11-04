"""Economy kit, batches 3 and 4 (4 Nov 2026): the saanche learned from the economy reference videos.

institutionBadge, paper, disc, vault, crowd, centralBank, committee and moneyBag are in the manifest with Hindi and
English words, and draw clean SVG (no NaN or undefined, balanced tags) at their defaults and in the variants a scene
plan will use (every badge kind and paper kind, open and closed vaults, shaded crowds, labels in Hindi).
"""
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
NEW = ["institutionBadge", "paper", "disc", "vault", "crowd", "centralBank", "committee", "moneyBag",
       "building", "priceTag", "gauge", "foreignNote", "barrier", "segmentedBar", "cart", "piggyBank", "ruler", "hands"]
VARIANTS = (
    [("institutionBadge", {"kind": k, "name": n, "sub": "उप"}) for k, n in
     [("central_bank", "RBI"), ("bank", "SBI"), ("government", "सरकार"), ("regulator", "SEBI"), ("international", "IMF"),
      ("cooperative", "PACS"), ("committee", "MPC"), ("market", "NSE"), ("company", "XYZ")]]
    + [("paper", {"kind": k, "title": "शीर्षक", "year": "1934", "value": "₹1,000", "note": "6% हर साल", "stamp": "AMENDED"})
       for k in ("law", "bond", "licence", "contract", "bill", "report")]
    + [("paper", {"lines": 0}), ("paper", {"lines": 8, "title": ""})]
    + [("vault", {"door": d, "fill": f, "locked": lk, "label": "CRR", "tag": "0% ब्याज", "metal": m})
       for d, f, lk, m in [(0, 0, True, "gold"), (0.3, 0.12, True, "gold"), (0.7, 0.5, False, "steel"), (1, 1, False, "steel")]]
    + [("crowd", {"n": 140, "cols": 20, "share": 0.6, "shareLabel": "पहुँच", "restColor": "#e5484d", "restLabel": "बाहर",
                  "label": "140 करोड़ लोग", "dimRest": True}), ("crowd", {"n": 1, "cols": 1, "share": 1})]
    + [("committee", {"n": n, "name": "मौद्रिक नीति समिति", "sub": "6 सदस्य"}) for n in (1, 6, 12)]
    + [("moneyBag", {"w": 40, "sign": ""}), ("moneyBag", {"w": 400, "label": "विदेशी मुद्रा"})]
    + [("disc", {"text": "4.5%"}), ("disc", {"text": "FIXED", "color": "#2459a6"})]
    + [("centralBank", {"label": ""}), ("centralBank", {"label": "भारतीय रिज़र्व बैंक"})]
    + [("building", {"kind": k, "label": "नाम"}) for k in ("office", "government", "exchange", "house", "tower", "shop", "warehouse", "hut")]
    + [("paper", {"kind": k, "title": "Share", "value": "₹10"}) for k in ("share", "unit")]
    + [("priceTag", {"value": "₹65", "old": "₹50", "trend": "up"}), ("priceTag", {"value": "₹40", "trend": "down"}), ("priceTag", {"trend": "none"})]
    + [("gauge", {"value": v, "text": "0.64", "label": "HDI", "reverse": r}) for v, r in ((0, False), (0.5, True), (1, False))]
    + [("foreignNote", {"sign": s, "value": "50"}) for s in ("$", "€", "£", "¥", "¤")]
    + [("barrier", {"label": "रोक"}), ("barrier", {"w": 60})]
    + [("segmentedBar", {"parts": "Food:46;Fuel:7;Core:47", "cross": "1,2", "label": "CPI"}), ("segmentedBar", {"parts": "Food:46;Fuel:7;Core:47", "hide": "1,2", "label": "Core"}),
       ("segmentedBar", {"parts": "CRR:3;SLR:18;कर्ज़:79", "unit": "", "glow": "1"}), ("segmentedBar", {"parts": "", "shrink": False}), ("segmentedBar", {"parts": "a:0;b:0"})]
    + [("cart", {"content": c, "label": "म्यूचुअल फंड"}) for c in ("veg", "notes", "goods", "empty")]
    + [("piggyBank", {"label": "NBFC"}), ("ruler", {"min": 100, "max": 75000, "value": 6590, "text": "$6,590", "minLabel": "$100", "maxLabel": "$75,000"}),
       ("ruler", {"min": 20, "max": 85, "value": 90}), ("ruler", {"min": 5, "max": 5, "value": 5})]
    + [("paper", {"kind": k, "title": "IDR"}) for k in ("receipt", "invoice")]
    + [("hands", {"item": it, "from": "पैसा ज़्यादा", "to": "पैसे की ज़रूरत"}) for it in ("notes", "coin", "paper", "none")]
    + [(n, {}) for n in NEW]
)


def balanced(svg: str) -> bool:
    stack = []
    for close, tag, selfclose in re.findall(r"<(/?)([a-zA-Z]+)(?:\s[^<>]*?)?(/?)>", svg):
        if close:
            if not stack or stack.pop() != tag:
                return False
        elif not selfclose:
            stack.append(tag)
    return not stack


class EconSaanche(unittest.TestCase):
    def test_they_are_in_the_manifest_with_hindi_and_english_words(self):
        for name in NEW:
            entry = saanche.get(name)
            self.assertIsNotNone(entry, name)
            self.assertEqual(entry["since"], "2026-11-04")
            self.assertTrue(any(not t.isascii() for t in entry["tags"]), name)
            self.assertTrue(any(t.isascii() for t in entry["tags"]), name)

    def test_a_search_in_hindi_finds_them(self):
        for word, name in [("तिजोरी", "vault"), ("समिति", "committee"), ("कानून", "paper"), ("भीड़", "crowd"), ("थैली", "moneyBag"),
                           ("गोदाम", "building"), ("दाम", "priceTag"), ("मीटर", "gauge"), ("डॉलर", "foreignNote"), ("दीवार", "barrier"), ("बँटवारा", "segmentedBar"), ("ठेला", "cart"), ("गुल्लक", "piggyBank"), ("पैमाना", "ruler"), ("उधार", "hands")]:
            found = [r.get("name") for r in saanche.search(word) if r.get("kind") == "draw"]
            self.assertIn(name, found, word)

    @unittest.skipUnless(shutil.which("node"), "needs node (the toolbox lane has it)")
    def test_every_variant_draws_clean_svg(self):
        script = (f"import {{drawSaancha}} from '{(ENGINE / 'draw.mjs').as_posix()}';"
                  f"const cases = {json.dumps(VARIANTS, ensure_ascii=False)};"
                  "console.log(JSON.stringify(cases.map(([n, p]) => drawSaancha(n, p))));")
        out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True)
        svgs = json.loads(out.stdout)
        self.assertEqual(len(svgs), len(VARIANTS))
        for (name, params), svg in zip(VARIANTS, svgs):
            with self.subTest(name=name, params=params):
                self.assertTrue(svg.strip())
                self.assertNotRegex(svg, r"NaN|undefined")
                self.assertTrue(balanced(svg))
                self.assertNotIn("stroke-width=\"-", svg)


if __name__ == "__main__":
    unittest.main()
