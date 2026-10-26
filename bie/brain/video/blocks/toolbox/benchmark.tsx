// The benchmark 3D world (Task 046, Part B): the L5a shots of the epithelium benchmark as code, one world per topic
// (VG-01). One component, CellWorld, draws every shot of a scene from a timeline in its data, so the camera moves
// between shots and nothing cuts:
//   cell_sheet     the world: a procedural sheet of one epithelium member (or a Blender-made glTF, route C, by src)
//                  over its basement membrane and the tissue beneath; one accent colour per member (B-11, VG-09)
//   particle_flow  B-04 / VG-08: particles cross the sheet (absorb, secrete, cross), sweep along it (cilia, mucus) or
//                  flake off it (shedding)
//   focus_glow     B-10: the one structure the sentence is about is lit, the rest dims
//   organ_zoom     B-09: a procedural organ (lung, kidney, intestine, skin, bladder, duct) far away; the camera comes
//                  down to the sheet, never a cut
//   leader_label   VG-02: labels are code text tied to a 3D part by a leader line, projected every frame, so they move
//                  with it and work in every language
//   camera_path    VG-01: establish, pan to the next part, zoom in on the lit part, orbit, zoom out
//   cutaway        VG-03: a clipping plane opens the sheet to its base and the layers below
//   exploded_view  VG-03: the layers lift apart (stratified members), then settle
// Each of the eight names is registered as a block; alone, each draws the world with its own preset (the demo clips);
// in a lesson the composer (bie/brain/video/compose.py) writes one cell_sheet layer per scene whose data.shots carry
// every clause's flags, so all eight act inside one canvas and one camera.
import React, { useMemo } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { ThreeCanvas } from "@remotion/three";
import { PerspectiveCamera } from "@react-three/drei";
import { useVideoConfig } from "remotion";
import { registerBlock, BlockProps } from "../registry";
import { W as STAGE_W } from "../index";
import { C, FONT, assetUrl, clamp01, ramp, useAsset, useRel } from "./common";

// ---------------------------------------------------------------- members (one accent each, VG-09)

export type Member = "simple_squamous" | "simple_cuboidal" | "simple_columnar" | "ciliated" | "pseudostratified" | "stratified_squamous"
  | "stratified_cuboidal" | "stratified_columnar" | "transitional" | "keratinised" | "glandular" | "generic";

type Shape = { r: number; h: number; nucleusAt: number; nucleusScale: [number, number, number]; cilia?: boolean; microvilli?: boolean };
const SHAPES: Record<string, Shape> = {
  squamous: { r: 0.62, h: 0.2, nucleusAt: 0.5, nucleusScale: [0.95, 0.35, 0.95] },
  cuboidal: { r: 0.5, h: 0.95, nucleusAt: 0.5, nucleusScale: [0.9, 0.75, 0.9] },
  columnar: { r: 0.42, h: 2.3, nucleusAt: 0.28, nucleusScale: [0.85, 1.6, 0.85] },
  dome: { r: 0.56, h: 0.9, nucleusAt: 0.5, nucleusScale: [0.9, 0.8, 0.9] },
  keratin: { r: 0.62, h: 0.14, nucleusAt: 0.5, nucleusScale: [0, 0, 0] },
};

// layers from the base up: [shape, x-offset phase]; the top layer's shape gives the member its name
const LAYERS: Record<Member, string[]> = {
  simple_squamous: ["squamous"], simple_cuboidal: ["cuboidal"], simple_columnar: ["columnar"], ciliated: ["columnar"],
  pseudostratified: ["columnar"], stratified_squamous: ["cuboidal", "dome", "dome", "squamous", "squamous"],
  stratified_cuboidal: ["cuboidal", "cuboidal"], stratified_columnar: ["cuboidal", "columnar"], transitional: ["cuboidal", "dome", "dome"],
  keratinised: ["cuboidal", "dome", "squamous", "keratin", "keratin"], glandular: ["cuboidal"], generic: ["cuboidal"],
};
import accents from "./accents.json";
export const ACCENT: Record<string, string> = accents as Record<string, string>;   // one accent per member (VG-09), shared with compose.py
const CYTO = "#e98f98", CYTO_DEAD = "#b9a58c", NUCLEUS = "#5a2f9c", MEMBRANE = "#4f8bb3", TISSUE = "#2a3f55", ORGAN = "#c96a6a";

// ---------------------------------------------------------------- procedural geometry (route A; route C loads a glTF instead)

type Built = { group: THREE.Group; parts: Record<string, THREE.Vector3>; layers: THREE.Group[]; top: number; width: number; depth: number;
  center?: THREE.Vector3; span?: number };      // a world that is not a sheet (the Earth) says where its middle is and how big it looks

function rng(seed: number) {
  let s = seed >>> 0;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}

const mat = (color: string, extra: Partial<THREE.MeshStandardMaterialParameters> = {}) =>
  new THREE.MeshStandardMaterial({ color, roughness: 0.52, metalness: 0.05, ...extra });

