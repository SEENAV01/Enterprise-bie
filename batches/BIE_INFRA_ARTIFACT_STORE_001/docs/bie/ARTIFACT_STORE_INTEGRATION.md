# Artifact Store Integration Plan

1. Replace `InMemoryArtifactResolver` in the orchestrator with a catalog-backed resolver.
2. Store every ArtifactEnvelope canonical serialization as an immutable CAS blob.
3. Store large media/code bundles separately and reference their hashes from envelopes.
4. Store execution/QA evidence as first-class evidence artifacts.
5. Persist catalog metadata in PostgreSQL while blob bytes live in object storage.
6. Build run/stage/type/parent indexes.
7. Verify blob hashes before a stage consumes an artifact.
8. Release evaluation must consume evidence records from the catalog, not arbitrary filesystem paths.
9. Add retention/GC only after reachability and release-retention rules are specified.
