# Asset intake (reference videos → shot cards → needs list → Blender recipes)

Staging area, kept apart from `main` work, for what BIE learns from reference videos and the first recipes built from
it (Navin, 26–27 Oct 2026). Nothing here is wired into the pipeline yet; Claude Code picks it up when Task 046/047
needs it (move recipes into `bie/toolbox/blender/`, register them, add tests). Status: IMPLEMENTED, not INTEGRATED.

No footage, frames or text from any reference video is stored here: shot cards are our own descriptions.

## Contents

| Path | What it is |
| --- | --- |
| `shot_cards/*.json` | 118 shot cards from 12 reference videos (about 96 minutes), written from code-detected shots and their frames. Same schema as the Gemini prompt, plus `recipe_needs`. |
| `needs_list.json` | The aggregated "what to build" list: families of models, motions, looks, cameras and text styles, ranked by how many videos use them and for how many seconds. |
| `tools/split.py` | Code shot splitter (ffmpeg scene changes + a ceiling per shot) that also makes numbered contact sheets. |
| `tools/aggregate.py`, `tools/cards_lib.py` | Card helpers and the aggregator that produces `needs_list.json`. |
| `tools/label_overlay.py` | Draws code labels with leader lines on a recipe preview from the anchors the recipe reports. |
| `recipes/*.py` | Blender recipes (bpy 5.0.1, Python 3.11, or `blender -b --python`). |
| `previews/recipes_preview.jpg`, `previews/recipe_variants.jpg` | The four recipe previews with code labels, and three variants made only by changing parameters (cell cutaway, skin layers, three charges). |

## Recipes

Every recipe is one parameterised script. It builds the scene, renders a preview with Cycles (CPU is fine), can
export the model as `.glb`, can write keyframes for a video block (`--frames N`), and prints one `RECIPE_RESULT`
JSON line (also saved as `<preview>.json`) with **anchors**: the pixel position of each named part, so BIE's code
draws labels on top in any language. No text is ever baked into a render.

| Recipe | Makes | Key parameters | Seen in |
| --- | --- | --- | --- |
| `studio_stage.py` | Grid-tiled glossy floor, curved gradient back wall, key/rim/fill lights; `build_stage()` is reused by other recipes | wall colours, floor and line colours, tile size | Branch Education (touchscreen, cache) |
| `exploded_layers.py` | A stack of thin layers that lift apart and close again (glass, diamond checker, solid, RGB pixel stripes, emissive) | layers JSON, `--t` (0 assembled → 1 exploded), gap, stage or void | touchscreen, SSD/NAND, chips; also skin/soil strata |
| `cutaway_sphere.py` | Concentric layers with a wedge cut out; procedural planet surface or plain; glowing core | layers JSON (radius, colour, glow), surface, spin keyframes | Earth interior, mantle convection; cells, atoms, fruit |
| `field_lines.py` | Field lines traced from point charges by code (RK2), glow tubes, arrows, charge spheres | preset dipole/radial/like, charges JSON, line count, plane-only, colour | Maxwell, capacitor field arcs |

Render time measured here (2 CPU cores, 960×540, 64 samples): about 20–40 s per still.

Licences: Blender/bpy is GPL — used only as a cloud/CI/VM tool, never shipped in an app; everything these scripts
make is BIE's own (no third-party assets used).

## What the needs list says (top of the list)

Used in the most videos: focus glow / highlight outline, leader-line labels, title tags (5–6 videos); orbit and
glide camera, cutaway / cross-section, particle flow (4); graph plotting, equation steps, field lines and vector
arrows, flow arrows, macro zoom (3); exploded layers, studio stage, construction machines, Earth cutaway (2).
Levels by seconds: L4 3,464 · L5a 1,042 · L3 810 · L2 334 · L1 123. The best 3D videos barely cut (Calculus: 3
cuts in 15 minutes); the benchmark changes view about every 4.7 s.

The cell and tissue recipe (translucent organic cells) is being built separately in Task 046's one-shot test and is
not duplicated here.
