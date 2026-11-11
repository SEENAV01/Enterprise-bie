// Backgrounds and foregrounds of the showing engine (stage 1920×1080). Soft, low-contrast scenery so the things of
// the lesson stay in front; every function is pure SVG.

import { world, worldSpots } from "./worlds.mjs";
import { svgBounds } from "./boxes.mjs";

const W = 1920, H = 1080;
// A camera can pan beyond the stage (the v2 plan pans to x=1250 at z=1), so every background paints from X0 to X1.
const X0 = -960, X1 = 2880;

function dots(color = "#e6ddc8", gap = 72) {
  let out = "";
  for (let y = gap; y < H; y += gap) for (let x = X0 + gap; x < X1; x += gap) out += `<circle cx="${x}" cy="${y}" r="2.2" fill="${color}"/>`;
  return out;
}

function hut(x, y, s, wall = "#e4cf9f", roof = "#c98850") {
  return `<g transform="translate(${x},${y}) scale(${s})">` +
    `<rect x="-90" y="-100" width="180" height="100" fill="${wall}" stroke="#bfa871" stroke-width="4"/>` +
    `<path d="M-110 -100 L0 -170 L110 -100 Z" fill="${roof}" stroke="#a5693a" stroke-width="4"/>` +
    `<rect x="-22" y="-62" width="44" height="62" fill="#8a5a2b"/></g>`;
}

function tree(x, y, s) {
  return `<g transform="translate(${x},${y}) scale(${s})"><rect x="-10" y="-70" width="20" height="70" fill="#8a5a2b"/>` +
    `<circle cx="0" cy="-100" r="56" fill="#9dbb6e"/><circle cx="-42" cy="-74" r="40" fill="#8fae5f"/><circle cx="42" cy="-74" r="40" fill="#a8c47e"/></g>`;
}

function stall(x, y, s, awn = "#e0533d") {
  return `<g transform="translate(${x},${y}) scale(${s})">` +
    `<rect x="-130" y="-150" width="12" height="150" fill="#8a5a2b"/><rect x="118" y="-150" width="12" height="150" fill="#8a5a2b"/>` +
    `<rect x="-140" y="-40" width="280" height="40" fill="#a9713c" stroke="#7a4e22" stroke-width="4"/>` +
    [0, 1, 2, 3].map((i) => `<path d="M${-150 + i * 75} -150 L${-75 + i * 75} -150 L${-93.75 + i * 75} -118 L${-131.25 + i * 75} -118 Z" fill="${i % 2 ? "#f3ead6" : awn}"/>`).join("") +
    `</g>`;
}

const sky = (top = "#cfe8f5", bottom = "#eaf4f9", gy = 700) =>
  `<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${top}"/><stop offset="1" stop-color="${bottom}"/></linearGradient></defs>` +
  `<rect x="${X0}" width="${X1 - X0}" height="${gy}" fill="url(#sky)"/>`;

// Painted fixtures the box rule reserves (Navin, 5 November 2026: "backgrounds.mjs har background ke reserved zone de
// (dukaan board, almari)"). Each is drawn by its own painter, so its zone is measured from the very drawing.
const shopShelf = () => `<rect x="120" y="120" width="640" height="300" fill="#e2d2b4" stroke="#bfa871" stroke-width="6"/>` +
  [0, 1].map((r) => `<rect x="140" y="${170 + r * 120}" width="600" height="14" fill="#bfa871"/>` +
    [0, 1, 2, 3, 4].map((i) => `<rect x="${170 + i * 115}" y="${120 + r * 120 + 10}" width="60" height="40" rx="8" fill="${["#c98850", "#8a9b56", "#c2447a", "#3a7bd5", "#c9a400"][(i + r) % 5]}" opacity="0.75"/>`).join("")).join("");
const shopBoard = () => `<rect x="1280" y="100" width="520" height="130" rx="16" fill="#2b2b33"/><text x="1540" y="185" font-family="'Noto Sans','Noto Sans Devanagari',sans-serif" font-size="64" font-weight="800" fill="#f2c14e" text-anchor="middle">दुकान</text>`;
const storeShelves = () => [0, 1, 2].map((r) => `<rect x="1300" y="${240 + r * 170}" width="520" height="16" fill="#a08c5e"/>` +
  [0, 1, 2].map((i) => `<ellipse cx="${1400 + i * 160}" cy="${228 + r * 170}" rx="52" ry="36" fill="#bfa871" opacity="0.8"/>`).join("")).join("");
const storeAlmari = () => `<path d="M120 160 L540 160 L540 860 L120 860 Z" fill="#dfd2b2" stroke="#b9a576" stroke-width="6"/><path d="M180 160 L180 860 M300 160 L300 860 M420 160 L420 860" stroke="#cbbb92" stroke-width="5"/>`;
const bunting = () => `<path d="M${X0 + 150} 90 L${X1 - 150} 90" stroke="#c9b683" stroke-width="5"/>` +
  [...Array(24).keys()].map((i) => `<path d="M${X0 + 180 + i * 150} 92 L${X0 + 225 + i * 150} 150 L${X0 + 270 + i * 150} 92 Z" fill="${["#e0533d", "#f29f05", "#2fb463", "#3a7bd5", "#7b61ff"][i % 5]}" opacity="0.85"/>`).join("");
