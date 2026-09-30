# Section 17 R1 controlled adoption review

This is a source-integration candidate, not Section 17 sign-off or product
acceptance. Task 028 remains paused; Section 18 is unchanged.

- Canonical comparison main: `8b8e500bf7b83addfcecce41c3fca08563eceb41`.
  This main includes the Section 16 QA implementation merge, but its own
  recovery ledger still records HARD-039/HARD-040 and operational acceptance
  obligations as open. A merge alone is not Section 16 sign-off.
- Source master: `Section17_R1_Master_RESTORED.zip`, 383,934,041 bytes,
  SHA-256 `03043839a2290672a4b672cbb39952846e77ff99572a791bf0ca89cf14a51f4e`.
  `VERIFY_MASTER.py` verified all 2,517 manifest payload files. The 103
  atomic ZIPs remain in that external master; they were not overlaid on Git.
- Read-only R1 preflight: 2,029 mapped paths; 0 direct collisions, 780 absent
  adoption candidates, 277 identical dependencies, 36 differing dependency
  checkout bytes, 920 historical-only paths, 15 generated caches, and one
  reviewed QA CLI route patch. The JSON plan is retained outside this checkout.
- Of the 36 differing dependencies, 34 normalize exactly to the same LF bytes
  and hashes recorded in the master. The remaining two are the canonical
  Section 16 `bie/infrastructure/__init__.py` and hardened
  `bie/math_intelligence/expression_ast.py`; both are preserved. No native
  dependency file was copied from the master.
- The 780 new files consist of 175 `bie/evaluation/benchmarks` files, 127
  Section 17 test/support files and 478 scoped docs/metadata/tools/examples.
  Each source file was SHA-256 checked against the preflight map before
  copying into an absent target. No `__pycache__` or `.pyc` was adopted.
  `SOURCE_INTEGRATION_MAP.json` and `ADOPTION_AMENDMENTS.json` are retained
  in this directory; `scripts/verify_section17_adoption.py` verifies all
  780 adopted paths, 12 reviewed amendments (two integration adaptations and
  ten EOF-only test formatting fixes), the original CLI route patch,
  and the absence of 15 generated caches. Its local result passed.
- The existing QA lifecycle CLI's Git blob SHA matched the package's stated
  predecessor. The two explicit `eval-api` and `eval-campaign` routes were
  applied by review; the original journal-inspection route remains present.
  The new CLI's LF-normalized SHA-256 matches the package's published
  `7bc0c5b937d14a4918349f377716d213e9447812aac2f8d5f443bda0b7f6ee0e`.
- The canonical `BenchmarkAPI` Git blob matches the package pin. Windows Git
  materializes it with CRLF, so the Section 17 caller accepts only an exact
  CRLF-to-LF reconstruction that still matches both pinned SHA-256 and Git
  blob SHA-1. Altered content remains rejected. The canonical API source is
  not changed.

The canonical integrated gate now runs the adopted Section 17 suite with an
exact 2,023-method census: 2,018 recovered methods plus five new checkout-pin
controls. Missing, duplicate, failed or skipped methods fail closed. The
existing 37 native durable-worker tests are already present byte-identically
in canonical Section 16 tests; they are not counted again as new tests.
Local targeted checks passed: 20/20 Metric 001 methods, 5/5 checkout-pin
methods, and 10/10 adoption/gate-control methods. The inherited preflight
test file has a Windows symlink-privilege setup error (`WinError 1314`), so
its combined local run was not a clean pass; its hosted Linux run remains
required. The complete Section 17/native/browser suite has not yet passed
against this exact repository candidate.

The adopted `native_api.Service` composes the canonical `BenchmarkAPI` with a
fixed PlanRegistry, Campaign and operator-owned Admission registry. Its
operator CLI is a local library/command route, **not** an HTTP service,
distributed authorization, or a general job-host integration. Actual
book-to-native-video/game production and independent full-metric evaluation
remain unexecuted and cannot be inferred from authored fixtures.

Historical master-only gaps are carried forward from the R1 master: exact H3,
H5, Native Campaign and Native API master containers, two old H5 helper
scripts, and other stated fingerprints have not been fabricated or relabelled.
The complete archive and original gap ledger remain in external preservation.

Local Windows verification boundary: the host Git configuration has
`core.autocrlf=true`. `scripts/verify_assembly.py` hashes working-tree bytes
of historical text snapshots, and this Windows checkout materialized CRLF
where the immutable manifest records LF. Its local run therefore reported
historical `Imported source mismatch` errors (for example
`batches/BIE_AST_001/TASK_RESULT.json`), even though `git hash-object` of
that path matches its committed Git blob. Historical files and the verifier
were not altered to make the check pass. The complete preservation gate must
run in the approved Linux checkout and its exact candidate result must be
inspected before PR/merge readiness is claimed.
