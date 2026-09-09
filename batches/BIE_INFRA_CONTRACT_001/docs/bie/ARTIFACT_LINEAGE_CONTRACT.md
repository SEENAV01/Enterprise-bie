# BIE Canonical Artifact Envelope & Lineage Contract

Task: BIE-INFRA-CONTRACT-001  
Status: IMPLEMENTED + CONTRACT-TESTED IN PACKAGE

## Purpose
Every major BIE artifact must be typed, versioned, immutable-by-content, traceable, and independently verifiable.

The contract applies to source-derived artifacts, knowledge graphs, prerequisite graphs, reasoning decisions, pedagogy plans, director plans, visual plans, animation plans, Scene IR, Game IR, generated code, build outputs, renders, QA evidence, and release manifests.

## Required Envelope
Every production artifact MUST include:

- `artifact_id`
- `artifact_type`
- `schema_version`
- `run_id`
- `created_at`
- `producer`
- `content_hash`
- `parent_refs`
- `provenance_summary`
- `metadata`
- `payload`

## Identity Rule
`artifact_id` is stable for the serialized canonical content + artifact type + schema version.

Changing payload or lineage-relevant metadata changes the `content_hash` and therefore the `artifact_id`.

## Parent Lineage Rule
Every non-source-root artifact must reference one or more parent artifacts. A release artifact must be able to traverse parent links back to source evidence.

## Provenance Rule
Source-grounded artifacts carry source references. Inferred artifacts must additionally carry inference reason and confidence.

## Producer Rule
Producer identity is framework-neutral:
- component
- component_version
- execution_kind (`deterministic`, `model`, `human`, `hybrid`)
- optional provider/model/tool identifiers

No downstream domain contract may depend directly on a provider name.

## Run Context
All artifacts belong to a `run_id`. A run records:
- product/version
- source identifiers
- configuration hash
- model/tool policy identifier
- environment fingerprint
- start time
- optional parent run

## Release Invariant
A release manifest may only reference artifacts whose lineage graph validates, whose hashes match content, and whose required QA evidence artifacts are present.

## Versioning
Schema versions use semantic versioning.
- PATCH: backward-compatible clarification/optional field.
- MINOR: backward-compatible additive change.
- MAJOR: incompatible contract change.
Consumers MUST reject unsupported major versions.

## Failure Semantics
Missing required lineage, hash mismatch, invalid provenance, unsupported major schema, cyclic lineage, or missing required release evidence are gate failures, not warnings.
