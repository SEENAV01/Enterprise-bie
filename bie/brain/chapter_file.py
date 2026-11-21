"""The chapter file ("kitaab ki file"): the whole chapter, as BIE understood it, in one file an AI can read at once
(Navin, 21 November 2026: "codex ko ek output file do jisse wo asani se content ko samjh paaye aur fir hamare niyam to
lage hi hai ... wo poore chapter ko pdhana kaise hai script analogies examples real world use case saman ki list technical
terms aur kitab se bahar jaakar kuchh cheejen add karni pade wo kar sakta hai").

Built by code from Section 1's chapter map (``chapter_map.json``: the items read from each page with both eyes, the
chapter's concepts and links) and nothing else: no AI call, nothing written by hand. The book's own order and sections
lead (``item.ncert_section`` and ``item.zone`` from ``reading.chapter_structure``); under each section every item stands
in reading order with what it is (its role in the book, its content type, its exam weight, how deep it must be taught),
the terms it opens (with their first appearance), its why steps, what it leads to, what the screen should show, what
must come first, and, for a figure, its labels. Then the concepts, how they hang together, the prerequisites, the exam
focus and Section 1's suggested order.

Three views of the same content: ``build`` (JSON, for code), ``markdown`` (CHAPTER.md, the file the teaching planner
reads whole, with BIE's rules beside it) and ``html`` (the "samajh ka page" Navin reads on his tablet; a review page,
never the learner's screen).
"""
from __future__ import annotations

import html as html_module
import re

SCHEMA = "bie.brain.chapter-file/1"
ROLE_WORDS = {"teach": "padhana hai", "in_text_question": "kitaab ka sawaal", "reader_talk": "kitaab ki baatcheet",
              "activity": "activity", "biography": "jeevani", "summary": "summary", "exercise": "exercise",
              "heading": "heading", "caption": "caption", "": "-"}
ZONE_TITLES = {"summary": "Summary", "exercise": "Exercises", "points_to_ponder": "Points to ponder"}
PART_KINDS = ("diagram_label", "table_row", "answer_option")


def _item_number(item_id: str) -> int:
    found = re.search(r"-i(\d+)$", item_id or "")
    return int(found.group(1)) if found else 0


def _order(items: dict) -> list:
    return sorted(items, key=lambda i: (items[i].get("page", 0), _item_number(i)))


def _terms(item: dict) -> list:
    return [{"term": t.get("term", ""), "meaning": t.get("plain_meaning", ""), "image": t.get("everyday_image", "")}
            for t in (item.get("unpack") or {}).get("terms") or [] if t.get("term")]


def _row(iid: str, item: dict, first_seen: dict, children: list) -> dict:
    unpack = item.get("unpack") or {}
    terms = _terms(item)
    for term in terms:
        key = term["term"].casefold()
        term["first_here"] = first_seen.setdefault(key, iid) == iid
    deepest = max((q for q in item.get("teacher_understanding") or [] if q.get("ask") in ("why", "how")),
                  key=lambda q: q.get("depth", 1), default=None)
    return {
        "id": iid, "page": item.get("page"), "kind": item.get("kind", ""), "role": item.get("role", ""),
        "content_type": item.get("content_type", ""), "content": item.get("content", ""),
        "teachable": bool(item.get("teachable")), "exam": item.get("exam_importance", ""),
        "exam_note": item.get("exam_note", ""),
        "depth": item.get("teach_depth", "normal"), "deep_why": item.get("deep_why", ""),
        "terms": terms,
        "why": [s.get("step", "") for s in unpack.get("why_chain") or [] if s.get("step")],
        "example": unpack.get("example_or_place", ""), "leads_to": unpack.get("consequence", ""),
        "show": unpack.get("visual_verb", ""), "level_extra": unpack.get("level_extra", ""),
        "needs_first": list(item.get("prerequisites") or []),
        "key_question": {"q": deepest.get("question", ""), "a": deepest.get("answer", ""), "basis": deepest.get("basis", "")}
        if deepest else None,
        "parts": [{"id": cid, "kind": c.get("kind", ""), "content": c.get("content", "")} for cid, c in children],
    }


