# BIE-QA-HARD-007 — Native document-to-QA provenance adapter

## Original audit requirement
Consume actual BI PDF/EPUB/scanned extraction outputs, rich page/region anchors and normalization maps in source QA; reuse native ingestion.

## Implemented local scope
Actual native PDFInventory ingestion through the preserved pypdf adapter, PyMuPDF page/region extraction, full-page pixel hashes and deterministic raster crops. Identity normalization retains text. Existing Anchor/TextBlock and Source/Block contracts are actually constructed. Verification reopens source bytes; no submitted native-success flag is credited.

## Executed / tested behavior
- Text PDF reaches byte and region checks; one image-only page reaches one successful OCR diagnostic and retains review-required recognition.
- Rehashed lost qualifiers, modified page/region pixels and reordered text are rejected; arbitrary figure/table meaning is reviewed.
- Page/text/pixel/byte limits fail without truncation.

## Required closure still open
- EPUB and arbitrary multilingual/multicolumn/native extraction provider coverage remain open.
- OCR meaning and reading order require independent assessment. These authored PDFs are not a real-book E2E run.
- Production parser isolation and canonical caller migration remain open.

This task has a local adapter/interface implementation, not full operational closure. Source files and old evaluations are never rewritten to create a pass. No release is authorized. Read the shared execution receipts; do not multiply shared test counts by five.
