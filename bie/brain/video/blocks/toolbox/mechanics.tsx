// Mechanics blocks (Task 046a, batch 2): beam_load (a beam on a pin and a roller, the load comes down, the beam bends by
// PyNite's deflection drawn larger so it can be seen, and the bending-moment diagram fills below) and heat_plate (a
// plate's temperature from scikit-fem, coloured triangle by triangle, with the heat-flux arrows growing).
import React from "react";
import { interpolateInferno, line, scaleLinear } from "d3";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, useRel } from "./common";

const BeamLoad: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const xs: number[] = data.x, dy: number[] = data.deflection_m, mz: number[] = data.moment_Nm;
  const L = data.length;
  const left = 140, right = width - 140, beamY = height * 0.42;
  const sx = scaleLinear().domain([0, L]).range([left, right]);
  const maxDef = Math.max(...dy.map((v) => Math.abs(v))) || 1;
  const scale = (data.exaggerate_px ?? 90) / maxDef;                       // drawn larger: a few mm become visible pixels
  const drop = ramp(rel, 0.4 * fps, 0.6 * fps);
  const bend = ramp(rel, 1.0 * fps, 0.9 * fps);
  const bmd = ramp(rel, 2.0 * fps, 1.2 * fps);
  const beam = line<number>().x((_, i) => sx(xs[i])).y((v) => beamY - v * scale * bend)(dy) || "";
  const maxM = Math.max(...mz) || 1;
  const my = scaleLinear().domain([0, maxM]).range([height - 90, height - 90 - 150]);
  const shown = Math.max(2, Math.round(xs.length * bmd));
  const area = xs.slice(0, shown).map((x, i) => `${sx(x)},${my(mz[i])}`).join(" ");
  const loadX = sx(data.at);
  const iMax = dy.reduce((best, v, i) => (Math.abs(v) > Math.abs(dy[best]) ? i : best), 0);
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <path d={beam} fill="none" stroke="#9fb3bf" strokeWidth={26} strokeLinecap="round" />
        <path d={beam} fill="none" stroke="#cfe0ea" strokeWidth={8} strokeLinecap="round" opacity={0.6} />
        <polygon points={`${left},${beamY + 14} ${left - 34},${beamY + 70} ${left + 34},${beamY + 70}`} fill={C.accent} />
        <circle cx={right} cy={beamY + 42} r={26} fill="none" stroke={C.accent} strokeWidth={6} />
        <line x1={right - 50} x2={right + 50} y1={beamY + 72} y2={beamY + 72} stroke={C.accent} strokeWidth={5} />
        <line x1={left - 50} x2={left + 50} y1={beamY + 72} y2={beamY + 72} stroke={C.accent} strokeWidth={5} />
        <g transform={`translate(0, ${(drop - 1) * 180 - dy[xs.findIndex((x) => x >= data.at)] * scale * bend})`} opacity={drop}>
          <line x1={loadX} x2={loadX} y1={beamY - 200} y2={beamY - 26} stroke={C.danger} strokeWidth={10} />
          <polygon points={`${loadX - 24},${beamY - 52} ${loadX + 24},${beamY - 52} ${loadX},${beamY - 18}`} fill={C.danger} />
          <text x={loadX + 20} y={beamY - 170} fill={C.danger} fontSize={34} fontWeight={800}>{(data.load_N / 1000).toFixed(0)} kN</text>
        </g>
        <g opacity={bend}>
          <line x1={sx(xs[iMax])} x2={sx(xs[iMax])} y1={beamY} y2={beamY - dy[iMax] * scale} stroke={C.warm} strokeWidth={3} strokeDasharray="8 6" />
          <text x={sx(xs[iMax]) + 14} y={beamY - dy[iMax] * scale + 46} fill={C.warm} fontSize={30} fontWeight={700}>
            {`sags ${Math.abs(data.max_deflection_mm).toFixed(2)} mm (drawn larger)`}</text>
        </g>
        <g opacity={bmd}>
          <line x1={left} x2={right} y1={height - 90} y2={height - 90} stroke={C.line} strokeWidth={2} />
          <polygon points={`${sx(0)},${my(0)} ${area} ${sx(xs[shown - 1])},${my(0)}`} fill={C.accent} opacity={0.35} stroke={C.accent} strokeWidth={4} />
          <text x={left} y={height - 260} fill={C.ink} fontSize={28}>{`bending moment, peak ${data.max_moment_kNm.toFixed(1)} kN·m`}</text>
        </g>
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 50, top: 36, opacity: ramp(rel, 1.9 * fps, 12) }} /> : null}
    </div>
  );
};

