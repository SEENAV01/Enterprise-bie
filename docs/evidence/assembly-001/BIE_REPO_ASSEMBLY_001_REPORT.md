# BIE Repository Assembly 001 — Lossless Inventory

Status: IMPLEMENTED, not ACCEPTED.

## Inventory
- Atomic ZIP archives discovered: **273**
- Files discovered inside archives: **2450**
- Categories: {"document_intelligence": 83, "game_engine": 1, "governance": 2, "infrastructure": 73, "knowledge_intelligence": 81, "model_gateway": 30, "qa": 1, "reasoning": 1, "scene_ir": 1}

## Lossless migration invariant
No discovered file may disappear silently. Every file must end in exactly one state:
`MIGRATED`, `ARCHIVED_EVIDENCE`, `DUPLICATE_WITH_PROVENANCE`, or `EXCLUDED_WITH_REASON`.

## What this task does
This task inventories the current `/mnt/data` BIE ZIP corpus, hashes every archive and every contained file,
checks presence of implementation/test/evidence material, and creates the source-of-truth migration manifest.

## What it does not claim
It does not claim that all source files have already been consolidated into canonical production modules.
That happens in later repository-assembly tasks, followed by import normalization and integrated test execution.