export function buildSheet(member: Member, rows = 5, cols = 7, seed = 7): Built {
  const group = new THREE.Group();
  const random = rng(seed);
  const parts: Record<string, THREE.Vector3> = {};
  const layers: THREE.Group[] = [];
  const names = LAYERS[member] || LAYERS.generic;
  let z0 = 0, width = 0, depth = 0;
  const midR = Math.floor(rows / 2), midC = Math.floor(cols / 2);
  names.forEach((shapeName, li) => {
    const shape = SHAPES[shapeName];
    const layer = new THREE.Group();
    layer.name = `layer_${li}`;
    layer.userData.base = z0;
    const dx = Math.sqrt(3) * shape.r, dz = 1.5 * shape.r;
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const x = (c - (cols - 1) / 2) * dx + (r % 2 ? dx / 2 : 0), z = (r - (rows - 1) / 2) * dz;
      let h = shape.h * (1 + (random() - 0.5) * 0.12);
      if (member === "pseudostratified") h = shape.h * (0.55 + 0.45 * random());          // every cell touches the base, not all reach the top
      const dead = shapeName === "keratin";
      const cell = new THREE.Mesh(new THREE.CylinderGeometry(shape.r * 0.97, shape.r * 0.97, h, 6), mat(dead ? CYTO_DEAD : CYTO, { transparent: true, opacity: 0.92 }));
      cell.position.set(x, z0 + h / 2, z);
      cell.name = `cell_${li}_${r}_${c}`;
      cell.userData.kind = dead ? "keratin" : "cell";
      layer.add(cell);
      if (!dead) {
        const n = new THREE.Mesh(new THREE.SphereGeometry(shape.r * 0.5, 16, 12), mat(NUCLEUS, { roughness: 0.4 }));
        const nucleusAt = member === "pseudostratified" ? 0.25 + 0.5 * random() : shape.nucleusAt;
        n.scale.set(...shape.nucleusScale);
        n.position.set(x, z0 + h * nucleusAt, z);
        n.name = `nucleus_${li}_${r}_${c}`;
        n.userData.kind = "nucleus";
        layer.add(n);
      }
      if (li === names.length - 1 && (member === "ciliated" || member === "pseudostratified")) {
        for (let k = 0; k < 7; k++) {                                     // cilia: fine hairs on the free surface
          const hair = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.028, 0.55, 5), mat("#f6d6a0", { emissive: "#6b4a1a", emissiveIntensity: 0.2 }));
          const a = (k / 7) * Math.PI * 2, rad = shape.r * 0.45 * random();
          hair.position.set(x + Math.cos(a) * rad, z0 + h + 0.27, z + Math.sin(a) * rad);
          hair.name = `cilium_${r}_${c}_${k}`;
          hair.userData.kind = "cilia";
          hair.userData.phase = random() * Math.PI * 2;
          layer.add(hair);
        }
      }
      if (li === names.length - 1 && member === "simple_cuboidal") {
        for (let k = 0; k < 5; k++) {                                     // microvilli: tiny bumps that enlarge the surface
          const mv = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.08, 5), mat("#f0a9b0"));
          const a = (k / 5) * Math.PI * 2 + random(), rad = shape.r * 0.5 * Math.sqrt(random());
          mv.position.set(x + Math.cos(a) * rad, z0 + h + 0.04, z + Math.sin(a) * rad);
          mv.name = `microvillus_${r}_${c}_${k}`;
          mv.userData.kind = "microvilli";
          layer.add(mv);
        }
      }
      if (r === midR && c === midC && li === names.length - 1) parts.cell = new THREE.Vector3(x, z0 + h * 0.9, z);
      if (r === midR && c === midC && li === names.length - 1) parts.nucleus = new THREE.Vector3(x, z0 + h * shape.nucleusAt, z);
      if (r === midR && c === midC && li === names.length - 1) parts.top = new THREE.Vector3(x, z0 + h + 0.3, z);
      if (r === midR && c === midC + 1 && li === names.length - 1) parts.junction = new THREE.Vector3(x - dx / 2, z0 + h * 0.6, z);
    }
    z0 += shape.h * (shapeName === "keratin" ? 0.9 : 0.86);
    width = Math.max(width, cols * dx); depth = Math.max(depth, rows * dz);
    group.add(layer);
    layers.push(layer);
  });
  const top = z0;
  const membrane = new THREE.Mesh(new THREE.BoxGeometry(width + 0.7, 0.09, depth + 0.7), mat(MEMBRANE, { emissive: MEMBRANE, emissiveIntensity: 0.15 }));
  membrane.position.set(0, -0.05, 0);
  membrane.name = "basement_membrane";
  membrane.userData.kind = "basement_membrane";
  group.add(membrane);
  const tissue = new THREE.Mesh(new THREE.BoxGeometry(width + 0.7, 0.9, depth + 0.7), mat(TISSUE, { transparent: true, opacity: 0.85, roughness: 0.9 }));
  tissue.position.set(0, -0.56, 0);
  tissue.name = "underlying_tissue";
  tissue.userData.kind = "tissue";
  group.add(tissue);
  if (member === "glandular") {                                           // a gland: the sheet folds inward into a duct
    const duct = new THREE.Mesh(new THREE.TorusGeometry(0.9, 0.28, 10, 24, Math.PI), mat(CYTO, { transparent: true, opacity: 0.9 }));
    duct.rotation.set(0, 0, Math.PI);
    duct.position.set(0, -0.35, 0);
    duct.name = "gland_duct";
    duct.userData.kind = "duct";
    group.add(duct);
    parts.duct = new THREE.Vector3(0, -1.0, 0);
  }
  parts.basement_membrane = new THREE.Vector3(width / 2 + 0.2, 0, 0);
  parts.tissue = new THREE.Vector3(width / 2 + 0.2, -0.6, 0);
  parts.layers = new THREE.Vector3(-width / 2 - 0.2, top / 2, 0);
  parts.sheet = new THREE.Vector3(0, top + 0.1, -depth / 2 - 0.2);
  if (member === "ciliated" || member === "pseudostratified") parts.cilia = new THREE.Vector3(0, top + 0.5, 0);
  if (member === "simple_cuboidal") parts.microvilli = new THREE.Vector3(0, top + 0.15, 0);
  if (member === "keratinised") parts.keratin = new THREE.Vector3(0, top + 0.05, depth / 2);
  return { group, parts, layers, top, width, depth };
}

