"""One course folder from the studio's runs (Navin, 18 November 2026): films, game and Living Book side by side.

    python -B tools/studio_course.py --films <films run folder> --games <games run folder> --book <book run folder> --out <folder>

Copies ``films/<qid>.html``, ``GAME.html`` and ``BOOK.html`` into one folder and writes ``index.html``, the course home:
the chapter's big question, its pillars and, per student question, Film → Game → Notes (Navin's order: films first,
then the games, then the notes). Pages that a run did not make are simply not linked. Code only, no maker call.
"""
from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import studio  # noqa: E402

PAGE = """<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
:root{{--paper:#eef0e4;--card:#f8f7f0;--ink:#1d2f27;--mute:#56685f;--line:#d6dacb;--tint:{tint}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",sans-serif}}
.wrap{{max-width:980px;margin:0 auto;padding:12px 16px 50px}}.top{{font-size:.75rem;letter-spacing:.16em;font-weight:700;color:var(--tint);padding:8px 0;border-bottom:2px solid var(--tint)}}
h1{{font-family:Georgia,serif;font-weight:400;font-size:clamp(2rem,6vw,3rem);margin:22px 0 6px}}.big{{color:var(--mute);font-size:1.1rem;margin:0 0 18px}}
.go{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}}.go a{{text-decoration:none;border-radius:99px;padding:9px 16px;font-weight:600;border:1px solid var(--tint);color:var(--tint)}}
.go a:first-child{{background:var(--tint);color:#fff}}
.pl{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:10px 0}}.pl h2{{margin:0;font-size:1.05rem;color:var(--tint)}}.pl p{{margin:2px 0 8px;color:var(--mute);font-size:.9rem}}
.q{{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;border-top:1px solid var(--line);padding:9px 0}}.q span{{flex:1 1 260px}}.q b{{color:#a07a26;font-size:.78rem;margin-right:6px}}
.q a{{font-size:.85rem;text-decoration:none;border:1px solid var(--line);border-radius:8px;padding:5px 10px;background:#fff;color:var(--ink)}}
</style></head><body><div class="wrap"><div class="top">BIE · COURSE</div><h1>{title}</h1><p class="big">{big}</p>
<div class="go">{go}</div>{pillars}</div></body></html>"""


def build(plan: dict, *, films: set, game: bool, book: bool, tint: str) -> str:
    esc = html.escape
    go = []
    first = next((q["id"] for q in plan.get("questions") or [] if q.get("id") in films), None)
    if first:
        go.append(f'<a href="films/{first}.html">▶ Pehli film</a>')
    if game:
        go.append('<a href="GAME.html">Chapter ka game</a>')
    if book:
        go.append('<a href="BOOK.html">Living Book (notes)</a>')
    blocks = []
    for pillar in plan.get("pillars") or []:
        rows = []
        for q in plan.get("questions") or []:
            if q.get("pillar") != pillar.get("id"):
                continue
            qid = esc(q.get("id", ""))
            links = ([f'<a href="films/{qid}.html">Film</a>'] if q.get("id") in films else []) \
                + ([f'<a href="GAME.html#{qid}">Game</a>'] if game else []) + ([f'<a href="BOOK.html#{qid}">Notes</a>'] if book else [])
            rows.append(f'<div class="q"><span><b>{qid.upper()}</b>{esc(q.get("question", ""))}</span>{"".join(links)}</div>')
        blocks.append(f'<div class="pl"><h2>{esc(pillar.get("title", ""))}</h2><p>{esc(pillar.get("line", ""))}</p>{"".join(rows)}</div>')
    return PAGE.format(title=esc(plan.get("chapter_title", "Course")), big=esc(plan.get("big_question", "")),
                       tint=esc(tint), go="".join(go), pillars="".join(blocks))


def assemble(*, films: Path = None, games: Path = None, book: Path = None, out: Path, course: str = "") -> dict:
    out.mkdir(parents=True, exist_ok=True)
    plan = None
    for run in (films, games, book):
        if run and (run / "questions.json").exists():
            plan = json.loads((run / "questions.json").read_text(encoding="utf-8"))
            break
    if plan is None:
        raise SystemExit("no questions.json in the runs")
    made = set()
    if films and (films / "films").is_dir():
        (out / "films").mkdir(exist_ok=True)
        for page in sorted((films / "films").glob("q*.html")):
            shutil.copyfile(page, out / "films" / page.name)
            made.add(page.stem)
    game = bool(games and (games / "GAME.html").exists())
    if game:
        shutil.copyfile(games / "GAME.html", out / "GAME.html")
    has_book = bool(book and (book / "BOOK.html").exists())
    if has_book:
        shutil.copyfile(book / "BOOK.html", out / "BOOK.html")
    (out / "questions.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "index.html").write_text(build(plan, films=made, game=game, book=has_book, tint=studio.subject_tint(course)),
                                    encoding="utf-8")
    return {"films": sorted(made), "game": game, "book": has_book, "questions": len(plan.get("questions") or [])}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("films", "games", "book"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--course", default="")
    args = parser.parse_args(argv)
    print(json.dumps(assemble(films=args.films, games=args.games, book=args.book, out=args.out, course=args.course)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
