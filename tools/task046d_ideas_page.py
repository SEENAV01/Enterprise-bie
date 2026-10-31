"""The dikhane ki list for Navin, BEFORE the render (Task 046 Part D1; Navin, 30 October 2026): for every beat of a video, what
the learner will see, on which word, and whether code (the book's own picture) or the maker decided it. No AI call, nothing
written by hand: everything comes from the canvas run's ``visual_ideas/<video>.json`` (``bie.brain.visual-ideas/1``),
``canvas.json``, ``needs.json`` and the lesson plan's narration.

    python -B tools/task046d_ideas_page.py --canvas <canvas run folder> --video v4 --html <page.html>
        [--lesson <lesson run folder>] [--before-canvas <earlier canvas run folder>] [--note "..."]

With ``--before-canvas`` the page opens with the measures before and after (the share of parts in the two world kits,
distinct icons, text-only screen time, the book's pictures drawn), read from the two runs' plans by code.
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

from bie.brain import formats  # noqa: E402

BY = {"book": "kitaab ki apni picture (code ne rakhi)", "card": "card type se (maker ne banaayi)", "maker": "maker ne chuni"}
EXTRA_CSS = (".rel { font-weight: 700; color: var(--accent) } .shows { font-weight: 600 } .book { background: var(--ok-bg) } "
             ".big { font-size: 30px; font-weight: 700; margin: 0 } :root { --ok-bg: #e9f6ec } "
             "@media (prefers-color-scheme: dark) { :root:not([data-theme=\"light\"]) { --ok-bg: #16301e } } "
             ":root[data-theme=\"dark\"] { --ok-bg: #16301e }")


def plan_measures(canvas_dir: Path, video_id: str) -> dict:
    """Measures read from a canvas run's plans for one video (works on runs made before Part D1 too): parts, world parts and
    their kits, distinct icons, canvas parts with no non-text element, book pictures drawn."""
    plans = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((canvas_dir / "plans").glob(f"{video_id}_*.plan.json"))]
    kits, icon_ids, text_only, pictures = [], set(), 0, set()
    for plan in plans:
        if "elements" in plan:
            kits.append(plan.get("kit") or "world")
            continue
        non_text = 0
        for n in plan.get("nodes") or []:
            if n.get("icon"):
                icon_ids.add(n["icon"])
            for group in ("panels", "events"):
                for item in (n.get("picture") or {}).get(group) or []:
                    if item.get("icon"):
                        icon_ids.add(item["icon"])
            if n.get("kind") == "picture":
                non_text += 1
                if (n.get("picture") or {}).get("item_id"):
                    pictures.add(n["picture"]["item_id"])
            elif n.get("kind") in ("icon", "crowd", "mark", "arrow", "value", "table", "tree") or n.get("flow"):
                non_text += 1
        if plan.get("graph"):
            non_text += 1
        if not non_text:
            text_only += 1
    n = len(plans)
    return {"parts": n, "world_parts": len(kits), "bank_shop": sum(1 for k in kits if k in ("bank", "shop")),
            "bank_shop_share": round(sum(1 for k in kits if k in ("bank", "shop")) / n, 3) if n else 0.0,
            "distinct_icons": len(icon_ids), "text_only_parts": text_only, "book_pictures_drawn": len(pictures)}


def build(canvas_dir: Path, video_id: str, *, lesson: dict | None = None, before: Path | None = None, note: str = "") -> str:
    e = html.escape
    ideas = json.loads((canvas_dir / "visual_ideas" / f"{video_id}.json").read_text(encoding="utf-8"))
    formats.check("visual_ideas", ideas, where=f"visual_ideas/{video_id}.json")
    canvas = json.loads((canvas_dir / "canvas.json").read_text(encoding="utf-8"))
    row = next((v for v in canvas.get("videos") or [] if v["video_id"] == video_id), {})
    report = row.get("report") or {}
    says = {}
    for v in (lesson or {}).get("videos") or []:
        if v.get("video_id") == video_id:
            says = {b["beat_id"]: b.get("say", "") for b in v.get("beats") or []}
    title = row.get("title") or video_id
    parts = [_page.page_head(f"{video_id} · dikhane ki list", EXTRA_CSS), "<main>",
             '<span class="tag">Task 046 · Part D1 · dikhane ki soch (render se pehle, by code)</span>',
             f"<h1>{e(video_id)} · {e(title)}</h1>",
             '<p class="lead">Har beat par learner ko kya <b>dikhega</b>, kis shabd par, aur kisne tay kiya: kitaab ki apni picture code ne '
             f"rakhi, baaki maker ne BIE ke visual verbs se. Yeh list render se pehle hai, taaki soch sasti jaanchi ja sake. {e(note)}</p>"]
    after = plan_measures(canvas_dir, video_id)
    cards = [("Distinct icons", report.get("distinct_icons", after["distinct_icons"])),
             ("Text-only screen", f"{report.get('text_only_seconds', 0)} s"),
             ("Kitaab ki pictures", f"{report.get('book_pictures_drawn', after['book_pictures_drawn'])} of {report.get('book_pictures', 0)}"),
             ("World parts", f"{after['world_parts']} of {after['parts']}")]
    parts.append('<div class="grid">' + "".join(f'<div class="card"><h3>{e(k)}</h3><p class="big">{e(str(v))}</p></div>' for k, v in cards) + "</div>")
    if before is not None and (before / "plans").is_dir():
        b = plan_measures(before, video_id)
        rows = [("Parts", b["parts"], after["parts"]), ("Bank + shop world parts", f"{b['bank_shop']} ({b['bank_shop_share']:.0%})",
                f"{after['bank_shop']} ({after['bank_shop_share']:.0%})"), ("Distinct icons", b["distinct_icons"], after["distinct_icons"]),
                ("Canvas parts with only text", b["text_only_parts"], after["text_only_parts"]),
                ("Kitaab ki pictures drawn", b["book_pictures_drawn"], after["book_pictures_drawn"])]
        parts.append("<h2>Pehle aur ab (plans se, by code)</h2>")
        parts.append('<div class="scroll"><table>' + _page._rows(["measure", "pehle (29–30 Oct)", "ab (Part D1)"], head=True)
                     + "".join(_page._rows([e(str(c)) for c in r]) for r in rows) + "</table></div>")
    if report.get("picture_types") or report.get("worlds"):
        parts.append(f'<p class="muted">Picture types: {e(", ".join(report.get("picture_types") or []))} · worlds: '
                     f'{e(", ".join(report.get("worlds") or []) or "koi nahi")}</p>')
    for p in ideas["parts"]:
        pic = p.get("picture") or {}
        books = p.get("book_pictures") or []
        head = f"{p['id']} · {p.get('part_id') or 'no part'} · mode {p.get('mode', '')}" + (f" ({p['kit']} world)" if p.get("kit") else "")
        parts.append(f"<h2>{e(head)}</h2>")
        parts.append(f'<p>Picture: <b>{e(pic.get("type", ""))}</b> · {e(BY.get(pic.get("by", ""), pic.get("by", "")))}'
                     + ("".join(f' · kitaab page {e(str(bp.get("page")))}: <i>{e(bp.get("title", ""))}</i> ({e(bp["type"])})' for bp in books))
                     + f' · status {e(p.get("status", ""))}</p>')
        rows = []
        for r in p["beats"]:
            say = says.get(r["beat_id"], "")
            rows.append(_page._rows([f'<b>{e(r["beat_id"])}</b>', e(_page._clip(say, 150)), e(r.get("idea", "")),
                                     f'<span class="rel">{e(r.get("relation", ""))}</span>' + (f'<br><span class="muted">{e(r.get("relation_note", ""))}</span>' if r.get("relation_note") else ""),
                                     f'<span class="shows">{e(r.get("shows", ""))}</span>' + (f'<br><span class="muted">photo: {e(r["image_wanted"])}</span>' if r.get("image_wanted") else ""),
                                     e(r.get("on_word", "") or "(shuru)"), e(", ".join(r.get("nouns") or [])), f'<span class="mono">{e(" ".join(r.get("icons") or []))}</span>']))
        parts.append('<div class="scroll"><table>' + _page._rows(["beat", "narration", "idea", "rishta", "dikhega", "kis shabd par", "cheezein", "icons"], head=True)
                     + "".join(rows) + "</table></div>")
    if ideas.get("relations_outside_list"):
        parts.append("<h2>Rishte jo list mein nahi the (Navin inhe visual_verbs.json mein jod sakte hain)</h2><ul>"
                     + "".join(f"<li>{e(o['part'])} {e(o['beat_id'])}: {e(o.get('note', ''))} ({e(o.get('idea', ''))})</li>" for o in ideas["relations_outside_list"]) + "</ul>")
    if ideas.get("needs"):
        parts.append("<h2>Zaroorat ki list (jo cheez kahin nahi mili)</h2>"
                     + '<div class="scroll"><table>' + _page._rows(["cheez", "kind", "beats", "kahan dhoondha"], head=True)
                     + "".join(_page._rows([e(n["thing"]), e(n["kind"]), e(", ".join(n.get("beats") or [])), e(", ".join(n.get("sources_tried") or []))])
                               for n in ideas["needs"]) + "</table></div>")
    parts.append('<p class="muted">Yeh page <code>tools/task046d_ideas_page.py</code> ne canvas run ke records se banaya; Claude ne koi soch, '
                 "picture ya shabd haath se nahi likha.</p></main>")
    return "\n".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--canvas", required=True, type=Path)
    parser.add_argument("--video", required=True)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--lesson", type=Path)
    parser.add_argument("--before-canvas", type=Path)
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)
    lesson = _page.load_run_json(args.lesson, "lesson_plan.json") if args.lesson else None
    page = build(args.canvas, args.video, lesson=lesson, before=args.before_canvas, note=args.note)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(page, encoding="utf-8")
    print(f"{args.html}: {len(page.encode('utf-8')) / 1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
