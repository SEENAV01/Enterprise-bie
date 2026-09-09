# BIE v0.4 — M4 Knowledge + Learning Graph

M4 expands the book graph into four layers:

1. **Internal Knowledge Graph** — relationships supported by the book.
2. **Backward Prerequisite Frontier** — knowledge outside the book needed to understand it.
3. **Forward Knowledge Frontier** — higher-level, extended, modern or research knowledge that builds on the book.
4. **Application Frontier** — verified real-world applications.

Every external node must carry provenance/evidence. External knowledge is explicitly marked and is never silently treated as book content.

## Learning graph

`PREREQUISITE_OF` edges are used to compute a topological learning order. Cycles are detected and rejected.

## Research grounding

Graph-based educational RAG is an active research direction. Recent work combines educational knowledge graphs with RAG to support concept understanding and question generation, while LLM-assisted KG completion has been explored for curriculum/domain modelling and personalized learning paths.

## Run

```bash
python -m pytest -q
```

This release is the M4 data/algorithm foundation. The next production layer is the **external frontier discovery pipeline**: retrieval → candidate generation → source verification → evidence scoring → graph merge.
