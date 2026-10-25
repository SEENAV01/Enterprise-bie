// three.js blocks (Task 046a), drawn through ThreeCanvas (@remotion/three; three-lite.tsx in the preview):
// - cell_sheet_3d: a sheet of cells (a Blender-made glTF, or a procedural sheet when there is none) with particles
//   flowing through it (particle_flow) and a glowing cell (focus_glow);
// - model_3d: any glTF model (an organ from NIH 3D, Z-Anatomy, BodyParts3D) turning, with named parts glowing and a
//   zoom (anatomy_3d, organ_zoom in 3D);
// - collision_3d: rigid bodies colliding, computed with cannon-es at a fixed time step from frame 0.
import React, { useMemo } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { ThreeCanvas } from "@remotion/three";
import { PerspectiveCamera } from "@react-three/drei";
import * as CANNON from "cannon-es";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, assetUrl, clamp01, ramp, useAsset, useRel } from "./common";

const loader = new GLTFLoader();
function loadGlb(src: string): Promise<THREE.Group> {
  return new Promise((resolve, reject) => loader.load(assetUrl(src), (g) => resolve(g.scene), undefined, (e) => reject(new Error(`glTF ${src}: ${e}`))));
}

const Lights: React.FC = () => (
  <>
    <hemisphereLight args={[0xffffff, 0x223344, 1.4]} />
    <directionalLight position={[4, 8, 6]} intensity={2.2} />
    <directionalLight position={[-6, 3, -4]} intensity={0.8} color={0x88ccff} />
  </>
);

/** A camera that orbits the target: angle in degrees, distance and height in model units. */
const Orbit: React.FC<{ angle: number; distance: number; height: number; target?: [number, number, number]; fov?: number }> =
  ({ angle, distance, height, target = [0, 0, 0], fov = 40 }) => {
    const a = (angle * Math.PI) / 180;
    const position: [number, number, number] = [target[0] + Math.sin(a) * distance, target[1] + height, target[2] + Math.cos(a) * distance];
    return <PerspectiveCamera makeDefault fov={fov} position={position} near={0.01} far={500}
      ref={(cam: any) => { if (cam) { cam.lookAt(...target); cam.updateMatrixWorld(); } }} />;
  };

// ---------------------------------------------------------------- cell sheet + particle flow

function proceduralSheet(kind: string): THREE.Group {
  const group = new THREE.Group();
  const shape = kind === "squamous" ? [0.62, 0.22] : kind === "cuboidal" ? [0.5, 0.95] : [0.42, 2.3];
  const [r, h] = shape;
  const cyto = new THREE.MeshStandardMaterial({ color: 0xee8c94, roughness: 0.55 });
  const nuc = new THREE.MeshStandardMaterial({ color: 0x5c3399, roughness: 0.5 });
  for (let row = 0; row < 5; row++) for (let col = 0; col < 7; col++) {
    const x = (col - 3) * Math.sqrt(3) * r + (row % 2 ? (Math.sqrt(3) * r) / 2 : 0), z = (row - 2) * 1.5 * r;
    const cell = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.98, r * 0.98, h, 6), cyto);
    cell.position.set(x, h / 2, z);
    cell.name = `cell_${row}_${col}`;
    const n = new THREE.Mesh(new THREE.SphereGeometry(r * 0.5, 16, 12), nuc);
    n.scale.set(1, kind === "columnar" ? 0.7 : 0.5, 1);
    n.position.set(x, h * (kind === "columnar" ? 0.3 : 0.5), z);
    group.add(cell, n);
  }
  return group;
}

