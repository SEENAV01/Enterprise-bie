# Task card · how BIE tells the AI exactly what to make

Task 043 · design, 22 October 2026 · implemented in Task 045 (`bie/brain/cards.py`, Sections 1 and 2) · Schema:
`bie/brain/task_card.schema.json` · Example: `docs/roadmap/task_card.example.json` (a real read_page card, built by code)

BIE is the system between Navin and the AI. It does not send the AI a long essay and hope; it sends a
**task card**: a short, fixed-format instruction that names the task, the unit, every part with its content
type and the questions that part must answer, the rule ids that apply, the output schema and the coverage
list. BIE's code then checks the answer against the same card.

## Why a card

| Problem today (Tasks 039–042) | What the card changes |
| --- | --- |
| Each call carries long prose instructions plus a large slice of the chapter map, rebuilt per call | The fixed part (role, rule texts, content types, schema) is one cached prefix; the card itself is about 800 tokens |
| The AI decides by itself what each part is and which questions matter | BIE names the content type of each part and its required questions (`bie/brain/rulebook/content_types.json`) |
| Coverage is claimed in the output and checked afterwards | The card lists `must_cover`; the output must claim every id in one named field; code checks both ways |
| Rules are referred to by text | Rules are referred to by id; texts live once in the prefix with the rulebook version and hash |
| Instructions differ slightly between sections | Every section sends the same card shape; only `task`, `parts` and the output schema change |

## Message layout

Every maker or reviewer call has exactly this shape:

1. **System message = the fixed prefix** (same bytes for every card of the same section and task in a run):
   1. header line: `BIE task prefix <prefix_id> · rulebook <version> · content types <version> · schema <schema_id>`;
   2. role (one paragraph, from the section);
   3. rule texts, sorted by id, only the rules of this section (`[S2-04] …`);
   4. the content types this section can meet: for each, its required questions and teaching pattern (from
      `content_types.json`, the same order every time);
   5. the output schema (JSON, keys sorted);
   6. how to answer: one JSON object; brief notes first (G-03); claim coverage in the named field.
2. **User message = the card** (compact JSON, keys in schema order), then the source parts: the page images
   as image parts, and the native text blocks of the unit as `block id | text` lines.
3. **Remakes** add the maker's previous answer and BIE's findings after the card, as today; the prefix and the
   card are not rebuilt.

**Cache rules.** Nothing that changes per unit goes into the prefix (no page numbers, no titles, no dates, no
run ids, no counts). The prefix is hashed (`prefix.sha256`) and recorded in every process record, so a changed
prefix is visible. Providers cache repeated prefixes on their side:

- Gemini (2.5 and newer) caches repeated prefixes implicitly; Google's own API bills cached input at a 90%
  discount (ai.google.dev "optimization"); through AICredits the model list shows a cached-input price, for
  example Gemini 4 Argon $0.10 instead of $2.00 per million input tokens (api.aicredits.in/api/models,
  20 Oct 2026). A hit is not guaranteed and needs a prefix above the provider's minimum length.
- OpenAI caches repeated prefixes automatically; AICredits bills cached input at half price.
- Claude through AICredits needs `"cache": true` (reads 0.1×, writes 1.25×, 5-minute life, prompts of about
  1,000 tokens or more). Claude is not used now (Navin, 21 Oct 2026).

The ledger now records `cached_input_tokens` per call (Task 043), so cache hits are measured, not assumed.

## The card