const VILLAGE_HUTS = [[260, 700, 1.0], [640, 690, 0.72, "#e8d7ae"]];
const VILLAGE_TREES = [[1500, 712, 1.1], [90, 706, 0.8]];
const HAAT_STALLS = [[260, 690, 1.0], [1660, 690, 1.0, "#3a7bd5"], [2520, 690, 0.9, "#2fb463"], [-560, 690, 0.9, "#7b61ff"]];

const worldBg = (kind) => `<g transform="translate(${W / 2},${H / 2})">${world({ kind, w: X1 - X0 })}</g>`;

export const BACKGROUNDS = {
  paper: () => `<rect x="${X0}" width="${X1 - X0}" height="${H}" fill="#f7f1e5"/>` + dots(),
  parchment: () => `<rect x="${X0}" width="${X1 - X0}" height="${H}" fill="#f3e7c9"/>` +
    `<rect width="${W}" height="${H}" fill="none" stroke="#d9c89a" stroke-width="40" opacity="0.5"/>` +
    `<rect x="26" y="26" width="${W - 52}" height="${H - 52}" fill="none" stroke="#b9a576" stroke-width="5" opacity="0.6"/>`,
  village: () => sky() + `<rect x="${X0}" y="700" width="${X1 - X0}" height="${H - 700}" fill="#ddc795"/>` +
    `<circle cx="1700" cy="170" r="80" fill="#ffd95a" opacity="0.9"/>` +
    `<ellipse cx="420" cy="140" rx="110" ry="40" fill="#ffffff" opacity="0.8"/><ellipse cx="1200" cy="220" rx="140" ry="46" fill="#ffffff" opacity="0.7"/>` +
    VILLAGE_HUTS.map((a) => hut(...a)).join("") + VILLAGE_TREES.map((a) => tree(...a)).join("") +
    `<path d="M0 760 Q480 730 960 760 T1920 755" stroke="#cdb67f" stroke-width="10" fill="none" opacity="0.7"/>`,
  haat: () => sky("#d8ecf3", "#f0f6f2") + `<rect x="${X0}" y="690" width="${X1 - X0}" height="${H - 690}" fill="#d9c288"/>` +
    HAAT_STALLS.map((a) => stall(...a)).join("") + bunting() +
    `<ellipse cx="960" cy="930" rx="840" ry="120" fill="#cdb67f" opacity="0.45"/>`,
  shop: () => `<rect x="${X0}" width="${X1 - X0}" height="${H}" fill="#efe3cf"/>` +
    `<rect x="${X0}" y="840" width="${X1 - X0}" height="${H - 840}" fill="#d9c8a6"/>` + shopShelf() + shopBoard(),
  store: () => `<rect x="${X0}" width="${X1 - X0}" height="${H}" fill="#e8dcc3"/>` +
    `<rect x="${X0}" y="860" width="${X1 - X0}" height="${H - 860}" fill="#c9b793"/>` +
    `<rect x="1320" y="180" width="480" height="480" fill="#dccFAD" opacity="0"/>` + storeShelves() + storeAlmari(),
  // The economy worlds (worlds.mjs) at their defaults, as plain places; a world item in the plan (draw: "world")
  // is the same place with signs, an open vault, a trend, a crowd or night light that can change in its steps.
  market: () => worldBg("market"),
  bankHall: () => worldBg("bankHall"),
  centralBank: () => worldBg("centralBank"),
  exchangeFloor: () => worldBg("exchangeFloor"),
  port: () => worldBg("port"),
  factory: () => worldBg("factory"),
  office: () => worldBg("office"),
  court: () => worldBg("court"),
  city: () => worldBg("city"),
  assembly: () => worldBg("assembly"),
  twoCountries: () => worldBg("twoCountries"),
  forexCounter: () => worldBg("forexCounter"),
  // the Sloman book's places (5 Nov 2026), at their defaults
  mandi: () => worldBg("mandi"),
  foodStreet: () => worldBg("foodStreet"),
  labourChowk: () => worldBg("labourChowk"),
  factoryFloor: () => worldBg("factoryFloor"),
  farm: () => worldBg("farm"),
  riverTown: () => worldBg("riverTown"),
  mohalla: () => worldBg("mohalla"),
  canteen: () => worldBg("canteen"),
  home: () => worldBg("home"),
  teaEstate: () => worldBg("teaEstate"),
  busStand: () => worldBg("busStand"),
  petrolPump: () => worldBg("petrolPump"),
  venue: () => worldBg("venue"),
  godown: () => worldBg("godown"),
  island: () => worldBg("island"),
  twoSector: () => worldBg("twoSector"),
  dealingRoom: () => worldBg("dealingRoom"),
  hospital: () => worldBg("hospital"),
  foodShop: () => worldBg("foodShop"),
};

