# H5 exact-source closure instructions

Canonical DIR verified lineage: commit `73840d86a78e5f31438e2a1bad34f3b2a8433eb9`, tree `adf64727adaf2ec9dd92c8f1ea03e2df2b8d738c`.

Before VIS can exit:
1. Mount/recover the canonical DIR source/artifacts and execute the strict DIR codec.
2. Recover all eight original REP ZIPs and verify these hashes:
- BIE_VIS_REP_001.zip: `9a818bff38a86235a2d40e039d35e3db24354da6da769e6183c881d2e233867d`
- BIE_VIS_REP_002.zip: `5280828dfb442a728d5504aec23f355d10acc99db8b05ff0e33920e6188f2c31`
- BIE_VIS_REP_003.zip: `59d3d6f7bc1fe7612600aaaefd9cf163eaeaa1b41a652546c2854eba6d7d7eca`
- BIE_VIS_REP_004.zip: `8393cb8886ed2d0e5d47b60bec1f9429f29f2e31e517eefde7a0941515ecdf75`
- BIE_VIS_REP_005.zip: `07eb7dfde8773122b524f63ebb028f8defc4461678cc6551e81da99b74c7bedb`
- BIE_VIS_REP_006.zip: `0c5ae1fe989bb108a5c8bb14d0d02996df82475cad8e8d3c45224a18da4dcb75`
- BIE_VIS_REP_007.zip: `fbc13e70b2eab37e0ccece48d902ee10e56c4f8dd0524aa16bbe97e5e99de8c8`
- BIE_VIS_REP_008.zip: `87ece417e7075744b0f42523d3f83e8e17f68cf4f15f84e4565f1c9c7bdc5e71`
3. Run the original REP 125 tests in the same environment as original GRAM..QA and all H1..H5 tests.
4. Run the strict H5 section gate; only a clean gate may permit `VIS = IMPLEMENTATION-SCOPE COMPLETE — NOT ACCEPTED`.
5. Then perform VIS final re-audit 003 and canonical GitHub integration/readback.

Current local-available regression: 564/564 PASS; exact REP and canonical DIR source execution not included.
