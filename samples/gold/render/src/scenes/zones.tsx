import React from "react";
import { Easing, interpolate, useCurrentFrame } from "../lite";
import { C, Card, Cell, Chip, DrawPath, Leader, Rise, Stamp, pulse, useIn, useMark, useRamp, useScene, wrap, Lines } from "../kit";
import { Plant } from "./plant";
import { GrassPatch, TrunkSection } from "./hook";

const Title: React.FC<{ n: string; name: string; meaning: string; color: string; p: number }> = ({ n, name, meaning, color, p }) => (
  <g opacity={Math.min(1, p)} transform={`translate(110,${210 + (1 - Math.min(1, p)) * 20})`}>
    <circle cx={34} cy={-16} r={34} fill={color} />
    <text x={34} y={-4} textAnchor="middle" fill={C.bg0} fontSize={40} fontWeight={900}>{n}</text>
    <text x={90} y={0} fill={C.ink} fontSize={58} fontWeight={900}>{name}</text>
    <text x={92} y={56} fill={color} fontSize={34} fontWeight={700}>{meaning}</text>
  </g>
);

export const PlantZones: React.FC = () => {
  const { zone } = useScene();
  if (zone === "lateral") return <Lateral />;
  if (zone === "intercalary") return <Intercalary />;
  return <Apical />;
};

const Apical: React.FC = () => {
  const f = useCurrentFrame();
  const three = useIn("three");
  const label = useIn("label");
  const shoot = useIn("shootTip");
  const root = useIn("rootTip");
  const grow = useRamp("grow", 120, 0, Easing.inOut);
  const up = useIn("up");
  const down = useIn("down");
  const H = 400 + 90 * grow, R = 190 + 60 * grow;
  return (
    <g>
      <g opacity={Math.min(1, three)}>
        {["Apical", "Lateral", "Intercalary"].map((t, i) => <Chip key={t} x={1380 + (i - 1) * 0} y={300 + i * 70} text={`${i + 1}. ${t}`} color={i === 0 ? C.amber : C.dim} p={three} size={30} />)}
      </g>
      <Title n="1" name="Apical meristem" meaning="Apex = tip (sira)" color={C.amber} p={label} />
      <Plant x={760} ground={720} height={H} root={R} apical={Math.max(Math.min(1, shoot), Math.min(1, root))} />
      <Leader p={useRamp("shootTip", 24)} from={[760, 720 - H - 6]} to={[1000, 720 - H - 40]} text="Shoot tip" color={C.amber} />
      <Leader p={useRamp("rootTip", 24)} from={[760, 720 + R]} to={[1000, 720 + R - 10]} text="Root tip" color={C.amber} />
      {up > 0 && <g opacity={Math.min(1, up)}><DrawPath d={`M 680 ${720 - H + 80} L 680 ${720 - H - 40}`} p={up} color={C.leaf} width={10} length={130} /></g>}
      {down > 0 && <g opacity={Math.min(1, down)}><DrawPath d={`M 680 ${720 + R - 80} L 680 ${720 + R + 30}`} p={down} color={C.leaf} width={10} length={120} /></g>}
      <g opacity={Math.min(1, useIn("grow"))} transform="translate(1180,840)">
        <rect x={0} y={-60} width={620} height={110} rx={24} fill={C.amber} opacity={0.14} stroke={C.amber} strokeWidth={3} />
        <text x={30} y={10} fill={C.ink} fontSize={36} fontWeight={800}>Kaam: shoot ↑ aur root ↓ ki lambai</text>
      </g>
    </g>
  );
};