/** The Earth as nested shells with a bar magnet through it (L4, own work): crust, mantle, outer core, inner core. The
 *  cutaway opens a wedge (the shells are built with a missing sector that grows), the exploded view lifts the shells apart. */
export function buildEarth(wedge = 0, explode = 0): Built {
  const group = new THREE.Group();
  const shells: [string, number, string][] = [["inner_core", 1.2, "#ffe08a"], ["outer_core", 2.2, "#ff9a3c"], ["mantle", 3.3, "#c8502e"], ["crust", 3.55, "#3f7fb5"]];
  const parts: Record<string, THREE.Vector3> = {};
  const layers: THREE.Group[] = [];
  const open = wedge * (Math.PI / 2);
  const facing = 2.06;          // the sphere's phi that faces the establishing camera (angle 28°), so the cut is seen head on
  const lift = 1.5;             // the exploded view lifts each shell this much more than the one inside it
  shells.forEach(([name, r, colour], i) => {
    const geo = new THREE.SphereGeometry(r, 48, 32, facing + open / 2, Math.PI * 2 - open, 0, Math.PI);
    const mesh = new THREE.Mesh(geo, mat(colour, { side: THREE.DoubleSide, roughness: 0.7, emissive: colour, emissiveIntensity: name === "outer_core" ? 0.35 : 0.08 }));
    mesh.name = name;
    mesh.userData.kind = name;
    const layer = new THREE.Group();
    layer.add(mesh);
    layer.position.y = explode * i * lift;
    layer.name = `layer_${i}`;
    group.add(layer);
    layers.push(layer);
    // the label anchor sits just inside the open sector at the shell's own radius: seen through the cut, on the surface when closed
    const phi = facing - open / 2 + 0.12;
    parts[name] = new THREE.Vector3(-Math.cos(phi) * r * 0.93, explode * i * lift + 0.15, Math.sin(phi) * r * 0.93);
  });
  // the bar magnet through the centre, tilted 11° like the Earth's dipole, its poles outside the crust
  const magnet = new THREE.Group();
  const north = new THREE.Mesh(new THREE.BoxGeometry(0.5, 4.2, 0.5), mat("#ff5a5a", { emissive: "#ff5a5a", emissiveIntensity: 0.3 }));
  north.position.y = 2.1;
  const south = new THREE.Mesh(new THREE.BoxGeometry(0.5, 4.2, 0.5), mat("#5a8bff", { emissive: "#5a8bff", emissiveIntensity: 0.3 }));
  south.position.y = -2.1;
  magnet.add(north, south);
  magnet.rotation.z = 0.2;
  magnet.name = "magnet";
  north.name = "magnet_north"; north.userData.kind = "magnet"; south.name = "magnet_south"; south.userData.kind = "magnet";
  layers[0].add(magnet);                                 // it stays with the core when the shells lift apart
  parts.north = new THREE.Vector3(-0.9, 4.4, 0);
  parts.south = new THREE.Vector3(0.9, -4.4, 0);
  parts.magnet = parts.north.clone();
  parts.cell = parts.crust;
  return { group, parts, layers, top: 3.55, width: 7.1, depth: 7.1,
    center: new THREE.Vector3(0, explode * lift * 1.5, 0), span: 11 + explode * 3.6 };
}

