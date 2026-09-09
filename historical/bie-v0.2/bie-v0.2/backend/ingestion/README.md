# M2 — Book Ingestion Engine

Normalizes native PDFs into a provenance-preserving intermediate document.
It intentionally does **not** call an LLM yet. That separation lets ingestion be
unit-tested and keeps source fidelity independent from semantic interpretation.

## Install

```bash
pip install pymupdf
```

## Run

```bash
python -m backend.ingestion.cli input.pdf output.json
```

The JSON preserves document hash, page number, block order, bounding boxes,
font metadata, image placeholders, and candidate headings/equations.
