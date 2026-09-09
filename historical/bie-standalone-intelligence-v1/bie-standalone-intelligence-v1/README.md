# BIE Standalone Intelligence v1

Portable consolidation of the existing Book-to-Video intelligence architecture.

## Scope

**Full Book/PDF -> understanding -> course/lesson/scene/visual planning -> validated video-generation code.**

Not included in this phase:

- MP4 rendering
- FFmpeg
- OCR of rendered video
- publishing

## Run

```bash
python run.py --book /path/to/book.pdf
```

The package currently provides the standalone orchestration boundary and contracts. It does not pretend that every provider/PDF extraction implementation has already been fully wired into one executable binary.