const CellSheet: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const model = useAsset(`glb:${data.src || "procedural:" + data.kind}`, () => (data.src ? loadGlb(data.src) : Promise.resolve(proceduralSheet(data.kind))));
  const flow = data.flow || {};
  const n = flow.particles ?? 40;
  const period = (flow.seconds ?? 2.5) * fps;
  const bounds = useMemo(() => (model ? new THREE.Box3().setFromObject(model) : null), [model]);
  const glowName = data.focus_cell as string | undefined;
  const glow = clamp01(Math.sin((rel / fps) * 3) * 0.5 + 0.5) * ramp(rel, (data.focus_at ?? 1.0) * fps, 15);
  const translucent = data.translucent !== false;
  const scene = useMemo(() => {
    if (!model) return null;
    const copy = model.clone(true);
    copy.traverse((o: any) => {
      if (o.isMesh) {
        const m = o.material.clone();
        if (o.name.startsWith("cell_")) {
          m.color = new THREE.Color(data.cell_colour || "#ee8f9c");
          if (translucent) { m.transparent = true; m.opacity = 0.5; m.depthWrite = false; }
        } else if (o.name.startsWith("nucleus_")) {
          m.color = new THREE.Color(data.nucleus_colour || "#6b3fc0");
        } else if (o.name.startsWith("basement")) {
          m.color = new THREE.Color("#5f8fb3");
        }
        o.material = m;
        if (glowName && o.name === glowName) o.userData.glow = true;
      }
    });
    return copy;
  }, [model, glowName, translucent]);
  if (!scene || !bounds) return null;
  scene.traverse((o: any) => {
    if (o.isMesh && o.userData.glow) {
      o.material.emissive = new THREE.Color(C.warm); o.material.emissiveIntensity = 1.4 * glow; o.material.opacity = 0.5 + 0.4 * glow;
    }
  });
  const size = bounds.getSize(new THREE.Vector3());
  const top = bounds.max.y, bottom = bounds.min.y;
  const particles = Array.from({ length: n }).map((_, i) => {
    const seed = Math.sin(i * 12.9898) * 43758.5453;
    const fx = seed - Math.floor(seed), fz = (seed * 7.13) - Math.floor(seed * 7.13);
    const t = (((rel / period) + i / n) % 1 + 1) % 1;
    const x = bounds.min.x + fx * size.x, z = bounds.min.z + fz * size.z;
    const y = flow.direction === "up" ? bottom - 0.6 + t * (top - bottom + 1.8) : top + 1.2 - t * (top - bottom + 1.8);
    return <mesh key={i} position={[x, y, z]}><sphereGeometry args={[Math.max(size.x, size.z) * 0.009, 10, 8]} />
      <meshStandardMaterial color={C.warm} emissive={C.warm} emissiveIntensity={0.8} /></mesh>;
  });
  const cam = data.camera || {};
  const angle = (cam.start ?? 25) + (cam.orbit ?? 50) * ramp(rel, 0, (cam.seconds ?? 5) * fps);
  const span = Math.max(size.x, size.z);
  return (
    <>
      <ThreeCanvas width={width} height={height} gl={{ alpha: true, preserveDrawingBuffer: true, antialias: true }}>
        <Lights />
        <Orbit angle={angle} distance={span * (cam.distance ?? 1.35)} height={span * (cam.height ?? 0.75)} target={[0, (top + bottom) / 2.6, 0]} />
        <primitive object={scene} />
        {flow.particles === 0 ? null : particles}
      </ThreeCanvas>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 24, bottom: 18 }} /> : null}
    </>
  );
};

// ---------------------------------------------------------------- any model: turn, glow, zoom

type Part = { match: string; colour: string; label: string; at: number };

const Model3D: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const model = useAsset(`glb:${data.src}`, () => loadGlb(data.src));
  const pattern = data.glow ? new RegExp(data.glow, "i") : null;
  // parts (batch 3): named parts take their own colour one after another (a brain's lobes), each glowing as it comes
  const parts = (data.parts || []) as Part[];
  const scene = useMemo(() => {
    if (!model) return null;
    const copy = model.clone(true);
    const box = new THREE.Box3().setFromObject(copy);
    const centre = box.getCenter(new THREE.Vector3()), size = box.getSize(new THREE.Vector3());
    const scale = 2 / Math.max(size.x, size.y, size.z);
    copy.position.sub(centre.multiplyScalar(scale));
    copy.scale.multiplyScalar(scale);
    copy.traverse((o: any) => {
      if (o.isMesh) {
        o.material = Array.isArray(o.material) ? o.material.map((m: any) => m.clone()) : o.material.clone();
        if (data.colour && !o.material.map) o.material.color = new THREE.Color(data.colour);
        if (pattern && pattern.test(o.name)) o.userData.glow = true;
        const k = parts.findIndex((p) => new RegExp(p.match, "i").test(o.name));
        if (k >= 0) o.userData.part = k;
      }
    });
    return copy;
  }, [model, data.glow, data.colour, JSON.stringify(parts)]);
  if (!scene) return null;
  const glow = ramp(rel, (data.glow_at ?? 1.5) * fps, 12) * (0.6 + 0.4 * Math.sin(rel / 4));
  const base = new THREE.Color(data.base_colour || "#9a9fa6");
  scene.traverse((o: any) => {
    if (o.isMesh && o.userData.glow) { const m = o.material; m.emissive = new THREE.Color(C.warm); m.emissiveIntensity = glow; }
    if (o.isMesh && o.userData.part !== undefined) {
      const p = parts[o.userData.part], m = o.material;
      const on = ramp(rel, p.at * fps, 10), pulse = on * Math.max(0, 1 - (rel - p.at * fps) / (0.9 * fps));
      m.color = base.clone().lerp(new THREE.Color(p.colour), on);
      m.emissive = new THREE.Color(p.colour); m.emissiveIntensity = 0.55 * pulse;
    }
  });
  const turn = (data.turn_degrees ?? 120) * ramp(rel, 0, (data.seconds ?? 5) * fps);
  const zoom = data.zoom ? 1 - (1 - data.zoom) * ramp(rel, (data.zoom_at ?? 2) * fps, 1.5 * fps) : 1;
  return (
    <>
      <div style={{ position: "absolute", inset: 0, transform: `translateX(${data.shift_x ?? 0}px)` }}>
        <ThreeCanvas width={width} height={height} gl={{ alpha: true, preserveDrawingBuffer: true, antialias: true }}>
          <Lights />
          {/* spin: the model turns under a fixed camera and fixed lights, so a part never turns its dark side to the viewer */}
          <Orbit angle={(data.start_degrees ?? 0) + (data.spin ? 0 : turn)} distance={(data.distance ?? 4.2) * zoom}
            height={(data.camera_height ?? 0.6) * zoom} target={data.target || [0, 0, 0]} />
          <primitive object={scene} rotation={[0, data.spin ? (turn * Math.PI) / 180 : 0, 0]} />
        </ThreeCanvas>
      </div>
      <Title text={data.title} sub={data.subtitle} />
      {parts.length ? <div style={{ position: "absolute", right: 40, top: 150, display: "flex", flexDirection: "column", gap: 12, fontFamily: FONT }}>
        {parts.map((p) => <div key={p.label} style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 28, color: C.ink, fontWeight: 700,
          opacity: ramp(rel, p.at * fps, 8), background: C.panel, padding: "6px 16px", borderRadius: 12 }}>
          <span style={{ width: 22, height: 22, borderRadius: 11, background: p.colour, display: "inline-block" }} />{p.label}</div>)}
      </div> : null}
      {data.credit ? <div style={{ position: "absolute", right: 16, bottom: 8, color: C.muted, fontSize: 16, fontFamily: "sans-serif" }}>{data.credit}</div> : null}
    </>
  );
};

