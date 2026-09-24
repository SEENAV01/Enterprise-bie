# BIE-AUDIO-H11-001 — deterministic future-receipt regression clock

## Authority
Residual hardening derived from mandatory AUDIO final regression; not an original roadmap task.

## Defect
The H5 signed-executor test for a future-issued receipt used the live wall clock. In a long section regression the +120 s mutation could become non-future before H5-003 executed, producing an order-dependent false failure.

## Correction
Capture the original receipt `issued_at` as an explicit verification clock, then mutate `issued_at`/`expires_at` by +120 s and verify at the captured clock. The production verification implementation is unchanged.

## Acceptance
- focused H5-003: 25/25 pass;
- complete AUDIO: 1,684/1,684 pass, 82 modules, zero failures/errors/skips;
- no production AUDIO source changed;
- no reduction of skew/expiry policy;
- product acceptance remains false.
