"""Render BIE notes as one self-contained, interactive HTML deck (phone first; its print view is the PDF).

Each slide shows its question and quick essence; "Samjho" opens the understand depth and "Gehraai" the
deep dive. The infographic is drawn from the slide's visual data (flow, timeline, difference table,
chart, relationship, concept map or tree, labelled list). Source chips show the book pages. Printing
opens every depth, one slide after another.
"""
from __future__ import annotations

import html
import json

PAGE = r"""<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f7f6f2;--card:#ffffff;--ink:#1d2433;--muted:#5d6676;--line:#dfe2e8;--accent:#0f6e68;--accent2:#b4532a;--soft:#e8f3f1;--warn:#fff4e5}
@media (prefers-color-scheme:dark){:root{--bg:#12161d;--card:#1b212b;--ink:#e9ecf1;--muted:#a3abb8;--line:#2c3441;--accent:#4fc1b6;--accent2:#f0965f;--soft:#1f3532;--warn:#3a2d1a}}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 "Noto Sans","Noto Sans Devanagari",system-ui,sans-serif}
header{padding:16px 16px 8px;max-width:860px;margin:auto}header h1{font-size:1.25rem;margin:0}header p{margin:2px 0 0;color:var(--muted);font-size:.9rem}
nav{max-width:860px;margin:auto;padding:0 16px;display:flex;gap:8px;align-items:center}
nav select{flex:1;min-width:0;padding:8px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);font:inherit}
nav button,.depth button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:8px 12px;font:inherit;cursor:pointer}
nav button:disabled{opacity:.4}
main{max-width:860px;margin:12px auto 40px;padding:0 16px}
.slide{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;display:none}
.slide.on{display:block}
.concept{font-size:.8rem;color:var(--accent);text-transform:uppercase;letter-spacing:.04em;font-weight:600}
.slide h2{font-size:1.25rem;margin:6px 0 10px}
.essence{font-size:1.05rem;background:var(--soft);border-radius:10px;padding:10px 12px;margin:0 0 12px}
.depth{display:flex;gap:8px;margin:10px 0}
.depth button[aria-pressed=true]{background:var(--accent);color:#fff;border-color:var(--accent)}
.more{display:none;margin:8px 0}.more.on{display:block}
.more h3{font-size:.85rem;margin:0 0 4px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.notbook{background:var(--warn);border-radius:10px;padding:8px 12px;margin:10px 0;font-size:.95rem}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.chip{font-size:.78rem;border:1px solid var(--line);border-radius:999px;padding:2px 9px;color:var(--muted)}
.chip.pyq{border-color:var(--accent2);color:var(--accent2)}.chip.basis{border-color:var(--accent);color:var(--accent)}
.visual{margin:14px 0 4px}.visual h4{margin:0 0 8px;font-size:.95rem}
.flow{display:flex;flex-wrap:wrap;gap:6px;align-items:stretch}
.step{flex:1 1 140px;border:1px solid var(--line);border-radius:10px;padding:8px 10px;cursor:pointer;position:relative;background:var(--card)}
.step b{display:block}.step .d{display:none;font-size:.9rem;color:var(--muted);margin-top:4px}.step.open .d{display:block}
.step .n{font-size:.75rem;color:var(--accent);font-weight:700}
.timeline{border-left:3px solid var(--accent);margin-left:8px;padding-left:14px}
.event{margin:0 0 10px;position:relative}.event:before{content:"";position:absolute;left:-21px;top:6px;width:11px;height:11px;border-radius:50%;background:var(--accent)}
.event .w{font-weight:700;color:var(--accent)}
.scroll{overflow-x:auto}table.diff{border-collapse:collapse;width:100%;font-size:.92rem}
table.diff th,table.diff td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
table.diff th{background:var(--soft);cursor:pointer}table.diff td.hl,table.diff th.hl{background:var(--accent);color:#fff}
.bars .bar{display:flex;align-items:center;gap:8px;margin:4px 0}.bars .bar span:first-child{width:38%;font-size:.9rem}
.bars .fill{height:18px;background:var(--accent);border-radius:4px}
.tree ul{list-style:none;margin:0;padding-left:18px;border-left:1px dashed var(--line)}.tree>ul{padding-left:0;border:0}
.tree li{margin:4px 0}.tree .node{cursor:pointer}.tree .node b:before{content:"▸ ";color:var(--accent)}.tree li.open>.node b:before{content:"▾ "}
.tree li>ul{display:none}.tree li.open>ul{display:block}.tree .d{color:var(--muted);font-size:.9rem}
.rel{display:grid;gap:6px}.rel div{border:1px solid var(--line);border-radius:10px;padding:6px 10px}
.labels{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:6px}
.labels div{border:1px solid var(--line);border-radius:10px;padding:6px 10px}
footer{max-width:860px;margin:auto;padding:0 16px 30px;color:var(--muted);font-size:.8rem}
@media print{nav,.depth{display:none}.slide{display:block!important;break-inside:avoid;margin:0 0 14px}.more{display:block!important}
.step .d{display:block}.tree li>ul{display:block}body{background:#fff}}
</style>
</head>
<body>
<header><h1>__TITLE__</h1><p>__SUBTITLE__</p></header>
<nav><button id="prev" aria-label="Pichhla">‹</button><select id="jump" aria-label="Slide chunein"></select><button id="next" aria-label="Agla">›</button></nav>
<main id="deck"></main>
<footer>BIE notes · __RULEBOOK__ · Kitaab ke page har baat ke saath diye gaye hain.</footer>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById("data").textContent);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
function visual(v) {
  const box = el("div", "visual");
  if (!v || v.type === "none") return box;
  if (v.title) box.appendChild(el("h4", null, v.title));
  if (v.type === "flow") {
    const f = el("div", "flow");
    v.steps.forEach((s, i) => { const d = el("div", "step"); d.appendChild(el("span", "n", String(i + 1))); d.appendChild(el("b", null, s.label));
      d.appendChild(el("div", "d", s.detail)); d.onclick = () => d.classList.toggle("open"); f.appendChild(d); });
    box.appendChild(f);
  } else if (v.type === "timeline") {
    const t = el("div", "timeline");
    v.events.forEach(e => { const d = el("div", "event"); d.appendChild(el("div", "w", e.when)); d.appendChild(el("b", null, e.label));
      if (e.detail) d.appendChild(el("div", "d", e.detail)); t.appendChild(d); });
    box.appendChild(t);
  } else if (v.type === "difference_table") {
    const t = el("table", "diff"), head = el("tr");
    head.appendChild(el("th", null, ""));
    v.columns.forEach((c, i) => { const th = el("th", null, c); th.onclick = () => {
        t.querySelectorAll(".hl").forEach(x => x.classList.remove("hl"));
        t.querySelectorAll("tr").forEach(r => { const cell = r.children[i + 1]; if (cell) cell.classList.add("hl"); }); };
      head.appendChild(th); });
    t.appendChild(head);
    v.rows.forEach(r => { const tr = el("tr"); tr.appendChild(el("th", null, r.label)); r.cells.forEach(c => tr.appendChild(el("td", null, c))); t.appendChild(tr); });
    const wrap = el("div", "scroll"); wrap.appendChild(t); box.appendChild(wrap);
  } else if (v.type === "chart") {
    const b = el("div", "bars"), max = Math.max(...v.series.map(s => Math.abs(s.value)), 1);
    v.series.forEach(s => { const r = el("div", "bar"); r.appendChild(el("span", null, s.label));
      const f = el("span", "fill"); f.style.width = (60 * Math.abs(s.value) / max) + "%"; r.appendChild(f);
      r.appendChild(el("span", null, s.value + (s.unit ? " " + s.unit : ""))); b.appendChild(r); });
    box.appendChild(b);
  } else if (v.type === "relationship") {
    const r = el("div", "rel"), names = Object.fromEntries(v.nodes.map(n => [n.id, n.label]));
    v.edges.forEach(e => r.appendChild(el("div", null, names[e.from_id] + "  →  " + e.label + "  →  " + names[e.to_id])));
    box.appendChild(r);
  } else if (v.type === "concept_map" || v.type === "tree") {
    const kids = {}; v.nodes.forEach(n => (kids[n.parent_id || ""] = kids[n.parent_id || ""] || []).push(n));
    const build = parent => { const ul = el("ul"); (kids[parent] || []).forEach(n => { const li = el("li", (kids[n.id] ? "" : "leaf")),
        node = el("div", "node"); node.appendChild(el("b", null, n.label)); if (n.detail) node.appendChild(el("div", "d", n.detail));
        node.onclick = () => li.classList.toggle("open"); li.appendChild(node); if (kids[n.id]) li.appendChild(build(n.id));
        if (!parent) li.classList.add("open"); ul.appendChild(li); }); return ul; };
    const t = el("div", "tree"); t.appendChild(build("")); box.appendChild(t);
  } else if (v.type === "labelled_list") {
    const l = el("div", "labels"); v.nodes.forEach(n => { const d = el("div"); d.appendChild(el("b", null, n.label));
      if (n.detail) d.appendChild(el("div", null, n.detail)); l.appendChild(d); }); box.appendChild(l);
  }
  return box;
}
const deck = document.getElementById("deck"), jump = document.getElementById("jump"), slides = [];
D.concepts.forEach(c => c.slides.forEach(s => {
  const card = el("section", "slide"); card.appendChild(el("div", "concept", c.name));
  card.appendChild(el("h2", null, s.question)); card.appendChild(el("p", "essence", s.essence));
  const depth = el("div", "depth"), more1 = el("div", "more"), more2 = el("div", "more");
  more1.appendChild(el("h3", null, "Samjho")); more1.appendChild(el("p", null, s.answer));
  more2.appendChild(el("h3", null, "Gehraai")); more2.appendChild(el("p", null, s.deep_dive));
  [["Samjho", more1], ["Gehraai", more2]].forEach(([label, part]) => { const b = el("button", null, label); b.setAttribute("aria-pressed", "false");
    b.onclick = () => { const on = part.classList.toggle("on"); b.setAttribute("aria-pressed", String(on)); }; depth.appendChild(b); });
  card.appendChild(depth); card.appendChild(visual(s.visual)); card.appendChild(more1); card.appendChild(more2);
  if (s.not_in_book) card.appendChild(el("div", "notbook", "Kitaab mein nahi: " + s.not_in_book));
  const chips = el("div", "chips");
  chips.appendChild(el("span", "chip basis", s.basis === "book" ? "Kitaab se" : s.basis === "outside" ? "Kitaab ke bahar se" : "Kitaab + bahar"));
  [...new Set(s.source_item_ids.map(i => (D.items[i] || {}).page).filter(Boolean))].sort((a, b) => a - b)
    .forEach(p => chips.appendChild(el("span", "chip", "Page " + p)));
  s.pyq_item_ids.forEach(q => chips.appendChild(el("span", "chip pyq", "PYQ")));
  card.appendChild(chips); deck.appendChild(card); slides.push(card);
  const o = el("option", null, (slides.length) + ". " + s.question); o.value = slides.length - 1; jump.appendChild(o);
}));
let at = 0;
function show(i) { at = Math.max(0, Math.min(slides.length - 1, i)); slides.forEach((s, k) => s.classList.toggle("on", k === at));
  jump.value = at; document.getElementById("prev").disabled = at === 0; document.getElementById("next").disabled = at === slides.length - 1; }
document.getElementById("prev").onclick = () => show(at - 1); document.getElementById("next").onclick = () => show(at + 1);
jump.onchange = () => show(Number(jump.value));
document.addEventListener("keydown", e => { if (e.key === "ArrowRight") show(at + 1); if (e.key === "ArrowLeft") show(at - 1); });
let x0 = null; deck.addEventListener("touchstart", e => x0 = e.touches[0].clientX, {passive: true});
deck.addEventListener("touchend", e => { if (x0 == null) return; const dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 60) show(at + (dx < 0 ? 1 : -1)); x0 = null; });
if (slides.length) show(0); else deck.appendChild(el("p", null, "Koi slide nahi bani."));
</script>
</body>
</html>
"""


def render_notes_html(notes: dict) -> str:
    course = notes.get("course") or {}
    data = {"concepts": [{"name": c["name"], "slides": c["slides"]} for c in notes.get("concepts", [])],
            "items": {iid: {"page": item["page"]} for iid, item in (notes.get("items") or {}).items()}}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    title = html.escape(f"{course.get('title', 'Notes')} · Notes")
    subtitle = html.escape(f"{course.get('subject', '')} · {course.get('learners', '')} · {course.get('language', '')}")
    return (PAGE.replace("__TITLE__", title).replace("__SUBTITLE__", subtitle)
            .replace("__RULEBOOK__", html.escape(str(notes.get("rulebook_version", "")))).replace("__DATA__", payload))
