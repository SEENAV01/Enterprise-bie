// Backgrounds and foregrounds of the showing engine (stage 1920×1080). Soft, low-contrast scenery so the things of
// the lesson stay in front; every function is pure SVG.

import { world } from "./worlds.mjs";

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

const worldBg = (kind) => `<g transform="translate(${W / 2},${H / 2})">${world({ kind, w: X1 - X0 })}</g>`;

export const BACKGROUNDS = {
  paper: () => `<rect x="${X0}" width="${X1 - X0}" height="${H}" fill="#f7f1e5"/>` + dots(),
  parchment: () => `<rect x="${X0}" width="${X1 - X0}" height="${H}" fill="#f3e7c9"/>` +
    `<rect width="${W}" height="${H}" fill="none" stroke="#d9c89a" stroke-width="40" opacity="0.5"/>` +
    `<rect x="26" y="26" width="${W - 52}" height="${H - 52}" fill="none" stroke="#b9a576" stroke-width="5" opacity="0.6"/>`,
  village: () => sky() + `<rect x="${X0}" y="700" width="${X1 - X0}" height="${H - 700}" fill="#ddc795"/>` +
    `<circle cx="1700" cy="170" r="80" fill="#ffd95a" opacity="0.9"/>` +
    `<ellipse cx="420" cy="140" rx="110" ry="40" fill="#ffffff" opacity="0.8"/><ellipse cx="1200" cy="220" rx="140" ry="46" fill="#ffffff" opacity="0.7"/>` +
    hut(260, 700, 1.0) + hut(640, 690, 0.72, "#e8d7ae") + tree(1500, 712, 1.1) + tree(90, 706, 0.8) +
    `<path d="M0 760 Q480 730 960 760 T1920 755" stroke="#cdb67f" stroke-width="10" fill="none" opacity="0.7"/>`,
  haat: () => sky("#d8ecf3", "#f0f6f2") + `<rect x="${X0}" y="690" width="${X1 - X0}" height="${H - 690}" fill="#d9c288"/>` +
    stall(260, 690, 1.0) + stall(1660, 690, 1.0, "#3a7bd5") + stall(2520, 690, 0.9, "#2fb463") + stall(-560, 690, 0.9, "#7b61ff") +
    `<path d="M${X0 + 150} 90 L${X1 - 150} 90" stroke="#c9b683" stroke-width="5"/>` +
    [...Array(24).keys()].map((i) => `<path d="M${X0 + 180 + i * 150} 92 L${X0 + 225 + i * 150} 150 L${X0 + 270 + i * 150} 92 Z" fill="${["#e0533d", "#f29f05", "#2fb463", "#3a7bd5", "#7b61ff"][i % 5]}" opacity="0.85"/>`).join("") +
    `<ellipse cx="960" cy="930" rx="840" ry="120" fill="#cdb67f" opacity="0.45"/>`,
  shop: () => `<rect x="${X0}" width="${X1 - X0}" height="${H}" fill="#efe3cf"/>` +
    `<rect x="${X0}" y="840" width="${X1 - X0}" height="${H - 840}" fill="#d9c8a6"/>` +
    `<rect x="120" y="120" width="640" height="300" fill="#e2d2b4" stroke="#bfa871" stroke-width="6"/>` +
    [0, 1].map((r) => `<rect x="140" y="${170 + r * 120}" width="600" height="14" fill="#bfa871"/>` +
      [0, 1, 2, 3, 4].map((i) => `<rect x="${170 + i * 115}" y="${120 + r * 120 + 10}" width="60" height="40" rx="8" fill="${["#c98850", "#8a9b56", "#c2447a", "#3a7bd5", "#c9a400"][(i + r) % 5]}" opacity="0.75"/>`).join("")).join("") +
    `<rect x="1280" y="100" width="520" height="130" rx="16" fill="#2b2b33"/><text x="1540" y="185" font-family="'Noto Sans','Noto Sans Devanagari',sans-serif" font-size="64" font-weight="800" fill="#f2c14e" text-anchor="middle">दुकान</text>`,
  store: () => `<rect x="${X0}" width="${X1 - X0}" height="${H}" fill="#e8dcc3"/>` +
    `<rect x="${X0}" y="860" width="${X1 - X0}" height="${H - 860}" fill="#c9b793"/>` +
    `<rect x="1320" y="180" width="480" height="480" fill="#dccFAD" opacity="0"/>` +
    [0, 1, 2].map((r) => `<rect x="1300" y="${240 + r * 170}" width="520" height="16" fill="#a08c5e"/>` +
      [0, 1, 2].map((i) => `<ellipse cx="${1400 + i * 160}" cy="${228 + r * 170}" rx="52" ry="36" fill="#bfa871" opacity="0.8"/>`).join("")).join("") +
    `<path d="M120 160 L540 160 L540 860 L120 860 Z" fill="#dfd2b2" stroke="#b9a576" stroke-width="6"/><path d="M180 160 L180 860 M300 160 L300 860 M420 160 L420 860" stroke="#cbbb92" stroke-width="5"/>`,
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
