# Phase 2 — Book-to-Video Code Intelligence v1

## New objective

**Input:** an entire book/PDF.

**Output:** the complete video-generation codebase/specification for the book.

This phase deliberately stops before implementation/rendering.

## Pipeline

```text
FULL BOOK
   ↓
DOCUMENT INGESTION
   ↓
STRUCTURE MAP
   ↓
KNOWLEDGE EXTRACTION
   ↓
CONCEPT GRAPH
   ↓
PREREQUISITE GRAPH
   ↓
COURSE ARCHITECTURE
   ↓
LESSON SPECS
   ↓
SCENE SPECS
   ↓
VISUAL SPECS
   ↓
VIDEO CODE ARCHITECTURE
   ↓
REMOTION CODE GENERATION
   ↓
STATIC VALIDATION
   ↓
FULL-BOOK CODE MANIFEST
```

## Key design decision

Do **not** ask an LLM to generate an entire book's video code from one giant prompt.

Instead, maintain a persistent intermediate representation:

`Source → Knowledge → Pedagogy → Scene DSL → Code`

Every downstream object retains provenance to upstream objects.

## Full-book scaling

A book is represented as:

`Book → Chapters → Topics → Concepts → Lessons → Scenes → Code modules`

The planner can therefore process chapters incrementally while retaining the global concept/prerequisite graph.

## Code generation boundary

The output of Phase 2 is code/specification such as:

- `Root.tsx`
- lesson modules
- scene modules
- reusable visual components
- asset manifest
- timing metadata
- narration metadata
- source provenance
- book-level generation manifest

No MP4 is required for Phase 2.

## Static validation before Phase 3

Before handing code to the implementation/render phase:

- schema validation
- missing concept references
- missing scene references
- duplicate IDs
- unresolved prerequisites
- unsupported source claims
- invalid component references
- missing assets
- timing conflicts
- import/dependency validation

Only code that passes these checks is promoted to Phase 3.
