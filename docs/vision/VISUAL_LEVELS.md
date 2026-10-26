# Visual levels (video kaisi ho · Task 046)

Decided by Navin on 26 October 2026, in his words (the two-star level rule and the pace were added the same day; sections below):

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

## The level rule has two stars (Navin, 26 October 2026)

**A. The chapter or book target.** Navin: "90 se 99 percent videos L3 ya isse upar ke level ki ho" — kitaab se banne wali
kul videos ki baat hai, aur ye koshish ka target hai, blocker nahi.

- Every video reports its **main level**: the level in which most of the video (shot-seconds) is made.
- The chapter or book report shows how many videos are at each main level and the share of videos whose main level is L3
  or above; the target is 90–99 %.
- Below the target, the report names the video and the reason. Nothing is blocked.

**B. Inside a video, the shot level.** Navin: "Scene plan ke hisaab se kisi video ka kuch hissa L2 ka ho sakta hai aur usi
mein koi baat L5 se dikhani ho sakti hai; poori video ek level ki bane, ye zaroori nahi."

- The level stays on every shot, from the content and the scene plan (one spoken sentence is one shot, benchmark rule B-01).
- The director's rule: where the content allows, choose L3 or above; L2 only where L2 shows the point better, and the reason
  is written on that shot.
- There is no "90 % of shot seconds or not rendered" check any more; no video is blocked because of its level. A shot at L1
  or L5b is still a planning error and fails the check.
- The report shows every video's level mix (which shots at which level).

How the director starts: from the capability's `default_level` in `bie/toolbox/capabilities.json` (`cell_sheet_3d` → L5a;
`equation_transform` → L3 on a lit board; `vector_field` → L2) and keeps the topic's 3D world under the L3 overlays (a
caption, a label, an arrow) where the world stays on screen. The level profile (`level_profiles.json`) decides how deep the
content goes; the visual grammar and the ladder are the same for every learner (benchmark rule B-12, vision rule G-07).

## The pace: the visual-change rate (Navin, 26 October 2026)

A visual change is a block change, a camera move, or the lit structure moving. The report gives every video's seconds per
change. Targets: micro biology 3–5 s per change (the benchmark: 19 changes in 90 s); engineering and physics worlds 10–20 s
(one 3D world, the camera moves between its parts). Rule VG-01 checks this rate; benchmark rule B-01 says 3–5 s per shot.
Where consecutive sentences would hold the same picture past the band, the director adds a camera move (a zoom on the lit
structure, an orbit, a zoom out) so the picture changes within it. Shown in `shots/<video>.json` (`pace`) and in SHOTS.md.

## Status words

The ladder, the two-star rule and the pace are rules BIE reads (IMPLEMENTED with Task 046 Part A, checked offline on v3 of the tissue chapter). A level
is INTEGRATED only when the blocks that render at it exist and a real book's video has been rendered through them
(Task 046 Part B), and ACCEPTED only when Navin says so.
