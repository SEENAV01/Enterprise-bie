# Section 15 GAME — audit round 3

This cumulative checkpoint adds verified expression-codegen repairs and a real generated-code consumer check for the reviewed legacy migration subset. It is not a final section release or canonical integration.

Six new differential tests first failed against the previous source. The failures included invalid subtraction syntax for negative literals, dynamic division by zero silently producing JavaScript Infinity, eager/short-circuit error differences, numeric enum values being converted to strings, Boolean/numeric equality differences, and invalid mixed arithmetic being emitted. The codegen repairs retain authoritative semantics for the tested cases. All 512 seeded numeric expression trees and the minimized cases now compile with strict TypeScript and execute under Node.

A reviewed legacy fixture now also passes through the migration, actual compiler and emitted runtime. Expected state, score and feedback are verified while the original legacy wire remains unchanged. This verifies one supported migration path; it does not prove arbitrary legacy semantic equivalence or real-book acceptance.

Fresh local gate: **574 tests passed** — 544 inherited portable tests, 13 H7 property/integrity tests, 11 generated-runtime regression checks, and 6 differential expression tests. Zero failures, errors or skips in this local gate. The earlier H6 candidate's 1,062 Linux passes remain historical evidence for that exact candidate; the changed source still needs Linux/browser verification.

Previous source bytes, initially failing counterexamples, current logs, source amendments, source inventory and continuation records are included. Root `CURRENT_STATUS.md` and `CONTINUATION.json` supersede earlier checkpoint narratives. No previously delivered ZIP was overwritten.

Remaining: finish action/challenge/input routing audit and the full specification/registry re-audit; repair concrete findings; run revised Linux and real-browser/deployed-origin gates; then produce the section exit deliverables, complete governed GitHub integration, full enterprise regression, merge/readback and repository backups. Sections 16–18 follow, and only then Task 028 resumes.

The earlier H7 public validation upload is still unpublished: automatic approval review required explicit authorization for that payload/destination. The isolated CI security setup was already approved. This checkpoint does not retry or bypass the rejected upload. No canonical GAME adoption or main-branch merge has occurred.