// A procedural organ for the zoom: simple forms, lit, no outside asset (own work).
function buildOrgan(kind: string): THREE.Group {
  const g = new THREE.Group();
  const m = mat(ORGAN, { roughness: 0.6, transparent: true, opacity: 0.95 });
  if (kind === "lung" || kind === "lungs") {
    for (const s of [-1, 1]) {
      const lobe = new THREE.Mesh(new THREE.SphereGeometry(1.6, 24, 18), m);
      lobe.scale.set(0.8, 1.3, 0.7); lobe.position.set(s * 1.5, -0.3, 0); g.add(lobe);
    }
    const trachea = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 2.2, 10), mat("#e8c9a8"));
    trachea.position.set(0, 1.4, 0); g.add(trachea);
    for (let i = 0; i < 14; i++) {                                           // alveolar sacs at the ends of the tree
      const sac = new THREE.Mesh(new THREE.SphereGeometry(0.16, 10, 8), mat("#f3b0a4"));
      const a = (i / 14) * Math.PI * 2; sac.position.set(Math.cos(a) * 1.0 + (i % 2 ? 1.5 : -1.5), -0.6 + Math.sin(a) * 0.9, 0.5); g.add(sac);
    }
  } else if (kind === "kidney" || kind === "tubule") {
    const bean = new THREE.Mesh(new THREE.SphereGeometry(1.5, 24, 18), m);
    bean.scale.set(0.7, 1.2, 0.5); g.add(bean);
    const tube = new THREE.Mesh(new THREE.TorusKnotGeometry(0.55, 0.08, 80, 8, 2, 3), mat("#f0c07a"));
    tube.position.set(0.2, 0.1, 0.5); g.add(tube);
  } else if (kind === "intestine" || kind === "gut") {
    const tube = new THREE.Mesh(new THREE.TorusGeometry(1.4, 0.42, 14, 40, Math.PI * 1.5), m);
    g.add(tube);
    for (let i = 0; i < 24; i++) {                                           // villi on the inner wall
      const v = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.07, 0.3, 6), mat("#f3b0a4"));
      const a = (i / 24) * Math.PI * 1.5; v.position.set(Math.cos(a) * 1.0, Math.sin(a) * 1.0, 0); v.rotation.z = a - Math.PI / 2; g.add(v);
    }
  } else if (kind === "bladder") {
    const sac = new THREE.Mesh(new THREE.SphereGeometry(1.5, 24, 18), m);
    sac.scale.set(1.1, 0.9, 0.9); g.add(sac);
    const ureter = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 2.4, 8), mat("#f0c07a"));
    ureter.position.set(1.0, 1.6, 0); ureter.rotation.z = -0.4; g.add(ureter);
  } else if (kind === "skin") {
    const slab = new THREE.Mesh(new THREE.BoxGeometry(4, 0.5, 2.6), mat("#d9a98b"));
    const derm = new THREE.Mesh(new THREE.BoxGeometry(4, 0.9, 2.6), mat("#c97d7d"));
    derm.position.y = -0.7; g.add(slab, derm);
  } else {                                                                   // a duct or any hollow organ
    const tube = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.9, 3.2, 20, 1, true), new THREE.MeshStandardMaterial({ color: ORGAN, side: THREE.DoubleSide, roughness: 0.6 }));
    tube.rotation.z = Math.PI / 2; g.add(tube);
  }
  return g;
}

const loader = new GLTFLoader();
const loadGlb = (src: string) => new Promise<THREE.Group>((res, rej) => loader.load(assetUrl(src), (g) => res(g.scene), undefined, (e) => rej(new Error(`glTF ${src}: ${e}`))));

function fromGlb(scene: THREE.Group): Built {
  // a Blender-made sheet (route C): the same names as the procedural one (cell_, nucleus_, basement_membrane ...)
  const group = scene.clone(true);
  const box = new THREE.Box3().setFromObject(group);
  const size = box.getSize(new THREE.Vector3());
  const parts: Record<string, THREE.Vector3> = {};
  const layers: THREE.Group[] = [];
  const byLayer = new Map<string, THREE.Group>();
  group.traverse((o: any) => {
    if (!o.isMesh) return;
    const name: string = o.name || "";
    if (name.startsWith("cell_")) o.userData.kind = name.includes("keratin") ? "keratin" : "cell";
    else if (name.startsWith("nucleus_")) o.userData.kind = "nucleus";
    else if (name.startsWith("basement")) o.userData.kind = "basement_membrane";
    else if (name.startsWith("cilium")) o.userData.kind = "cilia";
    else if (name.startsWith("microvillus")) o.userData.kind = "microvilli";
    else if (name.startsWith("gland") || name.startsWith("duct")) o.userData.kind = "duct";
    else if (name.startsWith("underlying") || name.startsWith("tissue")) o.userData.kind = "tissue";
    const li = name.match(/^(?:cell|nucleus)_(\d+)_\d+_\d+$/)?.[1] ?? "0";
    if (o.userData.kind === "cell" || o.userData.kind === "nucleus" || o.userData.kind === "keratin") {
      if (!byLayer.has(li)) { const g = new THREE.Group(); g.name = `layer_${li}`; byLayer.set(li, g); }
      o.userData.layer = li;
    }
  });
  for (const [, g] of byLayer) layers.push(g);
  const centre = box.getCenter(new THREE.Vector3());
  parts.cell = new THREE.Vector3(centre.x, box.max.y * 0.9, centre.z);
  parts.nucleus = new THREE.Vector3(centre.x, box.max.y * 0.5, centre.z);
  parts.top = new THREE.Vector3(centre.x, box.max.y + 0.3, centre.z);
  parts.junction = new THREE.Vector3(centre.x + 0.4, box.max.y * 0.6, centre.z);
  parts.basement_membrane = new THREE.Vector3(box.max.x + 0.2, 0, centre.z);
  parts.tissue = new THREE.Vector3(box.max.x + 0.2, -0.6, centre.z);
  parts.layers = new THREE.Vector3(box.min.x - 0.2, box.max.y / 2, centre.z);
  parts.sheet = new THREE.Vector3(centre.x, box.max.y + 0.1, box.min.z - 0.2);
  return { group, parts, layers, top: box.max.y, width: size.x, depth: size.z };
}

