// network_graph (Task 046a): nodes and links laid out by NetworkX, drawn with D3 scales; a traversal (BFS order from
// NetworkX) lights the nodes one by one and the queue fills at the bottom.
import React from "react";
import { scaleLinear } from "d3";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, useRel } from "./common";

const NetworkGraph: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const pad = { l: 120, r: 120, t: 130, b: 150 };
  const sx = scaleLinear().domain([0, 1]).range([pad.l, width - pad.r]);
  const sy = scaleLinear().domain([0, 1]).range([pad.t, height - pad.b]);
  const pos = Object.fromEntries((data.nodes as any[]).map((n) => [n.id, n]));
  const appear = ramp(rel, 0, 20);
  const every = (data.step_seconds ?? 0.45) * fps;
  const start = 0.8 * fps;
  const visitedAt = Object.fromEntries((data.order as string[]).map((id, i) => [id, start + i * every]));
  const tree = new Set((data.tree_edges as string[][]).map(([a, b]) => `${a}|${b}`));
  const visited = (data.order as string[]).filter((id) => rel >= visitedAt[id]);
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {(data.edges as string[][]).map(([a, b], i) => {
          const onTree = tree.has(`${a}|${b}`) || tree.has(`${b}|${a}`);
          const lit = onTree && rel >= Math.max(visitedAt[a], visitedAt[b]);
          return <line key={i} x1={sx(pos[a].x)} y1={sy(pos[a].y)} x2={sx(pos[b].x)} y2={sy(pos[b].y)}
            stroke={lit ? C.warm : C.ink} strokeOpacity={lit ? 1 : 0.35 * appear} strokeWidth={lit ? 7 : 4} />;
        })}
        {(data.nodes as any[]).map((n) => {
          const on = ramp(rel, visitedAt[n.id] ?? 1e9, 8);
          return <g key={n.id} opacity={appear}>
            <circle cx={sx(n.x)} cy={sy(n.y)} r={38 + 6 * on} fill={on > 0 ? C.accent : C.panel} stroke={C.accent} strokeWidth={5}
              style={on > 0 ? { filter: `drop-shadow(0 0 14px ${C.accent})` } : undefined} />
            <text x={sx(n.x)} y={sy(n.y) + 12} fill={on > 0 ? C.bg0 : C.ink} fontSize={34} fontWeight={800} textAnchor="middle">{n.id}</text>
          </g>;
        })}
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      <div style={{ position: "absolute", left: pad.l, bottom: 40, display: "flex", gap: 12, alignItems: "center", color: C.muted, fontSize: 28 }}>
        <span>{data.order_label || "visit order"}:</span>
        {visited.map((id) => <Badge key={id} text={id} />)}
      </div>
    </div>
  );
};

registerBlock("network_graph", NetworkGraph);
