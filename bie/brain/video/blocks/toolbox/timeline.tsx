// timeline_build (Task 046a, batch 3): events placed on a D3 time scale, the axis drawn first and then each event
// dropping in on its date in turn (above and below the axis by turns, two heights, so neighbours never cover each other),
// with optional era bands behind.
import React from "react";
import { scaleTime, timeYear } from "d3";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, useRel } from "./common";

type Event = { date: string; label: string; detail?: string };
type Era = { from: string; to: string; label: string; colour?: string };

const Timeline: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const events = (data.events as Event[]).slice().sort((a, b) => a.date.localeCompare(b.date));
  const x = scaleTime().domain([new Date(data.start), new Date(data.end)]).range([110, width - 110]);
  const axisY = height * 0.56;
  const grow = ramp(rel, 0, 0.6 * fps);
  const first = (data.first_at ?? 0.6) * fps, gap = ((data.seconds ?? 3.2) * fps) / Math.max(1, events.length);
  const years = timeYear.every(data.tick_years ?? 10)!.range(new Date(data.start), new Date(data.end));
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {((data.eras || []) as Era[]).map((e, i) => {
          const x0 = x(new Date(e.from)), x1 = x(new Date(e.to));
          return <g key={e.label} opacity={0.9 * ramp(rel, 0.3 * fps, 12)}>
            <rect x={x0} y={axisY - 300} width={x1 - x0} height={600} fill={e.colour || (i % 2 ? "#12303f" : "#0f2836")} />
            <text x={(x0 + x1) / 2} y={height - 40} fill={C.muted} fontSize={22} textAnchor="middle">{e.label}</text>
          </g>;
        })}
        <line x1={x.range()[0]} x2={x.range()[0] + (x.range()[1] - x.range()[0]) * grow} y1={axisY} y2={axisY} stroke={C.ink} strokeWidth={4} />
        {years.map((y) => {
          const px = x(y);
          const shown = px <= x.range()[0] + (x.range()[1] - x.range()[0]) * grow;
          return shown ? <g key={+y}>
            <line x1={px} x2={px} y1={axisY - 8} y2={axisY + 8} stroke={C.ink} strokeWidth={2} />
            <text x={px} y={axisY + 36} fill={C.muted} fontSize={22} textAnchor="middle">{y.getFullYear()}</text>
          </g> : null;
        })}
        {events.map((e, i) => {
          const start = first + i * gap;
          const o = ramp(rel, start, 10);
          if (o <= 0) return null;
          const px = x(new Date(e.date));
          const up = i % 2 === 0, level = Math.floor(i / 2) % 2;
          const len = (level ? 200 : 110) * ramp(rel, start, 12);
          const y2 = up ? axisY - len : axisY + len;
          const now = rel >= start && rel < start + gap;
          return <g key={e.date + e.label} opacity={o}>
            <line x1={px} x2={px} y1={axisY} y2={y2} stroke={now ? C.warm : C.accent} strokeWidth={3} />
            <circle cx={px} cy={axisY} r={now ? 12 : 9} fill={now ? C.warm : C.accent} stroke={C.bg0} strokeWidth={3} />
            <foreignObject x={px - 140} y={up ? y2 - 104 : y2 + 4} width={280} height={100}>
              <div style={{ fontFamily: FONT, color: C.ink, textAlign: "center", background: now ? "rgba(255,179,92,0.18)" : C.panel,
                border: `2px solid ${now ? C.warm : "rgba(255,255,255,0.12)"}`, borderRadius: 12, padding: "6px 8px", height: 88, boxSizing: "border-box" }}>
                <div style={{ fontSize: 26, fontWeight: 800, color: now ? C.warm : C.accent }}>{e.date.slice(0, 4)}</div>
                <div style={{ fontSize: 20, lineHeight: 1.15 }}>{e.label}</div>
              </div>
            </foreignObject>
          </g>;
        })}
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 40, top: 30 }} /> : null}
    </div>
  );
};

registerBlock("timeline_build", Timeline);
