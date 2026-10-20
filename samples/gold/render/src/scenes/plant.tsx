import React from "react";
import { useCurrentFrame } from "../lite";
import { C, pulse } from "../kit";

/** Side view of a young dicot plant with optional meristem highlights. */
export const Plant: React.FC<{ x: number; ground: number; height: number; root?: number; apical?: number; intercalary?: number;
  lateral?: number; scale?: number; leafScale?: number; dimLeaves?: number }> = ({ x, ground, height, root = 260, apical = 0, intercalary = 0, lateral = 0, scale = 1, leafScale = 1, dimLeaves = 1 }) => {
  const f = useCurrentFrame();
  const top = ground - height;
  const nodes = [0.3, 0.55, 0.78].map((k) => ground - height * k);
  const leaf = (nx: number, ny: number, dir: 1 | -1, size: number, key: number) => (
    <g key={key} transform={`translate(${nx},${ny}) scale(${dir * size * leafScale},${size * leafScale})`} opacity={dimLeaves}>
      <path d="M0,0 C30,-10 60,-40 120,-46 C100,-10 70,20 0,0 Z" fill="#22C55E" stroke="#15803D" strokeWidth={2} />
      <path d="M0,0 C40,-14 80,-34 118,-45" stroke="#14532D" strokeWidth={2} fill="none" opacity={0.6} />
    </g>
  );
  const glowA = apical * pulse(f, 28, 0.45);
  const glowI = intercalary * pulse(f, 28, 0.45);
  return (
    <g transform={`translate(${x},${ground}) scale(${scale}) translate(${-x},${-ground})`}>
      {/* roots */}
      <path d={`M${x},${ground} C${x - 6},${ground + root * 0.4} ${x + 8},${ground + root * 0.7} ${x},${ground + root}`} stroke="#A16207" strokeWidth={10} fill="none" strokeLinecap="round" />
      {[0.25, 0.45, 0.65].map((k, i) => (
        <path key={i} d={`M${x},${ground + root * k} q ${i % 2 ? -60 : 60} 30 ${i % 2 ? -110 : 110} ${70 - i * 10}`} stroke="#A16207" strokeWidth={5} fill="none" strokeLinecap="round" />
      ))}
      {/* stem */}
      <path d={`M${x},${ground} L${x},${top}`} stroke="#16A34A" strokeWidth={22} strokeLinecap="round" />
      {lateral > 0 && <>
        <line x1={x - 13} y1={ground} x2={x - 13} y2={top + 20} stroke={C.leaf} strokeWidth={5} opacity={lateral * pulse(f, 28, 0.5)} filter="url(#glow)" />
        <line x1={x + 13} y1={ground} x2={x + 13} y2={top + 20} stroke={C.leaf} strokeWidth={5} opacity={lateral * pulse(f, 28, 0.5)} filter="url(#glow)" />
      </>}
      {nodes.map((ny, i) => <g key={i}>
        <ellipse cx={x} cy={ny} rx={16} ry={7} fill="#15803D" />
        {leaf(x + 8, ny, 1, 1 - i * 0.12, i * 2)}
        {leaf(x - 8, ny, -1, 1 - i * 0.12, i * 2 + 1)}
        {intercalary > 0 && <rect x={x - 17} y={ny - 30} width={34} height={22} rx={6} fill={C.amber} opacity={glowI} filter="url(#glow)" />}
        {intercalary > 0 && <circle cx={x + 22} cy={ny - 4} r={10} fill={C.amber} opacity={glowI * 0.9} />}
        {intercalary > 0 && <circle cx={x - 22} cy={ny - 4} r={10} fill={C.amber} opacity={glowI * 0.9} />}
      </g>)}
      {/* shoot apex bud */}
      <path d={`M${x - 14},${top + 6} Q${x},${top - 34} ${x + 14},${top + 6} Z`} fill="#4ADE80" />
      {apical > 0 && <>
        <circle cx={x} cy={top - 6} r={30} fill={C.amber} opacity={glowA} filter="url(#glow)" />
        <circle cx={x} cy={ground + root} r={26} fill={C.amber} opacity={glowA} filter="url(#glow)" />
      </>}
      {/* ground */}
      <rect x={x - 330} y={ground} width={660} height={8} rx={4} fill="#5B4126" />
    </g>
  );
};

/** Simple human silhouette. */
export const Human: React.FC<{ x: number; foot: number; h: number; color?: string; opacity?: number }> = ({ x, foot, h, color = "#93C5FD", opacity = 1 }) => {
  const head = h * 0.13;
  return (
    <g opacity={opacity} fill={color} stroke={color} strokeLinecap="round">
      <circle cx={x} cy={foot - h + head} r={head} stroke="none" />
      <rect x={x - h * 0.11} y={foot - h + head * 2.1} width={h * 0.22} height={h * 0.36} rx={h * 0.08} stroke="none" />
      <line x1={x - h * 0.06} y1={foot - h * 0.42} x2={x - h * 0.08} y2={foot} strokeWidth={h * 0.07} />
      <line x1={x + h * 0.06} y1={foot - h * 0.42} x2={x + h * 0.08} y2={foot} strokeWidth={h * 0.07} />
      <line x1={x - h * 0.12} y1={foot - h * 0.68} x2={x - h * 0.2} y2={foot - h * 0.4} strokeWidth={h * 0.055} />
      <line x1={x + h * 0.12} y1={foot - h * 0.68} x2={x + h * 0.2} y2={foot - h * 0.4} strokeWidth={h * 0.055} />
    </g>
  );
};
