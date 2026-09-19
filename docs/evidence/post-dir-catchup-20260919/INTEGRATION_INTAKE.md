# Post-DIR canonical catch-up integration intake

Repository: `SEENAV01/Enterprise-bie`
Staging branch: `integration/post-dir-catchup-20260919`
Base main commit: `73840d86a78e5f31438e2a1bad34f3b2a8433eb9`
Base tree: `adf64727adaf2ec9dd92c8f1ea03e2df2b8d738c`

## Canonical base state

The base branch is DIR = IMPLEMENTATION-SCOPE COMPLETE — NOT ACCEPTED.
No change to `main` is authorized until post-DIR section lineage, source normalization,
tests, preservation evidence and exact remote readback pass.

## Recovered local post-DIR source

Final COMP/DSL cumulative source archive available in the current integration session:

- file: `BIE_COMP_HARDENING_H12_INTEGRATED.zip`
- SHA256: `96044db24b5d466dbc5e8c1136865dccece705c4d8ea71ce41b6c4265ce1c0d5`
- members: 5,494
- `app/bie/**` members: 217
- tests: 241
- docs: 168
- scripts: 30

Master:
- `BIE_COMP_HARDENING_H12_MASTER_BACKUP.zip`
- SHA256: `b886837bab63a8215ae261221f79460f2703e47ab3d5bd40bee0c6a8300c2320`

Normalization required during canonical integration:
- `app/bie/scene_ir/**` -> `bie/scene_ir/**`
- `app/bie/compiler/**` -> `bie/compiler/**`
- preserve the existing canonical `app/bie/__init__.py` compatibility alias mechanism
- stop on different-content collisions; do not unzip blindly over canonical source

## Missing exact-source inputs before canonical catch-up can be committed in dependency order

1. VIS final cumulative source / Master Backup corresponding to the final VIS exit evidence.
2. ANI final H4 / final section source and evidence. The latest currently recovered ANI evidence
   visible to this integration session is H3 and explicitly says H4 remained next.
3. DSL original/hardening archive bytes required for lossless archive preservation, unless supplied
   through a complete section Master Backup.
4. COMP original pre-BUILD archive bytes (ARCH/REACT/ELEM/ANI/AUDIO/ASSET families) required for
   the same lossless archive-preservation standard, unless supplied through their Master Backups.

Do not fabricate or reconstruct missing archive bytes from summaries.

## Intended commit order

DIR base -> VIS canonical integration -> ANI canonical integration -> DSL canonical integration ->
COMP canonical integration -> exact remote SHA/tree/blob readback -> enterprise regression ->
then fast-forward `main` only after all gates are green.

## Truth boundary

This intake commit records integration preparation only.
It does not claim VIS/ANI/DSL/COMP are canonically integrated on GitHub,
does not claim runtime/product acceptance, and does not modify `main`.
