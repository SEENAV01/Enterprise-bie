# The teaching soul · how BIE opens a book (Navin, 24 October 2026)

Navin's verdict on the tissue scripts (job 3, 23 October 2026): they restate the book. "Epithelium absorptive aur
secretive surfaces par milta hai" is the book's line in Hinglish; a teacher would say what an absorptive surface is,
show one the learner knows, and say why a thin sheet of cells sits there. This page is the agreed answer, for every
subject, and what BIE now does about it (Task 045d). It summarises; the binding rules are in
`bie/brain/rulebook/vision-2026-10-21.json` (G-06, G-07, S1-15, S2-07, S3-06) and the data files next to it.

## 1. What BIE is between the learner and the book

BIE is the link between the learner and the book, like a teacher. The book is the base; BIE carries its text, easy or
hard, into the learner's mind. It never just reads the line out (rule G-06). Every book line is opened: what its words
mean, why it is so, where it is seen, what follows.

## 2. The seven opening steps (one book line → one teacher's beat)

`bie/brain/rulebook/teacher_examples.json`, `opening_steps`:

1. a question about something the learner can see, then the name;
2. every term opened: its plain meaning with "yaani" and one everyday image (the word root where it helps);
3. the why, starting from a need or a problem, one link at a time;
4. an example or the place, by a zoom from the organ or the thing the learner knows;
5. the consequence: what follows, and the link to the previous or the next idea;
6. the contrast: what it is not, and what the exam confuses it with;
7. the memory beat by level: the exam's "yaad rakhna", the other names, the trick.

Not every line needs all seven; after any book line the beat must carry at least one of 2, 3 or 4 (rule S2-07).

## 3. The nine teacher methods (plus Navin's own)

From real teacher videos, paraphrased, Navin's selection; each with an example in the file, carried in every
script prefix as good examples: open with a question on something visible · one everyday image per shape or function
("farsh ki tiles = squamous") · the word root where it helps ("slender yaani long aur narrow") · why starts from a need
("pet mein HCl banta hai, isliye…") · contrast with the neighbour · ask and repeat the key word ("Irregular walls.
Kaisi? Irregular.") · exam memory beats by level · link to something already known · meaning with two or three real
examples. Navin's example: the book's adjective opened in three moves (what it means, an example the learner knows,
why this tissue is there). Navin adds methods and examples in the file and bumps its version.

## 4. Where it is built

| Layer | What changed (Task 045d) | Code check |
| --- | --- | --- |
| Section 1, understanding | Every teachable item gets an `unpack`: terms `[{term, plain_meaning (simple Hindi), everyday_image}]`, `why_chain` (1–4 steps, each with its basis, book or standard, starting from a need), `example_or_place`, `consequence`, `visual_verb`, `level_extra`. The naksha carries a short unpack cell per item | S1-15: at least one unpack element per teachable item; every why step names its basis; the plain meaning is Devanagari for Hinglish and never the term itself; the chain is no longer than the level allows |
| Section 2, plan and script | Pattern steps are flexible: a step may be skipped with a stated reason (`skipped_steps`), at most half of a pattern; one recap per part and one closing recap. New family pattern for a classification (section 6). The script maker gets every item's unpack and the locked explanations | S2-07: dohraav pakad (a beat whose English content words are 60% or more the book's own, 6 or more words, with no yaani / why / example / contrast marker goes back); clipped verbless Hindi sentences go back; a new topic opens with a question; duplicate recaps go back; a skipped step needs a real reason and must not also be performed |
| The measure | `dohraav` per video and per run: the share of judged beats (explaining beats that cover items) that only restate; `tools/dohraav.py <run folders>` prints it for any run, before and after | reported in `lesson_plan.json`, `SUMMARY.json` and the readable pages |

## 5. Level profiles (how deep, not how well)

