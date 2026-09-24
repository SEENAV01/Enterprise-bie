# Recovery implementation corrections and first-run history

The first 106-test recovery run had zero failures and two errors. Both negative
lease tests encountered the intended canonical `RecoveryError` rejection, while
the newly written tests incorrectly expected `AudioError` or `ValueError`.
The assertions now require the exact existing `RecoveryError` type. No production
lease code, rejection behavior, inherited test or acceptance criterion was relaxed.
The failing first-run log is retained as development history, followed by fresh
corrected-suite/packaged-source results. It is not replaced with a fabricated pass.

During implementation, exact durable-request fingerprint signing was added after
review identified that media/job/profile signatures alone would not authenticate
relabeled exported run/job/revision metadata. Negative publication tests rehash
that metadata and its inventory and require rejection by the v2 signature binding.

The first full fresh regression then caught the inherited import-purity rule:
application modules must not manipulate Python import paths. The new fixed child
initially put its isolated-engine bootstrap in `bie/audio/kernel_entry.py`.
The bootstrap is now a separate fixed script `scripts/audio_kernel_worker.py`,
while the application module remains import-pure. Both script and engine source
are explicitly profile-hashed and staged. No string obfuscation, guard relaxation
or inherited-test edit was used. Full fresh regression is rerun after this change.
The partial first full-run logs are retained as a superseded development attempt.

Fresh extraction of the initial small task closures exposed missing inherited
synthetic example inputs. All five task setups failed rather than silently using
workspace files. The closure builder now includes the unchanged `examples/`
fixtures, and each task is re-extracted and rerun. Integrated source already
contained those files. This packaging correction does not change application or
test code; failed zero-test setup logs remain in the development history.
