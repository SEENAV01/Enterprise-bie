# Batch 005 targeted audit and preserved development attempts

This is an implementation-batch review, not the full Section 16 completeness audit.

## Issues addressed before delivery

1. Domain preservation: recompute the original numerical reference as well as the candidate.
   A cancelled expression cannot hide a denominator that was undefined at the reference input.
2. Native parser boundary: the pinned native parser for tokens x * y + z can return a tree
   that omits + z. The additive adapter now requires original text and rejects a mismatch
   against the strict parser. Native bytes are unchanged; canonical producer repair remains open.
3. Rational square roots: detect a perfect numerator/denominator square exactly (for example
   sqrt(4/9)=2/3), rather than replacing it unnecessarily with a decimal enclosure.
4. Release boundary: healthy text evidence stays NOT_RUN for the complete mathematical gate.
   Missing assessor authority is review-required, while a failed computation blocks. No signature
   or caller-provided pass can waive the actual calculation or downstream media evidence.

## Executed attempts retained

- development_005/INITIAL_TEST_RUN.txt: 127 methods; one error and one failure. An exponent-tower
  test expected syntax outside the deliberate literal-power grammar; the test now expects
  rejection. A sqrt endpoint assertion used noncanonical fraction formatting; exact perfect-square
  handling and its rational-result expectation were improved. This attempt is not reported as pass.
- development_005/EXPANDED_TEST_RUN_1.txt: 226 methods; one failing assertion expected BLOCKED
  for healthy but unsigned input. The intended contract is REVIEW_REQUIRED; the test/CLI expectation
  was corrected. Release is still BLOCKED. No safety threshold was weakened to obtain a pass.
- development_005/EXPANDED_TEST_RUN_2.txt: 276 methods, all passed.
- executed_run_005/TEST_RESULT.json: final cumulative source/test-hashed execution, 276 new tests,
  444 contained subcases; all preserved batches pass separately.
- mutation_probes_005/MUTATION_RESULT.json: all 17 selected missing-safeguard mutants detected
  by assertion failures, every original control passing; main source tree not modified.
- demo_005/DEMO_RESULT.json: actual offline CLI and release-evaluator execution. Unsigned math
  REVIEW_REQUIRED; actual-media gate NOT_RUN; complete release BLOCKED, as required.

## Material limitations carried forward

This implementation does not parse arbitrary textbook LaTeX/math OCR, infer correct variable
meaning, perform general symbolic solving/calculus/linear algebra, validate empirical laws,
create independent reference inventories, calibrate assessor quality or verify actual rendered
math. Explicit user/operator scopes, bounds and references require real grounded assessment.
The native truncation counterexample is verified against the pinned snapshot only; a later HEAD
may differ and must be inspected during integration. Native parser code was not silently patched.

Unit checking distinguishes the shipped temperature/angle cases but is not a full semantic
quantity-kind algebra. Products can require additional context. Dimensional homogeneity alone
cannot certify a law. Numerical interval dependency overestimation can force review. An unsupported
proof remains unknown; extra coverage must be added via governed adapters and counterexample tests.
Lessons with no mathematics need a future explicit reviewed applicability policy instead of an
empty-category pass. Worker process isolation, performance, portability, real assessor operation,
canonical migration and product E2E remain open.

No Section 15 code or global task state is touched; no GitHub write is performed. The archive
is a continuation package, not a replacement repository or full product acceptance evidence.
