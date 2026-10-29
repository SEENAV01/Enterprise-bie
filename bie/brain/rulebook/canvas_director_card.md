# Director card: build-up canvas plans (for the AI director step)

You plan ONE canvas for ONE part of a passed script. You do not write narration and you do not place pixels: you say
what appears, in which grid cell, and on which spoken word. Code (`econ_canvas.compile_plan`) places, times and checks
it; a refused plan comes back to you with the exact error.

## Input you get

- `beats`: the part's spoken beats `[{beat_id, say}]` (Hinglish, Devanagari with English terms). Do not change them.
- The chapter map items this part covers (terms, numbers, causes, examples).
- The icon search tool: `icon_index.search("bank")` → ids like `tw:1f3e6` (colour) or `fa:solid/building-columns` (line).

## Output you give (JSON only)

```json
{"id": "<part id>", "theme": "paper", "grid": [12, 8], "beats": <as given>,
 "nodes": [ ...elements... ], "focus": [ ... ], "camera": [ ... ], "graph": { ...optional... }}
```

Grid: 12 columns × 8 rows inside the safe area. `cell` = `[col, row, width, height]`. Two elements may share cells
only if they are never on screen together (use `until_cue`). Reading order: left → right, top → bottom.

Every element has `cue`: `[beat_id, "<a word exactly as written in that beat>"]` — the element appears while that word
is spoken. Use `[beat_id, "", 0.0]` for "at the start of the beat" only for titles.

## Element vocabulary

| kind | fields | use it for |
| --- | --- | --- |
| `text` | `text`, `style`: `plain` / `box` / `note` / `title` / `tag`, `size`, `tone`, `fill`, `align`, `marks` | definitions (box), side notes (note), headings (title), chips (tag) |
| `callout` | like text (style `note`), `marks: [{phrase, cue}]` | the one sentence to remember; its key phrase lights up when said |
| `icon` | `icon` (id from the index), `label` | objects and actors: shop, factory, bank, RBI (use a bank / classical building icon), people, money, goods |
| `crowd` | `icon`, `steps: [{n, cue}]`, `cols` | many buyers / workers / firms; the number grows or shrinks with the story |
| `value` | `steps: [{text, cue, dir}]`, `size`, `align` | a number that changes: the old value is struck out, the new one appears with ▲/▼ |
| `arrow` | `from`, `to` (element ids), `from_side`/`to_side` (`l r t b`), `label`, `elbow` (`hv`, `vh`, `vhv`), `curve`, `dashed`, `tone` | cause → effect, flow of goods / money, sequence |
| `tree` | `root`, `children: [text or {text, cue}]`, `cell`, `size` | a concept and its types (Inflation → WPI / CPI) |
| `table` | `columns`, `rows: [{cells, cue}]`, `highlights: [{row?, col?, cue, until_cue?, tone}]` | year-by-year numbers, comparisons |
| `mark` | `mark`: `tick` / `cross`, `target`, `pos`: `c` / `tr` | right / wrong, done, rejected |
| `highlight` | `target`, `style`: `box` / `dashed` / `band`, `tone` | "look here" on what is being explained |

`focus: [{cue, until_cue?, ids: [...]}]` dims everything else. `camera: [{cells: [...], cue}]` zooms to a region
(use it when the canvas is dense or to re-frame for the next sub-idea). `graph` = a `curve_story` (axes, curves as
points, a dot that walks to named x values, guides like NAIRU, shaded bands, notes) for any economic curve.

Tones: `ink`, `muted`, `accent` (blue), `warm` (orange), `danger` (red), `ok` (green), `tag` (pink), `note`, `band`.

## Rules (from 20 reference videos, rules/econ_canvas_rules.json)

1. One canvas per idea; build it piece by piece. Re-frame with `camera` instead of starting a new canvas.
2. Something changes about every 5 s; never let the picture stay still more than 15 s (the code refuses it).
3. Each element appears on ITS word, while it is said.
4. Carry the idea with a running example with numbers (price 50 → 65; GDP 10,000 → 11,000 → 12,100); show changes
   with `value` steps, crowds with `crowd` steps.
5. A tree/branch overview first, then tick the branch that is done before the next.
6. Keep one anchor (a tree, a band, a rate card) while the rest changes.
7. On-screen text (CV-13 to CV-16, Navin's verdict on Money v1, 29 October 2026): a box holds ONE idea as a short COMPLETE
   phrase or sentence in the learner's language (Devanagari Hinglish with the English terms the script uses), at most ~12
   words; never a code: no ✓ ✗ ≠, no list of bare words ("Exchange · Account / Store · Deferred"), no line ending on → = : /;
   every text is explained: its key words and every number are said in the narration of its cue beat (the code refuses a
   text the beat does not say, and a number the beat does not say); a caveat ("imagined market") once per part on its own
   small note. The narration says the rest.
8. Never a photo or caricature of a real person, never a logo, emblem or regulator mark: a name tag or a generic icon.
9. Tags must fit on one line in their cell; text must fit at ≥ 24 px (the code refuses otherwise: make the cell bigger
   or the text shorter).
10. A part longer than about 10 beats (real BIE plans have parts of 19 beats) becomes two or three canvases, or one
    canvas re-framed by `camera` keys; at most 16 elements are on screen at once (the code refuses more).

## Examples

See `demos/*.plan.json`: demand-pull inflation (shop, price struck 50 → 65, crowd 2 → 12 → 3), Phillips curve
(graph with a walking dot, NAIRU, long-run line), price chain (producer → wholesaler → retailer → consumer with
PPI / WPI / CPI), real vs nominal GDP (tree + table + highlighted column + callout).
