// The box rule's measuring tape (Navin, 5 November 2026): the scene-plan compiler (bie/brain/video/boxes.py) sends one
// JSON request on stdin and reads every box back from the engine's own drawings, at ₹0 and with no browser.
//
//   node tools/saancha_boxes.mjs < request.json > boxes.json
//
// request: { "items": [{"draw": name, "p": {...}}], "persons": [{"h": 440, "look": "ramu"}], "bgs": ["shop"],
//            "worlds": [{...world p}] }
// answer:  { "items": [{"box": [x0,y0,x1,y1], "texts": [{"t", "px", "box"}]}], "persons": [{"box", "face"}],
//            "zones": {"shop": [{"name", "keep", "box"}]}, "worlds": [[{"name", "keep", "box"}]] }
import { boxOf } from "../bie/brain/video/engine/draw.mjs";
import { personBoxes } from "../bie/brain/video/engine/people.mjs";
import { zonesOf, worldZones } from "../bie/brain/video/engine/backgrounds.mjs";

let raw = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => (raw += c));
process.stdin.on("end", () => {
  const req = raw.trim() ? JSON.parse(raw) : {};
  const safe = (fn) => { try { return fn(); } catch (e) { return { box: null, texts: [], error: String(e && e.message || e) }; } };
  const out = {
    items: (req.items || []).map((it) => safe(() => boxOf(it.draw, it.p || {}))),
    persons: (req.persons || []).map((pr) => safe(() => personBoxes(pr))),
    zones: Object.fromEntries((req.bgs || []).map((b) => [b, zonesOf(b)])),
    worlds: (req.worlds || []).map((p) => worldZones(p || {})),
  };
  process.stdout.write(JSON.stringify(out));
});
