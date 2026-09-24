# BIE-AUDIO-QA-001 — pronunciation QA

## Ownership and purpose
Original AUDIO Section 14 capability; continuation from Batch 004, not a new speculative task.

Exact source/rule/voice/media-bound pronunciation targets and reported-observation processing. Mismatches block; positive reported text is not authenticated phonetic evidence. Independent pronunciation remains REVIEW.

## Implementation
`bie/audio/qa_pronunciation.py` with shared `qa_contract`, `qa_source`, `qa_pipeline`, `qa_io` and existing source-preserving VO/SYNC/MIX contracts. Shared code and dependencies are explicitly included in the atomic closure; an atomic package does not mean all included code is newly owned by this task.

## Verification
`python -B scripts/run_audio_tests.py --pattern test_audio_qa_001.py --output <external-result.json>`

Declared task tests: 18. Final freshly extracted atomic-package execution is recorded in the delivery's FINAL_VERIFICATION.json. Negative tests test rejection; their success never changes a sample's REVIEW/FAIL into product acceptance.

## Constraints
No content truncation, source mutation, generic caller PASS scores, paid provider calls or GitHub writes. Native tests require NumPy, FFmpeg/ffprobe and eSpeak with matching library/data. No external font files are shipped. Independent listening, production isolation and actual Remotion rendering are not claimed.

See `docs/audio/BATCH005_CONTRACTS.md` and `AUDIO_CAPABILITY_AUDIT_001.json` for the complete unresolved implementation/acceptance boundary.
