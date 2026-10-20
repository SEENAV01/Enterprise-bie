import React from "react";
import { Easing, interpolate, useCurrentFrame } from "../lite";
import { C, Cell, Chip, Leader, Rise, pulse, seeded, useIn, useMark, useRamp } from "../kit";

export const CellBuild: React.FC = () => {
  const f = useCurrentFrame();
  const badge = useIn("badge");
  const mem = useRamp("membrane", 30);
  const cyto = useRamp("cytoplasm", 20);
  const nuc = useIn("nucleus");
  const plantT = useRamp("plant", 30, 8, Easing.inOut);
  const intro = useIn("badge", 6) * (1 - useRamp("membrane", 12));
  const wall = useRamp("wall", 26);
  const vac = useRamp("vacuole", 30, 0, Easing.out);
  const remember = useIn("remember");
  const tease = useIn("tease");
  const labels = 1 - useRamp("plant", 10, -6);
  // animal cell moves left and shrinks when the plant cell arrives
  const ax = interpolate(plantT, [0, 1], [760, 400]);
  const as = interpolate(plantT, [0, 1], [1, 0.62]);
  const R = 230;
  const rnd = seeded(5);
  const gran = Array.from({ length: 26 }, () => ({ a: rnd() * Math.PI * 2, d: 0.25 + rnd() * 0.65 }));
  const circ = 2 * Math.PI * R;
  return (
    <g>
      <g opacity={1 - useRamp("plant", 14)}><Chip x={960} y={168} text="⏱  60 sec ka zaroori revision" color={C.violet} p={badge} size={32} /></g>
      {intro > 0 && (
        <g opacity={Math.min(1, intro)}>
          <circle cx={760} cy={580} r={230} fill="none" stroke={C.dim} strokeWidth={4} strokeDasharray="16 14" />
          <text x={760} y={590} textAnchor="middle" fill={C.soft} fontSize={44} fontWeight={800}>Cell = life ki unit</text>
          <text x={1300} y={560} fill={C.ink} fontSize={46} fontWeight={800}>Aaj ka pura topic</text>
          <text x={1300} y={620} fill={C.violet} fontSize={46} fontWeight={800}>cell par khada hai</text>
        </g>
      )}
      {/* animal / basic cell */}
      <g transform={`translate(${ax},580) scale(${as})`}>
        <circle r={R} fill={C.cyto} opacity={cyto * 0.95} />
        {gran.map((g, i) => <circle key={i} cx={Math.cos(g.a) * g.d * R} cy={Math.sin(g.a) * g.d * R} r={6} fill="#D97706" opacity={cyto * 0.5} />)}
        <circle r={R} fill="none" stroke="#F59E0B" strokeWidth={10} strokeDasharray={circ} strokeDashoffset={circ * (1 - mem)} />
        <g transform={`scale(${Math.min(1.1, nuc)})`} opacity={Math.min(1, nuc)}>
          <circle r={72} fill={C.nucleus} />
          <circle cx={-18} cy={-14} r={24} fill="#C4B5FD" />
        </g>
        <text y={R + 70} textAnchor="middle" fill={C.soft} fontSize={44} fontWeight={700} opacity={plantT}>Animal cell</text>
      </g>
      <g opacity={labels}>
        <Leader p={useRamp("membrane", 24, 10)} from={[760 + R * 0.72, 580 - R * 0.69]} to={[1180, 300]} text="Cell membrane" color="#F59E0B" sub="bahar ki parat" />
        <Leader p={useRamp("cytoplasm", 24, 4)} from={[760 + 120, 580 + 110]} to={[1180, 760]} text="Cytoplasm" color={C.amber} sub="andar ka jelly jaisa hissa" />
        <Leader p={useRamp("nucleus", 24, 4)} from={[760 + 60, 580]} to={[1180, 530]} text="Nucleus" color={C.violet} sub="control centre" />
      </g>
      {/* plant cell */}
      {plantT > 0 && (
        <g transform={`translate(1150,580) scale(${0.85 + 0.15 * plantT})`} opacity={plantT}>
          <rect x={-300 - 26 * wall} y={-220 - 26 * wall} width={600 + 52 * wall} height={440 + 52 * wall} rx={34} fill={C.wall} opacity={wall} />
          <rect x={-300} y={-220} width={600} height={440} rx={26} fill={C.cyto} stroke="#F59E0B" strokeWidth={8} />
          <ellipse cx={60} cy={0} rx={210 * vac} ry={150 * vac} fill="#BAE6FD" stroke="#38BDF8" strokeWidth={5}
            filter={remember > 0.5 ? "url(#glow)" : undefined} opacity={0.95} />
          <g transform={`translate(${interpolate(vac, [0, 1], [0, -205])},${interpolate(vac, [0, 1], [0, -110])})`}>
            <circle r={58} fill={C.nucleus} />
            <circle cx={-14} cy={-12} r={20} fill="#C4B5FD" />
          </g>
          <text y={300} textAnchor="middle" fill={C.soft} fontSize={44} fontWeight={700}>Plant cell</text>
        </g>
      )}
      <Leader p={useRamp("wall", 24, 8)} from={[1150 + 300 + 20, 580 - 160]} to={[1560, 250]} text="Cell wall" color={C.leaf} sub="mazboot bahari deewar" />
      <Leader p={useRamp("vacuole", 24, 10)} from={[1150 + 200, 580 + 60]} to={[1560, 900]} text="Bada vacuole" color={C.sky} sub="cell ka bada hissa ghere" />
      {remember > 0 && (
        <g transform={`translate(560,${905 - remember * 8}) rotate(-3)`} opacity={Math.min(1, remember)}>
          <rect x={-250} y={-58} width={500} height={110} rx={14} fill="#FEF08A" />
          <text x={0} y={-6} textAnchor="middle" fill="#713F12" fontSize={34} fontWeight={800}>📌 Yaad rakho:</text>
          <text x={0} y={36} textAnchor="middle" fill="#713F12" fontSize={34} fontWeight={800}>Plant cell = bada vacuole</text>
        </g>
      )}
      {tease > 0 && (
        <g transform={`translate(1150,${170})`} opacity={Math.min(1, tease)}>
          <text x={0} y={0} textAnchor="middle" fill={C.coral} fontSize={42} fontWeight={800} opacity={pulse(f, 30, 0.7)}>…par kuch cells mein vacuole hota hi nahi!</text>
        </g>
      )}
    </g>
  );
};
