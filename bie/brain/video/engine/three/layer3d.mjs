// The 3D layer of the showing engine (bundled only into engine3d.js, never into the plain engine.js): draws a model
// element's description (scene3d.mjs frameModel) with three.js (the toolbox's pinned three 0.186.1, MIT) into one
// WebGL canvas at the frame size, once per frame, inside the element's rectangle on the screen. The engine copies that
// canvas into the element's own layer between the SVG layers (engine.mjs), so a 3D place sits under the people and
// words and a 3D model sits at its own z. Same description -> same draw calls -> same pixels: nothing here keeps time.
// Speed: geometries and materials are cached by their numbers; nodes that share both are drawn as one InstancedMesh.
import * as THREE from "three";
import MAP_LAND from "../map_land.json";
import { frameModel } from "./scene3d.mjs";

let renderer = null;
const geoCache = new Map(), matCache = new Map(), instPool = new Map(), meshPool = [];
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, 16 / 9, 0.1, 1000);
const hemi = new THREE.HemisphereLight(0xffffff, 0x888888, 2);
const sun = new THREE.DirectionalLight(0xffffff, 1.5);
const fog = new THREE.Fog(0xffffff, 10, 100);
const dummy = new THREE.Object3D();
dummy.rotation.order = "YXZ";
let landTex = null;

