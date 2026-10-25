// Earth blocks (Task 046a, batch 2):
// - earth_section: the Earth cut in half (crust, mantle, outer core, inner core) with seismic rays from ObsPy's TauP
//   travelling out from the earthquake at their own speed, and the arrival times ticking in.
// - world_points: a Natural Earth world map (d3-geo, world-atlas) with points (earthquakes from the USGS) appearing in
//   time order, sized by magnitude.
// - plate_frames: coastlines moved back in time by pyGPlates, shown age by age on the same map projection.
import React from "react";
import { geoArea, geoGraticule10, geoNaturalEarth1, geoPath, scaleSqrt } from "d3";
import { feature } from "topojson-client";
import land110 from "world-atlas/land-110m.json";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, useRel } from "./common";

const LAYER_COLOURS: Record<string, string> = { crust: "#8a6a4a", mantle: "#c8572b", "outer core": "#f0a33a", "inner core": "#ffe08a" };
const RAY_COLOURS: Record<string, string> = { P: C.accent, S: C.warm, PcP: "#c79bff", SKS: "#7CFFB2", PKP: "#6fb7ff" };

const EarthSection: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const R = data.earth_radius_km;
  const radius = Math.min(height - 240, width * 0.55) / 2;
  const cx = width * 0.38, cy = height * 0.56;
  const k = radius / R;
  const rays = data.rays as { phase: string; time_s: number; angle_rad: number[]; radius_km: number[] }[];
  const maxT = Math.max(...rays.map((r) => r.time_s));
  const travel = (data.travel_seconds ?? 3.0) * fps;
  const clock = Math.max(0, (rel - 0.5 * fps) / travel) * maxT;                 // seismic seconds shown at this frame
  const pt = (a: number, r: number) => [cx + Math.sin(a) * r * k, cy - Math.cos(a) * r * k];
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {(data.layers as { name: string; radius_km: number }[]).map((l) =>
          <circle key={l.name} cx={cx} cy={cy} r={l.radius_km * k} fill={LAYER_COLOURS[l.name] || C.muted} opacity={0.85} />)}
        {(data.layers as { name: string; radius_km: number }[]).map((l, i) =>
          <text key={"t" + l.name} x={cx - l.radius_km * k + 14} y={cy + (i === 0 ? -10 : 8 + i * 4)} fill="#1b1006" fontSize={24} fontWeight={700}
            opacity={ramp(rel, 0, 12)}>{i === 0 ? "" : l.name}</text>)}
        {rays.map((ray) => {
          const share = Math.min(1, clock / ray.time_s);
          const n = Math.max(2, Math.round(ray.angle_rad.length * share));
          const d = ray.angle_rad.slice(0, n).map((a, i) => pt(a, ray.radius_km[i]).join(",")).join(" ");
          const tip = pt(ray.angle_rad[n - 1], ray.radius_km[n - 1]);
          return <g key={ray.phase}>
            <polyline points={d} fill="none" stroke={RAY_COLOURS[ray.phase] || C.ink} strokeWidth={5} strokeLinejoin="round" />
            {share < 1 ? <circle cx={tip[0]} cy={tip[1]} r={9} fill={RAY_COLOURS[ray.phase] || C.ink} /> : null}
          </g>;
        })}
        <g>
          {(() => { const [x, y] = pt(0, R - data.depth_km); return <g><circle cx={x} cy={y} r={14} fill={C.danger} />
            <text x={x + 20} y={y - 18} fill={C.ink} fontSize={28} fontWeight={800}>earthquake</text></g>; })()}
          {(() => { const a = (data.distance_deg * Math.PI) / 180; const [x, y] = pt(a, R + 250);
            return <g><polygon points={`${x - 16},${y + 14} ${x + 16},${y + 14} ${x},${y - 16}`} fill={C.ink} />
              <text x={x + 22} y={y} fill={C.ink} fontSize={28} fontWeight={800}>{`station, ${data.distance_deg}°`}</text></g>; })()}
        </g>
      </svg>
      <div style={{ position: "absolute", right: 60, top: 170, display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ color: C.muted, fontSize: 28 }}>{`clock: ${Math.min(clock, maxT).toFixed(0)} s after the quake`}</div>
        {rays.map((ray) => <div key={ray.phase} style={{ display: "flex", gap: 12, alignItems: "center", fontSize: 30, color: C.ink,
          opacity: clock >= ray.time_s ? 1 : 0.35 }}>
          <span style={{ width: 22, height: 22, borderRadius: 11, background: RAY_COLOURS[ray.phase] || C.ink, display: "inline-block" }} />
          <b>{ray.phase}</b><span style={{ color: C.muted }}>{clock >= ray.time_s ? `arrives at ${(ray.time_s / 60).toFixed(1)} min` : "on its way"}</span>
        </div>)}
      </div>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 50, bottom: 30 }} /> : null}
    </div>
  );
};

