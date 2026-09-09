# Book Intelligence Engine (BIE) v0.1

A production-oriented foundation for converting complete books into a verified learning representation, then compiling that representation into lessons, Remotion scenes, and interactive games.

## Pipeline

Book/PDF/EPUB/scan -> document structure -> UBR -> question map -> knowledge graph -> learning graph -> evaluator -> lesson -> Scene DSL -> Remotion / Game DSL

## Design principles

1. Preserve source provenance down to page/block/character offsets when available.
2. Never treat a paragraph as a single knowledge unit by default.
3. Separate book knowledge from current external knowledge.
4. Separate knowledge graph from learning graph.
5. AI emits typed intermediate representations, not arbitrary renderer code.
6. Every generated claim can be traced and evaluated.
7. Evaluation is part of generation, not an afterthought.

## v0.1 status

This repository contains the canonical schemas, Python reference models, deterministic graph utilities, validation, and example pipeline. Model/provider adapters are deliberately isolated so a future OpenAI/local/fine-tuned model can be plugged in without changing the data contracts.

## Run

```bash
python -m backend.example_pipeline
```

No external API or GPU is required for the reference pipeline.
