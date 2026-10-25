"""The readable toolbox page (Task 046a): subject family → capabilities → tools → status, the proof clips, what is
blocked and why, and the capabilities nothing can draw yet. Written to ``docs/toolbox/TOOLBOX.md`` by
``tools/toolbox_page.py`` from the registry and the demo results. Every lesson-use verdict on the page (per tool, per
source, per clip) is derived from the licence policy (``licence_policy.json``, Task 046a-L), never written by hand."""
from __future__ import annotations

from . import licence
from .demos import DEMOS, lesson_use
from .registry import STATUS_RANK, Toolbox
from .resolver import resolve

FLAG_TEXT = {"share_alike": "share-alike", "gpl": "GPL", "custom": "own licence", "per_item": "licence per item", "non_commercial": "non-commercial"}
STATUS_TEXT = {"used_on_real_book": "used on a real book", "demo_proven": "demo proven", "wrapped": "wrapped", "installed": "installed",
               "blocked_with_reason": "blocked"}
FAMILY_TEXT = {"all_subjects": "All subjects", "biology_medical": "Biology and medical", "chemistry": "Chemistry",
               "maths_statistics": "Maths and statistics", "physics": "Physics", "computer_science": "Computer science",
               "electrical_electronics": "Electrical and electronics", "mechanical_civil": "Mechanical and civil",
               "earth_science": "Geology and earth science", "astronomy_space": "Astronomy and space", "aerospace": "Aerospace",
               "geography_history_polity": "Geography, history and polity", "economics_commerce_management": "Economics, commerce and management",
               "law": "Law", "psychology_education_sociology": "Psychology, education and sociology", "languages_literature": "Languages and literature"}


def _flags(tool) -> str:
    return ", ".join(FLAG_TEXT[f] for f in tool.licence_flags) or "—"


def lesson_use_text(tool) -> str:
    """The lesson-use verdict of one tool or source, as the page shows it."""
    v = licence.tool_verdict(tool)
    if v.basis == "software":
        text = "software: allowed" + ("; cloud/CI/VM only, never in apps/" if "never ship inside apps/" in v.note else "")
        return text + ("; Remotion licence: Navin" if tool.id == "remotion" else "")
    text = {"allowed": "allowed", "refused": "**refused**", "needs_navin": "**needs Navin**", "per_item": "per item"}[v.verdict]
    if v.verdict == "allowed" and v.credit_required:
        text += " (credit)"
    return text + ("; India boundary: needs Navin" if v.note else "")


def clip_use(row: dict, box: Toolbox) -> dict:
    """A clip's lesson use: from its receipt when the demo runner judged it, otherwise judged now from its tools, its
    assets and the blocks in its spec."""
    if row.get("lesson_use"):
        return row["lesson_use"]
    known = {d.id: d for d in DEMOS}
    tools = known[row["demo"]].tools if row["demo"] in known else row.get("tools", [])
    return lesson_use(tools, row.get("assets") or [], row.get("blocks") or [], box=box)