// ---------------------------------------------------------------- the shot timeline

export type Shot = {
  at: number; until?: number;                 // frames, relative to the layer's start
  member?: Member;
  focus?: string | string[];                  // part kinds to light: cell, nucleus, basement_membrane, cilia, microvilli, keratin, junction, duct, layers, top
  flow?: { kind: "absorb" | "secrete" | "cross" | "sweep" | "shed" | "none"; particles?: number; seconds?: number };
  camera?: { move: "establish" | "hold" | "pan" | "zoom_in" | "zoom_out" | "orbit"; target?: string; seconds?: number };
  cutaway?: boolean; exploded?: boolean; stretch?: boolean; dim?: boolean;
  labels?: { text: string; part: string }[];
  organ?: string;                             // organ_zoom: the shot starts far at this organ and comes down to the sheet
  caption_terms?: string[];
};

type Cam = { angle: number; distance: number; height: number; target: THREE.Vector3; fov: number };

function currentShot(shots: Shot[], rel: number): { shot: Shot; index: number; since: number } {
  let index = 0;
  for (let i = 0; i < shots.length; i++) if (rel >= shots[i].at) index = i;
  const shot = shots[index] || { at: 0 };
  return { shot, index, since: rel - shot.at };
}

/** Frames since a flag (cutaway, exploded, stretch) came on, counted from the first of the consecutive shots that carry
 *  it, so a cut stays open while the next sentence keeps it instead of closing and opening again. */
function flagSince(shots: Shot[], rel: number, key: "cutaway" | "exploded" | "stretch"): number {
  const { index } = currentShot(shots, rel);
  let first = index;
  while (first > 0 && (shots[first - 1] as any)[key]) first--;
  return rel - (shots[first]?.at ?? 0);
}

function cameraFor(shot: Shot, previous: Cam | null, built: Built, seed: number): Cam {
  const span = built.span ?? Math.max(built.width, built.depth, built.top * 1.8);
  const centre = built.center ?? new THREE.Vector3(0, built.top / 2, 0);
  const focusKey = typeof shot.focus === "string" ? shot.focus : shot.focus?.[0];
  const target = (shot.camera?.target && built.parts[shot.camera.target]) || (focusKey && built.parts[focusKey]) || centre.clone();
  const base: Cam = { angle: 28, distance: span * 1.35, height: span * 0.7, target: centre.clone(), fov: 38 };
  const move = shot.camera?.move || "hold";
  const prev = previous || base;
  if (shot.organ) return { angle: prev.angle, distance: span * 4.2, height: span * 1.6, target: new THREE.Vector3(0, built.top, 0), fov: 44 };
  if (move === "establish") return base;
  if (move === "hold") return { ...prev, target: prev.target.clone() };
  // a zoom comes closer to the lit part but keeps dark space around the subject (B-11): never a frame filled with the sheet
  if (move === "zoom_in") return { angle: prev.angle + 4, distance: Math.max(span * 1.15, prev.distance * 0.85), height: Math.max(span * 0.55, prev.height * 0.8), target: target.clone(), fov: 36 };
  if (move === "zoom_out") return { angle: prev.angle - 3, distance: Math.min(span * 1.7, Math.max(prev.distance * 1.4, span * 1.35)), height: Math.min(span * 0.95, Math.max(prev.height * 1.35, span * 0.7)), target: centre.clone(), fov: 40 };
  if (move === "orbit") return { ...prev, angle: prev.angle + 26 + (seed % 3) * 4, distance: Math.max(prev.distance, span * 1.0), target: prev.target.clone() };
  if (move === "pan") return { angle: prev.angle + 10, distance: span * 1.3, height: span * 0.62, target: target.clone(), fov: 38 };
  return base;
}

