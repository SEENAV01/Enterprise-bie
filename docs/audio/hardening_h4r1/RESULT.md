# BIE AUDIO H4 recovery revision R1 — verified delivery

Current source checkpoint: **BIE-AUDIO-H4-R1-005**. Parent: **BIE-AUDIO-H3-005**.
Original H4-005 was documented but its source archive was unavailable. This is
newly implemented, explicitly labelled recovery code, not byte-identical H4 or H5.

## Actual verification
All **1322 AUDIO tests** across **59 test modules** passed
on freshly extracted source in **four disjoint worker processes**: zero failures,
errors or skips. This is the complete AUDIO test inventory, not full-enterprise
regression. It includes the unchanged 1,216 H3 tests and 106
new recovery tests. Every final executable/source/fixture/dependency input is
checked against that fresh-source candidate; final reports are additional metadata.

The five standalone task ZIPs were separately extracted and executed:
**22, 25, 28, 18, 13 tests**, all passing.
Those are repeated subsets of the 1322 total, not extra unique tests.
A separate sequential H3 parent run also passed 1,216/1,216 before this final run.

## Implemented capability
H4-R1-001 pins the existing canonical worker/dependency identities and an
externally approved, bounded Linux/no-proc acoustic profile.
H4-R1-002 executes the fixed acoustic operation through that worker without a
local fallback, with nonce/media/source/result and process/kernel-proof checks.
H4-R1-003 adds a separate Ed25519 v2 receipt, including exact durable-request
fingerprint binding. Legacy v1 alone cannot authorize kernel-verified reuse.
H4-R1-004 extends the unchanged H3 canonical CAS/SQLite/lease chain with a fourth
kernel-evaluation envelope and current-source/trust verification before reuse
or fenced completion. H4-R1-005 adds operational CLI, reverified atomic publication
and actual native/cold-process evidence.

## Actual native evidence
The synthetic English case produced **three measured segments and nine native
search passes** through the isolated worker. A second fresh CLI process reused
the exact stored evidence with **zero new native evaluations**. Source WAV and
exported payload bytes stayed identical. A Hindi case executed the worker but
remained **UNSUPPORTED_LANGUAGE**, with no false English fallback or acceptance.

Ten actual boundary checks passed: declared output writable; engine and input
read-only and unchanged; no access to host canary or host procfs; secret environment
not inherited; external network unavailable; mount syscall denied. Kernel proof
records distinct user/mount/network/PID namespaces. These are bounded fixtures,
not a security certification or hostile-host attestation. Current launcher
resolution matches the selected host profile; production PATH/host-policy gates
remain open.

## Preservation and development corrections
All **450 inherited files** remain accounted for:
**445 unchanged**, **5
metadata files updated with exact originals preserved, **zero deletions**.
All **180 inherited Python files** are
unchanged, including historical Python lineage copies. Eighteen selected canonical
standalone dependencies are identity-verified (ten inherited plus eight worker
modules). These fixtures must not overwrite a newer repository on integration.

The first run exposed two incorrect new test exception expectations; the full
inherited regression caught an import-layering violation; fresh task extraction
caught missing example fixtures in the smaller closures. Each was corrected,
without altering inherited source/tests or relaxing the existing gate. Superseded
failure logs are retained separately from the final passing evidence.

## What remains open
F01 live neural-provider execution and representative independent listening;
F02 production multilingual/accent/IPA/OOV evaluation, ground truth and calibration;
wider F03 TTS/cache/SYNC/MIX/native adoption, paid-call uncertainty, key custody,
production host policy, scheduling/repair/GC/fleet lifecycle; F04 real canonical
DIR-to-AUDIO-to-ANI/COMP handoff, dependent invalidation and actual render.
Real-book E2E, full enterprise regression and product/section acceptance remain
unverified. No real Remotion render, live neural request, production deployment,
GitHub write or separate Codex-track change occurred.

Next: derive the remaining bounded F03/native lifecycle work from the actual
canonical call sites, with F02/F04 retained. Do not repeat H4-R1, treat original H4
as recovered, jump to section acceptance, or overwrite newer Codex/GitHub progress.
