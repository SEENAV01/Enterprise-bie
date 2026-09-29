# Product vision and parallel-work handoff

The target remains an enterprise Book Intelligence Engine that transforms real
books/PDFs into grounded, complete learning experiences: accurate and understandable
teaching, purposeful cinematic educational videos, and genuinely playable learning
and revision games. It is not a PDF summarizer, text-slide factory or quiz-only app.

Preserved pipeline: document/OCR/provenance → knowledge/concepts → prerequisites
and misconceptions → mathematical and central reasoning → adaptive pedagogy →
lesson/script/narration direction → visual/animation planning → Scene IR → code
compiler → actual compile/render → audio/timing/accessibility → quality evaluation
and governed repair → release. Meaningful learning games share grounded objectives,
concepts and misconceptions instead of becoming disconnected entertainment.

Quality includes correct source grounding, causal/derivation explanation, readable
representations, purposeful 2D/3D motion, narration/visual synchronization, pacing,
feedback, simulations, mastery and transfer. Subject packs, reusable semantic scenes,
concept memory, reusable code, correction memory and measurable cumulative learning
remain part of the wider vision. This release-gate batch does not claim to implement
those systems or certify their quality.

## Work ownership

- Section 16 local QA source/tests/ZIPs: this lane.
- Section 15 GAME completion/hardening/runtime/integration: another user work session.
- Canonical repo/main, existing Codex/Android work and global continuation: unchanged.
- Section 16-dependent GAME evidence: pending until supplied and independently verified.

The user's latest instruction authorizes parallel development. Earlier sequential
handoff language must not be used to block this lane or pull Section 15 work back
into it. Parallel development does not let a missing upstream gate pass.

## Merge discipline

Before any later integration, read the latest repository state and original caller
contracts again; do not assume the inspected commit is still HEAD. Stage only
approved additive changes. Preserve v1 source, original tests, historical ZIPs and
all concurrent work. Conflicts require explicit reconciliation, never force-push or
blind overwrite. The local QA continuation is a lane checkpoint, not a replacement
for `task_registry/continuation.json`.

Implement original tasks in capability-based atomic closures. Reuse existing rich
implementations rather than replacing them with generic stubs. Keep specifications,
negative tests, actual execution logs, provenance, manifests, hashes and recoverable
ZIPs. Then perform full section audit, justified hardening, re-audit, guarded canonical
integration, regression and post-merge readback. Product acceptance still requires
actual real-book, educational video and playable-game evidence.
