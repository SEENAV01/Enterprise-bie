# BIE v0.6 — M6 Lesson Architect

M6 converts the verified learning graph into a structured lesson plan.

Core behavior:
- prerequisite-safe ordering
- importance/difficulty-aware ordering
- objectives
- prerequisites
- teaching sequence
- application insertion
- assessment hooks
- mastery criteria
- cycle protection

This is the deterministic planner foundation. Production M6 should add model-based pedagogical strategy selection, age/level adaptation, duration optimization, misconception targeting, and evaluator feedback loops.

Run: `pytest -q`
