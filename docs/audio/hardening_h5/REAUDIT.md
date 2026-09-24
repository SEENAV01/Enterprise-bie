# H5 bounded implementation re-audit

This is a focused correction review, not the final consolidated section-exit audit.

## Reproduced issues corrected before final frozen verification

1. Host/namespace runtime identity mismatch. The original provider's library path identities changed from /usr/lib-style resolved paths to /lib-style paths inside the actual canonical namespace although bytes matched. An initial real run rejected PIPELINE_CHILD_RUNTIME_DRIFT. The correction performs actual no-input namespace discovery under pinned code and selected host identities. It preserves both identities instead of suppressing the mismatch, fabricating a signature or loosening comparison.
2. Fractional lease clocks. The crash-recovery test reached a real store verification using canonical float wall time. The receipt authorization path initially required an integer `now` and rejected it. The correction permits only finite nonnegative numeric verification clocks, retains integer signed timestamps, and adds valid-fraction, nonfinite/bool/negative/string and fractional-expiry tests. Signature and lease checks are not bypassed.
3. Publication heartbeat coverage. Code review found that ending the heartbeat immediately after native execution leaves CAS publication outside active renewal. H5 now keeps the inherited heartbeat active during publication and serializes renewal/completion against its lock. Canonical source is unchanged. Stale owners remain unable to commit; expiry/revocation stays fail-closed.
4. Explicit signer. Both issuing and durable execution require a real supplied signer, rather than allowing a missing signer to reach later attribute access. Current external trust remains required on every reuse.

5. Canonical dependency resolution. The unmodified original preparation-integration guard rejected a direct reference to the standalone snapshot folder in the new production profile adapter. The correction resolves canonical module locations through their actual installed import specifications and follows the required fixed import closure, including named dynamic canonical APIs. Fixture path setup remains only in explicit standalone scripts/tests. The guard was not removed, renamed, bypassed or relaxed; a new test also verifies installed-module resolution. The first exploratory regression was superseded and the corrected source frozen for final verification.

## Controls and limits retained

No arbitrary command, provider endpoint, weaker execution fallback, in-worker key, inference of acoustic acceptance from engine marks, unsigned-cache acceptance, manifest-as-authority, source-revision overwrite or product-acceptance escalation is added. Original source is preserved. New code uses the existing worker, store and lease implementations.

Current tests use a mixture of actual native executions/real stores and clearly localized failure injection. A mocked issue_execution in the completed-cache test proves that reuse must not invoke it; it is not reported as a new native run. Crash injection occurs at the actual canonical lease-completion method, after the claim transaction. The separate CLI benchmark must independently demonstrate real process restart and actual zero native re-execution.

The new lane supports local technical speech and dry narration mixes only. General music/SFX configurations, live provider recovery, full fleet security, cross-book scheduling and deployed key custody are not verified. Holding a signature over selected proof does not certify a compromised host. Same-engine word marks are not independent pronunciation. A synthetic two-scene source is not a real textbook. No actual video render, human listening, full enterprise test run or section/product acceptance is claimed.

Final executed counts and status are in FRESH_COMPLETE_REGRESSION.json, ATOMIC_VERIFICATION.json and NATIVE_BENCHMARK.json; do not substitute earlier partial or failed exploratory logs for final evidence.
