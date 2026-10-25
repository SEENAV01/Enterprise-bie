// Diagram blocks (Task 046a, batch 3):
// - mermaid_build: a Mermaid diagram (Mermaid's own text, laid out by elkjs through @mermaid-js/layout-elk), rendered
//   once to SVG and then revealed node by node in the given order; an edge appears with the later of its two ends.
// - flow_build: BIE's own flowchart (flowchart, procedure, decision), laid out by dagre; steps, decisions and ends
//   are drawn by BIE so a step can carry its source (for law: the section number from India Code). layout "cycle" puts
//   the steps on a ring with arrows round it and a token travelling the cycle (process_cycle).
// - tree_build: a hierarchy grown level by level with D3's tree layout (tree_hierarchy).
import React from "react";
import mermaid from "mermaid";
import elkLayouts from "@mermaid-js/layout-elk";
import dagre from "@dagrejs/dagre";
import { curveBasis, hierarchy, line, tree } from "d3";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, useAsset, useRel } from "./common";

let mermaidReady = false;
function setupMermaid() {
  if (mermaidReady) return;
  mermaid.registerLayoutLoaders(elkLayouts);
  mermaid.initialize({
    startOnLoad: false, theme: "base", securityLevel: "strict", layout: "elk", fontFamily: FONT,
    themeVariables: { background: C.bg0, primaryColor: "#123a4a", primaryTextColor: C.ink, primaryBorderColor: C.accent,
      lineColor: "#9fb3bf", secondaryColor: "#3a2a12", tertiaryColor: "#0b2433", fontSize: "26px", edgeLabelBackground: "#0b2433" },
    flowchart: { htmlLabels: true, padding: 18, nodeSpacing: 40, rankSpacing: 50 },
  });
  mermaidReady = true;
}

const MermaidBuild: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const key = `mermaid:${data.source}`;
  const svg = useAsset(key, async () => {
    setupMermaid();
    const id = "bie-mmd-" + Math.abs([...String(data.source)].reduce((h, c) => (h * 31 + c.charCodeAt(0)) | 0, 7));
    return (await mermaid.render(id, data.source)).svg as string;
  });
  const order = data.order as string[];
  const first = (data.first_at ?? 0.4) * fps, gap = ((data.seconds ?? 3.0) * fps) / Math.max(1, order.length);
  const shown = (id: string) => { const i = order.indexOf(id); return i < 0 ? 1 : ramp(rel, first + i * gap, 10); };
  const edges = (data.edges as [string, string][]) || [];
  // CSS per frame: every node and edge hidden, then each one's opacity from its turn in the order. Mermaid names a node
  // "<svg id>-flowchart-<node id>-<n>" and marks an edge with data-id "L_<from>_<to>_<n>"; its own max-width is lifted so the
  // diagram fills the block.
  const node = (id: string) => `.bie-mmd g.node[id*="-flowchart-${id}-"]`;
  const css = [`.bie-mmd svg{width:100% !important;height:100% !important;max-width:none !important}`,
    `.bie-mmd g.node, .bie-mmd .flowchart-link, .bie-mmd .edgeLabel{opacity:0}`,
    ...order.map((id) => `${node(id)}{opacity:${shown(id).toFixed(3)}}` +
      (rel >= first + order.indexOf(id) * gap && rel < first + (order.indexOf(id) + 1) * gap
        ? `${node(id)} rect, ${node(id)} polygon, ${node(id)} path{stroke:${C.warm} !important;stroke-width:4px !important}` : "")),
    ...edges.map(([a, b]) => {
      const o = Math.min(shown(a), shown(b)).toFixed(3);
      return `.bie-mmd [data-id^="L_${a}_${b}_"]{opacity:${o}} .bie-mmd .edgeLabel:has([data-id^="L_${a}_${b}_"]){opacity:${o}}`;
    })].join("\n");
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <style>{css}</style>
      {svg ? <div className="bie-mmd" style={{ position: "absolute", left: 60, right: 60, top: 130, bottom: 40 }}
        dangerouslySetInnerHTML={{ __html: svg }} /> : null}
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 40, bottom: 30 }} /> : null}
    </div>
  );
};

