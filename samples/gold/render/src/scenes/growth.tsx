import React from "react";
import { Easing, interpolate, useCurrentFrame } from "../lite";
import { C, Cell, Chip, CheckRow, Rise, Stamp, pulse, seeded, useIn, useMark, useRamp } from "../kit";
import { Human, Plant } from "./plant";

export const GrowthCompare: React.FC = () => {
  const f = useCurrentFrame();
  const human = useRamp("human", 90, 0, Easing.inOut);
  const stop = useIn("stop");
  const tree = useRamp("tree", 160, 0, Easing.inOut);
  const tips = useIn("tips");
  const engine = useIn("engine");
  const map = useIn("map");
  const mer = useIn("map-mer");
  const perm = useIn("map-perm");
  const focus = useIn("focus");
  const part1 = 1 - useRamp("map", 18);
  const ages = [5, 10, 15, 20, 40];
  return (
    <g>
      {part1 > 0 && (
        <g opacity={part1}>
          <Rise p={useIn(0, 4)} x={960} y={190} size={54} anchor="middle">Insaan vs ped: badhna kab tak?</Rise>
          {/* humans by age */}
          <g>
            {ages.map((a, i) => {
              const h = [220, 300, 380, 420, 420][i];
              const p = Math.min(1, Math.max(0, human * 5 - i));
              return (
                <g key={a} opacity={p}>
                  <Human x={170 + i * 130} foot={880} h={h * (0.9 + 0.1 * p)} color="#93C5FD" />
                  <text x={170 + i * 130} y={930} textAnchor="middle" fill={C.soft} fontSize={30} fontWeight={700}>{a} saal</text>
                </g>
              );
            })}
            <line x1={120} y1={880 - 420 - 8} x2={800} y2={880 - 420 - 8} stroke={C.coral} strokeWidth={4} strokeDasharray="14 10" opacity={Math.min(1, stop)} />
            <Chip x={720} y={420} text="Lambai: STOP" color={C.coral} p={stop} size={30} solid />
          </g>
          {/* tree keeps growing */}
          <g opacity={Math.min(1, tree * 4)}>
            <Plant x={1400} ground={780} height={interpolate(tree, [0, 1], [200, 470])} root={interpolate(tree, [0, 1], [80, 200])}
              apical={Math.min(1, tips)} leafScale={interpolate(tree, [0, 1], [0.6, 1])} />
            <text x={1400} y={1050} textAnchor="middle" fill={C.leaf} fontSize={30} fontWeight={800} opacity={Math.min(1, tree * 3) * (1 - Math.min(1, engine))}>Ped: poori zindagi badhta rehta hai</text>
          </g>
          {engine > 0 && (
            <g transform={`translate(760,${1005})`} opacity={Math.min(1, engine)}>
              <rect x={-330} y={-50} width={660} height={84} rx={42} fill={C.amber} opacity={0.18} stroke={C.amber} strokeWidth={3} />
              <text x={0} y={6} textAnchor="middle" fill={C.amber} fontSize={38} fontWeight={900}>Meristematic tissue = growth engine</text>
            </g>
          )}
        </g>
      )}
      {map > 0 && (
        <g opacity={Math.min(1, map)}>
          <Rise p={map} x={960} y={190} size={54} anchor="middle">Plant tissue ka map</Rise>
          {/* root node */}
          <g transform="translate(960,290)">
            <rect x={-200} y={-44} width={400} height={80} rx={20} fill={C.sky} opacity={0.2} stroke={C.sky} strokeWidth={3} />
            <text y={12} textAnchor="middle" fill={C.ink} fontSize={38} fontWeight={800}>Plant tissue</text>
          </g>
          <path d="M960,330 L960,370 L520,370 L520,420 M960,370 L1400,370 L1400,420" stroke={C.dim} strokeWidth={4} fill="none" opacity={Math.min(1, Math.max(mer, perm))} />
          {/* meristematic branch */}
          <g opacity={Math.min(1, mer)}>
            <g transform="translate(520,470)">
              <rect x={-230} y={-44} width={460} height={80} rx={20} fill={C.leaf} opacity={0.2 + 0.15 * focus} stroke={C.leaf} strokeWidth={focus > 0.5 ? 6 : 3} />
              <text y={12} textAnchor="middle" fill={C.ink} fontSize={36} fontWeight={800}>Meristematic</text>
            </g>
            <text x={520} y={560} textAnchor="middle" fill={C.leaf} fontSize={28} fontWeight={600}>divide hote rehte hain</text>
            <path d="M520,580 L520,620 L260,620 L260,660 M520,620 L520,660 M520,620 L780,620 L780,660" stroke={C.dim} strokeWidth={4} fill="none" />
            {["Apical", "Intercalary", "Lateral"].map((t, i) => (
              <g key={t} transform={`translate(${260 + i * 260},700)`}>
                <rect x={-115} y={-36} width={230} height={66} rx={16} fill="rgba(255,255,255,0.06)" stroke={C.leaf} strokeWidth={2} />
                <text y={10} textAnchor="middle" fill={C.ink} fontSize={30} fontWeight={700}>{t}</text>
              </g>
            ))}
          </g>
          {/* permanent branch */}
          <g opacity={Math.min(1, perm) * (1 - 0.65 * Math.min(1, focus))}>
            <g transform="translate(1400,470)">
              <rect x={-230} y={-44} width={460} height={80} rx={20} fill={C.violet} opacity={0.2} stroke={C.violet} strokeWidth={3} />
              <text y={12} textAnchor="middle" fill={C.ink} fontSize={36} fontWeight={800}>Permanent</text>
            </g>
            <text x={1400} y={560} textAnchor="middle" fill={C.violet} fontSize={28} fontWeight={600}>divide band, pakka kaam</text>
            <path d="M1400,580 L1400,620 L1220,620 L1220,660 M1400,620 L1580,620 L1580,660" stroke={C.dim} strokeWidth={4} fill="none" />
            <g transform="translate(1220,700)"><rect x={-130} y={-36} width={260} height={66} rx={16} fill="rgba(255,255,255,0.06)" stroke={C.violet} strokeWidth={2} />
              <text y={10} textAnchor="middle" fill={C.ink} fontSize={30} fontWeight={700}>Simple</text></g>
            <g transform="translate(1580,700)"><rect x={-130} y={-36} width={260} height={66} rx={16} fill="rgba(255,255,255,0.06)" stroke={C.violet} strokeWidth={2} />
              <text y={10} textAnchor="middle" fill={C.ink} fontSize={30} fontWeight={700}>Complex</text></g>
            <text x={1220} y={790} textAnchor="middle" fill={C.soft} fontSize={24}>Parenchyma · Collenchyma · Sclerenchyma</text>
            <text x={1580} y={830} textAnchor="middle" fill={C.soft} fontSize={24}>Xylem · Phloem</text>
          </g>
          {focus > 0 && <Chip x={520} y={880} text="★ Aaj ka focus" color={C.amber} p={focus} size={40} solid />}
        </g>
      )}
    </g>
  );
};

