# BIE: the agreed understanding of 3 November 2026

Navin and Claude (planning chat), 3 November 2026. The whole conversation from Navin's verdict on the Money v2 demo
("yeh huyi na baat, achhi bani hai video") up to his message on the teaching-book deliverables ("yeh do cheejen to tum
poori karoge ... notes, game ka code, kaun si cheezen, notes kaise dikhenge, scene plan, cheezen banana") is the
agreed understanding. Read this before any BIE work, in any session. It does not replace `CLAUDE.md`, the Vision Spec
or the Roadmap; where they differ on the points below, this file is the newer decision.

**Hinglish saar (Navin ke liye):** BIE ka goal sahi hai: AI ka sahi, sasta aur tez istemaal karke kitaab se video,
game aur notes. Ab tak BIE ka AI sirf library se chunta tha aur cheezein jyon ki tyon chipka deta tha. Ab BIE
badalne layak saanchon aur ek general engine par chalega, aur uska AI v2 jaise demo ko misaal maankar har line ka
scene plan likhega. Pehle BIE ek-button tak juda hua product banega. Phir har subject ki ek "sikhane wali kitaab"
aur us subject ki videos se BIE seekhega: kitaab samajhna, saanche, game, notes, aur tarika. Usi subject ki agli
kitaab BIE ke liye aasaan hogi. Lakshya 22 November.

## 1. What happened and why

- Claude hand-made Money v2 (pages 2–3) with BIE's workflow start to end: narration (67 lines, plain Hinglish, all 32
  book items), Navin's interim clone voice, a scene plan where every thing said is shown and every action said
  happens on its word, rendered by a small engine. Navin's verdict: "yeh huyi na baat, achhi bani hai video".
  The code and the process notes are on branch `asset-intake`, folder `asset_intake/money_v2_demo/`
  (`PROCESS.md`). It is Claude's demo, not BIE output.
- Why BIE's own videos failed (D1/D2): its director could only choose from a small fixed vocabulary (two worlds,
  icons, text boards), had no actions, could not create or modify assets, and its checks measured format, not
  meaning. So it pasted library items unchanged, repeated the same setup, and cost more than its output was worth.
- BIE's goal is kept: precise, cheap, fast, consistent educational content at scale, which raw AI video tools
  (12-second clips) cannot give.

## 2. Decisions

1. **One world, one story, one cast is not a rule.** The story is whatever makes the concept visible; continuity of
   characters is a tool used when it helps.
2. **Assets are parametric saanche (code), not fixed pictures.** Every thing is a function with parameters (colour,
   label, size, content, state, pose, held item), so one saancha serves many uses. Modify and reuse first; create
   from scratch only when nothing fits. A missing thing is written as a new saancha by BIE's AI (or BIE's coder),
   tested, licence-clean, and added to the library for every later book.
3. **Three layers for showing:**
   - **Engine (all subjects):** scene, camera, timing to the voice (cue words), subtitles, layout checks, and general
     motion parts: appear/disappear, move along a path, hand over, transform A→B, count, split/join, fill/empty,
     flow along an arrow, compare, highlight, zoom, refuse (cross) / accept (tick), thought bubble.
   - **Subject kits (saanche per subject):** learned from Navin's reference videos and the teaching book of each
     subject (economy: money, people, shop; science: cell, apparatus, circuit, force, graph; polity: institutions,
     documents, maps; history: timelines, events).
   - **Per-video scene plan (written by BIE's AI):** for every line, what is seen and what happens, on which word,
     using the engine and the kits, in a plan language like the v2 demo's `builder.py`, with Claude's gold videos
     as examples. Code checks the plan.
4. **Science does not need 3D by default.** Most topics are taught with 2D/2.5D animated diagrams; 3D only where
   depth matters. The style per subject is learned from Navin's reference videos.
5. **Voice:** Navin's clone (Chatterbox Multilingual, his reference, pitch −2 semitones) is the interim voice; the
   voice section is finalised after one-button. GPU only on demand for whole-book batches: free GPU quotas first if
   their terms allow, otherwise hourly rental. Budget is Navin's decision.
6. **Video, game and notes share one base.** The same book understanding and the same saanche feed all three: a
   video's story becomes a game level ("padhai hi game": the student acts and the process happens), and its
   questions become infographic notes pages.
7. **Claude does not make whole books.** Per subject, Claude prepares one teaching book (section 3) and 1–2 gold
   videos; BIE makes the rest; Claude checks samples. Hand-made outputs are labelled "Claude's demo, not BIE output"
   and never become passed outputs.

## 3. The teaching book (one per subject)

The purpose is generalisation: what Claude builds from one book of a subject makes every other book of that subject
easy for BIE. Navin will not give BIE the same book. Claude does not render full videos here; Claude builds what BIE
needs to turn that book into its end output:

| Deliverable | What it contains |
| --- | --- |
| Book map | concepts per chapter, their type (process, comparison, timeline, numbers, definition), dependencies, the book's own pictures and tables; becomes BIE's book-understanding rules and examples |
| Scene plans | full line-by-line plans for 1–2 chapters (v2 standard); for the other chapters an outline per concept: story or picture, saanche and actions needed |
| Saanche (code) | the whole book's needs list ranked by frequency; the most frequent built first as parametric code (written, or fetched from open libraries and modified); a still for each |
| Game | whole-book game plan (chapter → game mechanic → levels); 3–5 game mechanics as code (run a process, build a timeline where a wrong pick breaks it, find the matching partner, place things correctly, cause-effect chain, market simulation); 2–3 playable sample levels |
| Notes | question list per chapter for the whole book; a notes-page saancha (one question per page, answered by a picture, flow, comparison or table, built from the same saanche); real pages for 1–2 chapters |
| Process file | why each decision was made (becomes BIE's rules), time and cost of each step |

What BIE gains from one teaching book: (1) the way to understand that subject's books (how concepts open, where
there is a process, a comparison, a timeline); (2) the subject's saanche (things, characters, places, actions, all
parametric); (3) game saanche that suit the subject (economy: running a market; history: building a timeline);
(4) notes saanche (question pages that cover the whole book in less time); (5) process, code and cost measurements
(how much AI each step needed and how much code did).