function useMap(width: number, height: number, top: number) {
  const land = feature(land110 as any, (land110 as any).objects.land) as any;
  const projection = geoNaturalEarth1().fitExtent([[30, top], [width - 30, height - 30]], { type: "Sphere" } as any);
  return { projection, path: geoPath(projection), land };
}

const WorldPoints: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const { projection, path, land } = useMap(width, height, 130);
  const rows = data.points as { lon: number; lat: number; magnitude: number; time_ms: number; place?: string }[];
  const t0 = Math.min(...rows.map((r) => r.time_ms)), t1 = Math.max(...rows.map((r) => r.time_ms));
  const seconds = (data.seconds ?? 3.2) * fps;
  const now = t0 + (t1 - t0) * Math.min(1, Math.max(0, (rel - 0.3 * fps) / seconds));
  const size = scaleSqrt().domain([6, 8.5]).range([6, 30]);
  const shown = rows.filter((r) => r.time_ms <= now);
  const biggest = shown.reduce((b: any, r) => (!b || r.magnitude > b.magnitude ? r : b), null);
  const date = new Date(now).toISOString().slice(0, 10);
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <path d={path({ type: "Sphere" } as any) || ""} fill="#0b2433" stroke={C.line} />
        <path d={path(geoGraticule10()) || ""} fill="none" stroke={C.line} strokeOpacity={0.5} />
        <path d={path(land) || ""} fill="#2c4a5a" stroke="#4b6b7b" strokeWidth={1} />
        {shown.map((r, i) => {
          const [x, y] = projection([r.lon, r.lat]) as [number, number];
          const age = (now - r.time_ms) / (t1 - t0 || 1);
          return <g key={i}>
            <circle cx={x} cy={y} r={size(r.magnitude) * (1 + Math.max(0, 0.08 - age) * 12)} fill={C.danger} opacity={0.55} stroke="#ffd0d0" strokeWidth={2} />
          </g>;
        })}
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      <div style={{ position: "absolute", right: 50, top: 30, textAlign: "right", color: C.ink, fontSize: 30 }}>
        <div style={{ fontWeight: 800 }}>{date}</div>
        <div style={{ color: C.muted }}>{`${shown.length} earthquakes`}</div>
        {biggest ? <div style={{ color: C.warm, fontSize: 26 }}>{`largest so far: M${biggest.magnitude.toFixed(1)}`}</div> : null}
      </div>
      {data.credit ? <div style={{ position: "absolute", left: 40, bottom: 10, color: C.muted, fontSize: 18 }}>{data.credit}</div> : null}
    </div>
  );
};

const PlateFrames: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const { projection, path } = useMap(width, height, 130);
  const frames = data.frames as { age_ma: number; shapes: number[][][] }[];
  const seconds = (data.seconds ?? 3.4) * fps;
  const f = Math.min(frames.length - 1, Math.floor((Math.max(0, rel - 0.2 * fps) / seconds) * frames.length));
  const frame = frames[f];
  // Each coastline is a closed ring on the sphere: d3-geo cuts it at the map's edge and fills it. A ring whose area comes
  // out larger than a hemisphere is wound the other way round, so it is reversed before drawing.
  const d = frame.shapes.map((s) => {
    const ring = s[0][0] === s[s.length - 1][0] && s[0][1] === s[s.length - 1][1] ? s : [...s, s[0]];
    let polygon: any = { type: "Polygon", coordinates: [ring] };
    if (geoArea(polygon) > 2 * Math.PI) polygon = { type: "Polygon", coordinates: [[...ring].reverse()] };
    return path(polygon) || "";
  }).join("");
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <path d={path({ type: "Sphere" } as any) || ""} fill="#0b2433" stroke={C.line} />
        <path d={path(geoGraticule10()) || ""} fill="none" stroke={C.line} strokeOpacity={0.5} />
        <path d={d} fill="#5d7f4f" fillOpacity={0.85} stroke="#e9c46a" strokeWidth={1.4} strokeLinejoin="round" />
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      <div style={{ position: "absolute", right: 60, top: 30, textAlign: "right", color: C.ink }}>
        <div style={{ fontSize: 64, fontWeight: 800 }}>{frame.age_ma === 0 ? "today" : `${frame.age_ma} million years ago`}</div>
      </div>
      {data.credit ? <div style={{ position: "absolute", left: 40, bottom: 10, color: C.muted, fontSize: 18 }}>{data.credit}</div> : null}
    </div>
  );
};

registerBlock("earth_section", EarthSection);
registerBlock("world_points", WorldPoints);
registerBlock("plate_frames", PlateFrames);