export const MeristemZoom: React.FC = () => {
  const f = useCurrentFrame();
  const zoom = useRamp("zoom", 40, 0, Easing.inOut);
  const shapes = useIn("shapes");
  const packed = useIn("packed");
  const spaces = useIn("spaces");
  const compact = useIn("compact");
  const vac = useIn("vac");
  const novac = useIn("novac");
  const bignuc = useRamp("bignuc", 25);
  const dividing = useRamp("dividing", 10);
  const active = useIn("active");
  const checks = ["c1", "c2", "c3", "c4"].map((m) => useIn(m, 0, 150));
  const checklistMode = useRamp("c1", 20, -20);
  const rnd = seeded(31);
  const cells = Array.from({ length: 30 }, (_, i) => ({ i, col: i % 6, row: Math.floor(i / 6), shape: (["round", "oval", "rect"] as const)[Math.floor(rnd() * 3)], d: rnd() }));
  const gx = interpolate(checklistMode, [0, 1], [1170, 700]);
  const gs = interpolate(checklistMode, [0, 1], [1, 0.78]);
  return (
    <g>
      {/* root tip outline on the left */}
      <g opacity={1 - checklistMode}>
        <path d="M250,250 L250,640 Q250,760 330,820 Q410,760 410,640 L410,250" fill="#FDE68A" stroke="#A16207" strokeWidth={6} />
        {[320, 400, 480, 560, 640].map((y) => <line key={y} x1={256} y1={y} x2={404} y2={y} stroke="#D6A84F" strokeWidth={2} opacity={0.7} />)}
        {[300, 360].map((x) => <line key={x} x1={x} y1={252} x2={x} y2={700} stroke="#D6A84F" strokeWidth={2} opacity={0.7} />)}
        <path d="M262,700 Q262,790 330,830 Q398,790 398,700 Q330,740 262,700 Z" fill="#D97706" opacity={0.8} />
        <text x={430} y={800} fill={C.soft} fontSize={26} fontWeight={600}>root cap</text>
        <circle cx={330} cy={740} r={48 + zoom * 6} fill="none" stroke={C.amber} strokeWidth={6} opacity={0.4 + 0.6 * zoom} />
        <text x={330} y={900} textAnchor="middle" fill={C.soft} fontSize={32} fontWeight={700}>Root tip</text>
        <line x1={378} y1={740} x2={interpolate(zoom, [0, 1], [378, 640])} y2={interpolate(zoom, [0, 1], [740, 560])} stroke={C.amber} strokeWidth={4} strokeDasharray="12 8" />
      </g>
      {/* magnified tissue */}
      <g transform={`translate(${gx},575) scale(${(0.3 + 0.55 * zoom) * gs})`} opacity={zoom}>
        <circle r={430} fill="#0b2a20" stroke={C.amber} strokeWidth={8} />
        <clipPath id="lens"><circle r={422} /></clipPath>
        <g clipPath="url(#lens)">
          {cells.map((c) => {
            const x = -330 + c.col * 132, y = -330 + c.row * 132;
            const div = dividing > 0 && (c.i * 7) % 5 === Math.floor(f / 18) % 5;
            const sx = div ? 1 + 0.25 * Math.sin((f % 18) / 18 * Math.PI) : 1;
            const ghost = vac * (1 - novac);
            return (
              <g key={c.i} transform={`translate(${x},${y}) scale(${sx},${1 / sx})`}>
                <Cell x={0} y={0} r={64} shape={c.shape === "oval" ? "round" : c.shape} fill="#FEF3C7" edge="#B45309" nucleus={0.34 + 0.12 * bignuc} granules={8} seed={c.i} />
                {ghost > 0 && <circle r={34} fill="#BAE6FD" opacity={ghost * 0.85} />}
              </g>
            );
          })}
          {shapes > 0 && packed < 1 && (
            <g opacity={Math.min(1, shapes) * (1 - Math.min(1, spaces))}>
              {[[-330, -330, "gol"], [-66, -198, "oval"], [198, -66, "rectangular"]].map(([x, y, t], i) => (
                <g key={i}>
                  <circle cx={x as number} cy={y as number} r={72} fill="none" stroke={C.sky} strokeWidth={6} />
                  <text x={x as number} y={(y as number) + 112} textAnchor="middle" fill={C.sky} fontSize={34} fontWeight={800}>{t}</text>
                </g>
              ))}
            </g>
          )}
        </g>
        {novac > 0 && <Stamp x={0} y={-60} text="VACUOLE ✗" color={C.red} p={novac} size={70} />}
        {active > 0 && <Stamp x={0} y={250} text="MOST ACTIVE" color={C.amber} p={active} rotate={4} size={56} />}
      </g>
      {/* explanation text on the left before checklist */}
      <g opacity={1 - checklistMode}>
        {packed > 0 && <g opacity={1 - Math.min(1, spaces)}><Rise p={packed} x={90} y={970} size={38} color={C.ink}>Chhoti cells, ek-doosre se sati hui</Rise></g>}
        {spaces > 0 && (
          <g opacity={Math.min(1, spaces)} transform="translate(90,950)">
            <text x={0} y={0} fill={C.soft} fontSize={34} fontWeight={700}>Intercellular spaces:</text>
            <text x={350} y={0} fill={C.red} fontSize={40} fontWeight={900}>ABSENT</text>
            <text x={0} y={56} fill={C.leaf} fontSize={38} fontWeight={800} opacity={Math.min(1, compact)}>→ compactly packed</text>
          </g>
        )}
      </g>
      {checklistMode > 0 && (
        <g opacity={checklistMode}>
          <Rise p={checklistMode} x={1180} y={230} size={42} color={C.leaf}>Checklist: meristematic tissue</Rise>
          <CheckRow x={1260} y={340} p={checks[0]} k="Kahan" v="Growing regions (root, shoot)" />
          <CheckRow x={1260} y={490} p={checks[1]} k="Intercellular spaces" v="Absent → compactly packed" />
          <CheckRow x={1260} y={640} p={checks[2]} k="Vacuole" v="Absent" />
          <CheckRow x={1260} y={790} p={checks[3]} k="Kaam" v="Sirf cell division" />
        </g>
      )}
    </g>
  );
};