Example of the shared base, from Money v2: the barter story becomes a game level (find a partner who has cloth and
wants wheat; a wrong partner refuses; then use salt as the bridge to finish the deal), and its questions become notes
pages ("Barter kya hai?": the exchange picture and the four features as icons; "Intrinsic aur Extrinsic mein farak?":
the ten differences as a compact comparison). Making one section strong makes the other two strong, so the game and
notes sections get completed on the same road.

Honest limit: a new book of the same subject will still bring some new things; BIE's AI makes them and they join the
library, so each new book needs less work.

What Navin sees per teaching book: one page with stills of the saanche, playable game levels, notes pages and sample
scene plans. Done when: Navin passes the samples, everything is in BIE's slot formats, and BIE run on a new book of
the same subject shows the difference.

Ranking: things that recur most are built first; a one-off thing is left for BIE's AI to make. Every deliverable is
in the format of BIE's slots (section 4, phase 1) so it plugs in directly. Proof of generalisation: after the teaching
book, BIE runs on an unseen book of the same subject; we measure how many new saanche it needed, the quality and the
cost.

## 4. Plan to 22 November 2026

| Phase | Dates (target) | Work |
| --- | --- | --- |
| 1. Skeleton | about 4–8 Nov | Claude Code, in one or two big prompts (it still opens PRs inside, Navin does not manage them one by one): one button, PDF → book understanding → narration → scene plan on the new engine (ported from the v2 demo) → voice → render → notes → game → one page with all outputs. Slots (formats) for saanche, game mechanics and notes pages. Quality not final; everything connected and running. |
| 2. Learning | from now, in parallel | Navin gives reference videos per subject and then that subject's teaching-book PDF (section 3). The videos teach every section of BIE, not only showing (section 8). Everything lands in BIE's slots. |
| 3. Two-place runs | about 9–18 Nov | 3–4 books: chapters made by Claude following BIE's workflow and by BIE; compare; every gap becomes code, saanche or examples in BIE; what Navin passes is locked. AI work goes down, code goes up, so cost and time fall. |
| 4. Whole book | about 19–22 Nov | BIE makes one unseen book end to end; Navin reviews; then official use for his goal. |

Open decisions for Navin: the GPU route and budget for the voice (options with prices to be brought to him); the
second subject (Polity proposed). Science 3D, and game and notes at the full quality of his vision, come after
22 November; game and notes join the skeleton in phase 1 and reach his vision through phase 3.

## 5. Quality target

"Zero error" is measured, not promised: every line "said = shown" (≥ 95%, by code and the LOOK review), no broken
render, voice and picture in sync, Navin passes the samples he checks; a failed check makes BIE redo the part by
itself. 22 November is tight; phase 3 takes the longest; progress is reported honestly every day.

## 6. Rules that continue

Lesson content in production is made by BIE; Claude's demos are labelled and never passed outputs. Navin's voice
recordings and generated voice never go into the public repository. Licences: CC0, public domain, CC BY (credited),
MIT, Apache, OFL; never NC or SA. No real persons' likeness. Caution and fact-check lines are background checks, never
on screen or in the narration. Narration never says "the book says". Secrets only in environment or Actions secrets.
Navin decides budget, security, quality verdicts and subjects.

## 7. Working arrangement

Discussion and decisions in the planning chat (plain Hinglish, one point at a time, plan before action); Claude
writes the prompts; Claude Code builds and merges on green; each task ends with one report file; the planning chat
does the learning track (videos, teaching books) on branch `asset-intake` in BIE's slot formats.