// ---------------------------------------------------------------- BIE's flowchart (dagre) and cycle

type FNode = { id: string; label: string; kind?: "step" | "decision" | "end" | "start"; section?: string; note?: string };
type FEdge = { from: string; to: string; label?: string };

function wrap(text: string, max: number): string[] {
  const out: string[] = [];
  for (const word of text.split(/\s+/)) {
    const last = out[out.length - 1];
    if (last && (last + " " + word).length <= max) out[out.length - 1] = last + " " + word; else out.push(word);
  }
  return out;
}

function nodeSize(n: FNode, chars: number) {
  const lines = wrap(n.label, chars);
  const w = Math.max(...lines.map((l) => l.length)) * 14.5 + 56;
  const h = lines.length * 32 + 30 + (n.section ? 30 : 0);
  return n.kind === "decision" ? { w: w * 1.45, h: h * 1.5, lines } : { w, h, lines };
}

const Shape: React.FC<{ n: FNode; x: number; y: number; w: number; h: number; lines: string[]; o: number; now: boolean; sectionPrefix: string }> =
  ({ n, x, y, w, h, lines, o, now, sectionPrefix }) => {
    const stroke = now ? C.warm : n.kind === "end" ? "#c79bff" : C.accent;
    const fill = n.kind === "end" ? "#24183a" : n.kind === "decision" ? "#3a2a12" : "#123a4a";
    const top = y - (lines.length * 32 + (n.section ? 30 : 0)) / 2 + 24;
    return (
      <g opacity={o} transform={`translate(${x},${y}) scale(${0.85 + 0.15 * o}) translate(${-x},${-y})`}>
        {n.kind === "decision"
          ? <polygon points={`${x},${y - h / 2} ${x + w / 2},${y} ${x},${y + h / 2} ${x - w / 2},${y}`} fill={fill} stroke={stroke} strokeWidth={now ? 5 : 3} />
          : <rect x={x - w / 2} y={y - h / 2} width={w} height={h} rx={n.kind === "end" || n.kind === "start" ? h / 2 : 14} fill={fill} stroke={stroke} strokeWidth={now ? 5 : 3} />}
        {n.section ? <text x={x} y={top} fill={C.warm} fontSize={22} fontWeight={800} textAnchor="middle">{`${sectionPrefix}${n.section}`}</text> : null}
        {lines.map((l, i) => <text key={i} x={x} y={top + (n.section ? 30 : 0) + i * 32} fill={C.ink} fontSize={25} fontWeight={600} textAnchor="middle">{l}</text>)}
      </g>
    );
  };

