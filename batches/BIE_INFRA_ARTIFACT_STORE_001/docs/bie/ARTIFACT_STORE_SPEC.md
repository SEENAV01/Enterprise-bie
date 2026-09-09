# BIE-INFRA-ARTIFACT-STORE-001 — Content-Addressed Artifact & Evidence Store

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Provide BIE with an immutable, content-addressed persistence boundary for artifacts and QA/execution evidence.

The store is responsible for bytes/content persistence and indexing. Semantic artifact identity remains governed by the ArtifactEnvelope contract.

## Core invariants
1. Stored blobs are addressed by SHA-256 digest.
2. Same bytes deduplicate to the same blob identity.
3. Existing blob content cannot be mutated in place.
4. Reads verify digest integrity.
5. Artifact records map artifact IDs to immutable blob hashes.
6. Evidence records are first-class artifacts, not informal log strings.
7. Run/stage indexes support reproducible artifact lookup.
8. Parent/lineage indexes support reverse and forward traversal.
9. A record cannot reference a missing blob.
10. Conflicting re-registration of an artifact ID is rejected.
11. Store interface is backend-neutral; local filesystem is only the reference implementation.
12. Deletion/retention policy is separate from semantic identity.
13. Corrupt bytes fail closed.
14. Artifact metadata and payload blobs may be persisted independently in future backends.

## Reference backend
This task includes a local filesystem CAS implementation suitable for development/tests:
`<root>/blobs/sha256/ab/<full_digest>`

Metadata/index is represented in memory in this atomic task; a durable SQL/object-store implementation is a downstream infrastructure task.

## Enterprise backend direction
The same interface can later be implemented using:
- S3-compatible object storage
- cloud blob storage
- local/NAS CAS
- database metadata + object storage
without changing domain stages.

## Evidence
Execution evidence, compile logs, render manifests, frame-QA reports, game runtime reports and release evidence are stored through the same immutable mechanism.
