// india_map (Task 046a, batch 3): India as India shows it (Natural Earth's India point-of-view boundary), its states and
// union territories, and the neighbours, from BIE's maps adapter (Shapely), drawn with d3-geo.
// - map_region: the highlighted states fill in and glow, the camera zooms from all of India to them, and the label
//   gives the name and the area the adapter computed;
// - map_route: a route through named places (Natural Earth's populated places) is drawn leg by leg along great
//   circles, each stop appearing as the line reaches it, with the distance so far.
import React from "react";
import { geoInterpolate, geoMercator, geoPath } from "d3";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, useRel } from "./common";

type Feature = { type: "Feature"; geometry: any; properties?: any };
const feature = (geometry: any): Feature => ({ type: "Feature", geometry, properties: {} });
const fmt = (n: number) => n.toLocaleString("en-IN");

/** Stop labels placed one by one where they cover no earlier label and no stop: right, left, below, above. */
function labelled(stops: { name: string; at: [number, number] }[]) {
  const boxes: [number, number, number, number][] = stops.map((s) => [s.at[0] - 10, s.at[1] - 10, s.at[0] + 10, s.at[1] + 10]);
  const hits = (b: [number, number, number, number]) => boxes.some((o) => b[0] < o[2] && b[2] > o[0] && b[1] < o[3] && b[3] > o[1]);
  return stops.map((s) => {
    const w = s.name.length * 14.5, h = 26, [x, y] = s.at;
    const tries: [number, number, "start" | "end" | "middle", [number, number, number, number]][] = [
      [x + 14, y + 9, "start", [x + 12, y - 13, x + 14 + w, y + 13]], [x - 14, y + 9, "end", [x - 14 - w, y - 13, x - 12, y + 13]],
      [x, y + 38, "middle", [x - w / 2, y + 14, x + w / 2, y + 14 + h]], [x, y - 18, "middle", [x - w / 2, y - 16 - h, x + w / 2, y - 14]]];
    const pick = tries.find((t) => !hits(t[3])) || tries[0];
    boxes.push(pick[3]);
    return { ...s, label: [pick[0], pick[1]] as [number, number], anchor: pick[2] };
  });
}

