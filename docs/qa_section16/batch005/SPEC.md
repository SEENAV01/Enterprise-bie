# Section 16 Batch 005 — mathematical QA

## Scope, authority and product boundary

Original 18-section registry, page 17: BIE-QA-MATH-001 formula evaluator;
BIE-QA-MATH-002 derivation evaluator; BIE-QA-MATH-003 numerical evaluator;
BIE-QA-MATH-004 units evaluator. Additive namespace: `bie.qa.math_v2`.
The cumulative archive includes Batches 001–005, not the full BIE repository.
Section 15 is externally managed and is not modified or re-audited here.

BIE's goal remains a grounded, accurate, cinematic and engaging learning experience
with meaningful educational games. These mathematical checks protect formula,
derivation, worked-example and unit correctness. They do not measure cinematic
quality, actual student learning, rendered frames, audio or playable interactions.
Implementation scope is bounded and described below; the four original capabilities
are not claimed to be universally complete or accepted for production.

## Interfaces, evidence and result semantics

`evaluate(request, artifact_root, policy, *, as_of, reviews=(), verifier=None,
source_assessments=(), source_verifier=None)` returns a `MathResult` containing
`source`, `formula`, `derivation`, `numerical`, `units` and mathematical witnesses.
`evaluate_formula`, `evaluate_derivation`, `evaluate_numerical` and `evaluate_units`
select an individual report after evaluating the common contract.
`verify_reports` recomputes the result, rejecting edited or stale records.

Reports bind the request, independent operator policy, evidence, trust configuration,
source/output identities and evaluation time. The earlier source-v2 evaluator is
executed against actual artifact bytes and exact output spans. Claims cannot earn
mathematical acceptance merely from a caller's `passed` field or native diagnostic.

Statuses are CHECKS_PASSED, REVIEW_REQUIRED and BLOCKED. CHECKS_PASSED applies only
to the declared typed/text contract. `product_accepted` is always false. A deterministic
proof witness may be PROVED while the report still requires source/mapping review.
An invalid formal computation blocks regardless of positive signed reviews.
Unknown or unsupported mathematics requires review instead of fabricated proof.

Operator policy separately owns required case IDs/kinds, reference equations,
terminal derivation targets, symbol scope, bounds, nonzero conditions, numeric
inputs/units, tolerances, rounding and minimum steps. Candidate-supplied inventory
cannot silently remove a requirement or replace its reference. A category without
an operator-defined scope is REVIEW_REQUIRED, not an implicit NOT_APPLICABLE pass.

Use the existing reasoning-v2 `Review`, `ReviewKey` and `ReviewVerifier` for inventory,
math mapping and condition-disclosure reviews. These reviews bind the math request
and policy digests, exact evidence IDs, assessor/version, expiry and independent group.
Source assessments use the preserved source-v2 contract. Default verifiers have no
keys. Test-only authority cannot provide operational approval. Authorized rejection,
uncertainty, stale evidence, wrong binding or inadequate independence do not disappear
under a majority vote. Declared independent groups and review correctness still need
real-world governance; authentication does not prove either.

## BIE-QA-MATH-001 — formula evaluator

Strict parser and immutable typed expressions support exact rational constants,
explicit symbols, negation, addition, subtraction, multiplication, division and
bounded literal integer powers. No `eval`, `exec`, `sympify`, Python expression
execution, arbitrary functions, attribute access, indexing or implicit multiplication
is used. Sqrt/abs are supported in numeric intervals; general transcendental symbolic
identities, calculus, vectors, matrices, inequalities and LaTeX remain unsupported.

Use bounded sparse rational-polynomial operations to compare candidate and reference
equations. Proportional residual numerators provide a sufficient zero-set certificate
only after checking original expression domains. This is not a complete equation
solver or a general proof of reference satisfiability. Multiplying by a nonconstant
factor is not silently treated as equivalent. A finite sampled counterexample can
disprove an equation equivalence; passing finite samples never establishes proof.

Original denominators, negative powers and the deliberately conservative 0^0 rule
remain checked before simplification. `x/x` cannot erase the need for x != 0.
Bounds/nonzero assumptions are operator-owned and require distinct, actual condition
spans with an authorized disclosure review. A bounded admissible scope witness is
required to avoid empty-domain certification; failure to find one means review, not
a proof that the scope is impossible. Dimensional homogeneity is also checked.

## BIE-QA-MATH-002 — derivation evaluator

A derivation carries explicit before/after equations, output claim links, operation,
operand and ordered steps. The beginning and endpoint are compared with independent
operator references. Adjacent typed equations must match; representation changes
need an explicit rewrite step. Required explanatory steps cannot be omitted.

Implemented rules: certified rewrite, swapping sides, adding/subtracting an operand
on both sides, multiplying/dividing both sides by a proved nonzero operand, and
squaring both sides only on a branch proved injective by real interval bounds.
One-sided changes fail. Multiplication by zero does not establish equivalence.
Squaring without adequate sign restrictions remains UNKNOWN; introduced/lost roots
are not accepted as a reversible step. Differentiate/substitute are explicit unsupported
rules, not accepted based on a label. Domain and dimension checks are applied at each
step. A correct deduction is conditional on the correctness and applicability of its
reviewed reference and text-to-math mapping.

## BIE-QA-MATH-003 — numerical evaluator

Numerical examples are recomputed with exact rational arithmetic and conservative
intervals. The operator supplies inputs, output units, reference expression, and a mode:
`exact_point`, `rounded_point`, or `interval`. Every input name/value/unit is checked;
mathematically equivalent units are normalized to SI before evaluation. Formula symbols
represent canonical-SI quantities. Both the original reference and candidate expression
are evaluated so cancellation cannot conceal an undefined reference point.