| Field | What it holds | Checked by code |
| --- | --- | --- |
| `card`, `card_id` | Format version; `<section>.<task>@<chapter>/<unit>` | unique in the run |
| `section`, `task` | Which section and which of its tasks (`read_page`, `build_chapter_map`, `trim_prerequisites`, `plan_videos`, `write_script`, `direct_scenes`, `plan_assets`, `choose_asset`, `lay_out_scene`, `design_game`, `build_mission`, `write_notes`, `review`) | task belongs to the section |
| `prefix` | `prefix_id`, rulebook version, content-types version, output schema id, prefix hash | matches the system message actually sent |
| `unit` | Unit id, title, pages | pages exist in the chapter |
| `parts` | For each part: `item_ids`, one content `type`, the `questions` it must answer, one-line `focus` | every item id exists in the chapter map; the questions include the type's `required_asks` |
| `rules` | Rule ids that apply (texts are in the prefix) | every id is a locked rule of this section |
| `output` | Output schema id, `full` or `patch`, output token cap | the schema is the one in the prefix |
| `coverage` | `must_cover` item ids, the output field that claims them, `may_skip` with a reason each | after the answer: every `must_cover` id is claimed; no claimed id is unknown; skips have reasons |
| `context` | A slice of the compact chapter map (`[id, type, page, short text]` rows) and one line each on the previous and next unit. Since Task 045d the naksha's own item rows also carry a short `unpack` cell (the terms opened, the why steps, an example), and the script's source lists every item's full unpack and the locked explanations (`explanations.json`) | only ids that exist |
| `source` | Native text block ids and page images (page and hash) sent with the card | the images sent have these hashes |

## The compact chapter map (shared by every section)

Section 1 keeps its full chapter map (every item with its teacher questions and answers) as the record. From it
BIE derives one **compact chapter map** that every later section uses, so no section re-sends the full map:

- items: `[id, content type, page, short text (at most about 100 characters), teachable, exam importance]`;
- concepts: `[concept id, name, content type, item ids]`;
- relations: `[from, relation, to]` (part of, type of, depends on, causes, contrasts with, sequence next, …);
- teaching order and the prerequisites to teach first.

A card's `context.map_slice` is the part of this compact map that its unit needs: its own items, their
prerequisites and the items they relate to. The teacher answers of Section 1 travel only where a section needs
them (lesson and notes), as part of the source, never the whole chapter.

## Example

`docs/roadmap/task_card.example.json` is the real read_page card that `bie/brain/cards.py` builds for page 3 of the tissue
chapter (no AI involved): BIE's code proposes `classification` for "There are mainly four different types of tissues
present in our body." and the four numbered lines under it (list context), structure or classification for other lines,
lists the page number as `may_skip` and every other block in `must_cover`. It is 4,453 characters compact (about 1,300
tokens). Its prefix (`understand.read_page/2`) is 15,237 characters (about 4,440 tokens) and is the same bytes for
every page of the run (rebuilt on 23 October 2026 after the seekh → code changes of job 1).

The design example of Task 043 (a lesson card for page 3) showed why the card names the type: Section 1 typed the four
list points "1. Epithelial … 4. Connective" as `fact`, while together they are a classification. The code now
proposes `classification` for them, and a maker that disagrees must say why.

## What Task 045 implemented (PR A, offline)

1. `bie/brain/cards.py`: the prefix (stable bytes, sha256 on the card and in every process record), the card in schema
   order, card checks before anything is sent, `must_cover` checked both ways after the answer. The reviewer gets its
   own fixed review prefix and the maker's card.
2. Cards for Section 1 (`read_page`, `build_chapter_map`) and Section 2 (`plan_videos`, `write_script`).
3. Content-type detection in code (`bie/brain/content_types.py`) compared with the maker's type in every round; required
   questions per type enforced in Section 1 for every teachable item.
4. The naksha (`bie/brain/naksha.py`): the compact chapter map, with slices per card.

Changes to the design, found while building it:

- A part's `type` may be `none`: on a read_page card for blocks the code has no proposal for (the maker decides), and
  on a script card for a video's exam questions (PYQs), which are answered as exam tips (step 0).
- On a read_page card, `item_ids` are native text block ids (and `pNNNN-image` for the page image); on a plan_videos
  card the parts are concepts and `must_cover` lists concept ids.
- The course (title, subject, learners, exam, language) is in the prefix: it is the same for every card of a run.
- Measured on the tissue chapter: a read_page card is 1,256–4,129 characters; the prefix makes each page's input larger
  than before (about 4,350 + 1,030 tokens against about 2,240 + 900), so its value depends on provider caching, which the
  ledger's `cached_input_tokens` will show in the live runs.

Still to do: Sections 3–7 switch to cards one at a time (046–050), each measured before and after from the ledger.
