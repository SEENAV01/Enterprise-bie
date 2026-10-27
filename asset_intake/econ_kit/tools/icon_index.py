"""Build BIE's searchable icon index from two CC BY 4.0 icon sets, and copy chosen icons into a render's assets.

Sources (both "CC BY 4.0": allowed by bie/toolbox/licence_policy.json class ``cc-by``, credit required):
- Twemoji graphics (jdecked/twemoji, ``assets/svg``): about 4,000 flat colour icons. Credit: "Twemoji graphics by
  Twitter, Inc and other contributors, CC BY 4.0".
- Font Awesome Free icons (``@fortawesome/fontawesome-free/svgs``, solid/regular/brands): about 2,000 one-colour icons with
  search terms. Brands are left out (logos are never used in lessons). Credit: "Font Awesome Free by Fonticons, Inc.,
  CC BY 4.0".

    python icon_index.py build --twemoji DIR --fontawesome DIR --out icons/index.json
    python icon_index.py search "bank" [--index icons/index.json]
    python icon_index.py copy ID [ID ...] --dest ASSETS_DIR [--twemoji DIR --fontawesome DIR]

Each entry: id ("tw:1f3e6", "fa:solid/building-columns"), name, terms, style ("colour" | "line"), file (relative to its
source folder), licence, credit, source_url. The copy command writes ``icons/<safe id>.svg`` and a ``credits.json``
that the lesson's credit roll reads.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
DEFAULT_INDEX = os.path.join(KIT, "icons", "index.json")
CREDITS = {
    "tw": {"licence": "CC BY 4.0", "credit": "Twemoji graphics by Twitter, Inc and other contributors",
           "licence_url": "https://creativecommons.org/licenses/by/4.0/", "source_url": "https://github.com/jdecked/twemoji"},
    "fa": {"licence": "CC BY 4.0", "credit": "Font Awesome Free by Fonticons, Inc.",
           "licence_url": "https://creativecommons.org/licenses/by/4.0/", "source_url": "https://fontawesome.com"},
}
# Twemoji flags of real countries are fine (a flag is not a logo); company and brand marks do not exist in Twemoji.
SKIN = re.compile(r"-1f3f[b-f]")          # skin-tone variants: keep the default yellow only, to keep the index small


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


def build(twemoji: str, fontawesome: str, out: str):
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
            rows.append({"id": "tw:" + stem, "name": name, "terms": terms, "style": "colour", "file": f, **CREDITS["tw"]})
    if fontawesome:
        meta = {}
        yml = os.path.join(os.path.dirname(fontawesome.rstrip("/")), "metadata", "icons.yml")
        if os.path.exists(yml):
            import yaml
            meta = yaml.safe_load(open(yml, encoding="utf-8")) or {}
        for style in ("solid", "regular"):
            d = os.path.join(fontawesome, style)
            if not os.path.isdir(d):
                continue
            for f in sorted(os.listdir(d)):
                if not f.endswith(".svg"):
                    continue
                stem = f[:-4]
                m = meta.get(stem, {})
                terms = sorted(set([stem.replace("-", " ")] + [str(t) for t in (m.get("search", {}) or {}).get("terms", []) or []]))
                rows.append({"id": f"fa:{style}/{stem}", "name": m.get("label", stem.replace("-", " ")), "terms": terms,
                             "style": "line", "file": f"{style}/{f}", **CREDITS["fa"]})
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"schema": "bie.icons/1", "count": len(rows), "icons": rows}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print("icons", len(rows), "->", out)


def search(query: str, index: str, limit: int = 12):
    data = json.load(open(index, encoding="utf-8"))["icons"]
    q = [w for w in re.findall(r"[a-z]+", query.lower())]
    scored = []
    for r in data:
        hay = (r["name"] + " " + " ".join(r["terms"])).lower()
        s = sum(3 if re.search(rf"\b{w}\b", r["name"].lower()) else (1 if w in hay else 0) for w in q)
        if s:
            scored.append((s + (0.5 if r["style"] == "colour" else 0), r))
    scored.sort(key=lambda t: -t[0])
    return [r for _, r in scored[:limit]]


def safe(icon_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", icon_id.lower()).strip("-")


def copy(ids, dest: str, twemoji: str, fontawesome: str, index: str, colour: str = "#2b3a4a"):
    data = {r["id"]: r for r in json.load(open(index, encoding="utf-8"))["icons"]}
    os.makedirs(os.path.join(dest, "icons"), exist_ok=True)
    credits = {}
    for i in ids:
        r = data[i]
        src = os.path.join(twemoji if i.startswith("tw:") else fontawesome, r["file"])
        dst = os.path.join(dest, "icons", safe(i) + ".svg")
        if i.startswith("fa:"):
            svg = open(src, encoding="utf-8").read()
            svg = svg.replace('fill="currentColor"', f'fill="{colour}"') if 'fill="currentColor"' in svg else \
                svg.replace("<path ", f'<path fill="{colour}" ')
            open(dst, "w", encoding="utf-8").write(svg)
        else:
            shutil.copy2(src, dst)
        credits[r["credit"]] = {k: r[k] for k in ("credit", "licence", "licence_url", "source_url")}
    json.dump(sorted(credits.values(), key=lambda c: c["credit"]), open(os.path.join(dest, "icons", "credits.json"), "w"),
              indent=1)
    return {i: "icons/" + safe(i) + ".svg" for i in ids}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "search", "copy"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--twemoji", default=os.environ.get("BIE_TWEMOJI_SVG", ""))
    ap.add_argument("--fontawesome", default=os.environ.get("BIE_FONTAWESOME_SVGS", ""))
    ap.add_argument("--index", default=DEFAULT_INDEX)
    ap.add_argument("--out", default=DEFAULT_INDEX)
    ap.add_argument("--dest", default="")
    a = ap.parse_args()
    if a.cmd == "build":
        build(a.twemoji, a.fontawesome, a.out)
    elif a.cmd == "search":
        for r in search(" ".join(a.args), a.index):
            print(r["id"], "|", r["name"], "|", r["style"])
    else:
        print(json.dumps(copy(a.args, a.dest, a.twemoji, a.fontawesome, a.index), indent=1))
