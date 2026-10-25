// Astronomy blocks (Task 046a, batch 2):
// - orbits: the inner planets around the Sun from NASA JPL's DE421 ephemeris (Skyfield), each moving along its own
//   orbit at its real pace, with the date counting up and each period checked by Kepler's third law (Astropy).
// - sky_dome: the bright stars above a place at a time (Hipparcos, Skyfield) on a round sky chart: zenith in the
//   middle, the horizon at the edge, north up; star size by brightness; the planets that are up are labelled.
import React from "react";
import { line, scaleLinear } from "d3";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, useRel } from "./common";

const PLANET_COLOURS: Record<string, string> = { mercury: "#b9b4ad", venus: "#f3d28b", earth: "#4fa3ff", mars: "#ff7a50" };

const Orbits: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const planets = data.planets as { name: string; x_au: number[]; y_au: number[]; kepler_period_days: number }[];
  const reach = Math.max(...planets.map((p) => Math.max(...p.x_au.map(Math.abs), ...p.y_au.map(Math.abs)))) * 1.08;
  const size = Math.min(width * 0.62, height - 170);
  const cx = width * 0.4, cy = 130 + size / 2;
  const s = scaleLinear().domain([-reach, reach]).range([-size / 2, size / 2]);
  const n = planets[0].x_au.length;
  const seconds = (data.seconds ?? 3.6) * fps;
  const i = Math.min(n - 1, Math.floor((Math.max(0, rel - 0.2 * fps) / seconds) * (n - 1)));
  const trail = 18;
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <circle cx={cx} cy={cy} r={22} fill="#ffd34d" style={{ filter: "drop-shadow(0 0 18px #ffb000)" }} />
        {planets.map((p) => {
          const orbit = line<number>().x((_, k) => cx + s(p.x_au[k])).y((_, k) => cy - s(p.y_au[k]))(p.x_au) || "";
          const from = Math.max(0, i - trail);
          const trailD = p.x_au.slice(from, i + 1).map((_, k) => `${cx + s(p.x_au[from + k])},${cy - s(p.y_au[from + k])}`).join(" ");
          return <g key={p.name}>
            <path d={orbit} fill="none" stroke={C.line} strokeWidth={2} />
            <polyline points={trailD} fill="none" stroke={PLANET_COLOURS[p.name] || C.ink} strokeWidth={5} opacity={0.6} />
            <circle cx={cx + s(p.x_au[i])} cy={cy - s(p.y_au[i])} r={p.name === "earth" ? 13 : 10} fill={PLANET_COLOURS[p.name] || C.ink} />
            <text x={cx + s(p.x_au[i]) + 16} y={cy - s(p.y_au[i]) - 12} fill={C.ink} fontSize={26} fontWeight={700}>{p.name}</text>
          </g>;
        })}
      </svg>
      <div style={{ position: "absolute", right: 60, top: 150, color: C.ink, display: "flex", flexDirection: "column", gap: 12, fontSize: 28 }}>
        <div style={{ fontSize: 44, fontWeight: 800 }}>{data.dates[i]}</div>
        {planets.map((p) => <div key={p.name} style={{ opacity: ramp(rel, 1.0 * fps, 12) }}>
          <span style={{ color: PLANET_COLOURS[p.name] }}>●</span>{` ${p.name}: one orbit = ${Math.round(p.kepler_period_days)} days`}</div>)}
      </div>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 50, bottom: 30 }} /> : null}
    </div>
  );
};

const SkyDome: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const st = data.stars;
  const R = Math.min(height - 200, width * 0.5) / 2;
  const cx = width * 0.42, cy = 140 + R;
  const turn = ((data.turn_degrees ?? 12) * Math.PI / 180) * ramp(rel, 0, (data.seconds ?? 4) * fps);
  const proj = (alt: number, az: number) => {
    const r = R * (90 - alt) / 90;
    const a = (az * Math.PI) / 180 + turn;
    return [cx - r * Math.sin(a), cy - r * Math.cos(a)];               // a sky chart is read overhead: east on the left
  };
  const appear = ramp(rel, 0.2 * fps, 1.6 * fps, (t: number) => t);
  const order = st.magnitude.map((m: number, k: number) => [m, k]).sort((a: number[], b: number[]) => a[0] - b[0]);
  const count = Math.round(order.length * appear);
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <circle cx={cx} cy={cy} r={R} fill="#040b14" stroke="#2c4a5a" strokeWidth={3} />
        {[30, 60].map((alt) => <circle key={alt} cx={cx} cy={cy} r={R * (90 - alt) / 90} fill="none" stroke={C.line} strokeDasharray="6 8" />)}
        {[["N", 0], ["E", 90], ["S", 180], ["W", 270]].map(([t, az]) => {
          const [x, y] = proj(-8, az as number);
          return <text key={t as string} x={x} y={y + 10} fill={C.muted} fontSize={30} fontWeight={800} textAnchor="middle">{t}</text>;
        })}
        {order.slice(0, count).map(([m, k]: number[]) => {
          const [x, y] = proj(st.alt[k], st.az[k]);
          return <circle key={k} cx={x} cy={y} r={Math.max(1.6, 6.5 - 1.5 * m)} fill="#fffbe8" opacity={Math.min(1, 1.15 - m / 5)} />;
        })}
        {Object.entries((data.names || {}) as Record<string, string>).map(([hip, name]) => {
          const k = (st.hip as number[]).indexOf(Number(hip));
          if (k < 0) return null;
          const [x, y] = proj(st.alt[k], st.az[k]);
          return <text key={hip} x={x + 12} y={y + 26} fill={C.accent} fontSize={24} fontWeight={700} opacity={ramp(rel, 2.2 * fps, 12)}>{name}</text>;
        })}
        {(data.planets as { name: string; alt: number; az: number }[]).map((p) => {
          const [x, y] = proj(p.alt, p.az);
          return <g key={p.name} opacity={ramp(rel, 1.8 * fps, 12)}>
            <circle cx={x} cy={y} r={9} fill={C.warm} />
            <text x={x + 14} y={y - 12} fill={C.warm} fontSize={28} fontWeight={800}>{p.name}</text></g>;
        })}
      </svg>
      <div style={{ position: "absolute", right: 60, top: 160, color: C.ink, fontSize: 28, display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ fontSize: 34, fontWeight: 800 }}>{data.place_name || "the sky"}</div>
        <div style={{ color: C.muted }}>{data.time_label || data.local_time}</div>
        <div>{`${count} bright stars above the horizon`}</div>
      </div>
      <Title text={data.title} sub={data.subtitle} />
      {data.credit ? <div style={{ position: "absolute", left: 40, bottom: 10, color: C.muted, fontSize: 18 }}>{data.credit}</div> : null}
    </div>
  );
};

registerBlock("orbits", Orbits);
registerBlock("sky_dome", SkyDome);
