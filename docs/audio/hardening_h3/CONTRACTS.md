# AUDIO Hardening H3 — canonical durable acoustic lifecycle

## Authority and scope

This batch subdivides the existing AUDIO-AUDIT-001-F03 finding into H3-001..005.
It does not add original AUDIO roadmap IDs, restart H1/H2, certify voice quality,
or close F03 in full. It implements the **durable local acoustic evaluation lane**.
F01 live neural/listening, F02 production multilingual/calibrated evaluator authority,
F03 canonical kernel adoption across all AUDIO operations, and F04 real canonical
DIR/ANI/COMP handoffs remain open. No full section re-audit or GitHub write occurs.

## H3-001 — exact canonical interfaces and request identity

The existing BIE FileSystemCAS, SQLiteArtifactCatalog, DirectorArtifactIO,
ArtifactEnvelope, DirectorLeaseStore and SQLiteIdempotencyStore are executed by
this adapter. Five newly included dependency source files are exact bytes from
commit 16d4d87824e77db3565a231a332e7977d39d7117; their Git blob identities and
SHA-256 values are in CANONICAL_AUDIO_DEPENDENCIES.json. The five inherited DIR
files and DEPENDENCY_SNAPSHOT.json remain unchanged. The original class names
are retained intentionally: this is reuse, not a renamed fork or new orchestrator.
Production modules import bie.*. Only explicit standalone launchers add the
pinned dependency directory to the import path. Later canonical integration must
compare these pinned APIs with the then-current repository; it must not replace
newer canonical implementations blindly with these fixtures.

A request binds a UUID run, job ID, explicit revision, exact H2 acoustic job,
delivered waveform identity, pronunciation/source/voice/timing bindings, selected
runtime, signing issuer, code/dependency identities and bounded policy. Run/job/
revision determines the durable key; changing source or policy under that same
key fails instead of silently reusing stale work. A deliberate new revision makes
a new key and retains old artifacts. No source words, equations, timings or audio
are rewritten by this batch.

## H3-002 — canonical storage and current authenticity

The delivered WAV goes into the existing content-addressed store. The index is
persisted by the existing SQLiteArtifactCatalog, not a competing JSON index.
The three-envelope lineage is source.asset -> audio.acoustic.request ->
audio.acoustic.evaluation. The source.asset is explicitly an imported mapped MIX
asset with DECLARED source references; it is **not** a fabricated PDF, canonical
DIR artifact, source extraction verification or rights approval. F04 owns that
upstream adoption.

The evaluation includes the original Ed25519 receipt plus historical assessment
and repair intent. On every load, CAS bytes, envelope/reference hashes, complete
parent relationships, source/run identity and expected request are revalidated.
The original H2 verifier then authenticates the receipt against **current external
trust**, issuer validity, revocation, age, runtime and source identity. Current
assessment and repair intents are recomputed. A stored or rehashed PASS field is
not authentication. Historical issue-time assessment is never returned as current
authorization; a changed valid trust revision is reflected in the fresh result.
Expired or revoked evidence fails closed. The adapter never manufactures a new
signature or reruns evaluation to conceal a cache-authentication failure.

No private key is serialized into CAS, SQLite, artifact metadata or reports.
Output metadata retains REVIEW and product_accepted=false. Existing pronunciation,
acoustic calibration and rendered AV uncertainty findings remain in QA.

## H3-003 — bounded, fenced jobs and recovery

AUDIO uses namespaced keys in the original lease and idempotency tables. Each
invocation gets a new unguessable owner token; two invocations cannot pretend to
be the same worker. Live leases cannot be stolen. Expired claims require a new
epoch and the original fenced reclaim operation. Heartbeats refresh the held
lease. Cancellation or loss of the heartbeat cancels the inherited native child.
Completion reauthenticates the stored result and verifies the fence again before
committing either success marker. At exact expiry a fence is not usable.

Short transitions across the two original table APIs are serialized using a
cooperating local file lock. A crash after the claim is completed but before the
lease is completed is recoverable without repeating native evaluation, but only
after current signature/source verification. A crash before the result pointer
is committed can cause **at-least-once local evaluation** after lease expiry. An
immutable orphan may remain. No exactly-once external TTS or distributed-lease
guarantee is claimed; paid provider retries are not routed through this lane.
Automatic attempts are bounded (default three epochs); exhaustion requires an
explicit new revision/recovery decision. No hidden loop or indefinite retry.

A COMPLETED job means the requested diagnostic execution was completed; its QA
status may still be REVIEW/BLOCKED/FAIL. Completion does not authorize release.

## H3-004 — actual existing native and QA adoption

The miss path calls H2 issue_evaluation, which internally executes the unchanged
bounded native acoustic worker and signs its actual measurement. A cache hit has
zero native evaluation calls but repeats current signature, source and runtime
checks. The existing audit_mix and publish_evaluation are consumed directly.
The original source waveform and captions are not silently changed. Source
pronunciation repairs remain owned intents; canonical repair dispatch and
transitive rendered-artifact invalidation remain F03/F04 work.

The worker remains H2_BOUNDED_LOCAL_NOT_CANONICAL_KERNEL. This batch does not
pretend the separately existing compiler kernel worker has been adopted for all
AUDIO native operations. No new sandbox or operating-system isolation proof is
claimed. Current legacy en-US limitations, unsupported Hindi/IPA/OOV paths and
uncalibrated phonetic evidence are preserved.

## H3-005 — executable entry and operational boundary

scripts/audio_durable.py loads a previously published exact MIX/SYNC workspace,
requires explicit local-diagnostic opt-in and an out-of-band runtime/trust/signer
configuration, and executes the durable lane. It rejects overlapping source,
authority, store and output paths, symlink inputs, existing output directories and
insecure private-key files. Credentials are never requested through chat.

The dedicated store is local to a service account, with a private root, bounded
file/count/byte budgets and rejection of symlink, nonregular, hardlinked and
foreign/writable members. This is not a hostile shared-filesystem, network-storage,
malicious administrator, encryption-at-rest or power-loss certification. Every
writer to this dedicated root must use the same short catalog/job locking
protocol. Disk-full/simultaneous power-loss, fleet-scale chaos and total cgroup
resource accounting remain deployment validation. The original SQLite catalog
reloads its bounded index per operation; distributed scale and garbage collection
are not introduced or implied.

Book-sized jobs must continue using explicit existing segment/scene boundaries.
This adapter refuses over-budget acoustic jobs instead of truncating them; it is
not a new autonomous book scheduler or an unbounded batch consumer.

## Verification interpretation

Native benchmark data uses actual timed-eSpeak speech and FFmpeg MIX on synthetic
text, independent legacy acoustic evaluation, SQLite/CAS persistence, separate
CLI processes and current signature rechecks. Test-only keys are ephemeral.
Fixtures and injected worker failures in unit tests are labelled as such. The
native benchmark and fresh cumulative test suite are separate evidence. A green
suite proves expected implementation behavior, not cinematic speech quality,
production evaluator authority, real-book acceptance or real Remotion rendering.
