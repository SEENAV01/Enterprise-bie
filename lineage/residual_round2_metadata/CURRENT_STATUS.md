# Section 15 GAME — audit repair round 2

The two newly supplied BIE_AUDIO_HARDENING_H6 ZIPs are Section **14 AUDIO**, confirmed by their internal continuation record (`section_number: 14`, `latest_implemented: BIE-AUDIO-H6-005`). All 685 integrated manifest entries match, both ZIP CRC checks pass, and the nested integrated ZIP in the master backup matches the supplied integrated ZIP byte-for-byte. They contain no `bie/game_engine/` source and do not replace the recovered Section 15 candidate.

Section 15 work continued from its existing verified GAME checkpoint. This revision fixes generated rule/adaptation name collisions across levels and between punctuation-distinct IDs, and rejects numeric-string arithmetic effects instead of silently converting them. Before-images and all three initially failing regression cases are preserved. The repairs join the previous challenge-outcome scoring and state-transaction repairs.

Fresh local verification: **567 tests passed** (544 inherited portable checks, 13 H7 property/integrity checks, 10 emitted-TypeScript/Node runtime regression checks). There were zero failures, errors, or skips in this local gate. The earlier H6 candidate separately passed 1,062 Linux tests; that count does not claim Linux verification of this changed revision.

This is a cumulative recovery ZIP, **not a completed Section 15 release or canonical integration**. The current source is `bie/`, with `tests/` and `scripts/`. Earlier README/continuation/evidence files describe historical checkpoints; `CURRENT_STATUS.md` and root `CONTINUATION.json` govern the current state. No original archive, prior delivered ZIP, canonical repository source, Android work, or Task 028 was overwritten.

Next: complete the remaining specification/registry audit and consumer checks, address proven residual findings, run the revised full Linux and real-browser/deployed-origin gates, and only then produce the final section exit package and governed GitHub integration. Sections 16–18 follow the same process; Task 028 remains paused until their integrations are complete.

The previous 18-file H7 public validation upload remains unpublished: automatic approval review rejected it and requested explicit authorization for that payload/destination. The isolated CI security setup itself was already approved. This local revision does not retry or bypass the rejected upload.
