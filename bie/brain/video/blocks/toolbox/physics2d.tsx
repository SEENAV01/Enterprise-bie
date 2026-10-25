// 2D physics blocks (Task 046a):
// - falling_body: a body dropped with and without air drag (computed by SciPy and NumPy in Python), shown side by side
//   with its height-time graph growing;
// - rigid_bodies_2d: boxes and balls falling and stacking, simulated by Matter.js with a fixed time step from frame 0.
import React from "react";
import Matter from "matter-js";
import { line, scaleLinear } from "d3";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, ticks, useRel } from "./common";

const FallingBody: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel } = useRel(at);
  const n = data.t.length;
  const f = Math.min(rel, n - 1);
  const towerW = width * 0.36, graphX = towerW + 80;
  const sy = scaleLinear().domain([0, data.height]).range([height - 70, 150]);
  const gx = scaleLinear().domain([0, data.t[n - 1]]).range([graphX + 70, width - 50]);
  const curve = (ys: number[]) => line<number>().x((_, i) => gx(data.t[i])).y((v) => sy(v))(ys.slice(0, f + 1)) || "";
  const balls = [{ x: towerW * 0.33, y: data.y_free[f], c: C.accent, label: data.free_label || "no air" },
                 { x: towerW * 0.7, y: data.y_drag[f], c: C.warm, label: data.drag_label || "with air drag" }];
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {ticks(0, data.height, 5).map((v) => <g key={v}><line x1={30} x2={towerW} y1={sy(v)} y2={sy(v)} stroke={C.line} />
          <text x={36} y={sy(v) - 8} fill={C.muted} fontSize={22}>{v} m</text></g>)}
        <rect x={20} y={height - 70} width={towerW} height={12} fill={C.muted} />
        {balls.map((b, i) => <g key={i}>
          <circle cx={b.x} cy={sy(b.y) - 22} r={22} fill={b.c} style={{ filter: `drop-shadow(0 0 12px ${b.c})` }} />
          <text x={b.x} y={130} fill={b.c} fontSize={24} fontWeight={700} textAnchor="middle">{b.label}</text></g>)}
        <line x1={graphX + 70} x2={width - 50} y1={height - 70} y2={height - 70} stroke={C.ink} strokeOpacity={0.6} />
        <line x1={graphX + 70} x2={graphX + 70} y1={150} y2={height - 70} stroke={C.ink} strokeOpacity={0.6} />
        {ticks(0, data.t[n - 1], 4).map((v) => <text key={"t" + v} x={gx(v)} y={height - 36} fill={C.muted} fontSize={22} textAnchor="middle">{v} s</text>)}
        <path d={curve(data.y_free)} fill="none" stroke={C.accent} strokeWidth={5} />
        <path d={curve(data.y_drag)} fill="none" stroke={C.warm} strokeWidth={5} />
        <text x={graphX + 80} y={140} fill={C.muted} fontSize={24}>height (m) / time (s)</text>
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 50, bottom: 90, opacity: ramp(rel, n * 0.6, 15) }} /> : null}
    </div>
  );
};

type Frame = { x: number; y: number; angle: number }[];
const runs = new Map<string, Frame[]>();

function simulate(data: any, frames: number, fps: number, width: number, height: number): Frame[] {
  const engine = Matter.Engine.create({ gravity: { x: 0, y: 1, scale: 0.001 } });
  const ground = Matter.Bodies.rectangle(width / 2, height - 30, width * 1.2, 60, { isStatic: true });
  const walls = [Matter.Bodies.rectangle(-30, height / 2, 60, height * 2, { isStatic: true }),
                 Matter.Bodies.rectangle(width + 30, height / 2, 60, height * 2, { isStatic: true })];
  const ramp_ = data.ramp ? [Matter.Bodies.rectangle(width * data.ramp.x, height * data.ramp.y, width * data.ramp.w, 24,
    { isStatic: true, angle: data.ramp.angle })] : [];
  const bodies = (data.bodies as any[]).map((b) => {
    const x = b.x * width, y = b.y * height, s = b.size * height;
    return b.shape === "circle" ? Matter.Bodies.circle(x, y, s / 2, { restitution: b.bounce ?? 0.5, friction: 0.05 })
                                : Matter.Bodies.rectangle(x, y, s, s, { restitution: b.bounce ?? 0.2, angle: b.angle ?? 0 });
  });
  Matter.Composite.add(engine.world, [ground, ...walls, ...ramp_, ...bodies]);
  const out: Frame[] = [];
  const dt = 1000 / fps / 4;
  for (let f = 0; f <= frames; f++) {
    out.push(bodies.map((b) => ({ x: b.position.x, y: b.position.y, angle: b.angle })));
    for (let s = 0; s < 4; s++) Matter.Engine.update(engine, dt);       // fixed steps: identical on every render
  }
  return out;
}

const RigidBodies2D: React.FC<BlockProps> = ({ data, at, width, height, id }) => {
  const { rel, fps } = useRel(at);
  const frames = Math.round((data.seconds ?? 5) * fps);
  if (!runs.has(id)) runs.set(id, simulate(data, frames, fps, width, height));
  const frame = runs.get(id)![Math.min(rel, frames)];
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <rect x={0} y={height - 60} width={width} height={60} fill="#16384a" />
        {data.ramp ? <rect x={width * data.ramp.x - (width * data.ramp.w) / 2} y={height * data.ramp.y - 12} width={width * data.ramp.w} height={24}
          fill={C.muted} transform={`rotate(${(data.ramp.angle * 180) / Math.PI} ${width * data.ramp.x} ${height * data.ramp.y})`} /> : null}
        {(data.bodies as any[]).map((b, i) => {
          const p = frame[i], s = b.size * height, colour = b.colour || (i % 2 ? C.warm : C.accent);
          return b.shape === "circle"
            ? <circle key={i} cx={p.x} cy={p.y} r={s / 2} fill={colour} />
            : <rect key={i} x={-s / 2} y={-s / 2} width={s} height={s} rx={6} fill={colour}
                transform={`translate(${p.x} ${p.y}) rotate(${(p.angle * 180) / Math.PI})`} />;
        })}
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 40, top: 30 }} /> : null}
    </div>
  );
};

registerBlock("falling_body", FallingBody);
registerBlock("rigid_bodies_2d", RigidBodies2D);