function lerpCam(a: Cam, b: Cam, t: number): Cam {
  return { angle: a.angle + (b.angle - a.angle) * t, distance: a.distance + (b.distance - a.distance) * t, height: a.height + (b.height - a.height) * t,
    target: a.target.clone().lerp(b.target, t), fov: a.fov + (b.fov - a.fov) * t };
}

/** The camera of frame ``rel``: every shot's camera eases from the one before over its first seconds (VG-01). */
export function cameraAt(shots: Shot[], rel: number, built: Built, fps: number): { cam: Cam; shot: Shot; index: number; since: number; organT: number } {
  let cam: Cam | null = null;
  let from: Cam | null = null;
  const { shot, index, since } = currentShot(shots, rel);
  for (let i = 0; i <= index; i++) {
    from = cam;
    const changed = i > 0 && shots[i].member && shots[i].member !== (shots[i - 1].member || shots[0].member);
    cam = cameraFor(changed ? { ...shots[i], camera: { move: "establish" } } : shots[i], cam, built, i);
  }
  const seconds = shot.camera?.seconds ?? (shot.organ ? 2.2 : 0.9);
  const t = ramp(since, 0, seconds * fps);
  let now = from && cam ? lerpCam(from, cam, t) : cam!;
  let organT = 0;
  if (shot.organ) {                               // the zoom: start far at the organ, arrive at the sheet by the end of the shot
    const length = Math.max(1, (shot.until ?? shot.at + 3 * fps) - shot.at);
    organT = ramp(since, 0, length * 0.85);
    const near = cameraFor({ ...shot, organ: undefined, camera: { move: "zoom_in" } }, cam, built, index);
    now = lerpCam(cam!, near, organT);
  }
  return { cam: now, shot, index, since, organT };
}

function cameraPose(cam: Cam): { position: THREE.Vector3; target: THREE.Vector3 } {
  const a = (cam.angle * Math.PI) / 180;
  return { position: new THREE.Vector3(cam.target.x + Math.sin(a) * cam.distance, cam.target.y + cam.height, cam.target.z + Math.cos(a) * cam.distance), target: cam.target };
}

/** Where a 3D point lands on the block's pixels, for leader labels (VG-02). */
export function project(point: THREE.Vector3, cam: Cam, width: number, height: number): { x: number; y: number; behind: boolean } {
  const camera = new THREE.PerspectiveCamera(cam.fov, width / height, 0.01, 500);
  const pose = cameraPose(cam);
  camera.position.copy(pose.position);
  camera.lookAt(pose.target);
  camera.updateMatrixWorld();
  camera.updateProjectionMatrix();
  const v = point.clone().project(camera);
  return { x: ((v.x + 1) / 2) * width, y: ((1 - v.y) / 2) * height, behind: v.z > 1 };
}

const CameraRig: React.FC<{ cam: Cam; aspect: number }> = ({ cam }) => {
  const pose = cameraPose(cam);
  return <PerspectiveCamera makeDefault fov={cam.fov} position={pose.position.toArray() as [number, number, number]} near={0.01} far={500}
    ref={(c: any) => { if (c) { c.lookAt(pose.target); c.updateMatrixWorld(); } }} />;
};

const Lights: React.FC<{ accent: string }> = ({ accent }) => (
  <>
    <hemisphereLight args={[0xffffff, 0x1a2a3a, 1.1]} />
    <directionalLight position={[5, 9, 6]} intensity={2.4} />
    <directionalLight position={[-7, 4, -5]} intensity={0.9} color={accent} />
    <pointLight position={[0, 6, 0]} intensity={14} distance={30} decay={2} color={accent} />
  </>
);

// ---------------------------------------------------------------- particles (B-04)

function Particles({ flow, rel, fps, built, accent }: { flow: NonNullable<Shot["flow"]>; rel: number; fps: number; built: Built; accent: string }) {
  if (!flow || flow.kind === "none") return null;
  const n = flow.particles ?? 36;
  const period = (flow.seconds ?? 2.4) * fps;
  const w = built.width, d = built.depth, top = built.top;
  const dots = [];
  for (let i = 0; i < n; i++) {
    const s1 = Math.sin(i * 12.9898) * 43758.5453, fx = s1 - Math.floor(s1);
    const s2 = Math.sin(i * 78.233) * 12345.678, fz = s2 - Math.floor(s2);
    const t = (((rel / period) + i / n) % 1 + 1) % 1;
    let x = (fx - 0.5) * w, z = (fz - 0.5) * d, y = 0;
    if (flow.kind === "absorb") y = top + 1.2 - t * (top + 2.4);
    else if (flow.kind === "secrete") y = -0.6 + t * (top + 1.9);
    else if (flow.kind === "cross") y = i % 2 ? top + 1.2 - t * (top + 2.4) : -0.6 + t * (top + 1.9);
    else if (flow.kind === "sweep") { x = -w / 2 + t * w; y = top + 0.42 + 0.12 * Math.sin(t * 12 + i); }
    else if (flow.kind === "shed") { y = top + 0.05 + t * 1.6; x += t * 0.8 * (fx - 0.5); }
    dots.push(<mesh key={i} position={[x, y, z]}><sphereGeometry args={[Math.max(w, d) * 0.011, 10, 8]} />
      <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={1.1} /></mesh>);
  }
  return <>{dots}</>;
}

