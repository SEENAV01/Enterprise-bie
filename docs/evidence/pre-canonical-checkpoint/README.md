# Enterprise BIE

Naveen's Book Intelligence Engine: source-grounded book understanding, prerequisite reasoning, educational video code and interactive revision games.

The repository now preserves **766 original BIE ZIP files** (691 distinct byte contents), expands their source history, and assembles **376 enterprise batches** into one `app/bie` source tree. This is repository recovery and source integration. Full-book production acceptance is still pending.

## Start here

- [Context and continuation](BIE_CONTEXT_HANDOFF.md)
- [Current verified state](docs/bie/CURRENT_STATE.md)
- [Master product specification](docs/bie/BIE_MASTER_SPEC.md)
- [Assembly decisions and fixes](docs/bie/REPOSITORY_ASSEMBLY.md)
- [Archive inventory](manifests/archive_inventory.json)

## Layout

| Path | Contents |
| --- | --- |
| `app/bie/` | Combined enterprise source; current working implementation |
| `tests/imported/` | Working copies of all 374 imported enterprise test files |
| `tests/test_repository_integration.py` | Regression checks for assembly fixes |
| `batches/` | Unmodified source, specifications, task results and test evidence from each enterprise ZIP |
| `historical/` | Preserved earlier BIE versions, M-series modules and product packages |
| `backups/BIE_ORIGINAL_ARCHIVES_2026-09-09.zip` | All 766 original ZIPs, byte-for-byte, including duplicate backup copies |
| `manifests/` | Archive/member checksums, task IDs, duplicate groups and source conflict decisions |
| `validation/` | Results actually produced during this assembly |

Generated cache files are retained inside the original ZIPs and omitted from the expanded source. No original archive, module, specification or task result has been discarded. Imported status claims remain historical evidence and are not automatically promoted to ACCEPTED.

## Local verification

Python 3.12 was used for this assembly. The enterprise checks require only the Python standard library and do not invoke a model provider.

```bash
python3 scripts/verify_assembly.py
python3 scripts/test_enterprise.py
```

Run one batch with `python3 scripts/test_enterprise.py --batch BIE_RE_DEC_001`.

Legacy packages retain their own dependencies and instructions. Their live model calls, renderer builds and full-book acceptance have not been executed by this assembly.

## Delivery rule

Every future completed development batch must update the working source, tests, specification, task registry and continuation checkpoint; commit verified changes to this repository; and deliver a downloadable backup ZIP with the exact commit SHA. An unavailable write must be reported as blocked, never described as uploaded.
