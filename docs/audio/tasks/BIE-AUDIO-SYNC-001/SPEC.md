# BIE-AUDIO-SYNC-001 — word timestamps

Original AUDIO Section 14 task; continuation from VO-010. Actual required behavior, input/output contracts, rejection modes and precise evidence boundaries are in `docs/audio/BATCH003_CONTRACTS.md` under SYNC-001. No new original task IDs invented.

Run `python scripts/run_audio_tests.py --pattern test_audio_sync_001.py --output /tmp/sync-001.json`.
Declared task tests: 31; actual native speech tests are concentrated in SYNC-001, with cross-task native CLI/browser evidence separately reported. All other synthetic media fixtures are explicitly non-speech/test-double inputs. Intermediate outputs cannot self-award acceptance.

Task ZIPs are independent shared-source closures, not ordered deltas. Require installed eSpeak for native speech. No GitHub writes.
