"""Law as data for BIE's flowchart and case-card blocks (Task 046a, batch 3).

- ``find_section``: a section of an Act (from ``sources.india_code_act``) by its official title, never by a number
  typed from memory: the flowchart shows the section number India Code gives that title.
- ``procedure``: a flowchart (nodes, edges) whose steps are sections of the Act, each with its official number and
  title; a step that names a title the Act does not have stops the build.
- ``case_card``: the fields a judgment card shows, from ``sources.sc_judgment``'s record.
"""
from __future__ import annotations

import re


class LawDataError(ValueError):
    pass


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def find_section(act: dict, title: str, *, between=None) -> dict:
    """The one section whose official title is ``title`` (case and punctuation ignored), optionally within a number range
    (an Act may use one title twice, for example 'Acquittal or conviction.' for two kinds of trial)."""
    want = _norm(title)
    hits = []
    for s in act["sections"]:
        number = int(re.match(r"\d+", s["number"]).group()) if re.match(r"\d+", s["number"]) else -1
        if _norm(s["title"]) == want and (between is None or between[0] <= number <= between[1]):
            hits.append(s)
    if len(hits) != 1:
        where = f" between sections {between[0]} and {between[1]}" if between else ""
        raise LawDataError(f"{act['title']}: {len(hits)} sections titled {title!r}{where}; name exactly one")
    return hits[0]


def procedure(act: dict, steps: list, edges: list) -> dict:
    """``steps``: [{id, title (official section title) or text (a step that is not a section), label, kind, between}];
    ``edges``: [[from, to, label?]]. Kinds: step, decision, end."""
    nodes, ids = [], set()
    for st in steps:
        node = {"id": st["id"], "label": st.get("label") or "", "kind": st.get("kind", "step")}
        if "title" in st:
            sec = find_section(act, st["title"], between=st.get("between"))
            node.update(section=sec["number"], official_title=sec["title"].rstrip("."), label=node["label"] or sec["title"].rstrip("."))
        elif not node["label"]:
            raise LawDataError(f"step {st['id']!r} needs a section title or a label")
        nodes.append(node)
        ids.add(st["id"])
    bad = [e for e in edges if e[0] not in ids or e[1] not in ids]
    if bad:
        raise LawDataError(f"edges name unknown steps: {bad}")
    return {"act": {k: act.get(k) for k in ("title", "act_number", "year", "in_force", "act_id")}, "nodes": nodes,
            "edges": [{"from": e[0], "to": e[1], "label": e[2] if len(e) > 2 else ""} for e in edges],
            "source": "India Code (indiacode.gov.in), section titles as published"}


def case_card(record: dict) -> dict:
    """Title, parties, court, date, bench, citations and the PDF link of a judgment, ready for the card block."""
    day = record.get("decision_date") or ""
    m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", day)
    months = "January February March April May June July August September October November December".split()
    pretty = f"{int(m.group(1))} {months[int(m.group(2)) - 1]} {m.group(3)}" if m else day
    return {"title": record.get("title"), "petitioner": record.get("petitioner"), "respondent": record.get("respondent"),
            "court": record.get("court") or "Supreme Court of India", "decided": pretty,
            "bench": f"{record['bench_judges']} judges" if record.get("bench_judges") else "",
            "coram": record.get("coram") or [], "presiding": record.get("judge"),
            "citations": [c for c in (record.get("citation"), record.get("case_id")) if c], "cnr": record.get("cnr"),
            "languages": (record.get("available_languages") or "").split(","), "pdf": record.get("pdf")}


def listed_items(section: dict) -> list:
    """The items a section lists as (i) ...; (ii) ...; and (iii) ... (for example the classes of criminal courts)."""
    parts = re.split(r"\(([ivx]+)\)\s*", section["text"])
    items = [re.sub(r"[;,.]?\s*(and|or)?\s*$", "", parts[k + 1].strip()).strip(" ;.") for k in range(1, len(parts) - 1, 2)]
    if len(items) < 2:
        raise LawDataError(f"section {section['number']} lists no (i), (ii) ... items")
    return items
