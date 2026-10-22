// BIE's game bot: plays one mission of a game page on a phone-sized screen, one wrong move and then the right
// moves on every stage, and takes screenshots for the reviewer.
//   node game_bot.mjs <game.html> <out-dir> [width] [height] [max-shots] [mission-index]
// Prints one JSON line: {shots, stages, won, stuck, errors, layout, wrong_moves, mastery}.
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [pagePath, outDir, w = "390", h = "844", limitArg = "6", missionArg = "0"] = process.argv.slice(2);
const require = createRequire(join(process.env.NODE_PATH || execFileSync("npm", ["root", "-g"]).toString().trim(), "_"));
const { chromium } = require("playwright");
const width = Number(w), height = Number(h), limit = Math.max(2, Number(limitArg)), mission = Number(missionArg);
const browser = await chromium.launch({ args: ["--disable-gpu", "--allow-file-access-from-files"] });
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
const errors = [], layout = [], shots = [];
page.on("pageerror", (e) => errors.push(String(e).slice(0, 300)));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text().slice(0, 300)); });
const wait = (ms) => page.waitForTimeout(ms);
const shot = async (name) => {
  if (shots.length >= limit) return;
  await page.screenshot({ path: join(outDir, name), type: "jpeg", quality: 82, fullPage: true });
  shots.push(name);
};
const inspect = (stageId) => page.evaluate((sid) => {
  const found = [], board = document.querySelector(".board");
  if (board) {
    const b = board.getBoundingClientRect();
    if (b.height < 150) found.push(`stage ${sid}: the board is only ${Math.round(b.height)} px tall on a phone`);
    document.querySelectorAll(".target").forEach((t) => {
      const r = t.getBoundingClientRect();
      if (r.left < b.left - 2 || r.top < b.top - 2 || r.right > b.right + 2 || r.bottom > b.bottom + 2)
        found.push(`stage ${sid}: target ${t.dataset.id} lies outside the board`);
      if (r.width < 28 || r.height < 28) found.push(`stage ${sid}: target ${t.dataset.id} is smaller than a fingertip (${Math.round(r.width)}x${Math.round(r.height)} px)`);
    });
  }
  document.querySelectorAll(".token").forEach((t) => {
    if (t.scrollWidth > t.clientWidth + 2) found.push(`stage ${sid}: token "${t.textContent.slice(0, 40)}" is cut off`);
  });
  const total = document.documentElement.scrollHeight;
  if (total > window.innerHeight * 2.2) found.push(`stage ${sid}: needs ${Math.round(total / window.innerHeight * 10) / 10} screens of scrolling`);
  return found;
}, stageId);

let result = { stages: 0, won: 0, stuck: "", wrong_moves: 0, mastery: null };
try {
  await page.goto(pathToFileURL(resolve(pagePath)).href);
  await page.waitForFunction(() => !!window.__bot);
  let st = await page.evaluate((i) => window.__bot.start(i), mission);
  result.stages = st.total;
  await wait(120);
  let k = 0;
  const seenKinds = new Set();
  while (st && !st.finished && k < st.total + 2) {
    const sid = st.stage_id, kind = st.kind;
    layout.push(...(await inspect(sid)));
    if (k === 0) await shot(`${String(k + 1).padStart(2, "0")}-${sid}-start.jpg`);
    const w1 = await page.evaluate(() => window.__bot.wrong());
    if (w1.wrong_done) {
      result.wrong_moves += 1;
      await wait(260);
      if (!seenKinds.has(kind)) { seenKinds.add(kind); await shot(`${String(k + 1).padStart(2, "0")}-${sid}-wrong.jpg`); }
    }
    const before = st.stage;
    let now = await page.evaluate(() => window.__bot.state());
    if (now && !now.finished && now.stage === before) {
      await page.evaluate(() => window.__bot.right());
      await wait(150);
      now = await page.evaluate(() => window.__bot.state());
    }
    if (!now || (!now.finished && now.stage === before)) { result.stuck = sid; break; }
    result.won += 1;
    await wait(80);
    st = await page.evaluate(() => window.__bot.state());
    k += 1;
  }
  if (st && st.finished) {
    shots.length = Math.min(shots.length, limit - 1);
    await wait(150);
    await page.screenshot({ path: join(outDir, "99-end.jpg"), type: "jpeg", quality: 82 });
    shots.push("99-end.jpg");
    result.mastery = await page.evaluate((i) => { try { return JSON.parse(localStorage.getItem("bie-game-" + window.__game.id) || "{}")[window.__game.missions[i].mission_id] || null; } catch (e) { return null; } }, mission);
  }
} catch (e) {
  errors.push("bot: " + String(e).slice(0, 300));
}
await browser.close();
console.log(JSON.stringify({ shots, ...result, errors, layout }));