const HeatPlate: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const nodes: number[][] = data.nodes, tris: number[][] = data.triangles, T: number[] = data.temperature;
  const size = Math.min(width * 0.55, height - 200);
  const ox = (width - size) / 2 - 120, oy = 150;
  const px = (p: number[]) => [ox + p[0] * size, oy + (1 - p[1]) * size];
  const colour = (t: number) => interpolateInferno(0.15 + 0.8 * (t - data.cold) / (data.hot - data.cold));
  const fill = ramp(rel, 0.2 * fps, 1.6 * fps, (t: number) => t);
  const grow = ramp(rel, 2.0 * fps, 1.2 * fps);
  const a = data.arrows;
  const maxF = Math.max(...a.fx.map((f: number, i: number) => Math.hypot(f, a.fy[i])));
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {tris.map((tri, i) => {
          const cx = (nodes[tri[0]][0] + nodes[tri[1]][0] + nodes[tri[2]][0]) / 3;
          const show = cx <= fill * 1.05;                                     // the heat spreads in from the hot edge
          const t = (T[tri[0]] + T[tri[1]] + T[tri[2]]) / 3;
          return <polygon key={i} points={tri.map((n) => px(nodes[n]).join(",")).join(" ")} fill={show ? colour(t) : "#16303f"}
            stroke={show ? colour(t) : "#1d3a4a"} strokeWidth={0.6} />;
        })}
        <rect x={ox - 14} y={oy + (1 - 0.65) * size} width={14} height={0.3 * size} fill="#ffdf6b" />
        <rect x={ox + size} y={oy} width={14} height={size} fill="#6fb7ff" />
        {a.x.map((x: number, i: number) => {
          const [x0, y0] = px([x, a.y[i]]);
          const m = Math.hypot(a.fx[i], a.fy[i]) / maxF;
          const len = 26 + 40 * m;
          const ang = Math.atan2(-a.fy[i], a.fx[i]);
          const x1 = x0 + Math.cos(ang) * len * grow, y1 = y0 + Math.sin(ang) * len * grow;
          return <g key={"a" + i} opacity={grow * (0.35 + 0.65 * m)}>
            <line x1={x0} y1={y0} x2={x1} y2={y1} stroke={C.ink} strokeWidth={4} />
            <circle cx={x1} cy={y1} r={5} fill={C.ink} /></g>;
        })}
        <text x={ox - 20} y={oy + (1 - 0.68) * size} fill="#ffdf6b" fontSize={28} textAnchor="end">{`${data.hot} °C`}</text>
        <text x={ox + size + 28} y={oy + size / 2} fill="#6fb7ff" fontSize={28}>{`${data.cold} °C`}</text>
        <g transform={`translate(${ox + size + 140}, ${oy + 40})`}>
          {[0, 0.25, 0.5, 0.75, 1].map((f, i) => <g key={i}>
            <rect x={0} y={(1 - f) * 300} width={40} height={75} fill={colour(data.cold + f * (data.hot - data.cold))} />
            <text x={54} y={(1 - f) * 300 + 10} fill={C.muted} fontSize={24}>{`${(data.cold + f * (data.hot - data.cold)).toFixed(0)} °C`}</text></g>)}
        </g>
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 50, bottom: 30, opacity: ramp(rel, 2.4 * fps, 12) }} /> : null}
    </div>
  );
};

registerBlock("beam_load", BeamLoad);
registerBlock("heat_plate", HeatPlate);
