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


def search(query: str, index: str | Path = DEFAULT_INDEX, limit: int = 12) -> list:
    """Icons whose name or search terms carry the query's words; colour icons rank a little above line icons."""
    data = load(index)["icons"]
    q = [w for w in re.findall(r"[a-z]+", query.lower())]
    scored = []
    for r in data:
        hay = (r["name"] + " " + " ".join(r["terms"])).lower()
        s = sum(3 if re.search(rf"\b{w}\b", r["name"].lower()) else (1 if w in hay else 0) for w in q)
        if s:
            scored.append((s + (0.5 if r["style"] == "colour" else 0), r))
    scored.sort(key=lambda t: -t[0])
    return [r for _, r in scored[:limit]]


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
