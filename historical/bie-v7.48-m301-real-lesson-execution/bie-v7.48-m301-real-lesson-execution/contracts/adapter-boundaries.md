# Adapter Boundaries

M278 deliberately keeps the canonical pipeline independent of vendors.

## Replaceable production adapters

- Source adapter → PDF/EPUB/scan ingestion
- Understanding adapter → layout-aware document understanding
- Knowledge adapter → retrieval + graph construction
- Planning adapter → pedagogical planner
- Script adapter → LLM-backed script generation
- Scene adapter → Scene DSL compiler
- Remotion adapter → deterministic TypeScript/React generation
- Render adapter → Remotion CLI/server rendering
- QA adapter → visual/audio/content regression
- Publish adapter → artifact storage and delivery

The orchestration spine remains stable while implementations behind these boundaries improve.
