# Task card · how BIE tells the AI exactly what to make

Task 043 · design, 22 October 2026 · implemented in Task 045 · Schema: `docs/roadmap/task_card.schema.json`
(moves into `bie/brain/` when Task 045 implements it) · Example: `docs/roadmap/task_card.example.json`

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
| `section`, `task` | Which section and which of its tasks (`read_page`, `build_chapter_map`, `plan_videos`, `write_script`, `direct_scenes`, `plan_assets`, `choose_asset`, `lay_out_scene`, `design_game`, `build_mission`, `write_notes`, `review`) | task belongs to the section |
| `prefix` | `prefix_id`, rulebook version, content-types version, output schema id, prefix hash | matches the system message actually sent |
| `unit` | Unit id, title, pages | pages exist in the chapter |
| `parts` | For each part: `item_ids`, one content `type`, the `questions` it must answer, one-line `focus` | every item id exists in the chapter map; the questions include the type's `required_asks` |
| `rules` | Rule ids that apply (texts are in the prefix) | every id is a locked rule of this section |
| `output` | Output schema id, `full` or `patch`, output token cap | the schema is the one in the prefix |
| `coverage` | `must_cover` item ids, the output field that claims them, `may_skip` with a reason each | after the answer: every `must_cover` id is claimed; no claimed id is unknown; skips have reasons |
| `context` | A slice of the compact chapter map (`[id, type, page, short text]` rows) and one line each on the previous and next unit | only ids that exist |
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

`docs/roadmap/task_card.example.json` is a card for the lesson script of one video on page 3 of the tissue
chapter, using real item ids from live run 39620281561 (epithelial tissue: the four kinds of tissue, the
structure of epithelium, Fig. 6.9 and the comparison table). It validates against the schema with BIE's own
strict validator and is 2,731 characters (about 800 tokens). It is a format example only; lesson content is
made by BIE.

That run also shows why the card names the type: Section 1 typed the four list points "1. Epithelial …
4. Connective" as `fact`, while together they are a classification. In Task 045 the code-side hints in
`content_types.json` ("four different types of tissues", numbered list) propose `classification`, and a
disagreement between code and AI is flagged for the reviewer.

## What Task 045 implements

1. `bie/brain/cards.py`: build the prefix (stable bytes, hash) and the card per unit; validate the card with
   the schema; record `prefix.sha256` and the card in every process record.
2. Compact chapter map from Section 1's output; map slices per unit.
3. Content-type detection from the hints (code), compared with the AI's type; required questions per type
   enforced in Section 1's checks (today only process, comparison and classification are enforced).
4. Sections 2–7 switch from prose instructions to cards, one section at a time, each rerun on the tissue
   chapter and 4–5 chapters of other subjects; tokens, cached tokens and rupees per page compared before and
   after from the ledger.