const FlowBuild: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const nodes = data.nodes as FNode[], edges = data.edges as FEdge[];
  const order: string[] = data.order || nodes.map((n) => n.id);
  const first = (data.first_at ?? 0.4) * fps, gap = ((data.seconds ?? 3.0) * fps) / Math.max(1, order.length);
  const turn = (id: string) => first + Math.max(0, order.indexOf(id)) * gap;
  const shown = (id: string) => ramp(rel, turn(id), 10);
  const isNow = (id: string) => rel >= turn(id) && rel < turn(id) + gap;
  const box = { x: 40, y: 130, w: width - 80 - (data.panel_width ?? 0), h: height - 170 };
  const chars = data.wrap ?? 22;
  const sizes = new Map(nodes.map((n) => [n.id, nodeSize(n, chars)]));
  const pos = new Map<string, { x: number; y: number }>();
  let routes: { e: FEdge; pts: [number, number][]; lx?: number; ly?: number }[] = [];
  let transform = "";                                     // dagre's drawing is scaled as a whole, text and all
  if (data.layout === "cycle") {
    const R = Math.min(box.w, box.h) / 2 - 110, cx = box.x + box.w / 2, cy = box.y + box.h / 2;
    nodes.forEach((n, i) => { const a = -Math.PI / 2 + (2 * Math.PI * i) / nodes.length; pos.set(n.id, { x: cx + R * Math.cos(a), y: cy + R * Math.sin(a) }); });
    routes = nodes.map((n, i) => {
      const a0 = -Math.PI / 2 + (2 * Math.PI * i) / nodes.length, a1 = a0 + (2 * Math.PI) / nodes.length;
      const pts: [number, number][] = [];
      for (let s = 0; s <= 16; s++) { const a = a0 + 0.32 + ((a1 - a0 - 0.64) * s) / 16; pts.push([cx + R * Math.cos(a), cy + R * Math.sin(a)]); }
      return { e: { from: n.id, to: nodes[(i + 1) % nodes.length].id }, pts };
    });
  } else {
    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: data.rankdir || "TB", nodesep: 46, ranksep: data.ranksep ?? 58, edgesep: 20, marginx: 10, marginy: 10 });
    g.setDefaultEdgeLabel(() => ({}));
    nodes.forEach((n) => { const s = sizes.get(n.id)!; g.setNode(n.id, { width: s.w, height: s.h }); });
    edges.forEach((e) => g.setEdge(e.from, e.to, e.label ? { label: e.label, width: e.label.length * 14 + 20, height: 30, labelpos: "c" } : {}));
    dagre.layout(g);
    const gw = g.graph().width || 1, gh = g.graph().height || 1;
    const scale = Math.min(1.25, box.w / gw, box.h / gh);
    transform = `translate(${box.x + (box.w - gw * scale) / 2},${box.y + (box.h - gh * scale) / 2}) scale(${scale})`;
    nodes.forEach((n) => { const v = g.node(n.id); pos.set(n.id, { x: v.x, y: v.y }); });
    routes = edges.map((e) => {
      const ed = g.edge(e.from, e.to) as any;
      return { e, pts: (ed.points as { x: number; y: number }[]).map((p) => [p.x, p.y] as [number, number]), lx: ed.x, ly: ed.y };
    });
  }
  const curve = line().curve(curveBasis);
  const done = order.every((id) => rel >= turn(id) + 10);
  // the token that travels a finished cycle
  let token: [number, number] | null = null;
  if (data.layout === "cycle" && done) {
    const all = routes.flatMap((r) => r.pts);
    const t = ((rel - (turn(order[order.length - 1]) + 10)) / (fps * 1.6)) % 1;
    token = all[Math.floor(t * (all.length - 1))];
  }
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <defs><marker id="flowhead" viewBox="0 0 10 10" refX={9} refY={5} markerWidth={7} markerHeight={7} orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#9fb3bf" /></marker></defs>
        <g transform={transform}>
          {routes.map((r, i) => {
            const o = Math.min(shown(r.e.from), shown(r.e.to));
            if (o <= 0) return null;
            const d = curve(r.pts) || "";
            return <g key={i} opacity={o}>
              <path d={d} fill="none" stroke="#9fb3bf" strokeWidth={3.5} markerEnd="url(#flowhead)" />
              {r.e.label && r.lx !== undefined ? <g><rect x={r.lx - r.e.label.length * 7 - 10} y={(r.ly as number) - 18} width={r.e.label.length * 14 + 20} height={34} rx={8} fill={C.bg0} />
                <text x={r.lx} y={(r.ly as number) + 8} fill={C.warm} fontSize={24} fontWeight={800} textAnchor="middle">{r.e.label}</text></g> : null}
            </g>;
          })}
          {nodes.map((n) => {
            const p = pos.get(n.id)!, s = sizes.get(n.id)!;
            return <Shape key={n.id} n={n} x={p.x} y={p.y} w={s.w} h={s.h} lines={s.lines} o={shown(n.id)} now={isNow(n.id)}
              sectionPrefix={data.section_prefix ?? "§ "} />;
          })}
          {token ? <circle cx={token[0]} cy={token[1]} r={14} fill={C.warm} /> : null}
          {data.layout === "cycle" && data.centre ? <text x={box.x + box.w / 2} y={box.y + box.h / 2 + 12} fill={C.muted} fontSize={34} fontWeight={800}
            textAnchor="middle" opacity={ramp(rel, turn(order[order.length - 1]), 12)}>{data.centre}</text> : null}
        </g>
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      {data.panel ? <div style={{ position: "absolute", right: 40, top: 150, width: (data.panel_width ?? 0) - 30, color: C.ink, fontSize: 24,
        background: C.panel, borderRadius: 14, padding: "14px 18px", lineHeight: 1.3, boxSizing: "border-box" }}>
        {data.panel_title ? <div style={{ color: C.muted, fontSize: 22, marginBottom: 10 }}>{data.panel_title}</div> : null}
        {(data.panel as { node: string; text: string; tag?: string }[]).map((l) =>
          <div key={l.node} style={{ marginBottom: 10, opacity: shown(l.node), color: isNow(l.node) ? C.warm : C.ink }}>
            {l.tag ? <b style={{ color: C.warm, marginRight: 10 }}>{l.tag}</b> : null}{l.text}</div>)}</div> : null}
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", left: 40, bottom: 24 }} /> : null}
    </div>
  );
};