const IndiaMap: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const states = data.states as { name: string; highlight: boolean; label: [number, number]; area_km2: number; kind: string; geometry: any }[];
  const picked = states.filter((s) => s.highlight);
  const route = data.route as { stops: { name: string; lon: number; lat: number }[]; legs: { km: number; total_km: number }[]; total_km: number } | undefined;
  const top = 120, pad = 30;
  const extent: [[number, number], [number, number]] = [[pad, top], [width - (route ? 470 : pad), height - pad]];   // the distance panel sits right
  // the frame to fit: all of India, or the route with a margin round it; then the picked states
  const margin = 2.5;
  const routeBox = route ? feature({ type: "MultiPoint", coordinates: route.stops.flatMap((s) =>
    [[s.lon - margin, s.lat - margin], [s.lon + margin, s.lat + margin]]) }) : null;
  const whole: any = { type: "FeatureCollection", features: routeBox && data.fit !== "india" ? [routeBox] : [feature(data.outline)] };
  const near: any = picked.length ? { type: "FeatureCollection", features: picked.map((s) => feature(s.geometry)) } : whole;
  const p0 = geoMercator().fitExtent(extent, whole);
  const p1 = geoMercator().fitExtent([[extent[0][0] + 380, extent[0][1] + 150], [extent[1][0] - 380, extent[1][1] - 120]], near);
  const z = picked.length ? ramp(rel, (data.zoom_at ?? 1.6) * fps, (data.zoom_seconds ?? 1.4) * fps) : 0;
  // the zoom: the scale grows geometrically while the map point at the middle of the frame moves straight to the states
  const mid: [number, number] = [(extent[0][0] + extent[1][0]) / 2, (extent[0][1] + extent[1][1]) / 2];
  const c0 = p0.invert!(mid)!, c1 = p1.invert!(mid)!;
  const centre: [number, number] = [c0[0] + (c1[0] - c0[0]) * z, c0[1] + (c1[1] - c0[1]) * z];
  const projection = geoMercator().scale(p0.scale() * Math.pow(p1.scale() / p0.scale(), z)).translate([0, 0]);
  const [cx, cy] = projection(centre)!;
  projection.translate([mid[0] - cx, mid[1] - cy]);
  const path = geoPath(projection);
  const fill = ramp(rel, (data.highlight_at ?? 0.6) * fps, 12);
  const glow = fill * (0.75 + 0.25 * Math.sin(rel / 5));
  // route: legs drawn one after another over route_seconds, each along its great circle
  let routeD = "", reached = 0, km = 0, tip: [number, number] | null = null;
  if (route) {
    const n = route.stops.length - 1;
    const progress = n * ramp(rel, (data.route_at ?? 0.6) * fps, (data.route_seconds ?? 3.0) * fps, (t: number) => t);
    const coords: [number, number][] = [];
    for (let i = 0; i < n; i++) {
      const share = Math.max(0, Math.min(1, progress - i));
      if (share <= 0) break;
      const a: [number, number] = [route.stops[i].lon, route.stops[i].lat], b: [number, number] = [route.stops[i + 1].lon, route.stops[i + 1].lat];
      const f = geoInterpolate(a, b);
      for (let s = 0; s <= 12; s++) coords.push(f((share * s) / 12));
      km = (i ? route.legs[i - 1].total_km : 0) + route.legs[i].km * share;
      reached = share >= 1 ? i + 1 : i;
    }
    routeD = coords.length > 1 ? path({ type: "LineString", coordinates: coords } as any) || "" : "";
    tip = coords.length ? (projection(coords[coords.length - 1]) as [number, number]) : null;
  }
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <filter id="mapglow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation={6 * glow} result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>
        <rect x={0} y={0} width={width} height={height} fill="#0a2030" />
        {(data.neighbours as { name: string; geometry: any }[]).map((n) =>
          <path key={n.name} d={path(feature(n.geometry)) || ""} fill="#34434b" stroke="#55666f" strokeWidth={1} />)}
        <path d={path(feature(data.outline)) || ""} fill="#2b5a4a" stroke="#9fd6c0" strokeWidth={2} />
        <path d={path(feature(data.beyond_states)) || ""} fill="#2b5a4a" />
        {states.map((s) => <path key={s.name} d={path(feature(s.geometry)) || ""} fill={s.highlight ? C.warm : "#2b5a4a"}
          fillOpacity={s.highlight ? 0.25 + 0.7 * fill : 1} stroke="#7fb8a4" strokeWidth={0.8} strokeOpacity={0.8}
          filter={s.highlight && fill > 0 ? "url(#mapglow)" : undefined} />)}
        {picked.map((s) => {
          const [x, y] = projection(s.label)!;
          return <g key={"l" + s.name} opacity={ramp(rel, ((data.zoom_at ?? 1.6) + (data.zoom_seconds ?? 1.4)) * fps - 6, 10)}>
            <text x={x} y={y} fill="#1b1006" fontSize={34} fontWeight={800} textAnchor="middle">{s.name}</text>
            <text x={x} y={y + 36} fill="#1b1006" fontSize={24} fontWeight={700} textAnchor="middle">{`about ${fmt(s.area_km2)} km²`}</text>
          </g>;
        })}
        {route ? <path d={routeD} fill="none" stroke={C.warm} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" /> : null}
        {route ? labelled(route.stops.map((s) => ({ name: s.name, at: projection([s.lon, s.lat]) as [number, number] }))).map((s, i) => {
          if (i > reached) return null;
          return <g key={s.name}>
            <circle cx={s.at[0]} cy={s.at[1]} r={9} fill={C.ink} stroke={C.warm} strokeWidth={4} />
            <text x={s.label[0]} y={s.label[1]} fill={C.ink} fontSize={26} fontWeight={700} textAnchor={s.anchor}
              stroke="#0a2030" strokeWidth={5} paintOrder="stroke">{s.name}</text>
          </g>;
        }) : null}
        {tip ? <circle cx={tip[0]} cy={tip[1]} r={12} fill={C.warm} /> : null}
      </svg>
      {route ? <div style={{ position: "absolute", right: 50, top: 150, color: C.ink, background: C.panel, padding: "14px 22px", borderRadius: 14,
        fontSize: 30, minWidth: 360 }}>
        <div style={{ color: C.muted, fontSize: 24 }}>{data.route_label || "distance so far"}</div>
        <div style={{ fontSize: 52, fontWeight: 800 }}>{`${fmt(Math.round(km))} km`}</div>
        <div style={{ color: C.muted, fontSize: 22 }}>{`great-circle legs · whole route ${fmt(route.total_km)} km`}</div>
      </div> : null}
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", left: 40, bottom: 40 }} /> : null}
      {data.credit ? <div style={{ position: "absolute", right: 30, bottom: 10, color: C.muted, fontSize: 18, background: "rgba(6,18,28,0.8)",
        padding: "2px 10px", borderRadius: 6 }}>{data.credit}</div> : null}
    </div>
  );
};

registerBlock("india_map", IndiaMap);
