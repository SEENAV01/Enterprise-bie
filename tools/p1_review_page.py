"""The chapter review page (Phase 1, part E): one page where Navin watches, reads and plays what BIE made.

    python -B tools/p1_review_page.py --run <folder> [--out REVIEW.html] [--title <chapter>]

The folder is one chapter's run: ``showplan.json`` with ``plans/`` and ``video_specs/`` (the director's work),
``notes/`` (the pages and deck), ``game/`` (the levels and game), and — when the render workflow has run —
``videos/<video>.mp4`` with ``stills/<video>.png`` posters and per-video ``audit.json`` text checks. The page links
what exists, says plainly what does not exist yet, and shows the honest numbers (passed, first-try, rounds, scenes,
seconds, texts under the floor, texts covering each other).
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PAGE = """<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · BIE review</title>
<style>
:root{{--bg:#f7f6f2;--card:#fff;--ink:#1d2433;--muted:#5d6676;--line:#dfe2e8;--accent:#0f6e68;--warn:#b4532a}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 "Noto Sans","Noto Sans Devanagari",system-ui,sans-serif}}
main{{max-width:900px;margin:auto;padding:16px}}
h1{{font-size:1.4rem;margin:8px 0 2px}} .sub{{color:var(--muted);margin:0 0 14px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin:0 0 14px}}
h2{{font-size:1.05rem;margin:0 0 10px}}
.vid{{display:flex;gap:12px;align-items:center;border-top:1px solid var(--line);padding:10px 0}}
.vid:first-of-type{{border-top:0}}
.vid img{{width:168px;border-radius:8px;border:1px solid var(--line)}}
.vid .meta{{flex:1;min-width:0}} .vid .meta b{{display:block}}
.pill{{display:inline-block;font-size:.8rem;border-radius:999px;padding:2px 10px;background:#e8f3f1;color:var(--accent);margin:2px 4px 0 0}}
.pill.warn{{background:#fdeee4;color:var(--warn)}}
a.btn{{display:inline-block;background:var(--accent);color:#fff;border-radius:10px;padding:8px 14px;text-decoration:none;font-weight:700;margin:4px 8px 0 0}}
a.btn.ghost{{background:transparent;color:var(--accent);border:1px solid var(--accent)}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}} td,th{{border:1px solid var(--line);padding:6px 8px;text-align:left}}
.missing{{color:var(--muted)}}
footer{{color:var(--muted);font-size:.8rem;padding:8px 0 24px}}
</style>
</head>
<body><main>
<h1>{title}</h1>
<p class="sub">BIE ka banaya hua: videos, notes aur game — ek jagah. {made}</p>
{videos}
{notes}
{game}
{numbers}
<footer>BIE review page · har number asli run se, kuch bhi haath se nahi.</footer>
</main></body></html>
"""


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def esc(text) -> str:
    return html.escape(str(text))


def videos_section(run: Path, showplan: dict | None) -> str:
    rows = []
    for row in (showplan or {}).get("videos") or []:
        vid = row["video_id"]
        mp4 = run / "videos" / f"{vid}.mp4"
        poster = run / "stills" / f"{vid}.png"
        audit = read_json(run / "videos" / f"{vid}.audit.json") or read_json(run / "audit" / f"{vid}.json")
        meta = [f"<span class='pill'>{row.get('scenes', '?')} scenes</span>",
                f"<span class='pill'>{row.get('els', '?')} cheezein</span>"]
        if row.get("seconds"):
            meta.append(f"<span class='pill'>{row['seconds'] / 60:.1f} min</span>")
        meta.append(f"<span class='pill'>{row.get('rounds', '?')} round</span>")
        if audit:
            small, overlap = len(audit.get("small") or []), len(audit.get("overlaps") or [])
            meta.append(f"<span class='pill{' warn' if small else ''}'>chhote text: {small}</span>")
            meta.append(f"<span class='pill{' warn' if overlap else ''}'>dhake text: {overlap}</span>")
        link = (f"<a class='btn' href='videos/{vid}.mp4'>Dekho</a>" if mp4.exists()
                else "<span class='missing'>video abhi render nahi hua</span>")
        img = f"<img src='stills/{vid}.png' alt=''>" if poster.exists() else ""
        status = row.get("status", "?")
        rows.append(f"<div class='vid'>{img}<div class='meta'><b>{esc(vid)} · {esc(status)}</b>"
                    f"{''.join(meta)}<div>{link}</div></div></div>")
    if not rows:
        return "<section><h2>Videos</h2><p class='missing'>Koi scene plan nahi bana.</p></section>"
    return "<section><h2>Videos</h2>" + "".join(rows) + "</section>"


def link_section(title: str, path: Path, href: str, what: str, extra: str = "") -> str:
    body = (f"<a class='btn' href='{href}'>{esc(what)}</a>{extra}" if path.exists()
            else f"<p class='missing'>abhi nahi bana.</p>")
    return f"<section><h2>{esc(title)}</h2>{body}</section>"


def numbers_section(showplan: dict | None, pages: dict | None, levels: dict | None, render: dict | None) -> str:
    rows = []
    if showplan:
        total = len(showplan.get("videos") or [])
        rows.append(("Scene plans", f"{showplan.get('passed', 0)}/{total} pass, {showplan.get('first_try', 0)} pehli baar mein"))
        rounds = [r.get("rounds", 0) for r in showplan.get("videos") or []]
        if rounds:
            rows.append(("Rounds", f"kul {sum(rounds)}, sabse zyada {max(rounds)}"))
    if pages:
        rows.append(("Notes panne", f"{pages.get('pages', 0)} ({pages.get('pictures', 0)} tasveer wale), {pages.get('rounds', 0)} round"))
    if levels:
        rows.append(("Game levels", f"{levels.get('levels', 0)} ({', '.join(levels.get('mechanics') or [])}), {levels.get('rounds', 0)} round"))
    if render:
        cost = (render.get("cost") or {})
        if cost.get("list_price_inr") is not None:
            rows.append(("Render", f"₹{cost['list_price_inr']} list price, {cost.get('minutes', '?')} min video"))
    if not rows:
        return ""
    table = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in rows)
    return f"<section><h2>Numbers (asli run se)</h2><table>{table}</table></section>"


def build(run: Path, title: str) -> str:
    showplan = read_json(run / "showplan.json")
    pages = read_json(run / "notes" / "pages_summary.json")
    levels = read_json(run / "game" / "levels_summary.json")
    render = read_json(run / "summary.json")
    made = []
    if showplan:
        made.append(f"{showplan.get('passed', 0)} video plan")
    if pages:
        made.append(f"{pages.get('pages', 0)} notes panne")
    if levels:
        made.append(f"{levels.get('levels', 0)} game level")
    return PAGE.format(title=esc(title), made=esc(", ".join(made) + "." if made else ""),
                       videos=videos_section(run, showplan),
                       notes=link_section("Notes", run / "notes" / "NOTES_PAGES.html", "notes/NOTES_PAGES.html",
                                          "Notes kholo"),
                       game=link_section("Game", run / "game" / "GAME.html", "game/GAME.html", "Khelo"),
                       numbers=numbers_section(showplan, pages, levels, render))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--title", default="")
    a = ap.parse_args(argv)
    title = a.title or a.run.name
    out = a.out or (a.run / "REVIEW.html")
    out.write_text(build(a.run, title), encoding="utf-8")
    print(f"review page: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
