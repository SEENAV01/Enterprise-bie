"""The readable toolbox page (Task 046a): subject family → capabilities → tools → status, the proof clips, what is
blocked and why, and the capabilities nothing can draw yet. Written to ``docs/toolbox/TOOLBOX.md`` by
``tools/toolbox_page.py`` from the registry and the demo results."""
from __future__ import annotations

from .demos import DEMOS
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
                  "| Clip | What it shows | Tools it proves | Length | Checks |", "| --- | --- | --- | --- | --- |"]
        for r in rows.values():
            ok = "passed" if r.get("passed") else f"failed: {(r.get('error') or 'checks')[:80]}"
            lines.append(f"| `{r['demo']}` | {r.get('title', '')} | {', '.join(r.get('tools', []))} | {r.get('seconds', '—')} s | {ok} |")
        lines.append("")
    lines += ["## By subject family", ""]
    for family in box.families:
        caps = [c for c in box.capabilities.values() if family in c.families]
        if not caps:
            continue
        lines += [f"### {FAMILY_TEXT.get(family, family)}", "", "| Capability | Draws it (web) | Computes | Assets | Offline | Proof clip |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for cap in caps:
            web = resolve(cap.id, subject=family, path="web", toolbox=box, log=None)
            offline = resolve(cap.id, subject=family, path="offline", toolbox=box, log=None)
            def names(ids):
                return ", ".join(f"{box.tool(i).name} ({STATUS_TEXT[box.tool(i).status]})" for i in ids[:3]) or "—"
            draw = names(web.draw) if not web.missing else "**missing**"
            clips = [d.id for d in DEMOS if cap.id in d.capabilities]                # a tool's status is per tool; this is per capability
            shown = ", ".join(f"`{c}`" + ("" if not rows or rows.get(c, {}).get("passed") else " (not passed)") for c in clips) or "none yet"
            lines.append(f"| {cap.id} | {draw} | {names(web.compute)} | {names(web.assets)} | "
                         f"{names(offline.draw) if offline.path == 'offline' and not offline.missing else '—'} | {shown} |")
        lines.append("")
    lines += ["## Every tool", "", "| Tool | Kind | Role / path | Version | Licence | Flags | Status | Batch |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for t in sorted(box.tools, key=lambda t: (t.batch, t.kind, t.id)):
        lines.append(f"| [{t.name}]({t.source}) | {t.kind} | {t.role} / {t.path} | {t.version} | {t.licence} | {_flags(t)} | "
                     f"{STATUS_TEXT[t.status]} | {t.batch} |")
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
    shared = [t for t in box.tools if set(t.licence_flags) & {"share_alike", "gpl", "custom"}]
    lines += ["", "## Licences to decide (Navin)", "",
              "Recorded, not blocked. Share-alike content may make an adapted video carry the same licence; a GPL program's "
              "outputs (the models BIE makes) are not GPL; Remotion needs a company licence above 3 people.", ""]
    lines += [f"- {t.name}: {t.licence}" for t in shared]
    return "\n".join(lines) + "\n"
