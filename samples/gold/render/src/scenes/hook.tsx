import React from "react";
import { Easing, interpolate, useCurrentFrame } from "../lite";
import { C, Chip, Rise, pulse, seeded, useIn, useMark, useRamp } from "../kit";

const GROUND = 840;
const CUT = GROUND - 120;

export const GrassPatch: React.FC<{ x0: number; x1: number; mowAt: number; regrowAt: number; showBase?: number; seed?: number; scale?: number }> = ({ x0, x1, mowAt, regrowAt, showBase = 0, seed = 3, scale = 1 }) => {
  const f = useCurrentFrame();
  const rnd = seeded(seed);
  const blades = Array.from({ length: 46 }, () => ({ x: x0 + rnd() * (x1 - x0), h: (190 + rnd() * 130) * scale, bend: -30 + rnd() * 60, ph: rnd() * 6, w: 9 + rnd() * 6, g: rnd() }));
  const sweep = interpolate(f, [mowAt, mowAt + 26], [x0 - 60, x1 + 60], { easing: Easing.inOut });
  const regrow = interpolate(f, [regrowAt, regrowAt + 70], [0, 1], { easing: Easing.out });
  const cutH = (GROUND - CUT) * scale;
  return (
    <g>
      <rect x={x0 - 60} y={GROUND} width={x1 - x0 + 120} height={60} rx={18} fill="#3B2A1A" />
      <rect x={x0 - 60} y={GROUND} width={x1 - x0 + 120} height={12} rx={6} fill="#5B4126" />
      {blades.map((b, i) => {
        const cut = f >= mowAt && sweep > b.x;
        const h = cut ? cutH + (b.h - cutH) * regrow * (b.h > cutH ? 1 : 0) : b.h;
        const sway = Math.sin(f / 22 + b.ph) * 6;
        const tipX = b.x + (b.bend + sway) * (h / b.h);
        const d = `M ${b.x - b.w / 2} ${GROUND} Q ${b.x + b.bend * 0.3} ${GROUND - h * 0.55} ${tipX} ${GROUND - h} Q ${b.x + b.bend * 0.3 + 4} ${GROUND - h * 0.5} ${b.x + b.w / 2} ${GROUND} Z`;
        const color = b.g > 0.5 ? "#4ADE80" : "#22C55E";
        return (
          <g key={i}>
            <path d={d} fill={color} opacity={0.95} />
            {showBase > 0 && <rect x={b.x - b.w / 2 - 2} y={GROUND - 26} width={b.w + 4} height={24} rx={6} fill={C.amber} opacity={showBase * pulse(f, 30, 0.5)} />}
          </g>
        );
      })}
      {f >= mowAt && f < mowAt + 40 && (
        <g opacity={interpolate(f, [mowAt + 26, mowAt + 40], [1, 0])}>
          <line x1={sweep - 120} y1={GROUND - cutH} x2={sweep} y2={GROUND - cutH} stroke={C.coral} strokeWidth={6} strokeDasharray="18 10" />
          <text x={sweep + 14} y={GROUND - cutH + 12} fontSize={44}>✂️</text>
        </g>
      )}
    </g>
  );
};

export const TrunkSection: React.FC<{ cx: number; cy: number; at: number; maxRings?: number; label?: boolean; glow?: number }> = ({ cx, cy, at, maxRings = 9, glow = 0 }) => {
  const f = useCurrentFrame();
  const grow = interpolate(f, [at, at + 150], [0, 1], { easing: Easing.inOut });
  const rings = 3 + Math.floor(grow * (maxRings - 3));
  const r = 120 + grow * 110;
  return (
    <g transform={`translate(${cx},${cy})`}>
      <circle r={r + 22} fill="#6B4423" />
      <circle r={r + 8} fill="#C08A4E" />
      {glow > 0 && <circle r={r + 6} fill="none" stroke={C.leaf} strokeWidth={10} opacity={glow * pulse(f, 30, 0.45)} filter="url(#glow)" />}
      <circle r={r} fill="#E9C28A" />
      {Array.from({ length: rings }, (_, i) => (
        <circle key={i} r={(r * (i + 1)) / (rings + 1)} fill="none" stroke="#B07A3E" strokeWidth={3} opacity={0.75} />
      ))}
      <circle r={10} fill="#8B5A2B" />
    </g>
  );
};

export const Hook: React.FC = () => {
  const f = useCurrentFrame();
  const intro = useIn(0, 6);
  const trunk = useIn("trunk");
  const q = useIn("question");
  const promise = useIn("promise");
  const regrowTxt = useRamp("regrow", 20);
  const dim = interpolate(f, [useMark("trunk"), useMark("trunk") + 20], [1, 0.45]);
  return (
    <g>
      <Rise p={intro} x={140} y={210} size={58} color={C.ink}>Ghaas upar se kaati…</Rise>
      <g opacity={dim}>
        <GrassPatch x0={160} x1={820} mowAt={useMark("mow")} regrowAt={useMark("regrow")} />
        <g opacity={regrowTxt}>
          <Chip x={490} y={330} text="⏱  kuch din baad…" color={C.amber} p={regrowTxt} size={34} />
        </g>
      </g>
      <g opacity={trunk} transform={`translate(0,${(1 - trunk) * 40})`}>
        <Rise p={trunk} x={1400} y={210} size={58} anchor="middle">Ped ka tana: har saal mota</Rise>
        <TrunkSection cx={1400} cy={560} at={useMark("trunk")} />
      </g>
      {q > 0 && (
        <g transform={`translate(960,${960 - q * 10})`} opacity={Math.min(1, q)}>
          <rect x={-560} y={-62} width={1120} height={100} rx={50} fill={C.amber} opacity={0.14} stroke={C.amber} strokeWidth={3} />
          <text x={0} y={8} textAnchor="middle" fill={C.amber} fontSize={50} fontWeight={800}>Ye badhat aati kahan se hai?</text>
          <text x={548} y={18} textAnchor="middle" fill={C.amber} fontSize={86} fontWeight={900} opacity={pulse(f, 24)}>?</text>
        </g>
      )}
      {promise > 0 && <Chip x={960} y={1040} text="+ ek UPSC trap" color={C.coral} p={promise} size={28} solid />}
    </g>
  );
};