const Lateral: React.FC = () => {
  const f = useCurrentFrame();
  const label = useIn("label");
  const bark = useIn("bark");
  const ring = useIn("ring");
  const thick = useMark("thick");
  const girth = useIn("girth");
  const answer = useIn("answer");
  return (
    <g>
      <Title n="2" name="Lateral meristem" meaning="Lateral = side (bagal)" color={C.leaf} p={label} />
      <Plant x={430} ground={800} height={480} root={160} lateral={Math.min(1, ring)} leafScale={0.85} />
      <Leader p={useRamp("bark", 24)} from={[443, 560]} to={[620, 470]} text="Bark ke neeche" color={C.leaf} size={32} />
      {/* cross-section of the stem */}
      <g opacity={Math.min(1, bark)}>
        <line x1={460} y1={600} x2={1060} y2={560} stroke={C.dim} strokeWidth={3} strokeDasharray="10 8" />
        <text x={1330} y={250} textAnchor="middle" fill={C.soft} fontSize={34} fontWeight={700}>Tane ka cross-section</text>
        <TrunkSection cx={1330} cy={580} at={thick} maxRings={8} glow={Math.min(1, ring)} />
      </g>
      {ring > 0 && <Leader p={useRamp("ring", 24)} from={[1330 + 128, 580 - 30]} to={[1590, 400]} text="Lateral meristem" color={C.leaf} size={30} sub="bark ke neeche ghera" />}
      {girth > 0 && (
        <g opacity={Math.min(1, girth)}>
          <DrawPath d="M 1090 860 L 1570 860" p={girth} color={C.amber} width={8} length={480} />
          <DrawPath d="M 1570 860 L 1090 860" p={girth} color={C.amber} width={8} length={480} />
          <text x={1330} y={930} textAnchor="middle" fill={C.amber} fontSize={42} fontWeight={900}>Girth (motai) ↑</text>
        </g>
      )}
      {answer > 0 && (
        <g transform={`translate(430,1000)`} opacity={Math.min(1, answer)}>
          <rect x={-330} y={-50} width={660} height={80} rx={40} fill={C.green} opacity={0.18} stroke={C.green} strokeWidth={3} />
          <text x={0} y={4} textAnchor="middle" fill={C.ink} fontSize={32} fontWeight={800}>✓ Paheli ka jawab #1: tana mota kyon</text>
        </g>
      )}
    </g>
  );
};

const Intercalary: React.FC = () => {
  const f = useCurrentFrame();
  const label = useIn("label");
  const base = useIn("base");
  const internode = useIn("internode");
  const stretch = useRamp("stretch", 90, 0, Easing.inOut);
  const grass = useRamp("grass", 20);
  const zone = useIn("zone");
  const plantPart = 1 - grass;
  return (
    <g>
      <Title n="3" name="Intercalary meristem" meaning="Inter = beech mein" color={C.sky} p={label} />
      {plantPart > 0 && (
        <g opacity={plantPart}>
          <Plant x={760} ground={900} height={560 + 110 * stretch} root={60} intercalary={Math.min(1, base)} leafScale={0.95} />
          <Leader p={useRamp("base", 24)} from={[778, 900 - (560 + 110 * stretch) * 0.55 - 20]} to={[1050, 520]} text="Leaf ka base / internode" color={C.amber} size={34} />
          {internode > 0 && (
            <g opacity={Math.min(1, internode)}>
              <line x1={700} y1={900 - (560 + 110 * stretch) * 0.3} x2={700} y2={900 - (560 + 110 * stretch) * 0.55} stroke={C.sky} strokeWidth={6} />
              <line x1={688} y1={900 - (560 + 110 * stretch) * 0.3} x2={712} y2={900 - (560 + 110 * stretch) * 0.3} stroke={C.sky} strokeWidth={6} />
              <line x1={688} y1={900 - (560 + 110 * stretch) * 0.55} x2={712} y2={900 - (560 + 110 * stretch) * 0.55} stroke={C.sky} strokeWidth={6} />
              <text x={676} y={900 - (560 + 110 * stretch) * 0.43} textAnchor="end" fill={C.sky} fontSize={32} fontWeight={800}>Internode</text>
              <text x={676} y={900 - (560 + 110 * stretch) * 0.43 + 38} textAnchor="end" fill={C.soft} fontSize={26} fontWeight={600}>(do nodes ke beech)</text>
            </g>
          )}
          {stretch > 0 && <g transform="translate(1180,800)" opacity={Math.min(1, stretch * 3)}>
            <rect x={0} y={-60} width={640} height={110} rx={24} fill={C.sky} opacity={0.14} stroke={C.sky} strokeWidth={3} />
            <text x={30} y={10} fill={C.ink} fontSize={36} fontWeight={800}>Kaam: leaves, internodes ki lambai</text>
          </g>}
        </g>
      )}
      {grass > 0 && (
        <g opacity={grass}>
          <Rise p={grass} x={1000} y={330} size={48} anchor="middle" color={C.amber}>Ghaas wali paheli</Rise>
          <g transform="translate(240,0)">
            <GrassPatch x0={260} x1={1180} mowAt={useMark("cut")} regrowAt={useMark("regrow")} showBase={Math.min(1, zone)} seed={9} />
          </g>
          {zone > 0 && <Leader p={useRamp("zone", 24)} from={[700, 826]} to={[480, 980]} text="Growth zone: neeche base par" color={C.amber} size={34} anchor="start" />}
          {useIn("regrow") > 0 && (
            <g transform="translate(1440,560)" opacity={Math.min(1, useIn("regrow"))}>
              <rect x={-300} y={-50} width={600} height={80} rx={40} fill={C.green} opacity={0.18} stroke={C.green} strokeWidth={3} />
              <text x={0} y={4} textAnchor="middle" fill={C.ink} fontSize={32} fontWeight={800}>✓ Paheli ka jawab #2</text>
            </g>
          )}
        </g>
      )}
    </g>
  );
};

