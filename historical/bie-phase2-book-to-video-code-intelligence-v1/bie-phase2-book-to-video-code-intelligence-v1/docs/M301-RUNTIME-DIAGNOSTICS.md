# M301 Runtime Diagnostics

This package adds a diagnostic checkpoint before attempting the real Lesson 1 render.

It checks for:

- Node
- npm
- npx
- FFmpeg
- ffprobe
- Tesseract
- an existing Remotion `package.json`

The diagnostic output is stored in `M301_RUNTIME_DIAGNOSTICS.json`.

**No render is claimed unless the runtime and actual output artifact exist.**