// ---------------------------------------------------------------- the world

const Overlay: React.FC<{ labels: { text: string; part: string }[]; built: Built; cam: Cam; width: number; height: number; since: number; accent: string }> =
  ({ labels, built, cam, width, height, since, accent }) => {
    const draw = ramp(since, 4, 14);
    return (
      <>
        <svg style={{ position: "absolute", inset: 0, width, height, overflow: "visible", pointerEvents: "none" }}>
          {labels.map((l, i) => {
            const p = built.parts[l.part];
            if (!p) return null;
            const s = project(p, cam, width, height);
            if (s.behind) return null;
            const lx = width * 0.78, ly = height * (0.22 + i * 0.11);
            return <g key={i} opacity={draw}>
              <line x1={lx} y1={ly} x2={lx + (s.x - lx) * draw} y2={ly + (s.y - ly) * draw} stroke={accent} strokeWidth={3.5} />
              <circle cx={s.x} cy={s.y} r={9 * draw} fill={accent} stroke="#06121c" strokeWidth={3} />
            </g>;
          })}
        </svg>
        {labels.map((l, i) => {
          const p = built.parts[l.part];
          if (!p) return null;
          const s = project(p, cam, width, height);
          if (s.behind) return null;
          const ly = height * (0.22 + i * 0.11);
          return <div key={i} style={{ position: "absolute", left: width * 0.78, top: ly - 26, transform: "translateX(0)", opacity: draw, fontFamily: FONT,
            fontSize: 30, fontWeight: 700, color: C.ink, background: C.panel, border: `3px solid ${accent}`, borderRadius: 12, padding: "8px 16px",
            whiteSpace: "nowrap" }}>{l.text}</div>;
        })}
      </>
    );
  };

