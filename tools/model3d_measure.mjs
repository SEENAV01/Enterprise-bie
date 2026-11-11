// The 3D layer's measuring tape (bie/brain/video/models3d.py): the scene-plan compiler sends one JSON request on stdin
// and reads back, from the very description the engine draws (engine/three/scene3d.mjs), where a 3D model's spots,
// box and zones land on the stage at given times, the problems of its parameters that types cannot see, and the kinds.
//
//   node tools/model3d_measure.mjs < request.json > answer.json
//
// request: { "measures": [{"el": {model element}, "t": seconds}], "checks": [{"model", "p"}], "describe": [{"el", "t"}],
//            "kinds": true }
// answer:  { "measures": [{"spots": {name: {x, y, front}}, "box", "zones": [{name, keep, box}], "rect"} | {"error"}],
//            "checks": [[problem, ...]], "describe": [{"nodes", "spots", "cam", "env"}], "kinds": {name: {camera}} }
import { KINDS, measure, check, frameModel } from "../bie/brain/video/engine/three/scene3d.mjs";

let raw = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (raw += c));
process.stdin.on("end", () => {
  const req = raw.trim() ? JSON.parse(raw) : {};
  const safe = (fn) => { try { return fn(); } catch (e) { return { error: String((e && e.message) || e) }; } };
  const out = {
    measures: (req.measures || []).map((m) => safe(() => measure(m.el, m.t))),
    checks: (req.checks || []).map((c) => { try { return check(c.model, c.p || {}); } catch (e) { return [String(e.message || e)]; } }),
    describe: (req.describe || []).map((d) => safe(() => { const f = frameModel(d.el, d.t); return { nodes: f.nodes, spots: f.spots, cam: f.cam, env: f.env }; })),
  };
  if (req.kinds) out.kinds = Object.fromEntries(Object.entries(KINDS).map(([k, v]) => [k, { camera: v.camera, check: !!v.check }]));
  process.stdout.write(JSON.stringify(out));
});