def build(chapter: dict) -> dict:
    """The chapter file as data: {"schema", "course", "sections": [{"number", "title", "zone", "pages", "items"}],
    "concepts", "relations", "prerequisites", "exam_focus", "suggested_order", "counts"}."""
    items = chapter.get("items") or {}
    heads = {(h.get("number", ""), h.get("zone", "body")): h for h in chapter.get("ncert_sections") or []}
    order = _order(items)
    children = {}
    for iid in order:
        parent = items[iid].get("parent_item_id") or ""
        if parent and items[iid].get("kind") in PART_KINDS:
            full = parent if parent in items else f"{iid.rsplit('-', 1)[0]}-{parent}"
            if full in items:
                children.setdefault(full, []).append((iid, items[iid]))
    folded = {cid for rows in children.values() for cid, _ in rows}
    sections, first_seen, by_key = [], {}, {}
    for iid in order:
        if iid in folded:
            continue
        item = items[iid]
        key = (item.get("ncert_section", ""), item.get("zone", "body"))
        if key not in by_key:
            head = heads.get(key) or {}
            title = head.get("title") or (ZONE_TITLES.get(key[1], "") if key[1] != "body" else ("" if key[0] else "Opening"))
            by_key[key] = {"number": key[0] if key[1] == "body" else "", "title": title, "zone": key[1], "pages": [], "items": []}
            sections.append(by_key[key])
        section = by_key[key]
        if item.get("page") not in section["pages"]:
            section["pages"].append(item.get("page"))
        section["items"].append(_row(iid, item, first_seen, children.get(iid, [])))
    plan = chapter.get("map") or {}
    names = {c.get("concept_id"): c.get("name", "") for c in plan.get("concepts") or []}
    roles = {}
    for item in items.values():
        roles[item.get("role") or ""] = roles.get(item.get("role") or "", 0) + 1
    return {
        "schema": SCHEMA, "course": chapter.get("course") or {}, "level": chapter.get("level", ""),
        "chapter_title": plan.get("chapter_title") or (chapter.get("course") or {}).get("title", ""),
        "summary": plan.get("chapter_summary", ""),
        "sections": sections,
        "concepts": [{"id": c.get("concept_id"), "name": c.get("name", ""), "type": c.get("content_type", ""),
                      "explanation": c.get("core_explanation", ""), "items": list(c.get("item_ids") or [])}
                     for c in plan.get("concepts") or []],
        "relations": [{"from": r.get("from_concept"), "relation": r.get("relation"), "to": r.get("to_concept"),
                       "note": r.get("note", "")} for r in plan.get("relations") or []],
        "prerequisites": [{"name": p.get("name", ""), "why": p.get("why_needed", ""), "for": list(p.get("needed_for") or []),
                           "basis": p.get("basis", "")} for p in plan.get("prerequisites_to_teach") or []],
        "exam_focus": [{"concept": e.get("concept_id"), "name": names.get(e.get("concept_id"), ""), "why": e.get("why", "")}
                       for e in plan.get("exam_focus") or []],
        "suggested_order": [names.get(c, c) for c in plan.get("teaching_order") or []],
        "counts": {"items": len(items), "teachable": sum(1 for i in items.values() if i.get("teachable")),
                   "sections": len(sections), "concepts": len(plan.get("concepts") or []), "roles": roles,
                   "terms": len(first_seen)},
    }


def _section_name(section: dict) -> str:
    return " ".join(x for x in (section["number"], section["title"]) if x) or "Opening"


