# BIE v0.5 — M5 Verification & Evaluation

M5 is the audit layer between extraction/graph construction and downstream lesson/video/game generation.

It evaluates:
- claim support and confidence
- provenance completeness
- information coverage
- relation accuracy
- evidence coverage for external knowledge
- prerequisite cycles
- PASS / REVIEW / REJECT
- automatic repair actions

Production extension points:
1. retrieval-backed evidence verification
2. model-based entailment/contradiction judging
3. expert adjudication
4. calibrated confidence
5. benchmark-based regression testing

Run: `pytest -q`
