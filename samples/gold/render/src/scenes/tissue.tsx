import React from "react";
import { Easing, interpolate, useCurrentFrame } from "../lite";
import { C, Card, Cell, Chip, Rise, Stamp, pulse, seeded, useIn, useMark, useRamp } from "../kit";

export const TissueTeam: React.FC = () => {
  const f = useCurrentFrame();
  const q = useIn(0, 4);
  const gather = useRamp("gather", 50, 0, Easing.inOut);
  const lock = useIn("lock");
  const twoKinds = useIn("plantT");
  const animalT = useIn("animalT");
  const labour = useIn("labour");
  const jobs = [useIn("j1"), useIn("j2"), useIn("j3")];
  const overload = useIn("overload");
  const share = useRamp("share", 40, 0, Easing.inOut);
  const workload = useIn("workload");
  const org = useIn("organisation");
  const phase1 = 1 - useRamp("plantT", 12, -14);
  const phase2 = useRamp("plantT", 12) * (1 - useRamp("labour", 12, -14));
  const phase3 = useRamp("labour", 12);
  const rnd = seeded(11);
  const loose = Array.from({ length: 20 }, () => ({ x: 260 + rnd() * 1400, y: 300 + rnd() * 560, ph: rnd() * 6, odd: rnd() > 0.72 }));
  return (
    <g>
      {phase1 > 0 && (
        <g opacity={phase1}>
          <Rise p={q} x={960} y={200} size={56} anchor="middle">Tissue kya hai?</Rise>
          {loose.map((c, i) => {
            const col = i % 5, row = Math.floor(i / 5);
            const tx = 760 + col * 100, ty = 470 + row * 100;
            const target = !c.odd;
            const x = target ? interpolate(gather, [0, 1], [c.x + Math.sin(f / 30 + c.ph) * 18, tx]) : c.x + Math.sin(f / 30 + c.ph) * 18;
            const y = target ? interpolate(gather, [0, 1], [c.y + Math.cos(f / 34 + c.ph) * 14, ty]) : c.y + Math.cos(f / 34 + c.ph) * 14;
            return <Cell key={i} x={x} y={y} r={target ? 46 : 38} shape={target ? "hex" : "round"} fill={target ? "#BBF7D0" : "#FBCFE8"} edge={target ? "#16A34A" : "#DB2777"}
              nucleus={0.3} seed={i} opacity={target ? 1 : 1 - gather * 0.6} />;
          })}
          {lock > 0 && <>
            <rect x={690} y={400} width={540} height={440} rx={30} fill="none" stroke={C.leaf} strokeWidth={6} strokeDasharray="20 12" opacity={Math.min(1, lock)} />
            <g transform={`translate(960,${960 - lock * 8})`} opacity={Math.min(1, lock)}>
              <rect x={-640} y={-56} width={1280} height={96} rx={48} fill={C.leaf} opacity={0.14} />
              <text x={0} y={8} textAnchor="middle" fill={C.ink} fontSize={42} fontWeight={800}>TISSUE = ek jaisa kaam karne wali cells ka group</text>
            </g>
          </>}
        </g>
      )}
      {phase2 > 0 && (
        <g opacity={phase2}>
          <Card x={180} y={250} w={700} h={620} p={twoKinds} title="Plant cells → Plant tissue" color={C.leaf}>
            {Array.from({ length: 12 }, (_, i) => <Cell key={i} x={170 + (i % 4) * 120} y={200 + Math.floor(i / 4) * 120} r={52} shape="rect" wall={8}
              fill="#D9F99D" edge="#65A30D" vacuole={0.45} nucleus={0.18} nucleusX={-26} nucleusY={-22} seed={i} />)}
          </Card>
          <Card x={1040} y={250} w={700} h={620} p={animalT} title="Animal cells → Animal tissue" color={C.coral}>
            {Array.from({ length: 12 }, (_, i) => <Cell key={i} x={170 + (i % 4) * 120} y={200 + Math.floor(i / 4) * 120} r={52} shape="round"
              fill="#FBCFE8" edge="#DB2777" nucleus={0.3} seed={i + 20} />)}
          </Card>
        </g>
      )}
      {phase3 > 0 && (
        <g opacity={phase3}>
          <Chip x={960} y={180} text="Division of labour" color={C.amber} p={labour} size={40} />
          {/* lone overloaded cell */}
          <g opacity={1 - share}>
            <Cell x={700} y={580} r={130 + overload * 8 * Math.sin(f / 3)} fill={overload > 0.5 ? "#FECDD3" : C.cyto} edge={overload > 0.5 ? C.red : "#F59E0B"} nucleus={0.3} granules={14} />
            {[["🍃", "Khana banana"], ["📦", "Store karna"], ["🚚", "Transport"]].map(([icon, t], i) => {
              const a = (f / 40 + i * 2.09);
              const p = jobs[i];
              return (
                <g key={i} opacity={Math.min(1, p)} transform={`translate(${700 + Math.cos(a) * 250},${580 + Math.sin(a) * 200})`}>
                  <circle r={54} fill="rgba(255,255,255,0.08)" stroke={C.cardLine} strokeWidth={2} />
                  <text y={18} textAnchor="middle" fontSize={50}>{icon}</text>
                  <text y={92} textAnchor="middle" fill={C.ink} fontSize={28} fontWeight={700}>{t}</text>
                </g>
              );
            })}
            <g transform="translate(1320,420)">
              <text x={0} y={0} fill={C.soft} fontSize={34} fontWeight={700}>Workload</text>
              <rect x={0} y={24} width={420} height={44} rx={22} fill="rgba(255,255,255,0.08)" />
              <rect x={0} y={24} width={420 * Math.min(1, 0.25 + 0.25 * (jobs[0] + jobs[1] + jobs[2]) / 1.2)} height={44} rx={22} fill={overload > 0.5 ? C.red : C.amber} />
            </g>
            <Stamp x={1520} y={640} text="OVERLOAD!" color={C.red} p={overload} size={60} />
          </g>
          {/* team: three groups */}
          {share > 0 && (
            <g opacity={share}>
              {[["🍃", "Khana banana", C.leaf], ["📦", "Store karna", C.amber], ["🚚", "Transport", C.sky]].map(([icon, t, col], g) => (
                <g key={g} transform={`translate(${380 + g * 400},${560 + (1 - share) * 60})`}>
                  {Array.from({ length: 6 }, (_, i) => <Cell key={i} x={-90 + (i % 3) * 90} y={-60 + Math.floor(i / 3) * 90} r={42} shape="hex"
                    fill="#F1F5F9" edge={col as string} nucleus={0.28} seed={g * 10 + i} />)}
                  <text x={0} y={-140} textAnchor="middle" fontSize={56}>{icon}</text>
                  <text x={0} y={140} textAnchor="middle" fill={col as string} fontSize={34} fontWeight={800}>{t}</text>
                </g>
              ))}
              <g transform="translate(1520,420)">
                <text x={0} y={0} fill={C.soft} fontSize={34} fontWeight={700}>Har cell ka workload</text>
                <rect x={0} y={24} width={300} height={44} rx={22} fill="rgba(255,255,255,0.08)" />
                <rect x={0} y={24} width={300 * interpolate(workload, [0, 1], [0.9, 0.3])} height={44} rx={22} fill={C.green} />
                <text x={0} y={120} fill={C.green} fontSize={40} fontWeight={800} opacity={Math.min(1, workload)}>↓ kam</text>
              </g>
              <Chip x={960} y={900} text="✓ Organisation" color={C.green} p={org} size={44} solid />
            </g>
          )}
        </g>
      )}
    </g>
  );
};

