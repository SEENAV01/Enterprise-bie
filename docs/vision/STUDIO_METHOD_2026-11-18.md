# Film-pehle course studio: the method (18 November 2026)

Claude's demo, not BIE output. This page records the method; the work was done outside BIE (learning track,
CLAUDE.md "Learning track"). Nothing here is IMPLEMENTED, INTEGRATED or ACCEPTED in BIE yet. No demo output goes into
`tests/fixtures/passed_outputs/`.

## What happened

- Navin, 18 November 2026: he asked for one topic from "Unit 10: Geography of India" at the Chapter 17 (Campbell Biology)
  golden-benchmark level, with a film, a Living Book (notes) and a game. Claude made the Monsoon set. Navin's verdicts:
  70 % → film approved ("Ek dum approved hai") → 8/10 → **9/10, accepted to move on**: "10 mein se 9 ke sath aage badho ab".
- Navin's order for what follows (decision card, 18 November 2026): Monsoon to its best, then **save the method and
  templates** (this page, the Navin-facing doc and the Drive kit), then **bring the templates into BIE**.
- Where things live:
  - The Navin-facing method, in Hinglish: Claude Docs "Kaam ki Kitaab: Film-pehle Course Studio".
  - The rebuild kit, in Navin's Google Drive (folder "Monsoon rebuild kit (2026-11-18)"): code templates, Navin's 11
    ChatGPT images, the film's clean frames, map texture and height, narration clips, and a README. The kit was
    checked by rebuilding the Living Book and the game from the zips alone in an empty folder (same sizes, no page errors).
  - Lesson content and Navin's images stay out of this public repository.

## The method in one picture

```
Topic (Navin) → Script (12 shots, one showing moment each) → Voice (shot lengths) → Film
Film → clean frames + pins → Living Book  ← ChatGPT images (Navin, from Claude's prompts)
Film's engine → Game (hands-on stage + decision, five times)
Navin reviews after each step; Living Book and game start only after the film is approved.
```

## The six steps

1. **Script, written as a film.** 10–12 shots in story order (question → causes → effects → recap). Each shot has an
   id, a title, a one-line key, and a *dikhane ka pal* (showing moment): one thing that changes on screen and carries
   the concept. Narration speaks to the viewer ("Dekhiye…"), 2–6 short sentences a shot; whatever cannot be shown is
   not in the script. Roman for reading, Devanagari for the voice.
2. **Film.** A subject visual engine (Geography: a three.js relief map from AWS Terrain Tiles and Natural Earth, India's
   own boundary view, wind streams, rain regions, ITCZ, labels, markers). Voice first (Kokoro TTS, Apache-2.0, voice
   `hf_alpha`, speed 0.95); shot length = speech + a pause; subtitle times split by sentence length. A deterministic
   compositor (same frame number, same picture) with a 2D layer for title, key, pins and subtitles. Frame capture in
   Chromium at 1280×720, 24 fps; ffmpeg H.264 + AAC + mov_text subtitles; renders resume from a frame. Checks: a
   contact sheet per shot, ASR against the script, phone size. Clean frames without the HUD are captured with their pin
   positions for the Living Book.
3. **Photoreal images (ChatGPT, by Navin).** One prompt per image: number and name, place and season, 2–4 things to
   show clearly (later pinned), camera, 16:9 landscape photoreal, and the bans (no text, logos, recognisable real people,
   flags or emblems). Claude turns each image into a "speaking image": pins (label + x/y in %), motion (arrows with
   flowing dash, rise, rain, glow) and pan/zoom to the part the current sentence names. Faces of Teacher, Asha and Dev
   are Claude-made illustrated SVGs, reused across topics.
4. **Living Book, from the film.** One offline HTML file: cover → chapter map → lessons → review. Each lesson opens with a
   question and has: a lens (film frames + "real world" images), models the learner moves (pressure diagram, 3D map,
   Coriolis globe, Ghat cross-section slider, onset map slider), five dialogue scenes, remember + check, a steps game,
   and speaking notes (picture or diagram, Roman and Hindi text, "Note suniye", table, quick check, transcript).
   Scene rule: one beat per sentence, and what is said is shown at that moment. Beat kinds: image (pan + pins + motion),
   film frame (with its pins), diagram (only the named part lights up, lines draw in), 3D map (one shared map, only that
   sentence's labels). "Poora lesson suniye" plays every scene by itself through a chain of short per-sentence clips —
   seeking inside one large data-URI audio fails on phones.
5. **Game, Pollen Lab pattern.** Five stages; each is a hands-on manipulation on the film's own engine (drag, slider,
   tap) and then one decision with 3–4 options, where every wrong option shows its own reason, and a two-line "why".
   Score at the end, and a link back to the Living Book. An MCQ alone is not a game.
6. **Checks before Navin sees it.** Phone size (Pixel 7), the auto-play chain, said = shown, a contact sheet per shot,
   ASR, every number and date against the source, caution lines and source names off the learner's screen (rule D1-06),
   licences (CC0/PD/CC BY/MIT/Apache/OFL only), no real people, logos or emblems, the demo label, files in Drive.

## Navin's review rules (from his own reviews)

| # | Rule | From |
| --- | --- | --- |
| 1 | Video first; notes and game use the video's elements, never notes pasted into a video. | Monsoon review 1, 70 % |
| 2 | Notes are a living book: the video's shots plus their own designs. | Film approval |
| 3 | Rich photoreal images; Teacher, Asha and Dev have faces. | "Very close" review |
| 4 | Narration comes with animation, motion graphics, interactive images, diagrams and 3D models. | With his 11 images |
| 5 | An image "speaks" with the narration: labels and motion arrive at that sentence. | 8/10 review |
| 6 | Scenes play by themselves in "Poora lesson suniye". | 8/10 review |
| 7 | A game is hands-on (Pollen Lab), not only MCQs. | First review: "bilkul bhi nahi hai" |
| 8 | Caution and fact-check lines stay off the screen. | 30 October 2026, D1-06 |

## Time, honestly

The first Monsoon set took about one working day including review rounds. With the templates, a next topic in the
same subject is estimated at about half a day (not measured yet). A new subject's first topic is slower, because each
subject needs its own visual engine.

## Next: into BIE (reuse, do not duplicate)

The templates join existing BIE parts; nothing becomes a parallel system. First mapping, to be checked against the code
in the integration task:

| Studio part | Existing BIE part it should extend |
| --- | --- |
| Film compositor and the 3D map | The showing engine `bie/brain/video/engine/` and its 3D layer (`engine3d.mjs`, `three/layer3d.mjs`); the map as a geography saancha family next to `families/econ_*.mjs`; shots through `bie.scene-plan/1` |
| Voice per shot and per sentence | `bie/audio/`, with Kokoro recorded through the licence gate (Task 046a-L) as a local voice engine |
| Living Book lessons, scene beats, speaking notes | The notes-page slot `bie/brain/notes_pages.py` (`bie.notes-page/1`) and the notes deck `bie/brain/notes_render.py`; new page kinds for scene beats and the clip chain |
| Game stages and decisions | The game-level slot `bie/brain/game_levels.py` (`bie.game-level/1`) and `bie/brain/game_runtime.py`; the manipulation stage and per-option reasons as additions to the five mechanics |
| Review rules and checks | The rulebook (`bie/brain/rulebook/`) and the render checks, so the checks run as code |

Each part counts only when BIE makes the same kind of output itself, from a real source, through its own sections.
