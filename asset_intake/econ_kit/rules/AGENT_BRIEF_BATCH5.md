# Brief for batch-5 card writers (economy reference videos)

You are helping build BIE, an engine that turns books into teaching videos, games and notes for Navin's online
coaching (Hindi/Hinglish learners, class 6 to UPSC). We learn from reference videos how each idea is SHOWN and how it
is TAUGHT, so BIE can do both itself. For each video ID you are given, write TWO files:

1. `cards3/<ID>.json` — the canvas card (how it was shown). Format: `CARD_SCHEMA.md` (base fields, element kinds,
   motion words) plus `CARD_SCHEMA_v3.md` (idea_type, idea, shown_as, meaning_carrier, things, actions,
   on_screen_words, camera, example per segment; format, recurring_cast, running_examples, best_moments, weak_moments
   per video). Inputs: every keyframe sheet `kf/<ID>/sheet-NN.jpg` (12 tiles, 3 x 4, each labelled with its time; a
   tile every 10 s plus one before each canvas clear), `kf/<ID>/frames.json`, and `events/<ID>.json` (visual change
   events: start/end s, kind add/big/reset, bbox_frac). Segment where the canvas is cleared or the composition
   clearly changes (typically 20–90 s). End screens: one segment with `idea_type: "end_screen"`.
2. `teach/<ID>.json` — the teaching card (how it was taught, talmel, book understanding, voice, game, notes, checks).
   Format: `TEACHING_CARD_SCHEMA.md`. Inputs: the full transcript `stt2/<ID>.json` (segments with start/end and word
   timings; field `language` says hi or en; small recognition errors are normal), your own canvas card, and every
   talmel sheet `talmel/<ID>/sheet-NN.jpg` with `talmel/<ID>/tiles.json` (each tile: the frame just after a visual
   change, a red box on what changed, and the words spoken from 3 s before to 1.5 s after, the nearest word in
   [brackets]). One `talmel` row per tile; take `naming_word` exactly as it appears in the tile text; together = the
   naming word within about ±0.8 s of the change. If a tile falls in a transcript gap, say so instead of guessing.

Folder: `/tmp/claude-0/-home-claude/2458773c-72c0-5c80-9ef5-9b5df2cc93b9/scratchpad/econ/` (all paths above are
relative to it). Finished examples of the level of detail: `cards3/E32.json` and `teach/E17.json` (read once; do not
copy their content). Other agents write other IDs in the same folders; touch only yours.

`things` names: reuse these where they fit: bank_building, rbi_building, government_building, office_building,
stock_exchange_building, house, warehouse, factory, shop, rural_bank_hut, person, crowd_people, committee_desk,
rupee_note, dollar_note, money_bag, gold_bar, bond_certificate, share_certificate, document, law_document,
licence_paper, stamp, vault, percentage_badge, risk_badge, price_tag, gauge, barrier_wall, rope, hand, globe,
india_map, world_map, calendar, mobile_phone, laptop, basket, goods_boxes, truck, graph_axes, bar_chart_icon,
table_grid, timeline, tick_mark, cross_mark, question_mark, speech_bubble, brand_logo, real_person_photo, coin_jar,
pillar, briefcase, podium_steps, staircase, desk, chair, piggy_bank, cart, stacked_bar, ruler, foreign_note. Add a new
generic snake_case name only when none fits.

New in batch 5 — the place. In every canvas-card segment add `place`: the world the segment happens in, one of
market, bank_hall, central_bank, exchange_floor, port, factory, village, office, court, city, assembly, plain_canvas
(a board or blank background with no place), or `other:<snake_name>` for a place not in the list; and `place_change`:
what about the place itself changes on screen and on which spoken word (a vault opens, the board turns red, night
falls, the crowd grows), or "" when nothing does. BIE now has these places as modifiable worlds; we learn which
ideas need a place, and which changes of the place teach.

What matters most:
- canvas card `shown_as`: how the picture makes the idea visible (what appears, moves, splits, is struck out), and an
  honest `meaning_carrier` (picture / picture_plus_label / diagram / text_only).
- teaching card: the narration moves actually used (scene or problem before the term, one running example with
  numbers, yaani unpacking, cause chains, what-if, the learner's objection voiced and answered, conclusion lines,
  recap, exam link); the `book_understanding.breakdown_rule` (how the topic was cut) and `teaching_order`; concrete
  `game_ideas` ("padhai hi game": the learner acts and the economic process happens; a wrong move shows what breaks)
  and `notes_questions`.
- Flag numbers that are shown but not spoken (or the reverse), spoken directions that contradict the motion, and
  doubtful facts (describe, do not certify).

Rules: English in our own short words (Hinglish fine in notes questions); never copy long passages of the narration,
on-screen text or exam questions; do not save, crop or copy any image; valid JSON only. Check the teaching cards with
`python3 /tmp/claude-0/-home-claude/2458773c-72c0-5c80-9ef5-9b5df2cc93b9/scratchpad/check_teach_args.py <IDs>` and
the canvas cards with your own Python check (parses, every segment has the base and v3 fields).

Reply briefly: per video the top 3 showing ideas and top 3 teaching moves worth teaching BIE, 1 game idea, the new
`things` names you added, and any recurring thing BIE should have as a drawing (saancha) that is not in the list.
