// Economy kit saanche, batch 3 (4 Nov 2026). Learned from 37 reference videos: the things they draw most that the
// v2 demo library did not have. BIE's own drawings: no logos, emblems, real banknote designs or real persons.
// Every function returns SVG markup. Anchor: buildings, vaults and crowds stand on y = 0 (bottom centre);
// badges, papers and discs are centred on (0, 0). `p` (0..1) is the progress of the saancha's own animation.
(function () {
  const D = window.BIEDraw;
  const T = (s, x, y, size, opt) => D.text(s, x, y, size, opt);
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const ease = (t) => 1 - Math.pow(1 - clamp(t), 3);
  let uid = 0;
  const nid = (p) => `es${p}${++uid}`;

  // ------------------------------------------------------------- institution badge (replaces logos and emblems)
  // The references show a real logo or emblem in 25 of 37 videos (94 segments). BIE never does: it shows this badge.
  const KINDS = {
    central_bank: { c1: "#138a8a", c2: "#0b5f63", glyph: "coin" },
    bank: { c1: "#3a7bd5", c2: "#2459a6", glyph: "columns" },
    government: { c1: "#e07b24", c2: "#b85a12", glyph: "dome" },
    regulator: { c1: "#7b5cd6", c2: "#5638a8", glyph: "scale" },
    international: { c1: "#2a9d8f", c2: "#1b6f66", glyph: "globe" },
    cooperative: { c1: "#2fa35b", c2: "#1d7a40", glyph: "hands" },
    committee: { c1: "#a0703d", c2: "#764e25", glyph: "table" },
    market: { c1: "#d6454f", c2: "#a52a35", glyph: "chart" },
    company: { c1: "#4a5568", c2: "#2d3748", glyph: "factory" },
  };
  function glyph(kind, s) {
    const w = "#ffffff";
    switch (kind) {
      case "coin": return `<circle r="${s * 0.42}" fill="none" stroke="${w}" stroke-width="${s * 0.09}"/>${T("₹", 0, s * 0.02, s * 0.55, { fill: w, weight: 800 })}`;
      case "columns": return `<path d="M ${-s * 0.5} ${-s * 0.18} L 0 ${-s * 0.5} L ${s * 0.5} ${-s * 0.18} Z" fill="${w}"/>${[-0.34, -0.11, 0.11, 0.34].map((x) => `<rect x="${x * s - s * 0.06}" y="${-s * 0.12}" width="${s * 0.12}" height="${s * 0.46}" fill="${w}"/>`).join("")}<rect x="${-s * 0.52}" y="${s * 0.36}" width="${s * 1.04}" height="${s * 0.1}" fill="${w}"/>`;
      case "dome": return `<path d="M ${-s * 0.32} ${-s * 0.08} A ${s * 0.32} ${s * 0.32} 0 0 1 ${s * 0.32} ${-s * 0.08} Z" fill="${w}"/><rect x="${-s * 0.03}" y="${-s * 0.55}" width="${s * 0.06}" height="${s * 0.18}" fill="${w}"/>${[-0.36, -0.12, 0.12, 0.36].map((x) => `<rect x="${x * s - s * 0.05}" y="${-s * 0.02}" width="${s * 0.1}" height="${s * 0.36}" fill="${w}"/>`).join("")}<rect x="${-s * 0.5}" y="${s * 0.36}" width="${s}" height="${s * 0.1}" fill="${w}"/>`;
      case "scale": return `<rect x="${-s * 0.04}" y="${-s * 0.45}" width="${s * 0.08}" height="${s * 0.8}" fill="${w}"/><rect x="${-s * 0.46}" y="${-s * 0.36}" width="${s * 0.92}" height="${s * 0.07}" fill="${w}"/><path d="M ${-s * 0.52} ${s * 0.02} L ${-s * 0.4} ${-s * 0.3} L ${-s * 0.28} ${s * 0.02} Z M ${s * 0.28} ${s * 0.02} L ${s * 0.4} ${-s * 0.3} L ${s * 0.52} ${s * 0.02} Z" fill="none" stroke="${w}" stroke-width="${s * 0.04}"/><path d="M ${-s * 0.54} ${s * 0.02} A ${s * 0.14} ${s * 0.1} 0 0 0 ${-s * 0.26} ${s * 0.02} Z M ${s * 0.26} ${s * 0.02} A ${s * 0.14} ${s * 0.1} 0 0 0 ${s * 0.54} ${s * 0.02} Z" fill="${w}"/><rect x="${-s * 0.22}" y="${s * 0.34}" width="${s * 0.44}" height="${s * 0.08}" fill="${w}"/>`;
      case "globe": return `<circle r="${s * 0.42}" fill="none" stroke="${w}" stroke-width="${s * 0.07}"/><ellipse rx="${s * 0.18}" ry="${s * 0.42}" fill="none" stroke="${w}" stroke-width="${s * 0.05}"/><line x1="${-s * 0.42}" y1="0" x2="${s * 0.42}" y2="0" stroke="${w}" stroke-width="${s * 0.05}"/><path d="M ${-s * 0.36} ${-s * 0.2} Q 0 ${-s * 0.1} ${s * 0.36} ${-s * 0.2} M ${-s * 0.36} ${s * 0.2} Q 0 ${s * 0.1} ${s * 0.36} ${s * 0.2}" fill="none" stroke="${w}" stroke-width="${s * 0.04}"/>`;
      case "hands": return [-0.3, 0, 0.3].map((x, i) => `<circle cx="${x * s}" cy="${-s * 0.22 + (i === 1 ? -s * 0.06 : 0)}" r="${s * 0.12}" fill="${w}"/><path d="M ${x * s - s * 0.17} ${s * 0.3} Q ${x * s - s * 0.17} ${-s * 0.04} ${x * s} ${-s * 0.04} Q ${x * s + s * 0.17} ${-s * 0.04} ${x * s + s * 0.17} ${s * 0.3} Z" fill="${w}"/>`).join("") + `<path d="M ${-s * 0.48} ${s * 0.1} Q 0 ${s * 0.32} ${s * 0.48} ${s * 0.1}" fill="none" stroke="${w}" stroke-width="${s * 0.06}"/>`;
      case "table": return [-0.32, 0, 0.32].map((x) => `<circle cx="${x * s}" cy="${-s * 0.24}" r="${s * 0.11}" fill="${w}"/><rect x="${x * s - s * 0.13}" y="${-s * 0.11}" width="${s * 0.26}" height="${s * 0.22}" rx="${s * 0.08}" fill="${w}"/>`).join("") + `<rect x="${-s * 0.52}" y="${s * 0.1}" width="${s * 1.04}" height="${s * 0.1}" rx="${s * 0.03}" fill="${w}"/><rect x="${-s * 0.42}" y="${s * 0.2}" width="${s * 0.07}" height="${s * 0.22}" fill="${w}"/><rect x="${s * 0.35}" y="${s * 0.2}" width="${s * 0.07}" height="${s * 0.22}" fill="${w}"/>`;
      case "chart": return `<path d="M ${-s * 0.45} ${s * 0.3} L ${-s * 0.15} ${-s * 0.05} L ${s * 0.08} ${s * 0.12} L ${s * 0.42} ${-s * 0.35}" fill="none" stroke="${w}" stroke-width="${s * 0.09}" stroke-linecap="round" stroke-linejoin="round"/><path d="M ${s * 0.22} ${-s * 0.4} L ${s * 0.46} ${-s * 0.4} L ${s * 0.46} ${-s * 0.16}" fill="none" stroke="${w}" stroke-width="${s * 0.08}" stroke-linecap="round"/>`;
      case "factory": return `<path d="M ${-s * 0.5} ${s * 0.4} L ${-s * 0.5} ${-s * 0.05} L ${-s * 0.2} ${s * 0.12} L ${-s * 0.2} ${-s * 0.05} L ${s * 0.1} ${s * 0.12} L ${s * 0.1} ${-s * 0.45} L ${s * 0.3} ${-s * 0.45} L ${s * 0.3} ${s * 0.12} L ${s * 0.5} ${s * 0.12} L ${s * 0.5} ${s * 0.4} Z" fill="${w}"/>`;
      default: return "";
    }
  }
  D.institutionBadge = ({ w = 200, name = "RBI", sub = "", kind = "central_bank", color, p = 1 } = {}) => {
    const k = KINDS[kind] || KINDS.bank, c1 = color || k.c1, c2 = color ? color : k.c2, r = w / 2, g = nid("b");
    const sc = 0.6 + 0.4 * ease(p);
    const fs = name.length > 5 ? r * 0.3 : name.length > 3 ? r * 0.36 : r * 0.44;
    return `<g transform="scale(${sc})" opacity="${clamp(p * 3)}"><defs><linearGradient id="${g}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></linearGradient></defs>
      ${D.shadow(w * 0.9, r * 1.02, 0.14)}<circle r="${r}" fill="#ffffff"/><circle r="${r * 0.9}" fill="url(#${g})"/>
      <circle r="${r * 0.8}" fill="none" stroke="#ffffff" stroke-width="${r * 0.025}" stroke-dasharray="${r * 0.05} ${r * 0.05}" opacity="0.55"/>
      <g transform="translate(0 ${-r * 0.3})">${glyph(k.glyph, r * 0.62)}</g>
      ${T(name, 0, r * 0.36, fs, { fill: "#ffffff", weight: 800 })}
      ${sub ? `<rect x="${-r * 1.1}" y="${r * 0.78}" width="${r * 2.2}" height="${r * 0.42}" rx="${r * 0.12}" fill="#ffffff" stroke="${c2}" stroke-width="${r * 0.04}"/>${T(sub, 0, r * 0.99, r * 0.24, { fill: c2, weight: 700 })}` : ""}</g>`;
  };

  // ------------------------------------------------------------- paper family: law, bond, licence, contract, bill, report
  // Documents, laws, bonds and certificates together appear in about 90 reference segments.
  const PAPERS = {
    law: { band: "#8e2b3a", tint: "#fbf3e6", icon: "scale" },
    bond: { band: "#1f8a5b", tint: "#eef8f1", icon: "coin" },
    licence: { band: "#2459a6", tint: "#eef3fb", icon: "columns" },
    contract: { band: "#4a5568", tint: "#f4f5f7", icon: "hands" },
    bill: { band: "#d9822b", tint: "#fdf3e7", icon: "factory" },
    report: { band: "#7b5cd6", tint: "#f3f0fc", icon: "chart" },
  };
  D.paper = ({ w = 240, kind = "law", title = "Act", year = "", value = "", note = "", lines = 4, stamp = "", stampColor = "#d6454f", p = 1, stampP = 1 } = {}) => {
    const k = PAPERS[kind] || PAPERS.law, h = w * 1.3, fold = w * 0.16, x0 = -w / 2, y0 = -h / 2;
    const rise = (1 - ease(p)) * h * 0.25;
    let body = "";
    if (kind === "bond") {
      body += `<rect x="${x0 + w * 0.07}" y="${y0 + h * 0.2}" width="${w * 0.86}" height="${h * 0.72}" rx="${w * 0.03}" fill="none" stroke="${k.band}" stroke-width="${w * 0.012}" stroke-dasharray="${w * 0.03} ${w * 0.015}"/>`;
    }
    const top = y0 + h * 0.27;
    if (year) body += T(year, 0, top + h * 0.06, w * 0.17, { fill: k.band, weight: 800 });
    if (value) body += T(value, 0, top + (year ? h * 0.2 : h * 0.08), w * 0.15, { fill: "#24242c", weight: 800 });
    const ly = top + (year || value ? h * (year && value ? 0.31 : 0.19) : h * 0.03);
    for (let i = 0; i < lines; i++) {
      const lw = w * (i === lines - 1 ? 0.45 : 0.72 - (i % 2) * 0.08);
      body += `<rect x="${-w * 0.36}" y="${ly + i * h * 0.075}" width="${lw}" height="${h * 0.026}" rx="${h * 0.013}" fill="#c9c6bd"/>`;
    }
    const sigY = note ? 0.7 : 0.86;
    if (kind === "contract") body += [-1, 1].map((s) => `<path d="M ${s * w * 0.22 - w * 0.14} ${y0 + h * sigY} q ${w * 0.05} ${-h * 0.05} ${w * 0.09} 0 t ${w * 0.1} 0" fill="none" stroke="#2d3748" stroke-width="${w * 0.012}"/><line x1="${s * w * 0.22 - w * 0.17}" y1="${y0 + h * (sigY + 0.03)}" x2="${s * w * 0.22 + w * 0.17}" y2="${y0 + h * (sigY + 0.03)}" stroke="#8a8f98" stroke-width="${w * 0.008}"/>`).join("");
    if (note) body += `<rect x="${-w * 0.42}" y="${y0 + h * 0.8}" width="${w * 0.84}" height="${h * 0.12}" rx="${h * 0.04}" fill="${k.band}"/>${T(note, 0, y0 + h * 0.86, w * 0.1, { fill: "#ffffff", weight: 700 })}`;
    let st = "";
    if (stamp) {
      const sp = ease(stampP), s = 1.7 - 0.7 * sp;
      st = `<g transform="translate(${w * 0.12} ${h * 0.22}) rotate(-14) scale(${s})" opacity="${clamp(stampP * 2.5) * 0.92}"><rect x="${-w * 0.36}" y="${-h * 0.07}" width="${w * 0.72}" height="${h * 0.14}" rx="${w * 0.03}" fill="none" stroke="${stampColor}" stroke-width="${w * 0.025}"/>${T(stamp, 0, 0, w * 0.12, { fill: stampColor, weight: 800 })}</g>`;
    }
    return `<g transform="translate(0 ${rise})" opacity="${clamp(p * 2)}"><ellipse cx="0" cy="${h * 0.51}" rx="${w * 0.46}" ry="${w * 0.05}" fill="#000" opacity="0.12"/>
      <path d="M ${x0} ${y0} L ${-x0 - fold} ${y0} L ${-x0} ${y0 + fold} L ${-x0} ${-y0} L ${x0} ${-y0} Z" fill="${k.tint}"/>
      <path d="M ${-x0 - fold} ${y0} L ${-x0 - fold} ${y0 + fold} L ${-x0} ${y0 + fold} Z" fill="#d9d3c6"/>
      <path d="M ${x0} ${y0} L ${-x0 - fold} ${y0} L ${-x0 - fold * 0.35} ${y0 + h * 0.17} L ${x0} ${y0 + h * 0.17} Z" fill="${k.band}"/>
      <g transform="translate(${x0 + w * 0.13} ${y0 + h * 0.085})">${glyph(k.icon, w * 0.13)}</g>
      ${T(title, w * 0.06, y0 + h * 0.085, title.length > 9 ? w * 0.09 : w * 0.11, { fill: "#ffffff", weight: 800 })}
      ${body}${st}</g>`;
  };

  // ------------------------------------------------------------- vault (reserves kept and locked)
  // CRR/SLR, forex reserves, capital buffers: "a part is kept aside, locked, earns nothing" shown as a place.
  D.vault = ({ w = 260, label = "", fill = 0.5, door = 0, locked = true, tag = "", tagColor = "#d6454f", metal = "gold", lockP = 1 } = {}) => {
    const h = w * 0.95, x0 = -w / 2, y0 = -h - w * 0.06, inset = w * 0.09, g = nid("v");
    const c = metal === "gold" ? ["#f3cf6a", "#c99a2e", "#8a6a1c"] : ["#c7ccd3", "#8e96a1", "#5a626d"];
    const ix = x0 + inset, iy = y0 + inset, iw = w - inset * 2, ih = h - inset * 2;
    const shelves = 3, per = 3, total = shelves * per, n = Math.round(clamp(fill) * total);
    let stack = "";
    for (let i = 0; i < n; i++) {
      const row = Math.floor(i / per), col = i % per, bw = iw / per * 0.82;
      const bx = ix + (col + 0.5) * (iw / per), by = iy + ih - (row + 0.5) * (ih / shelves);
      stack += `<g transform="translate(${bx} ${by}) scale(${bw / 300})">${D.noteBundle({ w: 300, value: 500 })}</g>`;
    }
    const shelfLines = Array.from({ length: shelves - 1 }, (_, i) => `<rect x="${ix}" y="${iy + ((i + 1) * ih) / shelves - 3}" width="${iw}" height="6" fill="${c[2]}" opacity="0.5"/>`).join("");
    const d = ease(door), dw = w - inset * 0.6;
    const doorPanel = `<g transform="translate(${x0 + inset * 0.3} 0) scale(${1 - d * 0.88} 1)"><rect x="0" y="${y0 + inset * 0.3}" width="${dw}" height="${h - inset * 0.6}" rx="${w * 0.04}" fill="url(#${g})"/>
      <circle cx="${dw * 0.5}" cy="${y0 + h * 0.5}" r="${w * 0.16}" fill="none" stroke="${c[2]}" stroke-width="${w * 0.03}"/>
      ${[0, 60, 120].map((a) => `<line x1="${dw * 0.5 - Math.cos((a * Math.PI) / 180) * w * 0.15}" y1="${y0 + h * 0.5 - Math.sin((a * Math.PI) / 180) * w * 0.15}" x2="${dw * 0.5 + Math.cos((a * Math.PI) / 180) * w * 0.15}" y2="${y0 + h * 0.5 + Math.sin((a * Math.PI) / 180) * w * 0.15}" stroke="${c[2]}" stroke-width="${w * 0.025}" stroke-linecap="round"/>`).join("")}
      <circle cx="${dw * 0.5}" cy="${y0 + h * 0.5}" r="${w * 0.045}" fill="${c[2]}"/>
      ${[0.2, 0.8].map((f) => `<rect x="${-w * 0.015}" y="${y0 + h * f - w * 0.05}" width="${w * 0.05}" height="${w * 0.1}" rx="${w * 0.015}" fill="${c[2]}"/>`).join("")}</g>`;
    const lk = ease(lockP), shackle = locked ? 0 : w * 0.05;
    const lock = `<g transform="translate(${-x0 - w * 0.02} ${y0 + w * 0.02}) scale(${0.4 + 0.6 * lk})" opacity="${clamp(lockP * 2)}"><path d="M ${-w * 0.07} 0 L ${-w * 0.07} ${-w * 0.07 - shackle} A ${w * 0.07} ${w * 0.07} 0 0 1 ${w * 0.07} ${-w * 0.07 - shackle} L ${w * 0.07} ${locked ? 0 : -shackle}" fill="none" stroke="#4a5568" stroke-width="${w * 0.03}"/><rect x="${-w * 0.11}" y="0" width="${w * 0.22}" height="${w * 0.17}" rx="${w * 0.03}" fill="${locked ? "#2d3748" : "#2fa35b"}"/><circle cy="${w * 0.08}" r="${w * 0.025}" fill="#ffffff"/></g>`;
    return `<g><defs><linearGradient id="${g}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${c[0]}"/><stop offset="1" stop-color="${c[1]}"/></linearGradient></defs>
      <ellipse cx="0" cy="0" rx="${w * 0.6}" ry="${w * 0.06}" fill="#000" opacity="0.13"/>
      <rect x="${x0 + w * 0.08}" y="${-w * 0.08}" width="${w * 0.12}" height="${w * 0.08}" fill="${c[2]}"/><rect x="${-x0 - w * 0.2}" y="${-w * 0.08}" width="${w * 0.12}" height="${w * 0.08}" fill="${c[2]}"/>
      <rect x="${x0}" y="${y0}" width="${w}" height="${h}" rx="${w * 0.06}" fill="${c[1]}"/>
      <rect x="${ix}" y="${iy}" width="${iw}" height="${ih}" rx="${w * 0.03}" fill="#3b3326"/>${shelfLines}${stack}
      ${d < 0.5 ? doorPanel : ""}
      ${d >= 0.5 ? `<path d="M ${x0 + inset * 0.3} ${y0 + inset * 0.3} L ${x0 + inset * 0.3 - w * 0.3 * d} ${y0 - h * 0.04 * d} L ${x0 + inset * 0.3 - w * 0.3 * d} ${y0 + h + h * 0.04 * d - inset * 0.3} L ${x0 + inset * 0.3} ${y0 + h - inset * 0.3} Z" fill="url(#${g})" stroke="${c[2]}" stroke-width="2"/><ellipse cx="${x0 + inset * 0.3 - w * 0.15 * d}" cy="${y0 + h * 0.5}" rx="${w * 0.05 * d}" ry="${w * 0.15}" fill="none" stroke="${c[2]}" stroke-width="${w * 0.025}"/>` : ""}
      ${label ? `<rect x="${-w * 0.3}" y="${y0 - w * 0.2}" width="${w * 0.6}" height="${w * 0.17}" rx="${w * 0.05}" fill="#2d3748"/>${T(label, 0, y0 - w * 0.115, w * 0.11, { fill: "#ffffff", weight: 800 })}` : ""}
      ${lock}
      ${tag ? `<g transform="translate(${-x0 + w * 0.02} ${y0 + h * 0.55})"><line x1="0" y1="0" x2="${w * 0.12}" y2="${w * 0.08}" stroke="#8a8f98" stroke-width="3"/><rect x="${w * 0.1}" y="${w * 0.03}" width="${w * 0.52}" height="${w * 0.17}" rx="${w * 0.05}" fill="${tagColor}"/>${T(tag, w * 0.36, w * 0.115, w * 0.085, { fill: "#ffffff", weight: 800 })}</g>` : ""}</g>`;
  };

  // ------------------------------------------------------------- crowd with a share (who is reached, who is left out)
  const SKIN = ["#c68a5c", "#d39a6a", "#b97c50", "#a8714a", "#d8a274", "#c98c5e"];
  const SHIRT = ["#3a7bd5", "#e5484d", "#2fa35b", "#f29f05", "#7b61ff", "#e2558f", "#2a9d8f", "#9b6b43"];
  function mini(x, y, s, i, dim) {
    const sk = SKIN[(i * 7) % SKIN.length], sh = SHIRT[(i * 5 + 3) % SHIRT.length], op = dim ? 0.3 : 1, woman = (i * 11) % 3 === 0;
    return `<g transform="translate(${x} ${y})" opacity="${op}"><path d="M ${-s * 0.3} 0 L ${-s * 0.3} ${-s * 0.55} Q ${-s * 0.3} ${-s * 0.82} 0 ${-s * 0.82} Q ${s * 0.3} ${-s * 0.82} ${s * 0.3} ${-s * 0.55} L ${s * 0.3} 0 Z" fill="${sh}"/>
      <circle cy="${-s * 1.0}" r="${s * 0.2}" fill="${sk}"/><path d="M ${-s * 0.2} ${-s * 1.03} Q 0 ${-s * 1.3} ${s * 0.2} ${-s * 1.03} Q ${s * 0.1} ${-s * 1.12} 0 ${-s * 1.12} Q ${-s * 0.1} ${-s * 1.12} ${-s * 0.2} ${-s * 1.03} Z" fill="#1f1a17"/>${woman ? `<circle cx="${s * 0.17}" cy="${-s * 1.12}" r="${s * 0.08}" fill="#1f1a17"/>` : ""}</g>`;
  }
  D.crowd = ({ w = 600, n = 30, cols = 10, share = 0, shareColor = "#f2c94c", shareLabel = "", restColor = "", restLabel = "", label = "", dimRest = false, p = 1 } = {}) => {
    const rows = Math.ceil(n / cols), s = (w / cols) * 0.95, rowH = s * 1.25, H = rows * rowH + s * 0.4;
    const sp = ease(p), cut = Math.round(clamp(share) * cols * sp), fs = Math.max(26, s * 0.5);
    let shade = "";
    if (share > 0 && cut > 0) shade += `<rect x="${-w / 2 - s * 0.12}" y="${-H}" width="${(cut * w) / cols + s * 0.24}" height="${H + s * 0.15}" rx="${s * 0.3}" fill="${shareColor}" opacity="0.55"/>`;
    if (restColor && cut < cols) shade += `<rect x="${-w / 2 + (cut * w) / cols - s * 0.05}" y="${-H}" width="${w - (cut * w) / cols + s * 0.17}" height="${H + s * 0.15}" rx="${s * 0.3}" fill="${restColor}" opacity="0.35"/>`;
    let ppl = "";
    for (let i = 0; i < n; i++) {
      const r = Math.floor(i / cols), c = i % cols;
      ppl += mini(-w / 2 + (c + 0.5) * (w / cols), -(rows - 1 - r) * rowH - s * 0.08, s * 0.78, i, dimRest && c >= cut);
    }
    const labels = (shareLabel && cut > 0 ? T(shareLabel, -w / 2 + (cut * w) / cols / 2, -H - fs * 0.7, fs, { fill: "#6b4a00" }) : "")
      + (restLabel && cut < cols ? T(restLabel, -w / 2 + (cut * w) / cols + (w - (cut * w) / cols) / 2, -H - fs * 0.7, fs, { fill: "#8a1c24" }) : "")
      + (label ? T(label, 0, s * 0.3 + fs * 0.8, fs * 1.1, { fill: "#2b2b33" }) : "");
    return `<g><ellipse cx="0" cy="${s * 0.05}" rx="${w * 0.52}" ry="${s * 0.18}" fill="#000" opacity="0.1"/>${shade}${ppl}${labels}</g>`;
  };

  // ------------------------------------------------------------- central bank building (generic; no emblem)
  D.centralBank = ({ w = 420, label = "RBI" } = {}) => {
    const h = w * 0.82, g = nid("c");
    const cols = Array.from({ length: 6 }, (_, i) => `<rect x="${-w * 0.4 + i * w * 0.15}" y="${-h * 0.6}" width="${w * 0.07}" height="${h * 0.44}" fill="url(#${g})"/>`).join("");
    return `<g><defs><linearGradient id="${g}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#f7f4ee"/><stop offset="1" stop-color="#d8d1c2"/></linearGradient></defs>
      ${D.shadow(w * 1.08)}
      <rect x="${-w * 0.54}" y="${-h * 0.08}" width="${w * 1.08}" height="${h * 0.08}" fill="#bdb5a4"/><rect x="${-w * 0.5}" y="${-h * 0.16}" width="${w}" height="${h * 0.08}" fill="#cfc8b8"/>
      ${cols}
      <rect x="${-w * 0.47}" y="${-h * 0.67}" width="${w * 0.94}" height="${h * 0.07}" fill="#0f6e6e"/>
      <path d="M ${-w * 0.52} ${-h * 0.67} L 0 ${-h * 0.98} L ${w * 0.52} ${-h * 0.67} Z" fill="#ece6da"/>
      <circle cy="${-h * 0.79}" r="${h * 0.09}" fill="#f3cf6a" stroke="#c99a2e" stroke-width="${h * 0.015}"/>${T("₹", 0, -h * 0.785, h * 0.11, { fill: "#8a6a1c", weight: 800 })}
      <g transform="translate(0 ${-h * 0.31})"><rect x="${-w * 0.1}" y="${-h * 0.14}" width="${w * 0.2}" height="${h * 0.3}" rx="${w * 0.02}" fill="#8e96a1"/><circle r="${w * 0.05}" fill="none" stroke="#4a5568" stroke-width="${w * 0.012}"/><circle r="${w * 0.012}" fill="#4a5568"/></g>
      <rect x="${-w * 0.2}" y="${-h * 1.13}" width="${w * 0.4}" height="${h * 0.13}" rx="10" fill="#0f6e6e"/>${T(label, 0, -h * 1.065, h * 0.09, { fill: "#ffffff" })}</g>`;
  };

  // ------------------------------------------------------------- disc tag (risk, fail, fixed, new)
  D.disc = ({ w = 130, text = "RISK", color = "#d6454f", ring = true, p = 1 } = {}) => {
    const r = w / 2, sc = 0.5 + 0.5 * ease(p);
    return `<g transform="scale(${sc})" opacity="${clamp(p * 3)}">${D.shadow(w * 0.8, r * 1.05, 0.12)}<circle r="${r}" fill="${color}"/>${ring ? `<circle r="${r * 0.84}" fill="none" stroke="#ffffff" stroke-width="${r * 0.05}" opacity="0.8"/>` : ""}${T(text, 0, 0, text.length > 4 ? r * 0.4 : r * 0.5, { fill: "#ffffff", weight: 800 })}</g>`;
  };
  // ------------------------------------------------------------- committee at a table (MPC, Basel Committee, reform committees)
  D.committee = ({ w = 520, n = 6, name = "समिति", sub = "", color = "#0f6e6e", p = 1 } = {}) => {
    const s = Math.min((w / n) * 0.8, w * 0.17), top = -s * 0.85, sp = ease(p), fs = Math.max(26, s * 0.3), ph = fs * 1.5;
    let ppl = "";
    for (let i = 0; i < n; i++) {
      const x = -w / 2 + (i + 0.5) * (w / n), show = clamp(sp * n - i);
      ppl += `<g opacity="${show}" transform="translate(0 ${(1 - show) * s * 0.2})">${mini(x, top + s * 0.3, s * 1.05, i + 3, false)}</g>`;
    }
    const plateW = Math.max(w * 0.4, name.length * fs * 0.62 + fs);
    return `<g><ellipse cx="0" cy="0" rx="${w * 0.56}" ry="${s * 0.16}" fill="#000" opacity="0.12"/>${ppl}
      <rect x="${-w * 0.54}" y="${top}" width="${w * 1.08}" height="${s * 0.18}" rx="${s * 0.06}" fill="#8a5d2e"/>
      <rect x="${-w * 0.5}" y="${top + s * 0.16}" width="${w}" height="${-top - s * 0.16}" fill="#a8763f"/>
      <rect x="${-plateW / 2}" y="${top + s * 0.16 + (-top - s * 0.16 - ph) / 2}" width="${plateW}" height="${ph}" rx="${ph * 0.25}" fill="${color}"/>${T(name, 0, top + s * 0.16 + (-top - s * 0.16) / 2, fs, { fill: "#ffffff", weight: 800 })}
      ${sub ? T(sub, 0, fs * 0.9, fs * 0.9, { fill: "#2b2b33", weight: 700 }) : ""}</g>`;
  };

  // ------------------------------------------------------------- money bag (size from tiny to huge; no currency sign of any country but ₹ if asked)
  D.moneyBag = ({ w = 160, label = "", sign = "₹", color = "#c9965a", p = 1 } = {}) => {
    const h = w * 1.1, sc = 0.4 + 0.6 * ease(p), g = nid("m");
    return `<g transform="scale(${sc})"><defs><radialGradient id="${g}" cx="0.4" cy="0.35" r="0.75"><stop offset="0" stop-color="#e2b57a"/><stop offset="1" stop-color="${color}"/></radialGradient></defs>
      <ellipse cx="0" cy="0" rx="${w * 0.5}" ry="${w * 0.07}" fill="#000" opacity="0.14"/>
      <path d="M ${-w * 0.16} ${-h * 0.78} Q ${-w * 0.52} ${-h * 0.55} ${-w * 0.48} ${-h * 0.22} Q ${-w * 0.44} 0 0 0 Q ${w * 0.44} 0 ${w * 0.48} ${-h * 0.22} Q ${w * 0.52} ${-h * 0.55} ${w * 0.16} ${-h * 0.78} Z" fill="url(#${g})"/>
      <path d="M ${-w * 0.16} ${-h * 0.78} L ${-w * 0.26} ${-h * 0.95} Q 0 ${-h * 0.86} ${w * 0.26} ${-h * 0.95} L ${w * 0.16} ${-h * 0.78} Z" fill="${color}"/>
      <rect x="${-w * 0.2}" y="${-h * 0.81}" width="${w * 0.4}" height="${h * 0.06}" rx="${h * 0.03}" fill="#7d5427"/>
      ${sign ? T(sign, 0, -h * 0.36, w * 0.42, { fill: "#6b4a22", weight: 800 }) : ""}
      ${label ? `<rect x="${-w * 0.42}" y="${-h * 0.16}" width="${w * 0.84}" height="${h * 0.14}" rx="${h * 0.05}" fill="#f7efe0"/>${T(label, 0, -h * 0.09, w * 0.13, { fill: "#6b4a22" })}` : ""}</g>`;
  };
})();