`bie/brain/rulebook/level_profiles.json`, versioned, Navin edits it: **school** (class 6–10: every term opened,
one why step from daily life, a trick for every list), **neet_11_12** (every term of the syllabus, 2–3 why steps to the
mechanism, "yaad rakhna" and the trap), **upsc_pcs** (fewer technical terms, a two-step why to daily life, health or
governance, the PYQ pattern), **revision** (one line per item, no new terms, one trick per list). The profile goes into
the fixed prefix of every page, plan and script card.

The level is inferred from the book's text (explicit markers such as "Class IX", "NEET", "MBBS"; without markers, the
share of long words) and combined with the course setting (`course.level`, or the words of `learners` and `exam`). When
they disagree (an MBBS text under a class 9 course; a text deeper than any profile), the run stops with status
`stopped: level` before any call and asks Navin; his answer is `--level <id> --trust-level`. The tissue chapter reads as
senior secondary and fits the UPSC profile, so it runs without a question.

## 6. The family pattern (classification)

A classification is taught as a family (`content_types.json`, 2026-10-24.1): the overview tree first (the basis of
division and every member named) → every member in the same slots (layer and shape → why it is named so → its special
feature → its function with its cause → where it is found by a zoom from the organ → its consequence) → the members
compared side by side, the most confused pair named directly → a memory trick for the family.

## 7. Two layers, like a film (rule G-07)

- **Writer and dialogue** = understanding, plan, script: what is said and how deep. Depth follows the level profile
  and the book's own level.
- **Director, cinematographer, editor** = `director.py`, the video blocks, the render: the presentation quality is the
  same skilled level for every learner, from class 6 to postgraduate. Only the detail shown follows the level, never
  the craft.

## 8. The video benchmark and its grammar (Task 046, rule S3-06)

`bie/brain/rulebook/benchmarks/epithelium_animation.json` is BIE's own shot description of a reference teaching
animation on the epithelium family (0:00 the question over a zoom from the skin … 2:30 the end card), with twelve rules:
one spoken sentence = one shot of 3–5 s (Navin, 26 October 2026; 2–4 s before); about 40–50 s per family member; said = shown; a function sentence shows
motion; a term opened with "yaani" on its first use; every name gets its reason; one "A → B" summary line per member on
a board that fills; the spoken words on top with the English terms coloured; "where found" by a zoom from the organ;
the focus glows; one dark style; depth from the level profile, grammar from the benchmark. Blocks to build in
Task 046: `cell_sheet`, `particle_flow`, `organ_zoom`, `focus_glow`, `kinetic_caption`, `concept_arrow`, `board_build`,
`mnemonic_card`; planned: `tree`, `split_compare`, `cause_chain`.

The video stays code-rendered, never an AI video model. Two routes, both planned in ROADMAP Task 046: **route A**,
three.js scenes rendered through Remotion; **route C**, 3D models made once (Blender Python scripts, or licensed models
in the asset library with their licence recorded) and animated by BIE code. Head to head: BIE's own engine against
AI-written block code on the same benchmark; merge path: an AI writes a block's code once, BIE tests it, Navin approves
it, the block is reused for every later book.

## 9. The explanation library

`bie/brain/rulebook/explanations.json`: every term meaning, everyday image, analogy and why chain that Navin's verdict
locks is stored with its source and run, and reused for the same concept in later books (the page maker gets it as the
unpack to reuse, the script maker as the opening to speak). It starts with Navin's own examples (absorptive surface,
secretive surface, slender). `tools/lock_explanations.py --run <folder> --items <ids> --by "Navin, <date>"` locks after
his verdict; Claude never locks on its own. Over time the writer layer needs less AI for what is already locked.

## 10. Status words

Everything on this page is IMPLEMENTED (offline, with the fake AI) when Task 045d merges; it becomes INTEGRATED when a
live run reads the tissue chapter and writes its scripts through these checks, and ACCEPTED only by Navin's verdict on
the new scripts side by side with the old ones and the dohraav number before and after.