export const FOREGROUNDS = {
  counter: () => `<g>` +
    `<rect x="${X0}" y="660" width="${X1 - X0}" height="60" fill="#b5834a" stroke="#8a5a2b" stroke-width="5"/>` +
    `<rect x="${X0}" y="720" width="${X1 - X0}" height="360" fill="#a9713c"/>` +
    [0, 1, 2, 3, 4, 5].map((i) => `<rect x="${90 + i * 320}" y="760" width="220" height="260" rx="10" fill="none" stroke="#8a5a2b" stroke-width="6" opacity="0.7"/>`).join("") +
    `</g>`,
};

export function background(name) {
  return (BACKGROUNDS[name] || BACKGROUNDS.paper)();
}

export function foreground(name) {
  return name && FOREGROUNDS[name] ? FOREGROUNDS[name]() : "";
}

// ---------------------------------------------------------------- reserved zones (the box rule)
// keep "all": nothing of the plan may sit on it (a board, a cupboard, a shelf of goods, the bunting); keep "text": no
// word may sit on it, while a person or a thing may stand in front of it (a hut, a tree, a stall, a counter, a desk).
const PAINTED = {
  shop: [["board", "all", shopBoard], ["shelf", "all", shopShelf]],
  store: [["shelves", "all", storeShelves], ["almari", "all", storeAlmari]],
  village: [...VILLAGE_HUTS.map((a, i) => [`hut${i + 1}`, "text", () => hut(...a)]), ...VILLAGE_TREES.map((a, i) => [`tree${i + 1}`, "text", () => tree(...a)])],
  haat: [["bunting", "all", bunting], ...HAAT_STALLS.map((a, i) => [`stall${i + 1}`, "text", () => stall(...a)])],
};
// The world places (worlds.mjs) name their spots already; these are the reserved ones (floors, queues, roads and
// fields are where people stand, so they stay open).
export const WORLD_ZONES = {
  market: { stall: "text" }, bankHall: { vault: "all", counter: "text" }, centralBank: { vault: "all" },
  exchangeFloor: { board: "all" }, port: { ship: "text", crane: "text" }, factory: { shed: "text", chimney: "text", belt: "text" },
  village: { hut: "text", well: "text", tree: "text" }, office: { desk: "text" }, court: { bench: "text" },
  city: { shop: "text" }, assembly: { podium: "text", seats: "text" }, twoCountries: { border: "text" },
  forexCounter: { board: "all", counter: "text" },
  mandi: { board: "all", notice: "all", heap: "text", buyers: "text", truck: "text" }, foodStreet: { stall: "text" },
  labourChowk: { board: "all", crowd: "text", truck: "text" }, factoryFloor: { board: "all", notice: "all", machine: "text", belt: "text", godown: "text" },
  farm: { heap: "text", fence: "text" }, riverTown: { factory: "text", pipe: "text", ghat: "text" }, mohalla: { house: "text" },
  canteen: { menu: "all", notice: "all", counter: "text", tables: "text" }, home: { tv: "text", stove: "text", fridge: "text", desk: "text", door: "text" },
  teaEstate: { board: "all", factory: "text", lines: "text", gate: "text", union: "text" }, busStand: { bay: "text" }, petrolPump: { board: "all", pump: "text" },
  venue: { board: "all", screen: "text", seats: "text", window: "text", door: "text" }, godown: { board: "all", store: "text", door: "text" },
  island: { huts: "text", bank: "text", boat: "text", neighbour: "text" }, twoSector: { shed: "text", bench: "text" },
  dealingRoom: { board: "all", desk: "text" }, hospital: { cabin: "text", reception: "text", ward: "text" }, foodShop: { board: "all", oven: "text", till: "text", counter: "text" },
};

/** A world's reserved zones in its own coordinates (centred on its origin, at its p.w). */
export function worldZones(p = {}) {
  const kind = WORLD_ZONES[p.kind] ? p.kind : "market", keep = WORLD_ZONES[kind], k = (+p.w || 3840) / 3840, out = [];
  for (const [name, b] of Object.entries(worldSpots({ ...p, kind }))) {
    const base = name.replace(/\d+$/, "");
    if (!keep[base] || !/^[a-z]+\d*$/.test(name)) continue;           // a sign's words alias a numbered spot: counted once
    out.push({ name, keep: keep[base], box: [(b.x * 1920 - 960) * k, (b.y * 1080 - 540) * k, ((b.x + b.w) * 1920 - 960) * k, ((b.y + b.h) * 1080 - 540) * k].map((v) => +v.toFixed(1)) });
  }
  return out;
}

/** The reserved zones of a background, on the 1920x1080 stage. */
export function zonesOf(name) {
  if (PAINTED[name]) return PAINTED[name].map(([zone, keep, paint]) => ({ name: zone, keep, box: svgBounds(paint()).box }));
  const bg = BACKGROUNDS[name] ? name : null;
  if (bg && WORLD_ZONES[bg]) return worldZones({ kind: bg }).map((z) => ({ ...z, box: [z.box[0] + 960, z.box[1] + 540, z.box[2] + 960, z.box[3] + 540] }));
  return [];
}
