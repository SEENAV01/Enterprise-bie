import React from "react";
import { interpolate, useCurrentFrame } from "../lite";
import { C, Cell, Chip, Rise, seeded, useIn } from "../kit";

export const Title: React.FC = () => {
  const f = useCurrentFrame();
  const a = useIn(0, 4, 90);
  const b = useIn("subtitle", 0, 120);
  const rnd = seeded(21);
  const cells = Array.from({ length: 14 }, (_, i) => ({ x: 120 + rnd() * 1680, y: 120 + rnd() * 840, r: 26 + rnd() * 34, s: rnd(), shape: (["round", "rect", "hex"] as const)[i % 3] }));
  return (
    <g>
      {cells.map((c, i) => (
        <Cell key={i} x={c.x + Math.sin(f / 50 + i) * 14} y={c.y + Math.cos(f / 60 + i) * 12} r={c.r} shape={c.shape} opacity={0.18 + 0.1 * c.s}
          fill={i % 2 ? "#FDE68A" : "#BBF7D0"} edge={i % 2 ? "#F59E0B" : "#16A34A"} wall={c.shape === "rect" ? 6 : 0} seed={i} granules={4} />
      ))}
      <g transform={`translate(960,${470 - (1 - a) * 30}) scale(${0.9 + 0.1 * a})`} opacity={a}>
        <text x={0} y={0} textAnchor="middle" fill={C.ink} fontSize={150} fontWeight={900} letterSpacing={-2}>Tissues</text>
        <rect x={-180} y={36} width={360 * Math.min(1, a)} height={8} rx={4} fill={C.leaf} />
      </g>
      <Rise p={b} x={960} y={620} size={52} anchor="middle" color={C.soft}>Part 1 · Cells ki team aur plant ka growth engine</Rise>
      <g opacity={interpolate(f, [40, 70], [0, 1])}>
        <Chip x={760} y={740} text="UPSC · State PCS" color={C.amber} size={30} />
        <Chip x={1160} y={740} text="Science & Technology" color={C.sky} size={30} />
      </g>
    </g>
  );
};
