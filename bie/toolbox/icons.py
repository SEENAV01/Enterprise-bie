"""BIE's icon index: the icon sets the build-up canvas draws with (Task 046 Part C, 27 October 2026; Part D2, 1 November 2026).

- Twemoji graphics (jdecked/twemoji, ``assets/svg``): about 1,900 flat colour icons (skin-tone variants left out).
  Credit: "Twemoji graphics by Twitter, Inc and other contributors, CC BY 4.0".
- Font Awesome Free icons (FortAwesome/Font-Awesome, ``svgs/solid`` and ``svgs/regular``): about 2,300 one-colour icons
  with search terms. Brands are left out (logos are never used in lessons, CV-11). Credit: "Font Awesome Free by
  Fonticons, Inc., CC BY 4.0".
- Fluent Emoji (microsoft/fluentui-emoji, MIT, pinned commit below; Navin, 1 November 2026: "add Microsoft Fluent Emoji ... as
  an icon source with its 3D style, preferred for objects"): about 1,600 3D PNGs (``fl:<name>``, skin-tone variants left out,
  the default one kept). Credit: "Fluent Emoji by Microsoft, MIT". The licence policy allows MIT for this source only.
- BIE's own money drawings (the ``bie:`` set of Part D2) are retired (Navin's addendum of 2 November 2026: "jis cheej ka
  jikar hai wohi cheej dikhe"; nothing hand-made for one chapter). A thing no icon is a picture of (``fits``) is a need: the
  general path finds it in the shared library, fetches it, or BIE's coder draws it (``bie/brain/coder.py``) into the library.

The index (``icons/index.json.gz``, schema ``bie.icons/1``) is searched by the director (``search("bank")`` → ids like
``tw:1f3e6`` or ``fa:solid/building-columns``); ``copy`` puts the chosen files into a render's assets and writes
``icons/credits.json`` for the credit roll. Files come from a local checkout (``BIE_TWEMOJI_SVG``, ``BIE_FONTAWESOME_SVGS``,
``BIE_FLUENT_EMOJI``) or, one by one, from the GitHub repositories at the pinned tags below, through ``sources.cached`` (never
into git).

    python -m bie.toolbox.icons search bank
    python -m bie.toolbox.icons copy tw:1f3ea fa:solid/warehouse --dest ASSETS_DIR
    python -m bie.toolbox.icons build --twemoji DIR --fontawesome DIR [--fluent DIR] --out icons/index.json.gz
    python -m bie.toolbox.icons add-sets [--fluent DIR]     (re-make the fl rows; the tw and fa rows stay as they are)
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
}
# An id of the retired bie: set still parses (earlier plans name them), so ``check_ids`` names it as not in the index.
ID = re.compile(r"^(tw:[0-9a-f-]{1,80}|fa:(solid|regular)/[a-z0-9-]{1,60}|fl:[a-z0-9-]{1,80}|bie:[a-z0-9-]{1,40})$")
# Ranking among the icons a query's words find (aliases come first anyway): Fluent's 3D icons (Navin, 1 November 2026:
# "preferred for objects"), then colour icons, then line icons.
STYLE_BONUS = {"fl": 0.75}
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


# What a thing is called in words → the index's own ids: vocabulary data (``icons/aliases.json``, ``bie.icon-aliases/1``), not
# a list of things to draw (Navin's addendum of 2 November 2026: nothing hand-made for one chapter).
ALIASES_FILE = HERE / "icons" / "aliases.json"
ALIASES = {k: list(v) for k, v in json.loads(ALIASES_FILE.read_text(encoding="utf-8"))["aliases"].items()}

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


FIT_STOP = frozenset("the a an and its their or".split())
FIT_PREPS = frozenset("of in with on for at from by to into under over".split())


def _stem(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def _head(words: list):
    """The thing a phrase names (its head noun): the word before the first preposition ("sack of salt", "shells in a palm"), else
    the last word ("debt ledger", "नमक की बोरी"). Numbers and signs are text, not the thing."""
    words = [w for w in words if not re.search(r"\d", w) and w not in FIT_STOP]
    for i, w in enumerate(words):
        if w in FIT_PREPS and i > 0:
            return words[i - 1]
    words = [w for w in words if w not in FIT_PREPS and w not in ("का", "की", "के")]
    return words[-1] if words else None


def _alias_hits(words: list) -> list:
    """(key, ids) of the aliases a query's words name, whole words."""
    text = " ".join(words)
    out = []
    for key, ids in ALIASES.items():
        plural = r"(?:e?s)?" if re.fullmatch(r"[₹a-z0-9 ]*[a-z]", key) else ""
        if re.search(r"(?<![a-z0-9\u0900-\u097f])" + re.escape(key) + plural + r"(?![a-z0-9\u0900-\u097f])", text):
            out.append((key, ids))
    return out


def _has_word(word: str, hay: str) -> bool:
    return re.search(rf"\b{re.escape(_stem(word))}(?:e?s)?\b", hay) is not None


def fits(query: str, row: dict) -> bool:
    """An icon is a picture OF the thing, not of a near word (Navin's addendum of 2 November 2026: "jis cheej ka jikar hai wohi
    cheej dikhe"; the Money run c: "payment claim" found a baggage claim, "net banking screen" a mosquito net, "cheque" a
    chequered flag):

    - an alias that names the phrase's head noun names it ("debt ledger" → the ledger; "sack of salt" is a sack, not the salt
      shaker the alias "salt" names);
    - when an alias names the head noun, the alias decides (it tells the money note from the musical note); otherwise every
      content word of the phrase is a whole word of the icon's name or search terms."""
    q = _words(query)
    head = _head(q)
    if head is None:
        return False
    named = [ids for key, ids in _alias_hits(q) if _stem(head) in {_stem(k) for k in key.split()}]
    if named:
        return row.get("id") in {i for ids in named for i in ids}
    words = [w for w in q if re.fullmatch(r"[a-z]+", w) and w not in FIT_STOP and w not in FIT_PREPS and len(w) > 1]
    if not words:
        return False
    hay = (row.get("name", "") + " " + " ".join(row.get("terms") or [])).lower()
    return all(_has_word(w, hay) for w in words)


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
    """The file of one icon: from the local checkout when its folder is set, else fetched once from the pinned tag or commit on
    GitHub into the asset cache (outside git)."""
    row = by_id(index).get(icon_id)
    if row is None:
        raise IconError(f"{icon_id!r} is not in the icon index")
    prefix = set_of(icon_id)
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
    """The whole index from local checkouts (Twemoji's ``assets/svg``, Font Awesome's ``svgs``, the Fluent Emoji clone)."""
    rows = (twemoji_rows(twemoji) if twemoji else []) + (fontawesome_rows(fontawesome) if fontawesome else [])
    rows += fluent_rows(fluent) if fluent else []
    return write_index(rows, out)


def add_sets(index: str | Path = DEFAULT_INDEX, out: str | Path | None = None, *, fluent: str | Path | None = None) -> dict:
    """Re-make the Fluent rows (from the clone, when given; else they stay) in an existing index; the Twemoji and Font Awesome
    rows stay exactly as they are (and the retired bie: rows are left out)."""
    old = load(index)["icons"]
    keep = [r for r in old if set_of(r["id"]) in ("tw", "fa")]
    fl = fluent_rows(fluent) if fluent else [r for r in old if set_of(r["id"]) == "fl"]
    return write_index(keep + fl, out or index)


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
