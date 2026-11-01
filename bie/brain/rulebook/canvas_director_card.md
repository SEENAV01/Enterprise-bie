# Director card: build-up canvas plans (for the AI director step)

You plan ONE canvas for ONE part of a passed script. You do not write narration and you do not place pixels: you say
what appears, in which grid cell, and on which spoken word. Code (`econ_canvas.compile_plan`) places, times and checks
it; a refused plan comes back to you with the exact error.

## Input you get

- `beats`: the part's spoken beats `[{beat_id, say}]` (Hinglish, Devanagari with English terms). Do not change them.
- The chapter map items this part covers (terms, numbers, causes, examples).
- The icon search tool: `icon_index.search("bank")` → ids like `tw:1f3e6` (colour), `fa:solid/building-columns` (line) or
  `fl:bank` (Fluent 3D), or a picture in the lesson's asset library; the candidates listed under the part are the ones code
  found for the beat's own things.

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
| `picture` | `cell`, `picture`: `{type: timeline / gallery / flow, title, items: [{when, name, icon, cue}], arrows}` | a row of things you draw yourself: dates on a timeline (`when` = the date as said), a numbered row of things (gallery), steps joined by arrows (flow); each item appears on its own cue |
| `action` | `cell` (at least 3 rows tall, best 5–6 rows and 8–12 columns), `action: {template, actors, objects, amounts, steps, texts, parts, close_up}` | a process the learner sees happen, made of motion parts (the saanche below), with the beat's own actors, things and numbers |

`focus: [{cue, until_cue?, ids: [...]}]` dims everything else. `camera: [{cells: [...], cue}]` zooms to a region
(use it when the canvas is dense or to re-frame for the next sub-idea). `graph` = a `curve_story` (axes, curves as
points, a dot that walks to named x values, guides like NAIRU, shaded bands, notes) for any economic curve.

Tones: `ink`, `muted`, `accent` (blue), `warm` (orange), `danger` (red), `ok` (green), `tag` (pink), `note`, `band`.

## Dikhane ki soch (Navin, 30 October 2026: "jo bola ja rha hai screen ke visuals se wo baat clear ho")

Before you plan, BIE has thought about every beat: its idea, its relation (reject, accept, compulsory, limit, sequence,
compare, …) and the things it names; the part message lists them with the icons BIE found for each thing. Draw THAT:

- Every beat shows at least one thing that is not text (an icon, a mark, an arrow, a crowd or value step, a table row, a
  picture item), cued on a word of that beat (D1-01). A screen of text alone for more than 10 s is refused (D1-02): a video
  that is only text is a book.
- Show the relation the way BIE's visual verbs say: a cross on the thing refused, a tick on the thing accepted, a law scroll
  and stamp for "compulsory", a meter with a red line for a limit, a numbered row or a timeline for a sequence, an arrow chain
  for cause → effect, a split or a scale for a comparison, before/after for a change, a receipt or a handshake for a promise.
- The picture shows the thing itself, so its label is understood without reading (the book's page 2): screen text is a
  name or a short phrase of at most 8 words, never a sentence; the sentence is the narration and the subtitles (D1-03).
- When the part message says BIE has placed the book's own picture (a timeline, a table, a gallery of the book's panels, a
  flow), keep it: never redraw it, never reuse its cells or its id, and build your elements in the rows below it (D1-04).
- Never put a caution or fact-check line on screen ("illustrative numbers", "imagined market", "data not given",
  "outside clarification"): those are BIE's background checks (D1-06).

## Kriya ke saanche: processes the learner sees happen (Task 046 Part D2; Navin, 1 and 2 November 2026)

Navin on the D1 videos: "process show nahi ho rahi hai ... agar wo visuals se clear ho, tab maja hai"; and on 2 November 2026:
"jis cheej ka jikar hai wohi cheej dikhe" — examples are illustrations, never a list of things to draw. When a beat tells a
PROCESS (someone gives, pays, scans, swaps, writes, counts, refuses, accepts, turns one thing into another), show it with an
`action` element made of general motion parts; the actors, the things and the numbers are THIS beat's own.

The motion parts BIE draws: `hold` (a person holds a thing), `give` (a thing goes from one hand to the other), `move` (a thing
moves along a path to a spot, a person or another thing; `back` returns it, `into` lets it go in), `transform` (A turns into B
where it is), `show_text` (a tag, sign, screen, ok screen, thought bubble or written text shows a short text), `meter` (a bar
fills to its limit, or a number changes with an up/down arrow), `appear` (things appear one by one, in a grid or onto a pile),
`refuse` / `accept` (a head shake and a cross, a nod and a tick), `compare` (two things side by side with = ≠ ? vs < >).

Recipes are ready compositions of these parts (`template`, each step on its cue word):

| template | steps | actors (role) | objects (name; optional ones may be left out) | amounts |
| --- | --- | --- | --- | --- |
| `hand_over` | give, take | giver, taker | thing | – |
| `pay_change` | pay, goods, change | buyer, seller | goods; money, change_money (optional: else a plain chip with the amount) | paid, change (price optional) |
| `barter_swap` | offer, ask, swap | a, b | a_thing, b_thing | – |
| `upi` | scan, paid, received | buyer, seller | device, sign, seller_device (all optional) | amount |
| `card_tap` | tap, approved | buyer, seller | card, machine (optional) | amount |
| `cheque` | write, hand, balances | payer, payee | cheque, place (optional) | amount (payer/payee before and after optional) |
| `coin_count` | count, limit | – | coin (optional) | each, limit |
| `refuse` | show, refuse | who | thing | – |
| `accept` | show, accept | who | thing | – |
| `count_stack` | count | – | thing | n (1 to 12) |
| `compose` | one per part | your own (at most two) | your own | – |

- Every object's icon is the thing the beat names, from the icon candidates of THAT beat's things; never a thing from an
  example, a card or another part, never a stand-in. A thing the beat names that has no icon goes to the needs list (code finds
  or makes it); meanwhile leave the optional object out.
- Numbers go on what carries them (a tag on the thing that travels, a screen, a meter), never on a separate label; every amount
  is said in the narration of the action's beats, written as the narration writes it (CV-16). `texts` adds one short word the
  narration says to a step's sign.
- A value given back travels back in a process (a `give` with its tag), never as a struck value with an arrow: a struck value
  with ▲/▼ is only for the SAME quantity changing.
- "Refused", "not valid": a `refuse` part puts the cross on that thing; "accepted", "valid": `accept`.
- One main character per video: the person the story follows has `who: "main"`; everyone else is `"other"`. `mood` is neutral,
  pleased, unsure or refusing; the parts change moods on their steps.
- A process no recipe fits: `template: "compose"` with its parts in order (each with its cue word and the fields it needs).
  A motion BIE has no part for: show it with icons and arrows meanwhile; the visual-idea step names it (`template: other`) and
  it goes to the missing-capability log.

Nothing sits under the subtitle strip: the bottom 14 % of the frame belongs to the captions; code moves the camera so that
what a beat shows stays above it, and refuses a plan whose element is still under it.

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