export const SummaryTable: React.FC = () => {
  const { marks } = useScene();
  const table = useIn("table");
  const rows = [useIn("sum-2:row"), useIn("sum-3:row"), useIn("sum-4:row")];
  const data: [string, string, string, string][] = [
    ["Apical", "Root aur shoot ki tip", "Lambai", C.amber],
    ["Lateral", "Bark ke neeche", "Girth (motai)", C.leaf],
    ["Intercalary", "Leaves ka base / internodes", "Leaves, internodes ki lambai", C.sky],
  ];
  return (
    <g>
      <Rise p={table} x={960} y={200} size={56} anchor="middle">Meristem: ek nazar mein</Rise>
      <g opacity={Math.min(1, table)}>
        {["Type", "Kahan", "Kya badhata hai"].map((h, i) => <text key={h} x={[180, 640, 1240][i]} y={320} fill={C.soft} fontSize={36} fontWeight={800}>{h}</text>)}
        <line x1={150} y1={345} x2={1770} y2={345} stroke={C.cardLine} strokeWidth={3} />
      </g>
      {data.map(([t, where, what, col], i) => {
        const p = Math.min(1, rows[i]);
        const y = 450 + i * 170;
        return (
          <g key={t} opacity={p} transform={`translate(${(1 - p) * 60},0)`}>
            <rect x={150} y={y - 80} width={1620} height={140} rx={26} fill={col} opacity={0.1} />
            <rect x={150} y={y - 80} width={12} height={140} rx={6} fill={col} />
            <text x={180} y={y + 10} fill={col} fontSize={48} fontWeight={900}>{t}</text>
            <text x={640} y={y + 10} fill={C.ink} fontSize={40} fontWeight={700}>{where}</text>
            <text x={1240} y={y + 10} fill={C.ink} fontSize={40} fontWeight={800}>{what}</text>
          </g>
        );
      })}
    </g>
  );
};

export const ExamTraps: React.FC = () => {
  const intro = useIn("intro");
  const items: [string, string, string, string][] = [
    ["trap-2", "“Lateral meristem plant ki lambai badhata hai.”", "Lateral → girth (motai). Lambai: apical + intercalary.", "1"],
    ["trap-3", "“Meristematic cells mein bada central vacuole hota hai.”", "Bada central vacuole = permanent tissue. Meristem: vacuole absent.", "2"],
    ["trap-4", "“Plants mein mitosis poore sharir mein barabar hota hai.”", "Plants: mitosis mainly meristem mein.", "3"],
  ];
  const ps = items.map(([b]) => [useIn(`${b}:wrong`, -40), useIn(`${b}:wrong`), useIn(`${b}:fix`)]);
  return (
    <g>
      <g opacity={Math.min(1, intro)} transform="translate(960,200)">
        <text x={0} y={0} textAnchor="middle" fill={C.coral} fontSize={60} fontWeight={900}>⚠ UPSC traps</text>
      </g>
      {items.map(([b, claim, fix, n], i) => {
        const [show, wrong, good] = ps[i];
        const y = 300 + i * 240;
        return (
          <g key={b} opacity={Math.min(1, show)} transform={`translate(0,${(1 - Math.min(1, show)) * 30})`}>
            <rect x={140} y={y} width={1640} height={200} rx={28} fill="rgba(255,255,255,0.05)" stroke={C.cardLine} strokeWidth={2} />
            <text x={190} y={y + 62} fill={C.soft} fontSize={30} fontWeight={800}>STATEMENT {n}</text>
            <text x={190} y={y + 112} fill={C.ink} fontSize={40} fontWeight={700} opacity={1 - 0.45 * Math.min(1, good)}>{claim}</text>
            <text x={190} y={y + 168} fill={C.green} fontSize={36} fontWeight={800} opacity={Math.min(1, good)}>✓ {fix}</text>
            <Stamp x={1610} y={y + 100} text="GALAT" color={C.red} p={wrong} size={52} />
          </g>
        );
      })}
    </g>
  );
};

