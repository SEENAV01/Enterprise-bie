# BIE v1.3 — Audio + Captions + Lesson Composer

Pipeline:

Book understanding
 -> Scene DSL
 -> visual component selection
 -> narration script
 -> audio provider adapter
 -> caption timing
 -> scene composition
 -> full lesson composition
 -> MP4

Important:
- The current package contains narration *scripts* derived from scene key points.
- It does NOT pretend that audio has been generated.
- `audio_asset` stays null until a TTS provider is explicitly configured.
- Captions are generated deterministically from the narration script as a production timing scaffold.
- API keys belong in environment variables, never source code.

This separation lets the same educational plan work with different TTS providers.
