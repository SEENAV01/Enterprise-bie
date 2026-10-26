// plate (Task 046 one-shot test, 26 October 2026): a picture made outside the browser as the world of a shot, with BIE's
// leader labels on top (VG-02: the picture itself carries no text).
//   - a frame sequence (Route 1: Blender Cycles frames, data.pattern "assets/plate/f%04d.png", data.first = its first
//     frame number) shown frame by frame, the frame held until its image has loaded;
//   - or one still (data.src) for a plate that moves by itself.
// data.anchors: {name: [[x, y, depth], ...]}, one entry per frame of the plate (x and y from the top-left, 0..1), written by
// the maker (epithelium_studio.py's anchors.json). data.labels: [{text, anchor, dx?, dy?}]: each label box sits at its
// anchor plus (dx, dy) pixels and draws a leader line to a dot on the anchor, in the shot's accent, as the cell world's
// labels do.
// parallax_plate (Route 2): one AI-made still moved in 2.5D by code. A plane cut into a fine grid takes the still as its
// colour and a depth map (Depth Anything V2 Small, bie/toolbox/adapters/depth.py) as its relief; the camera pushes in
// slowly and drifts, so near cells slide over far ones; blue particles cross into the layer (B-04), a warm glow grows on
// the cell the sentence is about (B-10), and the leader labels follow their anchor points (data.anchors_uv: {name: [u, v]}
// on the still) through the same camera.
import React, { useLayoutEffect, useRef } from "react";
import * as THREE from "three";
import { ThreeCanvas } from "@remotion/three";
import { PerspectiveCamera } from "@react-three/drei";
import { useVideoConfig } from "remotion";
import { registerBlock, BlockProps } from "../registry";
import { W as STAGE_W } from "../index";
import { C, FONT, assetUrl, clamp01, ramp, useAsset, useFrameHold, useRel } from "./common";

type Label = { text: string; anchor: string; dx?: number; dy?: number };

export function plateFrame(rel: number, count: number): number {
  return Math.max(0, Math.min(Math.max(1, count) - 1, Math.round(rel)));
}

export function framePath(pattern: string, first: number, index: number): string {
  return pattern.replace(/%0(\d)d/, (_m, n) => String(first + index).padStart(Number(n), "0"));
}

const Plate: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, frame } = useRel(at);
  const count: number = data.count ?? 1;
  const index = plateFrame(rel, count);
  const src: string = data.pattern ? framePath(data.pattern, data.first ?? 1, index) : data.src;
  const release = useFrameHold(frame);
  const img = useRef<HTMLImageElement>(null);
  useLayoutEffect(() => {                      // a still, or a frame already loaded: no load event comes, release now
    if (img.current && img.current.complete && img.current.naturalWidth > 0) release();
  });
  const anchors: Record<string, number[][]> = data.anchors || {};
  const labels: Label[] = data.labels || [];
  const accent: string = data.accent || C.accent;
  const draw = ramp(rel, data.label_at ?? 8, 14);
  const placed = labels.map((l) => {
    const track = anchors[l.anchor] || [];
    const a = track[Math.min(index, track.length - 1)];
    if (!a || a[2] <= 0) return null;                                    // behind the camera
    return place(l, a[0] * width, a[1] * height, width, height);       // out of frame: no label
  });
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: "#02050a" }}>
      <img ref={img} src={assetUrl(src)} onLoad={release} onError={release}
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
      <Labels placed={placed} draw={draw} accent={accent} width={width} height={height} />
    </div>
  );
};

type Placed = (Label & { x: number; y: number; bx: number; by: number }) | null;

function place(l: Label, x: number, y: number, width: number, height: number): Placed {
  if (!(x >= 0 && x <= width && y >= 0 && y <= height)) return null;
  const bx = Math.max(24, Math.min(width - 360, x + (l.dx ?? 150))), by = Math.max(height * 0.22, Math.min(height - 80, y + (l.dy ?? -120)));
  return { ...l, x, y, bx, by };
}

