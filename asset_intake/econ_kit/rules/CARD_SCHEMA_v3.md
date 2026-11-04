# Canvas cards, batch 3 (new lens, 4 Nov 2026)

Batch 3 uses the batch-2 card format (`CARD_SCHEMA.md`: segments with start, end, teaches, canvas, layout, elements,
motions, level, notes; the same element kinds and motion words) and adds the fields below. The new fields come from
what Navin passed in the Money v2 demo: every thing said is shown, every action said happens on its word, and the
picture carries the meaning (text alone is a book page, not a video).

We never store frames or copy the videos' text. Write our own short descriptions in English. A technical term
(CRR, repo rate, SLR) may be named; sentences on screen are summarised, not copied.

## Extra fields per segment

```json
{
  "idea_type": "process | comparison | classification | timeline | numbers | definition | cause_effect | mechanism | formula | data_status | exam_link | recap | intro | end_screen",
  "idea": "the idea in one plain line (what a learner should understand from this segment)",
  "shown_as": "how the picture makes that idea visible, as a visual verb phrase: 'commercial bank hands a slice of its cash stack to the RBI vault; the slice is labelled 4% and locked'",
  "meaning_carrier": "picture | picture_plus_label | diagram | text_only",
  "things": ["bank_building", "rbi_building", "cash_stack", "person_borrower"],
  "actions": ["hand_over", "lock", "split", "count_up"],
  "on_screen_words": 25,
  "camera": "still | zoom_in | zoom_out | pan | cut | clear",
  "example": "the running example or numbers used, if any (₹100 deposit → ₹4 kept as CRR)"
}
```

- `idea_type`: `end_screen` marks channel promotion (left out of every count); `mechanism` = how an institution acts (RBI lends to banks, a bank keeps reserves); `data_status` = current
  figures, rankings, "where India stands"; `exam_link` = how it was asked in an exam; `intro` = title/opening.
- `meaning_carrier`: `picture` when objects/people/actions show the idea; `picture_plus_label` when a picture is there
  but the label carries most of it; `diagram` when boxes, arrows, trees, graphs or tables carry it; `text_only` when
  it is sentences on screen. This tells us where the references are good examples and where BIE must do better.
- `things`: every drawn object, character or place, as snake_case nouns, generic (no brand): `bank_building`,
  `rbi_building`, `government_building`, `factory`, `shop`, `farmer`, `person`, `crowd_people`, `cash_stack`, `coin`,
  `rupee_note`, `gold_bar`, `bond_certificate`, `cheque`, `document`, `vault`, `ship`, `globe`, `india_map`, `calendar`,
  `percentage_badge`, `graph_axes`, `scale_balance`, `lock`, `hourglass` ... Reuse a name you used before; add a new
  name only when nothing fits.
- `actions`: what moves, in our motion words plus action verbs: `hand_over`, `flow_along_arrow`, `split`, `join`,
  `fill`, `empty`, `grow`, `shrink`, `lock`, `unlock`, `transform`, `count_up`, `strike_and_replace`, `cross_out`,
  `tick`, `walk_in`, `walk_out`, `stamp`, `sign`, `point`, `compare_side_by_side`, `zoom_to_region`, `highlight_text`,
  `pop_in`, `write_on`, `draw_line`.
- `on_screen_words`: about how many words are on screen when the segment's canvas is fully built (estimate).

## Extra fields per video

```json
{
  "format": "build_up_canvas | teacher_with_board | paper_walkthrough | mixed",
  "recurring_cast": ["things or characters that come back through the video"],
  "running_examples": ["number or story examples that carry the video"],
  "best_moments": [{"t": 123, "why": "a picture that makes an abstract idea obvious"}],
  "weak_moments": [{"t": 300, "why": "a long text-only stretch"}]
}
```

`best_moments` are the ideas BIE should learn to show the same way (in its own drawings); `weak_moments` are what BIE
must not copy.