export const Ladder: React.FC = () => {
  const f = useCurrentFrame();
  const steps: [string, string, string][] = [["l-cell", "Cell", "🔬"], ["l-tissue", "Tissue", "🧩"], ["l-organ", "Organ", "🍃❤️"], ["l-system", "Organ system", "🌿🫁"], ["l-organism", "Organism", "🌳🧍"]];
  const ps = steps.map(([m]) => useIn(m, 0, 150));
  const trap = useIn("trap");
  const recite = useIn("recite");
  return (
    <g>
      <Rise p={useIn(0, 4)} x={960} y={190} size={54} anchor="middle">Organisation ki seedhi</Rise>
      {steps.map(([m, label, icon], i) => {
        const x = 230 + i * 330, y = 900 - i * 100;
        const p = Math.min(1, ps[i]);
        return (
          <g key={m} opacity={0.25 + 0.75 * p} transform={`translate(${x},${y})`}>
            <rect x={-140} y={-10} width={300} height={1080 - y} fill={i % 2 ? "#123049" : "#163a57"} opacity={0.9} />
            <rect x={-140} y={-14} width={300} height={10} rx={5} fill={p > 0.5 ? C.sky : C.dim} />
            <g transform={`translate(10,${-90 - p * 20}) scale(${0.7 + 0.3 * p})`}>
              <text x={0} y={0} textAnchor="middle" fontSize={84}>{icon}</text>
            </g>
            <text x={10} y={60} textAnchor="middle" fill={p > 0.5 ? C.ink : C.dim} fontSize={40} fontWeight={800}>{label}</text>
            {i < 4 && p > 0.5 && <text x={175} y={-40} fill={C.sky} fontSize={56} fontWeight={900} opacity={Math.min(1, ps[i + 1] * 3)}>→</text>}
          </g>
        );
      })}
      {trap > 0 && (
        <g opacity={Math.min(1, trap) * (1 - Math.min(1, recite))}>
          <rect x={310} y={230} width={1100} height={110} rx={24} fill={C.coral} opacity={0.14} stroke={C.coral} strokeWidth={3} />
          <text x={860} y={300} textAnchor="middle" fill={C.ink} fontSize={40} fontWeight={700}>Tissue → Cell → Organ system → Organ ?</text>
          <Stamp x={1300} y={240} text="TRAP" color={C.coral} p={trap} size={40} />
        </g>
      )}
      {recite > 0 && (
        <g opacity={Math.min(1, recite)}>
          <rect x={310} y={220} width={1100} height={140} rx={24} fill={C.green} opacity={0.14} stroke={C.green} strokeWidth={3} />
          <text x={860} y={274} textAnchor="middle" fill={C.green} fontSize={32} fontWeight={800}>Chhote se bade ✓</text>
          <text x={860} y={330} textAnchor="middle" fill={C.ink} fontSize={36} fontWeight={800}>Cell → Tissue → Organ → Organ system → Organism</text>
        </g>
      )}
    </g>
  );
};
