# Section16 Batch019 — RIGHTS001/002

## Authority and scope

Original registry page18, BIE-QA-RIGHTS-001 asset rights; BIE-QA-RIGHTS-002 source
licenses. This is an additive continuation under `bie/qa/rights_v2`, not a restart,
Section15 implementation, repository merge, section exit or legal certification.
The exact Batch018 Integrated bytes are the parent; no canonical GitHub file was
read or written in this batch. The historical inspection SHA is not current HEAD.

## Contracts and data flow

An operator supplies immutable `RightsPolicy`, separate from `RightsRequest` and
reviewer keys. The request carries a bounded existing `Snapshot` and declared use
selections. The policy binds the exact snapshot digest, grantee, commercial flag,
territories, channels, half-open planned-use interval, material/extent inventory,
parent lineage, required operations and the complete set of uses. Every source-role
artifact must be mapped; assets/embedded components still require independent
inventory review. Policy categories and license mappings are not inferred from
filenames, user claims, purchase, educational intent or generated provenance.

Every snapshot file is read through the existing `SnapshotStore`, with hashes,
sizes, no-follow filesystem confinement, hard-link rejection and total-size limits.
The exact file set is checked before and after evaluation. This is bounded local
I/O (16MiB/file,64MiB snapshot), not large remote-object streaming or a hostile-input
execution sandbox. Request/policy decoding uses the existing closed-world codec.

`Material` distinguishes SOURCE and ASSET with an explicit extent ID, provenance
reference, license expression and parent materials. A derived material requires
explicit compatible operation coverage for every ancestor in the same output.
This conservative propagation does not decide whether a factual idea is copyrightable,
whether an adaptation is legally derivative or what exclusions a book's license has.
Those determinations belong to separately authorized review.

`Grant` identifies a grantor, evidence files, one selected license/exception atom,
permission basis and operations. Dimensions distinguish copyright, voice, likeness,
trademark, privacy, database, provider terms and other operator-declared rights.
READ/EXTRACT/QUOTE/ADAPT/SYNC/EMBED/DISPLAY/DISTRIBUTE/TRAIN/RETRIEVE are distinct data
permissions, not an automatic statement of what a given law or license requires.
The evaluator checks them literally against the reviewed planned use. No automatic
permission is created by an ownership claim, public-domain claim or AI generation.
Legal-exception records additionally require a separate inference-purpose review.

AND requires all selected terms; OR requires an explicit complete choice; WITH is
an indivisible atom, so an exception cannot silently disappear. The bounded parser
accepts SPDX-style IDs, parentheses, AND/OR/WITH. It does NOT implement a complete
SPDX catalog validator, '+' resolution, external DocumentRef retrieval, compatibility
inference or legal interpretation. Unknown/unsupported expressions require review.
A chosen grant must individually cover all required operations/dimensions and the
use window. Evidence from conflicting or insufficient grant scopes is not pooled
into a fabricated permission. Unselected alternatives do not veto a valid choice.

## Evidence freshness and obligations

A supplied rights-status artifact lists every grant exactly once and records an
explicit observation time. Unknown/inactive/stale states cannot pass. The evaluator
checks this snapshot and its independently authenticated review; it does not call a
live revocation registry, interpret termination, or override an irrevocable license.

Operator-defined attribution, license notices, change notices, source offers and
custom conditions require exact UTF-8 bytes at explicit byte offsets in approved
output/notice artifacts. Notice identity/location and complete obligation coverage
are checked. Output license labels must match any independently supplied allowlist.
This does not prove rendered legibility, actual deployment, link availability,
source-offer fulfillment or universal license compatibility. Disclosure review is
mandatory; the full rights release gate never passes from file checks alone.

## Authentication and decisions

Reuses `reasoning_v2.ReviewVerifier` and `repair_v2.planner.approved`. There are no
embedded operational trust keys. Inventory, current status, grant authority/terms,
material-to-output use, and disclosure receive separately bound subjects/purposes.
Reviews bind the complete request, policy, exact evidence IDs, time and reviewer.
Missing, uncertain, test-only, stale, wrong-scope or low-confidence review cannot
be a pass. An authenticated rejection cannot be outvoted. Hashes and HMACs establish
content identity and configured authority, not actual ownership or legal correctness.

