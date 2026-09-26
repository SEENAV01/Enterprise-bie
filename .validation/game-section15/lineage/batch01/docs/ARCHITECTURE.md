# GAME DSL/Core Architecture

`GameDocument` is the root immutable contract. Each experience owns levels; each level composes typed state, interaction rules, semantic visual/motion/camera intent, audio cues, adaptation rules and learning challenges. Learning decisions carry hashed source/reasoning/objective provenance.

The contract deliberately separates **what the learner should experience** from **how a downstream runtime renders it**. That prevents the compiler from collapsing rich semantics into a generic slide template. Dynamic experiences are not valid without semantic motion. Core experiences cannot be reference-card/quiz-only. Drag/adjust/place actions require keyboard-equivalent accessibility. Camera/motion cues require explicit pedagogical purpose.

Expressions use a closed AST; arbitrary Python/JavaScript execution is not permitted. Wire serialization uses tagged strict dataclasses/enums and rejects unknown fields/types. Legacy v1 can be inspected read-only, but automatic migration to v2 is blocked because v1 does not contain enough information to truthfully invent studio-grade visual, motion, accessibility and provenance semantics.
