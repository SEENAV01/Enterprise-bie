// flight_profile (Task 046a, batch 2): an aircraft's climb seen from the side, from JSBSim's simulation: the path drawn
// as altitude over distance, the aircraft pitched by the simulated attitude, and the cockpit numbers ticking with it.
import React from "react";
import { line, scaleLinear } from "d3";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, ticks, useRel } from "./common";

const Plane: React.FC<{ x: number; y: number; pitch: number }> = ({ x, y, pitch }) => (
  <g transform={`translate(${x},${y}) rotate(${-pitch}) scale(1.7)`}>
    <path d="M -46,0 L 30,-6 L 50,0 L 30,6 Z" fill={C.ink} />
    <path d="M -6,-2 L 4,-2 L -10,-36 L -20,-36 Z" fill={C.accent} />
    <path d="M -40,-2 L -32,-2 L -44,-22 L -50,-22 Z" fill={C.accent} />
  </g>
);

const FlightProfile: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const dist: number[] = data.distance_m, alt: number[] = data.altitude_ft, t: number[] = data.t_s;
  const pad = { l: 120, r: 60, t: 170, b: 110 };
  const sx = scaleLinear().domain([0, Math.max(...dist)]).range([pad.l, width - pad.r]);
  const sy = scaleLinear().domain([Math.min(...alt) - 200, Math.max(...alt) + 250]).nice().range([height - pad.b, pad.t]);
  const seconds = (data.seconds ?? 3.6) * fps;
  const f = (Math.max(0, rel - 0.2 * fps) / seconds) * (t.length - 1);
  const i = Math.min(t.length - 1, Math.floor(f));
  const path = line<number>().x((_, k) => sx(dist[k])).y((_, k) => sy(alt[k]))(alt.slice(0, i + 1)) || "";
  const [y0, y1] = sy.domain();
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {ticks(y0, y1, 5).map((v) => <g key={v}>
          <line x1={pad.l} x2={width - pad.r} y1={sy(v)} y2={sy(v)} stroke={C.line} />
          <text x={pad.l - 12} y={sy(v) + 8} fill={C.muted} fontSize={24} textAnchor="end">{`${v} ft`}</text></g>)}
        <line x1={pad.l} x2={width - pad.r} y1={sy(data.target_ft)} y2={sy(data.target_ft)} stroke={C.warm} strokeDasharray="10 8" strokeWidth={3}
          opacity={ramp(rel, 0, 12)} />
        <text x={pad.l + 12} y={sy(data.target_ft) - 12} fill={C.warm} fontSize={26} opacity={ramp(rel, 0, 12)}>
          {`autopilot target ${data.target_ft} ft`}</text>
        <path d={path} fill="none" stroke={C.accent} strokeWidth={6} strokeLinecap="round" />
        <Plane x={sx(dist[i])} y={sy(alt[i])} pitch={data.pitch_deg[i] * 2} />
        <text x={pad.l} y={height - pad.b + 50} fill={C.muted} fontSize={24}>{`distance flown: ${(dist[i] / 1000).toFixed(1)} km`}</text>
      </svg>
      <div style={{ position: "absolute", right: 60, top: 40, display: "grid", gridTemplateColumns: "auto auto", gap: "6px 22px", fontSize: 30,
        color: C.ink, background: C.panel, padding: "12px 22px", borderRadius: 14 }}>
        <span style={{ color: C.muted }}>time</span><b>{`${t[i].toFixed(0)} s`}</b>
        <span style={{ color: C.muted }}>altitude</span><b>{`${alt[i].toFixed(0)} ft`}</b>
        <span style={{ color: C.muted }}>airspeed</span><b>{`${data.airspeed_kts[i].toFixed(0)} kt`}</b>
        <span style={{ color: C.muted }}>climb</span><b>{`${data.climb_fpm[i].toFixed(0)} ft/min`}</b>
      </div>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", left: 40, bottom: 24 }} /> : null}
    </div>
  );
};

registerBlock("flight_profile", FlightProfile);
