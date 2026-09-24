# AUDIO consolidated capability audit 001

## Verdict
**AUDIO: COMPONENT IMPLEMENTATIONS PRESENT THROUGH QA-005 — HARDENING REQUIRED — NOT ACCEPTED.**

This is a consolidated current-source audit, not a new full audit after each hardening batch. It is based on the exact restored Batch 004 plus this newly completed original QA continuation. It does not claim to recover an unavailable earlier hardening ledger.

All 25 original task IDs now have source/test coverage under recorded bounded contracts. This is NOT proof that every original capability meets the envisioned production requirement. In particular, the pronunciation QA implementation provides a source-bound review queue and reported-observation handling, not an independently authenticated phonetic evaluator. Technical sample outcomes are REVIEW, not overall PASS. The absence of a falsely green receipt is useful safety behavior but is not implementation of the missing evaluator.

## Finite implementation/integration backlog

### AUDIO-AUDIT-001-F01 — AUDIO VO/SYNC

**Requirement:** Production-quality cinematic speech without replacing the existing provider-neutral architecture or silently downgrading voice.

**Observed:** Only executable eSpeak and timed-eSpeak local technical adapters are present. Provider-neutral contracts and deterministic voice selection exist; a production neural provider implementation/capability adoption is not present.

**Evidence:** `bie/audio/espeak_provider.py`, `bie/audio/timed_espeak_provider.py`, `bie/audio/tts_generation.py`, `bie/audio/voice_selection.py`, `docs/audio/BATCH004_GAP_LEDGER.json`

**Closure:** Adopt at least one real production-quality provider through existing contracts, with explicit voice/model/settings identity, pronunciation capability negotiation, cancellation, time/output bounds and rights/usage provenance. Feed the same byte-verified speech outputs through cache, SYNC and MIX without silent capability loss. Preserve local technical providers for explicit diagnostics. Live provider execution evidence and independent representative listening remain distinct from offline contract tests; missing credentials are a separate execution blocker, not proof of implementation.

### AUDIO-AUDIT-001-F02 — AUDIO QA/SYNC

**Requirement:** Pronunciation and word alignment must be assessed against actual delivered sound, not only expected text, same-engine events or caller claims.

**Observed:** Current QA-001 provides exact media/source-bound review targets and processes reported observations. It intentionally never declares phonetic correctness. SYNC uses public eSpeak marker timing; independent phonetic offsets/forced alignment and authenticated evaluator evidence are not implemented here.

**Evidence:** `bie/audio/qa_pronunciation.py`, `bie/audio/qa_contract.py`, `bie/audio/word_timestamps.py`, `bie/audio/qa_sync.py`, `docs/audio/BATCH005_NATIVE_QA_SUMMARY.json`

**Closure:** Implement independent acoustic/alignment evaluation against current WAV, expected readings and exact source spans, with model/provider identity and uncertainty. ASR lexical match alone cannot prove pronunciation. Validate evaluator provenance/authenticity and bind all reports to current audio, pronunciation, voice, policy and timeline. Rehashed caller JSON must not authorize acceptance. Produce owned repair requests for actual failures and recheck resynthesized media without changing source content. Calibrate acoustic/listening thresholds on held-out evidence before acceptance.

### AUDIO-AUDIT-001-F03 — AUDIO / existing INFRA

**Requirement:** Deployable, bounded native execution and durable source/evidence/cache lifecycle using existing BIE infrastructure.

**Observed:** Current standalone scripts use bounded local subprocesses, filesystem publication and local cache/locks. No adoption of the canonical kernel worker, durable artifact catalog and governed job lifecycle is included in this AUDIO workspace.

**Evidence:** `bie/audio/espeak_provider.py`, `bie/audio/timed_espeak_provider.py`, `bie/audio/mix_meter.py`, `bie/audio/tts_cache.py`, `bie/audio/qa_io.py`, `docs/audio/BATCH004_GAP_LEDGER.json`

**Closure:** Integrate current AUDIO native calls with the existing approved execution/secret/network/resource policy; do not introduce an unrelated second orchestrator. Use canonical durable artifact/evidence storage and verified cache identities with interruption/retry/recovery/concurrency tests. Hashes alone do not establish publisher/evaluator authenticity. Use bounded scene/segment jobs for long books with preserved ordering and no truncation; distinguish production deployment evidence from local fixtures.

### AUDIO-AUDIT-001-F04 — AUDIO / DIR / ANI / COMP / QA

**Requirement:** Real lectures consume generated narration, mixed waveform, speech/display/sound captions and derived sample/frame clocks through existing production contracts.

**Observed:** Standalone source-to-mix-to-QA CLI works. Current technical preview is not adoption into canonical DIR artifact results or production ANI/COMP media/audio consumers, and no real Remotion rendering has been run.

**Evidence:** `bie/audio/dir_sync_adapter.py`, `bie/audio/mix_clock.py`, `bie/audio/qa_accessibility.py`, `scripts/audio_qa.py`, `docs/audio/BATCH004_GAP_LEDGER.json`

**Closure:** Implement actual canonical adapters for realized DIR narration and downstream COMP media/timeline/animation/caption contracts, retaining source identity and invalidation. No manual recreation of a representative Scene IR may substitute for adoption. Ensure QA findings map to owning stage and repaired media invalidates every dependent clock/caption/render receipt. Do not weaken fail-closed release rules. Run pinned generated-project compile/discovery/smoke/full render and inspect actual video/audio/captions on an approved browser runtime. Reopen COMP only for a reproduced defect.

## Acceptance and process

The production neural adapter, independent acoustic evaluation and production handoffs are real missing implementation/integration work, not merely cosmetic test evidence. Credentials, approved execution hosts and real provider runs may separately block validation. Missing evidence must not be relabelled PASS; a synthetic implementation test cannot certify pronunciation, rendering or learner outcomes.

After these findings are addressed in traceable batches, run one full re-audit. If it exposes another material requirement-linked defect, record and fix it. Do not expand the section merely to increase task counts. No numbered prior AUDIO-H1/H2 continuation is assumed, and COMP is not restarted.

AUDIO GitHub integration remains prohibited until the agreed section-exit decision. The five pinned DIR dependency files are used only as the documented standalone exact-source fixture; full deployed DIR/INFRA/ANI/COMP execution is a different gate. No full 6,485-test enterprise regression, live neural provider, independent listening or Remotion render was executed in this continuation.
