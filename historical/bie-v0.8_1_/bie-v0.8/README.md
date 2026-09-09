# BIE v0.8 — M8 Game Intelligence + Game DSL

M8 converts verified learning targets into interactive game specifications.

Supported game modes:
- MCQ
- matching
- ordering
- drag/drop
- prediction
- simulation
- graph interpretation
- derivation ordering
- cause/effect
- fill-gap
- error detection
- concept maps
- adaptive quizzes

The planner selects a mechanic based on the knowledge type, retains source references, requires unambiguous answers, and exposes a mastery/adaptation contract.

Adaptive behavior:
- strong recent performance → increase difficulty
- weak performance → reduce difficulty and review prerequisites

The compiler emits a runtime-neutral `BIEGameRuntime` representation so the game engine remains separate from the AI planner.

Next step after M8: integrate M1–M8 into one end-to-end BIE pipeline and add the real external-evidence retrieval/verification, multimodal PDF ingestion, model calls, Remotion renderer, and game runtime.
