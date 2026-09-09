# Book Intelligence Engine — v0.2

M1–M8 architecture + **M2 working PDF ingestion layer**.

## Current pipeline

`PDF → provenance-preserving document blocks → UBR-ready JSON`

The next integration layer is M3: semantic extraction using a multimodal LLM,
strict JSON schemas, retrieval, and source-grounded validation.

## Principle

Never let an LLM replace the original source representation. Raw pages/blocks
remain the immutable evidence layer; UBR is a derived layer.
