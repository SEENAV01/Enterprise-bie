# H1-007 — approved compiler repair source-origin reconciliation

Finding-derived integration hardening, not an additional original Section18
task, not a new compiler behavior and not a render waiver.

Attempt017 run37066598268 stopped the complete canonical gate at the sealed
H12 producer target hash. The approved `enableCaching:false` change deliberately
changed that active producer; the original integration manifest still correctly
preserved its old hash. Blindly changing that ledger would erase provenance.

The amendment leaves every original manifest and archive unchanged. One exact
original row is redirected, for verification only, to its byte-identical LF
Git preimage. Both that preimage and the narrowly approved active producer are
independently hash-pinned. The full original manifest Git hash is pinned too.
Only standard CRLF-to-LF Git checkout conversion is permitted; no semantic
normalization or caller-provided replacement hash is accepted. Every other row
uses the existing verification unchanged. Original archive/member/target counts
are retained and a separate reviewed-amendment count is reported.

Nine focused controls passed, including positive original preservation,
arbitrary active replacement, missing/tampered preimage or amendment, edited
replacement hash, duplicate keys, original manifest drift, duplicate selected
row and unrelated-manifest non-override. Earlier failed control attempts are
retained. Hosted complete canonical regression is still required; local
standalone source intentionally excludes historical ZIP/manifest backups.

Task028 remains paused. Section implementation, integration, product acceptance
and deployment remain false. No sandbox/resource/coverage/toolchain constraint
is changed by this source-origin amendment.
