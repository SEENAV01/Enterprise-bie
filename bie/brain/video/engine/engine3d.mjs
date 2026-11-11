// The showing engine with its 3D layer (engine3d.js): the same engine as engine.js plus three.js, built only when a
// show-spec has a 3D model element (render.py needs_3d), so plain 2D videos never need three.js installed.
import { setLayer3d } from "./engine.mjs";
import { layer } from "./three/layer3d.mjs";

setLayer3d(layer);
window.__BIE_3D__ = layer.version;
window.__BIE_3D_STATS__ = layer.stats;
