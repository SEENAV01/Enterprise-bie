# Usage

From the extracted cumulative package root (Python3.11+):

```sh
python -B scripts/verify_qa_visual16_batch008.py --output /absolute/new/evidence-folder
python -B -m bie.qa.visual_v2 --request request.json --policy operator-policy.json --artifact-root ./artifacts --as-of 1800000000 --output qa-result.json
```

The example timestamp is synthetic; the operator must supply the applicable run time.
CLI is unsigned and will require review. Exit codes: 0 bounded checks passed, 2 blocked,
3 review required, 4 input/filesystem error. Existing output is never overwritten.
Application code can supply existing source and review verifier instances out of band;
do not deploy synthetic test keys as operational trust.

For trusted self-authored static browser diagnostics:

```sh
python -B scripts/verify_qa_visual16_browser.py --output /absolute/new/browser-evidence
```

Requires Playwright, Pillow and an operator-installed Chromium executable. Default
path is /usr/bin/chromium; API callers may pass a different local executable path.
No network installer runs automatically. The collector is not for hostile HTML in
an unsandboxed worker. Actual observed dependency versions are in the test receipt.

Run selected fault probes:

```sh
python -B scripts/verify_qa_visual16_mutation_probes.py --output /absolute/new/mutation-evidence
```

Only execute downloaded code after validating its independently supplied checksum.
Package checksum gives integrity, not author identity. Installation, canonical caller
migration, real renders and GitHub integration are not performed by these commands.
