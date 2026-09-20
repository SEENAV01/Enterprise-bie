# BIE VIS REP Rebuild 001 — REP-001…008

All eight original VIS REP tasks have been rebuilt as governed replacement artifacts.

- BIE-VIS-REP-001: Representation candidate generation — 20 tests PASS
- BIE-VIS-REP-002: Representation fitness scoring — 10 tests PASS
- BIE-VIS-REP-003: Diagram vs simulation decision — 18 tests PASS
- BIE-VIS-REP-004: Map decision — 10 tests PASS
- BIE-VIS-REP-005: Timeline decision — 10 tests PASS
- BIE-VIS-REP-006: Graph decision — 12 tests PASS
- BIE-VIS-REP-007: Equation visual decision — 10 tests PASS
- BIE-VIS-REP-008: 2D/3D decision and composed representation planning — 35 tests PASS

Integrated REP regression: **125/125 PASS**, failures/errors/skips = 0/0/0. Every atomic ZIP passes fresh extraction.

These ZIPs intentionally use the original names/task IDs for future replacement, but their SHA-256 values are new. During canonical VIS integration, the active REP hash lineage must be changed from the old hashes to the rebuilt hashes in `REP_REPLACEMENT_LINEAGE.json`; do not try to satisfy the historical H5 hash gate with rebuilt bytes.

Status: **REBUILT REPLACEMENT IMPLEMENTED — NOT ACCEPTED**.
