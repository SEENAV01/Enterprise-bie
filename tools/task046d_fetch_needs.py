"""The fetch step of the needs list (Task 046 Part D1; Navin, 30 October 2026: "bie ne jo duniya bnayi hai uske bahar sochke wo
cheejen ikathi hi nhi kar rha"). It runs in GitHub Actions only (``.github/workflows/task046d-fetch-needs.yml``), never on the
VM and never in the cloud workspace.

    python -B tools/task046d_fetch_needs.py --needs <needs.json, a file or an https URL> --library <BIE's shared library folder>
        [--per-need 1] [--sources met,openverse,commons] [--report fetched.json]

For every need of kind ``image`` or ``icon`` in ``needs.json`` (``bie.brain.needs/1``, written by the canvas section) it looks
in the shared library first, then in open sources whose licence BIE's policy allows for lessons: The Met Open Access (public
domain objects, CC0), Openverse (asked for CC0, CC BY and the Public Domain Mark only), Wikimedia Commons (each file's own
licence; share-alike and non-commercial are refused by the policy). Every image passes the licence gate
(``bie/toolbox/licence.py``) and is added to the library with its credit fields and the need's words as tags, so the next
canvas run (``tools/run_brain.py --library``) finds it first. Nothing needs a key; a source that needs one is Navin's to add.

Never fetched: a portrait or likeness of a person (card rule 8; historical figures are Navin's decision), a need of kind
``world kit``, ``block`` or ``3d`` (those go to Part D2's builders). The report (``fetched.json``) says, per need, what was
found, from where, under which licence, and what was not.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import assets, formats  # noqa: E402
from bie.brain.visual_thinking import PORTRAIT  # noqa: E402

SCHEMA = "bie.brain.fetched/1"
SOURCES = {"met": assets.search_met, "openverse": assets.search_openverse, "commons": assets.search_commons}
STOP = {"the", "a", "an", "of", "and", "with", "for", "on", "in", "to", "its", "from"}


def words_of(thing: str) -> list:
    return [w for w in re.findall(r"[a-z0-9]+|[ऀ-ॿ]+", thing.lower()) if w not in STOP and len(w) > 1]


def load_needs(source: str, opener=None) -> dict:
    if source.startswith("https://"):
        with (opener or urllib.request.urlopen)(urllib.request.Request(source, headers={"user-agent": "bie-fetch/1"}), timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
    else:
        data = json.loads(Path(source).read_text(encoding="utf-8"))
    formats.check("needs", data, where=source)
    return data


def fetch(needs: dict, library: assets.AssetLibrary, *, sources=("met", "openverse", "commons"), per_need: int = 1, opener=None,
          run: str = "") -> dict:
    """The report of one fetch: per need its status (in_library, fetched, not_found, skipped) and the assets added."""
    rows, seen = [], set()
    for need in needs.get("needs") or []:
        thing = str(need.get("thing") or "").strip()
        key = thing.lower()
        if not thing or key in seen:
            continue
        seen.add(key)
        row = {"thing": thing, "kind": need.get("kind"), "beats": need.get("beats") or [], "assets": [], "tried": []}
        if need.get("kind") not in ("image", "icon"):
            rows.append(dict(row, status="skipped", why=f"a {need.get('kind')} is built by Part D2, not fetched"))
            continue
        if PORTRAIT.search(thing):
            rows.append(dict(row, status="skipped", why="a portrait or likeness of a person: card rule 8 (Navin decides historical figures)"))
            continue
        words = words_of(thing)
        have = [a for a in library.find(words) if len(set(words) & {t.lower() for t in a.tags}) >= min(2, len(words))]
        if have:
            rows.append(dict(row, status="in_library", assets=[a.asset_id for a in have[:per_need]]))
            continue
        for name in sources:
            row["tried"].append(name)
            try:
                candidates = SOURCES[name](" ".join(words) or thing, limit=6, opener=opener)
            except (assets.AssetError, OSError, ValueError) as exc:
                row.setdefault("errors", []).append(f"{name}: {type(exc).__name__}: {str(exc)[:160]}")
                continue
            for cand in candidates:
                if PORTRAIT.search(cand.title or ""):
                    continue
                try:
                    asset = library.add_candidate(cand, tags=words + ["fetched", name, "d1-need"],
                                                  description=f"for '{thing}' (needs.json{' of ' + run if run else ''})", opener=opener)
                except (assets.AssetError, OSError, ValueError) as exc:
                    row.setdefault("errors", []).append(f"{name}: {cand.title[:60]}: {str(exc)[:120]}")
                    continue
                row["assets"].append({"asset_id": asset.asset_id, "source": asset.source, "title": asset.title, "licence": asset.licence,
                                      "credit": asset.credit, "page_url": asset.page_url})
                if len(row["assets"]) >= per_need:
                    break
            if len(row["assets"]) >= per_need:
                break
        rows.append(dict(row, status="fetched" if row["assets"] else "not_found"))
    library.save()
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in ("fetched", "in_library", "not_found", "skipped")}
    return {"schema": SCHEMA, "run": run, "needs": rows, "counts": counts, "library_assets": len(library.assets),
            "missing_capabilities": needs.get("missing_capabilities") or []}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--needs", required=True)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--per-need", type=int, default=1)
    parser.add_argument("--sources", default="met,openverse,commons")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in sources if s not in SOURCES]
    if unknown:
        parser.error(f"unknown sources: {', '.join(unknown)} (known: {', '.join(SOURCES)})")
    needs = load_needs(args.needs)
    run = args.needs.rsplit("/runs/", 1)[-1].split("/")[0] if "/runs/" in args.needs else ""
    report = fetch(needs, assets.AssetLibrary(args.library), sources=sources, per_need=max(1, min(3, args.per_need)), run=run)
    out = args.report or args.library / "fetched.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report["counts"]), "library:", report["library_assets"], "assets ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
