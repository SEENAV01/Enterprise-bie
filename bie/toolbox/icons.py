"""BIE's icon index: two CC BY 4.0 icon sets the build-up canvas draws with (Task 046 Part C, 27 October 2026).

- Twemoji graphics (jdecked/twemoji, ``assets/svg``): about 1,900 flat colour icons (skin-tone variants left out).
  Credit: "Twemoji graphics by Twitter, Inc and other contributors, CC BY 4.0".
- Font Awesome Free icons (FortAwesome/Font-Awesome, ``svgs/solid`` and ``svgs/regular``): about 2,300 one-colour icons
  with search terms. Brands are left out (logos are never used in lessons, CV-11). Credit: "Font Awesome Free by
  Fonticons, Inc., CC BY 4.0".

The index (``icons/index.json.gz``, schema ``bie.icons/1``) is searched by the director (``search("bank")`` → ids like
``tw:1f3e6`` or ``fa:solid/building-columns``); ``copy`` puts the chosen files into a render's assets and writes
``icons/credits.json`` for the credit roll. Files come from a local checkout (``BIE_TWEMOJI_SVG``, ``BIE_FONTAWESOME_SVGS``)
or, one by one, from the two GitHub repositories at the pinned tags below, through ``sources.cached`` (never into git).

    python -m bie.toolbox.icons search bank
    python -m bie.toolbox.icons copy tw:1f3ea fa:solid/warehouse --dest ASSETS_DIR
    python -m bie.toolbox.icons build --twemoji DIR --fontawesome DIR --out icons/index.json.gz
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import unicodedata
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_INDEX = HERE / "icons" / "index.json.gz"
SCHEMA = "bie.icons/1"
SETS = {
    "tw": {"id": "twemoji", "licence": "CC BY 4.0", "credit": "Twemoji graphics by Twitter, Inc and other contributors",
           "licence_url": "https://creativecommons.org/licenses/by/4.0/", "source_url": "https://github.com/jdecked/twemoji",
           "tag": "v16.0.1", "raw": "https://raw.githubusercontent.com/jdecked/twemoji/v16.0.1/assets/svg/{file}",
           "env": "BIE_TWEMOJI_SVG"},
    "fa": {"id": "fontawesome-free", "licence": "CC BY 4.0", "credit": "Font Awesome Free by Fonticons, Inc.",
           "licence_url": "https://creativecommons.org/licenses/by/4.0/", "source_url": "https://fontawesome.com",
           "tag": "7.3.1", "raw": "https://raw.githubusercontent.com/FortAwesome/Font-Awesome/7.3.1/svgs/{file}",
           "env": "BIE_FONTAWESOME_SVGS"},
}
ID = re.compile(r"^(tw:[0-9a-f-]{1,80}|fa:(solid|regular)/[a-z0-9-]{1,60})$")
# Twemoji flags of real countries are fine (a flag is not a logo); company and brand marks do not exist in Twemoji.
SKIN = re.compile(r"-1f3f[b-f]")          # skin-tone variants: keep the default yellow only, to keep the index small
CREDIT_FIELDS = ("credit", "licence", "licence_url", "source_url")


class IconError(ValueError):
    pass


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
    "wheat": ["tw:1f33e", "fa:solid/wheat-alt"], "grain": ["tw:1f33e", "fa:solid/wheat-alt"], "sheaf": ["tw:1f33e"], "rice": ["tw:1f33e"],
    "गेहूँ": ["tw:1f33e"], "गेहूं": ["tw:1f33e"], "अनाज": ["tw:1f33e"], "चावल": ["tw:1f35a"],
    "salt": ["tw:1f9c2"], "नमक": ["tw:1f9c2"], "cattle": ["tw:1f404"], "cow": ["tw:1f404"], "गाय": ["tw:1f404"], "मवेशी": ["tw:1f404"],
    "shell": ["tw:1f41a"], "shells": ["tw:1f41a"], "cowrie": ["tw:1f41a"], "कौड़ी": ["tw:1f41a"], "शंख": ["tw:1f41a"],
    "cloth": ["tw:1f9f5", "tw:1f455"], "fabric": ["tw:1f9f5"], "कपड़ा": ["tw:1f9f5", "tw:1f455"], "कपड़े": ["tw:1f9f5", "tw:1f455"],
    "tea": ["tw:1f375"], "चाय": ["tw:1f375"], "tobacco": ["fa:solid/smoking"], "तम्बाकू": ["fa:solid/smoking"], "तंबाकू": ["fa:solid/smoking"],
    "oil": ["tw:1f6e2"], "तेल": ["tw:1f6e2"], "sugar": ["tw:1f36c"], "चीनी": ["tw:1f36c"], "groceries": ["tw:1f6cd"], "राशन": ["tw:1f6cd"],
    # money
    "coin": ["tw:1fa99"], "coins": ["tw:1fa99", "fa:solid/coins"], "सिक्का": ["tw:1fa99"], "सिक्के": ["tw:1fa99", "fa:solid/coins"],
    "gold": ["tw:1fa99", "fa:solid/coins"], "सोना": ["tw:1fa99"], "silver": ["tw:1fa99"], "चाँदी": ["tw:1fa99"], "चांदी": ["tw:1fa99"],
    "note": ["fa:solid/money-bill-1", "tw:1f4b5"], "notes": ["fa:solid/money-bill-1", "tw:1f4b5"], "banknote": ["fa:solid/money-bill-1", "tw:1f4b5"],
    "currency": ["fa:solid/money-bill-1"], "नोट": ["fa:solid/money-bill-1", "tw:1f4b5"], "कागज़ी": ["fa:solid/money-bill-1"],
    "rupee": ["fa:solid/indian-rupee-sign"], "rupees": ["fa:solid/indian-rupee-sign"], "रुपया": ["fa:solid/indian-rupee-sign"], "रुपये": ["fa:solid/indian-rupee-sign"],
    "money": ["tw:1f4b0", "fa:solid/money-bill-1"], "पैसा": ["tw:1f4b0"], "पैसे": ["tw:1f4b0"], "cash": ["tw:1f4b5"], "नकद": ["tw:1f4b5"],
    "dollar": ["tw:1f4b5"], "euro": ["tw:1f4b6"], "yen": ["tw:1f4b4"], "pound": ["tw:1f4b7"], "yuan": ["tw:1f4b4"],
    "cheque": ["fa:solid/money-check"], "check book": ["fa:solid/money-check"], "चेक": ["fa:solid/money-check"],
    "card": ["tw:1f4b3"], "debit card": ["tw:1f4b3"], "credit card": ["tw:1f4b3"], "कार्ड": ["tw:1f4b3"],
    "phone": ["tw:1f4f1"], "mobile": ["tw:1f4f1"], "upi": ["tw:1f4f1", "fa:solid/qrcode"], "qr": ["fa:solid/qrcode"], "qr code": ["fa:solid/qrcode"],
    "मोबाइल": ["tw:1f4f1"], "फ़ोन": ["tw:1f4f1"], "फोन": ["tw:1f4f1"], "app": ["tw:1f4f1"],
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
        plural = r"(?:e?s)?" if re.fullmatch(r"[a-z ]+", key) else ""          # "cheques", "receipts", "deposits"
        m = re.search(r"(?<![a-z\u0900-\u097f])" + re.escape(key) + plural + r"(?![a-z\u0900-\u097f])", text)  # whole words: "warehouse" is not a house
        if m:
            hits.append((m.start(), -len(key), key))
    out = []
    for _, _, key in sorted(hits):
        out += [i for i in ALIASES[key] if i not in out]
    return out


def _words(query: str) -> list:
    return [w for w in re.findall(r"[a-z]+|[\u0900-\u097f]+", query.lower())]


def search(query: str, index: str | Path = DEFAULT_INDEX, limit: int = 12, *, religious: bool | None = None) -> list:
    """Icons for a thing named in words: the aliases first (Hindi words, synonyms, emoji names), then the icons whose name or
    search terms carry the query's words; colour icons rank a little above line icons. Religious symbols only when the query
    asks for them (``religious``: None reads the query, True keeps them, False drops them)."""
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
        s = sum(3 if re.search(rf"\b{w}\b", r["name"].lower()) else (1 if w in hay else 0) for w in latin)
        if s:
            scored.append((s + (0.5 if r["style"] == "colour" else 0), r))
    scored.sort(key=lambda t: -t[0])
    return (out + [r for _, r in scored])[:limit]


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
    folder = os.environ.get(SETS[prefix]["env"])
    return Path(folder) if folder and Path(folder).is_dir() else None


def icon_file(icon_id: str, *, index: str | Path = DEFAULT_INDEX, opener=None) -> Path:
    """The SVG of one icon: from the local checkout when its folder is set, else fetched once from the pinned tag on
    GitHub into the asset cache (outside git)."""
    row = by_id(index).get(icon_id)
    if row is None:
        raise IconError(f"{icon_id!r} is not in the icon index")
    prefix = icon_id[:2]
    local = _local_dir(prefix)
    if local is not None:
        path = local / row["file"]
        if not path.exists():
            raise IconError(f"{icon_id}: {path} is missing from {SETS[prefix]['env']}")
        return path
    from . import sources
    url = SETS[prefix]["raw"].format(file=row["file"])
    return sources.cached(url, f"icon-{SETS[prefix]['id']}-{SETS[prefix]['tag']}-{safe(icon_id)}.svg", opener=opener)


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
        dst = dest / "icons" / (safe(i) + ".svg")
        if i.startswith("fa:"):
            dst.write_text(_coloured(src.read_text(encoding="utf-8"), colour), encoding="utf-8")
        else:
            shutil.copy2(src, dst)
        credits[r["credit"]] = {k: r[k] for k in CREDIT_FIELDS}
        out[i] = "icons/" + safe(i) + ".svg"
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
        r, s = rows[i], SETS[i[:2]]
        data = icon_file(i, index=index, opener=opener).read_bytes()
        if i.startswith("fa:"):
            data = _coloured(data.decode("utf-8"), colour).encode("utf-8")
        asset = library.add_bytes(data, mime="image/svg+xml", source=s["id"], title=f"{r['name']} ({i})", page_url=s["source_url"],
                                  licence=s["licence"], licence_url=s["licence_url"], author=s["credit"].split(" by ", 1)[1],
                                  credit=s["credit"] + ", " + s["licence"], tags=["icon", s["id"]])
        out[i] = "assets/" + asset.path
    return out


def credit_assets(ids, index: str | Path = DEFAULT_INDEX) -> list:
    """The icons as asset records the licence gate reads (``licence.lesson_credits``), one per set used."""
    rows = by_id(index)
    seen, out = set(), []
    for i in ids:
        prefix = i[:2]
        if prefix in seen or i not in rows:
            continue
        seen.add(prefix)
        s = SETS[prefix]
        out.append({"asset_id": s["id"], "title": s["credit"].split(" by ", 1)[0], "author": s["credit"].split(" by ", 1)[1],
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


def build(twemoji: str | Path | None, fontawesome: str | Path | None, out: str | Path = DEFAULT_INDEX) -> dict:
    rows = []
    if twemoji:
        for f in sorted(os.listdir(twemoji)):
            if not f.endswith(".svg") or SKIN.search(f):
                continue
            stem = f[:-4]
            name = tw_name(stem)
            if not name:
                continue
            terms = sorted(set(re.findall(r"[a-z]+", name)))
            rows.append({"id": "tw:" + stem, "name": name, "terms": terms, "style": "colour", "file": f,
                         **{k: SETS["tw"][k] for k in CREDIT_FIELDS}})
    if fontawesome:
        meta = {}
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
                             "style": "line", "file": f"{style}/{f}", **{k: SETS["fa"][k] for k in CREDIT_FIELDS}})
    data = {"schema": SCHEMA, "count": len(rows), "icons": rows}
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if out.suffix == ".gz":
        with gzip.open(out, "wt", encoding="utf-8") as fh:
            fh.write(text)
    else:
        out.write_text(text, encoding="utf-8")
    load.cache_clear()
    return data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["build", "search", "copy"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--twemoji", default=os.environ.get("BIE_TWEMOJI_SVG", ""))
    ap.add_argument("--fontawesome", default=os.environ.get("BIE_FONTAWESOME_SVGS", ""))
    ap.add_argument("--index", default=str(DEFAULT_INDEX))
    ap.add_argument("--out", default=str(DEFAULT_INDEX))
    ap.add_argument("--dest", default="")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        data = build(a.twemoji, a.fontawesome, a.out)
        print("icons", data["count"], "->", a.out)
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
