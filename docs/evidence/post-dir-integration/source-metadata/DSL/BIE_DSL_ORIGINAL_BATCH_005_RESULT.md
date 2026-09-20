# BIE DSL Original Batch 005 — INT-001..003

Implemented:
- `BIE-DSL-INT-001` — interaction bindings
- `BIE-DSL-INT-002` — state bindings
- `BIE-DSL-INT-003` — simulation controls

Verification:
- atomic ZIPs: **3/3**
- every atomic ZIP fresh-extraction PASS
- INT atomic tests: **20/20 PASS**
- cumulative DSL regression through CORE + SCHEMA + ELEM + SPACE + TIME + INT: **161/161 PASS**
- failures/errors/skips: **0/0/0**
- atomic ZIP byte identity preserved in Master Backup

Truth boundaries:
- interaction bindings validate targets and handlers;
- state bindings validate declared state paths and target elements;
- simulation controls validate simulation/state identity;
- controls requiring verified runtime behavior cannot bind to conceptual/declared-only simulation output.

Status: **IMPLEMENTED — NOT ACCEPTED**
