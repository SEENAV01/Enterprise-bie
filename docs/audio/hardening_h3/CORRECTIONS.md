# H3 development findings and corrections

These are development records, not earlier accepted H3 releases.

1. New test support omitted the RecoveryError import. It was added; inherited tests were not modified.
2. A stale-owner test exposed differing exception ordering between the adapter and the canonical fence. The existing canonical fence is now checked first, followed by the stricter exact-expiry boundary. No failure is converted to success.
3. The first native restart benchmark incorrectly required whole-publication byte identity. The inherited publisher uses random path-derived lock names and corresponding outer manifests. The benchmark now compares every evidence/caption payload byte and verifies each publication with the unchanged inherited verifier. It does NOT claim whole-output reproducibility.
4. A real storage-inspection defect was reproduced: checking envelope CAS blobs alone did not detect corruption of the raw WAV referenced inside a source.asset envelope. inspect() now loads and verifies each referenced WAV and validates the acoustic job binding. Two regression tests were added. The independent CLI corruption test now rejects the altered store. The pre-correction source and failed logs are preserved in external evidence.

CUMULATIVE_DEV executed 1214 tests successfully on the development snapshot before the raw-WAV inspection correction and two added tests. That run is NOT final tested-source evidence. Final release verification is the separately delivered fresh-Integrated 1216-test record, after code freeze.