function ensure(W, H) {
  if (!renderer) {
    renderer = new THREE.WebGLRenderer({ canvas: document.createElement("canvas"), antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(1);
    renderer.autoClear = false;
  }
  const c = renderer.domElement;
  if (c.width !== W || c.height !== H) renderer.setSize(W, H, false);
}

function land() {
  if (landTex) return landTex;
  const c = document.createElement("canvas");
  c.width = 2048; c.height = 1024;
  const g = c.getContext("2d");
  g.fillStyle = "#4f8fc0"; g.fillRect(0, 0, 2048, 1024);
  g.strokeStyle = "rgba(255,255,255,0.13)"; g.lineWidth = 2;
  for (let k = 1; k < 12; k++) { g.beginPath(); g.moveTo((k * 2048) / 12, 0); g.lineTo((k * 2048) / 12, 1024); g.stroke(); }
  for (let k = 1; k < 6; k++) { g.beginPath(); g.moveTo(0, (k * 1024) / 6); g.lineTo(2048, (k * 1024) / 6); g.stroke(); }
  // map_land.json: equirectangular, lon -180..180 -> x 0..1920, lat 78..-58 -> y 0..1080; the texture spans lat 90..-90
  g.setTransform(2048 / 1920, 0, 0, ((136 / 1080) * 1024) / 180, 0, (12 * 1024) / 180);
  g.fillStyle = "#e0d2a4"; g.strokeStyle = "#bfa871"; g.lineWidth = 2.5;
  for (const d of MAP_LAND.paths) { const p = new Path2D(d); g.fill(p); g.stroke(p); }
  landTex = new THREE.CanvasTexture(c);
  landTex.colorSpace = THREE.SRGBColorSpace;
  landTex.anisotropy = 4;
  return landTex;
}

function surface(a) {
  const n = a.n || 40, S = a.size, H = a.h, pos = [], col = [], idx = [];
  const lo = new THREE.Color("#7cc47f"), mid = new THREE.Color("#f2c14e"), hi = new THREE.Color("#f29f05"), c = new THREE.Color();
  const top = Math.pow(S, a.a + a.b);
  for (let j = 0; j <= n; j++) for (let i = 0; i <= n; i++) {
    const X = (i / n) * S, Y = (j / n) * S, h = (H * Math.pow(X, a.a) * Math.pow(Y, a.b)) / top, k = h / H;
    pos.push(X, h, -Y);
    if (k < 0.5) c.copy(lo).lerp(mid, k * 2); else c.copy(mid).lerp(hi, (k - 0.5) * 2);
    col.push(c.r, c.g, c.b);
  }
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
    const q = j * (n + 1) + i;
    idx.push(q, q + 1, q + n + 1, q + 1, q + n + 2, q + n + 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

function geometry(nd) {
  const key = nd.g + ":" + JSON.stringify(nd.a);
  let g = geoCache.get(key);
  if (g) return g;
  const a = nd.a;
  switch (nd.g) {
    case "box": g = new THREE.BoxGeometry(a[0], a[1], a[2]); break;
    case "cyl": g = new THREE.CylinderGeometry(a[0], a[1], a[2], a[3] || 12); break;
    case "prism": g = new THREE.CylinderGeometry(a[0], a[0], a[1], 3); break;
    case "cone": g = new THREE.ConeGeometry(a[0], a[1], a[2] || 8); break;
    case "sphere": g = new THREE.SphereGeometry(a[0], a[1], a[2]); break;
    case "ico": g = new THREE.IcosahedronGeometry(a[0], a[1]); break;
    case "torus": g = new THREE.TorusGeometry(a[0], a[1], a[2], a[3]); break;
    case "tube": g = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(a.pts.map((v) => new THREE.Vector3(v[0], v[1], v[2]))), a.seg, a.r, 8, false); break;
    case "surface": g = surface(a); break;
    case "globe": g = new THREE.SphereGeometry(a[0], 72, 48); break;
    default: throw new Error(`BIE_3D_NODE: no geometry '${nd.g}'`);
  }
  geoCache.set(key, g);
  return g;
}

function material(nd) {
  const m = nd.g === "globe" ? "globe" : nd.m || "flat", o = nd.o ?? 1, e = nd.e || 0;
  const key = `${m}|${nd.c}|${e}|${o}`;
  let mat = matCache.get(key);
  if (mat) return mat;
  const tr = { transparent: o < 1, opacity: o, depthWrite: o >= 0.99 };
  if (m === "basic") mat = new THREE.MeshBasicMaterial({ color: nd.c, ...tr });
  else if (m === "vcol") mat = new THREE.MeshLambertMaterial({ vertexColors: true, flatShading: true, side: THREE.DoubleSide, ...tr });
  else if (m === "globe") mat = new THREE.MeshLambertMaterial({ map: land() });
  else mat = new THREE.MeshLambertMaterial({ color: nd.c, flatShading: m === "flat", emissive: e ? nd.c : 0x000000, emissiveIntensity: e, ...tr });
  matCache.set(key, mat);
  return mat;
}

function placeOf(obj, nd) {
  obj.position.set(nd.p[0], nd.p[1], nd.p[2]);
  obj.rotation.order = "YXZ";
  if (nd.r) obj.rotation.set(nd.r[0], nd.r[1], nd.r[2], "YXZ"); else obj.rotation.set(0, 0, 0, "YXZ");
  if (nd.s) obj.scale.set(nd.s[0] || 1e-4, nd.s[1] || 1e-4, nd.s[2] || 1e-4); else obj.scale.set(1, 1, 1);
}

/** Builds the scene of one description: nodes that share a geometry and a material become one InstancedMesh. */
function build(fm) {
  if (geoCache.size > 4000) { for (const g of geoCache.values()) g.dispose(); geoCache.clear(); instPool.clear(); }
  scene.clear();
  const env = fm.env || {};
  const [hs, hg, hi] = env.hemi || ["#ffffff", "#b9b2a4", 2.1], [sc, si, sd] = env.sun || ["#ffffff", 1.6, [0.45, 1, 0.55]];
  hemi.color.set(hs); hemi.groundColor.set(hg); hemi.intensity = hi;
  sun.color.set(sc); sun.intensity = si; sun.position.set(sd[0] * 50, sd[1] * 50, sd[2] * 50);
  scene.add(hemi, sun);
  if (env.fog) { fog.color.set(env.fog.c); fog.near = env.fog.near; fog.far = env.fog.far; scene.fog = fog; } else scene.fog = null;
  const groups = new Map();
  for (const nd of fm.nodes) {
    const k = nd.g + ":" + JSON.stringify(nd.a) + "|" + (nd.m || "") + "|" + nd.c + "|" + (nd.e || 0) + "|" + (nd.o ?? 1);
    let list = groups.get(k);
    if (!list) groups.set(k, (list = []));
    list.push(nd);
  }
  let used = 0;
  for (const [k, list] of groups) {
    const geo = geometry(list[0]), mat = material(list[0]);
    if (list.length >= 6) {
      let slot = instPool.get(k);
      if (!slot || slot.cap < list.length) {
        const cap = Math.max(16, list.length * 2);
        slot = { mesh: new THREE.InstancedMesh(geo, mat, cap), cap };
        slot.mesh.frustumCulled = false;
        instPool.set(k, slot);
      }
      list.forEach((nd, i) => { placeOf(dummy, nd); dummy.updateMatrix(); slot.mesh.setMatrixAt(i, dummy.matrix); });
      slot.mesh.count = list.length;
      slot.mesh.instanceMatrix.needsUpdate = true;
      scene.add(slot.mesh);
    } else {
      for (const nd of list) {
        let mesh = meshPool[used];
        if (!mesh) meshPool.push((mesh = new THREE.Mesh(geo, mat)));
        mesh.geometry = geo; mesh.material = mat;
        placeOf(mesh, nd);
        scene.add(mesh);
        used++;
      }
    }
  }
}

/** Draws model element ``el`` at show time ``t`` into the frame-size WebGL canvas, inside ``rect`` (frame pixels,
 * {x, y, w, h} from the top left), and returns that canvas. A 3D place paints its sky behind it; a model stays clear. */
const stats = { describe: 0, build: 0, draw: 0, frames: 0 };     // milliseconds summed over frames (the speed check)
function render(el, t, rect, W, H) {
  ensure(W, H);
  const t0 = performance.now();
  const fm = frameModel(el, t);
  const t1 = performance.now();
  build(fm);
  const t2 = performance.now();
  const v = fm.view;
  camera.fov = v.fov; camera.aspect = rect.w / rect.h; camera.near = v.near; camera.far = v.far;
  camera.position.set(v.eye[0], v.eye[1], v.eye[2]);
  camera.up.set(v.up[0], v.up[1], v.up[2]);
  camera.lookAt(v.target[0], v.target[1], v.target[2]);
  camera.updateProjectionMatrix();
  renderer.setScissorTest(false);
  renderer.setClearColor(0x000000, 0);
  renderer.clear(true, true, true);
  const x0 = Math.max(0, Math.floor(rect.x)), y0 = Math.max(0, Math.floor(rect.y));
  const x1 = Math.min(W, Math.ceil(rect.x + rect.w)), y1 = Math.min(H, Math.ceil(rect.y + rect.h));
  if (x1 <= x0 || y1 <= y0) return renderer.domElement;
  renderer.setViewport(rect.x, H - rect.y - rect.h, rect.w, rect.h);
  renderer.setScissor(x0, H - y1, x1 - x0, y1 - y0);
  renderer.setScissorTest(true);
  if (fm.place) { renderer.setClearColor(fm.env.sky || "#cfe8f5", 1); renderer.clear(true, true, true); }
  renderer.render(scene, camera);
  renderer.setScissorTest(false);
  stats.describe += t1 - t0; stats.build += t2 - t1; stats.draw += performance.now() - t2; stats.frames++;
  return renderer.domElement;
}

export const layer = { render, stats, canvas: () => (renderer ? renderer.domElement : null), version: THREE.REVISION };