def render_markdown(box: Toolbox, results: dict | None = None, *, missing_log: list | None = None, clips_note: str = "") -> str:
    results = results or {}
    rows = {r["demo"]: r for r in results.get("results", [])}
    counts = {}
    for t in box.tools:
        counts[t.status] = counts.get(t.status, 0) + 1
    lines = ["# BIE toolbox (auzaar-ghar)", "",
             "BIE ka auzaar-ghar: har library, tool aur asset source jo BIE kisi bhi scene ko dikhane ke liye use karta hai. "
             "A Python library computes, a BIE block shows.", "",
             f"Registry `{box.version}`, capabilities `{box.capabilities_version}`, npm packages as of `{box.npm_before}`. "
             f"Tools: {len(box.tools)} ("
             + ", ".join(f"{STATUS_TEXT[s]} {counts[s]}" for s in sorted(counts, key=lambda s: -STATUS_RANK[s])) + ").", "",
             "Status words: **installed** (the package is pinned and installs), **wrapped** (a BIE adapter or block uses it, with "
             "tests), **demo proven** (a BIE-made clip shows it working), **used on a real book** (it drew part of a real lesson), "
             "**blocked** (the reason says what it needs). Nothing here is ACCEPTED: that is Navin's verdict.", ""]
    if results:
        lines += [f"## Proof clips (batch {results.get('batch')})", "",
                  f"{sum(1 for r in rows.values() if r.get('passed'))} of {results.get('demos')} clips passed the checks "
                  "(not blank, something moves, 3–5 s). " + clips_note, "",
                  "Proof clips are internal proofs of the tools, not lessons. A clip whose content a lesson may not use (licence "
                  f"policy `{licence.version()}`) is marked **{licence.INTERNAL_PROOF}**; it stays as evidence.", "",
                  "| Clip | What it shows | Tools it proves | Length | Checks | Lesson use |", "| --- | --- | --- | --- | --- | --- |"]
        for r in rows.values():
            ok = "passed" if r.get("passed") else f"failed: {(r.get('error') or 'checks')[:80]}"
            known = {d.id: d for d in DEMOS}
            tools = known[r["demo"]].tools if r["demo"] in known else r.get("tools", [])      # the demo as the code defines it
            use = clip_use(r, box)
            shown = "lessons may use its content" if use["use"] == "lessons" else \
                f"**{use['use']}**: " + "; ".join(x.split(":", 2)[0] + ": " + x.split(":", 2)[1].strip() for x in use["reasons"])
            lines.append(f"| `{r['demo']}` | {r.get('title', '')} | {', '.join(tools)} | {r.get('seconds', '—')} s | {ok} | {shown} |")
        lines.append("")
    lines += ["## By subject family", ""]
    for family in box.families:
        caps = [c for c in box.capabilities.values() if family in c.families]
        if not caps:
            continue
        lines += [f"### {FAMILY_TEXT.get(family, family)}", "", "| Capability | Draws it (web) | Computes | Assets (lessons) | Offline | Proof clip |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for cap in caps:
            web = resolve(cap.id, subject=family, path="web", toolbox=box, log=None)
            offline = resolve(cap.id, subject=family, path="offline", toolbox=box, log=None)
            def names(ids):
                return ", ".join(f"{box.tool(i).name} ({STATUS_TEXT[box.tool(i).status]})" for i in ids[:3]) or "—"
            draw = names(web.draw) if not web.missing else "**missing**"
            clips = [d.id for d in DEMOS if cap.id in d.capabilities]                # a tool's status is per tool; this is per capability
            shown = ", ".join(f"`{c}`" + ("" if not rows or rows.get(c, {}).get("passed") else " (not passed)") for c in clips) or "none yet"
            held = "; not for lessons: " + ", ".join(h["tool"] for h in web.not_for_lessons) if web.not_for_lessons else ""
            assets = (names(web.assets) if web.assets else ("**none**" if web.licence_gap else "—")) + held
            lines.append(f"| {cap.id} | {draw} | {names(web.compute)} | {assets} | "
                         f"{names(offline.draw) if offline.path == 'offline' and not offline.missing else '—'} | {shown} |")
        lines.append("")
    lines += ["## Every tool", "", "Lesson use comes from the licence policy: content is allowed, refused, needs Navin or "
              "checked per item (per file); a program's licence governs the program, not what BIE draws with it.", "",
              "| Tool | Kind | Role / path | Version | Licence | Flags | Lesson use | Status | Batch |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for t in sorted(box.tools, key=lambda t: (t.batch, t.kind, t.id)):
        lines.append(f"| [{t.name}]({t.source}) | {t.kind} | {t.role} / {t.path} | {t.version} | {t.licence} | {_flags(t)} | "
                     f"{lesson_use_text(t)} | {STATUS_TEXT[t.status]} | {t.batch} |")
    blocked = [t for t in box.tools if t.status == "blocked_with_reason"]
    lines += ["", "## Blocked, and what each needs", ""]
    lines += [f"- **{t.name}**: {t.blocked_reason}" for t in blocked] or ["- Nothing is blocked."]
    missing = [c.id for c in box.capabilities.values() if resolve(c.id, path="web", toolbox=box, log=None).missing]
    lines += ["", "## Missing capabilities", "",
              "Capabilities in the vocabulary that no tool in the registry can draw yet (later batches, or the Task 046 merge path: "
              "an AI writes the block once, BIE tests it, Navin approves it):", ""]
    lines += [f"- {c}: {box.capabilities[c].label}" for c in missing] or ["- None."]
    if missing_log:
        lines += ["", "Logged by runs (capability, subject, times asked):", ""]
        lines += [f"- {m['capability']} ({m['subject'] or 'any subject'}): {m['count']}" for m in missing_log]
    lines += exam_lines(box)
    lines += gate_lines(box)
    return "\n".join(lines) + "\n"


def gate_lines(box: Toolbox) -> list:
    """The lesson licence gate: Navin's decision, what is blocked for lessons and why, and the open decisions."""
    pol = licence.policy()
    verdicts = {t.id: licence.tool_verdict(t) for t in box.tools}
    content = [t for t in box.tools if verdicts[t.id].basis != "software"]
    out = ["", "## Lesson licence gate", "",
           f"Navin, {pol['decided']['date']}: \"{pol['decided']['words']}\"", "",
           f"Policy `{pol['version']}` (`bie/toolbox/licence_policy.json`, the only source of truth). Lessons (anything seen or heard "
           "in a lesson video, game or notes) take only CC0, public domain and CC BY (with author, licence, licence URL and "
           "source page). The gate (`lesson_licence_check`) runs before any lesson output is rendered or packaged and stops it "
           "with the reason; nothing is swapped silently.", "", "Refused for lessons:", ""]
    out += [f"- {t.name}: {verdicts[t.id].reason}" for t in content if verdicts[t.id].verdict == "refused"] or ["- none"]
    out += ["", "Needs Navin (blocked until he approves the source by name in the policy file):", ""]
    out += [f"- {t.name}: {verdicts[t.id].reason}" for t in content if verdicts[t.id].verdict == "needs_navin"] or ["- none"]
    boundary = pol["india_boundary"]
    out += [f"- India's political boundary: {boundary['why']} (sources: {', '.join(boundary['sources'])}; blocks: "
            f"{', '.join(boundary['blocks'])})"]
    out += ["", "Checked per item (each file on its own licence):", ""]
    out += [f"- {t.name}: {verdicts[t.id].reason}" for t in content if verdicts[t.id].verdict == "per_item"]
    gpl = [t.name for t in licence.copyleft_programs(box.tools)]
    out += ["", f"Software: {pol['software']['rule']}. {pol['software']['gpl']}: {', '.join(gpl)}.", ""]
    out += [f"- Open decision (Navin): {d['decision']}" for d in pol["software"].get("open_decisions") or []]
    return out


def exam_lines(box: Toolbox) -> list:
    """The UGC NET and GATE map: how far the toolbox covers each subject today, and the gap where it does not."""
    from .exams import coverage
    cov = coverage(box)
    tot = cov["totals"]
    fit = lambda d: ", ".join(f"{k} {d.get(k, 0)}" for k in ("strong", "partial", "general"))
    out = ["", "## UGC NET and GATE map", "",
           f"{tot['ugc_net_subjects']} UGC NET subjects (plus Paper I) and {tot['gate_papers']} GATE papers, from the official lists "
           "(bie/toolbox/exam_map.json names the pages and the date). Fit is Claude's reading of the syllabus headings, for Navin to check: "
           "strong = the subject's own tools exist, partial = some, general = only the general blocks.", "",
           f"- UGC NET: {fit(tot['ugc_net_fit'])}", f"- GATE: {fit(tot['gate_fit'])}",
           f"- Subjects with no usable tool at all: {', '.join(tot['without_a_tool']) or 'none'}", ""]
    for exam, title in (("ugc_net", "UGC NET"), ("gate", "GATE")):
        out += [f"### {title}", "", "| Code | Subject | Families | Fit | Tools | Missing |", "| --- | --- | --- | --- | --- | --- |"]
        out += [f"| {r['code']} | {r['name']} | {', '.join(FAMILY_TEXT.get(f, f) for f in r['families'])} | {r['fit']} | {r['tools']} | "
                f"{r['gap'] or '—'} |" for r in cov[exam]]
        out.append("")
    return out
