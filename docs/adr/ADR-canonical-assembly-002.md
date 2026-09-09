# ADR: Canonical assembly of the existing BIE repository

Status: implemented. Authority: the user's explicit canonical continuation instruction. This supersedes the old working location `app/bie/`, not the product architecture or roadmap.

The restored Git tree exactly matched commit `8b979a46c6e4518908c3fe4d3828b87d10a1b8b0`. Its 766 archives, 12,259 members and 1,431 tests were verified before migration. Thirty later Reasoning ZIPs added 180 historical files and 120 regressions. No source was reconstructed.

## Namespace mappings

| Former namespace | Canonical namespace |
| --- | --- |
| app.bie.enterprise | bie.infrastructure |
| app.bie.book_intelligence | bie.document_intelligence |
| app.bie.game_ir | bie.game_engine |
| app.bie.other_module | bie.same_module |

`bie_core`, `notation_intelligence`, `misconception_intelligence` and `readiness_intelligence` remain additional namespaces. Empty target directories reserve the approved locations; they are not implementation claims.

## Decisions

1. Preserve all snapshots and archives. The ledger has 824 MIGRATED, 389 DUPLICATE_WITH_PROVENANCE and 11,226 ARCHIVED_EVIDENCE rows; zero exclusions. Archival is not production integration. Original bytecode remains in ZIP evidence only.
2. Retain the three richer-source resolutions in `manifests/source_conflicts.json` and prior retry/test corrections in `manifests/assembly_changes.json`.
3. Normalize import statements without altering string literals. Explicitly map the ambiguous bare `equation_semantics` test import to its original Knowledge implementation. Preserve its original test in the snapshot.
4. Canonical and supported `app.bie.*` compatibility imports share module identities. Historical folders never enter the integrated runner's import path.
5. Preserve existing decision and artifact contracts. New inference results adapt to them with evidence resolution and explicit downstream decision types.
6. Do not promote historical acceptance claims. Current task records remain IMPLEMENTED/accepted=false.

## Reproducibility and limits

The three supplied inputs remain byte-for-byte in `docs/evidence/assembly-001/`. Independent checks reopen every archive, verify every member and destination, and reconcile all 2,450 supplied rows. Ingestion rejects unsafe paths, conflicts and unclassified ZIPs before integration; classification does not execute archive code.

The older M-series remains archived pending characterization and governed integration. Production web/API composition, diverse real-book benchmarks, actual video render, playable-game QA and governed cumulative learning are not established by this change.
