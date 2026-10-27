# Canvas cards for the economy reference videos (batch 2)

These videos are "build-up canvas" explainers: a white or cream canvas, flat icons, text boxes, arrows, simple graphs,
tables and timelines that appear one piece at a time while the narrator speaks. There are almost no camera cuts; the
picture changes by ADDING, CHANGING or REMOVING elements, by zooming to a region, or by clearing the canvas for the
next idea. A card describes one SEGMENT: a stretch where one canvas composition is built (a new segment starts when the
canvas is cleared or replaced, or the camera moves to a clearly different region/composition).

We never store frames or copy text. Cards are our own short descriptions in English.

One JSON file per video: `cards/<ID>.json`

```json
{
  "id": "E19",
  "title_guess": "Bretton Woods system and India's exchange rate history",
  "segments": [
    {
      "start": 0, "end": 74,                      // seconds (from the contact-sheet timestamps; events JSON if present)
      "teaches": "devaluation lowers the exchange rate, exports rise, trade balance improves",
      "canvas": "new | builds_on_previous | zoom_in | zoom_out | pan",
      "layout": "flow_left_to_right | flow_top_down | tree | graph_with_notes | table | timeline | compare_two_sides | hub_and_spokes | free",
      "elements": [
        {"kind": "<one of the kinds below>", "what": "short description", "count": 1}
      ],
      "motions": ["<motion words below>"],
      "level": "L1 | L2 | L3",
      "notes": "anything special: a teaching trick, a running example with numbers, a recap, a question to the viewer"
    }
  ]
}
```

## Element kinds (use these words; add a new kind only if nothing fits, and say so in notes)

- `icon` — flat coloured icon of an object (shop, factory, warehouse, person, bank, central bank, gold bars, banknote,
  coin, car, server rack, laptop, basket, globe). Put the object in `what`.
- `crowd` — the same person/object icon repeated in a row or grid to show "many" (count = how many).
- `text_box` — a rectangle with a short definition or explanation sentence.
- `tag` — a small coloured pill/label (a school of thought, a heading chip, "DETERMINED BY RBI").
- `title_text` — big heading word(s) on the canvas.
- `arrow` — a single connector arrow (straight, elbow or curved), maybe with a label.
- `flow_chain` — several boxes/icons joined by arrows in sequence (producer → wholesaler → retailer → consumer).
- `tree` — one node splitting into branches (inflation → WPI / CPI).
- `bullet_chain` — a vertical list of short statements joined by down-arrows (cause → effect → effect).
- `graph` — axes with a curve/line; say in `what` what is on the axes and what happens (point moves, curve shifts,
  shaded area, drop lines, a second curve).
- `bar_or_chart` — bar/line chart with data.
- `table` — rows and columns of values (years × values); say if a column/cell is highlighted.
- `timeline` — a horizontal line with years/periods, maybe arcs between points.
- `value_change` — a number shown, then crossed out and replaced by a new number (often with a ↑/↓ arrow).
- `mark` — a red cross, green tick or similar verdict mark on an item.
- `up_down_arrow` — small green ↑ or red ↓ next to a quantity.
- `callout` — a speech/thought box pointing at something, or a "THIS MEANS"-type side note.
- `highlight` — a box, glow, coloured band or text highlighter drawn over existing content.
- `formula` — an equation (Real GDP = Nominal GDP / deflator).
- `map` — country or world map/silhouette.
- `character` — a cartoon presenter/caricature with a speech bubble.
- `photo` — a real photo (of a person, a building, a magazine cover). Note it; BIE will NOT use photos of real people.
- `logo_or_brand` — a real logo, product or brand mark. Note it; BIE will not use it.
- `question_mark` — a big "?" to open a question.
- `end_screen` — channel promotion/end card (mark it and ignore it for teaching).

## Motion words

`pop_in`, `fade_in`, `draw_line` (line/arrow draws itself), `write_on` (text types on), `slide_in`,
`strike_and_replace`, `multiply` (crowd grows), `move_point_on_curve`, `curve_shift`, `shade_area`, `zoom_to_region`,
`pan`, `highlight_text`, `pulse_or_glow`, `cross_out`, `clear_canvas`, `swap_element`, `count_up`.

## Level

L1 teacher-board (plain text on a board), L2 clean flat 2D (icons, arrows, boxes, simple graphs), L3 rich 2D/2.5D
motion graphics (depth, lighting, many moving parts, camera moves through a designed world).
