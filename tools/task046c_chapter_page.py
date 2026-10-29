"""The chapter page for Navin: every teachable line of the book and the video that teaches it, by code (Task 046 Part C,
work B; Navin, 29 October 2026). No AI call, nothing written by hand.

    python -B tools/task046c_chapter_page.py --chapter-map <file or understanding run folder> --lesson <file or lesson run folder>
        --html <page.html> [--page v1=https://... --page v3=https://...] [--json <chapter coverage record>] [--note "..."]

The page carries the chapter's numbers (teachable lines, lines a passed video teaches, lines in failed videos, lines no video
is assigned to, which must be none and are red otherwise), one row per video (status, lines assigned and covered, beats,
its review page when ``--page`` names one) and one row per teachable line (page, item id, kind, the line, its video, that
video's status, whether a beat covers it). The record is written next to the page as ``<page>.coverage.json``.
"""
from __future__ import annotations

import argparse
import html
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_SPEC = importlib.util.spec_from_file_location("task046c_page", Path(__file__).with_name("task046c_page.py"))
_page = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_page)

STATUS_MARK = {"passed": "✅ passed", "failed": "❌ failed", "": "— not scripted"}
EXTRA_CSS = (".big { font-size: 34px; font-weight: 700; margin: 0 } tr.warn td { background: var(--warn-bg) } "
             ":root { --warn-bg: #fff4dc } @media (prefers-color-scheme: dark) { :root:not([data-theme=\"light\"]) { --warn-bg: #3a2f14 } } "
             ":root[data-theme=\"dark\"] { --warn-bg: #3a2f14 }")


def _status(status: str) -> str:
    return STATUS_MARK.get(status, status)


