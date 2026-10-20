import React from "react";
import { Easing, interpolate, useCurrentFrame } from "../lite";
import { C, Chip, Rise, Stamp, pulse, useIn, useMark, useRamp } from "../kit";
import { Human, Plant } from "./plant";

/** A round cell that divides into two (progress 0 -> 1). */
const Dividing: React.FC<{ x: number; y: number; r: number; p: number; color?: string; edge?: string }> = ({ x, y, r, p, color = C.cyto, edge = "#F59E0B" }) => {
  const sep = interpolate(p, [0.35, 1], [0, r * 1.25], { easing: Easing.inOut });
  const pinch = interpolate(p, [0, 0.35], [1, 0.82]);
  if (p < 0.35) {
    return (
      <g transform={`translate(${x},${y}) scale(${1 / pinch},${pinch})`}>
        <circle r={r} fill={color} stroke={edge} strokeWidth={5} />
        <circle cx={-r * 0.3 * (1 - pinch) * 8} r={r * 0.28} fill={C.nucleus} opacity={0.9} />
        <circle cx={r * 0.3 * (1 - pinch) * 8} r={r * 0.28} fill={C.nucleus} opacity={(1 - pinch) * 5} />
      </g>
    );
  }
  const rr = r * interpolate(p, [0.35, 1], [0.82, 0.78]);
  return (
    <g transform={`translate(${x},${y})`}>
      {[-1, 1].map((s) => (
        <g key={s} transform={`translate(${s * sep},0)`}>
          <circle r={rr} fill={color} stroke={edge} strokeWidth={5} />
          <circle r={rr * 0.34} fill={C.nucleus} opacity={0.9} />
        </g>
      ))}
    </g>
  );
};

const ROWS: { k: string; m: [string, string]; x: [string, string] }[] = [
  { k: "Kahan hota hai", m: ["Somatic cells (body cells)", "m-somatic"], x: ["Germ cells", "x-germ"] },
  { k: "Nucleus divide", m: ["1 baar", "m-once"], x: ["2 baar", "x-twice"] },
  { k: "Daughter cells", m: ["2 · diploid (2n)", "m-two"], x: ["4 · haploid (n)", "x-four"] },
  { k: "Chromosome no.", m: ["Same rehta hai", "m-chromo"], x: ["Aadha ho jata hai", "x-half"] },
  { k: "Kaam", m: ["Growth aur repair", "m-chromo"], x: ["Gametes banana", "x-gametes"] },
  { k: "Naam", m: ["Equational division", "equational"], x: ["Reduction division", "reduction"] },
];

