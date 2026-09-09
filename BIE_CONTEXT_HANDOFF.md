# BIE context handoff — 2026-09-09

## Owner, repository and purpose

Naveen's My Book Intelligence Engine continues here. Active repository: https://github.com/SEENAV01/Enterprise-bie, branch `main`. An older conversation named `SEENAV01/MY-BOOK-INTELLIGENCE-ENGINE-`; that is historical context, not this verified target.

The user supplied https://chatgpt.com/share/6aa0e579-5268-83ee-b4f0-9a4694a22085 to carry the old conversation forward, integrate existing ZIPs into GitHub, and retain downloadable ZIP backups for future batches. The shared page could not be fetched in this session. Context was recovered from available conversation history and the actual archived project specifications and code; do not claim the complete shared transcript was read.

## Binding product decisions

1. Preserve the M001–M300 work, M301 integration history, enterprise modules, stable task IDs, specifications, tests, evidence and provenance. Continue from recovered work; do not restart or silently reduce the product.
2. BIE owns document/knowledge representations, graphs, orchestration, reasoning artifacts, pedagogy, compilers and QA. Model providers are replaceable. This application is not itself a newly trained foundation model.
3. The full product converts textbooks into a grounded learning model, lesson structure, teaching/script/visual/animation plans, executable educational video code and executable interactive revision games. Video and game share the same grounded learning model. The enterprise product specification retains actual build/render/runtime/QA gates; older phase-specific code-generation boundaries remain recorded as history.
4. Prerequisites for generation must derive from the topic, concept and related textbook paragraphs/source evidence. Do not require learners to supply what they know, a questionnaire or a mastery profile before source-driven generation. Later learner adaptation can be an optional separate concern.
5. Content determines teaching order, visual representation and duration. Do not impose arbitrary 60/90-second limits or replace semantic planning with a fixed lesson template.
6. More ingested PDFs should improve BIE cumulatively through better retrieval memory, extracted structures, corrections, evaluation and governed datasets. Domain adapters or fine-tuning require evidence and appropriate data governance; do not retrain a base model automatically for every uploaded PDF. This is a retained requirement, not an implemented training claim.
7. A module marked IMPLEMENTED or unit-tested is not automatically ACCEPTED. Acceptance requires its integration, real-book/golden benchmark and downstream evidence. Never claim success from a generated file alone.
8. Future completed batches must have both a verified GitHub commit and a downloadable ZIP backup, with an updated continuation checkpoint.

## Latest recovered development checkpoint

- Latest archive by creation timestamp: `BIE_RE_DEC_001.zip`, created 2026-09-08 21:28:19 UTC.
- Task: **BIE-RE-DEC-001 — Auditable reasoning decision factory**.
- Original status: `IMPLEMENTED`; `accepted: false`.
- Original blocker: integrated real-book reasoning validation pending.
- Its source is `app/bie/reasoning/decision_factory.py`; the richer earlier reasoning contract remains `app/bie/reasoning/decision_contracts.py`.
- Preceding recent work includes `BIE_RE_EVID_001`–`004`, mathematical intelligence and prerequisite intelligence. The actual PR and MATH files are present; do not restart prerequisite work from an older remembered checkpoint.
- No authoritative next atomic task after DEC-001 was recoverable. First reconcile the decision factory, richer decision contract and canonical artifact envelope, then define the next atomic task explicitly. Do not invent a previously approved DEC-002 specification.

## Repository assembly checkpoint

- 766 original ZIPs, 691 distinct archive hashes, 12,259 original member files.
- 376 enterprise batches, 390 historical packages, 390 combined enterprise source files.
- All 374 original task results are preserved without acceptance promotion.
- 11,151 imported non-cache files are expanded and checksum-verifiable.
- Real GitHub write and readback were verified with `test.txt`, commit `34d14230f6c323e0589e9e6f35421659522e201b`.
- The assembly commit is returned with the delivered backup and can be recovered from Git history. This document deliberately does not contain its own commit SHA.

## Read on the next session

Read this file, `docs/bie/CURRENT_STATE.md`, `docs/bie/REPOSITORY_ASSEMBLY.md`, the relevant batch SPEC and task result, and the live repository state. Keep provenance and the original archives intact. Update the working implementation and working tests; record any departure from an imported test in the assembly/change log.
