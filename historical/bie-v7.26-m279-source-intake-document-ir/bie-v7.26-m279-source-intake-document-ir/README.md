# BIE v7.26 — M279 Source Intake & Document IR

M279 upgrades the canonical M278 spine with a real source-input boundary.

Supported:
- PDF via pypdf
- EPUB XHTML/HTML
- TXT
- Markdown

The adapter emits stable, locatable Document IR blocks. Image-only PDFs are explicitly marked `NEEDS_OCR` and blocked by QA rather than silently producing empty content.
