# BIE v1.0 — Real Book Intelligence Engine

This is the first real API-backed implementation of the architecture.

## Pipeline

PDF
→ M2 page-preserving extraction
→ M3 AI atomic semantic decomposition
→ M4 external knowledge frontier + web verification
→ M5 deterministic verification gate
→ M6 lesson plan
→ M7 Scene DSL
→ M8 Game DSL

## Key design rule

The model is not allowed to silently mix:
- what the book says,
- what is required before the book,
- what comes after the book,
- and what is an external application.

Those are separate frontier buckets with provenance.

## Model

Default: `gpt-5.6-luna`, configurable with `BIE_MODEL`.

OpenAI's current model catalog lists GPT-5.6 Luna as a cost-sensitive/high-volume model and says the latest models are available through the Responses API. Structured Outputs are used so extraction is returned against an explicit JSON Schema.

## Run

1. Install:
`pip install -r requirements.txt`
2. Set `OPENAI_API_KEY` securely.
3. Run:
`python -m bie.cli /path/to/book.pdf --out artifacts`

M5 deliberately stops downstream generation when evidence/provenance falls below thresholds. This is safer than generating a polished lesson from uncertain extraction.

## Important production gaps

v1.0 is an actual vertical slice, not the final production system. For large books we should next add:
- multimodal page rendering for diagrams/equations
- chunk-level parallelism and merge
- retrieval cache
- source-ranking policy
- human review UI
- benchmark dataset and regression suite
- calibrated evaluator
- real Remotion renderer
- real game runtime
- Batch API mode for large asynchronous jobs