// ---------------------------------------------------------------- cannon-es collision

type Track = { positions: number[][][]; quaternions: number[][][] };
const tracks = new Map<string, Track>();

function simulate(data: any, frames: number, fps: number): Track {
  const world = new CANNON.World({ gravity: new CANNON.Vec3(0, -9.82, 0) });
  world.defaultContactMaterial.restitution = data.restitution ?? 0.45;
  world.defaultContactMaterial.friction = data.friction ?? 0.3;
  const ground = new CANNON.Body({ mass: 0, shape: new CANNON.Plane() });
  ground.quaternion.setFromEuler(-Math.PI / 2, 0, 0);
  world.addBody(ground);
  const bodies = (data.bodies as any[]).map((b) => {
    const shape = b.shape === "box" ? new CANNON.Box(new CANNON.Vec3(b.size / 2, b.size / 2, b.size / 2)) : new CANNON.Sphere(b.size / 2);
    const body = new CANNON.Body({ mass: b.mass ?? 1, shape, position: new CANNON.Vec3(...(b.position as [number, number, number])) });
    if (b.velocity) body.velocity.set(...(b.velocity as [number, number, number]));
    world.addBody(body);
    return body;
  });
  const positions: number[][][] = [], quaternions: number[][][] = [];
  for (let f = 0; f <= frames; f++) {
    positions.push(bodies.map((b) => [b.position.x, b.position.y, b.position.z]));
    quaternions.push(bodies.map((b) => [b.quaternion.x, b.quaternion.y, b.quaternion.z, b.quaternion.w]));
    for (let s = 0; s < 4; s++) world.step(1 / (fps * 4));          // fixed sub-steps: the same on every render
  }
  return { positions, quaternions };
}

const Collision3D: React.FC<BlockProps> = ({ data, at, width, height, id }) => {
  const { rel, fps } = useRel(at);
  const frames = Math.round((data.seconds ?? 5) * fps);
  if (!tracks.has(id)) tracks.set(id, simulate(data, frames, fps));
  const track = tracks.get(id)!;
  const f = Math.min(rel, frames);
  return (
    <>
      <ThreeCanvas width={width} height={height} gl={{ alpha: true, preserveDrawingBuffer: true, antialias: true }}>
        <Lights />
        <Orbit angle={(data.start_degrees ?? 30) + (data.turn_degrees ?? 20) * ramp(rel, 0, frames)} distance={data.distance ?? 9}
          height={data.camera_height ?? 4} target={data.target || [0, 1, 0]} />
        <mesh rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[14, 14]} /><meshStandardMaterial color={0x16384a} /></mesh>
        <gridHelper args={[14, 14, 0x38d3c3, 0x24485a]} position={[0, 0.01, 0]} />
        {(data.bodies as any[]).map((b, i) => {
          const p = track.positions[f][i], q = track.quaternions[f][i];
          return (
            <mesh key={i} position={p as any} quaternion={q as any}>
              {b.shape === "box" ? <boxGeometry args={[b.size, b.size, b.size]} /> : <sphereGeometry args={[b.size / 2, 32, 24]} />}
              <meshStandardMaterial color={b.colour || (i % 2 ? C.warm : C.accent)} roughness={0.4} metalness={0.1} />
            </mesh>
          );
        })}
      </ThreeCanvas>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 24, bottom: 18 }} /> : null}
    </>
  );
};

registerBlock("cell_sheet_3d", CellSheet);
registerBlock("model_3d", Model3D);
registerBlock("collision_3d", Collision3D);
