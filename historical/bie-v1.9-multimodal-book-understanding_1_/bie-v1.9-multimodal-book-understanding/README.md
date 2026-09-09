# BIE v1.9 — Multimodal Book Understanding

M13 adds the multimodal model boundary:
document text + figures + tables + equations + provenance.

Run:
`python src/pipeline.py examples/document.json examples/output.json`

The package prepares structured multimodal evidence. It intentionally does not fake visual interpretation when the actual asset bytes are unavailable.