def markdown(chapter: dict) -> str:
    """CHAPTER.md: the file the teaching planner reads whole."""
    data = build(chapter)
    course = data["course"]
    out = [f"# {data['chapter_title']}", "",
           f"{course.get('subject', '')} · {course.get('learners', '')} · {course.get('exam', '')} · level {data['level']}", "",
           "BIE's chapter file: the whole chapter in the book's own order, read from each page's text and image. Every item "
           "keeps its id (page and item) so a plan can name exactly what it teaches. Per item: [id · role · content type · "
           "exam weight · depth], then the book's words, the terms it opens (★ = first time in the chapter), the why "
           "steps, what it leads to, what the screen should show and what must come first. A figure lists its labels.", ""]
    if data["summary"]:
        out += ["## The chapter in brief", "", data["summary"], ""]
    out += ["## The book's sections", ""]
    out += [f"- {_section_name(s)} (pages {', '.join(str(p) for p in s['pages'])}): {len(s['items'])} items" for s in data["sections"]]
    out.append("")
    needed = set()
    for section in data["sections"]:
        out += [f"## {_section_name(section)}", ""]
        for row in section["items"]:
            tags = [row["id"], row["role"] or row["kind"], row["content_type"]]
            if row["exam"]:
                tags.append(f"exam {row['exam']}")
            if row["depth"] == "deep":
                tags.append(f"deep: {row['deep_why']}")
            out.append(f"- [{' · '.join(t for t in tags if t)}] {row['content']}")
            for part in row["parts"]:
                out.append(f"  - {part['kind']}: {part['content']}")
            if row["terms"]:          # a term is opened once: later it is only named
                out.append("  terms: " + "; ".join(f"★ {t['term']} = {t['meaning']}" if t["first_here"] else t["term"]
                                                  for t in row["terms"]))
            if row["why"]:
                out.append("  why: " + " → ".join(row["why"][:3]))
            keys = (("leads to", "leads_to"), ("example", "example"), ("show", "show"))
            if row["exam"] == "high":
                keys += (("exam", "exam_note"),)
            for label, key in keys:
                if row[key]:
                    out.append(f"  {label}: {row[key]}")
            new = [p for p in row["needs_first"] if p.casefold() not in needed]
            needed.update(p.casefold() for p in new)
            if new:
                out.append("  needs first: " + "; ".join(new))
        out.append("")
    out += ["## Concepts", ""]
    out += [f"- {c['id']} {c['name']} ({c['type']}): {c['explanation']} · items {', '.join(c['items'])}" for c in data["concepts"]]
    out += ["", "## How the concepts hang together", ""]
    out += [f"- {r['from']} {r['relation']} {r['to']}: {r['note']}" for r in data["relations"]]
    out += ["", "## Prerequisites to teach first", ""]
    out += [f"- {p['name']} ({p['basis']}): {p['why']} · for {', '.join(p['for'])}" for p in data["prerequisites"]]
    out += ["", "## Exam focus", ""]
    out += [f"- {e['concept']} {e['name']}: {e['why']}" for e in data["exam_focus"]]
    if data["suggested_order"]:
        out += ["", "## Section 1's suggested order of concepts", ""]
        out += [f"{n}. {name}" for n, name in enumerate(data["suggested_order"], 1)]
    return "\n".join(out).rstrip() + "\n"


