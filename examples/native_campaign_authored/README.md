# Authored local campaign example — NOT a real book benchmark

Three cases: valid 2-second local diagnostic, intentionally wrong frame reference, corrupt media.
The HTML is a placeholder and is NOT executed or a playable game.
All three native release verdicts remain BLOCKED; 28 native gates are preserved.

## Run from combined_source/ in a trusted private worker

Provision dependencies/tools from the retained source requirements first. Do not change managed browser policy.
Create a private parent directory named `local-work` before these commands.

```sh
python -B -m bie.qa.lifecycle_quality_v2 eval-campaign init --campaign-dir local-work/campaign --plan examples/native_campaign_authored/REQUEST.json --expected-plan-sha256 47cea0a819be3a5564641e0184bc00583a0110bf8d46824ea9543696bd57d125
python -B -m bie.qa.lifecycle_quality_v2 eval-campaign run --campaign-dir local-work/campaign --artifact-root examples/native_campaign_authored/artifacts --expected-plan-sha256 47cea0a819be3a5564641e0184bc00583a0110bf8d46824ea9543696bd57d125
python -B -m bie.qa.lifecycle_quality_v2 eval-campaign summary --campaign-dir local-work/campaign --expected-plan-sha256 47cea0a819be3a5564641e0184bc00583a0110bf8d46824ea9543696bd57d125
```

Expected exit code is **2**, including technical-positive cases: this is a blocked partial benchmark, not a release approval. A second run re-reads completed results without recollecting.

The request pins both runtime code and local FFmpeg tool/fixture identities. It may block on a different toolchain. Do not rewrite a trusted reference or pin merely to obtain PASS. For a fresh authored diagnostic on a separately approved runtime, use `tools/run_section17_native_campaign_diagnostics.py --output-dir <fresh-output>`; that regenerates a clearly labelled development fixture, not a golden benchmark.