const Labels: React.FC<{ placed: Placed[]; draw: number; accent: string; width: number; height: number }> = ({ placed, draw, accent, width, height }) => (
  <>
    <svg style={{ position: "absolute", inset: 0, width, height, overflow: "visible", pointerEvents: "none" }}>
      {placed.map((p, i) => p && (
        <g key={i} opacity={draw}>
          <line x1={p.bx} y1={p.by} x2={p.bx + (p.x - p.bx) * draw} y2={p.by + (p.y - p.by) * draw} stroke={accent} strokeWidth={3.5} />
          <circle cx={p.x} cy={p.y} r={9 * draw} fill={accent} stroke="#06121c" strokeWidth={3} />
        </g>
      ))}
    </svg>
    {placed.map((p, i) => p && (
      <div key={i} style={{ position: "absolute", left: p.bx, top: p.by - 26, opacity: draw, fontFamily: FONT, fontSize: 30, fontWeight: 700,
        color: C.ink, background: C.panel, border: `3px solid ${accent}`, borderRadius: 12, padding: "8px 16px", whiteSpace: "nowrap" }}>{p.text}</div>
    ))}
  </>
);

registerBlock("plate", Plate);

// ---------------------------------------------------------------- parallax_plate

type Relief = { texture: THREE.Texture; depth: THREE.Texture; sample: (u: number, v: number) => number };

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const im = new Image();
    im.onload = () => resolve(im);
    im.onerror = () => reject(new Error(`could not load ${url}`));
    im.src = url;
  });
}

async function loadRelief(src: string, depthSrc: string): Promise<Relief> {
  const [im, dm] = await Promise.all([loadImage(assetUrl(src)), loadImage(assetUrl(depthSrc))]);
  const texture = new THREE.Texture(im);            // no colour-space decode: the shader passes the still's pixels through as they are
  texture.needsUpdate = true;
  const canvas = document.createElement("canvas");
  canvas.width = dm.naturalWidth; canvas.height = dm.naturalHeight;
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(dm, 0, 0);
  const px = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  const depth = new THREE.CanvasTexture(canvas);
  const sample = (u: number, v: number) => {            // v from the top, like the picture; 0 far .. 1 near
    const x = Math.max(0, Math.min(canvas.width - 1, Math.round(u * (canvas.width - 1))));
    const y = Math.max(0, Math.min(canvas.height - 1, Math.round(v * (canvas.height - 1))));
    return px[(y * canvas.width + x) * 4] / 255;
  };
  return { texture, depth, sample };
}

const VERT = `
uniform sampler2D depthMap; uniform float strength; varying vec2 vUv; varying float vNear;
void main() {
  vUv = uv;
  float d = texture2D(depthMap, uv).r;
  vNear = d;
  vec3 p = position + vec3(0.0, 0.0, (d - 0.5) * strength);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
}`;
const FRAG = `
uniform sampler2D map; uniform vec2 glowUv; uniform float glow; uniform float aspect; uniform vec3 glowColor; varying vec2 vUv; varying float vNear;
void main() {
  vec4 c = texture2D(map, vUv);
  vec2 d = (vUv - glowUv) * vec2(aspect, 1.0);
  float g = glow * exp(-dot(d, d) / 0.006);
  vec3 col = c.rgb + glowColor * g * (0.35 + 0.65 * c.rgb);
  gl_FragColor = vec4(col, 1.0);
}`;

export function parallaxCamera(t: number, data: any, aspect: number): { position: [number, number, number]; target: [number, number, number]; fov: number } {
  const fov = data.fov ?? 30;
  const fill = 1 / Math.tan(((fov / 2) * Math.PI) / 180);                       // distance at which the plane's height fills the frame
  const d0 = fill * (data.margin ?? 0.93), push = data.push ?? 0.1, drift = data.drift ?? 0.06;
  const e = t * t * (3 - 2 * t);                                                 // ease in and out
  const dist = d0 * (1 - push * e);
  const fx = data.focus_uv ? (data.focus_uv[0] - 0.5) * 2 * aspect : 0, fy = data.focus_uv ? (0.5 - data.focus_uv[1]) * 2 : 0;
  const tx = fx * 0.25 * e, ty = fy * 0.25 * e;                                 // the push leans toward the lit cell
  return { position: [tx + drift * (e - 0.5), ty + drift * 0.4 * (0.5 - e), dist], target: [tx, ty, 0], fov };
}

