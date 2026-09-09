# BIE Canonical Backend v1.0

This package consolidates the Book/Source -> Educational Video Intelligence work through M300 into one canonical backend surface.

## Product boundary

`PDF/Book -> document understanding -> grounded knowledge -> learning/pedagogy -> script -> scene plan -> Remotion code`

OpenAI is the underlying reasoning/generation provider. BIE owns orchestration, schemas, provenance, validation boundaries and deterministic code generation.

## OpenAI connection

The backend uses the official OpenAI Python SDK and the Responses API. Set:

```bash
export OPENAI_API_KEY="..."
```

or copy `.env.example` to `.env` and load the variable through your deployment environment.

Model is configurable with `BIE_OPENAI_MODEL`; default is `gpt-5.6-luna`.

## Run

```bash
pip install -r requirements.txt
python run.py --book /path/to/book.pdf --workspace output
```

The API adapter uses Structured Outputs so BIE receives schema-constrained JSON for knowledge, lesson, script and scene stages.

## Architecture

```text
PDF
 ↓
M279–M283 document/knowledge layers
 ↓
M274 OpenAI inference boundary
 ↓
M275 prompt/context engineering
 ↓
M284–M287 lesson/script/scene compilers
 ↓
M288 deterministic Remotion generator
 ↓
M289–M300 QA/repair/runtime artifacts
```

## Important scope note

This is a canonical integration build, not a claim that the full 500-page production acceptance test has already passed. The next validation is the real `Indian Polity (1).pdf` run with an active OpenAI API key.
