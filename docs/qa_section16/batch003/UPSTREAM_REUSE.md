# Upstream reuse and preservation

Read-only connector inspection used pinned commit
`375d99af0edd0086206817dae932156ddf61c569`, the parent package's anchor. This is NOT
a statement that current HEAD was re-audited or is unchanged.

The five source files in `upstream/SEMANTIC_CONTRACT_PRESERVATION.json` were
reconstructed from the connector's returned full contents after direct container
network retrieval was unavailable. Their Git blob identities, SHA-256 hashes and
lengths were then checked. These are exact preserved upstream bytes, not rewritten
substitutes. The test suite actually imports the KI/RE/DIR modules and exercises
their entry points through explicit adapters.

All 122 inherited Batch002 files are preserved. Six superseded root lane-metadata
files remain exact under `history/batch002`; all other inherited files remain at
their original relative paths. No existing code or test was changed.

Standalone compatibility copies must be VERIFY-ONLY during canonical integration:
never overwrite a newer live repository file from these ZIPs. Section15, global
continuation, Codex/Android work and canonical branches were not modified.