## 8. Addendum, 4 November 2026: what the videos and the teaching book are for

**Hinglish saar (Navin ke liye):** Videos isliye hain ki Claude unhe dekh kar BIE ke liye jo bhi zaroori ho woh
kare; PDF isliye hai ki Claude us kitab se BIE ke liye jo bhi zaroori ho woh kare, taaki BIE us vision aur goal par
khara utre jo humne saath milkar socha hai. Videos BIE ke har section ko sikhati hain, sirf dikhana nahi: padhana,
padhane-dikhane ka talmel, kitab samajhna, awaaz, jaanch, game aur notes bhi. Asli imtihaan BIE ki pehli PDF book
hai: in sab ke baad bhi agar BIE wahan khara nahi utra, to BIE banana paise aur samay ki barbaadi hai.

Navin's purpose, in his words: he gives reference videos so that Claude, having watched them, does whatever BIE
needs; he gives the PDF so that Claude does whatever BIE needs; both serve the vision and goal designed together. If
after these processes BIE does not meet his vision and goal on its first PDF book, building BIE has wasted his money
and time. Every learning batch is therefore judged by what it adds to that test.

Why this addendum: section 4 described the video track as "how each idea is shown, the things needed, pace, text and
camera", and Claude kept narrowing the work to showing. That was too narrow. **The videos teach every section of
BIE.** Per batch of videos, Claude extracts and builds:

| BIE section | What the videos teach | What lands in BIE |
| --- | --- | --- |
| Book understanding | how a topic is broken into concepts, the teaching order (not the page order), which prerequisite is recalled first, where a concept is a process, comparison, timeline or number | concept-breakdown and ordering rules, with examples |
| Narration (teaching) | how a concept is explained: the scene or story before the term, examples and stories woven through, plain-word unpacking (yaani), cause chains, what-if cases (maan lijiye), small numbers, conclusion lines, recap, the exam link | narration rules and structure; gold lines in our own words |
| Teaching-showing fit (talmel) | what is being said when each thing appears; whether the picture leads or follows the voice; how one picture carries a whole story | scene-plan cue rules and their code checks |
| Scene plan (director) | the showing patterns for each kind of idea | the show lexicon, scene structure |
| Saanche and engine | things, characters, places, actions, camera, pace | parametric saanche and engine parts |
| Voice | pace, pauses, emphasis | voice rules |
| Checks | what worked and what was weak | code checks |
| Game | the processes in a video that can become play | game mechanics and level ideas |
| Notes | the questions a video answers, its recap pictures | notes-page questions and layouts |

Order per subject: that subject's videos first (Navin keeps adding videos until the subject is covered), then its
teaching-book PDF (section 3), then the next subject. Economy is the first subject.

**A batch is done only when its outputs are inside BIE's slots and run on a real page,** not when files sit on the
`asset-intake` branch. On 4 November the economy kit of 27 October and the batch-3 saanche are not yet inside
`bie/brain/video/engine/`; joining them is part of the economy work.

Decided by Navin on 4 November: an India map follows the official boundary of the Survey of India. The source is
licence-checked before use; until it is in place BIE does not draw an India outline and uses a "भारत" label instead.

Clean, word-timed transcripts of the reference narration are needed to learn teaching and the teaching-showing fit;
if getting them costs money, Navin decides first.

**Decided by Navin on 4 November 2026 (standing):** the rules, saanche and examples Claude builds from Navin's reference
videos and teaching-book PDFs go into BIE locked, without asking him rule by rule, and without separate before/after
comparison runs. He gave the videos and PDFs so that Claude puts its own workflow and thinking into BIE; he judges the
result the way he judged the Money v2 demo, by passing BIE's own output on his books. The first 23 rules
(`bie/brain/rulebook/econ_videos.json`) were locked the same day ("sab lock kar dun"). Security-sensitive changes,
budget, subjects and his verdict on outputs remain his.

Navin's product picture (4 November 2026): Claude Code turns BIE into a one-button software (Windows and Android app)
connected to his AI subscription; the planning chat keeps taking his videos and PDFs to make that software fully
capable. BIE is to AI and books what an operating system is to a machine and its user: it makes AI do exactly the
needed work, precisely and cheaply. His target: about 10,000 accurate, engaging educational videos (with games and
notes) from his PDF books for about ₹1–2 lakh, fast; the cost per page and per video is measured as BIE runs.

**Navin, 5 November 2026 (standing):** the videos must be engaging and must make the concept clear: what the student's
eyes see and ears hear at the same moment join into one clear idea in the mind. The benchmark stays the Money v2 demo,
not the reference videos: what the references do rarely (a place, people acting, things moving) is no ceiling for BIE;
when the scene plan needs it, people, moving things, processes and worlds work in as many segments as it needs (rule
EV-S13 of `bie/brain/rulebook/econ_videos.json`, rewritten that day).
