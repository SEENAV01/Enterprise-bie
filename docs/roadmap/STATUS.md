# BIE Status

Updated: 19 October 2026 · Read this first in every new session, then show Navin the current task card.

## Now

| Field | Value |
| --- | --- |
| Phase | 0 · Foundation |
| Current task | 037A · Repository memory (`CLAUDE.md`, Vision Spec, roadmap, status) |
| Branch | `task037a-repository-memory` |
| State | In progress |
| Next task | 037B · Fast lane and CI debts (needs Navin's approval of the fast lane) |
| Canonical main | `b3ce527ff102bc3b91942b3d6553e851c61bb6f9` (Task 036 closed) |

## Done

| Date | Task | Result |
| --- | --- | --- |
| 2026-10-19 | 036 · Scene IR producer | Canonical-complete within its bounded scope; PR #29 and #30 merged; exact-main CI green |
| 2026-10-19 | Local work rescue | Director Step 4 and Step 5 pushed as `wip/task036-director-step4` and `wip/task036-director-step5` (not merged) |

## Open decisions for Navin

- [ ] Approve the fast lane (037B)?
- [ ] Who presses merge: Navin on every PR, or Claude once CI is green?
- [ ] Providers for the blind test (Claude, OpenAI, Gemini) and the monthly budget.
- [ ] First book, chapter and class level (ideally a subject Navin teaches).
- [ ] First language: Hindi, English or Hinglish.
- [ ] Narration voices.
- [ ] What the Dhanteras goal becomes (a pilot of a few chapters?).
- [ ] Parked Director Step 4–6 work: finish, rework or drop.
- [ ] Where courses are published first.
- [ ] Meaning of "real video lectures": teacher or avatar on screen, or fully animated.

## Known technical debts

- F-08: Section 18 browser gate flake (`CDP_TIMEOUT:Page.navigate`); until fixed, rule FR-1 allows one recorded rerun per job only for that exact failure.
- M1 `verify` job uses 35m35s of 45 min.
- N-02: Section 18 source-ledger step slowed from 21 s to 612 s.
- Audio reconciliation open (`AUDIO_REPLAN_REQUIRED`); global VIDEO_CODE and later stages not run.
- PR29 follow-ups F-01..F-07 and PR30 follow-ups F1..F5 (low, non-blocking).