def html(chapter: dict) -> str:
    """The "samajh ka page": the same file for Navin (Hinglish headings, a section to a fold; a review page)."""
    data = build(chapter)
    e = html_module.escape
    counts = data["counts"]
    roles = ", ".join(f"{ROLE_WORDS.get(k, k)} {v}" for k, v in sorted(counts["roles"].items(), key=lambda kv: -kv[1]))
    parts = [f"""<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Samajh ka page · {e(data['chapter_title'])}</title><style>
body{{font:16px/1.6 system-ui,sans-serif;margin:0;padding:16px;background:#faf8f3;color:#222}}main{{max-width:900px;margin:auto}}
h1{{font-size:22px;margin:.2em 0}}h2{{font-size:18px;margin:1.4em 0 .4em}}details{{background:#fff;border:1px solid #ddd6c8;border-radius:10px;
margin:8px 0;padding:6px 12px}}summary{{cursor:pointer;font-weight:600}}.it{{border-top:1px solid #eee;padding:8px 0}}
.tag{{display:inline-block;font-size:12px;border-radius:6px;padding:0 6px;margin-right:4px;background:#eef2e8;color:#2f4d1f}}
.r-in_text_question{{background:#e7eefb;color:#1d3d7a}}.r-reader_talk{{background:#f3ecfb;color:#4b2a78}}.r-exercise{{background:#fdeee6;color:#7a3413}}
.r-biography,.r-activity,.r-summary{{background:#fbf3df;color:#6b4a07}}.deep{{background:#fde7ea;color:#7a1f2b}}
.k{{color:#666;font-size:14px}}.sum{{color:#555}}</style></head><body><main>
<p class="sum">BIE · samajh ka page (review page, learner ko nahi dikhta)</p><h1>{e(data['chapter_title'])}</h1>
<p>{counts['items']} items ({counts['teachable']} padhane wale) · {counts['sections']} hisse · {counts['concepts']} concepts ·
{counts['terms']} technical terms<br>{e(roles)}</p>"""]
    if data["summary"]:
        parts.append(f"<p>{e(data['summary'])}</p>")
    parts.append("<h2>Kitaab ke hisse, kram se</h2>")
    for section in data["sections"]:
        parts.append(f"<details><summary>{e(_section_name(section))} · page {', '.join(str(p) for p in section['pages'])} · "
                     f"{len(section['items'])} items</summary>")
        for row in section["items"]:
            tags = [f'<span class="tag r-{e(row["role"])}">{e(ROLE_WORDS.get(row["role"], row["role"] or row["kind"]))}</span>',
                    f'<span class="tag">{e(row["content_type"])}</span>']
            if row["exam"]:
                tags.append(f'<span class="tag">NEET {e(row["exam"])}</span>')
            if row["depth"] == "deep":
                tags.append(f'<span class="tag deep">gehra: {e(row["deep_why"])}</span>')
            body = [f'<div class="it">{"".join(tags)} <span class="k">{e(row["id"])}</span><div>{e(row["content"])}</div>']
            for part in row["parts"]:
                body.append(f'<div class="k">↳ {e(part["kind"])}: {e(part["content"])}</div>')
            if row["terms"]:
                body.append('<div class="k">Terms: ' + "; ".join(
                    f"{'★ ' if t['first_here'] else ''}<b>{e(t['term'])}</b> = {e(t['meaning'])}" for t in row["terms"]) + "</div>")
            if row["why"]:
                body.append(f'<div class="k">Kyun: {e(" → ".join(row["why"]))}</div>')
            if row["leads_to"]:
                body.append(f'<div class="k">Aage: {e(row["leads_to"])}</div>')
            if row["show"]:
                body.append(f'<div class="k">Screen par: {e(row["show"])}</div>')
            if row["needs_first"]:
                body.append(f'<div class="k">Pehle chahiye: {e("; ".join(row["needs_first"]))}</div>')
            body.append("</div>")
            parts.append("".join(body))
        parts.append("</details>")
    names = {c["id"]: c["name"] for c in data["concepts"]}
    parts.append("<h2>Concepts aur unke rishte</h2><details><summary>"
                 f"{len(data['concepts'])} concepts, {len(data['relations'])} rishte</summary>")
    parts += [f'<div class="it"><b>{e(c["id"])} {e(c["name"])}</b> <span class="tag">{e(c["type"])}</span><div>{e(c["explanation"])}</div></div>'
              for c in data["concepts"]]
    parts += [f'<div class="k">{e(names.get(r["from"], r["from"] or ""))} → <b>{e(r["relation"] or "")}</b> → '
              f'{e(names.get(r["to"], r["to"] or ""))}: {e(r["note"])}</div>' for r in data["relations"]]
    parts.append("</details><h2>Pehle yeh jaan lo (prerequisites)</h2><details><summary>"
                 f"{len(data['prerequisites'])} prerequisites</summary>")
    parts += [f'<div class="it"><b>{e(p["name"])}</b>: {e(p["why"])}</div>' for p in data["prerequisites"]]
    parts.append("</details></main></body></html>")
    return "\n".join(parts)