Local result: CHECKS_PASSED, REVIEW_REQUIRED or BLOCKED. Reports remain
`product_accepted=false` and `legal_clearance_certified=false`. The release bridge
checks the actual candidate identity, artifact coverage and per-output uses,
recomputes reports and emits unsigned FAIL (blocked) or NOT_RUN (otherwise) for
`rights_and_asset_provenance`. It never emits full release PASS or signs evidence.

## Run

From the extracted package, Python3.11+ with the inherited test dependencies:

```sh
PYTHONPATH=. python -B -m unittest discover -s tests/qa_rights19 -p 'test_*.py'
PYTHONPATH=. python -B scripts/verify_qa_rights19_batch019.py --output /tmp/new-qa19-tests
PYTHONPATH=. python -B scripts/verify_qa_rights19_mutations.py --output /tmp/new-qa19-mutations
PYTHONPATH=. python -B scripts/demo_qa_rights19.py --output /tmp/new-qa19-diagnostics
python -B scripts/verify_qa_section16_package.py
```

The full test runner uses isolated child processes. Each output directory must be
new. Keep receipts outside a frozen package or exact manifest verification fails.
The default CLI is an unsigned, read-only audit with no key or network setup:

```sh
PYTHONPATH=. python -B -m bie.qa.rights_v2 --request request.json --policy policy.json \
  --root snapshot --as-of 10000 --output /tmp/new-rights-result.json
```

The CLI refuses existing output files, snapshot-internal output, symlink request
files and oversized JSON. Exit3 means review required,2 blockers,4 invalid I/O;
zero means only bounded local checks, never product/legal acceptance. Positive
operational reviews can be supplied through the Python API after independent trust
configuration. Fixture keys must never be installed as operational authority.

## Verification and boundaries

143 new unique tests cover scope, actual bytes, Unicode notices, license-selection
branches, status, authentication, alias/lineage checks, strict wire contracts,
CLI behavior and unsigned release integration. Three structural JSON schemas are
validated; Python code enforces cross-record semantics. Sixteen guard-removal
probes have independent passing controls and fail by assertion rather than import
errors. These are targeted probes, not exhaustive mutation testing.

Ten authored diagnostics exercise real file reads and the actual evaluator. Their
grants, status documents, positive authority credentials and assessment clock are
SYNTHETIC; no actual book, asset or voice was cleared. No live licensing service,
independent legal professional, rendered credits, native media/game, actual learner
or real-book end-to-end run occurred. The existing release evaluator is separately
executed and remains BLOCKED.

## Source references consulted (not encoded as automatic permissions)

- User's original 18-section master registry: p18 RIGHTS001/002; p21 workflow rule.
- SPDX Specification2.3 AnnexD, https://spdx.github.io/spdx-spec/v2.3/SPDX-license-expressions/,
  consulted 2026-09-27: AND/OR/WITH semantics, precedence and case handling guided
  the bounded syntax selector. No full standards-conformance claim.
- CC BY4.0 legal code, https://creativecommons.org/licenses/by/4.0/legalcode.en,
  consulted 2026-09-27: scope, other rights and attribution conditions illustrate
  why reviewed terms/obligations are separate from a license label. The engine does
  not hard-code or paraphrase this license as a complete permission policy.

## Remaining obligations

Actual material/embedded-component inventory from BI/VIS/COMP/GAME; qualified,
independently provisioned rights review and license interpretation; production
status refresh and revocation/termination handling; rights lineage across native
outputs; rendered and deployed notices; complete SBOM/provider/license coverage;
large-artifact streaming; current-HEAD adoption; full canonical regression and
real-book acceptance. All inherited gaps, including Section15 native-origin runtime
validation, remain. Next original tasks: SEC001 generated-code security and SEC002
sandbox escape tests, then PERF/REL and full-section audit/hardening/re-audit.
