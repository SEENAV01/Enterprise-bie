# BIE v1.4 — Production Intelligence / M8

This milestone adds the production control layer:
- source-grounded QC
- explicit ambiguity/review handling
- dependency graph
- adaptive routing
- render manifest
- final-gate logic

The Electricity & Magnetism lesson is carried forward as the reference dataset.

Run QC:
`python engine/qc.py examples/electricity-magnetism.production.json`

Generate render jobs:
`python engine/render_manifest.py examples/electricity-magnetism.production.json render-jobs.json`

Run tests:
`python -m pytest`

Important: this package does not claim that external factual verification has been performed. External research is a separate mode and must be explicitly requested/configured.