export const Bridge: React.FC = () => {
  const f = useCurrentFrame();
  const stop = useIn("stop");
  const diff = useRamp("differentiate", 60, 0, Easing.inOut);
  const perm = useIn("permanent");
  const next = useIn("next");
  const coconut = useIn("coconut");
  const game = useIn("game");
  const part1 = 1 - useRamp("next", 16);
  const div = interpolate(f, [0, 50], [0, 1]);
  return (
    <g>
      {part1 > 0 && (
        <g opacity={part1}>
          <Rise p={useIn(0, 4)} x={960} y={200} size={54} anchor="middle">Meristem cell → ? </Rise>
          <Cell x={interpolate(diff, [0, 1], [960, 360])} y={560} r={90} shape="round" fill="#FEF3C7" edge="#B45309" nucleus={0.4} granules={6}
            opacity={1 - 0.3 * diff} />
          {stop > 0 && <Chip x={interpolate(diff, [0, 1], [960, 360])} y={710} text="divide band" color={C.coral} p={stop} size={30} />}
          {diff > 0 && <>
            <DrawPath d="M 470 560 L 760 560" p={diff} color={C.amber} width={8} length={300} />
            <text x={615} y={520} textAnchor="middle" fill={C.amber} fontSize={36} fontWeight={900} opacity={diff}>Differentiation</text>
            <g opacity={diff}>
              <Cell x={980} y={420} r={80} shape="round" fill="#D9F99D" edge="#65A30D" vacuole={0.62} nucleus={0.2} nucleusX={-50} nucleusY={-30} wall={6} />
              <Cell x={1240} y={560} r={70} shape="rect" stretch={1.9} fill="#BBF7D0" edge="#15803D" wall={10} nucleus={0.2} vacuole={0.4} />
              <Cell x={1520} y={700} r={78} shape="hex" fill="#FDE68A" edge="#92400E" wall={22} wallColor="#78350F" nucleus={0} />
            </g>
          </>}
          {perm > 0 && (
            <g transform="translate(1250,900)" opacity={Math.min(1, perm)}>
              <rect x={-420} y={-56} width={840} height={96} rx={48} fill={C.violet} opacity={0.18} stroke={C.violet} strokeWidth={3} />
              <text x={0} y={8} textAnchor="middle" fill={C.ink} fontSize={42} fontWeight={900}>= Permanent tissues</text>
            </g>
          )}
        </g>
      )}
      {next > 0 && (
        <g opacity={Math.min(1, next)}>
          <text x={960} y={250} textAnchor="middle" fill={C.soft} fontSize={36} fontWeight={800} letterSpacing={2}>AGLI VIDEO</text>
          <text x={960} y={340} textAnchor="middle" fill={C.ink} fontSize={64} fontWeight={900}>Permanent tissue</text>
          {["Parenchyma", "Collenchyma", "Sclerenchyma"].map((t, i) => <Chip key={t} x={560 + i * 400} y={470} text={t} color={[C.leaf, C.teal, C.amber][i]} p={useIn("next", i * 6)} size={36} />)}
          {coconut > 0 && <g opacity={Math.min(1, coconut)} transform="translate(960,640)">
            <circle cx={-330} cy={0} r={60} fill="#7C4A21" /><circle cx={-330} cy={0} r={42} fill="#A16207" />
            <text x={-240} y={14} fill={C.ink} fontSize={40} fontWeight={800}>Nariyal ka chhilka itna sakht kyon?</text>
          </g>}
          {game > 0 && (
            <g transform={`translate(960,${860}) scale(${1 + 0.04 * Math.sin(f / 8)})`} opacity={Math.min(1, game)}>
              <rect x={-330} y={-60} width={660} height={110} rx={55} fill={C.amber} />
              <text x={0} y={14} textAnchor="middle" fill={C.bg0} fontSize={48} fontWeight={900}>🎮  Ab game khelo!</text>
            </g>
          )}
        </g>
      )}
    </g>
  );
};
