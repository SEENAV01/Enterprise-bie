# Section 16 Batch 002 — Source evidence evaluators

## Original registry and authority

Original page 17: BIE-QA-SOURCE-001, “source grounding evaluator”; BIE-QA-SOURCE-002,
“citation/provenance evaluator”. The API and limits below are implementation choices
under those titles, not text claimed to appear in the registry. Original workflow:
section batches, completeness audit, justified hardening, re-audit, governed integration;
implementation completion is not real-book product acceptance.

The user explicitly assigned Section 15 to another work session. This package develops
Section 16 in parallel. It does not merge, modify or reassess Section 15. It does not
resume Codex Task028 or change Android/global task-registry files.

## Scope and non-goals

This is an additive `bie.qa.source_v2` implementation, using Batch001's immutable
artifact/candidate/evidence contracts. Source bytes, extracted blocks, quoted spans,
claim spans, output revisions, current assessments and operator scope are checked.

This is NOT a deployed natural-language factual judge, a PDF/OCR engine, a renderer,
a game runtime, or a production release certifier. A CHECKS_PASSED result describes
this declared text-surface check. It is never a claim of complete cinematic quality,
mathematical truth, learner understanding, complete source coverage, or product acceptance.

## Task 001 — source grounding

Each claim must refer to actual output text, cover whole lexical-token boundaries,
and resolve every citation. Even an exact quotation requires a current contextual
assessment: a source may be quoting a misconception, making a conditional statement,
or discussing a counterexample. Exact bytes do not establish entailment.

FACT requires an authenticated SUPPORTED assessment; other labels require an
explicit NO_FACTUAL_ASSERTION assessment. Labels alone cannot hide facts. A reported
contradiction blocks, uncertainty/insufficient confidence requires review. Contextual
support cannot replace missing extraction evidence. There is no keyword similarity,
normalized quote shortcut, or legacy grounded=True promotion.

An operator-provisioned HMAC assessment binds the full request, policy, subject,
purpose, verdict, confidence, rationale, evaluator/version, key, and validity interval.
The full surrounding block text is part of that request identity. Keys are not accepted
from input JSON. Revoked, mismatched, foreign, duplicate, stale, future, expired,
unauthorized or invalidly signed assessments cannot pass. Test-only keys cannot
provide operational support. HMAC authenticates an assertion; it does not prove the
assertion is correct, independent, or calibrated.

Default confidence floors are 900,000/1,000,000. These are explicit policy settings,
not measured 90% accuracy. They require later benchmark calibration. Stronger floors
are supported; weakening below these defaults is rejected by the current contract.

## Task 002 — citation/provenance

Reference chain: source artifact ID/hash -> extracted block ID/hash/page/region/box ->
exact citation offsets/quotation -> exact output claim offsets -> output artifact ID/hash.
Every link is evaluated, including unused/malformed citations; one good citation cannot
hide another broken reference. Direct and aggregate content limits apply.

The UTF-8 adapter requires one complete, unchanged source block and compares it to
actual decoded bytes. Whitespace/case are never silently normalized. Other formats
require an authorized extraction assessment; PDF/ZIP header checks are merely basic
sanity checks, not parsing or extraction accuracy checks.

Output scope is operator-owned and must match exactly. Coverage is the union of valid
spans over all non-whitespace Unicode code points. Overlapping claims cannot inflate
coverage. Punctuation is included; layout whitespace is excluded. Letter/mark/number
boundaries prevent partial-word coverage, including combining marks. No claim is made
that these lexical boundaries implement all linguistic segmentation systems.

Supported declared channels: narration, caption, on_screen, game_feedback, game_prompt,
lesson. This does not verify their presence in the final rendered media or executable game.

## Storage and trust boundaries

SnapshotStore confines reads beneath an opened operator-owned directory descriptor.
It checks relative paths, regular files, no hardlinks/symlink traversal below that root,
actual length/hash and before/after metadata on the same file descriptor. Verified bytes
are returned directly, avoiding a separate hash-check-then-reopen step. Unsupported
secure POSIX APIs fail closed. The supplied root and its provisioning are trusted
operator configuration; immutable publication storage is still required.

Maximums: 16 MiB per artifact snapshot, 64 MiB aggregate referenced snapshots;
1,000,000 code points per text field; 8,000,000 aggregate block/claim/quote characters;
4,096 records per collection; 128 citations per claim; 16 MiB wire JSON. Cross-field
constraints are enforced in Python. The JSON Schema expresses wire shape only.
No throughput or large-book capacity acceptance is inferred from these bounds.

## Public API

- `evaluate(request, root, policy, assessments=(), verifier=None, as_of=N)` returns both reports.
- `evaluate_provenance` / `evaluate_grounding` return the named report.
- `verify_reports(actual, ...)` recomputes against current bytes/configuration.
- `block_from_bi(...)` consumes actual canonical TextBlock/Anchor types.
- `claim_from_ki(...)` consumes actual extract()/bind() records with explicit anchor mapping.
- `prepare_release_evidence(...)` recomputes reports and binds source/output references
  against a ReleaseCandidate, returning unsigned GateEvidence plus exact report bytes.

`CHECKS_PASSED` / `REVIEW_REQUIRED` / `BLOCKED` are derived from findings. Report fields
include request/policy/evidence identity, evaluation time, inspected IDs, measurements,
findings with repair ownership and limitations. `product_accepted` is always false.
Only the runtime's provisioned assessor can attest judgments. Input exceptions are
ContractError, never an alternate successful result.

## Release bridge

The bridge checks candidate digest/run/revision, exact candidate artifact references
and complete candidate source inventory. It does not claim every support artifact is
an output: the operator must declare the complete relevant output surface scope.
CHECKS_PASSED maps to PASS; REVIEW_REQUIRED maps to NOT_RUN; BLOCKED maps to FAIL.
Envelopes remain UNSIGNED. No key is embedded or auto-generated. The bridge does not
write reports or sign/release them. The real release worker must persist/recheck bytes,
apply its own release policy and attest only legitimate operational evidence.

## Verification categories

Synthetic positive/negative fixtures, exact canonical producer compatibility, signed
fixture simulations, byte-tamper checks, Unicode/interval properties, confined filesystem
negative tests, CLI replay, preserved Batch001 and original release-contract regression,
unsigned release consumer integration, and eight selected fault-injection probes.
Synthetic operator_managed keys in tests simulate provisioning only. Those tests do
not constitute execution of a real semantic or extraction assessor. The PDF-shaped
contract fixture deliberately does not stand in for native PDF execution.

## Outstanding integration obligations

Real BI PDF/OCR/multimodal producer execution and source-location QA; rich Director
consumer migration and whole-repository regression; calibrated model/human semantic
assessors using the existing MODEL gateway; live worker identity/secret deployment;
source-to-rendered-video/game surface inventory; real-book coverage/benchmarks;
publication immutability/reverification; performance/platform/security matrix; final
Section16 completeness audit, hardening, repair and certification tasks. All remain
explicitly open. Their absence is not replaced by local test PASS counts.
