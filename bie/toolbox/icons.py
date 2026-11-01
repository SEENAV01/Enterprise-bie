"""BIE's icon index: the icon sets the build-up canvas draws with (Task 046 Part C, 27 October 2026; Part D2, 1 November 2026).

- Twemoji graphics (jdecked/twemoji, ``assets/svg``): about 1,900 flat colour icons (skin-tone variants left out).
  Credit: "Twemoji graphics by Twitter, Inc and other contributors, CC BY 4.0".
- Font Awesome Free icons (FortAwesome/Font-Awesome, ``svgs/solid`` and ``svgs/regular``): about 2,300 one-colour icons
  with search terms. Brands are left out (logos are never used in lessons, CV-11). Credit: "Font Awesome Free by
  Fonticons, Inc., CC BY 4.0".
- Fluent Emoji (microsoft/fluentui-emoji, MIT, pinned commit below; Navin, 1 November 2026: "add Microsoft Fluent Emoji ... as
  an icon source with its 3D style, preferred for objects"): about 1,600 3D PNGs (``fl:<name>``, skin-tone variants left out,
  the default one kept). Credit: "Fluent Emoji by Microsoft, MIT". The licence policy allows MIT for this source only.
- BIE's own drawings (``bie:<name>``, ``icons/bie/``, drawn by ``tools/bie_objects.py``, CC0 1.0): Indian coins and notes in
  BIE's own style, never replicas (``docs/bie/BIE_MONEY_OBJECTS.md``), and the objects of a money lesson (cheque, passbook,
  QR stand, POS machine, phone, salt sack, cowrie shells, cattle, grain sack, cloth roll, gold bar, ledger). Read from the
  repository; no network.

The index (``icons/index.json.gz``, schema ``bie.icons/1``) is searched by the director (``search("bank")`` → ids like
``tw:1f3e6`` or ``fa:solid/building-columns``); ``copy`` puts the chosen files into a render's assets and writes
``icons/credits.json`` for the credit roll. Files come from a local checkout (``BIE_TWEMOJI_SVG``, ``BIE_FONTAWESOME_SVGS``,
``BIE_FLUENT_EMOJI``) or, one by one, from the GitHub repositories at the pinned tags below, through ``sources.cached`` (never
into git); BIE's own drawings come from the repository folder.

    python -m bie.toolbox.icons search bank
    python -m bie.toolbox.icons copy tw:1f3ea fa:solid/warehouse --dest ASSETS_DIR
    python -m bie.toolbox.icons build --twemoji DIR --fontawesome DIR [--fluent DIR] --out icons/index.json.gz
    python -m bie.toolbox.icons add-sets [--fluent DIR]     (re-make the fl and bie rows; the tw and fa rows stay as they are)
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import subprocess
import unicodedata
import urllib.parse
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_INDEX = HERE / "icons" / "index.json.gz"
SCHEMA = "bie.icons/1"
FLUENT_COMMIT = "1ffb34c752ecf5d402f04cfb4b392c77f57c54bc"     # microsoft/fluentui-emoji main on 1 November 2026 (commit of 24 August 2026)
BIE_DIR = HERE / "icons" / "bie"                                 # BIE's own drawings (tools/bie_objects.py)
SETS = {
    "tw": {"id": "twemoji", "licence": "CC BY 4.0", "credit": "Twemoji graphics by Twitter, Inc and other contributors",
           "licence_url": "https://creativecommons.org/licenses/by/4.0/", "source_url": "https://github.com/jdecked/twemoji",
           "tag": "v16.0.1", "raw": "https://raw.githubusercontent.com/jdecked/twemoji/v16.0.1/assets/svg/{file}",
           "env": "BIE_TWEMOJI_SVG", "title": "Twemoji graphics", "author": "Twitter, Inc and other contributors"},
    "fa": {"id": "fontawesome-free", "licence": "CC BY 4.0", "credit": "Font Awesome Free by Fonticons, Inc.",
           "licence_url": "https://creativecommons.org/licenses/by/4.0/", "source_url": "https://fontawesome.com",
           "tag": "7.3.1", "raw": "https://raw.githubusercontent.com/FortAwesome/Font-Awesome/7.3.1/svgs/{file}",
           "env": "BIE_FONTAWESOME_SVGS", "title": "Font Awesome Free", "author": "Fonticons, Inc."},
    # MIT, allowed for this source only (licence_policy.json, sources.approved_by_navin: fluentui-emoji, 1 November 2026)
    "fl": {"id": "fluentui-emoji", "licence": "MIT", "credit": "Fluent Emoji by Microsoft",
           "licence_url": f"https://github.com/microsoft/fluentui-emoji/blob/{FLUENT_COMMIT}/LICENSE",
           "source_url": "https://github.com/microsoft/fluentui-emoji", "tag": FLUENT_COMMIT,
           "raw": f"https://raw.githubusercontent.com/microsoft/fluentui-emoji/{FLUENT_COMMIT}/{{file}}",
           "env": "BIE_FLUENT_EMOJI", "title": "Fluent Emoji", "author": "Microsoft"},
    # BIE's own work (licence_policy.json, own_work: bie-objects); published as CC0 1.0
    "bie": {"id": "bie-objects", "licence": "CC0 1.0", "credit": "BIE's own drawings (Book Intelligence Engine)",
            "licence_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "source_url": "https://github.com/SEENAV01/Enterprise-bie/tree/main/bie/toolbox/icons/bie", "tag": "repo",
            "raw": "", "env": "", "title": "BIE's own drawings", "author": "BIE (Book Intelligence Engine)"},
}
ID = re.compile(r"^(tw:[0-9a-f-]{1,80}|fa:(solid|regular)/[a-z0-9-]{1,60}|fl:[a-z0-9-]{1,80}|bie:[a-z0-9-]{1,40})$")
# Ranking among the icons a query's words find (aliases come first anyway): BIE's own money drawings, then Fluent's 3D
# icons (Navin, 1 November 2026: "preferred for objects"), then colour icons, then line icons.
STYLE_BONUS = {"bie": 1.0, "fl": 0.75}
# Twemoji flags of real countries are fine (a flag is not a logo); company and brand marks do not exist in Twemoji.
SKIN = re.compile(r"-1f3f[b-f]")          # skin-tone variants: keep the default yellow only, to keep the index small
CREDIT_FIELDS = ("credit", "licence", "licence_url", "source_url")


class IconError(ValueError):
    pass


def set_of(icon_id: str) -> str:
    """The set prefix of an icon id: ``tw``, ``fa``, ``fl`` or ``bie``."""
    return str(icon_id).split(":", 1)[0]


# ---------------------------------------------------------------- the index

@lru_cache(maxsize=4)
def load(index: str | Path = DEFAULT_INDEX) -> dict:
    path = Path(index)
    text = gzip.open(path, "rt", encoding="utf-8").read() if path.suffix == ".gz" else path.read_text(encoding="utf-8")
    data = json.loads(text)
    if data.get("schema") != SCHEMA:
        raise IconError(f"{path}: not a {SCHEMA} index")
    return data


def by_id(index: str | Path = DEFAULT_INDEX) -> dict:
    return {r["id"]: r for r in load(index)["icons"]}


# What the maker says in words → the index's own names (Task 046 Part D1, Navin's verdict of 30 October 2026: "cross" found
# religious crosses instead of the cross mark, "wheat" did not find the sheaf). Hindi words, everyday synonyms and the emoji
# names of the things an economy lesson draws; an alias may name an icon id outright. Navin and the seekh log add entries.
ALIASES = {
    # marks
    "cross": ["tw:274c"], "cross mark": ["tw:274c"], "reject": ["tw:274c"], "wrong": ["tw:274c"], "गलत": ["tw:274c"], "रद्द": ["tw:274c"],
    "tick": ["tw:2705"], "check": ["tw:2705"], "accept": ["tw:2705"], "right": ["tw:2705"], "सही": ["tw:2705"], "मान्य": ["tw:2705"],
    "question": ["tw:2753"], "सवाल": ["tw:2753"], "प्रश्न": ["tw:2753"],
    # goods and commodities
    "wheat": ["tw:1f33e", "fa:solid/wheat-alt"], "grain": ["bie:grain-sack", "tw:1f33e", "fa:solid/wheat-alt"], "sheaf": ["tw:1f33e"], "rice": ["tw:1f33e"],
    "गेहूँ": ["tw:1f33e"], "गेहूं": ["tw:1f33e"], "अनाज": ["bie:grain-sack", "tw:1f33e"], "चावल": ["tw:1f35a"],
    # commodity money is drawn as BIE's own sack, cow, cowries and cloth (Part D2: the D1 stills drew salt as a salt shaker)
    "salt": ["bie:salt-sack", "tw:1f9c2"], "नमक": ["bie:salt-sack", "tw:1f9c2"], "cattle": ["bie:cattle", "tw:1f404"], "cow": ["bie:cattle", "tw:1f404"],
    "गाय": ["bie:cattle", "tw:1f404"], "मवेशी": ["bie:cattle", "tw:1f404"],
    "shell": ["tw:1f41a"], "shells": ["tw:1f41a"], "cowrie": ["bie:cowrie-shells", "tw:1f41a"], "कौड़ी": ["bie:cowrie-shells", "tw:1f41a"], "शंख": ["tw:1f41a"],
    "cloth": ["bie:cloth-roll", "tw:1f9f5", "tw:1f455"], "fabric": ["bie:cloth-roll", "tw:1f9f5"], "कपड़ा": ["bie:cloth-roll", "tw:1f9f5", "tw:1f455"],
    "कपड़े": ["tw:1f9f5", "tw:1f455"],
    "tea": ["tw:1f375"], "चाय": ["tw:1f375"], "tobacco": ["fa:solid/smoking"], "तम्बाकू": ["fa:solid/smoking"], "तंबाकू": ["fa:solid/smoking"],
    "oil": ["tw:1f6e2"], "तेल": ["tw:1f6e2"], "sugar": ["tw:1f36c"], "चीनी": ["tw:1f36c"], "groceries": ["tw:1f6cd"], "राशन": ["tw:1f6cd"],
    # money
    "coin": ["tw:1fa99"], "coins": ["tw:1fa99", "fa:solid/coins"], "सिक्का": ["tw:1fa99"], "सिक्के": ["tw:1fa99", "fa:solid/coins"],
    "gold": ["tw:1fa99", "fa:solid/coins"], "सोना": ["tw:1fa99"], "silver": ["tw:1fa99"], "चाँदी": ["tw:1fa99"], "चांदी": ["tw:1fa99"],
    "note": ["fa:solid/money-bill-1", "tw:1f4b5"], "notes": ["fa:solid/money-bill-1", "tw:1f4b5"], "banknote": ["fa:solid/money-bill-1", "tw:1f4b5"],
    "currency": ["fa:solid/money-bill-1"], "नोट": ["fa:solid/money-bill-1", "tw:1f4b5"], "कागज़ी": ["fa:solid/money-bill-1"],
    "rupee": ["fa:solid/indian-rupee-sign"], "rupees": ["fa:solid/indian-rupee-sign"], "रुपया": ["fa:solid/indian-rupee-sign"], "रुपये": ["fa:solid/indian-rupee-sign"],
    "money": ["tw:1f4b0", "fa:solid/money-bill-1"], "पैसा": ["tw:1f4b0"], "पैसे": ["tw:1f4b0"], "cash": ["tw:1f4b5"], "नकद": ["tw:1f4b5"],
    "pound": ["tw:1f4b7"],
    "cheque": ["bie:cheque", "fa:solid/money-check"], "check book": ["bie:cheque", "fa:solid/money-check"], "चेक": ["bie:cheque", "fa:solid/money-check"],
    "card": ["tw:1f4b3"], "debit card": ["tw:1f4b3"], "credit card": ["tw:1f4b3"], "कार्ड": ["tw:1f4b3"],
    "phone": ["tw:1f4f1"], "mobile": ["tw:1f4f1"], "upi": ["bie:phone", "bie:qr-stand", "tw:1f4f1", "fa:solid/qrcode"],
    "qr": ["bie:qr-stand", "fa:solid/qrcode"], "qr code": ["bie:qr-stand", "fa:solid/qrcode"],
    "मोबाइल": ["tw:1f4f1"], "फ़ोन": ["tw:1f4f1"], "फोन": ["tw:1f4f1"], "app": ["tw:1f4f1"],
    # currencies by name: the money they are (the v4 render of 31 October 2026 drew the Euro as a bank and the Yuan as arrows)
    "us dollar": ["tw:1f4b5", "fa:solid/dollar-sign"], "united states dollar": ["tw:1f4b5", "fa:solid/dollar-sign"],
    "dollar": ["tw:1f4b5", "fa:solid/dollar-sign"], "euro": ["tw:1f4b6", "fa:solid/euro-sign"],
    "japanese yen": ["tw:1f4b4", "fa:solid/yen-sign"], "yen": ["tw:1f4b4", "fa:solid/yen-sign"],
    "chinese yuan": ["fa:solid/yen-sign"], "yuan": ["fa:solid/yen-sign"], "renminbi": ["fa:solid/yen-sign"],
    "pound sterling": ["tw:1f4b7", "fa:solid/sterling-sign"], "sterling": ["fa:solid/sterling-sign"],
    "herders": ["tw:1f404"], "herder": ["tw:1f404"], "pastoral": ["tw:1f404"], "चरवाहे": ["tw:1f404"],
    # people by their role in a money story (the Money run of 31 October 2026 named them and found nothing)
    "payer": ["fa:solid/hand-holding-dollar"], "recipient": ["fa:solid/user-check"], "payee": ["fa:solid/user-check"],
    "receiver": ["fa:solid/user-check"], "creditor": ["fa:solid/user-tie"], "lender": ["fa:solid/user-tie"], "लेनदार": ["fa:solid/user-tie"],
    "debtor": ["fa:solid/user"], "borrower": ["fa:solid/user"], "देनदार": ["fa:solid/user"], "कर्ज़दार": ["fa:solid/user"],
    "porter": ["fa:solid/person-walking-luggage"], "traveller": ["fa:solid/person-walking-luggage", "tw:1f9f3"],
    "traveler": ["fa:solid/person-walking-luggage", "tw:1f9f3"], "यात्री": ["fa:solid/person-walking-luggage"],
    "neighbour": ["fa:solid/people-roof"], "neighbor": ["fa:solid/people-roof"], "पड़ोसी": ["fa:solid/people-roof"], "पड़ोसियों": ["fa:solid/people-roof"],
    "valuables": ["fa:solid/gem"], "issuing authority": ["fa:solid/stamp", "fa:solid/building-columns"],
    "deposit": ["fa:solid/piggy-bank"], "savings": ["fa:solid/piggy-bank"], "जमा": ["fa:solid/piggy-bank"], "बचत": ["fa:solid/piggy-bank"],
    "loan": ["fa:solid/hand-holding-dollar"], "उधार": ["fa:solid/hand-holding-dollar"], "कर्ज़": ["fa:solid/hand-holding-dollar"], "कर्ज": ["fa:solid/hand-holding-dollar"],
    "wallet": ["tw:1f45b"], "बटुआ": ["tw:1f45b"], "receipt": ["tw:1f9fe"], "रसीद": ["tw:1f9fe"], "bill": ["tw:1f9fe"],
    # places and institutions (never a logo or an emblem, CV-11: a generic building)
    "bank": ["tw:1f3e6"], "बैंक": ["tw:1f3e6"], "rbi": ["fa:solid/building-columns"], "central bank": ["fa:solid/building-columns"],
    "government": ["fa:solid/landmark"], "सरकार": ["fa:solid/landmark"], "state": ["fa:solid/landmark"], "parliament": ["fa:solid/landmark"],
    "shop": ["tw:1f3ea"], "store": ["tw:1f3ea"], "दुकान": ["tw:1f3ea"], "market": ["tw:1f3ea"], "बाज़ार": ["tw:1f3ea"], "बाजार": ["tw:1f3ea"],
    "factory": ["tw:1f3ed"], "फैक्ट्री": ["tw:1f3ed"], "कारखाना": ["tw:1f3ed"], "mint": ["tw:1f3ed", "fa:solid/coins"], "press": ["fa:solid/industry"],
    "house": ["tw:1f3e0"], "home": ["tw:1f3e0"], "घर": ["tw:1f3e0"], "office": ["tw:1f3e2"], "दफ़्तर": ["tw:1f3e2"],
    "port": ["tw:2693", "tw:1f6a2"], "ship": ["tw:1f6a2"], "जहाज़": ["tw:1f6a2"], "बंदरगाह": ["tw:2693"], "farm": ["tw:1f33e", "tw:1f69c"], "खेत": ["tw:1f33e"],
    "temple": ["tw:1f6d5"], "मंदिर": ["tw:1f6d5"], "school": ["tw:1f3eb"], "hospital": ["tw:1f3e5"], "court": ["fa:solid/gavel"], "अदालत": ["fa:solid/gavel"],
    "map": ["tw:1f5fa"], "नक्शा": ["tw:1f5fa"], "world": ["tw:1f30d"], "globe": ["tw:1f30d"], "दुनिया": ["tw:1f30d"],
    # people (generic figures only, card rule 8)
    "person": ["tw:1f9d1"], "people": ["tw:1f465"], "आदमी": ["tw:1f9d1"], "व्यक्ति": ["tw:1f9d1"], "लोग": ["tw:1f465"],
    "farmer": ["tw:1f9d1-200d-1f33e"], "किसान": ["tw:1f9d1-200d-1f33e"], "worker": ["tw:1f477"], "मज़दूर": ["tw:1f477"], "मजदूर": ["tw:1f477"],
    "buyer": ["tw:1f6cd"], "customer": ["tw:1f6cd"], "खरीदार": ["tw:1f6cd"], "ग्राहक": ["tw:1f6cd"], "seller": ["tw:1f9d1-200d-1f4bc"], "shopkeeper": ["tw:1f9d1-200d-1f4bc"],
    "दुकानदार": ["tw:1f9d1-200d-1f4bc"], "trader": ["tw:1f9d1-200d-1f4bc"], "king": ["tw:1f451"], "राजा": ["tw:1f451"], "ruler": ["tw:1f451"], "dynasty": ["tw:1f451"],
    "emperor": ["tw:1f451"], "सुल्तान": ["tw:1f451"], "teller": ["tw:1f9d1-200d-1f4bc"], "cashier": ["tw:1f9d1-200d-1f4bc"],
    # law, promise, limits, time
    "law": ["tw:1f4dc", "fa:solid/gavel"], "act": ["tw:1f4dc"], "rule": ["tw:1f4dc"], "कानून": ["tw:1f4dc"], "क़ानून": ["tw:1f4dc"], "नियम": ["tw:1f4dc"],
    "compulsory": ["tw:1f4dc", "fa:solid/stamp"], "mandatory": ["tw:1f4dc"], "अनिवार्य": ["tw:1f4dc"], "fiat": ["fa:solid/money-bill-1"],
    "claim slip": ["tw:1f9fe"], "redemption": ["tw:1fa99"], "standard": ["tw:1fa99"],
    "stamp": ["fa:solid/stamp"], "seal": ["fa:solid/stamp"], "मोहर": ["fa:solid/stamp"], "मुहर": ["fa:solid/stamp"], "scroll": ["tw:1f4dc"],
    "handshake": ["tw:1f91d"], "promise": ["tw:1f91d"], "trust": ["tw:1f91d"], "वादा": ["tw:1f91d"], "भरोसा": ["tw:1f91d"], "agreement": ["tw:1f91d"],
    "meter": ["fa:solid/gauge-high"], "gauge": ["fa:solid/gauge-high"], "limit": ["fa:solid/gauge-high"], "सीमा": ["fa:solid/gauge-high"],
    "scale": ["tw:2696"], "scales": ["tw:2696"], "balance": ["tw:2696"], "तराज़ू": ["tw:2696"], "तराजू": ["tw:2696"], "compare": ["tw:2696"],
    "calendar": ["tw:1f4c5"], "year": ["tw:1f4c5"], "date": ["tw:1f4c5"], "साल": ["tw:1f4c5"], "तारीख़": ["tw:1f4c5"], "clock": ["tw:1f550"], "time": ["tw:1f550"], "समय": ["tw:1f550"],
    "lock": ["tw:1f512"], "ताला": ["tw:1f512"], "key": ["tw:1f511"], "चाबी": ["tw:1f511"], "arrow": ["tw:27a1"], "exchange": ["tw:1f501"], "swap": ["tw:1f501"],
    "chart": ["tw:1f4c8"], "graph": ["tw:1f4c8"], "growth": ["tw:1f4c8"], "fall": ["tw:1f4c9"], "गिरावट": ["tw:1f4c9"], "बढ़त": ["tw:1f4c8"],
    "truck": ["tw:1f69a"], "ट्रक": ["tw:1f69a"], "train": ["tw:1f686"], "box": ["tw:1f4e6"], "package": ["tw:1f4e6"], "डिब्बा": ["tw:1f4e6"],
    "letter": ["tw:2709"], "envelope": ["tw:2709"], "चिट्ठी": ["tw:2709"], "document": ["tw:1f4c4"], "paper": ["tw:1f4c4"], "कागज़": ["tw:1f4c4"],
    "computer": ["tw:1f4bb"], "laptop": ["tw:1f4bb"], "server": ["fa:solid/server"], "network": ["fa:solid/network-wired"], "internet": ["tw:1f310"],
    "flag": ["tw:1f3f3"], "झंडा": ["tw:1f3f3"],
}


def _money_aliases() -> dict:
    """BIE's own money drawings for the words that name them (Task 046 Part D2, Navin's brief of 1 November 2026): a coin or
    a note by its denomination ("₹500 का नोट", "10 rupee coin", "50 paise", "चवन्नी"), and the money objects (passbook, QR
    stand, card machine, ledger, gold bar ...). A bare "coin", "coins" or "सिक्का" keeps the plain coin: a lesson about
    old gold coins must not show a modern ₹1."""
    out = {}
    hi = {"1": "एक", "2": "दो", "5": "पाँच", "10": "दस", "20": "बीस", "50": "पचास", "100": "सौ", "200": "दो सौ",
          "500": "पाँच सौ", "2000": "दो हज़ार"}
    coins, notes = ("1", "2", "5", "10", "20"), ("10", "20", "50", "100", "200", "500", "2000")
    for d in coins:
        ids = [f"bie:coin-{d}"]
        for key in (f"₹{d} coin", f"{d} rupee coin", f"{d} rupees coin", f"{d} का सिक्का", f"₹{d} का सिक्का", f"{d} रुपये का सिक्का",
                    f"{d} रुपए का सिक्का", f"{hi[d]} रुपये का सिक्का", f"{hi[d]} रुपए का सिक्का"):
            out[key] = ids
    for d in notes:
        ids = [f"bie:note-{d}"]
        for key in (f"₹{d} note", f"{d} note", f"{d} rupee note", f"{d} rupees note", f"{d} का नोट", f"₹{d} का नोट",
                    f"{d} रुपये का नोट", f"{d} रुपए का नोट", f"{hi[d]} का नोट", f"{hi[d]} रुपये का नोट"):
            out[key] = ids
    for d in sorted(set(coins) | set(notes), key=int):          # "₹10" alone: the note and the coin
        out[f"₹{d}"] = ([f"bie:note-{d}"] if d in notes else []) + ([f"bie:coin-{d}"] if d in coins else [])
    out.update({"दो हजार का नोट": ["bie:note-2000"], "पांच सौ का नोट": ["bie:note-500"],          # spelling variants
                "पांच रुपये का सिक्का": ["bie:coin-5"], "पांच रुपए का सिक्का": ["bie:coin-5"]})
    for d, word, coin_word in (("50", "पचास", "अठन्नी"), ("25", "पच्चीस", "चवन्नी")):
        ids = [f"bie:coin-{d}p"]
        for key in (f"{d} paise", f"{d} paisa", f"{d} p", f"{d} पैसे", f"{d} पैसा", f"{word} पैसे", f"{d} पैसे का सिक्का", coin_word):
            out[key] = ids
    out.update({"athanni": ["bie:coin-50p"], "chavanni": ["bie:coin-25p"], "chawanni": ["bie:coin-25p"],
                "paise": ["bie:coin-50p", "bie:coin-25p"], "rupee coin": ["bie:coin-1", "tw:1fa99"], "एक रुपया": ["bie:coin-1"],
                "cheque book": ["bie:cheque", "fa:solid/money-check"], "चेकबुक": ["bie:cheque", "fa:solid/money-check"],
                "passbook": ["bie:passbook"], "pass book": ["bie:passbook"], "bank book": ["bie:passbook"], "पासबुक": ["bie:passbook"],
                "पास बुक": ["bie:passbook"], "bank account": ["bie:passbook", "tw:1f3e6"], "खाता": ["bie:passbook", "bie:ledger"],
                "upi scanner": ["bie:qr-stand", "fa:solid/qrcode"], "qr stand": ["bie:qr-stand"], "scan and pay": ["bie:qr-stand"],
                "क्यूआर": ["bie:qr-stand"], "क्यूआर कोड": ["bie:qr-stand"],
                "upi payment": ["bie:phone", "bie:qr-stand"], "phone payment": ["bie:phone"], "payment screen": ["bie:phone"],
                "digital payment": ["bie:phone", "bie:qr-stand"], "online payment": ["bie:phone"], "डिजिटल भुगतान": ["bie:phone", "bie:qr-stand"],
                "ऑनलाइन भुगतान": ["bie:phone"],
                "pos": ["bie:pos-machine"], "pos machine": ["bie:pos-machine"], "card machine": ["bie:pos-machine"],
                "swipe machine": ["bie:pos-machine"], "card terminal": ["bie:pos-machine"], "payment terminal": ["bie:pos-machine"],
                "कार्ड मशीन": ["bie:pos-machine"], "स्वाइप मशीन": ["bie:pos-machine"],
                "salt sack": ["bie:salt-sack"], "नमक की बोरी": ["bie:salt-sack"], "grain sack": ["bie:grain-sack"],
                "sack of grain": ["bie:grain-sack"], "अनाज की बोरी": ["bie:grain-sack"], "बोरी": ["bie:grain-sack", "bie:salt-sack"],
                "cowrie shell": ["bie:cowrie-shells"], "कौड़ियाँ": ["bie:cowrie-shells"], "कौड़ियां": ["bie:cowrie-shells"],
                "livestock": ["bie:cattle", "tw:1f404"], "पशु": ["bie:cattle", "tw:1f404"],
                "cloth roll": ["bie:cloth-roll"], "bolt of cloth": ["bie:cloth-roll"], "थान": ["bie:cloth-roll"], "textile": ["bie:cloth-roll"],
                "gold bar": ["bie:gold-bar"], "ingot": ["bie:gold-bar"], "bullion": ["bie:gold-bar"], "gold biscuit": ["bie:gold-bar"],
                "gold standard": ["bie:gold-bar", "tw:1fa99"], "gold reserve": ["bie:gold-bar"], "सोने की ईंट": ["bie:gold-bar"],
                "सोने का बिस्कुट": ["bie:gold-bar"],
                "ledger": ["bie:ledger", "tw:1f4d2"], "account book": ["bie:ledger"], "accounts book": ["bie:ledger"],
                "bahi khata": ["bie:ledger"], "बही": ["bie:ledger"], "बही खाता": ["bie:ledger"], "हिसाब": ["bie:ledger"]})
    return out


_MONEY = _money_aliases()
assert not set(_MONEY) & set(ALIASES), sorted(set(_MONEY) & set(ALIASES))      # the drawings add words; the words above stay as they are
ALIASES.update(_MONEY)

# Religious symbols come up only when the words ask for them (Navin, 30 October 2026: "cross" is the cross mark, not a crucifix).
RELIGIOUS = re.compile(r"orthodox cross|latin cross|star of david|wheel of dharma|dharmachakra|menorah|om symbol|\bom\b|star and crescent|"
                       r"yin yang|peace symbol|khanda|place of worship|church|mosque|synagogue|kaaba|hindu temple|prayer|torah|cross$|crucifix",
                       re.IGNORECASE)
RELIGION_WORDS = re.compile(r"religio|church|christian|crucifix|hindu|muslim|islam|jew|sikh|buddh|temple|mosque|synagogue|worship|prayer|धर्म|मंदिर|मस्जिद|गिरजा",
                            re.IGNORECASE)


def _alias_ids(words: list) -> list:
    """The icon ids the aliases name for a query's words, in the order the query names the things ("Cheques and deposits":
    the cheque first); at one place the longest alias wins ("check book" before "book")."""
    text = " ".join(words)
    hits = []
    for key in ALIASES:
        plural = r"(?:e?s)?" if re.fullmatch(r"[₹a-z0-9 ]*[a-z]", key) else ""          # "cheques", "receipts", "deposits", "500 notes"
        # whole words: "warehouse" is not a house, "₹100" is not "₹10"
        m = re.search(r"(?<![a-z0-9\u0900-\u097f])" + re.escape(key) + plural + r"(?![a-z0-9\u0900-\u097f])", text)
        if m:
            hits.append((m.start(), -len(key), key))
    out = []
    for _, _, key in sorted(hits):
        out += [i for i in ALIASES[key] if i not in out]
    return out


def _words(query: str) -> list:
    """The query's words: Latin and Devanagari words and numbers, a number keeping its rupee sign ("₹500 का नोट" → ₹500, का,
    नोट; "50 paise" → 50, paise), so a denomination finds its own coin or note (Part D2)."""
    return [w for w in re.findall(r"₹?[0-9]+|[a-z]+|[\u0900-\u097f]+", query.lower())]


def search(query: str, index: str | Path = DEFAULT_INDEX, limit: int = 12, *, religious: bool | None = None) -> list:
    """Icons for a thing named in words: the aliases first (Hindi words, synonyms, emoji names, BIE's own money drawings), then
    the icons whose name or search terms carry the query's words; among those BIE's own drawings rank first, then Fluent's 3D
    icons, then colour icons, then line icons (``STYLE_BONUS``). Religious symbols only when the query asks for them
    (``religious``: None reads the query, True keeps them, False drops them)."""
    data = load(index)["icons"]
    known = {r["id"]: r for r in data}
    q = _words(query)
    keep_religious = RELIGION_WORDS.search(query) is not None if religious is None else religious
    out = [known[i] for i in _alias_ids(q) if i in known]
    scored = []
    latin = [w for w in q if re.fullmatch(r"[a-z]+", w)]
    for r in data:
        if r["id"] in {o["id"] for o in out}:
            continue
        if not keep_religious and RELIGIOUS.search(r["name"]):
            continue
        hay = (r["name"] + " " + " ".join(r["terms"])).lower()
        # a word of the query counts where a word of the icon starts with it ("coin" finds "coins"), never inside another word
        # (the Money run of 31 October 2026: "lender" found "blender")
        s = sum(3 if re.search(rf"\b{w}\b", r["name"].lower()) else (1 if re.search(rf"\b{w}", hay) else 0) for w in latin)
        if s:
            scored.append((s + STYLE_BONUS.get(set_of(r["id"]), 0.5 if r["style"] == "colour" else 0), r))
    scored.sort(key=lambda t: -t[0])
    return (out + [r for _, r in scored])[:limit]


FIT_STOP = frozenset("of the a an and with for on in to at by from its their or".split())


def _stem(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def fits(query: str, row: dict) -> bool:
    """An icon is a picture OF the thing (not a near word): an alias names it for the query, or every content word of the query
    (Latin words without the small words; numbers and signs are text, not the thing) starts a word of its name or search terms
    (Navin's addendum of 2 November 2026: "jis cheej ka jikar hai wohi cheej dikhe"; the Money run c: "payment claim" found a
    baggage claim, "net banking screen" a mosquito net). A query with no such word fits by an alias only."""
    q = _words(query)
    if row.get("id") in _alias_ids(q):
        return True
    words = [w for w in q if re.fullmatch(r"[a-z]+", w) and w not in FIT_STOP and len(w) > 1]
    if not words:
        return False
    hay = (row.get("name", "") + " " + " ".join(row.get("terms") or [])).lower()
    return all(re.search(rf"\b{re.escape(_stem(w))}", hay) for w in words)


def fitting(query: str, index: str | Path = DEFAULT_INDEX, limit: int = 12) -> list:
    """The icons of ``search`` that are pictures of the thing (``fits``), best first."""
    return [r for r in search(query, index, limit=limit) if fits(query, r)]


def search_nouns(nouns, index: str | Path = DEFAULT_INDEX, per_noun: int = 3) -> dict:
    """{noun: [icon rows]} for the things a beat names; a noun with no icon maps to [] (the needs list picks it up)."""
    return {n: search(n, index, limit=per_noun) for n in nouns if str(n).strip()}


def check_ids(ids, index: str | Path = DEFAULT_INDEX) -> list:
    """The ids a plan names that the index does not have (so a plan is refused before any render)."""
    known = by_id(index)
    return [i for i in ids if not (isinstance(i, str) and ID.match(i) and i in known)]


def safe(icon_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", icon_id.lower()).strip("-")


# ---------------------------------------------------------------- the files

def _local_dir(prefix: str) -> Path | None:
    env = SETS[prefix]["env"]
    folder = os.environ.get(env) if env else None
    return Path(folder) if folder and Path(folder).is_dir() else None


def suffix(icon_id: str, index: str | Path = DEFAULT_INDEX) -> str:
    """The file type of an icon: ``.svg`` (Twemoji, Font Awesome, BIE's drawings) or ``.png`` (Fluent's 3D icons)."""
    row = by_id(index).get(icon_id) or {}
    return Path(row.get("file", "x.svg")).suffix.lower() or ".svg"


MIME = {".svg": "image/svg+xml", ".png": "image/png"}


def icon_file(icon_id: str, *, index: str | Path = DEFAULT_INDEX, opener=None) -> Path:
    """The file of one icon: BIE's own drawings from the repository folder; the others from the local checkout when its folder
    is set, else fetched once from the pinned tag or commit on GitHub into the asset cache (outside git)."""
    row = by_id(index).get(icon_id)
    if row is None:
        raise IconError(f"{icon_id!r} is not in the icon index")
    prefix = set_of(icon_id)
    if prefix == "bie":
        path = BIE_DIR / row["file"]
        if not path.is_file():
            raise IconError(f"{icon_id}: {path} is missing (python tools/bie_objects.py draws it)")
        return path
    local = _local_dir(prefix)
    if local is not None:
        path = local / row["file"]
        if not path.exists():
            raise IconError(f"{icon_id}: {path} is missing from {SETS[prefix]['env']}")
        return path
    from . import sources
    url = SETS[prefix]["raw"].format(file=urllib.parse.quote(row["file"]))
    return sources.cached(url, f"icon-{SETS[prefix]['id']}-{SETS[prefix]['tag']}-{safe(icon_id)}{suffix(icon_id, index)}", opener=opener)


def copy(ids, dest: str | Path, *, index: str | Path = DEFAULT_INDEX, colour: str = "#2b3a4a", opener=None) -> dict:
    """Copy the icons into ``<dest>/icons/`` (Font Awesome's one-colour paths get ``colour``) and write
    ``<dest>/icons/credits.json``; returns icon id → asset path for the plan compiler."""
    rows = by_id(index)
    bad = check_ids(ids, index)
    if bad:
        raise IconError("unknown icon ids: " + ", ".join(map(str, bad)))
    dest = Path(dest)
    (dest / "icons").mkdir(parents=True, exist_ok=True)
    credits, out = {}, {}
    for i in ids:
        r = rows[i]
        src = icon_file(i, index=index, opener=opener)
        name = safe(i) + suffix(i, index)
        dst = dest / "icons" / name
        if i.startswith("fa:"):
            dst.write_text(_coloured(src.read_text(encoding="utf-8"), colour), encoding="utf-8")
        else:
            shutil.copy2(src, dst)
        credits[r["credit"]] = {k: r[k] for k in CREDIT_FIELDS}
        out[i] = "icons/" + name
    (dest / "icons" / "credits.json").write_text(json.dumps(sorted(credits.values(), key=lambda c: c["credit"]), indent=1),
                                                encoding="utf-8")
    return out


def _coloured(svg: str, colour: str) -> str:
    """Font Awesome's one-colour paths take the canvas ink colour (the files say ``currentColor`` or nothing)."""
    if 'fill="currentColor"' in svg:
        return svg.replace('fill="currentColor"', f'fill="{colour}"')
    return svg.replace("<path ", f'<path fill="{colour}" ')


def add_to_library(ids, library, *, index: str | Path = DEFAULT_INDEX, opener=None, colour: str = "#2b3a4a") -> dict:
    """The icons as assets of a lesson's ``AssetLibrary`` (the credit fields recorded, so the licence gate and the credit
    roll read them); returns icon id → ``assets/...`` path for the plan compiler and the renderer."""
    rows = by_id(index)
    bad = check_ids(ids, index)
    if bad:
        raise IconError("unknown icon ids: " + ", ".join(map(str, bad)))
    out = {}
    for i in ids:
        r, s = rows[i], SETS[set_of(i)]
        data = icon_file(i, index=index, opener=opener).read_bytes()
        if i.startswith("fa:"):
            data = _coloured(data.decode("utf-8"), colour).encode("utf-8")
        asset = library.add_bytes(data, mime=MIME[suffix(i, index)], source=s["id"], title=f"{r['name']} ({i})", page_url=s["source_url"],
                                  licence=s["licence"], licence_url=s["licence_url"], author=s["author"],
                                  credit=s["credit"] + ", " + s["licence"], tags=["icon", s["id"]])
        out[i] = "assets/" + asset.path
    return out


def credit_assets(ids, index: str | Path = DEFAULT_INDEX) -> list:
    """The icons as asset records the licence gate reads (``licence.lesson_credits``), one per set used."""
    rows = by_id(index)
    seen, out = set(), []
    for i in ids:
        prefix = set_of(i)
        if prefix in seen or i not in rows:
            continue
        seen.add(prefix)
        s = SETS[prefix]
        out.append({"asset_id": s["id"], "title": s["title"], "author": s["author"],
                    "licence": s["licence"], "licence_url": s["licence_url"], "page_url": s["source_url"], "source": s["id"],
                    "credit": s["credit"] + ", " + s["licence"]})
    return out


# ---------------------------------------------------------------- building the index (one-time, from local checkouts)

def tw_name(stem: str) -> str:
    names = []
    for part in stem.split("-"):
        try:
            cp = int(part, 16)
        except ValueError:
            continue
        if cp in (0x200D, 0xFE0F):
            continue
        try:
            names.append(unicodedata.name(chr(cp)).lower())
        except ValueError:
            if 0x1F1E6 <= cp <= 0x1F1FF:
                names.append("flag letter " + chr(cp - 0x1F1E6 + 65))
    return " + ".join(names)


def _rows_of(prefix: str, made: list) -> list:
    return [dict(r, **{k: SETS[prefix][k] for k in CREDIT_FIELDS}) for r in made]


def twemoji_rows(twemoji: str | Path) -> list:
    rows = []
    for f in sorted(os.listdir(twemoji)):
        if not f.endswith(".svg") or SKIN.search(f):
            continue
        stem = f[:-4]
        name = tw_name(stem)
        if not name:
            continue
        terms = sorted(set(re.findall(r"[a-z]+", name)))
        rows.append({"id": "tw:" + stem, "name": name, "terms": terms, "style": "colour", "file": f})
    return _rows_of("tw", rows)


def fontawesome_rows(fontawesome: str | Path) -> list:
    rows, meta = [], {}
    families = Path(fontawesome).parent / "metadata" / "icon-families.json"
    if families.exists():
        meta = json.loads(families.read_text(encoding="utf-8"))
    for style in ("solid", "regular"):                # never brands (CV-11)
        d = Path(fontawesome) / style
        if not d.is_dir():
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".svg"):
                continue
            stem = f[:-4]
            m = meta.get(stem, {})
            terms = sorted(set([stem.replace("-", " ")] + [str(t) for t in (m.get("search", {}) or {}).get("terms", []) or []]))
            rows.append({"id": f"fa:{style}/{stem}", "name": m.get("label", stem.replace("-", " ")), "terms": terms,
                         "style": "line", "file": f"{style}/{f}"})
    return _rows_of("fa", rows)


def fl_slug(folder: str) -> str:
    """``Thumbs up`` → ``thumbs-up``, ``Piñata`` → ``pinata``."""
    text = unicodedata.normalize("NFKD", folder).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


# Fluent Emoji has no logos; a flag named "flag: ..." (a country, a region or an organisation) would be left out like a brand.
FLUENT_SKIP = re.compile(r"^flag:|\blogo\b", re.IGNORECASE)


def _fluent_paths(checkout: Path) -> list:
    """Every file path of the Fluent Emoji checkout: from git (a sparse, blob-less clone has the PNGs only in its tree; the
    commit must be the pinned one) or, without git, from the folder."""
    if (checkout / ".git").exists():
        head = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        if head != FLUENT_COMMIT:
            raise IconError(f"{checkout} is at {head}; the index pins microsoft/fluentui-emoji at {FLUENT_COMMIT}")
        listed = subprocess.run(["git", "-C", str(checkout), "ls-tree", "-r", "--name-only", "-z", "HEAD"], capture_output=True,
                                check=True).stdout.decode("utf-8")
        return [x for x in listed.split("\0") if x]
    return sorted(p.relative_to(checkout).as_posix() for p in checkout.rglob("*") if p.is_file())


def fluent_rows(checkout: str | Path) -> list:
    """The 3D icon of every Fluent emoji (``assets/<Name>/3D/<name>_3d.png``; for an emoji with skin tones the Default one,
    ``assets/<Name>/Default/3D/...``), named by its metadata (CLDR name, keywords)."""
    root = Path(checkout)
    found = {}
    for path in _fluent_paths(root):
        parts = path.split("/")
        if parts[0] != "assets" or not path.endswith(".png"):
            continue
        if len(parts) == 4 and parts[2] == "3D":
            found[parts[1]] = path
        elif len(parts) == 5 and parts[2] == "Default" and parts[3] == "3D":
            found.setdefault(parts[1], path)
    rows, seen = [], set()
    for folder in sorted(found):
        meta = json.loads((root / "assets" / folder / "metadata.json").read_text(encoding="utf-8"))
        name = str(meta.get("cldr") or folder).strip()
        if FLUENT_SKIP.search(name):
            continue
        slug = fl_slug(folder)
        if slug in seen:
            raise IconError(f"Fluent Emoji: two folders make the id fl:{slug}")
        seen.add(slug)
        terms = sorted({str(k).lower() for k in meta.get("keywords") or []} | set(re.findall(r"[a-z]+", name.lower())))
        rows.append({"id": "fl:" + slug, "name": name, "terms": terms, "style": "3d", "file": found[folder]})
    return _rows_of("fl", rows)


def bie_rows(folder: str | Path = BIE_DIR) -> list:
    """BIE's own drawings from their catalogue (``icons/bie/objects.json``, written by ``tools/bie_objects.py``)."""
    data = json.loads((Path(folder) / "objects.json").read_text(encoding="utf-8"))
    return _rows_of("bie", [{"id": o["id"], "name": o["name"], "terms": list(o["terms"]), "style": "colour", "file": o["file"]}
                           for o in data["objects"]])


def write_index(rows: list, out: str | Path = DEFAULT_INDEX) -> dict:
    data = {"schema": SCHEMA, "count": len(rows), "icons": rows}
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if out.suffix == ".gz":
        with open(out, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as fh:   # the same bytes every time
            fh.write(text.encode("utf-8"))
    else:
        out.write_text(text, encoding="utf-8")
    load.cache_clear()
    return data


def build(twemoji: str | Path | None, fontawesome: str | Path | None, out: str | Path = DEFAULT_INDEX, *,
          fluent: str | Path | None = None) -> dict:
    """The whole index from local checkouts (Twemoji's ``assets/svg``, Font Awesome's ``svgs``, the Fluent Emoji clone) and
    BIE's own drawings."""
    rows = (twemoji_rows(twemoji) if twemoji else []) + (fontawesome_rows(fontawesome) if fontawesome else [])
    rows += (fluent_rows(fluent) if fluent else []) + bie_rows()
    return write_index(rows, out)


def add_sets(index: str | Path = DEFAULT_INDEX, out: str | Path | None = None, *, fluent: str | Path | None = None) -> dict:
    """Re-make the Fluent rows (from the clone, when given; else they stay) and BIE's rows (from their catalogue) in an existing
    index; the Twemoji and Font Awesome rows stay exactly as they are."""
    old = load(index)["icons"]
    keep = [r for r in old if set_of(r["id"]) in ("tw", "fa")]
    fl = fluent_rows(fluent) if fluent else [r for r in old if set_of(r["id"]) == "fl"]
    return write_index(keep + fl + bie_rows(), out or index)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["build", "add-sets", "search", "copy"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--twemoji", default=os.environ.get("BIE_TWEMOJI_SVG", ""))
    ap.add_argument("--fontawesome", default=os.environ.get("BIE_FONTAWESOME_SVGS", ""))
    ap.add_argument("--fluent", default="", help="a clone of microsoft/fluentui-emoji at the pinned commit (metadata is enough)")
    ap.add_argument("--index", default=str(DEFAULT_INDEX))
    ap.add_argument("--out", default=str(DEFAULT_INDEX))
    ap.add_argument("--dest", default="")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        data = build(a.twemoji, a.fontawesome, a.out, fluent=a.fluent or None)
        print("icons", data["count"], "->", a.out)
    elif a.cmd == "add-sets":
        data = add_sets(a.index, a.out, fluent=a.fluent or None)
        counts = {}
        for r in data["icons"]:
            counts[set_of(r["id"])] = counts.get(set_of(r["id"]), 0) + 1
        print("icons", data["count"], counts, "->", a.out)
    elif a.cmd == "search":
        for r in search(" ".join(a.args), a.index):
            print(r["id"], "|", r["name"], "|", r["style"])
    else:
        if not a.dest:
            raise SystemExit("copy needs --dest")
        print(json.dumps(copy(a.args, a.dest, index=a.index), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
