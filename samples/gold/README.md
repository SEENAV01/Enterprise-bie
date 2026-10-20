# Gold reference lessons

A gold lesson is a hand-directed sample of the finished product for one real chapter: a narrated,
animated video and a playable revision game. It shows the level the automated BIE pipeline has to
reach. It is not pipeline output and it is not accepted product.

## tissues-v1 · "Tissues and Its Types", Video 1 (UPSC / State PCS, Hinglish)

- `tissues-v1/build_lesson.py` writes `lesson.json`. It holds the 7-video plan for the whole chapter and the Video 1 script, split into 14 scenes and 45 narration beats. Each beat's on-screen events are bound to spoken words.
- `tools/make_voice.py` makes the narration and word timings. It runs in `.github/workflows/gold-sample-voice.yml`, which uses OpenAI `gpt-4o-mini-tts` for the voice and `whisper-1` for word timestamps, and stores the output on the `gold-samples` branch.
- `render/` turns the lesson into the video:
  - `prepare.py` builds the frame timeline from the narration. Cues use the word times. When a transcript is incomplete, it falls back to the voiced parts of the audio.
  - `src/` holds the scenes and building blocks. They are written against a Remotion-compatible API in `src/lite.tsx`, so they can move into the Remotion compiler unchanged.
  - `render.mjs` renders every frame in Chromium and encodes it with ffmpeg.
  - `sound.py` adds a quiet synthesized music bed, ducked under the voice, plus cue-bound effects.
- `tissues-v1/game/index.html` is "Meristem Mission", a phone-first game built from the same lesson. Its six rounds use Section 15 mechanic types: sequencing, classify/sort, map interaction, scenario MCQ and misconception trap.

## Rebuild

```bash
python3 samples/gold/tissues-v1/build_lesson.py
python3 samples/gold/render/prepare.py --lesson samples/gold/tissues-v1/lesson.json --voice <gold-samples>/tissues-v1 --out out
node samples/gold/render/build.mjs
python3 samples/gold/render/sound.py --timeline out/timeline.json --narration out/narration.wav --out out/mix.wav
node samples/gold/render/render.mjs --timeline out/timeline.json --audio out/mix.wav --out out/video.mp4
```