// ---------------------------------------------------------------- tree (D3 hierarchy)

type TNode = { name: string; note?: string; children?: TNode[] };

const TreeBuild: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const root = hierarchy<TNode>(data.root);
  const depth = root.height + 1;
  const box = { x: 90, y: 180, w: width - 180, h: height - 300 };
  tree<TNode>().size([box.w, box.h]).separation((a, b) => (a.parent === b.parent ? 1 : 1.3))(root);
  const per = ((data.seconds ?? 3.0) * fps) / depth, first = (data.first_at ?? 0.3) * fps;
  const o = (d: number) => ramp(rel, first + d * per, 12);
  const P = (n: any) => [box.x + n.x, box.y + n.y] as [number, number];
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {root.links().map((l, i) => {
          const [x0, y0] = P(l.source), [x1, y1] = P(l.target);
          const ym = (y0 + y1) / 2;
          return <path key={i} d={`M${x0},${y0} C${x0},${ym} ${x1},${ym} ${x1},${y1}`} fill="none" stroke="#9fb3bf" strokeWidth={3}
            opacity={o(l.target.depth)} />;
        })}
        {root.descendants().map((n, i) => {
          const [x, y] = P(n);
          const lines = wrap(n.data.name, data.wrap ?? 18);
          const w = Math.max(...lines.map((l) => l.length), (n.data.note || "").length * 0.85) * 14 + 40, h = lines.length * 30 + 22 + (n.data.note ? 26 : 0);
          return <g key={i} opacity={o(n.depth)}>
            <rect x={x - w / 2} y={y - h / 2} width={w} height={h} rx={12} fill={n.depth === 0 ? "#3a2a12" : "#123a4a"}
              stroke={n.depth === 0 ? C.warm : C.accent} strokeWidth={3} />
            {lines.map((l, k) => <text key={k} x={x} y={y - h / 2 + 34 + k * 30} fill={C.ink} fontSize={24} fontWeight={700} textAnchor="middle">{l}</text>)}
            {n.data.note ? <text x={x} y={y + h / 2 - 12} fill={C.warm} fontSize={20} fontWeight={700} textAnchor="middle">{n.data.note}</text> : null}
          </g>;
        })}
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", left: 40, bottom: 24 }} /> : null}
    </div>
  );
};

registerBlock("mermaid_build", MermaidBuild);
registerBlock("flow_build", FlowBuild);
registerBlock("tree_build", TreeBuild);
