# Minimal authorized native measurement coverage correction

Finding: actual native render attempts 006 and 007 fail closed at the canonical
exhaustive TypeScript coverage gate. In attempt 007 the real TSC program includes
`qa-paint-helper.d.ts` but not the same-basename executable JavaScript helper.
TSC succeeded; the independent coverage gate correctly refused incomplete input.

The human explicitly authorized a minimal canonical producer correction on
2026-10-02, with before-image and regression evidence and no weakened guards.
Original `bie/compiler/real_paint.py` SHA256:
`9c243a4c15f524707dc84642335c2256e1ee655b04a6c6e996afa9d4a4aaa4ea`.
Its exact before-image remains outside the candidate in the local deliverables
`final-work/compiler-coverage-fix/real_paint.py.before`.

The producer retains the trusted executable helper, removes only its shadowing
declaration file, and places equivalent typed observation signatures in the
strict TS observer. Existing `allowJs=True/checkJs=False` for the trusted DOM
helper is unchanged. No source coverage, compiler configuration guard, renderer
isolation, witness seal, paint/raster assertion, dependency pin or Scene source
is relaxed. Original canonical checkout/main is not edited.

Four added explicit native tests exercise real isolated TSC: old-shadow defect
reproduction, fixed typed observer, seeded type error, seeded excluded source.
The actual native render journey additionally checks that coverage contains the
JavaScript helper and observer, and retains all previous renderer/CAS/corruption
assertions. Positive and negative native execution is pending until receipts
from the exact changed validation head are inspected. No render, real-book,
Section18 sign-off, PR, merge, deployment or product acceptance is claimed here.