For a point, accepted error is <= max(abs_tolerance, rel_tolerance * abs(expected)).
Tolerances cannot be set by the candidate and relative tolerance is capped at 0.01.
For rounded points, exact round-half-to-even integer arithmetic and the declared number
of decimal places determine the required lexical answer. Rounded mode forbids an
additional tolerance. Significant figures are not inferred from arbitrary strings.

For interval mode the reported interval must enclose the computed interval, and its
width must not exceed the operator limit. A disjoint interval fails; an overlapping but
insufficient enclosure requires review. Intervals with dependency overestimation can
require review even when the real expression range is tighter. Sqrt uses exact rational
results for perfect rational squares, otherwise an outward rational enclosure based on
integer square roots with 24 decimal places. These are conservative bounds, not statistical
confidence intervals. Exact-point mode does not invent an exact answer from an enclosure.

## BIE-QA-MATH-004 — units evaluator

The explicit immutable unit registry uses the seven base dimensions in the preserved
native order L, M, T, I, Theta, N, J. It covers the shipped subset of SI-derived units,
common scales/prefixes, time units, litre, percent and radians, not every scientific unit.
Compound units require explicit multiplication/division/integer powers. Unknown units
are rejected. Numeric constants, unit scales and affine offsets use rational arithmetic.

Equations are checked for dimensional consistency; dimensionless function arguments
and dimensionally incompatible sums are handled explicitly. Symbols using affine units
must first be normalized to SI. Celsius/Fahrenheit absolute temperatures are distinguished
from temperature differences. Affine units in compounds and below-absolute-zero absolute
conversions fail. Quantity-kind distinctions outside the explicit registry are not inferred.
A dimensional pass does not prove a physical law or an empirical reference value.
The units report checks dimensions/conversions; formula and numerical reports separately
check expression domains and mathematical equivalence. No one report replaces all gates.

## Resource and input boundaries

Expressions: 2048 characters, 256 lexical tokens, 128 nodes, depth 24. Literal powers:
integers -8..8, not exponent towers. Rational strings: <=160 characters, decimal exponent
magnitude <=128, intermediates bounded to 2048-bit numerator/denominator. Sparse polynomials:
<=128 terms, total degree <=32, <=50,000 charged operations. Scope: <=8 symbols and 16 nonzero
conditions. Equation counterexample/admissibility probing stops at 256 assignments; it is
never used as exhaustive positive proof. Case arrays <=64/category; derivations <=64 steps
per case and <=256 total; conversions <=32/unit case. Policy arrays <=256. Review arrays
<=4096. CLI inputs <=4 MiB each and the math request serialized representation <=2,000,000
characters. Unsupported/budget-limited proofs remain review/block conditions.

Closed-world JSON schemas describe structures. Runtime dataclass validation enforces
semantic, reference, type, resource and relationship constraints beyond the schemas.
The JSON decoder rejects extra fields and nonconforming primitive/tuple types. The CLI
is a local operator interface, not an internet-facing sandbox; its explicitly supplied
configuration paths are not untrusted document paths. Source artifacts use the earlier
bounded confinement and identity checks. Dedicated worker CPU/memory/time isolation,
Windows compatibility and adversarial large-book throughput are still open obligations.

## Native compatibility and release connection

Five pinned native MATH files are included unchanged and exercised by adapters/tests.
They are compatibility snapshots at commit 375d99af0edd0086206817dae932156ddf61c569,
not an assertion about current HEAD. The native expression adapter requires original
text and compares it with a strict full parse, rejecting a detected native truncation.
Native chain continuity and float numerical diagnostics remain informational, not proof.

`bridge.prepare_release_evidence` recomputes QA, verifies the release candidate/run/revision
and actual source/output references, and returns unsigned report bytes plus an envelope
for `mathematical_correctness`. Healthy typed/text scope emits NOT_RUN; failed scope emits
FAIL. No branch emits PASS for the complete source/video/game math gate. The canonical
caller has not been migrated. Actual frames, captions, audio, simulations and game outputs
must be bound and evaluated later before complete product-release evidence is possible.

## Verification and handoff

276 unique new unittest methods pass with 444 subcases inside them. Preserved regressions
217 + 134 + 146 + 132 + 10 also execute separately. Seventeen selected safeguard-removal
probes detect the intentionally removed checks with passing controls. These are selected
probes, not exhaustive mutation coverage. Real execution receipts and source/test hashes
are under evidence/qa_section16/executed_run_005; mutation and offline-demo receipts are
separate. Package extraction, fresh reruns, negative integrity checks, reconstruction and
backup identities belong to the separate executed DELIVERY.json, not this pre-package spec.

All 328 parent file records are preserved: six superseded lane-root metadata files are
archived byte-for-byte under history/qa_section16/batch004_root. The five additional native
files are verified by Git blob SHA, SHA-256 and length. All previous source/tests remain
unchanged. No section-exit, full repository regression, model/assessor execution, native
math OCR, real book E2E, actual media/game runtime, GitHub integration or acceptance is claimed.

Next original tasks: BIE-QA-PED-001, -002, -003 and -004. Carry the gap ledger forward.

## Primary technical references

The implementation is new project code; these references inform limits/unit conventions,
not evidence that the project passes them. Retrieved during this batch:
- Python ast documentation: https://docs.python.org/3/library/ast.html (untrusted input/resource risks;
  this implementation does not evaluate Python AST or use literal_eval for mathematical input).
- NIST SI units: https://www.nist.gov/pml/owm/metric-si/si-units .
- NIST SP 811 Chapter 8: https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-8 .
