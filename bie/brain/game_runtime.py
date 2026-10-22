"""BIE's chapter game runtime: one self-contained, phone-first HTML file that plays game data.

Three mission engines cover the mechanics the game designer chooses:
- drag: the student drags parts (tokens) onto places (targets) on a real picture or a schematic board; every
  token-target pair has a rule; a wrong drop shows what breaks and why (break, fade, shake), a right one moves
  the process forward (glow, flow, grow); ``ordered`` stages must be done in sequence (run a process,
  assemble). On a picture board the board takes the picture's shape, so target boxes (fractions of the
  picture) sit exactly on the real parts.
- branch: the student acts as a character or a judge and chooses; a wrong choice breaks the timeline with the
  reason, a right one moves the story on.
- slider: the student predicts first by setting the slider, then sees the real answer, the relationship drawn
  from its data points and how far the guess was.
Progress and mastery stay on the device; a replay can shuffle the parts. ``window.__bot`` lets BIE's bot play
a mission step by step (start, one wrong move, the right moves) for the playtest screenshots;
``window.__autoplay(missionIndex)`` plays a whole mission.
"""
from __future__ import annotations

import html
import json

PAGE = r"""<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#07131d;--panel:#0f2533;--ink:#eef4f6;--muted:#9bb2bf;--accent:#37d2c2;--warm:#ffb35c;--bad:#ff6b6b;--line:rgba(255,255,255,.16)}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;min-height:100%;background:radial-gradient(circle at 50% 20%,#0d2a3a,#07131d 70%) fixed;color:var(--ink);
  font:16px/1.45 "Noto Sans","Noto Sans Devanagari",system-ui,sans-serif}
#app{max-width:860px;margin:auto;min-height:100vh;display:flex;flex-direction:column;padding:12px 14px 90px}
header{display:flex;align-items:center;gap:10px;margin-bottom:8px}
header h1{font-size:1.05rem;margin:0;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pill{display:inline-block;font-size:.8rem;border:1px solid var(--line);border-radius:999px;padding:3px 10px;color:var(--muted)}
.bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin-bottom:10px}.bar i{display:block;height:100%;background:var(--accent);transition:width .4s}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px}
.intro{color:var(--muted);margin:0 0 8px}
.instr{font-weight:700;margin:0 0 10px}
#stage{display:flex;flex-direction:column;gap:10px}
.board{position:relative;width:100%;height:46vh;min-height:220px;border-radius:14px;overflow:hidden;border:1px solid var(--line);background:#0b1d28;margin:0 auto}
.board.pic{height:auto;max-height:56vh;background:#fff}
.board img{position:absolute;inset:0;width:100%;height:100%;object-fit:fill}
.credit{position:absolute;right:6px;bottom:4px;font-size:.62rem;color:#333;background:rgba(255,255,255,.75);padding:1px 5px;border-radius:6px;max-width:70%;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.target{position:absolute;border:2px dashed rgba(55,210,194,.6);border-radius:12px;display:flex;align-items:center;justify-content:center;
  text-align:center;font-size:.85rem;color:var(--muted);padding:4px;transition:background .2s,border-color .2s;overflow:hidden}
.pic .target{border-color:rgba(0,120,110,.85);color:#06302b;font-weight:700;background:rgba(55,210,194,.08)}
.pic .target .dot{position:absolute;width:22px;height:22px;border-radius:50%;background:var(--warm);color:#2b1600;font-size:.75rem;display:flex;
  align-items:center;justify-content:center;left:50%;top:50%;transform:translate(-50%,-50%);box-shadow:0 0 0 3px rgba(255,255,255,.8)}
.target.hot{background:rgba(55,210,194,.25);border-color:var(--accent)}
.target.done{border-style:solid;border-color:var(--accent);background:rgba(55,210,194,.28);color:var(--ink);font-weight:700}
.pic .target.done{color:#04201c;background:rgba(55,210,194,.55)}
.target.broken{border-color:var(--bad);background:rgba(255,107,107,.25);animation:shake .4s}
.tray{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}
.token{user-select:none;touch-action:none;background:#163a4b;border:2px solid var(--accent);border-radius:12px;padding:8px 12px;font-weight:700;
  cursor:grab;box-shadow:0 6px 16px rgba(0,0,0,.35);max-width:100%}
.token.drag{position:fixed;z-index:9;pointer-events:none;transform:scale(1.06)}
.token.used{opacity:.3;pointer-events:none}
.order{font-size:.8rem;color:var(--warm)}
.choices{display:grid;gap:8px}
.choice{text-align:left;background:#163a4b;border:2px solid var(--line);color:var(--ink);border-radius:12px;padding:12px;font:inherit;cursor:pointer}
.choice:active{border-color:var(--accent)}
.timeline{display:flex;gap:6px;align-items:center;margin:4px 0 8px}.timeline i{flex:1;height:8px;border-radius:4px;background:var(--line)}
.timeline i.ok{background:var(--accent)}.timeline i.broken{background:var(--bad);animation:shake .4s}
.slider{display:grid;gap:10px}.slider input{width:100%}
.reveal{font-size:1.05rem;font-weight:800;color:var(--warm)}
.chart{width:100%;height:auto;background:#0b1d28;border-radius:12px;border:1px solid var(--line)}
.toast{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);width:min(92vw,760px);z-index:10;border-radius:14px;padding:12px 16px;
  box-shadow:0 12px 30px rgba(0,0,0,.45);display:none}
.toast.on{display:block;animation:pop .25s}.toast.good{background:#0f3d37;border:2px solid var(--accent)}.toast.bad{background:#3d1717;border:2px solid var(--bad)}
.toast b{display:block;margin-bottom:2px}
.btn{background:var(--accent);color:#04201c;border:0;border-radius:12px;padding:10px 16px;font:inherit;font-weight:800;cursor:pointer}
.btn.ghost{background:transparent;color:var(--ink);border:1px solid var(--line)}
.end{text-align:center;display:grid;gap:12px;place-items:center;margin:auto}
.menu{display:grid;gap:8px}
.mission{display:flex;justify-content:space-between;align-items:center;gap:8px}
.credits{margin-top:16px;font-size:.72rem;color:var(--muted)}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}
@keyframes pop{from{transform:translate(-50%,10px);opacity:0}to{transform:translate(-50%,0);opacity:1}}
@keyframes glow{0%{box-shadow:0 0 0 rgba(55,210,194,0)}50%{box-shadow:0 0 30px rgba(55,210,194,.9)}100%{box-shadow:0 0 0 rgba(55,210,194,0)}}
.glow{animation:glow .9s}
</style>
</head>
<body>
<div id="app"></div>
<div id="toast" class="toast" role="status"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
const G = JSON.parse(document.getElementById("data").textContent);
const KEY = "bie-game-" + G.id;
let save = {}; try { save = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { save = {}; }
const store = () => { try { localStorage.setItem(KEY, JSON.stringify(save)); } catch (e) {} };
const app = document.getElementById("app"), toastEl = document.getElementById("toast");
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const shuffle = (a) => { const b = a.slice(); for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; } return b; };
let toastTimer = null;
function toast(good, title, text) {
  toastEl.className = "toast on " + (good ? "good" : "bad"); toastEl.innerHTML = "";
  toastEl.appendChild(el("b", null, title)); if (text) toastEl.appendChild(el("div", null, text));
  clearTimeout(toastTimer); toastTimer = setTimeout(() => toastEl.className = "toast", good ? 2600 : 5200);
}
function menu() {
  current = null; app.innerHTML = "";
  const head = el("header"); head.appendChild(el("h1", null, G.title)); app.appendChild(head);
  if (G.world) app.appendChild(el("p", "intro", G.world));
  const list = el("div", "menu");
  G.missions.forEach((m, i) => {
    const row = el("div", "card mission"), st = save[m.mission_id] || {};
    const left = el("div"); left.appendChild(el("b", null, (i + 1) + ". " + m.title)); left.appendChild(el("br"));
    left.appendChild(el("span", "pill", st.mastery != null ? "Mastery " + Math.round(st.mastery * 100) + "%" : "Naya"));
    if (st.weak && st.weak.length) left.appendChild(el("span", "pill", " Kamzor: " + st.weak.length));
    const go = el("button", "btn", st.mastery >= 0.8 ? "Dobara" : "Khelo"); go.onclick = () => play(i);
    row.appendChild(left); row.appendChild(go); list.appendChild(row);
  });
  app.appendChild(list);
  if (G.credits && G.credits.length) {
    const c = el("div", "credits"); c.appendChild(el("b", null, "Chitron ka shrey: "));
    c.appendChild(document.createTextNode(G.credits.join(" · "))); app.appendChild(c);
  }
}
let current = null;
function play(index, auto) {
  const m = G.missions[index]; const st = save[m.mission_id] || {};
  const twist = (st.plays || 0) > 0 ? (m.replay_twist || "none") : "none";
  current = { m, index, stage: 0, firstTry: 0, twist, auto: !!auto, stages: m.stages, weak: [] };
  renderStage();
}
function header() {
  const c = current; app.innerHTML = "";
  const head = el("header"); const back = el("button", "btn ghost", "‹"); back.onclick = menu; head.appendChild(back);
  head.appendChild(el("h1", null, c.m.title)); head.appendChild(el("span", "pill", (c.stage + 1) + "/" + c.stages.length)); app.appendChild(head);
  const bar = el("div", "bar"), fill = el("i"); fill.style.width = (100 * c.stage / c.stages.length) + "%"; bar.appendChild(fill); app.appendChild(bar);
  if (c.stage === 0 && c.m.intro) app.appendChild(el("p", "intro", c.m.intro));
}
function next(firstTry) {
  const c = current; if (!c) return;
  if (firstTry) c.firstTry += 1; else c.weak.push(c.stages[c.stage].stage_id);
  c.stage += 1;
  if (c.stage >= c.stages.length) return finish();
  setTimeout(renderStage, c.auto ? 30 : 900);
}
function finish() {
  const c = current, st = save[c.m.mission_id] || {};
  const mastery = c.firstTry / c.stages.length;
  save[c.m.mission_id] = { plays: (st.plays || 0) + 1, mastery: Math.max(mastery, st.mastery || 0), last: mastery, weak: c.weak }; store();
  c.finished = true; app.innerHTML = ""; const box = el("div", "card end");
  box.appendChild(el("h2", null, mastery >= 0.8 ? "Shabaash!" : "Ek baar aur?"));
  box.appendChild(el("p", null, c.m.win_text || ""));
  box.appendChild(el("div", "pill", "Pehli koshish mein sahi: " + c.firstTry + "/" + c.stages.length));
  const again = el("button", "btn", "Dobara khelo"); again.onclick = () => play(c.index);
  const back = el("button", "btn ghost", "Missions"); back.onclick = menu;
  box.appendChild(again); box.appendChild(back); app.appendChild(box);
}
function renderStage() {
  header(); const s = current.stages[current.stage]; const wrap = el("div"); wrap.id = "stage";
  wrap.appendChild(el("p", "instr", s.instruction)); app.appendChild(wrap);
  current.wrong = current.right = null;
  if (s.kind === "drag") dragStage(s, wrap); else if (s.kind === "branch") branchStage(s, wrap); else sliderStage(s, wrap);
}
function effect(node, kind) {
  if (!node) return;
  node.classList.remove("glow", "broken"); void node.offsetWidth;
  if (kind === "break" || kind === "shake" || kind === "fade") node.classList.add("broken");
  if (kind === "glow" || kind === "flow" || kind === "grow") node.classList.add("glow");
}
function autoBox(i, n) {
  const cols = n <= 2 ? n : n <= 4 ? 2 : 3, rows = Math.ceil(n / cols), w = 0.9 / cols, h = 0.86 / rows;
  return { x: 0.05 + (i % cols) * w + 0.01, y: 0.07 + Math.floor(i / cols) * h + 0.01, w: w - 0.02, h: h - 0.02 };
}
function dragStage(s, wrap) {
  const board = el("div", "board"), bg = s.background && s.background.src ? s.background : null;
  if (bg) { board.classList.add("pic"); board.style.aspectRatio = bg.width + " / " + bg.height;
    board.style.maxWidth = "calc(56vh * " + (bg.width / bg.height) + ")";
    const img = el("img"); img.src = bg.src; img.alt = bg.alt || ""; board.appendChild(img);
    if (bg.credit) board.appendChild(el("div", "credit", bg.credit)); }
  const targets = {};
  s.targets.forEach((t, i) => {
    const d = el("div", "target", bg ? null : (t.label || "")); const b = t.box && t.box.w ? t.box : autoBox(i, s.targets.length);
    if (bg) { d.appendChild(el("span", "dot", String(i + 1))); if (t.label) d.title = t.label; }
    Object.assign(d.style, { left: b.x * 100 + "%", top: b.y * 100 + "%", width: b.w * 100 + "%", height: b.h * 100 + "%" });
    d.dataset.id = t.id; board.appendChild(d); targets[t.id] = d;
  });
  wrap.appendChild(board);
  const tray = el("div", "tray"); wrap.appendChild(tray);
  const firstRight = {}; s.rules.forEach(r => { if (r.correct && !(r.token in firstRight)) firstRight[r.token] = r; });
  const order = Object.keys(firstRight);
  if (s.ordered) wrap.insertBefore(el("div", "order", "Kram zaroori hai: process jaise chalta hai, waise hi karo."), tray);
  let done = new Set(), mistakes = 0;
  const tokens = current.twist === "shuffle_tokens" ? shuffle(s.tokens) : s.tokens;
  function drop(tokenId, targetId, chip) {
    if (done.has(tokenId)) return;
    const rule = s.rules.find(r => r.token === tokenId && r.target === targetId);
    const node = targets[targetId];
    if (s.ordered && rule && rule.correct && order[done.size] !== tokenId) {
      mistakes++; effect(node, "break"); return toast(false, "Kram toota!", "Pehle woh kadam aata hai jo is se pehle hota hai. Process sahi kram mein hi chalta hai.");
    }
    if (!rule || !rule.correct) {
      mistakes++; effect(node, rule ? rule.effect : "shake");
      return toast(false, "Yahan nahi!", rule ? rule.feedback : "Yeh hissa yahan fit nahi hota. Socho iska kaam kya hai.");
    }
    done.add(tokenId); if (chip) chip.classList.add("used"); node.classList.add("done");
    const dot = node.querySelector(".dot"); if (dot) dot.remove();
    const tok = s.tokens.find(t => t.id === tokenId);
    node.appendChild(el("span", null, (node.dataset.filled ? " · " : "") + (tok ? tok.label : tokenId))); node.dataset.filled = "1";
    effect(node, rule.effect || "glow"); toast(true, "Sahi!", rule.feedback);
    if (order.every(t => done.has(t))) next(mistakes === 0);
  }
  tokens.forEach(t => {
    const chip = el("div", "token", t.label); chip.dataset.id = t.id; tray.appendChild(chip);
    chip.addEventListener("pointerdown", e => {
      e.preventDefault(); const ghost = chip.cloneNode(true); ghost.classList.add("drag"); document.body.appendChild(ghost);
      const inside = (n, ev) => { const r = n.getBoundingClientRect(); return ev.clientX > r.left && ev.clientX < r.right && ev.clientY > r.top && ev.clientY < r.bottom; };
      const move = ev => { ghost.style.left = ev.clientX - ghost.offsetWidth / 2 + "px"; ghost.style.top = ev.clientY - ghost.offsetHeight / 2 + "px";
        Object.values(targets).forEach(n => n.classList.toggle("hot", inside(n, ev))); };
      const up = ev => { document.removeEventListener("pointermove", move); document.removeEventListener("pointerup", up); ghost.remove();
        let hit = null; Object.values(targets).forEach(n => { n.classList.remove("hot"); if (inside(n, ev)) hit = n; });
        if (hit) drop(t.id, hit.dataset.id, chip); };
      move(e); document.addEventListener("pointermove", move); document.addEventListener("pointerup", up);
    });
  });
  const chipOf = id => tray.querySelector('[data-id="' + CSS.escape(id) + '"]');
  current.wrong = () => { const w = s.rules.find(r => !r.correct); if (w) drop(w.token, w.target, chipOf(w.token)); return !!w; };
  current.right = () => order.forEach(t => drop(t, firstRight[t].target, chipOf(t)));
}
function branchStage(s, wrap) {
  const line = el("div", "timeline"); current.stages.forEach((_, i) => { const seg = el("i"); if (i < current.stage) seg.className = "ok"; line.appendChild(seg); });
  wrap.appendChild(line);
  const card = el("div", "card"); card.appendChild(el("p", null, s.situation)); wrap.appendChild(card);
  const box = el("div", "choices"); let mistakes = 0, over = false;
  const choose = (c, btn) => {
    if (over) return; const seg = line.children[current.stage];
    if (!c.correct) { mistakes++; seg.className = "broken"; if (btn) effect(btn, "shake"); return toast(false, "Yahan kahani toot gayi!", c.feedback); }
    over = true; seg.className = "ok"; toast(true, "Sahi faisla!", c.feedback); next(mistakes === 0);
  };
  const buttons = new Map();
  (current.twist === "shuffle_tokens" ? shuffle(s.choices) : s.choices).forEach(c => { const b = el("button", "choice", c.label); b.onclick = () => choose(c, b); buttons.set(c, b); box.appendChild(b); });
  wrap.appendChild(box);
  current.wrong = () => { const w = s.choices.find(c => !c.correct); if (w) choose(w, buttons.get(w)); return !!w; };
  current.right = () => { const r = s.choices.find(c => c.correct); if (r) choose(r, buttons.get(r)); };
}
function valueAt(data, x) {
  const pts = data.slice().sort((a, b) => a.x - b.x); if (!pts.length) return 0;
  if (x <= pts[0].x) return pts[0].y; if (x >= pts[pts.length - 1].x) return pts[pts.length - 1].y;
  for (let i = 1; i < pts.length; i++) if (x <= pts[i].x) { const a = pts[i - 1], b = pts[i]; return a.y + (b.y - a.y) * (x - a.x) / (b.x - a.x); }
  return 0;
}
const fmtNum = v => Math.abs(v) >= 100 ? String(Math.round(v)) : String(Math.round(v * 100) / 100);
function chart(sl, guess) {
  const pts = (sl.data || []).slice().sort((a, b) => a.x - b.x); if (pts.length < 2) return null;
  const W = 600, H = 260, P = 40, xs = pts.map(p => p.x), ys = pts.map(p => p.y);
  const x0 = Math.min(...xs, sl.min), x1 = Math.max(...xs, sl.max), y0 = Math.min(...ys, 0), y1 = Math.max(...ys) || 1;
  const X = v => P + (W - 2 * P) * (v - x0) / ((x1 - x0) || 1), Y = v => H - P - (H - 2 * P) * (v - y0) / ((y1 - y0) || 1);
  const ns = "http://www.w3.org/2000/svg", svg = document.createElementNS(ns, "svg"); svg.setAttribute("viewBox", "0 0 " + W + " " + H); svg.setAttribute("class", "chart");
  const add = (tag, attrs, text) => { const n = document.createElementNS(ns, tag); for (const k in attrs) n.setAttribute(k, attrs[k]); if (text != null) n.textContent = text; svg.appendChild(n); return n; };
  add("line", { x1: P, y1: H - P, x2: W - P, y2: H - P, stroke: "#557", "stroke-width": 2 }); add("line", { x1: P, y1: P / 2, x2: P, y2: H - P, stroke: "#557", "stroke-width": 2 });
  add("polyline", { points: pts.map(p => X(p.x) + "," + Y(p.y)).join(" "), fill: "none", stroke: "#37d2c2", "stroke-width": 4 });
  pts.forEach(p => add("circle", { cx: X(p.x), cy: Y(p.y), r: 4, fill: "#37d2c2" }));
  add("line", { x1: X(guess), y1: P / 2, x2: X(guess), y2: H - P, stroke: "#ffb35c", "stroke-width": 3, "stroke-dasharray": "6 5" });
  add("text", { x: X(guess) + 6, y: P / 2 + 14, fill: "#ffb35c", "font-size": 16 }, "aapka andaaza");
  add("line", { x1: X(Number(sl.answer)), y1: P / 2, x2: X(Number(sl.answer)), y2: H - P, stroke: "#eef4f6", "stroke-width": 2 });
  add("text", { x: P, y: H - 10, fill: "#9bb2bf", "font-size": 15 }, fmtNum(x0) + " " + (sl.unit || ""));
  add("text", { x: W - P, y: H - 10, fill: "#9bb2bf", "font-size": 15, "text-anchor": "end" }, fmtNum(x1) + " " + (sl.unit || ""));
  add("text", { x: P + 6, y: P / 2 + 2, fill: "#9bb2bf", "font-size": 15 }, fmtNum(y1));
  return svg;
}
function sliderStage(s, wrap) {
  const sl = s.slider, card = el("div", "card slider");
  card.appendChild(el("p", null, sl.predict_prompt));
  const input = el("input"); Object.assign(input, { type: "range", min: sl.min, max: sl.max, step: sl.step || 1 }); input.value = (Number(sl.min) + Number(sl.max)) / 2;
  const show = el("div", "pill"), out = el("div", "reveal");
  const label = () => show.textContent = sl.label + ": " + input.value + " " + (sl.unit || "");
  input.oninput = label; label(); card.appendChild(input); card.appendChild(show);
  const check = el("button", "btn", "Mera andaaza pakka"); card.appendChild(check); card.appendChild(out); wrap.appendChild(card);
  const truth = Number(sl.answer), tol = Number(sl.tolerance || (sl.max - sl.min) * 0.1);
  let revealed = false, close = false, moved = false;
  const go = () => { if (!moved) { moved = true; next(close); } };
  const reveal = () => {
    if (revealed) return; revealed = true; input.disabled = true; check.remove();
    const guess = Number(input.value); close = Math.abs(guess - truth) <= tol;
    out.textContent = sl.reveal_label + ": " + fmtNum(truth) + " " + (sl.unit || "") + " · aapka andaaza: " + fmtNum(guess);
    const svg = chart(sl, guess); if (svg) card.appendChild(svg);
    toast(close, close ? "Bahut paas!" : "Phir socho", close ? s.feedback_close : s.feedback_far);
    const btn = el("button", "btn", "Aage badho"); btn.onclick = go; card.appendChild(btn);
  };
  check.onclick = reveal;
  current.wrong = () => { input.value = Math.abs(sl.min - truth) > tol ? sl.min : sl.max; label(); if (Math.abs(Number(input.value) - truth) <= tol) return false; reveal(); return true; };
  current.right = () => { if (!revealed) { input.value = truth; label(); reveal(); } go(); };
}
function state() {
  if (!current) return null;
  return { mission: current.m.mission_id, stage: current.stage, total: current.stages.length, finished: !!current.finished,
           kind: current.finished ? "" : current.stages[current.stage].kind, stage_id: current.finished ? "" : current.stages[current.stage].stage_id };
}
window.__bot = {
  start: (index) => { play(index, true); return state(); },
  wrong: () => { const did = current && current.wrong ? current.wrong() : false; return Object.assign(state() || {}, { wrong_done: !!did }); },
  right: () => { if (current && current.right) current.right(); return state(); },
  state,
};
window.__autoplay = (index) => new Promise(resolve => {
  window.__bot.start(index); let guard = 0;
  const step = () => {
    const st = state(); if (!st || st.finished || guard++ > 200) return resolve(save[G.missions[index].mission_id]);
    const before = st.stage; window.__bot.wrong(); window.__bot.right();
    setTimeout(() => { const now = state(); if (now && !now.finished && now.stage === before) return resolve(save[G.missions[index].mission_id]); step(); }, 80);
  };
  setTimeout(step, 50);
});
window.__game = G;
menu();
</script>
</body>
</html>
"""


def render_game_html(game: dict) -> str:
    payload = json.dumps(game, ensure_ascii=False).replace("</", "<\\/")
    return PAGE.replace("__TITLE__", html.escape(game.get("title", "BIE game"))).replace("__DATA__", payload)