export const Division: React.FC = () => {
  const f = useCurrentFrame();
  const split = useRamp("split", 40);
  const tableIn = useIn("mitosis");
  const meiosisIn = useIn("meiosis");
  const leaveTable = useRamp("pa", 18);
  const plantVsAnimal = useIn("pa", 10);
  const leavePA = useRamp("body", 16);
  const bodyIn = useIn("body", 8);
  const meristem = useIn("meristem");
  const bigCell = 1 - useRamp("mitosis", 16);
  const rowP = ROWS.map((r) => [useIn(r.m[1], 0, 160), useIn(r.x[1], 0, 160)]);
  const plate = useRamp("plate", 45);
  const furrow = useRamp("furrow", 45);
  const cen = useIn("centrioles");
  const tableOpacity = 1 - leaveTable;
  return (
    <g>
      {bigCell > 0 && (
        <g opacity={bigCell}>
          <Rise p={useIn(0, 4)} x={960} y={250} size={56} anchor="middle">Cell badhti kaise hai? Divide hokar.</Rise>
          <Dividing x={960} y={600} r={170} p={split} />
        </g>
      )}
      {tableOpacity > 0 && tableIn > 0 && (
        <g opacity={tableOpacity * Math.min(1, tableIn)}>
          <g transform="translate(930,190)">
            <rect x={-300} y={-52} width={600} height={84} rx={20} fill={C.leaf} opacity={0.16} />
            <text x={0} y={6} textAnchor="middle" fill={C.leaf} fontSize={50} fontWeight={900}>MITOSIS</text>
            <Dividing x={250} y={-10} r={26} p={interpolate(f, [useMark("mitosis"), useMark("mitosis") + 40], [0, 1])} />
          </g>
          <g transform="translate(1560,190)" opacity={Math.min(1, meiosisIn)}>
            <rect x={-300} y={-52} width={600} height={84} rx={20} fill={C.violet} opacity={0.18} />
            <text x={0} y={6} textAnchor="middle" fill={C.violet} fontSize={50} fontWeight={900}>MEIOSIS</text>
          </g>
          {ROWS.map((r, i) => {
            const y = 300 + i * 112;
            const [pm, px] = rowP[i];
            const any = Math.min(1, Math.max(pm, px));
            return (
              <g key={i}>
                <rect x={80} y={y - 4} width={1780} height={96} rx={18} fill="#fff" opacity={0.035 * any} />
                <text x={110} y={y + 58} fill={C.soft} fontSize={34} fontWeight={700} opacity={any}>{r.k}</text>
                <text x={930} y={y + 58 + (1 - Math.min(1, pm)) * 14} textAnchor="middle" fill={C.ink} fontSize={40} fontWeight={800} opacity={Math.min(1, pm)}>{r.m[0]}</text>
                <text x={1560} y={y + 58 + (1 - Math.min(1, px)) * 14} textAnchor="middle" fill={C.ink} fontSize={40} fontWeight={800} opacity={Math.min(1, px)}>{r.x[0]}</text>
              </g>
            );
          })}
          <line x1={1245} y1={150} x2={1245} y2={980} stroke={C.cardLine} strokeWidth={2} />
        </g>
      )}
      {plantVsAnimal > 0 && leavePA < 1 && (
        <g opacity={Math.min(1, plantVsAnimal) * (1 - leavePA)}>
          <Rise p={plantVsAnimal} x={960} y={200} size={52} anchor="middle">Mitosis: plant cell vs animal cell</Rise>
          {/* plant cell with cell plate */}
          <g transform="translate(560,560)">
            <rect x={-260} y={-190} width={520} height={380} rx={26} fill={C.wall} />
            <rect x={-240} y={-170} width={480} height={340} rx={20} fill={C.cyto} stroke="#F59E0B" strokeWidth={5} />
            <circle cx={-120} r={50} fill={C.nucleus} /><circle cx={120} r={50} fill={C.nucleus} />
            <rect x={-7} y={-170 * plate} width={14} height={340 * plate} rx={7} fill={C.leafDeep} />
            {plate > 0.6 && <text x={0} y={-200} textAnchor="middle" fill={C.leaf} fontSize={36} fontWeight={800} opacity={(plate - 0.6) * 2.5}>Cell plate ↓</text>}
            <text x={0} y={262} textAnchor="middle" fill={C.leaf} fontSize={44} fontWeight={800}>Plant cell</text>
            <text x={0} y={318} textAnchor="middle" fill={C.soft} fontSize={34} fontWeight={700} opacity={Math.min(1, cen)}>Centrioles: ✗ absent · Asters: ✗</text>
          </g>
          {/* animal cell with furrow */}
          <g transform="translate(1360,560)">
            {furrow < 0.98 ? (
              <g transform={`scale(${1 + furrow * 0.25},${1 - furrow * 0.4})`}>
                <ellipse rx={220} ry={190} fill={C.cyto} stroke="#F59E0B" strokeWidth={5} />
                <circle cx={-110} r={46} fill={C.nucleus} /><circle cx={110} r={46} fill={C.nucleus} />
              </g>
            ) : null}
            {furrow > 0 && (
              <g opacity={furrow}>
                <circle cx={-150 - furrow * 30} r={150} fill={C.cyto} stroke="#F59E0B" strokeWidth={5} opacity={furrow > 0.6 ? 1 : 0} />
                <circle cx={150 + furrow * 30} r={150} fill={C.cyto} stroke="#F59E0B" strokeWidth={5} opacity={furrow > 0.6 ? 1 : 0} />
                <circle cx={-150 - furrow * 30} r={46} fill={C.nucleus} opacity={furrow > 0.6 ? 1 : 0} />
                <circle cx={150 + furrow * 30} r={46} fill={C.nucleus} opacity={furrow > 0.6 ? 1 : 0} />
                <path d="M -30 -200 L 0 -150 L 30 -200" stroke={C.coral} strokeWidth={6} fill="none" opacity={furrow < 0.6 ? 1 : 0} />
                <path d="M -30 200 L 0 150 L 30 200" stroke={C.coral} strokeWidth={6} fill="none" opacity={furrow < 0.6 ? 1 : 0} />
              </g>
            )}
            <text x={0} y={262} textAnchor="middle" fill={C.coral} fontSize={44} fontWeight={800}>Animal cell</text>
            <text x={0} y={318} textAnchor="middle" fill={C.soft} fontSize={34} fontWeight={700} opacity={Math.min(1, cen)}>Centrioles: ✓ · Furrowing (cleavage)</text>
          </g>
        </g>
      )}
      {bodyIn > 0 && (
        <g opacity={Math.min(1, bodyIn)}>
          <Rise p={bodyIn} x={960} y={200} size={52} anchor="middle">Mitosis kahan hota hai?</Rise>
          <Human x={560} foot={900} h={560} color="#93C5FD" opacity={0.85} />
          {Array.from({ length: 18 }, (_, i) => {
            const pts = [[560, 420], [540, 520], [580, 600], [520, 700], [600, 760], [560, 860], [470, 560], [650, 560], [545, 640], [575, 470], [530, 800], [590, 820], [500, 470], [620, 470], [560, 560], [560, 700], [520, 880], [600, 880]][i];
            return <circle key={i} cx={pts[0]} cy={pts[1]} r={10} fill={C.coral} opacity={pulse(f + i * 7, 26, 0.3)} />;
          })}
          <text x={560} y={980} textAnchor="middle" fill={C.coral} fontSize={38} fontWeight={800}>Animals: poore body ke tissues mein</text>
          <Plant x={1380} ground={760} height={420} root={150} apical={Math.min(1, meristem) + 0.0001} intercalary={Math.min(1, meristem)} />
          <text x={1380} y={980} textAnchor="middle" fill={C.leaf} fontSize={38} fontWeight={800}>Plants: mainly meristem mein</text>
          {meristem > 0 && <Stamp x={1380} y={300} text="MERISTEM" color={C.amber} p={meristem} rotate={-4} size={64} />}
        </g>
      )}
    </g>
  );
};
