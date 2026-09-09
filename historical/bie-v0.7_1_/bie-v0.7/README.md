# BIE v0.7 — M7 Scene Intelligence + Remotion Compiler

M7 converts a structured lesson into a deterministic Scene DSL and then into a Remotion intermediate representation.

Principles:
- AI plans *what* should be shown, not arbitrary React implementation.
- Visual strategy is selected from a reusable scene library.
- Every scene retains content/source references.
- Timing is frame-based for deterministic Remotion rendering.
- The compiler emits an intermediate `BIEScene` representation suitable for a real Remotion component registry.

Visual mappings include definitions, processes, mechanisms, causal diagrams, derivations, comparisons, timelines, charts, simulations, applications, questions and summaries.

The next production step is the Remotion renderer: implement reusable React components for each visual type, audio/narration timing, asset loading, transitions, validation, and final MP4 rendering.
