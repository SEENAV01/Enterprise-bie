# Economy kit: build-up canvas videos (asset intake, batch 2, 27 Oct 2026)

Built from 20 Indian-economy reference videos (UPSC, about 2 h 5 min) that Navin uploaded to train BIE before the
economy chapter test. Those videos are flat 2D "build-up canvas" explainers: one canvas per idea, icons, boxes,
arrows, numbers that get struck out and replaced, crowds, simple graphs, a new piece about every 5 seconds, almost no
cuts. Status: IMPLEMENTED (renders, tested here), not INTEGRATED (the director does not emit canvas plans yet), not
ACCEPTED (Navin has not judged a video made from a real chapter).

No footage, frames, audio or text from the reference videos is stored here. The demos are hand-written fixtures that
test the templates; lesson content is made by BIE only.

## Batch 3 (4 Nov 2026): the economy learning track

Navin uploaded 20 more economy videos; 3 were already in batch 2, so 17 are new (about 2 h 30 min). Under the
agreement of 3 Nov 2026 (`docs/vision/AGREEMENT_2026-11-03.md`) each subject's videos give BIE four things; for
economy they are here, from all 37 videos (346 teaching segments):

| Path | What it is |
| --- | --- |
| `rules/show_lexicon.json` | **Dikhane ka shabdkosh**: 25 patterns, "when the line says this kind of thing, the picture does this", each with engine parts, economy saanche, our own Hindi example and where the references showed it. The director's dictionary. |
| `needs_list_v3.json` | **Saanche list**: 165 drawn things ranked by how many segments use them, each with where BIE gets it (`have_v2`, `built_batch3`, `engine`, `have_icon`, `replace`, `build_next`, `decision`, `one_off`). |
| `rules/econ_canvas_rules.json` | **Pace, text and camera**: measurements re-done on 37 videos, rules CV-13 … CV-18 added (show, do not write; ≤ 25 words on screen; reuse the picture for change; follow one object; no logos; facts only from the book). |
| `rules/teaching_style.json` | **How the narrator explains**: ten moves (scene before term, यानी unpacking, cause chains, मान लीजिए, small numbers, conclusion lines, human benefit, signposts), each with where it was heard. |
| `cards/E01–E37.json`, `rules/CARD_SCHEMA_v3.md` | Cards for all 37 videos with the v3 fields (idea type, idea, shown_as, meaning carrier, things, actions, words on screen, camera, example). E01–E20 were upgraded from their batch-2 text; E21–E37 were carded from keyframe sheets. |
| `saanche/econ_saanche.js`, `saanche/manifest.json`, `saanche/stills/` | Eight new parametric saanche for the v2-demo engine (`window.BIEDraw`): `institutionBadge` (replaces every logo), `paper` (law, bond, licence, contract, bill, report, with stamps), `disc`, `vault`, `crowd` (with a share), `centralBank`, `committee`, `moneyBag`; stills of each and one composed still (`scene_crr.png`, Claude's demo still, not BIE output). |
| `tests/test_saanche.mjs` | Renders every saancha with defaults, the still variants and animation steps; checks for errors, NaN/undefined and unbalanced SVG tags (`node tests/test_saanche.mjs`). |
| `tools/keyframes.py`, `tools/aggregate3.py`, `tools/needs3.py`, `tools/stills.mjs`, `tools/scene.mjs` | Keyframe sheets for carding, the 37-card aggregate, the needs list, saanche still sheets and composed scene stills. |
| `measurements/pace_37_videos.json`, `measurements/cards_summary_37.json` | The numbers behind the rules. |

What the numbers say: the references carry meaning by diagrams in 39% of segments, by a picture with labels in 34%,
by text alone in 17% and by things acting in only 11%; about 38 words are on screen once a canvas is built (p90 90);
a logo or emblem appears in 25 of 37 videos. BIE keeps their good pictures as patterns and replaces their text
stretches with the same patterns. Of all 1,074 thing-uses, 78% are covered by the v2 library (22%), the new saanche
and the logo replacement (29%), icons (10%) or engine parts (18%; timeline, table, graph and marks exist for the old
engine in this kit and are ported in Phase 1); `build_next` (10 things, 3%) is the next economy batch; one-offs (16%)
are left to BIE's AI; the India map (3%) waits for a decision.

Decided by Navin (4 Nov): an India map follows the Survey of India's official boundary; until a licence-checked source
is in place BIE uses a "भारत" label, not an outline.

### Batch 3b (4 Nov 2026): teaching, talmel and the other sections

Under the addendum of 4 Nov (agreement section 8: the videos teach every section of BIE), every video was also
transcribed with word timings (faster-whisper large-v3-turbo on CPU; transcripts stay in the workspace, never in the
repo) and carded for teaching:

| Path | What it is |
| --- | --- |
| `teach/E01–E37.json`, `rules/TEACHING_CARD_SCHEMA.md` | Teaching cards in our own words: concepts and teaching order, the cutting rule, narration moves, examples, story-before-term, 24 speech–picture tiles per video (what appeared, what was said, which came first, does the picture show the meaning), voice notes, game ideas, notes questions, checks learned. |
| `measurements/teaching_summary_37.json` | The aggregate: moves, example kinds, talmel lead/relation and measured lag, game mechanics, notes answer shapes, 262 learned checks, 268 notes questions. |
| `tools/talmel_sheets.py`, `tools/teach_aggregate.py`, `tools/stt_turbo.py` | Speech–picture tile sheets, the aggregate, the transcription run. |

What the numbers say (848 tiles): a picture lands a median 0.14 s before the word that names it, 73% within 1 s; but
only 37% of picture changes show the meaning, 46% only write the term or the sentence. The story comes a median 30 s
before the term. Most common game mechanics proposed: run a process (31), sort into groups (18), allocate (17), cause
chain (12); notes answer shapes: flow (79), comparison (43), table (42), picture (39).

In BIE: the eight saanche are in the engine (main, PR #138); 23 rules from this learning are in
`bie/brain/rulebook/econ_videos.json` as **proposed** (PR #139) and reach the makers only when Navin locks them.

Status: IMPLEMENTED (saanche render and pass their test; rules and lexicon written), not INTEGRATED (Phase 1 builds the
saanche slot and the director that reads the lexicon), not ACCEPTED.

## Contents

| Path | What it is |
| --- | --- |
| `blocks/canvas_build.tsx` | Toolbox block `canvas_build`: paper/dark theme; icons, text boxes, notes, tags, titles, arrows (side-attached, elbow, curved, drawn on), values struck out and replaced with ▲/▼, crowds that grow and shrink, tick/cross marks, highlights (box, dashed, band), callouts whose phrases light up when spoken, focus (dim the rest), subtitles on a dark strip. Registers itself with BIE's block registry. |
| `blocks/world_scene.tsx` | **L3** block `world_scene`: a 2.5D designed world (sky, far city, mid buildings, street, blurred foreground as parallax layers), a shop with a shelf of goods and a hanging price tag that flips and can be pulled up, BIE's own procedural walking people (no third-party art), crowds that arrive and leave walking, coin rain, a supply/demand balance that tips, glass labels, a big "pull" arrow and a title with a light sweep; a camera that glides, pushes in and pulls back through the layers. |
| `tools/world_plan.py` | World plan → scene spec (cue words → frames, unknown kinds, camera order and pace checked). |
| `blocks/curve_story.tsx` | Toolbox block `curve_story`: named axes, curves drawn from points, a dot that walks along a curve to named x values with drop lines, guide lines (natural rate, target), shaded or hatched bands, faded old curves for shifts, notes. |
| (canvas_build `touches`) | **L2 + L3 touches** on the same canvas: soft shadows and idle motion, people walking in and out, goods and coins flowing along arrows, a price tag that flips with a glow, a paper vignette, and a camera inside the block that frames each beat without cutting anything in half (`auto_camera`). |
| `tools/econ_canvas.py` | Canvas plan → scene spec. The director says only what goes in which grid cell and on which spoken word; this code places, times (through `bie/brain/video/timing.py`) and refuses plans that would look wrong: overlap, outside the safe area, text that does not fit at ≥ 24 px, tags wider than their cell, missing cue words, missing references; reports density and pace (CV-02/CV-03). |
| `tools/icon_index.py` | Builds and searches a 4,213-icon index from two CC BY 4.0 sets (Twemoji graphics, Font Awesome Free; no brand icons) and copies chosen icons plus `credits.json` into a render's assets. `icons/index.json` is the built index. |
| `tools/econ_aggregate.py` | Turns the canvas cards into the needs list with what BIE main has and what this kit adds. |
| `tools/build_econ.mjs`, `preview/main-econ.tsx` | Preview bundle: BIE's core preview harness + the two blocks (esbuild, like `bie/brain/video/preview/build.mjs`). |
| `rules/econ_canvas_rules.json` | Measured timing of the references and the rules CV-01 … CV-12 for the build-up canvas profile. |
| `cards/*.json`, `needs_list.json` | Canvas cards for the 20 videos (our own short descriptions) and the aggregated needs list. |
| `demos/make_demos.py` | Fixtures (the same demand-pull beats at three levels: L2 canvas, L2 + touches, L3 world), and: demand-pull inflation (price struck 50 → 65, crowd 2 → 12 → 3), Phillips curve (dot walks the curve, NAIRU, long-run line), price chain (producer → wholesaler → retailer → consumer, PPI/WPI/CPI). |
| `tests/test_econ_canvas.py` | 16 tests for the canvas compiler, the touches camera and the world plan. |

## Run

```bash
export BIE_TWEMOJI_SVG=<jdecked/twemoji>/assets/svg BIE_FONTAWESOME_SVGS=<@fortawesome/fontawesome-free>/svgs
python3 demos/make_demos.py
python3 tools/icon_index.py copy tw:1f3ea tw:1f4e6 tw:1f9cd tw:1f4b0 tw:1f3ed fa:solid/warehouse --dest DIST/assets
node tools/build_econ.mjs DIST
python3 tools/econ_canvas.py demos/*.plan.json --icons ICONS.json --out SPEC.json
node ../../bie/brain/video/preview/stills.mjs --dist DIST --spec SPEC.json --mp4 out.mp4 --page econ.html
python3 -m unittest tests/test_econ_canvas.py
```

## What Claude Code should do with it (Task 046 / 047)

1. Move the blocks into `bie/brain/video/blocks/toolbox/` (import paths `../registry`, `./common`), add them to
   `toolbox/index.ts`, and the plan compiler into `bie/brain/` (for example `bie/brain/canvas.py`) with its tests.
2. Fix `bie/brain/video/timing.py::_norm`: it keeps the Devanagari danda (।) glued to the last word, so a cue on the
   last word of a Hindi sentence is never found and silently lands at the start of the beat (patched in
   `econ_canvas.py` until then). Add a test.
3. Give the director a "build-up canvas" mode for subjects whose content is concepts, causes and numbers (economics,
   polity, history, commerce): one canvas plan per script part, element vocabulary = the kinds above, cue words from
   the beat text, layout by grid cells; the plan goes through `econ_canvas.compile_plan` and a refused plan goes back
   to the director with the error (code check, not a reviewer round).
4. Captions on light themes: the core `Captions` draws white text without a strip (invisible on paper); the kit draws
   subtitles inside `canvas_build` for now.
5. Icons: register Twemoji and Font Awesome Free as CC BY 4.0 sources in `bie/toolbox/sources.py`, fetch them in CI
   (GitHub / npm), and put the credit lines in the lesson's credit roll.

## Licences

Twemoji graphics: CC BY 4.0 (Twitter, Inc and other contributors). Font Awesome Free icons: CC BY 4.0 (Fonticons,
Inc.); brands are excluded. Both are allowed by `bie/toolbox/licence_policy.json` (class `cc-by`, credit required).
The kit's own code and drawings are BIE's own work.
