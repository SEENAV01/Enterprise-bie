# Native math parser repair — Section 16 candidate evidence

Status: **PENDING HOSTED COMBINED GATE AND RE-AUDIT**. This is a scoped repair,
not Section 16 sign-off, mathematical correctness acceptance, or product release.

The canonical `bie/math_intelligence/expression_ast.py` at base commit
`1ba9e25ff97822ef901bcb116afd90b4a76a8290` returned a `*` root for
`["x", "*", "y", "+", "z"]`, silently discarding `+ z`. The Section 16
complete-parser adapter detected that divergence and failed closed, but native
consumers still received an incomplete AST. The repair keeps the `Node` data
contract, adds complete token consumption and operator precedence, and rejects
unsupported/malformed syntax rather than accepting a prefix.

`manifests/qa_section16_native_math_parser_001.json` records the native owner
before/after hashes and the three inherited QA expectation migrations. The
original 817-path adoption manifest and the first fixture amendment remain
unchanged. `scripts/section16_gate.py --verify-only` checks all of these exact
bytes; additional seeded-negative tests verify tamper and sign-off rejection.

Focused local run on this uncommitted candidate (Windows Python 3.13):

| Scope | Result |
| --- | ---: |
| Section 16 adoption/integrity gate controls | 32/32 |
| New native-parser positive/negative controls | 10/10 |
| H4 parser controls | 43/43 |
| Math native-adapter controls | 16/16 |
| Inherited native AST contract | 4/4 |

Total: **105 unique focused tests**, zero assertion failures/errors in these
scopes. The full H4 suite is not claimed locally: on Windows its POSIX secure
artifact I/O correctly rejects use, and `jsonschema` is absent in the local
environment. The approved hosted Linux combined gate must run against the
exact committed candidate before any broader regression claim.

The repaired native grammar is intentionally bounded to explicit binary
operators and atomic symbols/numbers. Parentheses, unary operators, functions,
source extraction, semantic equivalence, rendered math, scientific truth and
the wider `QA16-GAP-025` / `QA16-GAP-028` obligations remain separately open.
No existing historical source ZIP was altered. No product acceptance is claimed.
