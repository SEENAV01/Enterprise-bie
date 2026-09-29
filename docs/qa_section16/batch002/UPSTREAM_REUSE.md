# Inspected upstream code and preservation

Repository: SEENAV01/Enterprise-bie
Pinned inspection: 375d99af0edd0086206817dae932156ddf61c569
Remote operations in this batch: read only. No branches, PRs, commits or files changed.

## Executed unchanged compatibility dependencies

The following exact files were read through the GitHub connector and reproduced with
matching Git blob SHA-1 identities and SHA-256/length manifests. They are dependency
copies, not newly authored source files to overwrite during integration:

- bie/document_intelligence/source_anchors.py
- bie/document_intelligence/text_blocks.py
- bie/knowledge_intelligence/claim_extraction.py
- bie/knowledge_intelligence/claim_evidence.py

`upstream/SOURCE_CONTRACT_PRESERVATION.json` records exact identities. New tests call
the actual canonical `build`, `extract`, `bind`, and Anchor interfaces. The KI binding's
`grounded=True` is intentionally not counted as contextual support.

## Inspected, not replaced and not executed in this batch

- bie/document_intelligence/real_pdf_text_runtime.py
- bie/director/qa_contract.py
- bie/director/source_grounding_qa.py
- bie/director/factual_script_qa.py

The existing Director path already distinguishes source-byte/citation checks from
contextual factual assessment and requires revision-bound source/script spans. This
batch preserves that separation. It does not overwrite rich Director code or claim
its callers were migrated. The native BI runtime is not reimplemented by a metadata
stand-in; actual PDF/OCR execution remains a declared integration obligation.

## Parent preservation

All Batch001 source, tests, scripts and executed evidence remain byte-identical.
Updated cumulative navigation/continuation/manifest metadata is separately preserved
under history/batch001. The original Batch001 ZIP itself is retained in the Master Backup.
Before repository adoption, compare exact current upstream files rather than applying
this archive as an unconditional overwrite. Re-read latest HEAD because parallel work
may change it after this inspection.
