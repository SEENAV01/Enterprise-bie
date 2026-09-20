# COMP Hardening H4 — continuation, not a restart

Checkpoint: BIE-COMP-H4-005. COMP remains IN PROGRESS / NOT ACCEPTED.
This batch implements a bounded local layout-repair branch for the existing
H3 source producer. Original emitter defaults and the H3 publication schema are
preserved; H4's new contracts are separately versioned. This is not a full
section re-audit, a new textbook-intelligence layer or an accepted video product.

## What actually changes

A visual-owner policy binds the original scene and explicitly permitted layout
regions. The repair process generates deterministic candidates, recompiles each
one, checks every frame's layer geometry, measures generated output in local
Chromium, checks visible text and within-owner collisions, and selects a locally
fitting candidate or emits an upstream revision request. Only rectangles and the
supported text/map presentation contract may change. Text, math, units, map
coordinates/projection, tracks, narration, timing, accessibility and provenance
remain byte-equivalent in the semantic contract. Font reduction, ellipsis,
clipping and automatic timing/pagination changes are not repair strategies.

`compiler_layout` is opt-in; the legacy emitters are unchanged without it. The
map's plot viewport is an explicit presentation permission, not a proof of equal
instructional effectiveness or equivalent cartographic feature resolution.

## Run the integrated workspace

Use the same Python mathematical dependencies, real TypeScript/Node toolchain,
FFmpeg/ffprobe and POSIX process controls as H3. H4's browser tests additionally
require Playwright Python and Chromium. No browser/font/dependency binaries are
bundled or silently downloaded. The exact local environment is in the evidence.

```bash
PYTHONPATH=app:. python -m unittest discover -s tests -v
PYTHONPATH=app:. python scripts/validate_comp_h4_repairs.py --output /absolute/new-evidence
```

A synthetic original/policy pair is stored in `fixtures/comp_h4/repair_corpus.json`.
Extract one pair to JSON files, then run:

```bash
PYTHONPATH=app:. python scripts/repair_scene_layout.py scene.json /absolute/new-project \
  --policy policy.json --evidence /absolute/new-repair-evidence \
  --width 1280 --height 720 --fps 24 --browser /usr/bin/chromium --screenshots
```

Exit 0 means locally measured source was published. Exit 2 requests upstream
revision. Exit 3 is an environment, input or publication block. None means actual
Remotion rendering passed. Omitting `--policy` grants no additional geometry:
only reflow inside the existing owned boxes is permitted.

The old CLI remains valid and exposes H4 as an explicit branch:

```bash
PYTHONPATH=app:. python scripts/compile_scene_checked.py scene.json /absolute/new-project \
  --layout-policy policy.json --layout-evidence /absolute/new-evidence
```

This older CLI keeps its 640x360 target; use `repair_scene_layout.py` for an
explicit target. Measurements are bound to the exact scene, manifest and target;
they cannot be reused after changing the target.

## Evidence limits

The local evaluator uses real generated TypeScript, explicit React/Remotion API
doubles, and actual Chromium DOM painting. It measures ALL frames of candidates
within its explicit budgets, and saves selected screenshots. It is not an actual
React or Remotion runtime. It blocks network requests but launches local Chromium
without an OS sandbox. Hashes prove consistency, not external authenticity. No
local repair receipt or caller-supplied JSON authorizes a production release.

For the actual installed-dependency render path:

```bash
PYTHONPATH=app:. python scripts/validate_checked_remotion.py /absolute/new-project --browser /usr/bin/chromium
```

This remains blocked until the governed dependencies/typecheck and real CLI stages
actually succeed. Layout source success is not a substitute. Browser font/locale
coverage, full ink/contrast analysis, specialized consumers, instructional
reduced-motion equivalence, operational isolation, real books and games remain on
`docs/COMP_CONSOLIDATED_GAP_LEDGER.json`.

## Packaging and GitHub

Use the separate INTEGRATED.zip directly for the cumulative DSL+COMP workspace.
Atomic archives are small ordered source deltas against the exact H3 baseline;
they are NOT standalone applications. Their README/manifest specifies ordering.
The current Master contains the identical integrated archive, the five current
atomic deltas, current evidence and reports. It does not embed the prior Master.
Historical parent files remain in the integrated workspace because inherited
lineage tests explicitly verify their bytes; they were not deleted to reduce size.
The current Master is a local delivery, not a GitHub commit or canonical merge.
