# BIE v1.3 — Audio + Caption + Full Lesson Composer

This milestone connects the Scene DSL to:
1. narration scripts
2. caption timing
3. optional audio assets
4. scene-level compositions
5. a single full-lesson Remotion composition

For the Electricity & Magnetism lesson, all 18 scenes are carried forward with source references intact.

Run:
cd remotion
npm install
npm run start

Select `ElectricityMagnetismLesson` to preview the full composition.

To render:
npm run render

To build a caption manifest:
python ../tools/build_caption_manifest.py src/data/electricity-magnetism.lesson.json out/captions.json

Audio is intentionally provider-neutral. Configure a TTS adapter before generating real narration.
