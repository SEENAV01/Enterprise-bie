# BIE v1.8 — Layout-Aware Book Ingestion

M12 adds a document IR for real textbooks:
pages, headings, paragraphs, tables, figures, equations, reading order, bounding boxes, and chapter hierarchy.

Run:
`python src/pipeline.py examples/document-ir.json examples/output.json`

This is the ingestion/structure layer. It does not yet perform model-based visual interpretation of every asset; M13 connects this IR to the LLM extraction engine.
