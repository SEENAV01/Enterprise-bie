# Upload the sealed canonical integration bundle

Status: transfer mechanism repaired and locally tested; post-DIR source is NOT yet published to this GitHub branch.

## One upload

1. Download `BIE_POST_DIR_CANONICAL_TRANSFER.tar.xz` from the accompanying ChatGPT delivery. Do not extract or rename it.
2. In this repository, select branch `integration/post-dir-catchup-20260919` and open this folder: `.integration/post-dir-catchup/`.
3. Choose **Add file > Upload files**, select that one binary file, and commit directly to this staging branch. Do not upload it to `main` or create another branch.

Exact file size: **8,452,556 bytes**.
SHA-256: `17ce2d9700ccb6227a7fb86a879a5f39c4e5ebec535980a7cdf446a2e961d9b4`.

The upload triggers **Apply Sealed Post-DIR Integration** automatically. The workflow rejects any file with a different hash. It restores exact supplied originals, applies VIS -> ANI -> DSL -> COMP as four local commits, runs the declared complete regression and preservation gates, and publishes only the verified result to staging. A separate write-permission job validates every phase's Git tree before a non-force push. `main` is never changed by this workflow.

The evidence artifact contains the full candidate repository ZIP and actual gate logs. A failed gate stops publication; it must not be treated as a successful integration.

## Scope and evidence

The sealed package preserves **386 supplied files**, including **193 top-level ZIPs**, and reconciles **435 distinct nested ZIP objects / 83,616 member records**. Its complete local restore reproduced **20,489 candidate files byte-for-byte**. The local canonical regression passed **6,485 tests**, zero failures, errors or skips. These are source/integration checks, not actual Remotion or product acceptance.

The ten previously declared `BIE_VIS_LAYOUT_001.zip` through `010.zip` archives were not found as exact original archive bytes in the supplied collection. Their combined layout source package is preserved and its active code is integrated in the candidate. This historical availability gap is explicitly recorded; no missing archive is reconstructed or falsely marked received.

Do not upload all section batches again. This single sealed bundle carries the complete supplied collection and the verified canonical source plan.