const CellWorld: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const dpr = Math.min(1, useVideoConfig().width / STAGE_W);          // a 720p output draws the 3D at 720p (the stage scales the rest)
  const shots: Shot[] = (data.shots && data.shots.length ? data.shots : [{ at: 0, ...data }]) as Shot[];
  const { shot, since, organT } = { ...cameraAt(shots, rel, { width: 1, depth: 1, top: 1, group: new THREE.Group(), parts: {}, layers: [] }, fps) };
  const member: Member = (shot.member || data.member || "simple_columnar") as Member;
  const accent = data.accent || (data.world === "earth" ? "#ffb35c" : ACCENT[member]) || C.accent;
  const earth = data.world === "earth";
  // route C: a Blender-made glTF for this member (data.models[member]) or for the scene (data.src); otherwise the procedural sheet
  const src: string | undefined = (data.models && data.models[member]) || data.src;
  const glb = useAsset(`sheet:${earth ? "earth" : src || "procedural:" + member + (data.rows || 5) + "x" + (data.cols || 7)}`,
    () => (earth ? Promise.resolve(new THREE.Group()) : src ? loadGlb(src) : Promise.resolve(buildSheet(member, data.rows || 5, data.cols || 7).group)));
  const { shot: shotNow } = currentShot(shots, rel);
  const wedgeNow = earth && shotNow.cutaway ? ramp(flagSince(shots, rel, "cutaway"), 0, 1.2 * fps) : 0;
  const explodeNow = earth && shotNow.exploded ? ramp(flagSince(shots, rel, "exploded"), 0, 1.2 * fps) : 0;
  const built = useMemo(() => {
    if (!glb) return null;
    if (earth) return buildEarth(wedgeNow, explodeNow);
    if (src) return fromGlb(glb);
    return buildSheet(member, data.rows || 5, data.cols || 7);
  }, [glb, member, src, data.rows, data.cols, earth, wedgeNow, explodeNow]);
  const organ = useMemo(() => (shot.organ ? buildOrgan(shot.organ) : null), [shot.organ]);
  if (!built) return null;
  const view = cameraAt(shots, rel, built, fps);
  const cam = view.cam;
  // focus glow (B-10): the lit parts pulse, the rest dims a little
  const focus = new Set<string>(Array.isArray(shot.focus) ? shot.focus : shot.focus ? [shot.focus] : []);
  const glow = clamp01(0.55 + 0.45 * Math.sin((since / fps) * 3.2)) * ramp(since, 0, 10);
  const cut = shot.cutaway ? ramp(flagSince(shots, rel, "cutaway"), 0, 0.9 * fps) : 0;
  const explode = shot.exploded ? ramp(flagSince(shots, rel, "exploded"), 0, 1.1 * fps) : 0;
  const stretch = shot.stretch ? ramp(flagSince(shots, rel, "stretch"), 0, 1.2 * fps) : 0;
  built.group.traverse((o: any) => {
    if (!o.isMesh) return;
    const kind = o.userData.kind as string | undefined;
    if (earth) {
      const m = o.material as THREE.MeshStandardMaterial;
      const lit = kind && focus.has(kind);
      if (lit) { m.emissiveIntensity = 0.5 + 0.5 * glow; }
      return;
    }
    const m = o.material as THREE.MeshStandardMaterial;
    const lit = (kind && focus.has(kind)) || (focus.has("layers") && (kind === "cell" || kind === "keratin")) || (focus.has("top") && kind === "cell" && o.userData.layer === undefined && false);
    const anyFocus = focus.size > 0;
    const many = kind === "cell" || kind === "keratin" || kind === "cilia" || kind === "microvilli";
    m.emissive = new THREE.Color(lit ? accent : "#000000");
    m.emissiveIntensity = lit ? (many ? 0.12 + 0.18 * glow : 0.35 + 0.65 * glow) : 0;
    if (m.transparent) m.opacity = lit ? 1 : anyFocus ? 0.62 : 0.92;
    if (kind === "cilia") o.rotation.z = Math.sin((rel / fps) * 7 + (o.userData.phase || 0)) * 0.35;           // cilia beat
    if (kind === "cell" && stretch > 0) o.scale.set(1 + 0.12 * stretch, 1 - 0.45 * stretch, 1 + 0.12 * stretch);  // transitional stretches flat
    if (shot.dim) { m.transparent = true; m.opacity = Math.min(m.opacity, 0.38); }                                   // a panel teaches: the world rests
    // cutaway (VG-03): the near half of the sheet opens from the front edge inward, showing the layers' sides, the membrane and the tissue
    if ((kind === "cell" || kind === "nucleus" || kind === "keratin" || kind === "cilia" || kind === "microvilli") && cut > 0)
      o.visible = o.position.z < built.depth / 2 - cut * built.depth * 0.55;
    else o.visible = true;
  });
  if (!earth) built.layers.forEach((layer, i) => { layer.position.y = explode * 0.9 * i; });     // exploded view: the layers lift apart
  const labels = shot.labels || [];
  const organScale = organ ? 1 + 0.4 * (1 - organT) : 1;
  return (
    <>
      <ThreeCanvas width={width} height={height} dpr={dpr} gl={{ alpha: true, preserveDrawingBuffer: true, antialias: true }}>
        <Lights accent={accent} />
        <CameraRig cam={cam} aspect={width / height} />
        <fog attach="fog" args={["#06121c", cam.distance * 0.9, cam.distance * 3.2]} />
        <primitive object={built.group} />
        {shot.flow ? <Particles flow={shot.flow} rel={since} fps={fps} built={built} accent={accent} /> : null}
        {organ ? <primitive object={organ} position={[0, built.top + 2.2 + 3 * (1 - organT), 0]} scale={[organScale, organScale, organScale]}
          visible={organT < 0.97} /> : null}
      </ThreeCanvas>
      {/* depth and focus: a vignette and a soft glow around the frame, in code (L5a look) */}
      <div style={{ position: "absolute", inset: 0, pointerEvents: "none", boxShadow: "inset 0 0 220px rgba(0,0,0,0.75)" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 8, background: `linear-gradient(90deg, transparent, ${accent}, transparent)`, opacity: 0.35 }} />
      <Overlay labels={labels} built={built} cam={cam} width={width} height={height} since={since} accent={accent} />
      {shot.organ && organT < 0.8 ? <div style={{ position: "absolute", left: 40, top: 30, fontFamily: FONT, fontSize: 34, fontWeight: 800, color: C.ink, opacity: 1 - organT / 0.8 }}>
        {data.organ_label || shot.organ}</div> : null}
    </>
  );
};

// Each benchmark name draws the same world with a preset, so a spec can ask for it by the rule it serves (and each has a demo).
const preset = (extra: Partial<Shot>): React.FC<BlockProps> => (props) =>
  <CellWorld {...props} data={{ ...props.data, shots: props.data.shots || [{ at: 0, ...extra, ...props.data }] }} />;

registerBlock("cell_sheet", CellWorld);
registerBlock("particle_flow", preset({ flow: { kind: "absorb", particles: 40, seconds: 2.4 }, focus: "cell" }));
registerBlock("focus_glow", preset({ focus: "nucleus", camera: { move: "zoom_in" } }));
registerBlock("organ_zoom", preset({ organ: "lung", focus: "cell" }));
registerBlock("leader_label", preset({ labels: [{ text: "basement membrane", part: "basement_membrane" }, { text: "nucleus", part: "nucleus" }] }));
registerBlock("camera_path", preset({ camera: { move: "orbit", seconds: 3 } }));
registerBlock("cutaway", preset({ cutaway: true, focus: "basement_membrane", camera: { move: "zoom_in", target: "basement_membrane" } }));
registerBlock("exploded_view", preset({ exploded: true, member: "stratified_squamous", focus: "layers" }));
