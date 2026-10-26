# Visual levels (video kaisi ho · Task 046)

Decided by Navin on 26 October 2026, in his words:

- "Task 46 will surpass even the tarazu point 'video kaisi ho' level on its full completion, implementing things required."
- "90 se 99 percent videos L3 ya isse upar ke level ki ho."
- The chain: content decides the scene plan; the scene plan decides which visual level the video code is made at.
  BIE itself must be capable up to L5a.

The machine-readable copy is `bie/brain/rulebook/visual_levels.json` (schema `bie.brain.visual-levels/1`); the director
(`bie/brain/shots.py`) and the checks read that file, never this page.

## The ladder

| Level | Name | What it means | BIE |
| --- | --- | --- | --- |
| **L1** | Teacher at a board | A person explaining at a board, as in a classroom recording. | Never a BIE output. Only for learning how teachers explain (the teacher example bank). |
| **L2** | Clean 2D | Vector diagrams, draw-on line art, equation cards, slides. | Allowed where a flat drawing is the clearest picture: a vector problem, a circuit, a case card. |
| **L3** | Rich 2D / 2.5D | Motion graphics, illustrated stills, light 3D, timelines, lit boards, kinetic captions. | The floor for most shots: equation steps on a lit board, a self-drawing graph, a timeline, the A → B board, a mnemonic card, a split comparison. |
| **L4** | Stylized 3D | One 3D world per topic; the camera moves between its parts; cutaway and exploded views; a process shown with flow. | Engineering, physics apparatus, the earth, machines, orbits. |
| **L5a** | Photoreal micro or machine 3D | Lighting, depth of field, focus glow, particle motion; cells, molecules, chips, organs. | The epithelium benchmark level. The highest level BIE makes. |
| **L5b** | Photoreal humans, landscapes, Pixar-grade character acting | Feature-film people and places. | Not made by code; outside BIE's output. A scene plan that asks for L5b is a planning error and fails the check. |

## How a level is chosen

1. The content decides the scene plan: one spoken sentence of the passed script is one shot (benchmark rule B-01).
2. Every shot carries a `level` from {L2, L3, L4, L5a}. The director starts from the capability's `default_level` in
   `bie/toolbox/capabilities.json` (`cell_sheet_3d` → L5a; `equation_transform` → L3 on a lit board; `vector_field` → L2)
   and keeps the topic's 3D world under the L3 overlays (a caption, a label, an arrow) where the world stays on screen.
3. The level profile (`level_profiles.json`) decides how deep the content goes; the visual grammar and the level ladder
   are the same for every learner (benchmark rule B-12, vision rule G-07).

## The code check (per video)

- The shot-seconds at **L3 or above must be at least 90 %** of the video (`minimum_share` in the JSON). The report shows
  the split per level (shots, seconds, share).
- A video below 90 % is **not rendered**; a shot at L1 or L5b fails the check as a planning error.
- Shown in `shots/<video>.json` (`level_split`, `at_or_above`, `render_allowed`) and in SHOTS.md.

## Status words

The ladder is a rule BIE reads (IMPLEMENTED with Task 046 Part A, checked offline on v3 of the tissue chapter). A level
is INTEGRATED only when the blocks that render at it exist and a real book's video has been rendered through them
(Task 046 Part B), and ACCEPTED only when Navin says so.