def build(chapter: dict, lesson: dict, *, pages: dict | None = None, note: str = "") -> tuple[str, dict]:
    from bie.brain import coverage
    e = html.escape
    pages = pages or {}
    record = coverage.chapter_coverage(chapter, lesson)
    course = chapter.get("course") or {}
    title = record["chapter"] or course.get("title") or "chapter"
    failed = sorted({v["video_id"] for r in record["rows"] for v in r["videos"] if v["status"] == "failed"}, key=_vkey)
    in_failed = sum(1 for r in record["rows"] if r["videos"] and all(v["status"] != "passed" for v in r["videos"]))
    parts = [_page.page_head(f"{title} · lines → videos", EXTRA_CSS), "<main>", '<span class="tag">Task 046 · Part C · kitaab ki har line → video (by code)</span>',
             f"<h1>{e(title)} · kitaab ki har line kis video mein padhaayi gayi</h1>",
             f'<p class="lead">{e(course.get("subject", ""))} · {e(course.get("learners", ""))}. '
             f'Lines: chapter map ki teachable items ({record["teachable"]}); video: lesson plan ki assignment (concept → video); '
             f'status: us video ki script ka status. {e(note)}</p>']
    unassigned = record["unassigned"]
    parts.append('<div class="grid">'
                 f'<div class="card"><h3>Teachable lines</h3><p class="big">{record["teachable"]}</p></div>'
                 f'<div class="card"><h3>Passed video padhaata hai</h3><p class="big ok">{record["taught_by_a_passed_video"]}</p></div>'
                 f'<div class="card"><h3>Failed videos mein</h3><p class="big{" bad" if in_failed else ""}">{in_failed}</p>'
                 f'<p class="muted">{e(", ".join(failed)) or "koi nahi"}</p></div>'
                 f'<div class="card"><h3>Kisi video ko nahi di gayi</h3><p class="big{" bad" if unassigned else " ok"}">{len(unassigned)}</p></div>'
                 '</div>')
    if unassigned:
        parts.append('<div class="bad-box"><b>Lines jo kisi video ko assign nahi hui (yeh 0 honi chahiye):</b><ul>'
                     + "".join(f"<li>page {u['page']} · {e(u['item_id'])} · {e(_page._clip(u['content']))}</li>" for u in unassigned) + "</ul></div>")
    parts.append("<h2>Videos</h2>")
    rows = []
    for v in record["videos"]:
        link = f'<a href="{e(pages[v["video_id"]])}" target="_blank" rel="noopener">review page</a>' if pages.get(v["video_id"]) else '<span class="muted">—</span>'
        unc = f'<span class="bad">{len(v["uncovered"])} nahi</span>' if v["uncovered"] else '<span class="ok">0</span>'
        rows.append(_page._rows([f"<b>{e(v['video_id'])}</b>", e(v["title"]), e(_status(v["status"])),
                                 f"{v['covered']} of {v['assigned']}" if v["assigned"] else e("prerequisites" if v["kind"] == "prerequisites" else "—"),
                                 unc, str(v["beats"]), link]))
    parts.append('<div class="scroll"><table>' + _page._rows(["video", "title", "status", "lines covered", "not covered", "beats", "page"], head=True)
                 + "".join(rows) + "</table></div>")
    parts.append(f"<h2>Har line ({record['teachable']})</h2>")
    rows = []
    for r in record["rows"]:
        if r["videos"]:
            cell = "<br>".join((f'<a href="{e(pages[v["video_id"]])}" target="_blank" rel="noopener"><b>{e(v["video_id"])}</b></a>' if pages.get(v["video_id"])
                                else f"<b>{e(v['video_id'])}</b>") + f" · {e(_status(v['status']))}" + ("" if v["covered"] else ' · <span class="bad">beat nahi</span>')
                               for v in r["videos"])
            cls = "" if any(v["status"] == "passed" and v["covered"] for v in r["videos"]) else "warn"
        else:
            cell, cls = '<span class="bad">koi video nahi ❌</span>', "bad"
        rows.append(f'<tr class="{cls}"><td>{r["page"]}</td><td class="mono">{e(r["item_id"])}<br><span class="muted">{e(r["kind"])}</span></td>'
                    f'<td title="{e(r["content"])}">{e(_page._clip(r["content"], 200))}</td><td>{cell}</td></tr>')
    parts.append('<div class="scroll"><table>' + _page._rows(["page", "line", "kitaab ki line", "video · status"], head=True) + "".join(rows) + "</table></div>")
    parts.append('<p class="muted">Yeh page <code>tools/task046c_chapter_page.py</code> ne chapter map aur lesson plan se banaya; '
                 'Claude ne koi line, video ya status haath se nahi likha.</p></main>')
    return "\n".join(parts), record


def _vkey(vid: str):
    try:
        return int(vid.lstrip("v"))
    except ValueError:
        return 999


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--chapter-map", required=True, type=Path, help="chapter_map.json, or the understanding run folder")
    parser.add_argument("--lesson", required=True, type=Path, help="lesson_plan.json, or the lesson run folder")
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--json", type=Path, help="where the chapter coverage record goes (default: <page>.coverage.json)")
    parser.add_argument("--page", action="append", default=[], metavar="VIDEO=URL", help="a video's review page")
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)
    chapter = _page.load_run_json(args.chapter_map, "chapter_map.json")
    lesson = _page.load_run_json(args.lesson, "lesson_plan.json")
    if not chapter or not lesson:
        parser.error("the chapter map and the lesson plan are both needed")
    pages = dict(p.split("=", 1) for p in args.page)
    page, record = build(chapter, lesson, pages=pages, note=args.note)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(page, encoding="utf-8")
    from bie.brain import formats
    formats.check("chapter_review_record", record, where="chapter coverage record")
    out = args.json or args.html.with_suffix(".coverage.json")
    out.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{args.html}: {len(page.encode('utf-8')) / 1e6:.2f} MB; {record['teachable']} teachable lines, "
          f"{record['taught_by_a_passed_video']} taught by a passed video, {len(record['unassigned'])} unassigned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
