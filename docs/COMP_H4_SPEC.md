# COMP H4 — bounded content-preserving layout repair

Audit source: `docs/COMP_H3_REAUDIT.md`, finding H3-R01. This is the next correction batch in the existing audit cycle, NOT a new full section audit. Original COMP numbering is unchanged.

## Tasks fixed before implementation
- BIE-COMP-H4-001: source-bound layout permissions, deterministic candidate generation, semantic invariants. Only explicitly authorized owner rectangles and supported presentation fields may change. No content, labels, units, map projection, narration, timing, accessibility, tracks or provenance may be discarded or rewritten. No font reduction.
- BIE-COMP-H4-002: opt-in source emitters for readable literal text and responsive map legends; preserve legacy emitters without layout configuration. Actual wrapping and layout are emitted, not metadata-only promises.
- BIE-COMP-H4-003: exhaustive measured within-owner text collision/content checks, precise measurement identities, missing/duplicate frame rejection. Browser scope stays explicit; no bridge or unsigned evidence is promoted to actual Remotion acceptance.
- BIE-COMP-H4-004: bounded compile/measure/repair loop; revalidate every candidate, preserve original/effective identities, stop at the first observed safe candidate or produce a machine-readable upstream revision request. Caller reports cannot skip internal measurement.
- BIE-COMP-H4-005: CLI + publication integration, replayable fixtures, negative tests, package lineage and regression. Source publication is still source-only; actual-render authorization is never inferred.

## Hard limits and implementation boundary
The local candidate evaluator uses generated TypeScript executed with explicitly labelled React/Remotion doubles followed by real Chromium DOM painting, with network requests blocked. This can establish a locally measured technical candidate, not a trusted production renderer witness or learning-equivalence proof. Publication runs H3 regeneration and full-frame geometry again. The actual Remotion path retains its dependency/typecheck gate. No mandatory new question to the end user: the upstream Visual/Director layer supplies permitted regions; defaults do not claim authority to rearrange semantic figures. General scene redesign is requested upstream, not fabricated here.

R01 actual Remotion/ink/contrast/locale matrix, R02 specialized consumers and instructional equivalence, R03 operational isolation/complete toolchain, R04 pinned actual execution and R05 real-book/game acceptance remain on the SAME consolidated backlog. There is no section exit in this batch.

## Delivery
Separate cumulative integrated source and Master Backup. Current master embeds the current integrated source plus current atomic archives/evidence only, not prior masters. Required tests/fixtures and history remain available. Historical evidence may be moved only with a checksum-complete index and a tested restore command; no silent file loss.