const ParallaxPlate: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const dpr = Math.min(1, useVideoConfig().width / STAGE_W);
  const relief = useAsset(`relief:${data.src}:${data.depth}`, () => loadRelief(data.src, data.depth));
  const count: number = data.count ?? 135;
  const t = clamp01(rel / Math.max(1, count - 1));
  const aspect = data.aspect ?? width / height;
  const strength: number = data.strength ?? 0.32;
  const accent: string = data.accent || C.accent;
  const glow = (data.glow ?? 0.55) * ramp(rel, (data.glow_at ?? 0.15) * count, 0.3 * count);
  const material = React.useMemo(() => relief ? new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, uniforms: {
    map: { value: relief.texture }, depthMap: { value: relief.depth }, strength: { value: strength }, glow: { value: 0 },
    glowUv: { value: new THREE.Vector2(data.focus_uv ? data.focus_uv[0] : 0.5, data.focus_uv ? 1 - data.focus_uv[1] : 0.5) },
    glowColor: { value: new THREE.Color(data.glow_color || "#ffb38a") }, aspect: { value: aspect } } }) : null, [relief]);
  if (!relief || !material) return null;
  material.uniforms.glow.value = glow;
  const cam = parallaxCamera(t, data, width / height);
  const H = 2, Wd = 2 * aspect;
  const point = (u: number, v: number, lift = 0) => new THREE.Vector3((u - 0.5) * Wd, (0.5 - v) * H, (relief.sample(u, v) - 0.5) * strength + lift);
  const camera = new THREE.PerspectiveCamera(cam.fov, width / height, 0.01, 100);
  camera.position.set(...cam.position);
  camera.lookAt(new THREE.Vector3(...cam.target));
  camera.updateMatrixWorld();
  camera.updateProjectionMatrix();
  const toScreen = (p: THREE.Vector3) => { const v = p.clone().project(camera); return { x: ((v.x + 1) / 2) * width, y: ((1 - v.y) / 2) * height, behind: v.z > 1 }; };
  // particles (B-04): blue spheres come down out of the dark and sink into the layer, one after another
  const n: number = data.particles ?? 30;
  const period = (data.particle_seconds ?? 2.6) * fps;
  const dots = [];
  for (let i = 0; i < n; i++) {
    const r1 = Math.sin(i * 12.9898) * 43758.5453, fu = r1 - Math.floor(r1);
    const r2 = Math.sin(i * 78.233) * 12345.678, fv = r2 - Math.floor(r2);
    const phase = (((rel / period) + i / n) % 1 + 1) % 1;
    const u = 0.12 + 0.76 * fu, v = 0.3 + 0.6 * fv;
    const surface = point(u, v);
    const lift = (1 - phase) * 0.9;
    const fade = phase < 0.12 ? phase / 0.12 : phase > 0.88 ? (1 - phase) / 0.12 : 1;
    dots.push(<mesh key={i} position={[surface.x, surface.y + lift * 0.35, surface.z + lift]}>
      <sphereGeometry args={[0.016 + 0.01 * ((i * 7) % 3), 14, 10]} />
      <meshStandardMaterial color={data.particle_color || "#2f7dff"} emissive={data.particle_color || "#2f7dff"} emissiveIntensity={0.55}
        roughness={0.25} metalness={0.05} transparent opacity={fade} />
    </mesh>);
  }
  const labels: Label[] = data.labels || [];
  const anchorsUv: Record<string, number[]> = data.anchors_uv || {};
  const placed = labels.map((l) => {
    const a = anchorsUv[l.anchor];
    if (!a) return null;
    const s = toScreen(point(a[0], a[1]));
    return s.behind ? null : place(l, s.x, s.y, width, height);
  });
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: "#02050a" }}>
      <ThreeCanvas width={width} height={height} dpr={dpr} gl={{ alpha: false, preserveDrawingBuffer: true, antialias: true }}>
        <PerspectiveCamera makeDefault fov={cam.fov} position={cam.position} near={0.01} far={100}
          ref={(c: any) => { if (c) { c.lookAt(new THREE.Vector3(...cam.target)); c.updateMatrixWorld(); } }} />
        <color attach="background" args={["#02050a"]} />
        <ambientLight intensity={0.6} />
        <directionalLight position={[-2, 3, 4]} intensity={1.6} />
        <directionalLight position={[2, 2, -3]} intensity={0.8} color="#8fb8ff" />
        <mesh material={material}><planeGeometry args={[Wd, H, 384, 216]} /></mesh>
        {dots}
      </ThreeCanvas>
      <div style={{ position: "absolute", inset: 0, pointerEvents: "none", boxShadow: "inset 0 0 200px rgba(0,0,0,0.6)" }} />
      <Labels placed={placed} draw={ramp(rel, data.label_at ?? 8, 14)} accent={accent} width={width} height={height} />
    </div>
  );
};

registerBlock("parallax_plate", ParallaxPlate);
