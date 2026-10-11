# Task036 exact canonical-history profile compatibility

This is a test-support compatibility repair, not a dependency/native/rendering
change or an approval record. The original seven Task035 PROFILE_BLOBS and all
20 CI-R2 safety methods/assertions remain intact. The historical workflow pin
is retained as profile authority, not described as the current workflow bytes.

## Observed boundary

Candidate 34007d3265ffb55961f48a8becd359bef741a9a4 adds only full-history
checkout to three canonical workflows. Canonical dispatch 38149635357 attempt1
completed successfully. Its safe archive still needs independent receipt review;
an aggregate success is not sufficient for Task036 closure. Focused Scene IR
38149408741 failed its strict AFTER step; M1 38149408760 failed the original
safety step. M1 affected/native-extra succeeded and renders were skipped.

The separate reviewer directly executed approved_profiles on that candidate and
observed APPROVED_PROFILE_IDENTITY_MISMATCH. It pins the entire canonical
Post-DIR workflow, including the unrelated checkout-history option. All other
six profile inputs are unchanged. The direct safety assertion uses the same
guard, so bypassing only the AFTER wrapper would leave mandatory coverage broken.
Historical first-run painter causes remain UNKNOWN and are unrelated to this
demonstrated guard mismatch. The failed AFTER and safety ZIPs and successful
canonical ZIP were subsequently retrieved with exact API digest/byte checks and
ZIP CRC checks. Receipt contents are reviewed separately, not inferred from labels.

## Exact governed selection

The separate task036-ci-history-amendment/AMENDMENT.json authenticates two exact
preimages: the historical workflow and the original test-support guard. Fixed
original/workflow-replacement hashes and lengths are fixed in canonical_history_profile.
The workflow's replacement must equal the original bytes after removing exactly
one fetch-depth:0 line. The reviewed Git guard is the bootstrap trust root. It
checks the helper's fixed source hash before execution and executes precisely
those checked bytes, without a second import-loader read. Separate REPLACEMENTS
source-contract tests authenticate the exact active guard/helper/manifest hashes.
That attestation does not grant admission or override the bootstrap pin. This
acyclic arrangement avoids impossible mutually self-referential hashes.
Unknown paths, altered manifests, rollback, missing preimages, additional workflow
changes and other profile drift reject. No expected source hash is derived from
the current files during verification; only the fixed reviewed identities apply.
Raw preimages are -text files. Existing native seals/ledgers are unchanged.

Old roots without this amendment keep original admission only with the exact
original guard identity. An active guard with a rolled-back workflow and missing
seal rejects. Amended roots
emit a distinct bie.task035.post-dir-after/2 closed receipt with a separately
authenticated bie.task036.canonical-history-profile-witness/1 object. Its map
role explicitly identifies historical authority versus actual workflow bytes.
The content digest names canonical amendment content, not a claim of raw-file
identity. Legacy v1 receipt validators remain compatible with old receipts and
unchanged safety fixtures. Actual current collection always emits v2 after exact
source admission. Current-candidate v1 cannot substitute for source-currentness
proof. V2 still requires the original real runtime/pip/parser checks,
all six original candidate/base probes, zero failures/errors/skips and the same
interpreter identity. A witness cannot substitute for any gate.

The original Task035 runner, inherited assertions, installer/requirement versions,
native engines, graph and all execution budgets are unchanged. Additional scoped
source/receipt controls belong exactly once to the Task036 NEW lane, separately
from the original 12+20 safety inventories. Local synthetic validator fixtures
do not constitute hosted compiler or producer proof. Fresh exact-candidate M1,
Scene IR, full canonical evidence and independent review remain mandatory.

Task035 bounded sign-off stands. Audio reconciliation remains OPEN. Scene IR
remains review-required/unaccepted; later global stages remain NOT_RUN. No PR,
merge, Task036 canonical completion or product acceptance is asserted here.
