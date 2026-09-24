# BIE AUDIO Hardening H2 — local verified implementation

**Section 14, BIE-AUDIO-H2-001..005 implemented and tested in the stated local diagnostic scope. F02 is NOT fully closed; AUDIO and product acceptance remain false. No GitHub write.**

## Exact continuation
H1 Integrated SHA-256: `b75e4e8e5ae0a291581098e411f0151b812748bc5a2788ece111c010bbcb2624`. Both supplied H1 archives matched the saved hashes and CRCs. Pristine H1 was actually rerun: **1,009 tests, zero failures/errors/skips**. H2 is an engineering subdivision of the existing AUDIO-AUDIT-001-F02 finding, not a restart or replacement.

## Implemented tasks
| Task | Capability | Tests |
|---|---|---:|
| BIE-AUDIO-H2-001 | Exact source/media/voice/policy evaluation identity | 28 |
| BIE-AUDIO-H2-002 | Independent bounded native acoustic measurements | 21 |
| BIE-AUDIO-H2-003 | Externally configured evaluator trust and signed receipts | 31 |
| BIE-AUDIO-H2-004 | QA ownership, source-preserving repair intents and fresh rechecks | 19 |
| BIE-AUDIO-H2-005 | Verified publication, diagnostic CLI and real-audio benchmark | 21 |

The full frozen-source AUDIO regression passed **1,129 tests: 1,009 inherited + 120 new, zero failures/errors/skips**. All executed Python hashes match the delivered active code. Atomic packages are independently runnable shared-source closures, not sequential deltas. Final fresh-extraction/CRC/payload and tested-source verification is in the separately supplied FINAL_VERIFICATION file. The whole canonical enterprise 6,485-test suite was NOT rerun.

## Real processing, not only mocked contracts
The native benchmark used actual timed-eSpeak speech and real FFmpeg MIX on synthetic source examples. Three independent searches per measured English segment (constrained word FSG, unconstrained allphone, unconstrained N-gram) operated on delivered WAV crops. English: three measured segments, 15 word windows, nine native search passes, status REVIEW. A second independent CLI execution reproduced the exact measurement.

Controlled silent final audio: FAIL, correct AUDIO/MIX ownership because the original dry source still had signal. The existing MIX implementation was genuinely rerun; the repaired media matched the original non-silent mix. A fresh signed recheck preserved source and reading and resolved the detected silence items, while overall acceptance remained false. Hindi: explicit unsupported-language BLOCKED, not silently substituted with English recognition.

The benchmark also rejected old-media receipts, unknown/revoked issuers, and altered evidence with recomputed public hashes but no valid signature. Read-only signature/publication verification returned success for current original evidence. Test and benchmark issuers are ephemeral local TEST-ONLY authorities; no private signing key is bundled. Packaged receipts are historical and naturally expire for live reuse.

## Fail-closed integration and review
The existing audit_mix now optionally adopts signed current-source acoustic evidence. Original required pronunciation/alignment/render uncertainty findings are retained. Owned repair intents never rewrite source text and cannot falsely resolve when the replacement evaluator is blocked. Publication verifies exact bytes and reauthenticates acoustic results rather than trusting caller-rehashed JSON. No new orchestrator is introduced.

The first development cumulative run caught one real architecture failure: worker bootstrap logic lived inside a production AUDIO module. The unchanged inherited guard failed. Bootstrap was moved into a pinned standalone launcher; the guard and then the complete suite passed. The original failed development evidence is retained separately, not misrepresented as a passing delivery. Other focused corrections cover MIX-vs-VO ownership, blocked repair rechecks, bool-as-number fields and caption-export tampering.

## Preservation and remaining work
Only one inherited runtime file changes: bie/audio/qa_pipeline.py, with exact original backup and a unified patch. All inherited tests, original speech providers, H1 neural provider source, both preparation implementations and the five pinned DIR dependencies remain byte-identical. Governance files and the package manifest are deliberately updated with exact originals preserved. PRESERVATION.json accounts for every parent file. No fonts, model weights, native binaries or private keys are shipped.

This is a real independent **local diagnostic** path, not cinematic pronunciation certification. The installed evaluator is an explicitly identified legacy en-US model. Production multilingual/accent/IPA/OOV capabilities, calibrated phonetic/word-boundary performance, independent listening and production evaluator trust remain material F02 work. F01 live neural/listening validation remains open. F03 canonical worker/CAS/cache/recovery and F04 canonical DIR/ANI/COMP and rendered AV remain open. Declared invalidations are not durable kernel dispatch. Real-book and learner/product acceptance remain unverified. No section exit or full section re-audit is claimed.

Use CONTINUATION.json and the updated consolidated gap ledger. The next task IDs must be derived from those finite residuals; no automatic H3 numbering or section exit is invented.
