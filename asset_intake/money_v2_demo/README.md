# Money v2 demo (Claude's demo, not BIE output)

Navin asked on 3 November 2026 for Money v2 made by Claude with BIE's workflow, start to end, in his interim clone voice,
so he can judge it; if it passes, the process becomes BIE's rules, saanche and code (see `PROCESS.md`).
Status: made and rendered (10 min 53 s, 1280 × 720), waiting for Navin's verdict. Not BIE output; never a passed output.

Not in this folder on purpose: Navin's voice recording, the generated voice and the video (the repository is public).

| File | What it is |
| --- | --- |
| `script.py` → `script.json` | the narration (67 lines), subtitles in Hinglish, voice text in Devanagari, book items covered |
| `tts_v2.py` | voice: Chatterbox Multilingual (MIT) with Navin's reference clip, capped generation, seed per sentence |
| `assemble.py`, `align.py` | trims, checks every sentence by speech-to-text, places the voice on the timeline, pitch −2 semitones |
| `timeline.py` | where every line and sentence sits; cue word → time |
| `builder.py` | the scene plan: for every line the thing said and the action said, on the word it is said |
| `dist/draw.js`, `dist/people.js` | the drawings and the characters (poses, hand positions, expressions), backgrounds |
| `dist/engine.js`, `dist/index.html` | the frame renderer (same window API as BIE's `stills.mjs`) |
| `render.mjs`, `render_all.sh` | frame-range render in parallel halves, then the voice is muxed |

Licences: Fluent Emoji (MIT, `dist/assets/LICENSE-fluentui-emoji.txt`), Baloo 2 and Hind (OFL, `dist/fonts/`),
land outline from Natural Earth via `world-atlas` (ISC; data public domain), everything else drawn here.
