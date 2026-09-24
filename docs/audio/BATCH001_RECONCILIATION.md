# AUDIO Batch 001 — explicit reconciliation

Two different implementations were delivered under the same original VO-001..005 task IDs. They are **not** merely different test totals. Both exact cumulative ZIPs are preserved under `lineage/audio_batch001/`.

The later 144-test API remains unchanged at `bie.audio.*`. The earlier 204-test implementation is retained byte-for-byte under `bie.audio.compat204.*`. The original 204 test assertions are preserved; only their import paths, helper import, and CLI module name were changed. Both inherited suites run in the current workspace (348 tests). Fourteen additional tests verify the compatibility handoff, original archive hashes, lossless source mappings, review propagation, Hindi reading and retained sums/products.

The 204 parser's sums/products and broader Greek-name vocabulary have **not** been silently removed. The 144 parser's English/Hindi reading, scoped lexicon, IPA/PLS metadata and source-bound pauses remain. Different public data models and policies are never implicitly interchanged. `preparation_bridge.from_v144` and `from_v204` execute and validate the respective real preparation pipeline, then expose one `SpeechPlan`. Both can now feed the same language, voice, synthesis and cache pipeline. The supplied original ZIPs stay immutable.

No claim is made that 348 tests represent 348 unique features: the two suites overlap in intent. This is a compatibility-preserving reconciliation, not an unreviewed rewrite into a supposedly superior third preparation engine. Any later API consolidation must retain these behavior tests and documented differences. No new roadmap task IDs were invented for the reconciliation.
