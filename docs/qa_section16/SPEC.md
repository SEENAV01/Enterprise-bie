# BIE-QA-RELEASE-001 — Evidence-bound release contract v2

## Source and continuation

The user-supplied Original 18-Section Master Atomic Task Registry names this task
on page 17. Section 16 spans pages 17–19 and has 76 original entries. Page 21
requires original implementation, completeness audit, justified hardening, re-audit,
integration and real-book end-to-end proof; implementation is not acceptance.
The latest explicit user instruction permits this QA implementation lane to run in
parallel with externally managed Section 15. It does not waive release dependencies.

Read-only repository inspection was pinned to commit
`375d99af0edd0086206817dae932156ddf61c569`. The existing v1 contract and its ten tests
are preserved exactly, not silently rewritten or recounted as new work.

## Reproduced baseline limitation

The original evaluator aggregates metadata and reference strings; it does not read
the referenced artifact bytes. A preserved behavior test can receive `SUCCESS`
from all required PASS records even when the cited files do not exist. This is a
contract-level behavior, not evidence that a real production release was made.
The new diagnostic bridge retains the original decision but returns BLOCKED and
requires freshly generated candidate-bound evidence. It cannot upgrade legacy PASS.
Canonical caller migration is deliberately pending because other work is concurrent.

## New implementation decisions

These are this batch's explicit design choices, not text attributed to the registry:

1. Opt-in namespace `bie.qa.release_v2`, exact wire/policy version `2.0.0`.
2. Frozen dataclasses and tuples; closed-world JSON fields; bounded inputs; no implicit
   coercion of strings, booleans or floating-point values into identities/times/sizes.
3. SHA-256 content identities and a project-specific deterministic JSON encoding
   (sorted keys, compact UTF-8, integer-only values). No external canonical-JSON
   standard or Unicode semantic-equivalence guarantee is claimed.
4. Candidate identity includes run, 40-character repository revision and every
   declared artifact identity. A full candidate must include source, video and game.
   Auxiliary supporting files can also be declared.
5. The trusted policy defines mandatory floors. Custom policies may strengthen
   floors, but may not remove gates, drop required roles, weaken execution to review,
   or silently reroute owners. Math/accessibility/performance are not silently optional.
   A domain with no mathematical content still requires a grounded applicability
   finding from its eventual evaluator; this batch does not invent that finding.
6. An evidence record binds candidate digest, policy digest, run, revision, evaluator
   identity/version, evidence kind, inspected artifact IDs, hashed report bytes,
   creation/expiry times and signer identity. All are covered by its receipt MAC.
7. A POSIX directory-FD backend uses no-follow directory/file opens, nonblocking file
   open, regular-file checks, hard-link rejection, streamed hashing and before/after
   file metadata checks. It never executes files, fetches URLs or follows symlinks.
8. A caller-configured, out-of-band HMAC verifier authorizes evaluator, version, gate
   and proof kind. The default denies. Its test-only assurance cannot become production
   readiness. Unknown/revoked/unauthorized keys and malformed verifier responses fail.
9. All required candidate artifacts for the gate must be covered. Unknown artifact
   IDs, ambiguous ID/path versions, duplicate evidence IDs and unknown gates fail.
   Strengthened independent-rater floors require distinct evaluator IDs AND reports.
10. Fixed input `as_of` makes replay deterministic. Future, expired or excessively
    long-lived evidence is invalid. FAIL/ERROR/SKIPPED/NOT_RUN cannot be outvoted by PASS.
11. Output is BLOCKED, CONTRACT_ONLY or READY_FOR_REVIEW. `release_authorized` and
    `product_accepted` are always false. No score, certifier, repair execution or
    publication side effect is hidden in this interface.

## Limits and trust assumptions

Input JSON: 4 MiB. Candidate artifacts: at most 2,048. Evidence records: at most 1,024.
Single file: 256 MiB. Combined declared bytes: 2 GiB. Maximum evidence lifetime: seven
days; stricter operator policies are allowed. Larger cinematic assets fail explicitly
rather than being truncated or auto-approved; governed large-media support is open.

The operator must provide a trusted, immutable artifact store. Verification proves
bytes observed during this check, not immutability after the check or at later
publication. A concurrently writable directory is not a production storage solution.
The no-follow implementation does not replace process/container/network isolation.

HMAC authenticates possession of a shared secret, not the truth or quality of an
educational claim. It is not asymmetric non-repudiation. Production key distribution,
rotation, worker execution attestation and secret-backend integration are pending.
A caller able to configure the trust registry is inside the trusted service boundary;
the bundle may not configure it. Honest evaluator adapters and calibration still matter.

A file with role `video` is a declared subject, not proof of decodable/rendered media.
The actual render/frame/audio/game evaluators, original-source grounding and semantic
checks are separate original tasks. The schema alone does not prove any of them.
The bundled examples are unmistakably synthetic, and positive controls use test trust.

## API

```python
from bie.qa.release_v2 import ReleaseEvaluator
from bie.qa.release_v2.codec import load

bundle = load("bundle.json")
report = ReleaseEvaluator().evaluate(bundle, "artifact-root", as_of=1790413200)
assert report.release_authorized is False
```

An authenticated service can inject its independently provisioned verifier. No trust
keys, "skip" flags or policy weakening are accepted from the submitted bundle.

## Verification scope

132 new tests; ten unchanged original QA contract tests; eight selected mutation
probes; schema meta-validation and dataclass field consistency; source byte hashes;
no-side-effect test; seeded permutations; per-gate negative examples; CLI hash-seed
replay and fresh ZIP extraction. All actual logs are supplied separately.

These are standalone capability/contract checks. They do not establish whole-repo
compatibility, actual Linux GAME/Remotion output, calibrated pedagogy, real books,
production key-management quality, successful GitHub integration or product acceptance.
